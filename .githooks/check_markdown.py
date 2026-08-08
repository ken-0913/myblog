#!/usr/bin/env python3
"""마크다운 글이 포매터에 의해 깨졌는지 검사한다.

검사 항목
  1. shortcode HTML 이스케이프  — `{{&lt; name &gt;}}`  (원본: `{{< name >}}`)
  2. 인라인 수식 구분자 소실     — 본문에 `\\text{` 등이 `\\(...\\)` 밖에 노출

정상 종료 0, 문제 발견 시 1.
"""
import re
import sys


def split_front_matter(src: str):
    """(front matter, body) 를 돌려준다. front matter가 없으면 ('', src)."""
    if not src.startswith("---"):
        return "", src
    parts = src.split("---", 2)
    if len(parts) < 3:
        return "", src
    return parts[1], parts[2]


def find_issues(path: str):
    with open(path, encoding="utf-8") as f:
        src = f.read()

    issues = []

    # 1) shortcode 가 이스케이프된 경우
    if "{{&lt;" in src or "&gt;}}" in src:
        issues.append("shortcode가 HTML 이스케이프됨 — `{{&lt;` (원래 `{{<`)")

    front_matter, body = split_front_matter(src)

    # 2) 수식을 쓰는 글에서만 인라인 구분자 소실을 검사한다
    if "math:" in front_matter:
        stripped = body
        stripped = re.sub(r"\$\$.*?\$\$", "", stripped, flags=re.S)   # 블록 수식
        stripped = re.sub(r"```.*?```", "", stripped, flags=re.S)     # 코드 펜스
        stripped = re.sub(r"`[^`]*`", "", stripped)                   # 인라인 코드
        stripped = re.sub(r"\\\(.*?\\\)", "", stripped, flags=re.S)   # 정상 인라인 수식

        leaked = re.findall(
            r"\\(?:text|mathbb|mathbf|mathrm|times|approx|sqrt|infty|begin|cdot|top)\b",
            stripped,
        )
        if leaked:
            sample = ", ".join(sorted(set(leaked))[:3])
            issues.append(
                f"본문에 구분자 없는 raw LaTeX {len(leaked)}건 (예: {sample}) "
                "— 인라인 수식이 `\\(...\\)` 없이 노출됐다"
            )

    return issues


def main(paths):
    failed = False
    for path in paths:
        try:
            issues = find_issues(path)
        except OSError:
            continue  # 삭제된 파일 등은 건너뛴다
        if issues:
            failed = True
            print(f"  ✗ {path}")
            for issue in issues:
                print(f"      - {issue}")

    if failed:
        print()
        print("커밋을 중단했다. 마크다운 편집기가 수식/shortcode를 훼손한 상태다.")
        print()
        print("내용 편집은 남기고 손상만 되돌리려면:")
        print("    python3 scripts/repair_markdown.py " + " ".join(paths))
        print()
        print("의도한 것이라면 `git commit --no-verify` 를 쓴다.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
