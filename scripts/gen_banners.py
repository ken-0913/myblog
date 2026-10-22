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
# 사이트 색 체계(assets/css/_custom.scss 의 --sat: 0, 무채색)와 같은 연한 회색 대각 그라디언트 + 진회색 글자.
# 왼쪽 ~60% 에 제목을 두고 오른쪽에 Kubernetes 공식 로고(조타륜)를 희미하게 넣는다.
# 홈 목록 카드는 배너의 오른쪽(장식 영역)만 잘라 쓴다(layouts/summary.html 의 "fill ... Right").
BG_FROM = (243, 244, 246)      # #f3f4f6 왼쪽 위(아주 연한 회색)
BG_TO = (219, 222, 228)        # #dbdee4 오른쪽 아래(조금 진한 회색)
TITLE_COLOR = (38, 41, 48)     # #262930 제목(진회색)
PROMPT = (84, 90, 102)         # 프롬프트 모티프(중간 회색)
MUTED = (110, 116, 128)        # 보조 텍스트
DOT = (38, 41, 48, 14)         # 점 무늬(진회색 5%)
INK = (38, 41, 48)             # 로고 먹색(진회색). 투명도는 LOGO_ALPHA
LOGO_ALPHA = 0.14              # 로고 최대 불투명도
LOGO_PATH = ROOT / "assets" / "images" / "icons" / "kubernetes" / "logo" / "logo.png"
LOGO_SIZE = 440                # 로고 한 변(px). 오른쪽 장식 영역(x >= 700) 안에 들어간다
TITLE_MAX_W = 600              # 제목 영역 폭(오른쪽 장식 영역을 남긴다. summary.html 의 세로 크롭과 겹치지 않게)

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


def gradient_background() -> Image.Image:
    """왼쪽 위 → 오른쪽 아래 대각 그라디언트. 작은 이미지를 만들어 키우면 픽셀 루프 없이 빠르다."""
    small_w, small_h = 120, 63
    small = Image.new("RGB", (small_w, small_h))
    px = small.load()
    for y in range(small_h):
        for x in range(small_w):
            t = (x / small_w * 0.65) + (y / small_h * 0.35)
            px[x, y] = tuple(int(BG_FROM[i] + (BG_TO[i] - BG_FROM[i]) * t) for i in range(3))
    return small.resize((W, H), Image.BICUBIC)


def render_banner(title: str, out_path: Path, font_path: str):
    img = gradient_background().convert("RGBA")

    # 점 무늬는 반투명 레이어에 그려서 합성한다.
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    step = 28
    for y in range(step // 2, H, step):
        for x in range(step // 2, W, step):
            od.ellipse([x - 1, y - 1, x + 1, y + 1], fill=DOT)

    # Kubernetes 로고: 파란 면은 먹색으로, 흰 조타륜 살은 투명하게 바꿔 단색 워터마크로 만든다.
    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGBA").resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
        lum = logo.convert("L")                                   # 흰색 255, 파랑 약 100
        ink_mask = Image.eval(lum, lambda v: 255 - v)            # 파랑 → 진하게, 흰색 → 0
        alpha = logo.getchannel("A")
        from PIL import ImageChops
        mask = ImageChops.multiply(ink_mask, alpha).point(lambda v: int(v * LOGO_ALPHA))
        tinted = Image.new("RGBA", logo.size, INK + (0,))
        tinted.putalpha(mask)
        lx = W - LOGO_SIZE - 60
        ly = (H - LOGO_SIZE) // 2
        overlay.alpha_composite(tinted, (lx, ly))

    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    pad = 90
    # 상단 프롬프트 모티프 (브랜드 일관성)
    mono = ImageFont.truetype(font_path, 30)
    draw.text((pad, pad - 6), "ken@blog:~$ ", font=mono, fill=PROMPT)
    pw = draw.textlength("ken@blog:~$ ", font=mono)
    draw.text((pad + pw, pad - 6), "cat post.md", font=mono, fill=MUTED)

    # 제목 (길이에 따라 폰트 크기 자동 조정). 오른쪽 장식 영역을 남기기 위해 폭을 제한한다.
    max_w = TITLE_MAX_W
    for size in (70, 62, 54, 48, 42):
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
    img.convert("RGB").save(out_path, "PNG")


def iter_posts():
    # 하위 폴더(섹션)까지 재귀 순회한다.
    #   - <섹션>/<글>.md  : 일반 글 → stem 이 slug
    #   - <폴더>/index.md : 페이지 번들 → 폴더명이 slug
    #   - _index.md       : 섹션 목록 페이지 → 배너 대상 아님(제외)
    for p in sorted(POSTS_DIR.rglob("*.md")):
        if p.name == "_index.md":
            continue
        if p.name == "index.md":
            yield p, p.parent.name
        else:
            yield p, p.stem


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
