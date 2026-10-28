"""홈랩 MLflow 기록 흐름 시퀀스 SVG 생성 (gen_homelab_mlflow.py 와 같은 색·글꼴 체계).

사용: python3 diagrams/mlpe/gen_homelab_mlflow_seq.py <simpleicons 디렉터리>
  디렉터리에는 https://cdn.simpleicons.org/<slug> 로 받은 jupyter·mlflow·postgresql .svg 를 둔다.
출력: content/posts/mlpe/mlpe-04-mlflow-install/homelab-mlflow-seq.svg
근거: 4.1절 노트북 실행 결과(MLflow 3.17.2 클라이언트, 3.16.0 서버). log_model 은 run 아티팩트가 아니라
      logged model(<exp>/models/m-…)에 저장되고, register_model(runs:/…) 은 그 logged model 로 대신 등록된다.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POST = ROOT / "content/posts/mlpe/mlpe-04-mlflow-install"
SI = Path(sys.argv[1])
BRAND = {"jupyter": "#f37626", "mlflow": "#0194e2", "postgresql": "#4169e1"}
INK, MUTED, ACCENT, PAPER = "#2d3142", "#4f5d75", "#eb6c36", "#f5f5f5"
MONO, SANS = "'Geist Mono', monospace", "'Geist', sans-serif"


def icon(name, x, y, size):
    d = re.search(r'<path d="([^"]+)"', (SI / f"{name}.svg").read_text()).group(1)
    return f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 24 24" aria-hidden="true"><path fill="{BRAND[name]}" d="{d}"/></svg>'


out = []
P = out.append

LANES = {"NB": 130, "ML": 390, "PG": 620, "FS": 840}
HEADS = [("NB", "노트북", "chapter-4 커널", "jupyter"), ("ML", "MLflow server", "3.16.0 · REST :5000", "mlflow"),
         ("PG", "Postgres", "백엔드 스토어", "postgresql"), ("FS", "RustFS", "S3 :9000", None)]

# (from, to, label, sub, kind)  kind: meta(회색) / s3(주황, 서버를 거치지 않는 파일)
STEPS = [
    ("NB", "ML", 'set_experiment("income-classifier")', None, "meta"),
    ("ML", "PG", "experiment 생성", "artifact_location s3://mlflow-artifacts/chapter-4/<exp>", "meta"),
    ("NB", "ML", "start_run()", None, "meta"),
    ("ML", "PG", "run 생성", "artifact_uri …/chapter-4/<exp>/<run>/artifacts", "meta"),
    ("NB", "FS", "save_df_to_minio (minio SDK)", "mlflow-datasets/income-classifier-datasets/train-<run>.csv", "s3"),
    ("NB", "ML", "log_input · log_metric · log_params", None, "meta"),
    ("ML", "PG", "기록", None, "meta"),
    ("NB", "FS", "log_artifacts(plots) (boto3)", "mlflow-artifacts/chapter-4/<exp>/<run>/artifacts/", "s3"),
    ("NB", "ML", "log_model: logged model m-… 생성", None, "meta"),
    ("NB", "FS", "MLmodel · model.skops 업로드", "mlflow-artifacts/chapter-4/<exp>/models/m-…/artifacts/", "s3"),
    ("NB", "ML", "register_model(runs:/<run>/income-classifier)", 'name "random-forest-classifier"', "meta"),
    ("ML", "PG", "model version 생성", "source = models:/m-… (run 경로가 비어 logged model 로 대체)", "meta"),
]

TOP, HEAD_H = 24, 56
y0 = TOP + HEAD_H + 28
YS, acc = [], y0
for st in STEPS:
    acc += 18 if st[3] else 0
    YS.append(acc)
    acc += 34
H = acc + 48
W = 960

P(f'<rect width="100%" height="100%" fill="{PAPER}"/>')
# lifelines
for key, x in LANES.items():
    P(f'<line x1="{x}" y1="{TOP+HEAD_H}" x2="{x}" y2="{H-48}" stroke="rgba(45,49,66,0.25)" stroke-width="1" stroke-dasharray="3 3"/>')
# participant heads
for key, title, sub, mark in HEADS:
    x = LANES[key]; w = 168
    P(f'<rect x="{x-w/2}" y="{TOP}" width="{w}" height="{HEAD_H}" rx="6" fill="#ffffff" stroke="{INK}" stroke-width="1"/>')
    P(f'<text x="{x}" y="{TOP+24}" fill="{INK}" font-size="12" font-weight="600" font-family="{SANS}" text-anchor="middle">{title}</text>')
    P(f'<text x="{x}" y="{TOP+42}" fill="{MUTED}" font-size="9" font-family="{MONO}" text-anchor="middle">{sub}</text>')
    if mark:
        P(icon(mark, x + w / 2 - 24, TOP + 7, 16))

for i, (a, b, label, sub, kind) in enumerate(STEPS):
    y = YS[i]
    xa, xb = LANES[a], LANES[b]
    col = ACCENT if kind == "s3" else MUTED
    m = "arrow-accent" if kind == "s3" else "arrow"
    P(f'<line x1="{xa+3}" y1="{y}" x2="{xb-4}" y2="{y}" stroke="{col}" stroke-width="1.2" marker-end="url(#{m})"/>')
    cx = (xa + xb) / 2
    ly = y - (20 if sub else 6)
    tw = len(label) * 6.2 + 12
    P(f'<rect x="{cx-tw/2:g}" y="{ly-10}" width="{tw:g}" height="13" rx="2" fill="{PAPER}"/>')
    P(f'<text x="{cx:g}" y="{ly}" fill="{INK}" font-size="10" font-family="{MONO}" text-anchor="middle">{label}</text>')
    if sub:
        sw = len(sub) * 5.4 + 12
        P(f'<rect x="{cx-sw/2:g}" y="{y-16}" width="{sw:g}" height="11" rx="2" fill="{PAPER}"/>')
        P(f'<text x="{cx:g}" y="{y-7}" fill="{col}" font-size="8.5" font-family="{MONO}" text-anchor="middle">{sub}</text>')
    # step number
    P(f'<circle cx="34" cy="{y}" r="9" fill="#ffffff" stroke="{col}" stroke-width="1"/>')
    P(f'<text x="34" y="{y+3.5}" fill="{col}" font-size="9" font-weight="600" font-family="{MONO}" text-anchor="middle">{i+1}</text>')

# legend
ly = H - 22
P(f'<line x1="24" y1="{ly-16}" x2="936" y2="{ly-16}" stroke="rgba(45,49,66,0.10)" stroke-width="0.8"/>')
P(f'<line x1="24" y1="{ly-3}" x2="44" y2="{ly-3}" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#arrow)"/>')
P(f'<text x="52" y="{ly}" fill="{MUTED}" font-size="9" font-family="{SANS}">메타데이터 (REST → Postgres)</text>')
P(f'<line x1="250" y1="{ly-3}" x2="270" y2="{ly-3}" stroke="{ACCENT}" stroke-width="1.2" marker-end="url(#arrow-accent)"/>')
P(f'<text x="278" y="{ly}" fill="{MUTED}" font-size="9" font-family="{SANS}">파일 (노트북 Pod → RustFS 직접 S3 PUT, MLflow 서버를 거치지 않음)</text>')

TITLE = "홈랩 MLflow 기록 흐름"
DESC = ("4.1절 노트북이 MLflow 서버, Postgres, RustFS 와 주고받는 순서. 실험과 run 생성, 파라미터와 지표 기록, 모델 등록 같은 메타데이터는 "
        "MLflow 서버를 거쳐 Postgres 에 쌓이고, 데이터셋 CSV, EDA 그림, 모델 파일은 노트북 Pod 가 RustFS 에 S3 로 직접 올린다. "
        "MLflow 3 에서 log_model 은 run 아티팩트가 아니라 chapter-4/<exp>/models/m-… 의 logged model 로 저장되고, "
        "register_model(runs:/<run>/income-classifier) 은 run 경로가 비어 있어 그 logged model 을 source 로 버전을 만든다.")
svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="hl-seq-title hl-seq-desc">
<title id="hl-seq-title">{TITLE}</title>
<desc id="hl-seq-desc">{DESC}</desc>
<defs>
<style>@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&amp;family=Geist+Mono:wght@400;500;600&amp;display=swap');</style>
<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>
<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker>
</defs>
''' + "\n".join(out) + "\n<!-- icons: Simple Icons(CC0) 브랜드 마크 -->\n</svg>\n"
svg = svg.replace("<exp>", "&lt;exp&gt;").replace("<run>", "&lt;run&gt;")
(POST / "homelab-mlflow-seq.svg").write_text(svg)
print("ok", POST / "homelab-mlflow-seq.svg", W, H)
