"""홈랩 2주차 MLOps 플랫폼 전체 구성도 SVG 생성 (gen_homelab_mlflow.py / gen_homelab_feast.py 와 같은 색·글꼴·도형 체계).

사용: python3 diagrams/mlpe/gen_homelab_platform.py
  브랜드 아이콘(kubernetes·mlflow·postgresql·jupyter·redis)은 이미 생성된 homelab-mlflow.svg / homelab-feast.svg 에서 꺼내 쓰므로
  simpleicons 디렉터리가 따로 필요 없다.
출력: content/posts/mlpe/mlpe-04-mlflow-install/homelab-platform.svg + diagrams/mlpe/homelab-platform.html(원본 보기용 래퍼)
근거: 홈랩 ~/k8s/{mlflow,feast,kubeflow-pipelines} 매니페스트와 2026-10-28 클러스터 상태 (ADR-045, 046, 047, 051).
아이콘: Simple Icons(CC0) 브랜드 마크, kubernetes/community 리소스 아이콘(Apache-2.0, assets/images/icons/kubernetes).
"""
import re, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POST = ROOT / "content/posts/mlpe/mlpe-04-mlflow-install"
SRC = ROOT / "diagrams/mlpe"
K8S = ROOT / "assets/images/icons/kubernetes/icons/resources/unlabeled"
BRAND = {"kubernetes": "#326ce5", "mlflow": "#0194e2", "postgresql": "#4169e1", "jupyter": "#f37626", "redis": "#ff4438"}

INK, MUTED, ACCENT, PAPER = "#2d3142", "#4f5d75", "#eb6c36", "#f5f5f5"
MONO, SANS = "'Geist Mono', monospace", "'Geist', sans-serif"

# 기존 구성도에 들어 있는 브랜드 아이콘 path 를 색으로 찾아 재사용한다
_PATHS = {}
for f in (POST / "homelab-mlflow.svg", ROOT / "content/posts/mlpe/mlpe-04-mlflow-feast/homelab-feast.svg"):
    for col, d in re.findall(r'viewBox="0 0 24 24"[^>]*><path fill="(#[0-9a-f]{6})" d="([^"]+)"', f.read_text()):
        _PATHS.setdefault(col, d)
for name, col in BRAND.items():
    assert col in _PATHS, f"{name} 아이콘을 기존 svg 에서 찾지 못함"


def simple(name):
    return ("0 0 24 24", f'<path fill="{BRAND[name]}" d="{_PATHS[BRAND[name]]}"/>')


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


out = []


def P(frag):
    out.append(frag)


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


W, H = 960, 752


def draw():
    out.clear()
    P(f'<rect width="100%" height="100%" fill="{PAPER}"/>')
    boundary(24, 40, 912, 664, "HOME LAN · 192.168.0.0/24", 124)
    boundary(208, 72, 704, 616, "HOMELAB · K8S v1.36.5 · CILIUM LB IPAM", 188)
    P(icon("kubernetes", 416, 69, 12, bg=True))
    boundary(232, 104, 656, 224, "NS · MLFLOW · 4장", 92)
    boundary(232, 360, 320, 216, "NS · FEAST", 64)
    boundary(576, 360, 312, 216, "NS · KUBEFLOW · 5장 · amd64", 148)
    boundary(232, 600, 656, 72, "NS · ARGO (기존) · CERT-MANAGER · 공용", 212)

    # 화살표 먼저 (상자가 끝을 덮는다)
    arrow("M 96,120 V 88 H 336 V 136")                       # 클라이언트 → Jupyter
    arrow("M 96,120 V 88 H 528 V 136")                       # 클라이언트 → MLflow UI
    arrow("M 96,120 V 88 H 900 V 420 H 872")                 # 클라이언트 → KFP UI (SDK 도 같은 주소)
    arrow("M 96,196 V 440 H 248")                            # 클라이언트 → Feast 서버·UI
    arrow("M 424,168 H 440")                                 # Jupyter → MLflow (run, 지표)
    arrow("M 616,168 H 640")                                 # MLflow → Postgres
    arrow("M 336,200 V 224", accent=True)                    # Jupyter → RustFS (S3 아티팩트)
    arrow("M 500,200 V 224", dashed=True)                    # MLflow ⇢ RustFS (artifact root)
    arrow("M 468,392 V 316", accent=True)                    # Feast Job → RustFS (parquet, 레지스트리)
    arrow("M 360,392 V 316", dashed=True)                    # Feast 서버 ⇢ RustFS (레지스트리)
    arrow("M 468,448 V 480", accent=True)                    # materialize → Redis
    arrow("M 400,488 H 408")                                 # Feast 서버 → Redis
    arrow("M 592,496 H 568 V 200")                           # 실행 Pod → MLflow (Production 모델)
    arrow("M 592,512 H 560 V 270 H 540", accent=True)        # 실행 Pod → RustFS (Dataset, 로그, parquet)
    arrow("M 808,448 V 472")                                 # API → MySQL
    arrow("M 736,616 V 448", dashed=True)                    # cert-manager ⇢ cache-server TLS
    arrow("M 864,448 V 460 H 880 V 680 H 356 V 660")         # API → Argo (Workflow 생성)
    arrow("M 400,616 V 590 H 656 V 548")                     # Argo → 실행 Pod 생성

    chip(230, 88, 72, "브라우저")
    chip(714, 88, 112, "KFP UI · SDK")
    chip(172, 440, 96, "피처 서버 · UI")
    chip(432, 126, 64, "run · 지표")
    chip(628, 126, 72, "backend DB")
    chip(336, 212, 72, "S3 아티팩트", ACCENT)
    chip(500, 212, 80, "artifact root")
    chip(468, 344, 104, "parquet · 레지스트리", ACCENT)
    chip(360, 344, 72, "레지스트리")
    chip(468, 464, 64, "30,162 키", ACCENT)
    chip(568, 344, 96, "Production 모델")
    chip(560, 460, 84, "Dataset · 로그", ACCENT)
    chip(736, 588, 96, "cache-server TLS")
    chip(864, 588, 80, "Workflow 생성")
    chip(520, 590, 60, "Pod 생성")

    box(40, 120, 112, 76, "PC", "클라이언트", ["브라우저 · curl", "KFP SDK (rocky)"], kind="pc")
    box(248, 136, 176, 64, "NB", "JupyterLab", ["LB 192.168.0.239:8888", "커널 chapter-4 · Feast SDK"], mark="jupyter")
    box(440, 136, 176, 64, "SVR", "MLflow 3.16.0", ["LB 192.168.0.238:5000", "추적 서버 · 레지스트리 · UI"], mark="mlflow", tagw=28)
    box(640, 136, 104, 64, "DB", "Postgres 18", ["백엔드 스토어", "PVC 5Gi"], mark="postgresql", tagw=20)
    box(760, 136, 112, 64, "SEC", "Secret 4개", ["rustfs-credentials", "mlflow-postgres · 외"], kind="small", mark="secret", tagw=28)
    box(248, 224, 292, 92, "S3", "RustFS 1.0.3", ["LB 192.168.0.237:9000 · worker2-arm64", "mlflow-artifacts · mlflow-datasets",
                                                  "feature-data-sets · feature-registry", "inference-datasets · mlpipeline"])
    box(248, 392, 152, 104, "SRV", "Feast 서버 · UI", ["feast serve · feast ui", "LB 192.168.0.240:6566", "LB 192.168.0.241:8080", "Deployment 0.67.0"], mark="deploy", tagw=28)
    box(408, 392, 120, 56, "JOB", "Feast Job", ["apply · materialize"], kind="small", mark="job", tagw=28)
    box(408, 480, 120, 56, "ONL", "Redis 8.10.2", ["온라인 스토어 · 2Gi"], mark="redis", tagw=28)
    box(592, 392, 280, 56, "KFP", "ml-pipeline UI · API 2.17.3", ["LB 192.168.0.242 · UI 가 /apis 프록시 · cache · MLMD"], mark="deploy", tagw=28)
    box(592, 472, 128, 76, "RUN", "실행 Pod", ["driver · launcher", "컴포넌트 4개", "python:3.13-slim"], mark="pod", tagw=28)
    box(744, 472, 128, 56, "DB", "MySQL 8.4", ["메타데이터 · PVC 20Gi"], mark="deploy", tagw=20)
    box(248, 616, 216, 44, "ARGO", "workflow-controller v4.1.4", ["ns argo · 전체 네임스페이스 감시"], kind="small", tagw=34)
    box(656, 616, 216, 44, "TLS", "cert-manager v1.21.3", ["ns cert-manager · cache-server 인증서"], kind="small", tagw=28)

    P(f'<line x1="40" y1="716" x2="920" y2="716" stroke="rgba(45,49,66,0.10)" stroke-width="0.8"/>')
    lx = 40
    for sw, txt in [("node", "Pod · 리소스"), ("lb", "LAN 에 노출된 LB IP"), ("acc", "데이터 · 아티팩트가 RustFS 와 Redis 로 가는 길"), ("dash", "설정 참조 · 인증서"), ("bnd", "경계 (LAN · 클러스터 · ns)")]:
        if sw == "node":
            P(f'<rect x="{lx}" y="726" width="16" height="12" rx="2" fill="#ffffff" stroke="{INK}" stroke-width="1"/>')
        elif sw == "lb":
            P(f'<text x="{lx}" y="736" fill="{ACCENT}" font-size="9" font-family="{MONO}">192.168.0.x</text>')
        elif sw == "acc":
            P(f'<line x1="{lx}" y1="732" x2="{lx+16}" y2="732" stroke="{ACCENT}" stroke-width="1.2" marker-end="url(#arrow-accent)"/>')
        elif sw == "dash":
            P(f'<line x1="{lx}" y1="732" x2="{lx+16}" y2="732" stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="4 3"/>')
        else:
            P(f'<rect x="{lx}" y="726" width="16" height="12" rx="2" fill="rgba(45,49,66,0.02)" stroke="rgba(45,49,66,0.30)" stroke-width="0.8"/>')
        off = 70 if sw == "lb" else 24
        P(f'<text x="{lx+off}" y="736" fill="{MUTED}" font-size="9" font-family="{SANS}">{txt}</text>')
        lx += off + len(txt) * 7 + 22


TITLE = "홈랩 2주차 MLOps 플랫폼 전체 구성"
DESC = ("홈 LAN 안의 홈랩 Kubernetes 클러스터(v1.36.5)에 올린 2주차 실습 플랫폼. mlflow 네임스페이스에 JupyterLab(192.168.0.239), MLflow 3.16.0(192.168.0.238), "
        "Postgres 18, Secret 4개, RustFS 1.0.3(192.168.0.237, 버킷 6개: mlflow-artifacts, mlflow-datasets, feature-data-sets, feature-registry, inference-datasets, mlpipeline)이 있고, "
        "feast 네임스페이스에 Feast 서버·UI(192.168.0.240:6566, 192.168.0.241:8080), apply·materialize Job, Redis 8.10.2 가, kubeflow 네임스페이스에 ml-pipeline UI·API 2.17.3(192.168.0.242), 실행 Pod, MySQL 8.4 가 있다. "
        "기존 argo 네임스페이스의 workflow-controller v4.1.4 가 KFP Workflow 를 받아 실행 Pod 를 만들고, cert-manager 가 cache-server 인증서를 준다. "
        "노트북은 MLflow 에 run 과 지표를, RustFS 에 아티팩트를 직접 올리고, Feast Job 은 RustFS 에 parquet 와 레지스트리를, Redis 에 키 30,162개를 쓴다. "
        "KFP 실행 Pod 는 MLflow 에서 Production 모델을 받고 RustFS 에 Dataset 과 로그를 쓴다. 객체 스토리지는 RustFS 하나뿐이다.")

draw()
svg = f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="hl-platform-title hl-platform-desc">
<title id="hl-platform-title">{TITLE}</title>
<desc id="hl-platform-desc">{DESC}</desc>
<defs>
<style>@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&amp;family=Geist+Mono:wght@400;500;600&amp;display=swap');</style>
<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>
<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker>
</defs>
''' + "\n".join(out) + "\n<!-- icons: Simple Icons(CC0) 브랜드 마크 + kubernetes/community 리소스 아이콘(Apache-2.0) -->\n</svg>\n"
(POST / "homelab-platform.svg").write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + svg)

html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{TITLE}</title>
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
    <p class="eyebrow">Architecture · MLPE</p>
    <h1>{TITLE}</h1>
{svg}  </div>
</body>
</html>
'''
(SRC / "homelab-platform.html").write_text(html)
print("ok", POST / "homelab-platform.svg", len(svg))
