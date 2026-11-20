"""MLPE 5주차(9장, SUUMO 학습 추적) 글의 도식 SVG 생성.

사용: python3 diagrams/mlpe/gen_ch9_suumo_diagrams.py
출력: content/posts/mlpe/mlpe-09-1-suumo-tracking/*.svg
상자·화살표·색은 7장 생성기(gen_ch7_suumo_diagrams.py)의 것을 그대로 쓴다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_ch7_suumo_diagrams as base  # noqa: E402
from gen_ch7_suumo_diagrams import D, left, right  # noqa: E402

base.POST = base.ROOT / "content/posts/mlpe/mlpe-09-1-suumo-tracking"


# 9장 전체 흐름은 스택 다이어그램(diagrams/mlpe/ch9-overview-stack.html → ch9-overview-stack.png)으로 그린다.


# ---------------------------------------------------------------- 승격 판단
def promote_flow():
    d = D("promote-flow", 960, 250, "승격 판단",
          "검증을 통과한 run 이 들어오면 먼저 레지스트리에 staging 별칭이 있는지 본다. 없으면 바로 새 버전으로 등록하고 staging 을 붙인다. "
          "있으면 그 버전의 run 과 val MAPE 를 비교한다. 나빠지지 않았으면 새 버전을 등록하고 staging 을 옮긴다. "
          "나빠졌으면 staging 은 그대로 두고 run 에 태그만 남긴다.")
    n0 = d.node(20, 95, 150, 56, "검증 통과한 run", kind="pipe")
    d.diamond(290, 123, 190, 84, "@staging 이 있는가")
    d.diamond(540, 123, 220, 84, "val MAPE 가 나빠졌는가")
    ok = d.node(740, 30, 200, 56, "새 버전 등록, @staging 이동", kind="emph", size=12)
    no = d.node(740, 185, 200, 56, "@staging 유지, run 에 태그", kind="node", size=12)
    d.edge([right(n0), (193, 123)], kind="pipe")
    d.edge([(385, 123), (428, 123)], "예", kind="line")
    d.edge([(290, 81), (290, 44), (ok[0] - 2, 44)], "아니오", kind="emph", lpos=(360, 44))
    d.edge([(650, 123), (700, 123), (700, 72), (ok[0] - 2, 72)], "아니오", kind="emph", lpos=(700, 100))
    d.edge([(540, 165), (540, 213), (no[0] - 2, 213)], "예", kind="line", lpos=(620, 213))
    d.write()


if __name__ == "__main__":
    promote_flow()
