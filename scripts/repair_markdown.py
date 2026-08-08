#!/usr/bin/env python3
"""편집기가 훼손한 마크다운을 복구한다. **내용 편집은 보존한다.**

    python3 scripts/repair_markdown.py content/posts/llm/llm-series-all-in-one.md
    python3 scripts/repair_markdown.py --check  content/posts/**/*.md   # 진단만
    python3 scripts/repair_markdown.py --base HEAD~3  <파일>            # 기준 커밋 지정

배경
    리치 텍스트 계열 편집기가 파일을 다시 저장하면서 세 가지를 망가뜨린다.
      1. 인라인 수식 구분자 `\\(...\\)` 제거      → 화면에 raw LaTeX 노출
      2. `{{< shortcode >}}` HTML 이스케이프      → shortcode가 글자로 출력
      3. `<br/>` 를 ORCA 플레이스홀더로 치환      → mermaid 줄바꿈 깨짐

    이때 사용자가 **직접 고친 내용**도 같은 파일에 섞여 있다.
    파일을 통째로 되돌리면 그 편집까지 날아간다. 그래서 3-way 병합을 쓴다.

동작 방식
    2·3번은 규칙이 역방향으로 결정적이라 그냥 되돌린다.
    1번은 지워진 정보라 복원할 수 없으므로, git의 정상본을 참조한다.

        ours   = git 정상본                (구분자 있음)
        base   = 정상본에서 구분자만 제거   ← 인위적 공통 조상
        theirs = 작업본 (2·3번 복구 후)     (구분자 없음 + 내용 편집)

    base와 theirs의 차이는 **순수한 내용 편집**뿐이므로,
    git merge-file이 그 편집만 정상본 위에 얹어 준다.

    충돌이 나면 파일을 건드리지 않고 충돌 지점을 보고한다.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()

ORCA_RE = re.compile(r"\[\[ORCA_RICH_MD:[0-9a-fA-F]+:inline-html:([^\]]+)\]\]")
MATH_CMD_RE = re.compile(
    r"\\(?:text|mathbb|mathbf|mathrm|times|approx|sqrt|infty|begin|cdot|top|"
    r"frac|underbrace|Phi|odot|neq|to|quad|left|right)\b")


# ---------------------------------------------------------------- 되돌릴 수 있는 손상

def undo_reversible(src):
    """shortcode 이스케이프와 ORCA 플레이스홀더를 되돌린다. (본문, 건수)"""
    n = 0

    def orca(m):
        nonlocal n
        n += 1
        return urllib.parse.unquote(m.group(1))

    src = ORCA_RE.sub(orca, src)
    for bad, good in (("{{&lt;", "{{<"), ("&gt;}}", ">}}"),
                      ("{{&#37;", "{{%"), ("&#37;}}", "%}}")):
        n += src.count(bad)
        src = src.replace(bad, good)
    return src, n


# ---------------------------------------------------------------- 진단

def split_front_matter(src):
    if not src.startswith("---"):
        return "", src
    parts = src.split("---", 2)
    return (parts[1], parts[2]) if len(parts) >= 3 else ("", src)


def diagnose(src):
    """남아 있는 손상을 나열한다."""
    issues = []
    if "{{&lt;" in src or "&gt;}}" in src:
        issues.append("shortcode가 HTML 이스케이프됨")
    if ORCA_RE.search(src):
        issues.append("ORCA 플레이스홀더가 남음 (원래 인라인 HTML)")

    front, body = split_front_matter(src)
    if "math:" in front:
        s = body
        s = re.sub(r"\$\$.*?\$\$", "", s, flags=re.S)
        s = re.sub(r"```.*?```", "", s, flags=re.S)
        s = re.sub(r"`[^`]*`", "", s)
        s = re.sub(r"\\\(.*?\\\)", "", s, flags=re.S)
        leaked = MATH_CMD_RE.findall(s)
        if leaked:
            sample = ", ".join(sorted(set(leaked))[:3])
            issues.append(f"구분자 없는 raw LaTeX {len(leaked)}건 (예: {sample})")
    return issues


def leaked_lines(src):
    """수식 구분자가 없는 줄의 (번호, 내용)."""
    out = []
    fence = block = False
    for i, line in enumerate(src.split("\n"), 1):
        if re.match(r"^\s*```", line):
            fence = not fence
            continue
        if line.strip() == "$$":
            block = not block
            continue
        if fence or block:
            continue
        probe = re.sub(r"\\\(.*?\\\)", "", line)
        probe = re.sub(r"`[^`]*`", "", probe)
        if MATH_CMD_RE.search(probe):
            out.append((i, line.strip()))
    return out


# ---------------------------------------------------------------- 복구

def strip_math_delims(src):
    """`\\(x\\)` → `x`. 인위적 공통 조상을 만들기 위한 정규화."""
    return re.sub(r"\\\((.*?)\\\)", r"\1", src, flags=re.S)


def math_vocab(good):
    """정상본에 쓰인 인라인 수식 알맹이를 모은다. 긴 것부터."""
    seen = {m.group(1) for m in re.finditer(r"\\\((.*?)\\\)", good, flags=re.S)}
    return sorted((s for s in seen if "\n" not in s), key=len, reverse=True)


def rewrap_math(text, vocab):
    """구분자가 벗겨진 수식에 `\\(...\\)` 를 다시 씌운다.

    정상본에 실제로 등장했던 문자열만 대상으로 하므로 오탐이 적다.
    코드펜스와 `$$` 블록, 이미 감싸인 곳은 건드리지 않는다.
    """
    out, fence, block, n = [], False, False, 0
    for line in text.split("\n"):
        if re.match(r"^\s*```", line):
            fence = not fence
            out.append(line); continue
        if line.strip() == "$$":
            block = not block
            out.append(line); continue
        # 건드리면 안 되는 줄:
        #   - heading: KaTeX가 렌더되지 않는다(유니코드로 쓴다)
        #   - shortcode: 파라미터는 수식이 아니라 데이터다
        #   - 충돌 마커
        if (fence or block or re.match(r"^#{1,6} ", line)
                or "{{<" in line or "{{%" in line
                or line.startswith(("<<<<<<<", "=======", ">>>>>>>", "|||||||"))):
            out.append(line); continue

        # 이미 감싸인 수식과 인라인 코드는 통째로 건너뛰고,
        # 그 사이 자유 텍스트에서만 치환한다.
        # 한 번 감싼 것이 다시 대상이 되지 않도록 안정될 때까지 반복한다.
        for _ in range(10):
            segs = re.split(r"(\\\(.*?\\\)|`[^`]*`)", line)
            hit = 0
            for si in range(0, len(segs), 2):      # 짝수 인덱스만 자유 텍스트
                seg = segs[si]
                if not seg:
                    continue
                for item in vocab:
                    if item not in seg:
                        continue
                    pat = r"(?<![\\\w`])" + re.escape(item) + r"(?![\w`])"
                    seg, k = re.subn(pat, lambda m: "\\(" + m.group(0) + "\\)", seg)
                    if k:
                        hit += k
                        break              # 이 구간은 다음 회차에 다시 훑는다
                segs[si] = seg
            line = "".join(segs)
            if not hit:
                break
            n += hit
        out.append(line)
    return "\n".join(out), n


def resolve_take_theirs(merged):
    """충돌 블록에서 '작업본' 쪽만 남긴다. 줄 단위 상태 기계."""
    out, state = [], "keep"
    for line in merged.split("\n"):
        if line.startswith("<<<<<<< "):
            state = "ours"
        elif line.startswith("||||||| "):
            state = "base"
        elif line == "=======" and state in ("ours", "base"):
            state = "theirs"
        elif line.startswith(">>>>>>> ") and state == "theirs":
            state = "keep"
        elif state in ("keep", "theirs"):
            out.append(line)
    return "\n".join(out)


def git_show(ref, relpath):
    r = subprocess.run(["git", "-C", ROOT, "show", f"{ref}:{relpath}"],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def merge3(ours, base, theirs):
    """git merge-file 3-way 병합. (결과, 충돌수)"""
    paths = []
    try:
        for name, text in (("ours", ours), ("base", base), ("theirs", theirs)):
            fd, p = tempfile.mkstemp(suffix=f".{name}.md")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            paths.append(p)
        r = subprocess.run(
            ["git", "merge-file", "-p", "--diff3",
             "-L", "정상본", "-L", "공통조상", "-L", "작업본", *paths],
            capture_output=True, text=True)
        # 반환코드 = 충돌 수, 음수는 오류
        return r.stdout, (r.returncode if r.returncode >= 0 else -1)
    finally:
        for p in paths:
            os.unlink(p)


def repair(path, base_ref, apply_changes, take_theirs=False):
    rel = os.path.relpath(os.path.abspath(path), ROOT)
    with open(path, encoding="utf-8") as f:
        working = f.read()

    print(f"\n{rel}")

    before = diagnose(working)
    if not before:
        print("  손상 없음")
        return 0
    for i in before:
        print(f"  ✗ {i}")

    # 1) 되돌릴 수 있는 손상 먼저
    fixed, n_rev = undo_reversible(working)
    if n_rev:
        print(f"  · 되돌림: shortcode·인라인 HTML {n_rev}건")

    # 2) 수식 구분자는 정상본을 참조해 3-way 병합
    result, conflicts = fixed, 0
    if any("raw LaTeX" in i for i in before):
        good = git_show(base_ref, rel)
        if good is None:
            print(f"  ! {base_ref} 에 이 파일이 없다 — 수식 구분자는 복구 불가")
        else:
            result, conflicts = merge3(good, strip_math_delims(good), fixed)
            if conflicts < 0:
                print("  ! 병합 실패 — 파일을 그대로 둔다")
                return 1
            print(f"  · 3-way 병합: 기준 {base_ref}"
                  + (f", 충돌 {conflicts}곳" if conflicts else ", 충돌 없음"))

    if conflicts and take_theirs:
        # 충돌 지점은 작업본(사용자 편집)을 채택하고, 벗겨진 수식만 다시 씌운다.
        result = resolve_take_theirs(result)
        good = git_show(base_ref, rel)
        result, n_wrap = rewrap_math(result, math_vocab(good))
        print(f"  · 충돌 {conflicts}곳: 작업본 채택, 수식 {n_wrap}건 다시 씌움")
        conflicts = 0

    if conflicts:
        print(f"  ! 충돌 {conflicts}곳 — 파일을 쓰지 않았다.")
        print("    수식이 들어 있는 줄을 직접 고쳤을 때 생긴다.")
        print("    아래 '작업본' 문장에 \\(...\\) 를 다시 씌워 저장하면 된다.\n")
        for hunk in re.findall(r"^<<<<<<< .*?^>>>>>>> .*?$",
                               result, flags=re.S | re.M):
            for line in hunk.split("\n"):
                print(f"      {line}")
            print()
        return 1

    after = diagnose(result)
    if apply_changes:
        with open(path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"  → 저장함 ({len(result.splitlines())}줄)")
    else:
        print("  (--check 모드: 저장하지 않음)")

    if after:
        print("  남은 문제 — 직접 손봐야 한다:")
        for i in after:
            print(f"      ✗ {i}")
        for ln, txt in leaked_lines(result)[:10]:
            print(f"      {ln}: {txt[:90]}")
        return 1

    print("  ✓ 복구 완료")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="편집기가 훼손한 마크다운을 복구한다(내용 편집 보존).")
    ap.add_argument("paths", nargs="+", help="복구할 .md 파일")
    ap.add_argument("--base", default="HEAD",
                    help="정상본을 가져올 git ref (기본: HEAD)")
    ap.add_argument("--take-theirs", action="store_true",
                    help="충돌 시 작업본(내 편집)을 채택하고 수식만 다시 씌운다")
    ap.add_argument("--check", action="store_true",
                    help="진단만 하고 파일을 쓰지 않는다")
    a = ap.parse_args()

    if not ROOT:
        sys.exit("git 저장소 안에서 실행해야 한다.")

    rc = 0
    for p in a.paths:
        rc |= repair(p, a.base, apply_changes=not a.check,
                     take_theirs=a.take_theirs)
    print()
    return rc


if __name__ == "__main__":
    sys.exit(main())
