"""MLPE 4주차(7.3절 메이플스토리 코디 추천) 구성도 SVG 3개 생성.

사용: python3 diagrams/mlpe/gen_ch7_3_diagrams.py
출력:
  content/posts/mlpe/mlpe-07-3-capstone-topics/outfit-service-overview.svg
  content/posts/mlpe/mlpe-07-3-capstone-topics/ch7-structure.svg
  content/posts/mlpe/mlpe-07-3-capstone-topics/outfit-dataprep-dag.svg
  (+ diagrams/mlpe/*.html 미리보기)
"""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POST = ROOT / "content/posts/mlpe/mlpe-07-3-capstone-topics"
SRC = ROOT / "diagrams/mlpe"
K8S = ROOT / "assets/images/icons/kubernetes/icons/resources/unlabeled"
KFP_FLOW = ROOT / "content/posts/mlpe/mlpe-05-1-kfp-income-pipeline/kfp-pipeline-flow.svg"

INK, MUTED, ACCENT, PAPER = "#2d3142", "#4f5d75", "#eb6c36", "#f5f5f5"
MONO, SANS = "'Geist Mono', monospace", "'Geist', sans-serif"

BRAND = {"mlflow": "#0194e2", "rustfs": "#0196d0"}
_ICON_N = {}


def k8s_resource(name):
    root = ET.parse(K8S / f"{name}.svg").getroot()
    vb = root.get("viewBox")
    skip = {"metadata", "namedview", "defs"}

    def ser(el):
        tag = el.tag.split("}")[-1]
        if tag in skip:
            return ""
        attrs = {k.split("}")[-1]: v for k, v in el.attrib.items() if "inkscape" not in k and "sodipodi" not in k}
        if "id" in attrs:
            attrs["id"] = f"k8s-{name}-{attrs['id']}"
        a = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        inner = "".join(ser(c) for c in el)
        return f"<{tag} {a}>{inner}</{tag}>" if inner else f"<{tag} {a}/>"

    return vb, "".join(ser(c) for c in root)


def icon(kind, x, y, size):
    vb, body = k8s_resource(kind)
    n = _ICON_N[kind] = _ICON_N.get(kind, 0) + 1
    body = body.replace(f'id="k8s-{kind}-', f'id="k8s-{kind}-{n}-')
    return f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="{vb}" aria-hidden="true">{body}</svg>'


def simple(name, x, y, w, h, vb="0 0 24 24"):
    src = KFP_FLOW.read_text()
    m = re.search(rf'<path fill="{BRAND[name]}" d="([^"]+)"', src)
    d = m.group(1)
    return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vb}" aria-hidden="true"><path fill="{BRAND[name]}" d="{d}"/></svg>'


out = []


def P(frag):
    out.append(frag)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def boundary(x, y, w, h, label, lw, accent=False):
    stroke = "rgba(235,108,54,0.45)" if accent else "rgba(45,49,66,0.16)"
    fill = "rgba(235,108,54,0.03)" if accent else "rgba(45,49,66,0.02)"
    tcol = ACCENT if accent else "rgba(45,49,66,0.55)"
    P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="{1.0 if accent else 0.8}"/>')
    P(f'<rect x="{x+12}" y="{y-6}" width="{lw}" height="12" rx="2" fill="{PAPER}"/>')
    P(f'<text x="{x+12+lw/2:g}" y="{y+3}" fill="{tcol}" font-size="7" font-family="{MONO}" text-anchor="middle" letter-spacing="0.12em">{esc(label)}</text>')


def box(x, y, w, h, tag, title, lines, kind="node", tagw=None, top=26, right_icon=None, title_size=11):
    styles = {
        "node": ("#ffffff", INK, INK, "1", None),
        "active": ("#ffffff", ACCENT, ACCENT, "1.5", None),
        "store": ("rgba(79,93,117,0.10)", "#7a8399", "#7a8399", "1", None),
        "next": ("#ffffff", "rgba(79,93,117,0.55)", MUTED, "1", "4 3"),
    }
    fill, stroke, tagc, sw, dash = styles[kind]
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{PAPER}"/>')
    P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash_attr}/>')
    if tag:
        tw = tagw or (10 + 5.5 * len(tag))
        P(f'<rect x="{x+8}" y="{y+6}" width="{tw:g}" height="12" rx="2" fill="transparent" stroke="{tagc}" stroke-opacity="0.55" stroke-width="0.8"/>')
        P(f'<text x="{x+8+tw/2:g}" y="{y+15}" fill="{tagc}" font-size="7" font-family="{MONO}" text-anchor="middle" letter-spacing="0.06em">{esc(tag)}</text>')
    if right_icon:
        P(right_icon)
    cx = x + w / 2
    ty = y + top
    P(f'<text x="{cx:g}" y="{ty}" fill="{INK if kind != "next" else MUTED}" font-size="{title_size}" font-weight="600" font-family="{SANS}" text-anchor="middle">{esc(title)}</text>')
    for i, ln in enumerate(lines):
        col = ACCENT if ln.startswith("ACC ") else MUTED
        ln = ln.removeprefix("ACC ")
        P(f'<text x="{cx:g}" y="{ty+15+13*i}" fill="{col}" font-size="8.5" font-family="{MONO}" text-anchor="middle">{esc(ln)}</text>')


def chip(cx, cy, w, text, color=MUTED, size=8, bg=PAPER):
    P(f'<rect x="{cx-w/2:g}" y="{cy-6}" width="{w}" height="12" rx="2" fill="{bg}"/>')
    P(f'<text x="{cx:g}" y="{cy+3}" fill="{color}" font-size="{size}" font-family="{MONO}" text-anchor="middle" letter-spacing="0.02em">{esc(text)}</text>')


def arrow(d, accent=False, dashed=False):
    col = ACCENT if accent else MUTED
    m = "arrow-accent" if accent else "arrow"
    dash = ' stroke-dasharray="4 3"' if dashed else ""
    P(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="1.2"{dash} marker-end="url(#{m})"/>')


def legend(y, items):
    P(f'<line x1="24" y1="{y-12}" x2="936" y2="{y-12}" stroke="rgba(45,49,66,0.10)" stroke-width="0.8"/>')
    lx = 28
    for kind, txt in items:
        if kind == "active":
            P(f'<rect x="{lx}" y="{y-4}" width="16" height="10" rx="2" fill="#ffffff" stroke="{ACCENT}" stroke-width="1.4"/>')
        elif kind == "next":
            P(f'<rect x="{lx}" y="{y-4}" width="16" height="10" rx="2" fill="#ffffff" stroke="rgba(79,93,117,0.65)" stroke-width="1" stroke-dasharray="3 2"/>')
        elif kind == "store":
            P(f'<rect x="{lx}" y="{y-4}" width="16" height="10" rx="2" fill="rgba(79,93,117,0.10)" stroke="#7a8399" stroke-width="1"/>')
        elif kind == "acc":
            P(f'<line x1="{lx}" y1="{y+1}" x2="{lx+16}" y2="{y+1}" stroke="{ACCENT}" stroke-width="1.3" marker-end="url(#arrow-accent)"/>')
        elif kind == "line":
            P(f'<line x1="{lx}" y1="{y+1}" x2="{lx+16}" y2="{y+1}" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#arrow)"/>')
        elif kind == "dash":
            P(f'<line x1="{lx}" y1="{y+1}" x2="{lx+16}" y2="{y+1}" stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="4 3" marker-end="url(#arrow)"/>')
        elif kind == "pod":
            P(icon("pod", lx, y - 7, 16))
        P(f'<text x="{lx+22}" y="{y+4}" fill="{MUTED}" font-size="9" font-family="{SANS}">{esc(txt)}</text>')
        lx += 22 + len(txt) * 8 + 26


def write(name, title, desc, w, h):
    svg = f'''<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{name}-title {name}-desc">
<title id="{name}-title">{esc(title)}</title>
<desc id="{name}-desc">{esc(desc)}</desc>
<defs>
<style>@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&amp;family=Geist+Mono:wght@400;500;600&amp;display=swap');</style>
<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>
<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker>
</defs>
''' + "\n".join(out) + "\n<!-- icons: Simple Icons(CC0), kubernetes/community(Apache-2.0) -->\n</svg>\n"
    (POST / f"{name}.svg").write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + svg)
    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)}</title>
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Geist', system-ui, sans-serif; background: #f5f5f5; color: #2d3142; min-height: 100vh;
      display: flex; align-items: center; justify-content: center; padding: 3rem 2rem; }}
    .frame {{ max-width: 1200px; width: 100%; }}
    .eyebrow {{ font-family: 'Geist Mono', monospace; font-size: 0.66rem; font-weight: 500; letter-spacing: 0.18em;
      text-transform: uppercase; color: #4f5d75; margin-bottom: 0.5rem; }}
    h1 {{ font-family: 'Instrument Serif', serif; font-size: clamp(1.5rem, 2.4vw + 0.75rem, 2rem); font-weight: 400;
      letter-spacing: -0.02em; line-height: 1.15; margin-bottom: 1.5rem; }}
    svg {{ width: 100%; min-width: 960px; display: block; }}
  </style>
</head>
<body>
  <div class="frame">
    <p class="eyebrow">Architecture · MLPE 4주차</p>
    <h1>{esc(title)}</h1>
{svg}  </div>
</body>
</html>
'''
    (SRC / f"{name}.html").write_text(html)
    print("ok", POST / f"{name}.svg")


# ---------------------------------------------------------------- 1. 전체 서비스 흐름
def outfit_service_overview():
    out.clear()
    _ICON_N.clear()
    W, H = 960, 344
    P(f'<rect width="100%" height="100%" fill="{PAPER}"/>')

    boundary(224, 34, 464, 114, "CH7 데이터 준비 (이번 글)", 142, accent=True)
    boundary(704, 34, 234, 248, "CH8 ~ 9 모델 학습·등록 (다음 글)", 172)
    boundary(224, 170, 464, 112, "서비스 뼈대 (이번 글)", 128, accent=True)

    # 화살표 (상자 아래에 깔리게 먼저 그린다)
    arrow("M 202,94 H 244", accent=True)                   # Open API -> 데이터 준비
    arrow("M 442,94 H 484", accent=True)                   # 데이터 준비 -> RustFS
    arrow("M 672,94 H 718")                                # RustFS -> 학습·검증
    arrow("M 821,132 V 190")                               # 학습·검증 -> 모델 레지스트리
    arrow("M 720,228 H 674")                               # 모델 레지스트리 -> 추천 API
    arrow("M 464,228 H 422", accent=True)                  # 추천 API -> 웹 화면
    arrow("M 118,132 V 296 H 568 V 268", dashed=True)      # Open API -> 추천 API (캐릭터 현재 코디)

    chip(223, 80, 32, "수집", ACCENT)
    chip(463, 80, 46, "Parquet", ACCENT)
    chip(695, 80, 38, "학습")
    chip(821, 160, 34, "등록")
    chip(697, 214, 52, "모델 로드")
    chip(443, 214, 48, "JSON", ACCENT)
    chip(340, 296, 134, "실시간 조회 · 캐릭터 현재 코디")

    # 상단 행
    box(34, 58, 168, 72, "SOURCE", "메이플스토리 Open API", ["ranking · id · cash · beauty"], kind="store", top=36)
    box(246, 58, 196, 72, "KFP · CH7", "데이터 준비 파이프라인", ["수집 · 정제 · 분할 · QA"], kind="active", top=36,
        right_icon=icon("pod", 246 + 196 - 24, 64, 16))
    box(486, 58, 186, 72, "S3", "오브젝트 스토리지", ["RustFS · Parquet 5개"], kind="store", top=36,
        right_icon=simple("rustfs", 486 + 186 - 68, 65, 60, 10, vb="0 9.9 24 4.2"))
    box(720, 58, 202, 72, "CH8 ~ 9", "학습 · 검증 파이프라인", ["PyTorch MF · Recall@10"], kind="next", top=36)

    # 하단 행
    box(720, 192, 202, 72, "REGISTRY", "MLflow 모델 레지스트리", ["Production 모델 승격"], kind="next", top=36,
        right_icon=simple("mlflow", 720 + 202 - 24, 198, 16, 16))
    box(464, 192, 208, 72, "GO API", "추천 API (backend)", ["GET /api/outfit/recommend", "ACC 기준선 model.json 장착"], kind="active", top=36,
        right_icon=icon("deploy", 464 + 208 - 24, 198, 16))
    box(240, 192, 180, 72, "VUE UI", "웹 화면 (OutfitPage)", ["가운데 캐릭터 + 슬롯 추천"], kind="active", top=36)

    legend(326, [("active", "이번 글에서 구현 (Ch7 · 서비스 뼈대)"),
                 ("next", "다음 글에서 구현 (Ch8 ~ 9)"),
                 ("store", "외부 API · 스토리지"),
                 ("dash", "실시간 캐릭터 코디 조회")])
    write(
        "outfit-service-overview",
        "메이플스토리 코디 추천 시스템 전체 흐름",
        "메이플스토리 Open API에서 시작해 Ch7 데이터 준비 파이프라인(KFP)과 RustFS(Parquet)를 거쳐 Ch8~9 학습·검증과 MLflow 모델 레지스트리로 이어지고, 추천 API(Go backend)와 웹 화면(Vue)으로 서비스하는 전체 흐름. 이번 글은 Ch7 데이터 준비와 서비스 뼈대(추천 API·웹 화면)를 만들고, 가운데 학습과 레지스트리는 다음 글에서 채운다.",
        W,
        H,
    )


# ---------------------------------------------------------------- 2. Ch7의 구도
def ch7_structure():
    out.clear()
    _ICON_N.clear()
    W, H = 960, 292
    P(f'<rect width="100%" height="100%" fill="{PAPER}"/>')

    boundary(24, 34, 178, 196, "7.1 데이터 분석 (3주차)", 122)
    boundary(238, 34, 202, 196, "7.2 데이터 전달 (3주차)", 122)
    boundary(476, 34, 294, 196, "7.3 데이터 준비 파이프라인 (이번 글)", 172, accent=True)

    # 영역 간 연결 화살표
    arrow("M 202,132 H 236")
    arrow("M 440,132 H 474")
    arrow("M 770,132 H 808", accent=True)

    chip(220, 114, 54, "수집 결정")
    chip(457, 114, 54, "전달 규칙")
    chip(789, 114, 46, "Dataset", ACCENT)

    # 7.1 내부
    box(38, 86, 150, 92, "EDA", "Kubeflow Notebook", ["같은 클러스터", "같은 베이스 이미지", "표본·전처리 탐색"], kind="node", top=38,
        right_icon=icon("pod", 38 + 150 - 24, 92, 16))

    # 7.2 내부
    box(252, 62, 174, 62, "VALUE", "작은 값 (파라미터)", ["반환값 · .output"], kind="node", top=36)
    box(252, 146, 174, 62, "PATH", "큰 데이터 (아티팩트)", ["Output[Dataset].path"], kind="store", top=36)

    # 7.3 내부 (4단계)
    arrow("M 604,93 H 638", accent=True)
    arrow("M 698,124 V 135 H 547 V 144", accent=True)
    arrow("M 604,177 H 638", accent=True)

    box(490, 62, 114, 62, "STEP 1", "다운로드", ["Open API 수집"], kind="active", top=36)
    box(640, 62, 116, 62, "STEP 2", "정제 · 저장", ["Parquet · S3"], kind="active", top=36)
    box(490, 146, 114, 62, "STEP 3", "분할", ["75 / 15 / 10"], kind="active", top=36)
    box(640, 146, 116, 62, "STEP 4", "QA 검사", ["PyArrow · Metrics"], kind="active", top=36)

    # Ch8
    box(810, 86, 126, 92, "NEXT", "Ch8 학습·검증", ["검증 메트릭 출력", "Ch9 레지스트리"], kind="next", top=40)

    legend(272, [("node", "3주차 정리 내용 (7.1 ~ 7.2)"),
                 ("active", "이번 글 핵심 (7.3 파이프라인)"),
                 ("next", "다음 장 입력으로 연결")])
    write(
        "ch7-structure",
        "7장의 구도: 7.1 노트북 탐색, 7.2 전달 규칙, 7.3 데이터 준비 파이프라인",
        "7장은 세 단계로 이어진다. 7.1절 Kubeflow Notebook에서 클러스터·동일 이미지 환경으로 데이터를 탐색해 수집 대상을 정하고, 7.2절에서 작은 값은 파라미터(.output)로, 큰 데이터는 아티팩트 경로(.path)로 넘기는 규칙을 정한다. 7.3절에서는 그 규칙으로 다운로드, 정제·저장, train/val/test 분할, PyArrow QA로 구성된 데이터 준비 파이프라인을 만들어 Ch8 학습·검증으로 넘긴다.",
        W,
        H,
    )


# ---------------------------------------------------------------- 3. 코디 추천 데이터 준비 DAG
def outfit_dataprep_dag():
    out.clear()
    _ICON_N.clear()
    W, H = 960, 468
    P(f'<rect width="100%" height="100%" fill="{PAPER}"/>')

    boundary(24, 34, 912, 314, "KFP PIPELINE · MAPLE-OUTFIT-DATAPREP · 컴포넌트마다 POD 1개", 316)

    # 좌표 그리드 (6열)
    # Col 1: x=40..172 (w=132)
    # Col 2: x=204..336 (w=132)
    # Col 3: x=376..496 (w=120)
    # Col 4: x=524..636 (w=112)
    # Col 5: x=664..788 (w=124)
    # Col 6: x=814..922 (w=108)

    y_top, y_mid, y_bot = 60, 158, 256
    bh = 68

    # 연결선 먼저
    # Col 1: plan_pages -> collect_characters (값 전달: List[int])
    arrow(f"M 106,{y_top+bh} V {y_mid-2}", dashed=True)
    # Secret -> plan_pages, collect_characters
    arrow(f"M 172,{y_bot+34} H 184 V {y_top+34} H 174", dashed=True)
    arrow(f"M 106,{y_bot} V {y_mid+bh+2}", dashed=True)

    # Col 1 -> Col 2: collect_characters -> build_interactions (raw Dataset)
    arrow(f"M 172,{y_mid+34} H 202")

    # Col 2 -> Col 3: build_interactions -> 3x csv_to_parquet
    arrow(f"M 336,{y_mid+22} H 356 V {y_top+34} H 374")
    arrow(f"M 336,{y_mid+34} H 374")
    arrow(f"M 336,{y_mid+46} H 356 V {y_bot+34} H 374")

    # Col 3 -> Col 4/5
    arrow(f"M 496,{y_top+34} H 522")          # P1 -> split_dataset
    arrow(f"M 636,{y_top+34} H 662")          # split_dataset -> U1
    arrow(f"M 496,{y_mid+34} H 662")          # P2 -> U2 (직선 통과)
    arrow(f"M 496,{y_bot+34} H 662")          # P3 -> U3 (직선 통과)

    # Col 5 -> Col 6: 3x upload_to_s3 -> qa_data (의존성: s3 URI)
    arrow(f"M 788,{y_top+34} H 800 V {y_mid+22} H 812", dashed=True)
    arrow(f"M 788,{y_mid+34} H 812", dashed=True)
    arrow(f"M 788,{y_bot+34} H 800 V {y_mid+46} H 812", dashed=True)

    # Col 5/6 <-> RustFS
    arrow(f"M 726,{y_bot+bh} V 364", accent=True)        # upload_to_s3 -> RustFS 쓰기
    arrow(f"M 868,366 V {y_mid+bh+2}", dashed=True)      # RustFS -> qa_data 직접 읽기

    # 라벨 칩
    chip(106, 143, 56, "List[int]")
    chip(188, 178, 28, "raw")
    chip(356, 76, 64, "interactions")
    chip(356, 178, 52, "characters")
    chip(356, 276, 36, "items")
    chip(649, 76, 36, "splits")
    chip(726, 344, 62, "Parquet 5개", ACCENT)
    chip(868, 304, 68, "PyArrow 읽기")

    # Col 1
    box(40, y_top, 132, bh, "POD 1", "plan_pages", ["레벨 10구간 층화"], kind="node", tagw=34, top=34,
        right_icon=icon("pod", 40 + 132 - 22, y_top + 5, 15))
    box(40, y_mid, 132, bh, "POD 2", "collect_characters", ["Open API ×16"], kind="node", tagw=34, top=34, title_size=10,
        right_icon=icon("pod", 40 + 132 - 22, y_mid + 5, 15))
    box(40, y_bot, 132, bh, "SECRET", "nexon-api-key", ["env: NEXON_API_KEY"], kind="store", tagw=38, top=34,
        right_icon=icon("secret", 40 + 132 - 22, y_bot + 5, 15))

    # Col 2
    box(204, y_mid, 132, bh, "POD 3", "build_interactions", ["프리셋·투명템 정제", "CSV 3개 출력"], kind="active", tagw=34, top=34, title_size=10,
        right_icon=icon("pod", 204 + 132 - 22, y_mid + 5, 15))

    # Col 3: 3x csv_to_parquet
    for y, tag, sub in [(y_top, "POD 4a", "interactions.parquet"),
                        (y_mid, "POD 4b", "characters.parquet"),
                        (y_bot, "POD 4c", "items.parquet")]:
        box(376, y, 120, bh, tag, "csv_to_parquet", [sub], kind="node", tagw=38, top=34, title_size=10,
            right_icon=icon("pod", 376 + 120 - 22, y + 5, 15))

    # Col 4: split_dataset
    box(524, y_top, 112, bh, "POD 5", "split_dataset", ["75 / 15 / 10"], kind="node", tagw=34, top=34, title_size=10,
        right_icon=icon("pod", 524 + 112 - 22, y_top + 5, 15))

    # Col 5: 3x upload_to_s3
    for y, tag, sub in [(y_top, "POD 6a", "splits/*.parquet"),
                        (y_mid, "POD 6b", "characters.parquet"),
                        (y_bot, "POD 6c", "items.parquet")]:
        box(664, y, 124, bh, tag, "upload_to_s3", [sub], kind="node", tagw=38, top=34, title_size=10,
            right_icon=icon("pod", 664 + 124 - 22, y + 5, 15))

    # Col 6: qa_data
    box(814, y_mid, 108, bh, "POD 7", "qa_data", ["5개 항목 검사", "ACC Output[Metrics]"], kind="active", tagw=34, top=34, title_size=10.5,
        right_icon=icon("pod", 814 + 108 - 22, y_mid + 5, 15))

    # 하단 RustFS
    box(24, 366, 912, 54, "S3 · SECRET rustfs-credentials", "RustFS · s3://maple-capstone/outfit/v1",
        ["splits/{train,val,test}.parquet  |  characters.parquet  |  items.parquet"], kind="store", tagw=148, top=34,
        right_icon=simple("rustfs", 24 + 912 - 70, 373, 60, 10, vb="0 9.9 24 4.2"))

    legend(452, [("pod", "KFP 컴포넌트 Pod"),
                 ("active", "핵심 정제·QA 단계"),
                 ("line", "Output[Dataset] 아티팩트 전달"),
                 ("dash", "파라미터(값) · Secret · 직접 읽기"),
                 ("acc", "Parquet 업로드")])
    write(
        "outfit-dataprep-dag",
        "코디 추천 데이터 준비 파이프라인 DAG (maple-outfit-dataprep)",
        "KFP 파이프라인 maple-outfit-dataprep 의 실행 흐름. plan_pages 가 레벨 10구간을 층화 샘플링해 페이지 번호 목록(List[int])을 collect_characters 로 넘기고, 두 컴포넌트는 Secret nexon-api-key 를 환경변수로 주입받는다. collect_characters 가 수집한 원본 JSONL(raw)을 build_interactions 가 활성 프리셋·뷰티 정제 규칙으로 CSV 3개(interactions, characters, items)로 펼친다. 세 CSV 는 병렬 csv_to_parquet 컴포넌트 3개를 거쳐 Parquet 로 바뀌고, interactions 만 split_dataset 에서 75/15/10 으로 분할된 뒤 upload_to_s3 3개가 RustFS 버킷 maple-capstone/outfit/v1 에 올린다. 마지막으로 qa_data 가 RustFS 에서 5개 Parquet 파일을 PyArrow 로 직접 읽어 스키마·결측·비율·참조 무결성을 검사하고 Metrics 를 기록한다.",
        W,
        H,
    )


if __name__ == "__main__":
    outfit_service_overview()
    ch7_structure()
    outfit_dataprep_dag()
