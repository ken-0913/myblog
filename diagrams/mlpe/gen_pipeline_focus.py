"""MLOps 파이프라인 그림에서 절마다 해당하는 단계만 강조한 SVG 를 만든다 (mlpe-04-1 실습 글용).

사용: python3 diagrams/mlpe/gen_pipeline_focus.py <simpleicons 디렉터리>
  디렉터리에는 https://cdn.simpleicons.org/<slug> 로 받은 mlflow.svg, jupyter.svg 를 둔다.
출력: content/posts/mlpe/mlpe-04-1-mlflow-practice/ 의 pipeline-6-*.svg 와 mlops_pipeline.svg(6.8)

바탕 배치는 원래 mlops_pipeline.svg(9개 단계 + 공유 저장소)와 같다. 강조하지 않는 상자와 화살표는 회색으로 흐리게 두고,
역할별로 색을 준다.
  run   : Jupyter 노트북에서 직접 실행한 단계 (초록)
  store : MLflow 에 기록·등록한 곳 (주황)
  next  : 다음 절·장에서 할 단계 (보라 점선)
아이콘: Simple Icons(CC0) MLflow, Jupyter 마크.
"""
import re, sys
from pathlib import Path

SI = Path(sys.argv[1])
OUT = Path(__file__).resolve().parents[2] / "content/posts/mlpe/mlpe-04-1-mlflow-practice"


def mark(name, color):
    d = re.search(r'<path d="([^"]+)"', (SI / f"{name}.svg").read_text()).group(1)
    return f'<path fill="{color}" d="{d}"/>'


ICON = {"mlflow": mark("mlflow", "#0194E2"), "jupyter": mark("jupyter", "#F37626"), "redis": mark("redis", "#FF4438")}
FEAST_OUT = OUT.parent / "mlpe-04-mlflow-feast"
KFP_OUT = OUT.parent / "mlpe-05-1-kfp-income-pipeline"

DIM = dict(fill="#F4F4F2", stroke="#C9C8C2", text="#9C9B95", sub="#B4B3AD")
ROLE = {
    "run":   dict(fill="#E1F5EE", stroke="#0F6E56", text="#085041", sub="#0F6E56", icon="jupyter", dash=None),
    "store": dict(fill="#FDEEE6", stroke="#EB6C36", text="#7A2E0C", sub="#EB6C36", icon="mlflow", dash=None),
    "next":  dict(fill="#EEEDFE", stroke="#534AB7", text="#3C3489", sub="#534AB7", icon=None, dash="5 3"),
    "feast": dict(fill="#E6F0FA", stroke="#1F6FB2", text="#0C3B66", sub="#1F6FB2", icon="redis", dash=None),
    "kfp":   dict(fill="#E3F4F4", stroke="#0E7C86", text="#08474D", sub="#0E7C86", icon=None, dash=None),
}
LEGEND = {"run": "Jupyter 에서 직접 실행", "store": "MLflow 에 기록·등록", "next": "다음 절·장에서 할 단계", "feast": "4.2절 Feast 로 구현", "kfp": "5장 KFP 로 자동화"}
ARROW_DIM = "#C9C8C2"

# 상자: id → (x, y, w, h, 제목, 부제)
BOX = {
    "biz":    (250, 40, 200, 44, "비즈니스 요구사항", None),
    "prob":   (250, 124, 200, 44, "문제 정의·설계", None),
    "mdesign": (490, 124, 150, 44, "모델 설계", None),
    "dw":     (40, 124, 160, 56, "데이터 웨어하우스", "배치·스트리밍"),
    "fs":     (40, 260, 160, 56, "피처 스토어", "공유 피처 저장소"),
    "data":   (250, 260, 200, 44, "데이터 수집·준비", None),
    "train":  (250, 356, 200, 44, "모델 학습", None),
    "eval":   (250, 452, 200, 44, "모델 평가·검증", None),
    "deploy": (250, 548, 200, 44, "모델 배포", None),
    "track":  (490, 356, 150, 56, "실험 추적", "파라미터·메트릭"),
    "reg":    (490, 452, 150, 56, "모델 레지스트리", "버전 관리"),
    "api":    (250, 680, 200, 56, "모델 API", "예측 서빙"),
    "mon":    (490, 680, 150, 56, "모델 모니터링", "드리프트 감지"),
    "user":   (250, 800, 200, 44, "사용자", None),
}
# 화살표: id → path d
ARROW = {
    "biz-prob": "M350 84 L350 118", "prob-md": "M450 146 L484 146", "md-data": "M565 168 L565 282 L456 282",
    "prob-data": "M350 168 L350 254", "dw-fs": "M120 180 L120 254", "fs-data": "M200 282 L244 282",
    "fs-train": "M150 316 L150 378 L244 378", "fs-api": "M90 316 L90 708 L244 708",
    "data-train": "M350 304 L350 350", "train-eval": "M350 400 L350 446", "eval-deploy": "M350 496 L350 542",
    "train-track": "M450 378 L484 378", "eval-reg": "M450 474 L484 474", "reg-deploy": "M565 508 L565 570 L456 570",
    "deploy-api": "M350 592 L350 674", "api-mon": "M450 708 L484 708", "api-user": "M330 736 L330 794",
    "user-api": "M370 800 L370 742",
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(name, title, desc, roles, arrows=(), extra_arrows=(), card=None, subs=None, orch=None, out=OUT):
    """roles: {box_id: role}, arrows: [(arrow_id, role, label, (lx, ly, anchor), dashed)],
    extra_arrows: [(path_d, role, label, (lx, ly, anchor), dashed)], card: dict(y, title, kicker, lines, note, link)
    subs: {box_id: 부제 덮어쓰기}, orch: 오케스트레이션 점선 상자 역할"""
    subs = subs or {}
    o = []
    P = o.append
    P(f'<rect width="960" height="920" fill="#FFFFFF"/>')

    # 오케스트레이션 점선 상자
    oc = ROLE[orch] if orch else None
    P(f'<rect x="230" y="220" width="240" height="392" rx="12" fill="{oc["fill"] if oc else "none"}" fill-opacity="{0.35 if oc else 1}" '
      f'stroke="{oc["stroke"] if oc else DIM["stroke"]}" stroke-width="{1.5 if oc else 0.75}" stroke-dasharray="4 4"/>')
    P(f'<text x="350" y="240" text-anchor="middle" font-size="12" font-weight="{600 if oc else 400}" fill="{oc["sub"] if oc else DIM["sub"]}">파이프라인 오케스트레이션</text>')

    # 흐린 화살표 (강조할 것은 뒤에서 덮어 그린다)
    hl = {a[0] for a in arrows}
    P(f'<g stroke="{ARROW_DIM}" stroke-width="1.2" fill="none">')
    for aid, d in ARROW.items():
        if aid not in hl:
            P(f'  <path d="{d}" marker-end="url(#arrow)"/>')
    P('</g>')

    # 상자
    for bid, (x, y, w, h, t, sub) in BOX.items():
        sub = subs.get(bid, sub)
        r = ROLE.get(roles.get(bid)) if bid in roles else None
        cx = x + w / 2
        if r:
            dash = f' stroke-dasharray="{r["dash"]}"' if r["dash"] else ""
            P(f'<rect x="{x-8}" y="{y-8}" width="{w+16}" height="{h+16}" rx="12" fill="none" stroke="{r["stroke"]}" stroke-opacity="0.22" stroke-width="6"/>')
            P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{r["fill"]}" stroke="{r["stroke"]}" stroke-width="2"{dash}/>')
            tc, sc, fw = r["text"], r["sub"], 700
        else:
            P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{DIM["fill"]}" stroke="{DIM["stroke"]}" stroke-width="0.75"/>')
            tc, sc, fw = DIM["text"], DIM["sub"], 600
        if sub:
            P(f'<text x="{cx:g}" y="{y+18}" text-anchor="middle" dominant-baseline="central" font-size="14" font-weight="{fw}" fill="{tc}">{esc(t)}</text>')
            P(f'<text x="{cx:g}" y="{y+36}" text-anchor="middle" dominant-baseline="central" font-size="12" fill="{sc}">{esc(sub)}</text>')
        else:
            P(f'<text x="{cx:g}" y="{y+h/2:g}" text-anchor="middle" dominant-baseline="central" font-size="14" font-weight="{fw}" fill="{tc}">{esc(t)}</text>')
        if r and r["icon"]:
            P(f'<svg x="{x+w-19}" y="{y+5}" width="13" height="13" viewBox="0 0 24 24" aria-hidden="true">{ICON[r["icon"]]}</svg>')
    P(f'<text x="565" y="760" text-anchor="middle" font-size="12" fill="{DIM["sub"]}">↻ 재학습 트리거</text>')

    # 강조 화살표
    def draw(d, role, label, lpos, dashed):
        r = ROLE[role]
        da = ' stroke-dasharray="4 3"' if dashed else ""
        P(f'<path d="{d}" fill="none" stroke="{r["stroke"]}" stroke-width="2"{da} marker-end="url(#arrow-{role})"/>')
        if label:
            lx, ly, anc = lpos
            for i, ln in enumerate(label.split("\n")):
                P(f'<text x="{lx}" y="{ly+12*i}" text-anchor="{anc}" font-size="10" font-weight="600" fill="{r["stroke"]}">{esc(ln)}</text>')
    for aid, role, label, lpos, dashed in arrows:
        draw(ARROW[aid], role, label, lpos, dashed)
    for d, role, label, lpos, dashed in extra_arrows:
        draw(d, role, label, lpos, dashed)

    # 설명 카드
    if card:
        role = ROLE[card.get("role", "store")]
        lines = card["lines"]
        h = 64 + 20 * len(lines) + (20 if card.get("note") else 0)
        y = card["y"]
        if card.get("link"):
            lx, ly = card["link"]
            P(f'<line x1="{lx}" y1="{ly}" x2="684" y2="{ly}" stroke="{role["stroke"]}" stroke-width="1" stroke-dasharray="2 2"/>')
        P(f'<rect x="684" y="{y}" width="256" height="{h}" rx="10" fill="#FFFFFF" stroke="{role["stroke"]}" stroke-width="1.2"/>')
        P(f'<text x="700" y="{y+24}" font-size="11" font-weight="700" fill="{role["stroke"]}" letter-spacing="0.06em">{esc(card["kicker"])}</text>')
        P(f'<text x="700" y="{y+48}" font-size="13" font-weight="700" fill="#2C2C2A">{esc(card["title"])}</text>')
        for i, ln in enumerate(lines):
            P(f'<text x="700" y="{y+70+20*i}" font-size="12" fill="#444441">· {esc(ln)}</text>')
        if card.get("note"):
            P(f'<text x="700" y="{y+70+20*len(lines)}" font-size="11" fill="#9C9B95">{esc(card["note"])}</text>')

    # 범례
    arrow_roles = {a[1] for a in arrows} | {a[1] for a in extra_arrows}
    used = [r for r in ("kfp", "run", "store", "next", "feast") if r in roles.values() or r == orch or r in arrow_roles]
    x = 40
    for r in used:
        c = ROLE[r]
        dash = f' stroke-dasharray="{c["dash"]}"' if c["dash"] else ""
        P(f'<rect x="{x}" y="874" width="14" height="12" rx="3" fill="{c["fill"]}" stroke="{c["stroke"]}" stroke-width="1.5"{dash}/>')
        P(f'<text x="{x+22}" y="884" font-size="12" fill="#5F5E5A">{LEGEND[r]}</text>')
        x += 22 + len(LEGEND[r]) * 11 + 30
    P(f'<rect x="{x}" y="874" width="14" height="12" rx="3" fill="{DIM["fill"]}" stroke="{DIM["stroke"]}" stroke-width="0.75"/>')
    P(f'<text x="{x+22}" y="884" font-size="12" fill="#5F5E5A">이 절과 무관한 단계</text>')

    markers = "\n    ".join(
        f'<marker id="arrow-{k}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M2 1L8 5L2 9" fill="none" stroke="{v["stroke"]}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></marker>'
        for k, v in ROLE.items())
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="920" viewBox="0 0 960 920" font-family="'Pretendard','Noto Sans KR','Apple SD Gothic Neo',sans-serif" role="img" aria-labelledby="{name}-title {name}-desc">
  <title id="{name}-title">{esc(title)}</title>
  <desc id="{name}-desc">{esc(desc)}</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="{ARROW_DIM}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker>
    {markers}
  </defs>
  {chr(10).join("  " + s for s in o).lstrip()}
  <!-- icons: Simple Icons (CC0) MLflow, Jupyter, Redis -->
</svg>
'''
    (out / f"{name}.svg").write_text(svg)
    print("ok", name)


# 6.1 한눈에 보기: Jupyter 가 손, MLflow 가 저장소
render("pipeline-6-1-overview", "6절 전체: Jupyter 가 실행하고 MLflow 가 기록한다",
       "MLOps 파이프라인에서 데이터 수집·준비, 모델 학습, 모델 평가·검증은 Jupyter 노트북 셀로 직접 실행했고, 그 결과를 MLflow 실험 추적에 기록하고 1등 모델을 모델 레지스트리에 등록했다. 점선 오케스트레이션 자리는 원래 5장의 Kubeflow Pipelines 몫이다.",
       roles={"data": "run", "train": "run", "eval": "run", "track": "store", "reg": "store"},
       arrows=[("data-train", "run", None, None, False), ("train-eval", "run", None, None, False),
               ("train-track", "store", "log_*", (467, 368, "middle"), False),
               ("eval-reg", "store", "등록", (467, 464, "middle"), False)],
       card=dict(y=300, role="store", kicker="6절 전체", title="Jupyter 가 손, MLflow 가 저장소",
                 lines=["초록: 노트북 셀로 직접 실행 (6.3 ~ 6.7)", "주황: MLflow 에 기록·등록 (6.5 ~ 6.8)",
                        "점선 상자 자동화는 5장 Kubeflow 몫", "피처 스토어 4.2절, 배포·서빙은 5장 이후"],
                 link=(640, 430)))

# 6.3 EDA run
render("pipeline-6-3-eda", "6.3 EDA run: 데이터 탐색 결과를 실험 추적에 남긴다",
       "데이터 수집·준비 단계에서 범주형 8컬럼마다 Target 비율 막대그래프를 그리고, log_artifacts 로 실험 추적(MLflow run 의 아티팩트, 파일은 RustFS)에 PNG 8장을 올렸다.",
       roles={"data": "run", "track": "store"}, subs={"data": "EDA 플롯 8장"},
       extra_arrows=[("M450 296 L530 296 L530 350", "store", "log_artifacts", (536, 324, "start"), False)],
       card=dict(y=230, role="store", kicker="6.3 EDA run", title="eda-4d07c060… FINISHED",
                 lines=["범주형 8컬럼 × Target 비율 막대", "plot.save → categorical_variable_plots/",
                        "log_artifacts → RustFS PNG 8장", "경로 chapter-4/2/<run ID>/artifacts/"],
                 note=".ipynb_checkpoints PNG 3장도 같이 올라감", link=(640, 384)))

# 6.4 데이터 준비
render("pipeline-6-4-data", "6.4 데이터 준비: 학습에 넣을 형태로 바꾼다",
       "데이터 수집·준비 단계에서 범주형 컬럼을 더미 90컬럼으로, Target 을 0과 1로 바꾸고, 컬럼 목록을 column_list.pkl 로 저장한 뒤 학습용과 평가용으로 8대 2로 나눴다.",
       roles={"data": "run"}, subs={"data": "더미 90컬럼 · 분할"},
       arrows=[("data-train", "run", "X_train · y_train", (358, 330, "start"), False)],
       card=dict(y=220, role="run", kicker="6.4 데이터 준비", title="Train Test Split 셀 (수정 없음)",
                 lines=["get_dummies(drop_first) → 90컬럼", "OneHotEncoder → Target 0/1 (>50K=1)",
                        "column_list.pkl 저장 (5장 추론용)", "train_test_split 80:20"],
                 note="random_state 없음: 실행마다 AUC 가 조금 다르다"))

# 6.5 모델 run
render("pipeline-6-5-train", "6.5 모델 run: 학습 결과를 실험 추적에 기록한다",
       "모델 학습 단계에서 결정 트리와 랜덤 포레스트를 학습하고, 데이터셋 CSV 는 RustFS 에 올려 log_input 으로, 지표와 파라미터와 모델은 log_metric, log_params, log_model 로 실험 추적에 기록했다.",
       roles={"train": "run", "track": "store"}, subs={"train": "결정 트리 · 랜덤 포레스트"},
       arrows=[("train-track", "store", "log_*", (467, 368, "middle"), False)],
       card=dict(y=300, role="store", kicker="6.5 모델 run", title="run 하나에 네 가지를 기록",
                 lines=["데이터셋 3개: CSV 는 RustFS, log_input", "지표 4개: AUC · 정확도 (train/test)",
                        "파라미터: 결정 트리 13 · 랜덤 포레스트 19", "모델: logged model m-… (model.skops)"],
                 note="skops_trusted_types 없으면 run 이 FAILED", link=(640, 384)))

# 6.6 XGBoost autolog
render("pipeline-6-6-autolog", "6.6 XGBoost autolog: 기록을 자동으로 남긴다",
       "모델 학습 단계에서 XGBoost 를 두 번 학습하는 동안 mlflow.xgboost.autolog 가 파라미터, 모델, 특성 중요도 플롯을 실험 추적에 자동으로 기록했다. 지표 4개만 직접 기록했다.",
       roles={"train": "run", "track": "store"}, subs={"train": "XGBoost (xgb.train × 2)"},
       arrows=[("train-track", "store", "autolog", (467, 368, "middle"), False)],
       card=dict(y=300, role="store", kicker="6.6 XGBoost autolog", title="thoughtful-smelt-879 FINISHED",
                 lines=["autolog() 한 줄: 파라미터 · 모델 · 플롯", "지표 4개만 log_metric 으로 직접",
                        "xgb.train 2번 → logged model 2개", "파라미터는 첫 학습 것만 10개",
                        "Datasets 1개 (배열로 기록)"], link=(640, 384)))

# 6.7 결과 비교
render("pipeline-6-7-eval", "6.7 결과 비교: 실험 추적에서 지표를 꺼내 평가한다",
       "모델 평가·검증 단계에서 실험 추적에 쌓인 run 세 개의 test AUC 와 정확도를 비교했다. 랜덤 포레스트가 AUC 0.8608 로 1등이다.",
       roles={"eval": "run", "track": "store"}, subs={"eval": "AUC · 정확도 비교"},
       extra_arrows=[("M490 404 L478 404 L478 462 L456 462", "store", "search", (482, 432, "start"), False)],
       card=dict(y=300, role="run", kicker="6.7 결과 비교", title="test AUC 기준 1등: 랜덤 포레스트",
                 lines=["랜덤 포레스트 0.8608", "결정 트리 0.8187", "XGBoost (hinge 지표) 0.7320",
                        "정확도는 셋 다 0.81 ~ 0.83"],
                 note="UI 검색: metrics.roc_auc_score_test > 0.8"))

# 6.8 모델 등록 (기존 파일명 유지)
render("mlops_pipeline", "6.8 모델 등록: 1등 모델을 모델 레지스트리에 올린다",
       "MLOps 파이프라인 전체를 흐리게 두고 모델 레지스트리만 강조한 그림. 모델 평가·검증에서 test AUC 1등인 랜덤 포레스트(0.8608)를 MLflow 3.16 Model Registry 에 random-forest-classifier v2 로 등록했고, 백엔드는 Postgres, 모델 파일은 RustFS 에 있다. 레지스트리에서 모델 배포로 가는 연결은 5장에서 이어진다.",
       roles={"reg": "store"},
       arrows=[("eval-reg", "store", "등록", (467, 464, "middle"), False),
               ("reg-deploy", "next", "models:/…@champion\n5장에서 배포로", (558, 532, "end"), True)],
       card=dict(y=388, role="store", kicker="6.8 모델 등록", title="MLflow 3.16 Model Registry",
                 lines=["search_runs: test AUC > 0.8, 1등 선택", "1등: 랜덤 포레스트 AUC 0.8608",
                        "random-forest-classifier v2 등록", "백엔드 Postgres · 모델 파일 RustFS",
                        "pyfunc.load_model 로 다시 불러오기"],
                 note="v1 은 FAILED run 의 빈 모델이라 삭제", link=(640, 480)))

# 6.9 남은 것
render("pipeline-6-9-next", "6.9 다음 단계: 아직 손으로 하거나 비어 있는 곳",
       "4.1절에서 다루지 않은 피처 스토어는 4.2절 Feast 에서, 점선 오케스트레이션 상자의 자동화와 모델 배포는 5장 Kubeflow Pipelines 에서, 모델 API 와 모니터링은 뒷장에서 다룬다.",
       roles={"fs": "next", "deploy": "next", "api": "next", "mon": "next"}, orch="next",
       subs={"fs": "4.2절 Feast", "deploy": "5장 배치 추론", "api": "뒷장", "mon": "뒷장"},
       card=dict(y=240, role="next", kicker="6.9 다음 단계", title="4.1절 다음에 채울 곳",
                 lines=["피처 스토어: 4.2절 Feast + Redis", "점선 상자 자동화: 5장 Kubeflow",
                        "모델 배포: 5장, models:/…@champion", "모델 API · 모니터링: 뒷장"],
                 note="지금은 사람이 셀을 눌러 점선 상자를 대신 돌렸다"))

# mlpe-04-mlflow-feast (4.2절): 6.1 그림에서 피처 스토어만 켠다
render("feast-pipeline-overview", "4.2절 Feast: MLOps 파이프라인의 피처 스토어 자리를 채운다",
       "4.1절 그림에서 비어 있던 피처 스토어를 Feast 로 채운 그림. 책 저장소의 parquet 3개를 오프라인 스토어(RustFS)에 두고, "
       "학습 쪽은 get_historical_features 로 시점 기준 피처를, 서빙 쪽은 materialize 로 Redis 에 옮긴 최신 피처를 get_online_features 와 피처 서버로 꺼낸다.",
       roles={"fs": "feast"}, subs={"fs": "Feast 0.67 · RustFS + Redis"},
       arrows=[("dw-fs", "feast", "parquet 3개\n→ RustFS", (128, 212, "start"), False),
               ("fs-data", "feast", "조인", (222, 274, "middle"), False),
               ("fs-train", "feast", "historical", (158, 370, "start"), False),
               ("fs-api", "feast", "online\n(Redis · :6566)", (98, 600, "start"), False)],
       card=dict(y=230, role="feast", kicker="4.2절 Feast", title="학습과 추론에 같은 피처를",
                 lines=["오프라인: RustFS parquet 3개 (뷰 3개)", "레지스트리: registry_local.db (RustFS)",
                        "materialize: 오프라인 → Redis 30,162키", "학습: get_historical_features (시점 기준)",
                        "추론: get_online_features · 피처 서버"],
                 note="엔티티 user_id · ttl 365일"),
       out=FEAST_OUT)

# mlpe-05-1 (5장): 오케스트레이션 점선 상자와 배치 추론(모델 배포 자리)을 켜고, 4장의 Feast · MLflow 를 끌어다 쓴다
render("kfp-pipeline-overview", "5장 KFP: 파이프라인 오케스트레이션 자리를 채운다",
       "4.1절 그림에서 점선으로 비어 있던 파이프라인 오케스트레이션을 Kubeflow Pipelines 로 채운 그림. 5장의 배치 추론 파이프라인은 "
       "모델 배포 자리에서 돌며, 4.2절 Feast 피처 스토어에서 get_historical_features 로 피처를, 4.1절 MLflow 모델 레지스트리에서 Production 모델을 가져와 "
       "RustFS(책은 MinIO)에 결과를 쓴다.",
       roles={"deploy": "kfp", "fs": "feast", "reg": "store"}, orch="kfp",
       subs={"deploy": "배치 추론 파이프라인", "fs": "4.2절 Feast", "reg": "4.1절 MLflow"},
       arrows=[("reg-deploy", "store", "Production 모델\n+ column_list.pkl", (572, 540, "start"), False)],
       extra_arrows=[("M170 316 L170 560 L244 560", "feast", "historical\n피처 8개", (176, 470, "start"), False)],
       card=dict(y=600, role="kfp", kicker="5장 Kubeflow Pipelines", title="수작업 4단계를 컴포넌트 4개로",
                 lines=["read_data: RustFS 에서 user_id 목록", "retrieve_features: Feast 오프라인 조회",
                        "run_inference: MLflow 모델 predict_proba", "write_data: 결과 parquet 를 RustFS 로"],
                 note="홈랩 KFP 2.17.3 실측: 3분 9초, 30,162행"),
       out=KFP_OUT)
