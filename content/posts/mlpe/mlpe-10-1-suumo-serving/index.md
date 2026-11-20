---
title: "MLPE 스터디 5주차 - Ch10 도쿄 23구 중고 맨션 호가 모델을 BentoML 과 MLflow 로 서빙하기"
date: 2026-11-19T11:00:00+09:00
draft: false
tags: ["MLOps", "MLPE", "BentoML", "MLflow", "Model Serving", "Model Registry", "Docker", "KServe", "LightGBM", "Capstone"]
categories: ["MLOps"]
series: ["MLPE 5주차"]
featuredImage: images/banners/mlpe-10-1-suumo-serving-4f4cafc0.png
---
[9장](../mlpe-09-1-suumo-tracking/)에서 m²당 단가 모델을 MLflow 레지스트리에 `suumo-unit-price@prod` 로 올렸다. 10장에서는 이 모델을 주소와 매물 조건을 보내면 추정 호가를 돌려주는 HTTP 서비스로 만든다.

## 1. 한눈에 보기

### 1.1 만들 서비스

7장에서 세운 목표는 "주소와 조건을 넣으면 그 자리의 호가를 알려 준다" 였다. 지금까지는 노트북에서 모델을 직접 불러 예측했다. 서비스로 만들면 모델을 모르는 사람이나 다른 프로그램도 주소 한 줄로 같은 답을 받는다.

```terminal {title="만들 서비스에 보내는 요청과 응답"}
$ curl -s -X POST http://localhost:3000/estimate -H 'Content-Type: application/json' \
    -d '{"address":"東京都世田谷区三軒茶屋2","area":70,"year":2015,"floor":5,"floors":10,"walk":7,"layout":"3LDK","structure":"RC","facing":"南"}'
{"address":"東京都世田谷区三軒茶屋2","chome_key":"世田谷区三軒茶屋2","geo_level":"chome","unit_price":214.6,"price":15020,"low":10210,"high":17550,"model":"suumo_unit_price:vsn4dnxec6bypbz4"}
```

세타가야구 산겐자야(世田谷区三軒茶屋) 2초메의 70m², 2015년 준공 매물이면 추정 호가는 1억 5,020만엔이고, 80% 구간은 1억 210만엔 ~ 1억 7,550만엔이다. 9장의 노트북에서 같은 모델로 뽑은 값과 같다.

### 1.2 진행 단계

![10장 전체 흐름. 위쪽 줄은 빌드 과정이다. MLflow 모델 레지스트리의 prod 별칭(v4) 모델을 import_model 로 BentoML 모델 스토어에 가져오고, build 로 코드와 모델과 의존성을 묶은 Bento 를 만들고, containerize 로 컨테이너 이미지를 만든다. Bento 를 serve 하면 아래쪽 BentoML Service 가 뜬다. 사용자가 주소와 조건을 POST /estimate 로 보내면 API 서버가 입력을 검증하고 주소를 좌표로 바꾼 뒤 suumo_prod Runner(v4)에 넘긴다. /compare 는 같은 입력을 suumo_v1 Runner(v1)에도 보낸다.](ch10-overview-stack.png)

- **A. 서비스의 구조 이해하기**
  - BentoML 서비스는 요청을 받는 API 서버와 모델을 돌리는 Runner 로 나뉜다. 왜 둘로 나누는지를 먼저 본다.
- **B. 모델 파일로 가장 단순한 서비스 만들기**
  - 모델 파일을 폴더에 내려받아 두고, 그 폴더를 읽는 서비스를 코드 30줄 안팎으로 만든다. 내 PC 에서 띄워 요청을 보내 본다.
- **C. 레지스트리의 prod 모델로 바꾸기**
  - 모델 파일 경로를 코드에 적는 대신, 9장에서 `prod` 이름표를 붙인 모델을 레지스트리에서 가져오게 바꾼다. 입력도 좌표가 아니라 주소로 받는다.
- **D. 모델 두 개를 동시에 돌려 비교하기**
  - Runner 를 하나 더 붙여, 같은 요청을 지금 모델(v4)과 예전 모델(v1)에 함께 보내고 답을 나란히 받는다.
- **E. 서비스 상태 확인하기**
  - 서비스가 살아 있는지 알려 주는 주소와, 요청 수와 응답 시간을 숫자로 내주는 주소가 처음부터 들어 있다. 직접 만들지 않아도 된다는 것을 확인한다.
- **F. 배포 단위로 묶기**
  - 코드, 모델, 필요한 패키지를 Bento 라는 꾸러미 하나로 묶고, 그것으로 컨테이너 이미지를 만들어 실행한다.
- **G. MLflow 만으로 서빙하기**
  - BentoML 없이 MLflow 명령 한 줄로도 같은 모델을 서비스로 띄울 수 있다. 무엇이 같고 무엇이 다른지 비교한다.

## 2. 서비스의 구조

### 2.1 모델 서빙에서 따져야 할 것

모델을 서비스로 내놓는 일은 일반 웹 서비스 배포에 몇 가지가 더 붙는다. 이 글의 서비스에 해당하는 것만 고르면 이렇다.

| 따질 것 | 이 서비스에서 |
| --- | --- |
| 추론 방식 (실시간, 배치) | 실시간. 주소 한 건을 받아 바로 답한다 |
| 데이터 의존성 | 주소를 좌표로 바꾸는 표가 서비스 안에 있어야 한다. 학습 때와 같은 표를 쓴다 |
| 모델 버전 | 레지스트리의 `prod` 별칭이 가리키는 버전을 쓰고, 응답에 어느 모델인지 적는다 |
| 하드웨어 | CPU 로 충분하다. LightGBM 은 시스템 라이브러리 `libgomp1` 이 필요하다 |
| 모니터링 | 상태 확인 주소와 Prometheus 지표를 내준다 |

### 2.2 API 서버와 Runner

BentoML 서비스는 프로세스 두 종류로 돈다.

| | API 서버 | Runner |
| --- | --- | --- |
| 하는 일 | HTTP 요청을 받고, 입력을 검사하고, 모델에 넣을 모양으로 바꾼다 | 모델을 메모리에 올려 두고 예측만 한다 |
| 이 서비스에서 | 주소를 좌표로 바꾸고, 응답 JSON 을 만든다 | LightGBM 모델 세 개로 단가와 구간을 계산한다 |
| 늘리는 기준 | 동시에 들어오는 요청 수 | 예측에 드는 계산량 |

둘을 나누면 요청이 몰릴 때는 API 서버만, 모델이 무거울 때는 Runner 만 따로 늘릴 수 있다. Runner 를 여러 종류 두는 것도 가능해서, 6절에서 모델 두 개를 한 서비스에 올린다.

BentoML 은 6장에서 Yatai 와 함께 쓴 1.1.10 을 그대로 쓴다.

## 3. 모델 파일로 가장 단순한 서비스 만들기

### 3.1 Runner

먼저 모델 파일을 폴더에 받아 두고 그것을 직접 읽는 서비스를 만든다. 모델 폴더 `model/` 에는 9장의 `prod` 모델 파일 네 개(`p50.txt`, `p10.txt`, `p90.txt`, `meta.json`)가 들어 있다.

```python {title="service_local.py"}
import bentoml
import pandas as pd
from bentoml.io import JSON

from suumo_model import SuumoModel


class SuumoRunnable(bentoml.Runnable):
    SUPPORTED_RESOURCES = ("cpu",)
    SUPPORTS_CPU_MULTI_THREADING = True

    def __init__(self):
        self.model = SuumoModel("model")          # p50.txt, p10.txt, p90.txt, meta.json

    @bentoml.Runnable.method(batchable=False)
    def predict(self, rows: pd.DataFrame) -> pd.DataFrame:
        return self.model.predict(rows)           # unit_price, low, high (만엔/m²)


suumo_runner = bentoml.Runner(SuumoRunnable, name="suumo_runnable")
svc = bentoml.Service("suumo_price_local", runners=[suumo_runner])
```

- **`bentoml.Runnable`**: Runner 안에서 돌 코드를 담는 클래스이다. `__init__` 에서 모델을 한 번만 읽어 메모리에 올려 둔다.
- **`@bentoml.Runnable.method`**: 이 메서드를 다른 프로세스(API 서버)에서 부를 수 있게 한다. `batchable=False` 는 요청을 묶어서 처리하지 않겠다는 뜻이다.
- **`bentoml.Runner`**: 위 클래스로 Runner 를 만든다. 로그에서 알아보기 쉽게 이름을 붙인다.
- **`bentoml.Service`**: 서비스 이름과, 이 서비스가 쓰는 Runner 목록이다.

### 3.2 API

```python {title="service_local.py (이어서)"}
@svc.api(input=JSON(), output=JSON())
async def predict(rows: list) -> list:
    """피처 행 목록을 받아 행마다 단가와 80% 구간을 돌려준다."""
    out = await suumo_runner.predict.async_run(pd.DataFrame(rows))
    return out.round(1).to_dict("records")
```

- **`@svc.api`**: 함수 이름이 그대로 주소가 된다. 이 함수는 `POST /predict` 로 불린다. 입력과 출력이 JSON 이라는 것도 여기서 정한다.
- **`async_run` 과 `await`**: Runner 는 다른 프로세스이므로 예측을 맡기고 답을 기다려야 한다. `await` 로 기다리는 동안 API 서버는 다른 요청을 받는다. `await` 를 빼면 답이 아니라 "나중에 답을 주겠다" 는 약속 객체가 돌아와 다음 줄에서 쓸 수 없다.

### 3.3 실행

```terminal {title="개발 PC: 서비스 실행"}
$ bentoml serve service_local.py:svc
[cli] Prometheus metrics for HTTP BentoServer from "service_local.py:svc" can be accessed at http://localhost:3000/metrics.
[cli] Starting production HTTP BentoServer from "service_local.py:svc" listening on http://0.0.0.0:3000 (Press CTRL+C to quit)
```

```terminal {title="다른 터미널: 요청"}
$ curl -s -X POST http://localhost:3000/predict -H 'Content-Type: application/json' \
    -d '[{"lat":35.6436,"lon":139.6693,"専有面積_m2":70,"築年":2015,"所在階_階":5,"総階数":10,"最短徒歩分":7,"間取り":"3LDK","構造":"RC","向き":"南"}]'
[{"unit_price":214.8,"low":145.9,"high":264.2}]
```

서버 로그에는 요청 하나가 두 줄로 남는다. API 서버가 받은 요청과, 그 안에서 Runner 로 넘어간 호출이다.

```terminal {title="bentoml serve 로그"}
[runner:suumo_runnable:1] _ (scheme=http,method=POST,path=/predict,type=application/octet-stream,length=286) (status=200,type=application/vnd.bentoml.PandasDataFrameContainer,length=73) 122.996ms
[api_server:suumo_price_local:8] 127.0.0.1:63739 (scheme=http,method=POST,path=/predict,type=application/json,length=265) (status=200,type=application/json,length=47) 163.520ms
```

이 서비스는 동작하지만 아쉬운 점이 둘 있다. 모델 폴더를 손으로 받아 두어야 하고, 좌표와 일본어 컬럼 이름을 요청하는 쪽이 알아야 한다.

## 4. 레지스트리의 prod 모델로 바꾸기

### 4.1 모델 가져오기

BentoML 에는 자체 **모델 스토어**가 있다. 서비스가 쓸 모델을 이름과 태그로 보관하는 로컬 저장소이다. MLflow 레지스트리의 모델을 여기로 가져오는 함수가 `bentoml.mlflow.import_model` 이다.

```python {title="fetch_assets.py (핵심 부분)"}
NAME = "suumo-unit-price"
client = mlflow.MlflowClient()

for bento_name, uri, version in [
    ("suumo_unit_price", f"models:/{NAME}@prod", client.get_model_version_by_alias(NAME, "prod")),
    ("suumo_unit_price_v1", f"models:/{NAME}/1", client.get_model_version(NAME, "1")),
]:
    run = client.get_run(version.run_id)
    m = bentoml.mlflow.import_model(
        bento_name, uri,
        labels={"registered_model": NAME, "version": str(version.version), "run_id": version.run_id},
        metadata={"val_mape": run.data.metrics["val_mape"], "test_mape": run.data.metrics["test_mape"]})

boto3.client("s3").download_file("datasets", "suumo/prepared/2026-11-13/chome.parquet", "chome.parquet")
```

- **`models:/suumo-unit-price@prod`**: 버전 번호가 아니라 별칭으로 가져온다. 레지스트리에서 `prod` 가 다른 버전으로 옮겨 가면, 이 스크립트를 다시 돌리는 것만으로 새 모델이 들어온다.
- **`labels`**: 레지스트리의 버전과 MLflow run ID 를 BentoML 쪽에도 적어 둔다. 9장에서 만든 계보가 서비스까지 이어진다.
- **두 번째 모델**: 6절의 비교에 쓸 v1 이다. 8장과 같은 설정으로 학습한 모델이다.
- **`chome.parquet`**: 주소를 좌표로 바꾸는 초메(丁目) 표이다. 7장의 데이터 준비 파이프라인이 버킷에 남긴 것을 그대로 받는다.

```terminal {title="개발 PC: 모델 가져오기"}
$ python fetch_assets.py
imported suumo_unit_price:vsn4dnxec6bypbz4  ← models:/suumo-unit-price@prod (v4, run suumo-pvc-5)
imported suumo_unit_price_v1:vvq55dhec6bypbz4  ← models:/suumo-unit-price/1 (v1, run suumo-pvc-1)
chome.parquet 161991 bytes
$ bentoml models list
 Tag                              Module          Size      Creation Time
 suumo_unit_price_v1:vvq55dhec6…  bentoml.mlflow  5.04 MiB  2026-11-19 21:49:36
 suumo_unit_price:vsn4dnxec6byp…  bentoml.mlflow  4.18 MiB  2026-11-19 21:49:35
```

모델 스토어에 들어간 모델의 정보에는 출처가 함께 남는다.

```yaml {title="model.yaml (발췌)"}
name: suumo_unit_price
version: vsn4dnxec6bypbz4
module: bentoml.mlflow
labels:
  registered_model: suumo-unit-price
  version: '4'
  run_id: 45f21d1a4101421888532a9cbd3f0b1b
metadata:
  val_mape: 0.1520649076261791
  test_mape: 0.13312737145225992
```

### 4.2 Runner

3절에서는 `Runnable` 클래스를 직접 썼다. MLflow 에서 가져온 모델은 그럴 필요가 없다. 9장에서 모델을 pyfunc 로 묶어 두었으므로 BentoML 이 `predict` 를 부르는 Runner 를 알아서 만든다.

```python {title="service.py (Runner 와 서비스)"}
prod_model = bentoml.mlflow.get("suumo_unit_price:latest")
v1_model = bentoml.mlflow.get("suumo_unit_price_v1:latest")
prod_runner = prod_model.to_runner(name="suumo_prod")
v1_runner = v1_model.to_runner(name="suumo_v1")
svc = bentoml.Service("suumo_price_service", runners=[prod_runner, v1_runner])
```

`service_local.py` 에 있던 `from suumo_model import SuumoModel` 과 모델 폴더 경로가 사라졌다. 서비스 코드는 모델이 LightGBM 인지, 파일이 몇 개인지 모른다.

### 4.3 주소로 받는 API

요청하는 쪽이 보낼 값을 클래스로 정의한다. 필수는 주소, 면적, 준공 연도 셋이고 나머지는 비워도 된다.

```python {title="service.py (입력 정의)"}
class Listing(BaseModel):
    address: str                        # 예: 東京都世田谷区三軒茶屋2
    area: float                         # 전용 면적(専有面積, m²)
    year: float                         # 준공 연도(築年)
    floor: Optional[float] = None       # 소재 층(所在階)
    floors: Optional[float] = None      # 총 층수(総階数)
    walk: Optional[float] = None        # 가장 가까운 역까지 도보 분(徒歩分)
    layout: Optional[str] = None        # 방 구조(間取り)
    structure: Optional[str] = None     # 건물 구조(構造)
    facing: Optional[str] = None        # 방향(向き)
```

주소를 좌표로 바꾸는 표는 서비스가 뜰 때 한 번 읽어 둔다.

```python {title="service.py (시작할 때 한 번)"}
@svc.on_startup
async def load_locator(context: bentoml.Context):
    context.state["locate"] = make_locator(pd.read_parquet("chome.parquet"))   # 초메(丁目) 5,390곳의 좌표
```

`make_locator` 는 7장의 `address.py` 에 있는 함수이다. 데이터 준비 파이프라인이 매물 주소에 좌표를 붙일 때 쓴 것과 같은 코드이므로, 학습 때와 서빙 때 같은 주소가 같은 좌표로 바뀐다.

```python {title="service.py (/estimate)"}
@svc.api(input=JSON(pydantic_model=Listing), output=JSON())
async def estimate(item: Listing, ctx: bentoml.Context) -> dict:
    """주소와 조건으로 추정 호가(만엔)와 80% 구간을 돌려준다."""
    row, where = locate_row(item, ctx)
    if row is None:
        ctx.response.status_code = 422
        return {"error": "주소를 찾지 못했다. 도쿄 23구의 구, 동, 초메까지 적는다", "address": item.address}
    pred = await prod_runner.predict.async_run(to_frame([row]))
    return {"address": item.address, **where, **price(pred.iloc[0], item.area), "model": str(prod_model.tag)}
```

API 서버가 하는 일은 세 가지이다.

| 단계 | 함수 | 하는 일 |
| --- | --- | --- |
| 입력 검사 | `JSON(pydantic_model=Listing)` | 필수 값이 있는지, 숫자 자리에 숫자가 왔는지 본다 |
| 모델 입력 만들기 | `locate_row`, `to_frame` | 주소를 위도, 경도로 바꾸고, 모델이 학습 때 본 컬럼 이름과 타입으로 맞춘다 |
| 응답 만들기 | `price` | 단가에 면적을 곱해 호가와 구간을 만엔 단위로 만든다 |

모델이 내는 값은 m²당 단가이고 사람이 알고 싶은 것은 가격이다. 이 차이를 메우는 코드가 API 서버에 있고, 모델은 건드리지 않는다.

### 4.4 실행 결과

```terminal {title="개발 PC: 서비스 실행"}
$ bentoml serve service.py:svc
[cli] Starting production HTTP BentoServer from "service.py:svc" listening on http://0.0.0.0:3000 (Press CTRL+C to quit)
```

조건은 8장, 9장과 같다. 전용 면적 70m², 2015년 준공, 10층 건물의 5층, 역까지 도보 7분, 3LDK, RC 구조, 남향(南)이다.

| 주소 | 단가 (만엔/m²) | 추정 호가 (만엔) | 80% 구간 (만엔) |
| --- | ---: | ---: | --- |
| 미나토구 롯폰기(港区六本木) 3초메 | 404.0 | 28,280 | 11,860 ~ 32,060 |
| 세타가야구 산겐자야(世田谷区三軒茶屋) 2초메 | 214.6 | 15,020 | 10,210 ~ 17,550 |
| 가쓰시카구 가메아리(葛飾区亀有) 3초메 | 91.6 | 6,410 | 4,790 ~ 7,920 |
| 스기나미구 젠푸쿠지(杉並区善福寺) 2초메 (수집 매물 0건) | 161.6 | 11,310 | 8,570 ~ 12,800 |

네 주소 모두 9장 노트북에서 레지스트리의 모델을 직접 불러 뽑은 값과 같다.

필수 값 셋만 보내도 답이 나온다. 비운 조건은 결측으로 들어가고 LightGBM 이 그대로 처리한다.

```terminal {title="필수 값만 보낸 요청"}
$ curl -s -X POST http://localhost:3000/estimate -H 'Content-Type: application/json' \
    -d '{"address":"東京都世田谷区三軒茶屋2","area":70,"year":2015}'
{"address":"東京都世田谷区三軒茶屋2","chome_key":"世田谷区三軒茶屋2","geo_level":"chome","unit_price":158.9,"price":11120,"low":7340,"high":13270,"model":"suumo_unit_price:vsn4dnxec6bypbz4"}
```

같은 자리, 같은 면적인데 단가가 214.6 에서 158.9 로 내려간다. 층, 역까지 거리, 방 구조를 모를 때 모델이 내는 값이므로, 조건을 채울수록 답이 달라진다는 것을 서비스 사용자에게 알려야 한다.

받을 수 없는 입력은 모델까지 가지 않고 API 서버에서 걸러진다.

| 요청 | 응답 코드 | 응답 |
| --- | ---: | --- |
| 23구 밖의 주소(`大阪府大阪市北区梅田1`) | 422 | `{"error":"주소를 찾지 못했다. 도쿄 23구의 구, 동, 초메까지 적는다", ...}` |
| 면적에 글자(`"area":"넓음"`) | 400 | `Invalid JSON input received: 1 validation error for Listing ... Input should be a valid number` |

좌표를 이미 가진 프로그램을 위한 `/predict` 도 그대로 둔다. 행 여러 개를 한 번에 받는다.

```terminal {title="/predict 에 두 행"}
$ curl -s -X POST http://localhost:3000/predict -H 'Content-Type: application/json' \
    -d '[{"lat":35.6436,"lon":139.6693,"専有面積_m2":70,"築年":2015,"所在階_階":5,"総階数":10,"最短徒歩分":7,"間取り":"3LDK","構造":"RC","向き":"南"},
         {"lat":35.7664,"lon":139.8483,"専有面積_m2":55,"築年":1995}]'
[{"unit_price":214.8,"low":145.9,"high":264.2},{"unit_price":50.7,"low":45.6,"high":71.9}]
```

| 주소 | 받는 것 | 돌려주는 것 | 누가 쓰나 |
| --- | --- | --- | --- |
| `/estimate` | 주소와 조건 한 건 | 추정 호가, 구간, 찾은 초메, 모델 태그 | 사람, 화면 |
| `/predict` | 피처 행 여러 개 | 행마다 단가와 구간 | 다른 프로그램, 배치 |

서버에 접속하면 API 문서가 자동으로 만들어져 있다. 입력 형식을 따로 문서로 써서 넘길 필요가 없다.

![BentoML 이 자동으로 만든 API 페이지. 제목은 suumo_price_service 이고 BentoML 1.1.10 표시가 있다. InferenceAPI 표에 POST /estimate, POST /predict, POST /compare 가 있고 입력과 출력은 모두 JSON 이다. 아래 Service APIs 묶음에 같은 세 주소가 펼칠 수 있는 항목으로 있고, 그 아래 Infrastructure 묶음에 GET /healthz, /livez, /readyz 가 있다.](bentoml-api-page.jpg)

> **핸즈온ML 보강**: [모델 저장과 서빙](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#model-serving) · [사용자 정의 변환기와 파이프라인](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#custom-transformer)

## 5. 모델 두 개를 동시에 돌려 비교하기

서비스에 Runner 를 둘 올려 두었다. `/compare` 는 같은 입력을 두 Runner 에 함께 보낸다.

```python {title="service.py (/compare)"}
@svc.api(input=JSON(pydantic_model=Listing), output=JSON())
async def compare(item: Listing, ctx: bentoml.Context) -> dict:
    """같은 입력을 두 모델에 동시에 넣는다."""
    row, where = locate_row(item, ctx)
    ...
    frame = to_frame([row])
    prod, v1 = await asyncio.gather(prod_runner.predict.async_run(frame), v1_runner.predict.async_run(frame))
    return {"address": item.address, **where,
            "prod": {**price(prod.iloc[0], item.area), "version": prod_model.info.labels["version"]},
            "v1": {**price(v1.iloc[0], item.area), "version": v1_model.info.labels["version"]}}
```

`asyncio.gather` 는 두 호출을 차례로 기다리지 않고 한꺼번에 보낸 뒤 둘 다 끝나면 돌아온다. Runner 가 서로 다른 프로세스이므로 두 예측은 실제로 동시에 돈다.

```terminal {title="/compare"}
$ curl -s -X POST http://localhost:3000/compare -H 'Content-Type: application/json' \
    -d '{"address":"東京都世田谷区三軒茶屋2","area":70,"year":2015,"floor":5,"floors":10,"walk":7,"layout":"3LDK","structure":"RC","facing":"南"}'
{"address":"東京都世田谷区三軒茶屋2","chome_key":"世田谷区三軒茶屋2","geo_level":"chome","prod":{"unit_price":214.6,"price":15020,"low":10210,"high":17550,"version":"4"},"v1":{"unit_price":206.8,"price":14470,"low":9920,"high":16620,"version":"1"}}
```

| | prod (v4) | v1 |
| --- | ---: | ---: |
| 단가 (만엔/m²) | 214.6 | 206.8 |
| 추정 호가 (만엔) | 15,020 | 14,470 |
| 80% 구간 (만엔) | 10,210 ~ 17,550 | 9,920 ~ 16,620 |

v1 의 값은 8장 글의 같은 주소 결과(206.8, 14,470)와 같다. 새 모델을 `prod` 로 올리기 전에 지금 모델과 같은 요청으로 나란히 돌려 보는 용도로 쓸 수 있다.

Runner 를 여러 개 두는 다른 쓰임은 단계를 나누는 것이다. 전처리가 무거우면 전처리 Runner 와 모델 Runner 로 나눠 각각 따로 늘린다.

## 6. 서비스 상태 확인하기

Kubernetes 는 Pod 가 살아 있는지, 요청을 받을 준비가 됐는지를 정해진 주소로 물어본다. BentoML 서비스에는 이 주소가 처음부터 들어 있다.

```terminal {title="상태 확인"}
$ curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/healthz
200
$ curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/livez
200
$ curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/readyz
200
```

| 주소 | 뜻 | Kubernetes 에서 |
| --- | --- | --- |
| `/livez` | 프로세스가 살아 있다 | liveness probe. 실패하면 Pod 를 다시 띄운다 |
| `/readyz` | Runner 까지 떠서 요청을 받을 수 있다 | readiness probe. 실패하는 동안 트래픽을 보내지 않는다 |
| `/healthz` | 서비스가 정상이다 | 사람이나 모니터링이 확인할 때 |

서비스를 띄운 직후에는 `/readyz` 가 503 을 내다가 Runner 가 모델을 다 읽으면 200 으로 바뀐다. 모델이 준비되기 전에 요청이 들어오는 일을 이것으로 막는다.

`/metrics` 는 Prometheus 형식의 지표를 내준다. 3장에서 FastAPI 앱에 지표 코드를 직접 넣었던 것과 달리 코드를 한 줄도 쓰지 않았다.

```terminal {title="/metrics (발췌)"}
$ curl -s http://localhost:3000/metrics | grep estimate
bentoml_api_server_request_duration_seconds_bucket{endpoint="/estimate",http_response_code="200",le="0.01",...} 29.0
bentoml_api_server_request_duration_seconds_bucket{endpoint="/estimate",http_response_code="200",le="0.025",...} 51.0
bentoml_api_server_request_duration_seconds_count{endpoint="/estimate",http_response_code="200",...} 55.0
bentoml_api_server_request_duration_seconds_count{endpoint="/estimate",http_response_code="422",...} 1.0
```

| 지표 | 내용 |
| --- | --- |
| `bentoml_api_server_request_total` | 주소와 응답 코드별 요청 수 |
| `bentoml_api_server_request_duration_seconds` | 주소별 응답 시간 분포 |
| `bentoml_api_server_request_in_progress` | 지금 처리 중인 요청 수 |
| `bentoml_runner_request_total`, `..._duration_seconds`, `..._in_progress` | 같은 세 가지를 Runner 별로 |

성공한 요청 55건 가운데 29건이 10ms 안에, 51건이 25ms 안에 끝났다. 주소를 찾지 못해 422 로 끝난 1건도 따로 세어진다. API 서버와 Runner 의 시간이 따로 나오므로, 느려졌을 때 주소 변환이 느린지 모델이 느린지를 가를 수 있다.

> **핸즈온ML 보강**: [모니터링과 재학습](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#monitoring)

## 7. 배포 단위로 묶기

### 7.1 Bento 빌드

지금까지는 소스 폴더에서 바로 서비스를 띄웠다. 다른 환경으로 옮기려면 코드, 모델, 패키지 목록을 한 꾸러미로 묶어야 한다. BentoML 에서는 이 꾸러미를 **Bento** 라고 부르고, 무엇을 담을지는 `bentofile.yaml` 에 적는다.

```yaml {title="bentofile.yaml"}
service: "service:svc"
labels:
  owner: mlops-study
  stage: prod
include:
  - "service.py"
  - "address.py"
  - "chome.parquet"
python:
  requirements_txt: requirements.txt
docker:
  python_version: "3.11"
  system_packages:
    - libgomp1          # LightGBM 이 쓰는 시스템 라이브러리 (8장 학습 이미지와 같다)
```

```text {title="requirements.txt"}
bentoml==1.1.10
mlflow==3.16.0
lightgbm==4.7.0
pandas==3.1.1
pyarrow
boto3
setuptools<81
```

- **`include`**: 서비스 코드, 주소 변환 코드, 초메(丁目) 표 세 파일만 담는다. 모델은 적지 않아도 서비스가 쓰는 것을 BentoML 이 찾아서 함께 담는다.
- **패키지 버전**: LightGBM 과 pandas 는 8장 학습 이미지와, MLflow 는 추적 서버와 같은 버전으로 맞췄다.
- **`system_packages`**: 8장에서 학습 이미지에 `libgomp1` 을 넣은 것과 같은 이유이다. 서빙 이미지에도 있어야 모델을 읽을 수 있다.

```terminal {title="개발 PC: Bento 빌드"}
$ bentoml build
Successfully built Bento(tag="suumo_price_service:22khquhec6dtio24").
$ bentoml list
 Tag                                Size        Model Size  Creation Time
 suumo_price_service:22khquhec6dt…  186.89 KiB  9.23 MiB    2026-11-19 21:50:46
```

Bento 안은 이렇게 생겼다.

| 경로 | 내용 |
| --- | --- |
| `bento.yaml` | 서비스 이름, 버전, 쓰는 모델과 Runner, API 목록 |
| `src/` | `service.py`, `address.py`, `chome.parquet` |
| `apis/openapi.yaml` | API 문서 |
| `env/python/requirements.txt` | 패키지 목록 |
| `env/docker/Dockerfile` | 이 Bento 로 이미지를 만드는 Dockerfile |

`bento.yaml` 에는 어떤 모델을 담았는지가 태그로 고정된다.

```yaml {title="bento.yaml (발췌)"}
name: suumo_price_service
version: 22khquhec6dtio24
models:
- tag: suumo_unit_price_v1:vvq55dhec6bypbz4
  module: bentoml.mlflow
- tag: suumo_unit_price:vsn4dnxec6bypbz4
  module: bentoml.mlflow
runners:
- name: suumo_prod
  runnable_type: MLflowPyfuncRunnable
  models:
  - suumo_unit_price:vsn4dnxec6bypbz4
```

### 7.2 태그

빌드할 때마다 `서비스이름:버전` 형태의 태그가 새로 붙는다. 서비스 코드에서는 모델을 `suumo_unit_price:latest` 로 불렀지만, Bento 안에는 그 시점의 실제 태그가 적힌다.

| 이름 | 태그 | 가리키는 것 |
| --- | --- | --- |
| MLflow 등록 모델 | `suumo-unit-price` v4 (`@prod`) | 학습 run `suumo-pvc-5` 의 모델 |
| BentoML 모델 | `suumo_unit_price:vsn4dnxec6bypbz4` | 위 모델을 가져온 사본. 레이블에 v4 와 run ID |
| Bento | `suumo_price_service:22khquhec6dtio24` | 서비스 코드 + 위 모델 + 패키지 목록 |
| 컨테이너 이미지 | `suumo_price_service:22khquhec6dtio24` | 위 Bento 로 만든 이미지 |

레지스트리에서 `prod` 가 v5 로 바뀌어도 이미 만든 Bento 는 v4 를 담은 채로 남는다. 배포된 서비스가 어느 모델로 답하는지는 Bento 태그 하나로 정해지고, 거기서 9장의 run 과 데이터까지 거슬러 올라갈 수 있다.

### 7.3 컨테이너 이미지

Bento 로 컨테이너 이미지를 만든다. BentoML 1.1.10 은 6장에서 쓴 방식대로 같은 내부 함수를 스크립트로 부른다.

```terminal {title="개발 PC: 이미지 빌드와 실행"}
$ python build_bento_image.py suumo_price_service:22khquhec6dtio24 suumo_price_service:22khquhec6dtio24
BUILD_FINISHED
$ docker images | grep suumo_price_service
suumo_price_service   22khquhec6dtio24   1.91GB
$ docker run --rm -p 3000:3000 suumo_price_service:22khquhec6dtio24
[cli] Service loaded from Bento directory: bentoml.Service(tag="suumo_price_service:22khquhec6dtio24", path="/home/bentoml/bento/")
[cli] Starting production HTTP BentoServer from "/home/bentoml/bento" listening on http://0.0.0.0:3000 (Press CTRL+C to quit)
```

컨테이너는 13초 뒤에 `/readyz` 가 200 이 됐다. 같은 요청을 보내면 소스 폴더에서 띄웠을 때와 같은 답이 나온다.

```terminal {title="컨테이너에 요청"}
$ curl -s -X POST http://localhost:3000/estimate -H 'Content-Type: application/json' \
    -d '{"address":"東京都世田谷区三軒茶屋2","area":70,"year":2015,"floor":5,"floors":10,"walk":7,"layout":"3LDK","structure":"RC","facing":"南"}'
{"address":"東京都世田谷区三軒茶屋2","chome_key":"世田谷区三軒茶屋2","geo_level":"chome","unit_price":214.6,"price":15020,"low":10210,"high":17550,"model":"suumo_unit_price:vsn4dnxec6bypbz4"}
```

이미지 안에는 Python 3.11.18, LightGBM 4.7.0, MLflow 3.16.0, BentoML 1.1.10 이 들어 있다. 이 이미지는 MLflow 서버나 버킷에 접속하지 않는다. 모델과 초메(丁目) 표가 이미지 안에 있으므로, 네트워크가 끊긴 곳에서도 같은 답을 낸다.

이 이미지를 클러스터에 올리는 일은 6장에서 소득 분류기로 한 것과 같다. Bento 를 Yatai 에 올리면 Yatai 가 이미지를 빌드하고 Deployment 로 띄운다.

> **핸즈온ML 보강**: [재현 가능하게 남기기](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#reproducibility)

## 8. MLflow 만으로 서빙하기

BentoML 을 쓰지 않고 MLflow 만으로도 모델을 서비스로 띄울 수 있다. 서비스 코드를 쓰지 않고 명령 한 줄이면 된다.

```terminal {title="개발 PC: MLflow 로 서빙"}
$ export MLFLOW_TRACKING_URI=http://192.168.0.238:5000
$ mlflow models serve -m "models:/suumo-unit-price@prod" --env-manager local -p 5001
INFO mlflow.pyfunc.backend: === Running command 'exec uvicorn --host 127.0.0.1 --port 5001 --workers 1 mlflow.pyfunc.scoring_server.app:app'
INFO:     Uvicorn running on http://127.0.0.1:5001 (Press CTRL+C to quit)
```

주소는 `/invocations` 하나이고, 입력은 MLflow 가 정한 형식으로 보낸다.

```terminal {title="/invocations"}
$ curl -s -X POST http://localhost:5001/invocations -H 'Content-Type: application/json' \
    -d '{"dataframe_split":{"columns":["lat","lon","専有面積_m2","築年","所在階_階","総階数","最短徒歩分","間取り","構造","向き"],
         "data":[[35.6436,139.6693,70,2015,5,10,7,"3LDK","RC","南"]]}}'
{"predictions": [{"unit_price": 214.77751901799098, "low": 145.88628521825942, "high": 264.18751134564786}]}
$ curl -s http://localhost:5001/version
3.16.0
```

같은 좌표와 조건을 BentoML 서비스의 `/predict` 에 넣었을 때의 214.8, 145.9, 264.2 와 같은 값이다. 9장에서 모델에 서명을 붙여 두었으므로 서버가 입력의 컬럼 이름과 타입을 서명에 맞춰 준다.

컨테이너로 만드는 명령도 있다. `mlflow models build-docker -m "models:/suumo-unit-price@prod" -n suumo-unit-price` 가 같은 서버를 담은 이미지를 만든다.

두 방식을 같은 PC 에서 띄워 요청 50건씩을 차례로 보냈다.

| | BentoML 서비스 | MLflow 서빙 |
| --- | --- | --- |
| 준비한 것 | `service.py`, `bentofile.yaml`, `fetch_assets.py` | 명령 한 줄 |
| 주소 | `/estimate`, `/predict`, `/compare` | `/invocations` |
| 입력 | 주소와 조건 | 위도, 경도와 학습 때의 컬럼 이름 |
| 출력 | 호가(만엔), 구간, 찾은 초메, 모델 태그 | m²당 단가와 구간 |
| 상태 확인 | `/healthz`, `/livez`, `/readyz` | `/health`, `/ping` |
| 지표 | `/metrics` (Prometheus) | 기본으로는 없다 |
| 프로세스 | API 서버와 Runner 가 따로 | 서버 하나 |
| 응답 시간 중앙값 | 10.5ms (`/estimate`) | 6.3ms (`/invocations`) |
| 모델을 읽는 시점 | 빌드할 때 Bento 에 담는다 | 띄울 때 레지스트리에서 받는다 |

MLflow 서빙이 4ms 빠른 것은 주소 변환이 없고 프로세스 사이를 건너지 않기 때문이다. 대신 주소를 좌표로 바꾸는 일, 단가를 가격으로 바꾸는 일, 지표를 내는 일은 요청하는 쪽이나 다른 서비스가 맡아야 한다.

## 9. 세 도구 비교

Kubeflow 에는 **KServe** 라는 서빙 도구가 함께 들어 있다. 모델 파일의 위치를 적은 `InferenceService` 리소스를 만들면 KServe 가 서버를 띄운다. 이 클러스터에는 KServe 를 설치하지 않았으므로 실행하지 않고 방식만 비교한다.

```yaml {title="KServe InferenceService (예시)"}
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: suumo-unit-price
spec:
  predictor:
    model:
      modelFormat:
        name: mlflow
      storageUri: s3://mlflow-artifacts/<모델 경로>
```

| | BentoML | MLflow | KServe |
| --- | --- | --- | --- |
| 중심 | 모델을 서비스로 묶어 배포하기 | 실험부터 서빙까지 ML 수명주기 전체 | Kubernetes 위의 서빙 운영 |
| 서비스 코드 | Python 으로 자유롭게 쓴다 | 쓰지 않는다 (pyfunc 에 넣어야 한다) | 기본은 쓰지 않는다 |
| Kubernetes 지식 | 없어도 된다 (Yatai 가 맡는다) | 없어도 된다 | 필요하다 |
| 실험 추적 | 없다 | 있다 | 없다 |
| 스케일링 | Yatai 나 직접 만든 Deployment | 직접 만든다 | 처음부터 들어 있다 (요청이 없으면 0 까지) |
| 이 글에서 | 실행 (4 ~ 7절) | 실행 (8절) | 비교만 |

이 프로젝트는 주소를 좌표로 바꾸는 코드가 모델 앞에 꼭 있어야 한다. 그래서 서비스 코드를 자유롭게 쓸 수 있는 BentoML 과, 모델의 버전과 출처를 맡는 MLflow 를 함께 쓰는 구성이 맞는다. 모델에 좌표를 그대로 넣는 내부 배치 작업이라면 MLflow 서빙만으로 충분하다.

11장에서는 이 서비스에 모니터링과 드리프트 탐지를 붙인다.
