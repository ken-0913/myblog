"""MLPE 4주차(7.2 ~ 7.3절, SUUMO 데이터 적용) 글의 도식 SVG 15개 생성.

사용: python3 diagrams/mlpe/gen_ch7_suumo_diagrams.py
출력: content/posts/mlpe/mlpe-07-3-capstone-topics/*.svg
색·글꼴은 3주차 글(notebook-pipeline-overview.svg)과 같은 체계를 쓴다:
  바탕 흰색, 상자 #F4F4F2 / #C9C8C2, 강조 초록 #0F6E56, 파이프라인 청록 #0E7C86, 주의 주황 #EB6C36, 글꼴 Pretendard.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POST = ROOT / "content/posts/mlpe/mlpe-07-3-capstone-topics"

FONT = "'Pretendard','Noto Sans KR','Apple SD Gothic Neo',sans-serif"
INK, MUTED, LINE, PAPER = "#444441", "#5F5E5A", "#C9C8C2", "#F4F4F2"
GREEN, GREEN_BG = "#0F6E56", "#E1F5EE"
TEAL, TEAL_BG = "#0E7C86", "#E3F4F4"
ORANGE, ORANGE_BG = "#EB6C36", "#FDEEE6"
PURPLE, PURPLE_BG = "#534AB7", "#EEEDFE"

KINDS = {
    "node": (PAPER, LINE, INK, 0.75),
    "emph": (GREEN_BG, GREEN, GREEN, 1.4),
    "pipe": (TEAL_BG, TEAL, TEAL, 1.4),
    "warn": (ORANGE_BG, ORANGE, ORANGE, 1.4),
    "alt": (PURPLE_BG, PURPLE, PURPLE, 1.4),
    "dim": ("#FFFFFF", LINE, "#9C9B95", 0.75),
}
MARKERS = {"line": LINE, "emph": GREEN, "pipe": TEAL, "warn": ORANGE, "alt": PURPLE}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class D:
    def __init__(self, name, w, h, title, desc):
        self.name, self.w, self.h, self.title, self.desc = name, w, h, title, desc
        self.out = []

    def P(self, s):
        self.out.append(s)

    # 상자. title 은 한 줄, sub 는 보조 줄 목록. 글자는 상자 가운데에 세로로도 가운데 정렬한다.
    def node(self, x, y, w, h, title, sub=(), kind="node", size=13):
        sub = ()  # 그림에는 제목만 둔다. 세부 설명은 본문에 쓴다
        fill, stroke, tcol, sw = KINDS[kind]
        dash = ' stroke-dasharray="4 4"' if kind == "dim" else ""
        self.P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')
        lines = [(title, size, 600, tcol)] + [(s, 10.5, 400, MUTED) for s in sub]
        total = sum(l[1] + 4 for l in lines) - 4
        cy = y + h / 2 - total / 2
        for text, fs, fw, col in lines:
            cy += fs / 2
            self.P(f'<text x="{x + w / 2:g}" y="{cy:g}" text-anchor="middle" dominant-baseline="central" font-size="{fs}" font-weight="{fw}" fill="{col}">{esc(text)}</text>')
            cy += fs / 2 + 4
        return (x, y, w, h)

    def diamond(self, cx, cy, w, h, text, kind="warn"):
        fill, stroke, tcol, sw = KINDS[kind]
        self.P(f'<polygon points="{cx},{cy - h / 2:g} {cx + w / 2:g},{cy} {cx},{cy + h / 2:g} {cx - w / 2:g},{cy}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        self.P(f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="central" font-size="12" font-weight="600" fill="{tcol}">{esc(text)}</text>')

    def group(self, x, y, w, h, label, kind="pipe"):
        fill, stroke, tcol, _ = KINDS[kind]
        self.P(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" fill-opacity="0.35" stroke="{stroke}" stroke-width="1.5" stroke-dasharray="4 4"/>')
        self.P(f'<text x="{x + w / 2:g}" y="{y + 18}" text-anchor="middle" font-size="12" font-weight="600" fill="{tcol}">{esc(label)}</text>')

    # 꺾은선 화살표. pts 는 (x, y) 목록. label 은 선 중간에 흰 바탕을 깔고 쓴다.
    def edge(self, pts, label=None, kind="line", dashed=False, lpos=None, lsize=10.5, arrow=True):
        col = MARKERS[kind]
        d = "M" + " L".join(f"{x} {y}" for x, y in pts)
        dash = ' stroke-dasharray="5 4"' if dashed else ""
        mk = f' marker-end="url(#m-{kind})"' if arrow else ""
        self.P(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="1.2"{dash}{mk}/>')
        if label:
            if lpos is None:
                (x1, y1), (x2, y2) = pts[0], pts[-1]
                if len(pts) == 2:
                    lx, ly = (x1 + x2) / 2, (y1 + y2) / 2
                else:
                    mid = pts[len(pts) // 2]
                    lx, ly = mid
            else:
                lx, ly = lpos
            lines = label.split("\n")[:1]
            lw = max(len(l) for l in lines) * lsize * 0.62 + 10
            lh = len(lines) * (lsize + 3)
            self.P(f'<rect x="{lx - lw / 2:g}" y="{ly - lh / 2:g}" width="{lw:g}" height="{lh:g}" rx="3" fill="#FFFFFF"/>')
            for i, l in enumerate(lines):
                ty = ly - lh / 2 + (lsize + 3) * (i + 0.5)
                self.P(f'<text x="{lx:g}" y="{ty:g}" text-anchor="middle" dominant-baseline="central" font-size="{lsize}" fill="{col if kind != "line" else MUTED}">{esc(l)}</text>')

    def text(self, x, y, s, size=11, col=MUTED, anchor="middle", weight=400):
        self.P(f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central" font-size="{size}" font-weight="{weight}" fill="{col}">{esc(s)}</text>')

    def write(self):
        markers = "\n".join(
            f'    <marker id="m-{k}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="{c}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></marker>'
            for k, c in MARKERS.items())
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" font-family="{FONT}" role="img" aria-labelledby="{self.name}-title {self.name}-desc">\n'
               f'  <title id="{self.name}-title">{esc(self.title)}</title>\n'
               f'  <desc id="{self.name}-desc">{esc(self.desc)}</desc>\n'
               f'  <defs>\n{markers}\n  </defs>\n'
               f'  <rect width="{self.w}" height="{self.h}" fill="#FFFFFF"/>\n'
               + "\n".join("  " + s for s in self.out) + "\n</svg>\n")
        (POST / f"{self.name}.svg").write_text(svg)
        print("ok", self.name)


# 가로 한 줄에 상자 n개를 균등 배치하고, 상자 사이에 화살표를 그린다. 상자 좌표 목록을 돌려준다.
def hrow(d, y, items, w, h, x0=20, gap=None, total=None, kind="node", edge_labels=None, edge_kind="line"):
    total = total or (d.w - 2 * x0)
    n = len(items)
    gap = gap if gap is not None else (total - n * w) / (n - 1)
    boxes = []
    for i, it in enumerate(items):
        title, sub = (it, ()) if isinstance(it, str) else (it[0], it[1:])
        k = kind[i] if isinstance(kind, (list, tuple)) else kind
        x = x0 + i * (w + gap)
        boxes.append(d.node(x, y, w, h, title, sub, k))
    for i in range(n - 1):
        x1 = boxes[i][0] + w
        x2 = boxes[i + 1][0]
        lab = edge_labels[i] if edge_labels else None
        d.edge([(x1 + 2, y + h / 2), (x2 - 2, y + h / 2)], lab, kind=edge_kind)
    return boxes


def right(b):
    return b[0] + b[2], b[1] + b[3] / 2


def left(b):
    return b[0], b[1] + b[3] / 2


def bottom(b):
    return b[0] + b[2] / 2, b[1] + b[3]


def top(b):
    return b[0] + b[2] / 2, b[1]


# ---------------------------------------------------------------- 1. 실습 순서
def lab_order():
    d = D("ch7-lab-order", 960, 130, "7장 진행 단계",
          "준비 하나와 본 단계 다섯 개가 왼쪽에서 오른쪽으로 이어진다. 0 준비: 데이터 적재. A 단계: 값과 경로 전달. B 단계: 아티팩트 타입. C 단계: 아티팩트로 잇는 파이프라인. D 단계: 고정 경로로 잇는 파이프라인. E 단계: target_image.")
    items = ["준비", "A. 값과 경로", "B. 아티팩트 타입", "C. 아티팩트 연결", "D. 고정 경로 연결", "E. target_image"]
    hrow(d, 30, items, 136, 70, kind=["dim", "node", "node", "pipe", "emph", "node"])
    d.write()


# ---------------------------------------------------------------- 2. 입력과 출력
def problem_io():
    d = D("problem-io", 960, 250, "입력과 출력",
          "입력은 주소(필수), 専有面積·築年·所在階·間取り(필수), 総階数·徒歩分·向き(선택)이다. 주소는 지오코딩으로 위도·경도가 되어 회귀 모델에 들어간다. 모델의 타깃은 log(万円/m²)이고 출력은 추정 가격(万円)과 80% 구간이다.")
    d.group(20, 20, 300, 210, "입력")
    a = d.node(40, 50, 260, 46, "주소 (필수)")
    b = d.node(40, 108, 260, 50, "면적, 준공 연도, 층, 방 구조 (필수)", size=12)
    c = d.node(40, 170, 260, 46, "총 층수, 도보 분, 방향 (선택)", size=12)
    g = d.node(380, 42, 160, 62, "지오코딩", ["위도, 경도"], "pipe")
    m = d.node(600, 90, 170, 70, "회귀 모델", ["타깃: m²당 단가(만엔)"], "emph")
    o = d.node(820, 90, 120, 70, "추정 가격", ["만엔(万円)", "80% 구간"], "emph")
    d.edge([right(a), (340, right(a)[1]), (340, 73), left(g)])
    d.edge([right(g), (570, 73), (570, 110), (m[0] - 2, 110)], kind="pipe")
    d.edge([right(b), (570, right(b)[1]), (570, 125), (m[0] - 2, 125)])
    d.edge([right(c), (570, right(c)[1]), (570, 140), (m[0] - 2, 140)])
    d.edge([right(m), left(o)], kind="emph")
    d.write()


# ---------------------------------------------------------------- 3. RustFS 적재
def rustfs_staging():
    d = D("rustfs-staging", 960, 200, "S3 호환 버킷에 미리 올려 둘 것",
          "매물 통합 CSV 하나를 datasets 버킷의 suumo/raw/2026-11-13/tokyo_23ku_all.csv 로 올린다. A ~ E 모든 단계가 이 파일 하나를 읽는다. 좌표 데이터는 공개 URL 에서 파이프라인이 직접 받는다.")
    s1 = d.node(20, 40, 190, 56, "매물 CSV")
    d.group(300, 20, 360, 100, "버킷 datasets", "pipe")
    r1 = d.node(320, 48, 320, 56, "tokyo_23ku_all.csv", kind="pipe")
    c1 = d.node(760, 40, 180, 56, "A ~ E 단계")
    d.edge([right(s1), left(r1)], "한 번 업로드")
    d.edge([right(r1), left(c1)], kind="pipe")
    s2 = d.node(20, 130, 190, 50, "위치참조정보 zip", kind="dim")
    c2 = d.node(760, 130, 180, 50, "D, E 단계", kind="dim")
    d.edge([right(s2), (c2[0] - 2, 155)], "버킷을 거치지 않는다", lpos=(480, 142), dashed=True)
    d.write()


# ---------------------------------------------------------------- 4. A 단계
def lab_a():
    d = D("lab-a-flow", 960, 140, "A 단계: 값과 경로 전달",
          "export_ward(ward: str) 가 Output[Artifact] 디렉터리 경로로 CSV 를 넘기고, count_rows 가 int 값을 반환하고, output_result 가 str 값을 반환해 Rows: 3565 같은 결과가 나온다.")
    items = [("export_ward", "ward: str"), ("count_rows",), ("output_result",), ("Rows: 3565",)]
    boxes = hrow(d, 50, items, 160, 64, x0=30, kind=["pipe", "pipe", "pipe", "dim"])
    for i, lab in enumerate(["Output[Artifact]\n디렉터리 경로", "int\n값", "str\n값"]):
        x = (boxes[i][0] + boxes[i][2] + boxes[i + 1][0]) / 2
        d.edge([(x, 48), (x, 48)], lab, lpos=(x, 28), arrow=False)
    d.write()


# ---------------------------------------------------------------- 5. B 단계
def lab_b():
    d = D("lab-b-types", 960, 330, "B 단계: 타입별 출력",
          "prepare_dataset 이 S3 호환 버킷의 통합 CSV 를 읽고, prepare_dataset 은 Dataset 과 Artifact(config.json)를 낸다. fit_baseline 이 Model 을, evaluate_baseline 이 Metrics(MAE, MAPE), ClassificationMetrics(가격대 혼동 행렬), SlicedClassificationMetrics(구별 가격대 지표), HTML(오차 분포 리포트), Markdown(데이터 카드)를 낸다.")
    i = d.node(20, 40, 130, 56, "S3 호환 버킷", ["통합 CSV"], "dim")
    p = d.node(200, 40, 160, 56, "prepare_dataset", kind="pipe")
    f = d.node(410, 40, 150, 56, "fit_baseline", kind="pipe")
    e = d.node(410, 180, 150, 56, "evaluate_baseline", kind="pipe")
    cfg = d.node(200, 180, 160, 56, "config.json", ["분할 비율, 컬럼 목록"])
    outs = [("Metrics", ""), ("ClassificationMetrics", ""), ("SlicedClassificationMetrics", ""), ("HTML", ""), ("Markdown", "")]
    d.edge([right(i), left(p)])
    d.edge([right(p), left(f)], "Dataset", kind="pipe")
    d.edge([bottom(p), top(cfg)], "Artifact", kind="pipe")
    d.edge([bottom(f), top(e)], "Model", kind="pipe")
    d.edge([(p[0] + 110, p[1] + p[3]), (p[0] + 110, 150), (385, 150), (385, 208), (e[0] - 2, 208)], "Dataset", kind="pipe", lpos=(385, 150))
    ys = [30, 88, 146, 204, 262]
    for (title, typ), y in zip(outs, ys):
        o = d.node(700, y, 240, 46, title, [typ], "emph")
        d.edge([right(e), (620, right(e)[1]), (620, y + 23), (o[0] - 2, y + 23)], kind="emph")
    d.write()


# ---------------------------------------------------------------- 7. C 단계 파이프라인
def lab_c_pipe():
    d = D("lab-c-pipeline", 960, 230, "C 단계: suumo-artifact-passing",
          "download_dataset 이 Output[Dataset] 으로 CSV 를 넘기고, split_dataset(random_state=42)이 train_dataset, validation_dataset, test_dataset 세 개를 낸다. validation_dataset 만 output_file_contents 로 가서 파일 트리와 행 수를 로그로 남긴다. train 과 test 는 이후 학습과 평가에서 쓴다.")
    dl = d.node(20, 86, 160, 56, "download_dataset", kind="pipe")
    sp = d.node(260, 86, 160, 56, "split_dataset", ["random_state=42"], "pipe")
    t1 = d.node(600, 20, 150, 46, "train_dataset", ["이후 학습에서 사용"], "dim")
    o = d.node(600, 92, 180, 46, "output_file_contents", kind="pipe")
    t3 = d.node(600, 164, 150, 46, "test_dataset", ["이후 평가에서 사용"], "dim")
    lg = d.node(820, 92, 120, 46, "로그", ["파일 트리, 행 수"], "dim")
    d.edge([right(dl), left(sp)], "Output[Dataset]\n매물 CSV 32,593행", kind="pipe", lpos=(220, 62))
    d.edge([right(sp), (470, 114), (470, 43), left(t1)], "train_dataset", lpos=(535, 30), kind="pipe", lsize=10)
    d.edge([right(sp), left(o)], "validation_dataset", lpos=(535, 100), kind="pipe", lsize=10)
    d.edge([right(sp), (470, 114), (470, 187), left(t3)], "test_dataset", lpos=(535, 200), kind="pipe", lsize=10)
    d.edge([right(o), left(lg)])
    d.write()


# ---------------------------------------------------------------- 8. D 단계 파이프라인
def lab_d_pipe():
    d = D("lab-d-pipeline", 960, 660, "D 단계: suumo-data-prep",
          "왼쪽 열: download_raw(버킷의 통합 CSV) → csv_to_parquet(utf-8-sig) → clean_dedup → geocode → split_dataset(丁目 그룹 75/15/10) → put_to_minio u2(train/val/test) → qa_data. 오른쪽 열: download_geo(位置参照情報 zip) → unzip_data → csv_to_parquet-2(cp932) → put_to_minio u1(chome.parquet). csv_to_parquet-2 의 출력은 geocode 에도 들어간다. split_dataset 은 eda_report 로도 간다. qa_data 는 u1, u2 가 모두 끝난 뒤 .after(u1, u2) 로 실행되며 고정 경로에서 읽는다.")
    W, H, step = 220, 56, 84
    ax, bx = 110, 560
    ya = lambda r: 24 + r * step
    imp = d.node(ax, ya(0), W, H, "download_raw", kind="pipe")
    p1 = d.node(ax, ya(1), W, H, "csv_to_parquet", ["utf-8-sig"], "pipe")
    cl = d.node(ax, ya(2), W, H, "clean_dedup", kind="pipe")
    ge = d.node(ax, ya(3), W, H, "geocode", kind="pipe")
    sp = d.node(ax, ya(4), W, H, "split_dataset", ["초메(丁目) 그룹 75 / 15 / 10"], "emph")
    u2 = d.node(ax, ya(5), W, H, "put_to_minio (u2)", ["train / val / test"], "pipe")
    qa = d.node(ax, ya(6) + 16, W, H, "qa_data", ["고정 경로에서 읽음"], "emph")
    dg = d.node(bx, ya(0), W, H, "download_geo", ["위치참조정보(位置参照情報) zip"], "pipe")
    uz = d.node(bx, ya(1), W, H, "unzip_data", kind="pipe")
    p2 = d.node(bx, ya(2), W, H, "csv_to_parquet-2", ["cp932"], "pipe")
    u1 = d.node(bx, ya(3), W, H, "put_to_minio (u1)", ["chome.parquet"], "pipe")
    ed = d.node(bx, ya(5), W, H, "eda_report", kind="pipe")
    for a, b in [(imp, p1), (p1, cl), (cl, ge), (ge, sp), (sp, u2), (dg, uz), (uz, p2), (p2, u1)]:
        d.edge([bottom(a), (top(b)[0], top(b)[1] - 2)], kind="pipe")
    d.edge([bottom(u2), (top(qa)[0], top(qa)[1] - 2)], ".after(u1, u2)", kind="emph", dashed=True, lpos=(ax + W / 2 + 62, ya(6) - 6))
    qy = ya(6) + 16 + H / 2
    d.edge([right(u1), (bx + W + 30, right(u1)[1]), (bx + W + 30, qy), (ax + W + 2, qy)], kind="emph", dashed=True)
    # csv_to_parquet-2 → geocode (대각)
    d.edge([left(p2), (bx - 60, left(p2)[1]), (bx - 60, ya(3) + H / 2), (ax + W + 2, ya(3) + H / 2)], kind="pipe")
    # split → eda_report
    d.edge([right(sp), (bx - 60, right(sp)[1]), (bx - 60, ya(5) + H / 2), (bx - 2, ya(5) + H / 2)], kind="pipe")
    d.write()


# ---------------------------------------------------------------- 9. clean_dedup
def clean_steps():
    d = D("clean-dedup-steps", 960, 330, "clean_dedup 처리 순서",
          "원본 32,593행 → 사용할 컬럼 15개만 남김 → 같은 매물 중복 제거(物件名, 住所, 価格, 面積, 所在階 기준) → 약 24,131행 → 준공 2027년 이후 매물 제외 → 構造 57종을 RC/SRC/S/기타로 정리 → 築年数 제거, 築年만 유지 → unit_price 추가(価格_万円 / 専有面積_m2) → 같은 구 중앙 단가의 10배를 넘는 가격 오류 제외 → 24,117행.")
    r1 = [("원본", "32,593행"), ("컬럼 15개만 남김",), ("같은 매물 중복 제거", "물건명, 주소, 가격,", "면적, 층이 같으면 하나만"), ("약 24,131행",)]
    r2 = [("unit_price 추가", "가격_만엔 / 전용 면적"), ("건물 연식(築年数) 제거", "준공 연도(築年)만 유지"), ("구조(構造) 정리", "57종 → RC / SRC / S / 기타"), ("준공 2027년 이후 제외",)]
    top_boxes = hrow(d, 24, r1, 200, 64, x0=30, kind=["dim", "node", "emph", "dim"])
    xs = [b[0] for b in top_boxes]
    bot = []
    for (title, *sub), x in zip(r2, xs):
        bot.append(d.node(x, 160, 200, 64, title, sub, "emph" if title.startswith("unit") else "node"))
    last = top_boxes[-1]
    d.edge([bottom(last), (top(bot[-1])[0], top(bot[-1])[1] - 2)])
    for i in range(3, 0, -1):
        d.edge([left(bot[i]), (right(bot[i - 1])[0] + 2, right(bot[i - 1])[1])])
    pf = d.node(xs[0], 260, 200, 50, "가격 오류 제외", kind="warn")
    fin = d.node(xs[1], 260, 200, 50, "24,117행", kind="dim")
    d.edge([bottom(bot[0]), (top(pf)[0], top(pf)[1] - 2)], kind="warn")
    d.edge([right(pf), (left(fin)[0] - 2, left(fin)[1])])
    d.write()


# ---------------------------------------------------------------- 10. geocode
def geocode_flow():
    d = D("geocode-flow", 960, 520, "geocode 처리 흐름",
          "東京都千代田区外神田３ → NFKC 정규화(ヶ를 ケ로, 구분자 통일) → 区/町名/丁目 분해(千代田区/外神田/3) → 丁目 일치? 예(93.2%)면 丁目 좌표, 아니오면 町名 일치? 예(6.8%)면 町 좌표, 아니오면 제외하고 건수를 Metrics 에 기록. 좌표가 붙으면 lat, lon, chome_key, geo_level 컬럼을 추가한다.")
    cx = 320
    a = d.node(cx - 130, 14, 260, 56, "도쿄도 치요다구 소토칸다 3", ["東京都千代田区外神田３"], kind="dim")
    b = d.node(cx - 130, 96, 260, 56, "NFKC 정규화", ["ヶ → ケ, 구분자 통일"], "pipe")
    c = d.node(cx - 130, 182, 260, 56, "구 / 동 / 초메로 분해", ["치요다구 / 소토칸다 / 3"], "pipe")
    d.edge([bottom(a), (cx, 94)])
    d.edge([bottom(b), (cx, 180)], kind="pipe")
    d.edge([bottom(c), (cx, 273)], kind="pipe")
    d.diamond(cx, 310, 200, 70, "초메(丁目) 일치?")
    d.edge([(cx + 100, 310), (560 - 2, 310)], "예 (93.2%)", kind="emph", lpos=(455, 296))
    e = d.node(560, 285, 150, 50, "초메(丁目) 좌표", kind="emph")
    d.edge([(cx, 345), (cx, 425 - 2)], "아니오", lpos=(cx + 32, 385))
    d.diamond(cx, 460, 200, 70, "동(町名) 일치?")
    d.edge([(cx + 100, 460), (560 - 2, 460)], "예 (6.8%)", kind="emph", lpos=(455, 446))
    g = d.node(560, 435, 150, 50, "동(町) 좌표", kind="emph")
    h = d.node(20, 435, 130, 50, "제외", ["Metrics 에 건수 기록"], "warn")
    d.edge([(cx - 100, 460), (h[0] + h[2] + 2, 460)], "아니오", lpos=(185, 446), kind="warn")
    i = d.node(760, 345, 180, 70, "컬럼 추가", ["lat, lon", "chome_key, geo_level"], "emph")
    d.edge([right(g), (735, 460), (735, 380)], kind="emph", arrow=False)
    d.edge([right(e), (735, 310), (735, 380), (i[0] - 2, 380)], kind="emph")
    d.write()


# ---------------------------------------------------------------- 11. 분할 비교
def split_compare():
    d = D("split-random-vs-group", 960, 250, "무작위 분할과 丁目 그룹 분할",
          "C 단계의 무작위 분할은 外神田3 의 매물 A 를 train, 매물 B 를 test 에 넣어 같은 丁目 가 양쪽에 들어간다. D 단계의 丁目 그룹 분할은 外神田3 의 매물 A 와 B 를 모두 train 에, 高輪3 의 매물 C 를 test 에 넣는다.")
    d.group(20, 20, 440, 210, "C 단계: 무작위 분할", "warn")
    a1 = d.node(50, 60, 170, 46, "소토칸다 3 매물 A", ["外神田3"])
    a2 = d.node(50, 150, 170, 46, "소토칸다 3 매물 B", ["外神田3"])
    tr = d.node(290, 60, 140, 46, "train", kind="pipe")
    te = d.node(290, 150, 140, 46, "test", kind="warn")
    d.edge([right(a1), left(tr)])
    d.edge([right(a2), left(te)], kind="warn")
    d.group(500, 20, 440, 210, "D 단계: 초메(丁目) 그룹 분할", "emph")
    b1 = d.node(530, 44, 170, 40, "소토칸다 3 매물 A", ["外神田3"])
    b2 = d.node(530, 104, 170, 40, "소토칸다 3 매물 B", ["外神田3"])
    b3 = d.node(530, 170, 170, 40, "타카나와 3 매물 C", ["高輪3"])
    tr2 = d.node(770, 54, 140, 46, "train", kind="pipe")
    te2 = d.node(770, 167, 140, 46, "test", kind="emph")
    d.edge([right(b1), (740, 64), (740, 72), (tr2[0] - 2, 72)])
    d.edge([right(b2), (740, 124), (740, 82), (tr2[0] - 2, 82)])
    d.edge([right(b3), left(te2)], kind="emph")
    d.write()


# ---------------------------------------------------------------- 12. QA 게이트
def qa_gate():
    d = D("qa-gate", 960, 400, "qa_data 가 읽는 고정 경로와 검사",
          "datasets/suumo/prepared/2026-11-13/ 의 train.parquet, val.parquet, test.parquet, chome.parquet 를 pyarrow fs.S3FileSystem 으로 읽어 검사 7개를 한다: 파일 4개 존재, 분할 간 chome_key 중복 0, 분할 간 物件ID 중복 0, 행 비율 75/15/10 ±2%p, 좌표 결측 0, 같은 구 중앙 단가의 10배 이하, 23구가 모든 분할에 존재. 모두 통과하면 Markdown 리포트와 Metrics 를 기록하고, 아니면 태스크가 실패한다.")
    d.group(20, 20, 920, 96, "고정 경로", "pipe")
    files = ["train.parquet", "val.parquet", "test.parquet", "chome.parquet"]
    for i, f in enumerate(files):
        d.node(50 + i * 220, 50, 200, 46, f, kind="pipe")
    q = d.node(400, 150, 160, 46, "qa_data", kind="emph")
    d.edge([(480, 116), (480, 148)], kind="pipe")
    checks = ["파일 4개 존재", "chome_key 중복 0", "물건 ID 중복 0", "행 비율 ±2%p", "좌표 결측 0", "단가 10배 이하", "23구 모두 존재"]
    cw, cgap = 122, 10
    x0 = (960 - (7 * cw + 6 * cgap)) / 2
    for i, c in enumerate(checks):
        x = x0 + i * (cw + cgap)
        b = d.node(x, 230, cw, 44, c, kind="node", size=11)
        d.edge([bottom(q), (bottom(q)[0], 215), (x + cw / 2, 215), (x + cw / 2, 228)], kind="emph")
        d.edge([bottom(b), (x + cw / 2, 290), (480, 290), (480, 304)])
    d.diamond(480, 335, 170, 56, "모두 통과?")
    ok = d.node(620, 312, 220, 46, "Markdown 리포트, Metrics 기록", kind="emph", size=12)
    ng = d.node(130, 312, 200, 46, "태스크 실패", kind="warn")
    d.edge([(565, 335), (ok[0] - 2, 335)], "예", kind="emph", lpos=(592, 322))
    d.edge([(395, 335), (ng[0] + ng[2] + 2, 335)], "아니오", kind="warn", lpos=(362, 322))
    d.write()


# ---------------------------------------------------------------- 13. 컴포넌트 종류
def component_kinds():
    d = D("component-kinds", 960, 130, "컴포넌트를 만드는 세 가지 방식",
          "경량 파이썬 컴포넌트(dsl.component, 실행할 때 pip install) → 컨테이너화된 파이썬 컴포넌트(dsl.component 와 target_image, 빌드할 때 설치) → 컨테이너 컴포넌트(dsl.container_component, 이미지와 명령을 직접 지정).")
    items = [("경량 파이썬 컴포넌트", "dsl.component", "실행할 때 pip install"),
             ("컨테이너화된 파이썬 컴포넌트", "dsl.component + target_image", "빌드할 때 설치"),
             ("컨테이너 컴포넌트", "dsl.container_component", "이미지와 명령을 직접 지정")]
    hrow(d, 24, items, 270, 80, x0=30, kind=["pipe", "emph", "node"])
    d.text(165, 116, "D 단계", 11, TEAL, weight=600)
    d.text(480, 116, "E 단계", 11, GREEN, weight=600)
    d.text(795, 116, "8장", 11, MUTED, weight=600)
    d.write()


# ---------------------------------------------------------------- 14. E 단계 순서
def lab_e_order():
    d = D("lab-e-order", 960, 110, "E 단계 진행 순서",
          "컴포넌트에 target_image 지정 → kfp component build 로 이미지 1개 빌드 → 레지스트리에 push → 컴파일 → run 실행 → D 단계와 비교.")
    items = [("target_image 지정", "컴포넌트에"), ("kfp component build", "이미지 1개 빌드"), ("레지스트리 push",), ("컴파일",), ("run 실행",), ("D 단계와 비교",)]
    hrow(d, 24, items, 140, 60, x0=20, kind=["node", "emph", "node", "node", "node", "emph"])
    d.write()



if __name__ == "__main__":
    POST.mkdir(parents=True, exist_ok=True)
    for fn in [lab_order, problem_io, rustfs_staging, lab_a, lab_b, lab_c_pipe, lab_d_pipe,
               clean_steps, geocode_flow, split_compare, qa_gate, component_kinds, lab_e_order]:
        fn()
