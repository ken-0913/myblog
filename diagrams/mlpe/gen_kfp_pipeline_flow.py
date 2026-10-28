"""5장 소득 분류기 배치 추론 파이프라인 흐름도 SVG 생성 (gen_kfp_cluster.py 와 같은 색·글꼴·도형 체계).

사용: python3 diagrams/mlpe/gen_kfp_pipeline_flow.py <아이콘 디렉터리>
  디렉터리에는 https://cdn.simpleicons.org/<slug> 로 받은 mlflow·rustfs .svg 와
  Feast 공식 아이콘 feast_icon-black.png(feast-dev/feast 저장소 infra/website/public/images, Apache-2.0)를 둔다.
출력: content/posts/mlpe/mlpe-05-1-kfp-income-pipeline/kfp-pipeline-flow.svg
근거: 책 Listing 5.1 ~ 5.11 의 컴포넌트 4개와 입출력. 2절 표와 같은 내용을 그림으로 옮긴 것이다.
아이콘: Simple Icons(CC0) 브랜드 마크, Feast 공식 아이콘(Apache-2.0), kubernetes/community 리소스 아이콘(Apache-2.0).
"""
import base64, re, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POST = ROOT / "content/posts/mlpe/mlpe-05-1-kfp-income-pipeline"
K8S = ROOT / "assets/images/icons/kubernetes/icons/resources/unlabeled"
ICONS = Path(sys.argv[1])
BRAND = {"mlflow": "#0194e2", "rustfs": "#0196d0"}

INK, MUTED, ACCENT, PAPER = "#2d3142", "#4f5d75", "#eb6c36", "#f5f5f5"
MONO, SANS = "'Geist Mono', monospace", "'Geist', sans-serif"

out = []


def k8s_resource(name, uid):
    root = ET.parse(K8S / f"{name}.svg").getroot()
    vb = root.get("viewBox")
    skip = {"metadata", "namedview", "defs"}

    def ser(el):
        tag = el.tag.split("}")[-1]
        if tag in skip:
            return ""
        attrs = {k.split("}")[-1]: v for k, v in el.attrib.items() if "inkscape" not in k and "sodipodi" not in k}
        if "id" in attrs:
            attrs["id"] = f"k8s-{name}-{uid}-{attrs['id']}"
        a = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        inner = "".join(ser(c) for c in el)
        return f"<{tag} {a}>{inner}</{tag}>" if inner else f"<{tag} {a}/>"
    return vb, "".join(ser(c) for c in root)


def simple(name, x, y, w, h, vb="0 0 24 24"):
    d = re.search(r'<path d="([^"]+)"', (ICONS / f"{name}.svg").read_text()).group(1)
    return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vb}" aria-hidden="true"><path fill="{BRAND[name]}" d="{d}"/></svg>'


def feast_icon(x, y, size):
    with tempfile.TemporaryDirectory() as tmp:            # 2085px 원본을 96px 로 줄여 넣는다
        small = Path(tmp) / "feast.png"
        subprocess.run(["sips", "-Z", "96", str(ICONS / "feast_icon-black.png"), "--out", str(small)], check=True, capture_output=True)
        b64 = base64.b64encode(small.read_bytes()).decode()
    return f'<image x="{x}" y="{y}" width="{size}" height="{size}" href="data:image/png;base64,{b64}"/>'


def pod_icon(x, y, size, uid):
    vb, body = k8s_resource("pod", uid)
    return f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="{vb}" aria-hidden="true">{body}</svg>'


def P(frag):
    out.append(frag)


def boundary(x, y, w, h, label, lw):
    P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="rgba(45,49,66,0.02)" stroke="rgba(45,49,66,0.14)" stroke-width="0.8"/>')
    P(f'<rect x="{x+12}" y="{y-6}" width="{lw}" height="12" rx="2" fill="{PAPER}"/>')
    P(f'<text x="{x+12+lw/2:g}" y="{y+3}" fill="rgba(45,49,66,0.50)" font-size="7" font-family="{MONO}" text-anchor="middle" letter-spacing="0.14em">{label}</text>')


def box(x, y, w, h, tag, title, lines, kind="node", tagw=24, top=26):
    fill, stroke, tagc = {"node": ("#ffffff", INK, INK),
                          "store": ("rgba(79,93,117,0.10)", "#7a8399", "#7a8399")}[kind]
    P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{PAPER}"/>')
    P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
    if tag:
        P(f'<rect x="{x+8}" y="{y+6}" width="{tagw}" height="12" rx="2" fill="transparent" stroke="{tagc}" stroke-opacity="0.45" stroke-width="0.8"/>')
        P(f'<text x="{x+8+tagw/2:g}" y="{y+15}" fill="{tagc}" font-size="7" font-family="{MONO}" text-anchor="middle" letter-spacing="0.08em">{tag}</text>')
    cx = x + w / 2
    ty = y + top
    P(f'<text x="{cx:g}" y="{ty}" fill="{INK}" font-size="12" font-weight="600" font-family="{SANS}" text-anchor="middle">{title}</text>')
    for i, ln in enumerate(lines):
        col = ACCENT if ln.startswith("LB ") else MUTED
        ln = ln.removeprefix("LB ")
        P(f'<text x="{cx:g}" y="{ty+16+14*i}" fill="{col}" font-size="9" font-family="{MONO}" text-anchor="middle">{ln}</text>')


def chip(cx, cy, w, text, color=MUTED, size=8):
    P(f'<rect x="{cx-w/2:g}" y="{cy-6}" width="{w}" height="12" rx="2" fill="{PAPER}"/>')
    P(f'<text x="{cx:g}" y="{cy+3}" fill="{color}" font-size="{size}" font-family="{MONO}" text-anchor="middle" letter-spacing="0.04em">{text}</text>')


def arrow(d, accent=False, dashed=False):
    col = ACCENT if accent else MUTED
    m = "arrow-accent" if accent else "arrow"
    dash = ' stroke-dasharray="4 3"' if dashed else ""
    P(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="1.2"{dash} marker-end="url(#{m})"/>')


W, H = 960, 436
BW, BH = 180, 80
XS = [48, 280, 512, 744]                 # 컴포넌트 x. 가운데는 x + 90
CY = 176                                 # 컴포넌트 y

P(f'<rect width="100%" height="100%" fill="{PAPER}"/>')
boundary(24, 148, 912, 136, "KFP PIPELINE · income-classifier-pipeline · 컴포넌트마다 Pod 1개", 320)

# arrows first
for x in XS[:-1]:
    arrow(f"M {x+BW},{CY+BH/2:g} H {x+BW+50}")                 # 앞 단계 Dataset → 다음 단계
arrow("M 370,108 V 174", dashed=True)                           # Feast → retrieve_features
arrow("M 602,108 V 174", dashed=True)                           # MLflow → run_inference
arrow("M 138,324 V 258", dashed=True)                           # RustFS → read_data
arrow("M 370,324 V 258", dashed=True)                           # RustFS → retrieve_features (feature_store.yaml)
arrow("M 834,258 V 322", accent=True)                           # write_data → RustFS

for x in XS[:-1]:
    chip(x + BW + 26, CY + BH / 2 - 12, 44, "Dataset")
chip(370, 128, 110, "historical 피처 8개")
chip(602, 128, 150, "Production 모델 · column_list")
chip(138, 304, 104, "entity_df.parquet")
chip(370, 304, 110, "feature_store.yaml")
chip(834, 304, 132, "inference_result.parquet", ACCENT)

box(260, 44, 220, 64, "4.2", "Feast 레지스트리", ["registry_local.db · parquet"], kind="store")
box(492, 44, 220, 64, "4.1", "MLflow 모델 레지스트리", ["random-forest-classifier"], kind="store")
P(feast_icon(260 + 220 - 26, 50, 18))
P(simple("mlflow", 492 + 220 - 26, 50, 18, 18))
for x, tag, name, lines in [(XS[0], "POD 1", "read_data", ["엔티티 목록 읽기", "user_id · event_timestamp"]),
                            (XS[1], "POD 2", "retrieve_features", ["Feast 오프라인 조회", "get_historical_features"]),
                            (XS[2], "POD 3", "run_inference", ["MLflow 모델로 추론", "predict_proba"]),
                            (XS[3], "POD 4", "write_data", ["결과 parquet 업로드", "LB Predicted_Income_Class"])]:
    box(x, CY, BW, BH, tag, name, lines, tagw=34, top=36)
    P(pod_icon(x + BW - 26, CY + 6, 18, tag[-1]))
box(48, 324, 876, 56, "S3", "RustFS",
    ["inference-datasets: entity_df.parquet, inference_result.parquet  |  feature-registry: feature_store.yaml"], kind="store")
P(simple("rustfs", 48 + 876 - 72, 331, 64, 11, vb="0 9.9 24 4.2"))   # 워드마크라 글자 높이만 잘라 쓴다

# legend
P(f'<line x1="40" y1="396" x2="920" y2="396" stroke="rgba(45,49,66,0.10)" stroke-width="0.8"/>')
lx = 40
for sw, txt in [("node", "Pod (KFP 컴포넌트 1개)"), ("store", "저장소 · 레지스트리"), ("line", "단계 사이 Dataset 전달"),
                ("dash", "저장소에서 읽기"), ("acc", "추론 결과 쓰기")]:
    if sw == "node":
        P(pod_icon(lx, 401, 18, "legend"))
    elif sw == "store":
        P(f'<rect x="{lx}" y="404" width="16" height="12" rx="2" fill="rgba(79,93,117,0.10)" stroke="#7a8399" stroke-width="1"/>')
    elif sw == "acc":
        P(f'<line x1="{lx}" y1="410" x2="{lx+16}" y2="410" stroke="{ACCENT}" stroke-width="1.2" marker-end="url(#arrow-accent)"/>')
    elif sw == "line":
        P(f'<line x1="{lx}" y1="410" x2="{lx+16}" y2="410" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#arrow)"/>')
    else:
        P(f'<line x1="{lx}" y1="410" x2="{lx+16}" y2="410" stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="4 3"/>')
    P(f'<text x="{lx+24}" y="414" fill="{MUTED}" font-size="9" font-family="{SANS}">{txt}</text>')
    lx += 24 + len(txt) * 7 + 24

TITLE = "소득 분류기 배치 추론 파이프라인 흐름"
DESC = ("KFP 파이프라인 income-classifier-pipeline 의 컴포넌트 4개가 각각 Pod 하나로 실행되며 차례로 이어진다. read_data 가 RustFS 에서 entity_df.parquet 를 읽고, "
        "retrieve_features 가 RustFS 의 feature_store.yaml 과 4.2절 Feast 레지스트리로 historical 피처 8개를 붙이며, run_inference 가 4.1절 MLflow 레지스트리의 "
        "Production 모델과 column_list 로 predict_proba 를 계산하고, write_data 가 inference_result.parquet 를 RustFS 에 쓴다. 단계 사이에는 Dataset 아티팩트가 전달된다.")
body = "\n".join(out)
svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="kfp-flow-title kfp-flow-desc">
<title id="kfp-flow-title">{TITLE}</title>
<desc id="kfp-flow-desc">{DESC}</desc>
<defs>
<style>@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&amp;family=Geist+Mono:wght@400;500;600&amp;display=swap');</style>
<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>
<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker>
</defs>
{body}
</svg>
'''
(POST / "kfp-pipeline-flow.svg").write_text(svg)
print("ok", POST / "kfp-pipeline-flow.svg")
