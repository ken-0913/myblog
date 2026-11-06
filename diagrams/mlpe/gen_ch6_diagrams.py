"""MLPE 3주차(6장) 구성도 SVG 2개 생성 (gen_install_order.py 와 같은 색·글꼴·도형 체계).

사용: python3 diagrams/mlpe/gen_ch6_diagrams.py
출력:
  content/posts/mlpe/mlpe-06-1-bentoml-yatai/bentoml-deploy-flow.svg  (+ diagrams/mlpe/bentoml-deploy-flow.html)
  content/posts/mlpe/mlpe-06-2-evidently-drift/drift-pipeline.svg      (+ diagrams/mlpe/drift-pipeline.html)
근거: 책 6장 그림 6.2, 6.19 와 홈랩(K8s v1.36.5, Yatai 1.1.13, KFP 2.17.3) 실행 결과 (2026-11-06).
아이콘: kubernetes/community 리소스 아이콘(Apache-2.0, assets/images/icons/kubernetes).
"""
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POSTS = ROOT / "content/posts/mlpe"
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


def step(x, y, w, h, tag, title, sub, mark=None, accent=False, sub2=None):
    stroke = ACCENT if accent else "rgba(45,49,66,0.45)"
    P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#ffffff" stroke="{stroke}" stroke-width="1"/>')
    tw = 8 + 6 * len(tag)
    P(f'<rect x="{x+8}" y="{y+6}" width="{tw}" height="12" rx="2" fill="transparent" stroke="{MUTED}" stroke-opacity="0.45" stroke-width="0.8"/>')
    P(f'<text x="{x+8+tw/2:g}" y="{y+15}" fill="{MUTED}" font-size="7" font-family="{MONO}" text-anchor="middle">{tag}</text>')
    P(f'<text x="{x+16+tw}" y="{y+17}" fill="{INK}" font-size="10" font-weight="600" font-family="{SANS}">{title}</text>')
    P(f'<text x="{x+12}" y="{y+34}" fill="{ACCENT if accent else MUTED}" font-size="8" font-family="{MONO}">{sub}</text>')
    if sub2:
        P(f'<text x="{x+12}" y="{y+46}" fill="{MUTED}" font-size="8" font-family="{MONO}">{sub2}</text>')
    if mark:
        P(icon(mark, x + w - 8 - 16, y + 6, 16))


def chip(cx, cy, w, text, color=MUTED, size=8):
    P(f'<rect x="{cx-w/2:g}" y="{cy-6}" width="{w}" height="12" rx="2" fill="{PAPER}"/>')
    P(f'<text x="{cx:g}" y="{cy+3}" fill="{color}" font-size="{size}" font-family="{MONO}" text-anchor="middle" letter-spacing="0.04em">{text}</text>')


def arrow(d, accent=False, dashed=False):
    col = ACCENT if accent else MUTED
    m = "arrow-accent" if accent else "arrow"
    dash = ' stroke-dasharray="4 3"' if dashed else ""
    P(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="1.2"{dash} marker-end="url(#{m})"/>')


def legend(y, items):
    P(f'<line x1="40" y1="{y-8}" x2="920" y2="{y-8}" stroke="rgba(45,49,66,0.10)" stroke-width="0.8"/>')
    lx = 40
    for sw, txt in items:
        if sw == "acc":
            P(f'<line x1="{lx}" y1="{y}" x2="{lx+16}" y2="{y}" stroke="{ACCENT}" stroke-width="1.2" marker-end="url(#arrow-accent)"/>')
        elif sw == "line":
            P(f'<line x1="{lx}" y1="{y}" x2="{lx+16}" y2="{y}" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#arrow)"/>')
        else:
            P(f'<line x1="{lx}" y1="{y}" x2="{lx+16}" y2="{y}" stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="4 3"/>')
        P(f'<text x="{lx+24}" y="{y+3}" fill="{MUTED}" font-size="9" font-family="{SANS}">{txt}</text>')
        lx += 24 + len(txt) * 8 + 30


def write(post, name, title, desc, w, h):
    svg = f'''<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{name}-title {name}-desc">
<title id="{name}-title">{title}</title>
<desc id="{name}-desc">{desc}</desc>
<defs>
<style>@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&amp;family=Geist+Mono:wght@400;500;600&amp;display=swap');</style>
<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>
<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker>
</defs>
''' + "\n".join(out) + "\n<!-- icons: kubernetes/community 리소스 아이콘(Apache-2.0) -->\n</svg>\n"
    (POSTS / post / f"{name}.svg").write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + svg)
    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
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
    <h1>{title}</h1>
{svg}  </div>
</body>
</html>
'''
    (SRC / f"{name}.html").write_text(html)
    print("ok", POSTS / post / f"{name}.svg", len(svg))


# ---------------------------------------------------------------- 1. BentoML · Yatai 배포 흐름
def bentoml_flow():
    out.clear()
    W, H = 960, 470
    P(f'<rect width="100%" height="100%" fill="{PAPER}"/>')
    boundary(24, 40, 236, 368, "ROCKY-LINUX · PY 3.12 VENV", 132)
    boundary(280, 40, 656, 368, "HOMELAB K8S v1.36.5 · YATAI 1.1.13", 184)

    # 화살표 먼저 (상자가 끝을 덮는다)
    arrow("M 296,106 H 246", accent=True)                         # ① MLflow → ② 로컬 스토어
    arrow("M 142,132 V 198")                                       # ② → 로컬 컨테이너
    arrow("M 244,124 H 268 V 226 H 294", accent=True)              # ② → ③ Yatai (push)
    arrow("M 496,226 H 518")                                       # ③ → ④ BentoRequest
    arrow("M 720,226 H 742", accent=True)                          # ④ → ⑤ Docker Hub (push)
    arrow("M 832,252 V 318")                                       # ⑤ → ⑥ Bento CRD → BentoDeployment
    arrow("M 744,346 H 722")                                       # ⑥ → API 서버 Pod
    arrow("M 520,346 H 498")                                       # API 서버 → 러너
    arrow("M 790,252 V 286 H 620 V 318", dashed=True)              # 레지스트리 → Pod 이미지 pull

    chip(271, 68, 74, "import_model", ACCENT)
    chip(142, 166, 92, "이미지 빌드 · run")
    chip(282, 176, 74, "bentoml push", ACCENT)
    chip(507, 188, 44, "apply")
    chip(731, 188, 28, "push")
    chip(872, 286, 64, "Bento CRD")
    chip(690, 276, 96, "Docker Hub pull")
    chip(733, 310, 30, "생성")
    chip(509, 310, 36, "추론")

    step(40, 80, 204, 52, "2", "BentoML 로컬 스토어", "모델 38.9MB · skops", "vol", sub2="bentofile_homelab.yaml")
    step(40, 200, 204, 52, "L", "로컬 컨테이너 (시험)", "python:3.12-slim · :3010", "pod", sub2="100명 중 >50K 23명")
    step(296, 80, 200, 52, "1", "MLflow 3.16 레지스트리", "random-forest v2 · Production", "deploy")
    step(296, 200, 200, 52, "3", "Yatai · LB .243", "DB mlflow-postgres/yatai", "deploy", sub2="RustFS yatai 버킷")
    step(520, 200, 200, 52, "4", "BentoRequest → kaniko", "amd64 · 6Gi · 3분 37초", "job", accent=True)
    step(744, 200, 176, 52, "5", "Docker Hub", "hyeonjae0913/yatai-bentos", "vol", sub2="공개 저장소")
    step(744, 320, 176, 52, "6", "BentoDeployment", "ns yatai · 1 + 1", "crd", sub2="SA 로 Secret 읽기")
    step(520, 320, 200, 52, "7", "API 서버 Pod 3/3", "LB .244 · /predict", "pod", sub2="ServiceMonitor → Prometheus")
    step(296, 320, 200, 52, "8", "러너 Pod 2/2", "모델 추론 · worker1-gpu", "pod")

    legend(440, [("acc", "모델·Bento 이동"), ("line", "생성 · 요청"), ("dash", "이미지 pull")])
    write("mlpe-06-1-bentoml-yatai", "bentoml-deploy-flow", "홈랩 BentoML과 Yatai의 배포 흐름",
          "홈랩의 배포 흐름. rocky-linux 의 Python 3.12 venv(BentoML 1.1.10)가 MLflow 3.16 레지스트리의 Production 모델(random-forest v2, skops 38.9MB)을 "
          "bentoml.mlflow.import_model 로 로컬 BentoML 스토어에 가져오고 bentofile_homelab.yaml 로 Bento 를 만든다. 로컬에서는 python:3.12-slim 이미지로 :3010 에 띄워 "
          "사용자 100명 중 >50K 23명을 확인했다. bentoml push 로 Yatai(LB 192.168.0.243, DB 는 mlflow-postgres 의 yatai, 파일은 RustFS yatai 버킷)에 올리고, "
          "BentoRequest 매니페스트를 apply 하면 yatai-image-builder 가 amd64 노드에 kaniko 빌더(제한 6Gi)를 띄워 3분 37초에 이미지를 만들어 Docker Hub hyeonjae0913/yatai-bentos 에 push 한다. "
          "Bento CRD 를 거쳐 BentoDeployment 가 yatai 네임스페이스에 API 서버 Pod(3/3, LB 192.168.0.244, ServiceMonitor)와 러너 Pod(2/2)를 하나씩 만들고, "
          "두 Pod 는 Docker Hub 에서 이미지를 받는다. API 서버는 ServiceAccount 로 Secret 을 읽어 RustFS 키와 Redis 암호를 얻는다.",
          W, H)


# ---------------------------------------------------------------- 2. 드리프트 탐지 KFP 파이프라인
def drift_pipeline():
    out.clear()
    W, H = 960, 410
    P(f'<rect width="100%" height="100%" fill="{PAPER}"/>')
    boundary(24, 40, 912, 212, "KFP 파이프라인 · INCOME-CLASSIFIER-PIPELINE-WITH-DRIFT", 268)

    # 화살표
    arrow("M 200,98 H 218")                                        # fetch → retrieve
    arrow("M 380,98 H 578")                                        # retrieve → infer (data_output)
    arrow("M 740,98 H 758")                                        # infer → write
    arrow("M 340,124 V 170 H 398")                                 # retrieve → drift
    arrow("M 560,184 H 620 V 126", dashed=True)                    # drift → infer (.after)
    arrow("M 290,292 V 232 H 440 V 214")                           # MLflow → drift (reference 위치)
    arrow("M 520,292 V 214")                                       # MinIO → drift (reference CSV)
    arrow("M 560,200 H 700 V 290", accent=True)                    # drift → Evidently (add_report)

    chip(480, 88, 80, "data_output")
    chip(298, 150, 58, "피처 parquet")
    chip(620, 150, 60, ".after()")
    chip(290, 266, 92, "reference 위치")
    chip(520, 266, 80, "reference CSV")
    chip(700, 236, 70, "add_report", ACCENT)

    step(40, 72, 160, 52, "1", "fetch_data", "RustFS entity_df", "pod")
    step(220, 72, 160, 52, "2", "retrieve_features", "Feast historical", "pod")
    step(580, 72, 160, 52, "4", "run_inference", "MLflow 모델 예측", "pod")
    step(760, 72, 160, 52, "5", "write_data", "결과 parquet 업로드", "pod")
    step(400, 158, 160, 52, "3", "detect_drift", "Evidently 0.5 Report", "pod", accent=True)

    step(200, 292, 180, 52, "S", "MLflow 3.16", "Production run 의", "deploy", sub2="reference_features 태그")
    step(420, 292, 200, 52, "S", "RustFS", "reference CSV 30,162행", "sts", sub2="결과 ..._with_drift.parquet")
    step(640, 292, 200, 52, "S", "Evidently UI · LB .245", "income-classifier", "deploy", accent=True, sub2="드리프트 0/8 · 33초")
    P(f'<text x="480" y="372" fill="{ACCENT}" font-size="9" font-family="{MONO}" text-anchor="middle">드리프트가 나도 run_inference 는 돈다 · .after() 는 순서만 묶는다 · 멈추려면 dsl.If 분기</text>')

    legend(392, [("line", "데이터 · 단계 연결"), ("dash", "순서만 (.after)"), ("acc", "리포트 기록")])
    write("mlpe-06-2-evidently-drift", "drift-pipeline", "드리프트 탐지 KFP 파이프라인",
          "income-classifier-pipeline-with-drift 의 다섯 단계. fetch_data 가 RustFS 의 entity_df 를 읽고, retrieve_features 가 Feast historical 피처를 붙인다. "
          "피처 parquet 는 detect_drift 와 run_inference 두 곳으로 간다. detect_drift 는 MLflow 의 Production 모델 run 에서 log_input 으로 남긴 reference 데이터셋 위치를 찾고, "
          "RustFS 에서 reference CSV 를 받아 Evidently 0.5 Report 를 만든 뒤 Evidently UI 의 income-classifier 프로젝트에 add_report 로 스냅숏을 올린다. "
          "run_inference 는 detect_drift 와 .after() 로 순서만 묶여 있어 드리프트가 나도 실행되고, write_data 가 결과를 RustFS 에 쓴다. 멈추려면 dsl.If 분기가 필요하다.",
          W, H)


bentoml_flow()
drift_pipeline()
