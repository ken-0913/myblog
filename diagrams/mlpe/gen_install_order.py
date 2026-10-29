"""홈랩 2주차 플랫폼 설치 순서 구성도 SVG 생성 (gen_homelab_platform.py 와 같은 색·글꼴·도형 체계).

사용: python3 diagrams/mlpe/gen_install_order.py
출력: content/posts/mlpe/mlpe-04-mlflow-install/install-order.svg + diagrams/mlpe/install-order.html(원본 보기용 래퍼)
근거: 홈랩 ~/k8s/{mlflow,feast,kubeflow-pipelines}/scripts/install.sh 의 실행 순서.
아이콘: kubernetes/community 리소스 아이콘(Apache-2.0, assets/images/icons/kubernetes).
"""
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POST = ROOT / "content/posts/mlpe/mlpe-04-mlflow-install"
SRC = ROOT / "diagrams/mlpe"
K8S = ROOT / "assets/images/icons/kubernetes/icons/resources/unlabeled"

INK, MUTED, ACCENT, PAPER = "#2d3142", "#4f5d75", "#eb6c36", "#f5f5f5"
MONO, SANS = "'Geist Mono', monospace", "'Geist', sans-serif"


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


_ICON_N = {}


def icon(kind, x, y, size):
    vb, body = k8s_resource(kind)
    n = _ICON_N[kind] = _ICON_N.get(kind, 0) + 1
    body = body.replace(f'id="k8s-{kind}-', f'id="k8s-{kind}-{n}-')
    return f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="{vb}" aria-hidden="true">{body}</svg>'


out = []


def P(frag):
    out.append(frag)


def boundary(x, y, w, h, label, lw):
    P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="rgba(45,49,66,0.02)" stroke="rgba(45,49,66,0.14)" stroke-width="0.8"/>')
    P(f'<rect x="{x+12}" y="{y-6}" width="{lw}" height="12" rx="2" fill="{PAPER}"/>')
    P(f'<text x="{x+12+lw/2:g}" y="{y+3}" fill="rgba(45,49,66,0.50)" font-size="7" font-family="{MONO}" text-anchor="middle" letter-spacing="0.14em">{label}</text>')


def step(x, y, w, h, tag, title, sub, mark, accent=False):
    stroke = ACCENT if accent else "rgba(45,49,66,0.45)"
    P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#ffffff" stroke="{stroke}" stroke-width="1"/>')
    P(f'<rect x="{x+8}" y="{y+6}" width="16" height="12" rx="2" fill="transparent" stroke="{MUTED}" stroke-opacity="0.45" stroke-width="0.8"/>')
    P(f'<text x="{x+16}" y="{y+15}" fill="{MUTED}" font-size="7" font-family="{MONO}" text-anchor="middle">{tag}</text>')
    P(f'<text x="{x+32}" y="{y+17}" fill="{INK}" font-size="10" font-weight="600" font-family="{SANS}">{title}</text>')
    P(f'<text x="{x+32}" y="{y+33}" fill="{ACCENT if accent else MUTED}" font-size="8" font-family="{MONO}">{sub}</text>')
    P(icon(mark, x + w - 8 - 16, y + (h - 16) / 2, 16))


def chip(cx, cy, w, text, color=MUTED, size=8):
    P(f'<rect x="{cx-w/2:g}" y="{cy-6}" width="{w}" height="12" rx="2" fill="{PAPER}"/>')
    P(f'<text x="{cx:g}" y="{cy+3}" fill="{color}" font-size="{size}" font-family="{MONO}" text-anchor="middle" letter-spacing="0.04em">{text}</text>')


def arrow(d, accent=False, dashed=False):
    col = ACCENT if accent else MUTED
    m = "arrow-accent" if accent else "arrow"
    dash = ' stroke-dasharray="4 3"' if dashed else ""
    P(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="1.2"{dash} marker-end="url(#{m})"/>')


W, H = 960, 496
COLS = [
    (24, "① MLFLOW/SCRIPTS/INSTALL.SH · 10-25", 196, [
        ("1", "Secret 3개 생성", "rustfs-credentials · postgres · jupyter", "secret"),
        ("2", "RustFS", "Deployment · LB .237 · PV 20Gi (Pi)", "deploy"),
        ("3", "버킷 Job", "mlflow-artifacts · mlflow-datasets", "job"),
        ("4", "Postgres 18", "Deployment · PV 5Gi (worker1-gpu)", "deploy"),
        ("5", "MLflow 3.16 (helm)", "community-charts 1.11.7 · LB .238", "deploy"),
        ("6", "JupyterLab", "scipy-notebook · PV 20Gi · LB .239", "deploy"),
    ]),
    (336, "② FEAST/SCRIPTS/INSTALL.SH · 10-26", 192, [
        ("1", "Secret 준비", "redis-auth 생성 · rustfs 계정 복사", "secret"),
        ("2", "Redis 8.10", "StatefulSet · PV 2Gi · requirepass", "sts"),
        ("3", "버킷·parquet Job", "버킷 2개 · GitHub raw parquet 3개", "job"),
        ("4", "ConfigMap feast-repo", "피처 정의 3개 · feast·mlflow 양쪽", "cm"),
        ("5", "feast apply Job", "registry_local.db → feature-registry", "job"),
        ("6", "feast materialize Job", "parquet → Redis 키 30,162개", "job"),
        ("7", "서버 · UI · Jupyter 재기동", "LB .240 · .241 · redis-auth → mlflow", "deploy"),
    ]),
    (648, "③ KUBEFLOW-PIPELINES/SCRIPTS/INSTALL.SH · 10-26", 252, [
        ("1", "cert-manager v1.21.3", "cache-server 웹훅 인증서", "ns"),
        ("2", "클러스터 범위 리소스", "Namespace · KFP CRD 2개 (Argo 제외)", "crd"),
        ("3", "KFP 본체 2.17.3", "번들 Argo 삭제 · amd64 · RustFS 패치", "deploy"),
        ("4", "UI LoadBalancer", "ml-pipeline-ui-lb · LB .242", "svc"),
    ]),
]
CW, BW, BH, PITCH, Y0 = 288, 256, 44, 56, 72


def draw():
    out.clear()
    P(f'<rect width="100%" height="100%" fill="{PAPER}"/>')
    for x, label, lw, steps in COLS:
        boundary(x, 40, CW, 416, label, lw)
        for i, (tag, title, sub, mark) in enumerate(steps):
            y = Y0 + PITCH * i
            if i:
                arrow(f"M {x+CW/2:g},{y-12} V {y-1}")
            step(x + 16, y, BW, BH, tag, title, sub, mark, accent=(mark == "secret"))
    # 디렉터리 사이 순서 화살표 (첫 단계 높이)
    yc = Y0 + BH / 2
    arrow(f"M {24+16+BW},{yc:g} H {336+15}", accent=True)
    arrow(f"M {336+16+BW},{yc:g} H {648+15}", accent=True)
    chip(W / 2, 476, 560, "세 스크립트 모두 멱등 (다시 실행하면 바뀐 것만 적용) · 비밀값은 처음 한 번 무작위 생성해 Secret 에만 저장 · 노드 3대 K8s v1.36.5", size=7)


draw()
TITLE = "홈랩 2주차 플랫폼 설치 순서"
DESC = ("홈랩 저장소의 설치 스크립트 세 개를 mlflow, feast, kubeflow-pipelines 순서로 실행하는 흐름. "
        "① mlflow/scripts/install.sh (10-25): Secret 3개 생성 → RustFS → 버킷 Job → Postgres 18 → MLflow 3.16 (helm) → JupyterLab. "
        "② feast/scripts/install.sh (10-26): redis-auth 생성과 rustfs-credentials 복사 → Redis 8.10 → 버킷·parquet Job → ConfigMap feast-repo → feast apply Job → feast materialize Job → 서버·UI 와 Jupyter 재기동. "
        "③ kubeflow-pipelines/scripts/install.sh (10-26): cert-manager → 클러스터 범위 리소스 → KFP 본체 2.17.3 (번들 Argo 삭제, amd64 고정, 10-28 RustFS 패치) → UI LoadBalancer. "
        "세 스크립트 모두 멱등이고 비밀값은 처음 한 번 무작위로 만들어 Secret 에만 저장한다.")
svg = f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="hl-order-title hl-order-desc">
<title id="hl-order-title">{TITLE}</title>
<desc id="hl-order-desc">{DESC}</desc>
<defs>
<style>@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&amp;family=Geist+Mono:wght@400;500;600&amp;display=swap');</style>
<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>
<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker>
</defs>
''' + "\n".join(out) + "\n<!-- icons: kubernetes/community 리소스 아이콘(Apache-2.0) -->\n</svg>\n"
(POST / "install-order.svg").write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + svg)

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
(SRC / "install-order.html").write_text(html)
print("ok", POST / "install-order.svg", len(svg))
