"""홈랩 Feast 피처 스토어 구성도 SVG 생성 (gen_homelab_mlflow.py 와 같은 색·글꼴·도형 체계).

사용: python3 diagrams/mlpe/gen_homelab_feast.py <simpleicons 디렉터리>
  디렉터리에는 https://cdn.simpleicons.org/<slug> 로 받은 kubernetes·jupyter·redis·github .svg 를 둔다.
출력: content/posts/mlpe/mlpe-04-mlflow-feast/homelab-feast.svg(전체) + feast-2-*.svg(실습 절마다 해당 부분만 강조)
      + diagrams/mlpe/homelab-feast.html(원본 보기용 래퍼)
근거: 홈랩 ~/k8s/feast/ 매니페스트와 README, 2026-10-26 클러스터 상태(ns feast, 전부 worker1-gpu).
아이콘: Simple Icons(CC0) 브랜드 마크, kubernetes/community 리소스 아이콘(Apache-2.0, assets/images/icons/kubernetes).
"""
import re, sys, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POST = ROOT / "content/posts/mlpe/mlpe-04-mlflow-feast"
SRC = ROOT / "diagrams/mlpe"
SI = Path(sys.argv[1])          # simpleicons dir
K8S = ROOT / "assets/images/icons/kubernetes/icons/resources/unlabeled"
BRAND = {"kubernetes": "#326ce5", "jupyter": "#f37626", "redis": "#ff4438", "github": "#181717"}

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


def badge(cx, cy, n):
    """흐름 순서 번호. 본문의 ① ② ③ 과 같은 번호를 상자와 화살표에 단다."""
    P(f'<circle cx="{cx}" cy="{cy}" r="8" fill="{ACCENT}" stroke="{PAPER}" stroke-width="1.5"/>')
    P(f'<text x="{cx}" y="{cy+3.5}" fill="#ffffff" font-size="10" font-weight="700" font-family="{SANS}" text-anchor="middle">{n}</text>')


def chip(cx, cy, w, text, color=MUTED, size=8):
    P(f'<rect x="{cx-w/2:g}" y="{cy-6}" width="{w}" height="12" rx="2" fill="{PAPER}"/>')
    P(f'<text x="{cx:g}" y="{cy+3}" fill="{color}" font-size="{size}" font-family="{MONO}" text-anchor="middle" letter-spacing="0.04em">{text}</text>')


def arrow(d, accent=False, dashed=False):
    col = ACCENT if accent else MUTED
    m = "arrow-accent" if accent else "arrow"
    dash = ' stroke-dasharray="4 3"' if dashed else ""
    P(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="1.2"{dash} marker-end="url(#{m})"/>')


W, H = 960, 660


def draw():
    out.clear()
    K("base")
    P(f'<rect width="100%" height="100%" fill="{PAPER}"/>')
    boundary(24, 40, 912, 576, "HOME LAN · 192.168.0.0/24", 124)
    boundary(208, 72, 704, 528, "HOMELAB · K8S v1.36.5 · CILIUM LB IPAM", 188)
    P(icon("kubernetes", 416, 69, 12, bg=True))
    boundary(232, 104, 656, 316, "NS · FEAST · 전부 worker1-gpu", 140)
    boundary(232, 452, 656, 132, "NS · MLFLOW · 4.1 에서 설치", 132)

    # arrows first (boxes cover their ends)
    K("a-gh");      arrow("M 152,278 H 244", dashed=True)                       # GitHub ⇢ prepare-buckets
    K("a-prep");    arrow("M 424,268 H 432 V 470", accent=True)                 # prepare-buckets → RustFS
    K("a-apply");   arrow("M 424,212 H 444 V 470")                              # apply → RustFS (registry 쓰기)
    K("a-matread"); arrow("M 424,164 H 456 V 470")                              # materialize → RustFS (parquet 읽기)
    K("a-matwrite"); arrow("M 424,144 H 460", accent=True)                      # materialize → Redis
    K("a-srv-redis"); arrow("M 680,156 H 652")                                  # feast-server → Redis
    K("a-srv-reg"); arrow("M 680,196 H 668 V 436 H 470 V 470", dashed=True)     # feast-server ⇢ registry
    K("a-ui-reg");  P(f'<path d="M 680,284 H 668 V 436 H 470 V 470" fill="none" stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="4 3" marker-end="url(#arrow)"/>')
    K("a-nb-redis"); arrow("M 640,472 V 212")                                   # Jupyter → Redis
    K("a-nb-s3");   arrow("M 600,520 H 484")                                    # Jupyter → RustFS
    K("a-pc-srv");  arrow("M 96,120 V 88 H 776 V 112")                          # PC → feast-server
    K("a-pc-ui");   arrow("M 96,120 V 88 H 900 V 284 H 876")                    # PC → feast-ui
    K("a-pc-nb");   arrow("M 96,120 V 88 H 900 V 514 H 876")                    # PC → Jupyter

    K("a-pc-srv");  chip(488, 88, 112, "피처 서버 :6566")
    K("a-pc-ui");   chip(820, 88, 120, "UI :8080 · lab :8888")
    K("c-corr");    chip(338, 436, 172, "parquet 업로드 · 레지스트리 쓰기 · 읽기", ACCENT)
    K("c-reg");     chip(568, 436, 104, "레지스트리 읽기")
    K("a-nb-s3");   chip(542, 510, 104, "historical 조회")
    K("a-nb-redis"); chip(640, 460, 92, "online 조회")
    K("a-gh");      chip(196, 278, 56, "raw GET")

    K("pc");   box(40, 120, 112, 64, "PC", "개발 PC", ["브라우저 · curl"], kind="pc")
    K("gh");   box(40, 246, 112, 64, "WEB", "GitHub raw", ["책 저장소 parquet"], kind="pc", tagw=28)
    K("mat");  box(248, 124, 176, 52, "JOB", "feast materialize", ["2022-09-16 ~ 2023-09-17"], kind="small", mark="job", tagw=28)
    K("apply"); box(248, 188, 176, 52, "JOB", "feast apply", ["엔티티 1 · 피처 뷰 3"], kind="small", mark="job", tagw=28)
    K("prep"); box(248, 252, 176, 52, "JOB", "prepare-buckets", ["버킷 2개 · parquet 3개"], kind="small", mark="job", tagw=28)
    K("cm");   box(248, 316, 176, 52, "CM", "feast-repo", ["py 2개 · feature_store.yaml"], kind="small", mark="cm")
    K("sec");  box(248, 376, 176, 36, "SEC", "redis-auth", [], kind="small", mark="secret", tagw=28)
    K("redis"); box(464, 116, 184, 96, "ONL", "Redis 8.10.2", ["온라인 스토어 · StatefulSet", "ClusterIP :6379 · PVC 2Gi", "해시 키 30,162 (사용자당 1)"], mark="redis", tagw=28)
    K("reg");  box(464, 232, 168, 134, "REG", "등록된 피처", ["project my_feature_repo", "entity user_id", "view demographic", "view relationship", "view occupation", "ttl 365d · String 8개"], kind="small", tagw=28)
    K("srv");  box(680, 116, 192, 92, "SRV", "feature server 0.67.0", ["feast serve · Deployment", "POST /get-online-features", "LB 192.168.0.240:6566"], mark="deploy", tagw=28)
    K("ui");   box(680, 244, 192, 76, "UI", "Feast UI", ["feast ui · Deployment", "LB 192.168.0.241:8080"], mark="deploy")
    K("img");  box(680, 340, 192, 64, "IMG", "quay.io/feastdev", ["feature-server:0.67.0", "amd64 전용"], kind="small", tagw=28)
    K("s3");   box(248, 472, 236, 92, "S3", "RustFS 1.0.3", ["worker2-arm64 · rustfs.mlflow.svc:9000", "feature-data-sets · parquet 3개", "feature-registry · registry_local.db"])
    # 흐름 번호: 상자 왼쪽 위 + 해당 화살표 위
    K("prep");  badge(248, 252, 1)
    K("apply"); badge(248, 188, 2)
    K("mat");   badge(248, 124, 3)
    K("a-prep");    badge(432, 300, 1)
    K("a-apply");   badge(444, 340, 2)
    K("a-matread"); badge(456, 380, 3)
    K("a-matwrite"); badge(442, 144, 3)
    K("nb");   box(600, 472, 272, 84, "NB", "JupyterLab", ["Feast SDK 0.67.0 · 커널 chapter-4", "/opt/feast-repo 마운트", "LB 192.168.0.239:8888"], mark="jupyter")

    # legend
    K("base")
    P(f'<line x1="40" y1="628" x2="920" y2="628" stroke="rgba(45,49,66,0.10)" stroke-width="0.8"/>')
    lx = 40
    for sw, txt in [("node", "Pod · 리소스"), ("lb", "LAN 에 노출된 LB IP"), ("acc", "데이터가 오프라인 → 온라인으로 가는 길"), ("dash", "레지스트리 참조 · 외부 다운로드"), ("bnd", "경계 (LAN · 클러스터 · ns)")]:
        if sw == "node":
            P(f'<rect x="{lx}" y="638" width="16" height="12" rx="2" fill="#ffffff" stroke="{INK}" stroke-width="1"/>')
        elif sw == "lb":
            P(f'<text x="{lx}" y="648" fill="{ACCENT}" font-size="9" font-family="{MONO}">192.168.0.x</text>')
        elif sw == "acc":
            P(f'<line x1="{lx}" y1="644" x2="{lx+16}" y2="644" stroke="{ACCENT}" stroke-width="1.2" marker-end="url(#arrow-accent)"/>')
        elif sw == "dash":
            P(f'<line x1="{lx}" y1="644" x2="{lx+16}" y2="644" stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="4 3"/>')
        else:
            P(f'<rect x="{lx}" y="638" width="16" height="12" rx="2" fill="rgba(45,49,66,0.02)" stroke="rgba(45,49,66,0.30)" stroke-width="0.8"/>')
        off = 70 if sw == "lb" else 24
        P(f'<text x="{lx+off}" y="648" fill="{MUTED}" font-size="9" font-family="{SANS}">{txt}</text>')
        lx += off + len(txt) * 7 + 22


def render(focus, uid, title, desc, step=None):
    """focus 가 None 이면 전체를, 아니면 focus 에 든 key 만 진하게 그리고 나머지는 흐리게 둔다. step 이 있으면 왼쪽 위에 절 이름 배지를 단다."""
    draw()
    body = []
    for key, frag in out:
        dim = focus is not None and key != "base" and key not in focus
        body.append(f'<g opacity="0.16">{frag}</g>' if dim else frag)
    if step:
        body.append(f'<rect x="40" y="8" width="{len(step)*7.4+24:g}" height="22" rx="4" fill="{ACCENT}"/>'
                    f'<text x="52" y="23" fill="#ffffff" font-size="11" font-weight="600" font-family="{SANS}">{step}</text>')
    head = f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{uid}-title {uid}-desc">
<title id="{uid}-title">{title}</title>
<desc id="{uid}-desc">{desc}</desc>
<defs>
<style>@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&amp;family=Geist+Mono:wght@400;500;600&amp;display=swap');</style>
<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>
<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker>
</defs>
'''
    return head + "\n".join(body) + "\n<!-- icons: Simple Icons(CC0) 브랜드 마크 + kubernetes/community 리소스 아이콘(Apache-2.0) -->\n</svg>\n"


TITLE = "홈랩 Feast 피처 스토어 구성"
DESC = ("홈랩 Kubernetes 클러스터의 feast 네임스페이스(전부 worker1-gpu)에 Redis 8.10.2 온라인 스토어, feast apply·materialize Job, "
        "feature server 0.67.0, Feast UI 를 올리고, 오프라인 스토어와 레지스트리는 mlflow 네임스페이스의 RustFS 를 같이 쓰는 구성. "
        "① prepare-buckets Job 이 GitHub 에서 parquet 3개를 받아 RustFS feature-data-sets 버킷에 올리고, ② feast apply 가 엔티티 user_id 와 피처 뷰 3개를 "
        "feature-registry 버킷의 registry_local.db 에 등록하고, ③ feast materialize 가 parquet 를 읽어 Redis 에 사용자별 해시 키 30,162개를 쓴다. "
        "피처 서버(192.168.0.240:6566)와 UI(192.168.0.241:8080)는 레지스트리를 읽고 Redis 를 조회하며, JupyterLab 의 Feast SDK 는 RustFS 에서 historical, Redis 에서 online 피처를 가져온다.")
svg = render(None, "hl-feast", TITLE, DESC)
(POST / "homelab-feast.svg").write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + svg)

# 실습 절마다 해당 부분만 강조한 그림 (mlpe-04-1 실습 글의 pipeline-6-* 와 같은 방식)
FOCUS = [
    ("feast-2-1-data", "2.1 피처 파일 준비", {"gh", "a-gh", "prep", "a-prep", "c-corr", "s3"},
     "prepare-buckets Job 이 GitHub 책 저장소에서 parquet 3개를 받아 RustFS feature-data-sets 버킷에 올린다."),
    ("feast-2-2-define", "2.2 피처 정의", {"cm", "sec", "reg", "nb"},
     "entity.py, features.py, feature_store.yaml 을 ConfigMap feast-repo 로 만들어 Job, 서버, UI, Jupyter(/opt/feast-repo)에 마운트한다. Redis 암호는 Secret redis-auth 에서 환경변수로 들어간다."),
    ("feast-2-3-apply", "2.3 feast apply", {"apply", "cm", "reg", "a-apply", "c-corr", "s3"},
     "feast apply 가 정의 파일을 읽어 엔티티 user_id 와 피처 뷰 3개를 RustFS feature-registry 버킷의 registry_local.db 에 등록한다."),
    ("feast-2-4-materialize", "2.4 feast materialize", {"mat", "a-matread", "a-matwrite", "c-corr", "s3", "redis"},
     "feast materialize 가 RustFS 의 parquet 를 읽어 사용자별 최신 값을 Redis 에 해시 키 30,162개로 쓴다."),
    ("feast-2-5-retrieve", "2.5 오프라인 · 온라인 조회", {"nb", "a-nb-s3", "a-nb-redis", "s3", "redis", "pc", "a-pc-nb"},
     "JupyterLab 의 Feast SDK 가 get_historical_features 는 RustFS parquet 에서, get_online_features 는 Redis 에서 읽는다."),
    ("feast-2-6-server", "2.6 피처 서버", {"pc", "a-pc-srv", "srv", "a-srv-redis", "redis", "a-srv-reg", "c-reg", "s3"},
     "개발 PC 가 192.168.0.240:6566 의 feature server 에 POST /get-online-features 를 보내면 서버가 레지스트리를 읽고 Redis 에서 값을 꺼내 돌려준다."),
    ("feast-2-7-ui", "2.7 Feast UI", {"pc", "a-pc-ui", "ui", "a-ui-reg", "c-reg", "s3", "reg"},
     "개발 PC 가 192.168.0.241:8080 의 Feast UI 로 레지스트리에 등록된 엔티티, 피처 뷰, 데이터 소스, 태그를 본다."),
]
for name, step, keys, desc in FOCUS:
    (POST / f"{name}.svg").write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + render(keys, name, f"{TITLE} · {step}", desc, step=step))
    print("ok", name)

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
(SRC / "homelab-feast.html").write_text(html)
print("ok", POST / "homelab-feast.svg", len(svg))
