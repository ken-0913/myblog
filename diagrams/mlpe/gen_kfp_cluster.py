"""홈랩 KFP 배치 추론 파이프라인 실행 구성도 SVG 생성 (gen_homelab_feast.py 와 같은 색·글꼴·도형 체계).

사용: python3 diagrams/mlpe/gen_kfp_cluster.py <simpleicons 디렉터리>
  디렉터리에는 https://cdn.simpleicons.org/<slug> 로 받은 kubernetes·mlflow .svg 를 둔다.
출력: content/posts/mlpe/mlpe-05-1-kfp-income-pipeline/kfp-cluster.svg
근거: 홈랩 실측(2026-10-28, KFP 2.17.3 standalone, run 52f896e8). 저장소는 RustFS 하나다.
      KFP 아티팩트(단계 사이 Dataset·로그)도 번들 SeaweedFS 대신 RustFS 버킷 mlpipeline 에 둔다(홈랩 ADR-051).
아이콘: Simple Icons(CC0) 브랜드 마크, kubernetes/community 리소스 아이콘(Apache-2.0, assets/images/icons/kubernetes).
"""
import re, sys, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POST = ROOT / "content/posts/mlpe/mlpe-05-1-kfp-income-pipeline"
SI = Path(sys.argv[1])
K8S = ROOT / "assets/images/icons/kubernetes/icons/resources/unlabeled"
BRAND = {"kubernetes": "#326ce5", "mlflow": "#0194e2"}

INK, MUTED, ACCENT, PAPER = "#2d3142", "#4f5d75", "#eb6c36", "#f5f5f5"
MONO, SANS = "'Geist Mono', monospace", "'Geist', sans-serif"
def simple(name):
    d = re.search(r'<path d="([^"]+)"', (SI / f"{name}.svg").read_text()).group(1)
    return ("0 0 24 24", f'<path fill="{BRAND[name]}" d="{d}"/>')


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
    return (vb, "".join(ser(c) for c in root))


def icon(kind, x, y, size, bg=False):
    vb, body = simple(kind) if kind in BRAND else k8s_resource(kind)
    pad = 3
    chip = f'<rect x="{x-pad}" y="{y-pad}" width="{size+2*pad}" height="{size+2*pad}" rx="3" fill="{PAPER}"/>' if bg else ""
    return f'{chip}<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="{vb}" aria-hidden="true">{body}</svg>'


out = []                         # (key, svg 조각). key 가 FOCUS 에 없으면 흐리게 그린다
CUR = ["base"]


def P(frag):
    out.append((CUR[0], frag))


def K(key):
    CUR[0] = key


def boundary(x, y, w, h, label, lw):
    P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="rgba(45,49,66,0.02)" stroke="rgba(45,49,66,0.14)" stroke-width="0.8"/>')
    P(f'<rect x="{x+12}" y="{y-6}" width="{lw}" height="12" rx="2" fill="{PAPER}"/>')
    P(f'<text x="{x+12+lw/2:g}" y="{y+3}" fill="rgba(45,49,66,0.50)" font-size="7" font-family="{MONO}" text-anchor="middle" letter-spacing="0.14em">{label}</text>')


def box(x, y, w, h, tag, title, lines, kind="node", mark=None, tagw=24):
    fill, stroke, tagc = {"node": ("#ffffff", INK, INK),
                          "pc": ("rgba(79,93,117,0.10)", "#7a8399", "#7a8399"),
                          "small": ("#ffffff", "rgba(45,49,66,0.45)", MUTED)}[kind]
    P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{PAPER}"/>')
    P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
    if tag:
        P(f'<rect x="{x+8}" y="{y+6}" width="{tagw}" height="12" rx="2" fill="transparent" stroke="{tagc}" stroke-opacity="0.45" stroke-width="0.8"/>')
        P(f'<text x="{x+8+tagw/2:g}" y="{y+15}" fill="{tagc}" font-size="7" font-family="{MONO}" text-anchor="middle" letter-spacing="0.08em">{tag}</text>')
    cx = x + w / 2
    ty = y + (26 if h >= 64 else 21)
    P(f'<text x="{cx:g}" y="{ty}" fill="{INK}" font-size="{12 if h >= 64 else 10}" font-weight="600" font-family="{SANS}" text-anchor="middle">{title}</text>')
    for i, ln in enumerate(lines):
        col = ACCENT if ln.startswith("LB ") else MUTED
        P(f'<text x="{cx:g}" y="{ty+16+14*i}" fill="{col}" font-size="9" font-family="{MONO}" text-anchor="middle">{ln}</text>')
    if mark:
        size = 18 if h >= 64 else 14
        P(icon(mark, x + w - 8 - size, y + 6, size))


def chip(cx, cy, w, text, color=MUTED, size=8):
    P(f'<rect x="{cx-w/2:g}" y="{cy-6}" width="{w}" height="12" rx="2" fill="{PAPER}"/>')
    P(f'<text x="{cx:g}" y="{cy+3}" fill="{color}" font-size="{size}" font-family="{MONO}" text-anchor="middle" letter-spacing="0.04em">{text}</text>')


def arrow(d, accent=False, dashed=False):
    col = ACCENT if accent else MUTED
    m = "arrow-accent" if accent else "arrow"
    dash = ' stroke-dasharray="4 3"' if dashed else ""
    P(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="1.2"{dash} marker-end="url(#{m})"/>')


W, H = 960, 720
P(f'<rect width="100%" height="100%" fill="{PAPER}"/>')
boundary(24, 40, 912, 648, "HOME LAN · 192.168.0.0/24", 124)
boundary(208, 72, 704, 600, "HOMELAB · K8S v1.36.5 · KFP 2.17.3 STANDALONE", 252)
P(icon("kubernetes", 478, 69, 12, bg=True))
boundary(224, 100, 672, 316, "NS · KUBEFLOW", 72)
boundary(224, 448, 672, 208, "NS · MLFLOW · 4장에서 설치", 136)

# arrows first
arrow("M 152,140 H 236")                                        # PC → KFP
arrow("M 330,208 V 248", dashed=True)                           # KFP → Pod 생성 (Argo)
arrow("M 540,208 V 248", dashed=True)                           # kfp-launcher → Pod (아티팩트 저장 위치)
arrow("M 770,208 V 248", dashed=True)                           # Secret · ConfigMap → Pod
arrow("M 390,282 H 396")                                        # read → retrieve
arrow("M 550,282 H 556")                                        # retrieve → inference
arrow("M 710,282 H 716")                                        # inference → write
arrow("M 315,312 V 538")                                        # read → RustFS
arrow("M 475,312 V 538")                                        # retrieve → RustFS
arrow("M 635,312 V 464")                                        # inference → MLflow
arrow("M 795,312 V 538", accent=True)                           # write → RustFS

chip(194, 128, 76, "UI · SDK")
chip(330, 228, 150, "공유 Argo(argo ns)가 Pod 생성")
chip(540, 228, 100, "아티팩트 저장 위치")
chip(770, 228, 110, "env · /src (4개 Pod)")
chip(315, 432, 100, "entity_df.parquet")
chip(475, 432, 150, "feature_store.yaml · parquet")
chip(635, 432, 104, "Production 모델")
chip(795, 432, 132, "inference_result.parquet", ACCENT)
chip(560, 336, 380, "4개 Pod 모두 python:3.13-slim + 런타임 pip install, 책 코드는 /src 에 마운트", size=7)
chip(560, 350, 380, "단계 사이 Dataset · 로그는 RustFS mlpipeline 버킷 (SeaweedFS 는 replicas 0)", size=7)

box(40, 108, 112, 64, "PC", "브라우저", ["KFP UI · SDK"], kind="pc")
box(240, 124, 180, 84, "KFP", "KFP 2.17.3", ["ml-pipeline UI · API", "MySQL 8.4 (메타데이터)", "LB 192.168.0.242"], tagw=28)
box(440, 124, 200, 84, "CM", "kfp-launcher", ["pipeline root", "minio://mlpipeline/v2/artifacts", "LB → rustfs.mlflow.svc:9000"], mark="cm")
box(660, 124, 220, 36, "SEC", "rustfs-credentials (복사)", [], kind="small", mark="secret", tagw=28)
box(660, 172, 220, 36, "CM", "ch5-src (책 코드 4개)", [], kind="small", mark="cm")
for x, name, sub in [(240, "read-data", "RustFS 에서 entity_df"), (400, "retrieve-features", "Feast 0.67 historical"),
                     (560, "model-inference", "MLflow 3.17 · sklearn"), (720, "write-data", "결과 parquet 업로드")]:
    box(x, 252, 150, 60, None, name, [sub], kind="small")
box(560, 468, 160, 64, "SRV", "MLflow 3.16.0", ["random-forest-classifier v2", "stage Production"], mark="mlflow", tagw=28)
box(240, 540, 640, 106, "S3", "RustFS 1.0.3 · rustfs.mlflow.svc:9000", ["inference-datasets: entity_df.parquet · inference_result.parquet", "feature-registry: feature_store.yaml · registry_local.db (4.2절)", "feature-data-sets: parquet 3개 (4.2절)  ·  mlflow-artifacts: 모델 파일 (4.1절)", "LB mlpipeline: KFP 단계 사이 Dataset · 로그"])

# legend
P(f'<line x1="40" y1="696" x2="920" y2="696" stroke="rgba(45,49,66,0.10)" stroke-width="0.8"/>')
lx = 40
for sw, txt in [("node", "Pod · 리소스"), ("acc", "추론 결과 쓰기"), ("line", "읽기 · 단계 연결"), ("dash", "생성 · 주입 · KFP 아티팩트"), ("bnd", "경계 (LAN · 클러스터 · ns)")]:
    if sw == "node":
        P(f'<rect x="{lx}" y="704" width="16" height="12" rx="2" fill="#ffffff" stroke="{INK}" stroke-width="1"/>')
    elif sw == "acc":
        P(f'<line x1="{lx}" y1="710" x2="{lx+16}" y2="710" stroke="{ACCENT}" stroke-width="1.2" marker-end="url(#arrow-accent)"/>')
    elif sw == "line":
        P(f'<line x1="{lx}" y1="710" x2="{lx+16}" y2="710" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#arrow)"/>')
    elif sw == "dash":
        P(f'<line x1="{lx}" y1="710" x2="{lx+16}" y2="710" stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="4 3"/>')
    else:
        P(f'<rect x="{lx}" y="704" width="16" height="12" rx="2" fill="rgba(45,49,66,0.02)" stroke="rgba(45,49,66,0.30)" stroke-width="0.8"/>')
    P(f'<text x="{lx+24}" y="714" fill="{MUTED}" font-size="9" font-family="{SANS}">{txt}</text>')
    lx += 24 + len(txt) * 7 + 30

TITLE = "홈랩 KFP 배치 추론 파이프라인 실행 구성"
DESC = ("홈랩 Kubernetes 의 KFP 2.17.3 standalone(ns kubeflow)에서 소득 분류기 배치 추론 파이프라인이 도는 모습. 브라우저나 SDK 로 192.168.0.242 의 KFP 에 실행을 만들면 "
        "공유 Argo Workflows 가 kubeflow 네임스페이스에 Pod 4개(read-data, retrieve-features, model-inference, write-data)를 차례로 띄운다. 각 Pod 는 python:3.13-slim 에 패키지를 설치하고 "
        "ConfigMap ch5-src 로 마운트한 책 코드를 실행하며, RustFS 키는 Secret rustfs-credentials 에서 환경변수로 받는다. 단계 사이 Dataset 과 로그는 "
        "ConfigMap kfp-launcher 의 pipeline root 설정에 따라 RustFS 의 mlpipeline 버킷에 저장되고, KFP 번들 SeaweedFS 는 쓰지 않는다. "
        "read-data 는 RustFS inference-datasets 의 entity_df.parquet 를, retrieve-features 는 4.2절 Feast 레지스트리와 parquet 를 읽고, model-inference 는 mlflow 네임스페이스의 MLflow 에서 "
        "Production 단계 random-forest-classifier v2 를 받아 예측하며, write-data 는 inference_result.parquet 를 RustFS 에 쓴다.")
body = "\n".join(f for _, f in out)
svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="kfp-cl-title kfp-cl-desc">
<title id="kfp-cl-title">{TITLE}</title>
<desc id="kfp-cl-desc">{DESC}</desc>
<defs>
<style>@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&amp;family=Geist+Mono:wght@400;500;600&amp;display=swap');</style>
<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>
<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker>
</defs>
{body}
<!-- icons: Simple Icons(CC0) 브랜드 마크 + kubernetes/community 리소스 아이콘(Apache-2.0) -->
</svg>
'''
(POST / "kfp-cluster.svg").write_text(svg)
print("ok", POST / "kfp-cluster.svg")
