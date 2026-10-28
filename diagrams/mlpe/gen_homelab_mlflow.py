"""홈랩 MLflow 실습 플랫폼 구성도 SVG 생성.

mlpe-03 다이어그램과 같은 색·글꼴 체계(종이색 #f5f5f5, 잉크 #2d3142, 강조 #eb6c36, Geist/Geist Mono).
사용: python3 diagrams/mlpe/gen_homelab_mlflow.py <simpleicons 디렉터리>
  디렉터리에는 https://cdn.simpleicons.org/<slug> 로 받은 kubernetes·mlflow·postgresql·jupyter·prometheus .svg 를 둔다.
출력: content/posts/mlpe/mlpe-04-mlflow-install/homelab-mlflow.svg + diagrams/mlpe/homelab-mlflow.html(원본 보기용 래퍼)
아이콘: Simple Icons(CC0) 브랜드 마크, kubernetes/community 리소스 아이콘(Apache-2.0, assets/images/icons/kubernetes).
"""
import re, sys, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path.home() / "myblog"
POST = ROOT / "content/posts/mlpe/mlpe-04-mlflow-install"
SRC = ROOT / "diagrams/mlpe"
SI = Path(sys.argv[1])          # simpleicons dir
K8S = ROOT / "assets/images/icons/kubernetes/icons/resources/unlabeled"
BRAND = {"kubernetes": "#326ce5", "mlflow": "#0194e2", "postgresql": "#4169e1",
         "jupyter": "#f37626", "prometheus": "#e6522c", "helm": "#0f1689"}

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


out = []
P = out.append


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


P(f'<rect width="100%" height="100%" fill="{PAPER}"/>')
boundary(24, 40, 912, 480, "HOME LAN · 192.168.0.0/24", 124)
boundary(208, 72, 704, 428, "HOMELAB · K8S v1.36.5 · CILIUM LB IPAM", 188)
P(icon("kubernetes", 416, 69, 12, bg=True))
boundary(232, 104, 656, 316, "NS · MLFLOW", 64)
boundary(232, 436, 656, 48, "NS · MONITORING", 84)

# arrows first (boxes cover their ends)
arrow("M 152,256 H 224 V 174 H 240")               # PC → Jupyter
arrow("M 152,288 H 224 V 310 H 240")               # PC → RustFS console
arrow("M 96,240 V 88 H 732 V 128")                 # PC → MLflow UI
arrow("M 480,164 H 592")                           # Jupyter → MLflow (REST)
arrow("M 300,212 V 260", accent=True)              # Jupyter → RustFS (S3 direct)
arrow("M 732,212 V 260")                           # MLflow → Postgres
arrow("M 616,212 L 444,262", dashed=True)          # MLflow ⇢ RustFS (artifact root)
arrow("M 864,460 H 876 V 174 H 872", dashed=True)  # Prometheus ⇢ MLflow /metrics

chip(188, 256, 48, "lab :8888")
chip(188, 288, 56, "콘솔 :9001")
chip(420, 88, 88, "MLflow UI :5000")
chip(540, 164, 60, "REST :5000")
chip(540, 182, 100, "run · param · metric")
chip(388, 236, 152, "S3 PUT · 아티팩트 · 데이터셋 CSV", ACCENT)
chip(636, 236, 168, "backend-store-uri postgresql://")
chip(560, 246, 108, "default-artifact-root")

box(40, 240, 112, 64, "PC", "개발 PC", ["브라우저 · kubectl"], kind="pc")
box(248, 136, 232, 76, "NB", "JupyterLab", ["worker1-gpu · PVC jupyter-home 20Gi", "LB 192.168.0.239:8888 · 커널 chapter-4"], mark="jupyter")
box(600, 136, 264, 76, "SRV", "MLflow server 3.16.0", ["helm community-charts/mlflow 1.11.7", "LB 192.168.0.238:5000 · workers 2"], mark="mlflow", tagw=28)
box(248, 268, 232, 84, "S3", "RustFS 1.0.3", ["worker2-arm64 · PVC rustfs-data 20Gi", "LB 192.168.0.237 · :9000 S3 · :9001 콘솔", "버킷 mlflow-artifacts · mlflow-datasets"])
box(600, 268, 264, 84, "DB", "Postgres 18.6", ["worker1-gpu · PVC mlflow-postgres-data 5Gi", "DB mlflow · ClusterIP :5432", "init: dbchecker → mlflow db upgrade"], mark="postgresql")
box(248, 372, 192, 32, "SEC", "rustfs-credentials", [], kind="small", mark="secret", tagw=28)
box(464, 372, 192, 32, "SEC", "mlflow-postgres", [], kind="small", mark="secret", tagw=28)
box(680, 372, 180, 32, "SEC", "jupyter-token", [], kind="small", mark="secret", tagw=28)
box(600, 444, 264, 32, "MON", "Prometheus · ServiceMonitor mlflow", [], kind="small", mark="prometheus", tagw=28)

# legend
P(f'<line x1="40" y1="532" x2="920" y2="532" stroke="rgba(45,49,66,0.10)" stroke-width="0.8"/>')
lx = 40
for sw, txt in [("node", "노드 · 리소스"), ("lb", "LAN 에 노출된 LB IP"), ("acc", "노트북이 S3 에 직접 쓴다"), ("dash", "URI 참조 · 스크레이프"), ("bnd", "경계 (LAN · 클러스터 · ns)")]:
    if sw == "node":
        P(f'<rect x="{lx}" y="542" width="16" height="12" rx="2" fill="#ffffff" stroke="{INK}" stroke-width="1"/>')
    elif sw == "lb":
        P(f'<text x="{lx}" y="552" fill="{ACCENT}" font-size="9" font-family="{MONO}">192.168.0.x</text>')
    elif sw == "acc":
        P(f'<line x1="{lx}" y1="548" x2="{lx+16}" y2="548" stroke="{ACCENT}" stroke-width="1.2" marker-end="url(#arrow-accent)"/>')
    elif sw == "dash":
        P(f'<line x1="{lx}" y1="548" x2="{lx+16}" y2="548" stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="4 3"/>')
    else:
        P(f'<rect x="{lx}" y="542" width="16" height="12" rx="2" fill="rgba(45,49,66,0.02)" stroke="rgba(45,49,66,0.30)" stroke-width="0.8"/>')
    off = 70 if sw == "lb" else 24
    P(f'<text x="{lx+off}" y="552" fill="{MUTED}" font-size="9" font-family="{SANS}">{txt}</text>')
    lx += off + len(txt) * 9 + 28

TITLE = "홈랩 MLflow 실습 플랫폼 구성"
DESC = ("홈 LAN 안의 홈랩 Kubernetes 클러스터 mlflow 네임스페이스에 JupyterLab, MLflow server 3.16.0, Postgres 18.6, RustFS 1.0.3 을 올린 구성. "
        "노트북은 MLflow 서버에 run·파라미터·지표를 REST 로 기록하고 아티팩트와 데이터셋 CSV 는 RustFS 에 S3 로 직접 올린다. "
        "MLflow 서버는 Postgres 를 백엔드 스토어로 쓰고 default-artifact-root 로 RustFS 버킷을 가리킨다. "
        "세 서비스는 Cilium LB IPAM 으로 192.168.0.237~239 에 노출되고, monitoring 네임스페이스의 Prometheus 가 ServiceMonitor 로 /metrics 를 긁는다.")
HEAD = f'''<svg viewBox="0 0 960 560" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="hl-mlflow-title hl-mlflow-desc">
<title id="hl-mlflow-title">{TITLE}</title>
<desc id="hl-mlflow-desc">{DESC}</desc>
<defs>
<style>@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&amp;family=Geist+Mono:wght@400;500;600&amp;display=swap');</style>
<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>
<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker>
</defs>
'''
svg = HEAD + "\n".join(out) + "\n<!-- icons: Simple Icons(CC0) 브랜드 마크 + kubernetes/community 리소스 아이콘(Apache-2.0) -->\n</svg>\n"
(POST / "homelab-mlflow.svg").write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + svg)

html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{TITLE}</title>
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{ --color-paper: #f5f5f5; --color-ink: #2d3142; --color-muted: #4f5d75;
      --font-sans: 'Geist', system-ui, sans-serif; --font-serif: 'Instrument Serif', serif; --font-mono: 'Geist Mono', ui-monospace, monospace; }}
    body {{ font-family: var(--font-sans); background: var(--color-paper); color: var(--color-ink); min-height: 100vh;
      display: flex; align-items: center; justify-content: center; padding: 3rem 2rem; }}
    .frame {{ max-width: 1200px; width: 100%; }}
    .eyebrow {{ font-family: var(--font-mono); font-size: 0.66rem; font-weight: 500; letter-spacing: 0.18em;
      text-transform: uppercase; color: var(--color-muted); margin-bottom: 0.5rem; }}
    h1 {{ font-family: var(--font-serif); font-size: clamp(1.5rem, 2.4vw + 0.75rem, 2rem); font-weight: 400;
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
(SRC / "homelab-mlflow.html").write_text(html)
print("ok", POST / "homelab-mlflow.svg", len(svg))
