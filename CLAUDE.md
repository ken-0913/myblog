# `블로그 작업 가이드라인 (CLAUDE.md)

> 이 문서는 Claude Code가 이 저장소에서 작업할 때 지켜야 할 규칙을 정의합니다.
> 매 세션 자동으로 읽히므로, 여기에 적힌 내용은 기본 동작보다 우선합니다.

## 프로젝트 개요

<!-- 이 블로그가 무엇인지, 어떤 기술 스택을 쓰는지 한두 줄로 적으세요. -->

<!-- 예: Hugo 정적 블로그 / DoIt 테마 / GitHub(main 브랜치) 푸시로 발행 -->

- 종류:  Hugo 정적 블로그
- 테마: DoIt 테마 
- 배포 방식:  GitHub(main 브랜치) 푸시로 발행
- 기술 스택 : Kubernetes, Network, Golang

---

## 커밋 규칙

<!-- 커밋 메시지 형식, 언어(한글/영어), 커밋 단위, add 범위 등을 적으세요. -->

- 커밋 메세지 형식은 특정하지 않음.

## 배포 / 발행

<!-- 어떻게 하면 블로그에 글이 올라가는지, 어떤 브랜치에 푸시하는지 적으세요. -->

- main 브랜치 푸시할 경우 발행

## 이메일 / 개인정보

<!-- 커밋에 어떤 이메일을 써야 하는지, 노출하면 안 되는 정보가 무엇인지 적으세요. -->

- 전화번호 형식 (070이나 080으로 시작하는 일본 전화번호)

## 글 작성 규칙

<!-- 새 글의 위치(content/posts 등), front matter 필드, 파일명 규칙 등을 적으세요. -->

- 새 글 위치: `content/posts/` 아래에 마크다운(`.md`) 파일로 작성.
- front matter의 `date`는 **작성 시점보다 과거**로 둔다(미래 날짜는 Hugo가 빌드에서 제외 → 발행 누락).
- 스터디 글은 front matter에 `series: ["MLPE 1주차"]`처럼 **주차 시리즈**를 넣는다. 카테고리·섹션 목록 페이지가 연도 아래 이 이름으로 묶어 보여 주고(`layouts/_partials/archive-groups.html`), `/series/<이름>/` 페이지와 글 하단 이전·다음 내비게이션이 생긴다. 이름 형식은 `<스터디 약칭> N주차`로 통일한다.
- 글 번들(`index.md` 가 있는 디렉터리) 안에 보조 마크다운 파일을 두고 본문에서 `{{% include "파일.md" %}}` 로 끌어다 쓸 수 있다(`layouts/_shortcodes/include.html`). 예: `mlpe-04-mlflow-feast/homelab-practice-4-1.md`. 보조 파일은 별도 페이지로 발행되지 않고, 포함된 소제목은 글의 목차에 들어간다. **반드시 `%` 표기**로 부른다. `<` 표기로 부르면 마크다운이 그대로 노출된다.

### 코드블록 렌더 규칙 (중요)

- **`json` / `yaml` / `bash` / `python` 코드블록은 "터미널 창" 디자인으로 자동 렌더된다.** 코드를 넣을 때 언어를 이 넷 중 하나로 지정하면(``` ```json ```/``` ```yaml ```/``` ```bash ```/``` ```python ```), 빨강·노랑·초록 점이 있는 다크 터미널 창 + 구문 강조로 표시된다.
- 이 동작은 render hook이 담당한다: `layouts/_markup/render-codeblock-{bash,yaml,json,python}.html` → 공용 `layouts/_partials/term-codeblock.html`. 창 스타일은 `assets/css/_custom.scss`의 `.term-code`가 담당한다. 상단 바의 "복사" 버튼은 `layouts/_partials/term-copy.html`(버튼 + 페이지당 한 번 넣는 스크립트)이고 `terminal`·`termcast` 창에도 같이 들어간다. terminal/termcast 는 `$ ` 명령어 줄만 복사한다. **이 파일들을 지우거나 덮어쓰지 말 것.**
- 다른 언어를 추가하려면 `layouts/_markup/render-codeblock-<lang>.html` 파일을 만들고 한 줄만 넣으면 된다: `{{- partial "term-codeblock.html" . -}}`
- 창 제목은 언어명이 기본이며, `{title="..."}` 속성으로 바꿀 수 있다(예: ``` ```bash {title="deploy.sh"} ```).
- **셸 명령 위주**로 `$ 프롬프트` 형태를 강조하고 싶을 때만 별도의 `terminal` 펜스(``` ```terminal ```)를 쓴다. 그 외 일반 코드는 위 세 언어를 쓴다.
- ASCII 다이어그램·구조도는 코드블록 대신 `mermaid`(플로우차트) 또는 `plantuml`(시퀀스 등)로 그린다.

### 편집기가 수식을 깨뜨렸을 때

깨진 채로 커밋되는 것은 pre-commit 훅이 막는다. 새로 clone한 환경에서는 한 번 활성화해야 한다.

```bash
git config core.hooksPath .githooks
```


리치 텍스트 계열 편집기가 저장하면서 인라인 수식 `\(...\)`, `{{< shortcode >}}`, `<br/>` 를 훼손하는 경우가 있다. **내용 편집은 남기고 손상만 되돌린다.**

```bash
python3 scripts/repair_markdown.py <파일>          # 복구
python3 scripts/repair_markdown.py --check <파일>  # 진단만
```

git의 정상본을 기준으로 3-way 병합하므로, 그 파일에 직접 한 편집은 보존된다. **수식이 든 줄을 직접 고친 경우에만** 충돌이 나는데, 이때는 파일을 쓰지 않고 충돌 지점을 보여준다.

`content/` 전체를 되돌리는 `git checkout` 은 내용 편집까지 날리므로 쓰지 말 것.

### 생성되는 글 (직접 고치지 말 것)

- `content/posts/llm/llm-series-all-in-one.md` 는 `scripts/build_all_in_one.py` 로 **처음 만들어졌지만, 이후 손으로 많이 다듬어졌다.** 지금은 직접 편집하는 문서로 본다.
- **이 파일에 `build_all_in_one.py` 를 다시 돌리지 말 것.** 손편집이 전부 사라진다. 생성 결과와 다르면 스크립트가 알아서 중단한다(`--force` 로만 강제).
- 편집기가 서식을 깨뜨렸을 뿐이라면 **재생성이 아니라 복구**를 쓴다.
  ```bash
  python3 scripts/repair_markdown.py --take-theirs content/posts/llm/llm-series-all-in-one.md
  ```
- 개별 글(`llm-03`~`llm-08`)의 수정은 통합본에 자동 반영되지 않는다. 필요하면 통합본에도 같은 수정을 직접 한다.

### 소제목(heading)과 본문 간격

<!-- 가독성을 위해 소제목 위 여백은 넓게, 소제목~내용 간격은 좁게 유지한다. -->

- 구조: **소제목(`#`/`##`) → 한 줄 비우고 내용 → 내용이 끝나면 빈 줄 → 다음 소제목** 순서로 작성.
- 마크다운에서 소제목 앞뒤에는 항상 빈 줄을 둔다(빈 줄 개수 자체가 화면 여백을 늘리지는 않지만, 구조를 명확히 하기 위함).
- **화면상 실제 여백**은 `assets/css/_custom.scss`가 담당한다: `#content`의 heading에 위 여백은 넓게(`margin-top`), 아래 여백은 좁게(`margin-bottom`) 적용됨. 이 파일을 지우거나 덮어쓰지 말 것.

### 메타정보와 본문 첫 문장 간격

<!-- 제목·날짜 등 메타정보와 본문 첫 문장이 붙어 보이지 않도록 여백을 둔다. -->

- 메타정보(제목·작성일 등)와 **본문 첫 문장 사이에는 충분한 위 여백**을 둔다.
- **주의**: 마크다운 본문 맨 앞에 빈 줄을 넣어도 Hugo가 제거하므로 화면 여백은 생기지 않는다. 따라서 글마다 빈 줄을 넣지 말 것.
- 이 여백은 `assets/css/_custom.scss`의 `#content { margin-top }`이 담당한다(모든 글에 자동 적용). 이 값을 지우지 말 것.

## 문체 / 톤

<!-- 아래 항목을 채우거나, 원하는 톤의 예시 문장을 직접 적으세요. -->

<!-- 추상적 표현("친근하게")보다 구체적 규칙 + 예시 문장이 더 잘 지켜집니다. -->

- 말투(어미):  ~한다체 (~이다/~다)
- 독자 호칭: 호칭 없음
- 문장 길이:  한 문단 3문장 이내
- 1인칭 표현 : 1인칭 지양
- 기술 용어 표기: 영어 원문 유지(Pod, Deployment)
- 이모지 / 강조:   굵게 강조 허용
- 피해야 할 표현: 과장 광고체 금지, "~것 같다" 같은 애매한 표현 지양
- **em dash(—) 절대 사용 금지.** 쉼표, 마침표, 콜론(:), 괄호로 바꿔 쓴다.
  - `A — B` → `A. B` 또는 `A, B` 또는 `A(B)`
  - en dash(–), 물결표를 제외한 다른 대시류도 쓰지 않는다. 숫자 범위는 `246 ~ 266` 형태로 적는다
- 원하는 톤 예시 문장: "Pod는 Kubernetes에서 배포 가능한 가장 작은 단위이다. 하나의 Pod 안에서 여러 container가 함께 실행되며, 동일한 network namespace와 storage를 공유한다."

## 하지 말아야 할 것

<!-- 절대 하면 안 되는 것들. 예: 히스토리 강제 푸시 금지, 특정 파일 수정 금지 등 -->

- 

---

## 참고

<!-- 자주 쓰는 명령어, 링크, 기타 메모 -->

- 


## 사이트 디자인 (색 체계 · 카드 · 배너)

- 디자인은 색상(hue) 하나를 oklch 로 밝기만 바꿔 쓰는 방식이다. `assets/css/_custom.scss` 맨 위 `:root { --hue: 265; --sat: 0 }` 가 기준이다. `--sat` 는 채도 배율로, 0 이면 지금처럼 연한 회색 무채색이고 1 이면 파랑·보라가 된다. `--primary` / `--surface` / `--line` 같은 사이트 토큰과 DoIt 의 `--global-*` 변수가 여기서 정해진다. 다크 모드는 `html.dark` 블록이 같은 hue 로 다시 매긴다. **색을 바꿀 때는 이 변수만 바꾼다.** 개별 선택자에 색상 코드를 직접 쓰지 않는다.
- 글·소개·목록 페이지는 연한 바탕 위의 흰 카드(`.page.single`, `.page.archive`)다. 홈 글 목록은 요약 하나가 카드 하나이고(`.home[data-posts] .summary`), 오른쪽 칸에 대표 이미지가 들어간다.
- 글 페이지의 대표 이미지는 CSS `order: -1` 로 카드 맨 위에 배너처럼 올라간다. 마크업 순서는 테마 그대로다.
- 웹폰트(Pretendard, JetBrains Mono)는 `layouts/_partials/head/link.html` 이 `<link>` 로 넣는다. 이 파일은 테마의 `head/link.html` 복사본 끝에 폰트 링크만 붙인 것이다. **테마를 업데이트하면 원본과 diff 해서 다시 맞춘다.** `_custom.scss` 의 `--font-sans` / `--font-mono` 와 한 쌍이다.
- 배너(`scripts/gen_banners.py`)는 사이트와 같은 연한 회색 그라디언트에 진회색 제목을 왼쪽에 두고, 오른쪽에 Kubernetes 공식 로고(`assets/images/icons/kubernetes/logo/logo.png`)를 희미한 워터마크로 넣는다. 공식 아이콘 모음과 라이선스는 `assets/images/icons/README.md` 참고(Kubernetes 리소스 아이콘, CNCF 프로젝트 로고, Grafana). 사이트 색을 바꾸면 배너 색 상수도 같이 맞춘다. 제목 영역 폭(`TITLE_MAX_W`)은 홈 카드가 배너의 **오른쪽 끝만 세로로 잘라 쓰는 것**(`layouts/summary.html` 의 `fill 400x500 Right`)과 겹치지 않게 맞춘 값이다. 한쪽을 바꾸면 다른 쪽도 확인한다.
- 터미널 창(`.term`, `.term-code`, `.termcast`)과 손글씨 브랜드(Caveat)는 이 디자인과 별개로 유지한다.
- 본문 이미지는 클릭하면 확대 보기(lightgallery)가 열린다. `hugo.yaml` 의 `params.page.lightgallery` 가 스위치이고, `layouts/_markup/render-image.html` 이 테마와 달리 제목 없는 이미지까지 모두 링크로 감싼다. 이미지 alt 텍스트가 확대 보기의 캡션으로 나오므로 alt 를 성의 있게 쓴다.

## 시크릿 하드코딩 방지 (gitleaks)

- 토큰·비밀번호·키를 글이나 설정에 직접 쓰지 않는다. 예시 명령에는 `<TOKEN>`, `${GH_TOKEN}` 같은 자리표시자를 쓴다.
- 검사는 두 단계다. 로컬은 `.githooks/pre-commit` 이 커밋 전에 staged 변경분을, CI 는 `.github/workflows/gitleaks.yml` 이 push·PR 마다 전체 이력을 검사한다. 훅은 `git config core.hooksPath .githooks` 로 켠다(위 "편집기가 수식을 깨뜨렸을 때" 절과 같은 훅).
- 설정은 `.gitleaks.toml`(기본 규칙 + `public/`, `resources/`, `themes/`, `docs/books/` 제외).
- 오탐은 `.gitleaksignore` 에 지문을 한 줄씩, 왜 오탐인지 주석과 함께 넣는다. 규칙을 끄거나 경로를 통째로 빼서 해결하지 않는다.
- 진짜 시크릿이 걸렸으면 커밋에서 빼는 것으로 끝내지 않는다. 이미 push 했다면 그 키를 먼저 폐기·재발급한다.
