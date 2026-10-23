"""mlpe-03 다이어그램 4장에 제품 마크·Kubernetes 리소스 아이콘을 넣는다.

사용: python3 diagrams/mlpe/inject_icons.py <simpleicons 디렉터리>
  디렉터리에는 https://cdn.simpleicons.org/<slug> 로 받은 kubernetes·argo·docker·github·githubactions .svg 를 둔다.
글의 SVG(content/posts/mlpe/mlpe-03-platform-foundation/*.svg)와 원본 HTML(diagrams/mlpe/*.html)을 함께 고친다.
다시 돌려도 기존 아이콘 블록을 교체하므로 중복되지 않는다. 라이선스: Simple Icons CC0, kubernetes/community 아이콘 Apache-2.0.
"""
import re, sys, xml.etree.ElementTree as ET
from pathlib import Path
ROOT = Path.home()/"myblog"
POST = ROOT/"content/posts/mlpe/mlpe-03-platform-foundation"
SRC  = ROOT/"diagrams/mlpe"
SI   = Path(sys.argv[1])          # simpleicons dir
K8S  = ROOT/"assets/images/icons/kubernetes/icons/resources/unlabeled"
BRAND = {"kubernetes":"#326ce5","argo":"#ef7b4d","docker":"#2496ed","github":"#24292f","githubactions":"#2088ff"}
SVGNS="http://www.w3.org/2000/svg"

def simple(name):
    d = re.search(r'<path d="([^"]+)"', (SI/f"{name}.svg").read_text()).group(1)
    return ("0 0 24 24", f'<path fill="{BRAND[name]}" d="{d}"/>')

def k8s_resource(name):
    """Inkscape 파일에서 그림 요소만 꺼내고 id 는 접두어를 붙여 충돌을 막는다."""
    tree = ET.parse(K8S/f"{name}.svg"); root = tree.getroot()
    vb = root.get("viewBox")
    skip = {"metadata","namedview","defs"}
    out=[]
    def ser(el):
        tag = el.tag.split("}")[-1]
        if tag in skip: return ""
        attrs = {k.split("}")[-1]:v for k,v in el.attrib.items() if "inkscape" not in k and "sodipodi" not in k}
        if "id" in attrs: attrs["id"] = f"k8s-{name}-{attrs['id']}"
        a = " ".join(f'{k}="{v}"' for k,v in attrs.items())
        inner = "".join(ser(c) for c in el)
        return f"<{tag} {a}>{inner}</{tag}>" if inner else f"<{tag} {a}/>"
    body = "".join(ser(c) for c in root)
    return (vb, body)

def icon_svg(kind, x, y, size, bg=True):
    vb, body = simple(kind) if kind in BRAND else k8s_resource(kind)
    pad = 3
    chip = f'<rect x="{x-pad}" y="{y-pad}" width="{size+2*pad}" height="{size+2*pad}" rx="3" fill="#f5f5f5"/>' if bg else ""
    return f'{chip}<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="{vb}" aria-hidden="true">{body}</svg>'

# (kind, box x, box y, box w) → top-right inside the node box
def node(kind, bx, by, bw, size=18):
    return icon_svg(kind, bx+bw-8-size, by+6, size, bg=False)
# container label icon: right after the label text
def label(kind, x, y, size=12):
    return icon_svg(kind, x, y, size, bg=True)

PLAN = {
 "gitops-pipeline": [
   node("github",240,80,160), node("githubactions",500,80,180), node("docker",780,80,160),
   node("argo",240,280,160), node("kubernetes",500,280,180), node("docker",780,280,160),
   label("kubernetes",284,245)],
 "homelab-cluster": [
   label("kubernetes",372,69),
   node("svc",264,232,248,16), node("deploy",264,320,248,16),
   node("argo",600,232,256,16), node("argo",600,320,256,16)],
 "app-of-apps": [
   node("github",40,80,160), node("argo",280,80,180), node("argo",540,80,160),
   node("ns",780,80,168), node("docker",780,232,168), label("kubernetes",380,45)],
 "least-privilege-tokens": [
   label("kubernetes",152,45),
   node("secret",64,80,220), node("secret",64,200,220),
   node("argo",364,80,212), node("pod",364,200,212),
   node("github",740,80,192), node("docker",740,200,192)],
}
for name, parts in PLAN.items():
    inj = "\n<!-- icons: Simple Icons(CC0) 브랜드 마크 + kubernetes/community 리소스 아이콘(Apache-2.0) -->\n" + "\n".join(parts) + "\n"
    for p in (POST/f"{name}.svg", SRC/f"{name}.html"):
        s = p.read_text()
        s = re.sub(r"\n<!-- icons:.*?-->\n.*?(?=</svg>\n(?:  </div>|\Z))", "\n", s, flags=re.S) if "<!-- icons:" in s else s
        i = s.rfind("</svg>")
        s = s[:i].rstrip("\n") + inj + s[i:]
        p.write_text(s)
    print("ok", name)
