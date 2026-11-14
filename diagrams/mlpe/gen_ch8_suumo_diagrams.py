"""MLPE 4주차(8.1절, SUUMO 회귀 모델 학습) 글의 도식 SVG 생성.

사용: python3 diagrams/mlpe/gen_ch8_suumo_diagrams.py
출력: content/posts/mlpe/mlpe-08-1-suumo-training/*.svg
상자·화살표·색은 7장 생성기(gen_ch7_suumo_diagrams.py)의 것을 그대로 쓴다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_ch7_suumo_diagrams as base  # noqa: E402
from gen_ch7_suumo_diagrams import D, bottom, left, right, top  # noqa: E402

base.POST = base.ROOT / "content/posts/mlpe/mlpe-08-1-suumo-training"


# ---------------------------------------------------------------- 1. 8장 전체 흐름
def ch8_overview():
    d = D("ch8-overview", 960, 400, "8장 전체 흐름",
          "7장이 남긴 버킷의 train, val, test Parquet 을 KFP 파이프라인이 읽는다. 피처 준비 뒤 두 갈래로 나뉜다. "
          "위쪽은 LightGBM 학습으로 추정값, 10%, 90% 세 모델을 만들어 Model 아티팩트로 남긴다. "
          "아래쪽은 구, 동 중앙 단가로 찍는 기준선이다. 검증이 둘을 val, test 로 채점해 MAE, MAPE, 80% 구간 적중률을 Metrics 로 남긴다. "
          "기준선보다 나으면 저장된 모델로 주소 몇 개를 예측해 상식 범위인지 확인하고, 아니면 피처와 하이퍼파라미터를 고쳐 다시 학습한다.")
    d.group(200, 20, 560, 300, "KFP 파이프라인")
    src = d.node(20, 70, 150, 56, "train / val / test", kind="dim")
    ft = d.node(220, 70, 150, 56, "피처 준비", kind="pipe")
    tr = d.node(420, 70, 150, 56, "LightGBM 학습", kind="emph")
    ev = d.node(610, 150, 130, 56, "검증", kind="pipe")
    bl = d.node(420, 230, 150, 56, "기준선", kind="node")
    md = d.node(420, 150, 150, 46, "Model 아티팩트 3개", kind="emph", size=12)
    mt = d.node(610, 250, 130, 46, "Metrics", kind="pipe")

    d.edge([right(src), left(ft)], kind="pipe")
    d.edge([right(ft), left(tr)], kind="pipe")
    d.edge([bottom(ft), (top(ft)[0], 258), (bl[0] - 2, 258)], kind="pipe")
    d.edge([bottom(tr), (top(md)[0], top(md)[1] - 2)], "추정·10%·90%", kind="emph")
    d.edge([right(md), (ev[0] - 2, right(md)[1])], kind="emph")
    d.edge([right(bl), (590, right(bl)[1]), (590, 195), (ev[0] - 2, 195)], kind="line")
    d.edge([bottom(ev), (top(mt)[0], top(mt)[1] - 2)], "val, test", kind="pipe")

    cx, cy = 860, 178
    d.diamond(cx, cy, 170, 84, "기준선보다 나은가")
    d.edge([right(ev), (cx - 87, cy)], kind="pipe")
    ok = d.node(785, 300, 150, 56, "주소로 예측 확인", kind="emph")
    d.edge([(cx, cy + 42), (top(ok)[0], top(ok)[1] - 2)], "예", kind="emph")
    d.edge([(cx, cy - 42), (cx, 50), (top(tr)[0] + 40, 50), (top(tr)[0] + 40, top(tr)[1] - 2)],
           "아니오: 피처, 하이퍼파라미터 수정", kind="warn", dashed=True, lpos=(640, 50))
    d.text(495, 345, "학습은 libgomp 가 든 이미지의 컨테이너 컴포넌트로 실행", size=11)
    d.write()


if __name__ == "__main__":
    ch8_overview()
