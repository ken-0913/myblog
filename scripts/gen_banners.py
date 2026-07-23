#!/usr/bin/env python3
"""
포스트 제목 배너 자동 생성기 (B안: AI 아님, 비용 0, 화풍 일관).

동작:
  - content/posts 아래의 각 글(.md 단일 파일 또는 <폴더>/index.md)을 순회
  - front matter에 featuredImage가 이미 있으면 건너뜀(idempotent)
  - 없으면 제목을 얹은 배너 PNG를 static/images/banners/<slug>.png 로 생성
  - front matter에 featuredImage: /images/banners/<slug>.png 삽입

배너 디자인: 터미널 브랜드 톤(다크 배경 + 초록 프롬프트 모티프).
폰트: FONT_PATH 환경변수로 지정 가능. 없으면 OS별 한글 폰트 후보를 탐색.
"""

import os
import re
import sys
import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "content" / "posts"
# assets/ 전역 리소스로 두어야 Hugo가 baseURL(/myblog/)을 붙인 URL을 생성한다.
# static/에 두면 하위 경로 사이트에서 featuredImage 링크가 깨진다.
BANNER_DIR = ROOT / "assets" / "images" / "banners"
# featuredImage 값은 앞 슬래시 없이(assets 상대경로) — resources.Get 이 해석한다.
BANNER_URL_PREFIX = "images/banners"

W, H = 1200, 630
# 연한 회색 배경 + 검은색 글자 (라이트 톤)
BG_TOP = (244, 245, 247)       # #f4f5f7
BG_BOTTOM = (231, 234, 238)    # #e7eaee
GREEN = (34, 139, 63)          # #228b3f 프롬프트(라이트 배경 대비 확보한 초록)
TITLE_COLOR = (24, 24, 27)     # #18181b 제목(검은색)
MUTED = (100, 108, 120)        # #646c78 보조 텍스트
ACCENT_BAR = (34, 139, 63)

FONT_CANDIDATES = [
    os.environ.get("FONT_PATH", ""),
    # Linux (CI): fonts-noto-cjk
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Bold.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    # macOS
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
]


def find_font_path():
    for p in FONT_CANDIDATES:
        if p and Path(p).exists():
            return p
    raise SystemExit(
        "한글 폰트를 찾지 못했다. FONT_PATH 환경변수로 .ttf/.ttc 경로를 지정하라."
    )


def slugify(stem: str) -> str:
    """ASCII 슬러그 + 짧은 해시(한글 파일명 충돌 방지)."""
    ascii_part = re.sub(r"[^a-zA-Z0-9_-]+", "-", stem).strip("-").lower()
    short = hashlib.md5(stem.encode("utf-8")).hexdigest()[:8]
    return f"{ascii_part}-{short}" if ascii_part else short


def parse_front_matter(text: str):
    """(title, featured_value, fm_start, fm_end) 반환.
    front matter 없으면 title=None. featuredImage 없으면 featured_value=None."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, None, None, None
    fm = m.group(1)
    title = None
    featured = None
    for line in fm.splitlines():
        tm = re.match(r"\s*title:\s*(.+?)\s*$", line)
        if tm and title is None:
            title = tm.group(1).strip().strip('"').strip("'")
        fm2 = re.match(r"\s*featuredImage\s*:\s*(.+?)\s*$", line)
        if fm2 and featured is None:
            featured = fm2.group(1).strip().strip('"').strip("'")
    return title, featured, m.start(1), m.end(1)


def wrap_text(draw, text, font, max_width):
    """공백 및 글자 단위로 줄바꿈(한글은 글자 단위 fallback)."""
    lines, cur = [], ""
    tokens = re.findall(r"\S+\s*", text)
    for tok in tokens:
        trial = cur + tok
        if draw.textlength(trial, font=font) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur.rstrip())
            cur = tok
    if cur.strip():
        lines.append(cur.rstrip())
    # 한 토큰이 너무 길면 글자 단위로 강제 분할
    out = []
    for ln in lines:
        if draw.textlength(ln, font=font) <= max_width:
            out.append(ln)
            continue
        buf = ""
        for ch in ln:
            if draw.textlength(buf + ch, font=font) <= max_width or not buf:
                buf += ch
            else:
                out.append(buf)
                buf = ch
        if buf:
            out.append(buf)
    return out


def render_banner(title: str, out_path: Path, font_path: str):
    img = Image.new("RGB", (W, H), BG_TOP)
    draw = ImageDraw.Draw(img)

    # 세로 그라디언트 배경
    for y in range(H):
        t = y / H
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    pad = 90
    # 왼쪽 초록 액센트 바
    draw.rectangle([pad - 24, pad, pad - 14, H - pad], fill=ACCENT_BAR)

    # 상단 프롬프트 모티프 (브랜드 일관성)
    mono = ImageFont.truetype(font_path, 30)
    draw.text((pad, pad - 6), "ken@blog:~$ ", font=mono, fill=GREEN)
    pw = draw.textlength("ken@blog:~$ ", font=mono)
    draw.text((pad + pw, pad - 6), "cat post.md", font=mono, fill=MUTED)

    # 제목 (길이에 따라 폰트 크기 자동 조정)
    max_w = W - pad * 2
    for size in (74, 66, 58, 50, 44):
        title_font = ImageFont.truetype(font_path, size)
        lines = wrap_text(draw, title, title_font, max_w)
        line_h = int(size * 1.28)
        total_h = line_h * len(lines)
        if len(lines) <= 4 and total_h <= (H - pad * 2 - 120):
            break

    y = pad + 70
    for ln in lines[:4]:
        draw.text((pad, y), ln, font=title_font, fill=TITLE_COLOR)
        y += line_h

    # 하단 블로그 이름
    foot = ImageFont.truetype(font_path, 28)
    draw.text((pad, H - pad - 8), "ken's blog", font=foot, fill=MUTED)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")


def iter_posts():
    for p in sorted(POSTS_DIR.glob("*.md")):
        yield p, p.stem
    for d in sorted(POSTS_DIR.iterdir()):
        idx = d / "index.md"
        if d.is_dir() and idx.exists():
            yield idx, d.name


def main():
    font_path = find_font_path()
    print(f"[banner] font: {font_path}")
    generated = 0

    for md_path, stem in iter_posts():
        text = md_path.read_text(encoding="utf-8")
        title, featured, fm_s, fm_e = parse_front_matter(text)
        if title is None:
            print(f"[skip] front matter 없음: {md_path}")
            continue
        # 사용자가 직접 지정한(우리가 만든 배너가 아닌) 대표 이미지는 존중하고 건너뜀
        if featured is not None and not featured.startswith(BANNER_URL_PREFIX):
            continue

        slug = slugify(stem)
        banner_path = BANNER_DIR / f"{slug}.png"
        # 디자인 변경 반영을 위해 기존 배너도 항상 다시 렌더(overwrite)
        render_banner(title, banner_path, font_path)

        if featured is None:
            # 대표 이미지가 없던 글에만 front matter 삽입
            featured_line = f"featuredImage: {BANNER_URL_PREFIX}/{slug}.png"
            new_text = text[:fm_e] + "\n" + featured_line + text[fm_e:]
            md_path.write_text(new_text, encoding="utf-8")

        generated += 1
        print(f"[gen] {md_path.name} -> {banner_path.relative_to(ROOT)}")

    print(f"[banner] 생성 {generated}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
