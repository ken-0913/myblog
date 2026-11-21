---
title: "MLPE 스터디 5주차 - Ch10 도쿄 23구 중고 맨션 호가 모델을 KServe 와 MLflow 로 서빙하기"
date: 2026-11-19T11:00:00+09:00
draft: false
tags: ["MLOps", "MLPE", "KServe", "MLflow", "Model Serving", "Model Registry", "Gateway API", "Istio", "LightGBM", "Capstone"]
categories: ["MLOps"]
series: ["MLPE 5주차"]
featuredImage: images/banners/mlpe-10-1-suumo-serving-4f4cafc0.png
---
[9장](../mlpe-09-1-suumo-tracking/)에서 m²당 단가 모델을 MLflow 레지스트리에 `suumo-unit-price@prod` 로 올렸다. 10장에서는 이 모델을 주소와 매물 조건을 보내면 추정 호가를 돌려주는 HTTP 서비스로 만든다. 서빙 도구는 KServe 를 쓰고, Kubernetes 클러스터에 바로 띄운다.

## 1. 한눈에 보기

### 1.1 만들 서비스

7장에서 세운 목표는 "주소와 조건을 넣으면 그 자리의 호가를 알려 준다" 였다. 지금까지는 노트북에서 모델을 직접 불러 예측했다. 서비스로 만들면 모델을 모르는 사람이나 다른 프로그램도 주소 한 줄로 같은 답을 받는다.

```terminal {title="만들 서비스에 보내는 요청과 응답"}
$ curl -s http://192.168.0.248/v1/models/suumo-unit-price:predict \
    -H 'Host: suumo-unit-price-suumo-serving.example.com' -H 'Content-Type: application/json' \
    -d '{"instances":[{"address":"東京都世田谷区三軒茶屋2","area":70,"year":2015,"floor":5,"floors":10,"walk":7,"layout":"3LDK","structure":"RC","facing":"南"}]}'
{"predictions":[{"address":"東京都世田谷区三軒茶屋2","chome_key":"世田谷区三軒茶屋2","geo_level":"chome","unit_price":214.6,"price":15020,"low":10210,"high":17550}],"run_id":"45f21d1a4101421888532a9cbd3f0b1b"}
```

세타가야구 산겐자야(世田谷区三軒茶屋) 2초메의 70m², 2015년 준공 매물이면 추정 호가는 1억 5,020만엔이고, 80% 구간은 1억 210만엔 ~ 1억 7,550만엔이다. 9장의 노트북에서 같은 모델로 뽑은 값과 같다. 응답 끝의 `run_id` 는 이 모델을 만든 9장의 학습 run 이다.

### 1.2 진행 단계

![10장 전체 흐름. 사용자가 주소와 조건을 보내면 Kubernetes 의 suumo-serving namespace 앞에 있는 Gateway(Istio, Gateway API)가 받아 HTTPRoute 에 따라 InferenceService suumo-unit-price 로 넘긴다. InferenceService 는 Pod 가 아니라 선언이고, KServe controller 가 이를 보고 transformer 와 predictor 마다 Deployment, Service, HPA, HTTPRoute 를 만든다. 요청은 transformer Pod 에서 주소가 좌표로 바뀐 뒤 피처 행으로 predictor Pod 에 전달되고, 돌아온 단가가 호가로 바뀐다. 아래쪽 S3 호환 버킷에서 transformer Pod 는 초메(丁目) 표(chome.parquet)를, predictor Pod 는 모델 폴더를 뜰 때 내려받는다. 모델 폴더는 MLflow 모델 레지스트리의 prod 별칭이 가리키는 v4 의 저장 경로이다. 비교용 InferenceService suumo-unit-price-v1 도 같은 구조로 transformer Pod 와 predictor Pod 를 따로 가지며, Gateway 는 Host 가 -v1 인 요청을 이쪽으로 보낸다.](ch10-overview-stack.png)

- **A. 서비스의 구조 이해하기**
  - KServe 에서는 서비스 하나를 `InferenceService` 라는 리소스 하나로 적는다. 그 안에서 모델을 돌리는 부분(predictor)과 입력과 출력을 다듬는 부분(transformer)이 나뉜다. 왜 둘로 나누는지를 먼저 본다.
- **B. KServe 설치하기**
  - 클러스터에 KServe 를 설치하고, 바깥에서 들어오는 요청을 받을 입구(Gateway)를 하나 만든다.
- **C. 모델을 돌리는 서버 만들기 (predictor)**
  - 9장에서 레지스트리에 올린 모델을 읽어, 좌표와 조건을 받으면 m²당 단가를 돌려주는 서버를 코드 40줄 안팎으로 만든다. 모델 파일은 KServe 가 버킷에서 받아 준다.
- **D. 주소로 받게 만들기 (transformer)**
  - 요청하는 쪽은 좌표가 아니라 주소를 안다. 주소를 좌표로 바꿔 predictor 에 넘기고, 돌아온 단가에 면적을 곱해 가격으로 바꾸는 서버를 앞에 하나 더 둔다.
- **E. 클러스터에 배포하고 요청 보내기**
  - 두 서버를 `InferenceService` 하나로 적어 클러스터에 올린다. KServe 가 대신 만들어 주는 리소스를 확인하고, 주소 네 곳으로 요청을 보낸다.
- **F. 모델 두 개를 나란히 띄워 비교하기**
  - 예전 모델(v1)로 같은 서비스를 하나 더 띄우고, 같은 요청을 지금 모델(v4)과 함께 보내 답을 나란히 받는다.
- **G. 서비스 상태 확인하기**
  - 서비스가 살아 있는지 알려 주는 주소와, 요청 수와 응답 시간을 숫자로 내주는 주소가 처음부터 들어 있다. 직접 만들지 않아도 된다는 것을 확인한다.
- **H. MLflow 만으로 서빙하기**
  - KServe 없이 MLflow 명령 한 줄로도 같은 모델을 서비스로 띄울 수 있다. 무엇이 같고 무엇이 다른지 비교한다.

## 2. 서비스의 구조

### 2.1 모델 서빙에서 따져야 할 것

모델을 서비스로 내놓는 일은 일반 웹 서비스 배포에 몇 가지가 더 붙는다. 이 글의 서비스에 해당하는 것만 고르면 이렇다.

| 따질 것 | 이 서비스에서 |
| --- | --- |
| 추론 방식 (실시간, 배치) | 실시간. 주소 한 건을 받아 바로 답한다 |
| 데이터 의존성 | 주소를 좌표로 바꾸는 표가 서비스 안에 있어야 한다. 학습 때와 같은 표를 쓴다 |
| 모델 버전 | 레지스트리의 `prod` 별칭이 가리키는 버전을 쓰고, 응답에 어느 run 의 모델인지 적는다 |
| 하드웨어 | CPU 로 충분하다. LightGBM 은 시스템 라이브러리 `libgomp1` 이 필요하다 |
| 모니터링 | 상태 확인 주소와 Prometheus 지표를 내준다 |

### 2.2 InferenceService, predictor, transformer

KServe 는 Kubernetes 위에서 모델 서빙을 맡는 도구이다. 사용자는 `InferenceService` 라는 리소스에 "어떤 모델을, 어떤 서버로 띄울지" 만 적는다. Deployment, Service, 라우팅 규칙처럼 서비스를 띄우는 데 필요한 나머지는 KServe 가 만든다.

`InferenceService` 안은 역할별로 나뉜다.

| | transformer | predictor |
| --- | --- | --- |
| 하는 일 | HTTP 요청을 받고, 입력을 검사하고, 모델에 넣을 모양으로 바꾼다. 모델의 답을 사람이 읽을 모양으로 바꾼다 | 모델을 메모리에 올려 두고 예측만 한다 |
| 이 서비스에서 | 주소를 좌표로 바꾸고, 단가를 호가로 바꾼다 | LightGBM 모델 세 개로 단가와 구간을 계산한다 |
| 늘리는 기준 | 동시에 들어오는 요청 수 | 예측에 드는 계산량 |

둘은 서로 다른 Deployment 로 뜬다. 요청이 몰릴 때는 transformer 만, 모델이 무거울 때는 predictor 만 따로 늘릴 수 있다. predictor 는 꼭 있어야 하고 transformer 는 필요할 때만 둔다.

KServe 에는 모델 형식만 적으면 서버를 골라 주는 기본 런타임도 있다. MLflow 형식을 읽는 런타임(MLServer)은 기본 이미지의 MLflow 가 9장에서 쓴 3.16.0 보다 오래됐다. 그래서 이 글에서는 KServe 의 Python SDK 로 predictor 와 transformer 를 직접 쓴다.

### 2.3 KServe 설치

KServe 0.21.0 을 **Standard** 모드로 설치한다. Standard 모드는 서비스를 평범한 Deployment 로 띄우는 방식이다. 요청이 없을 때 Pod 를 0개까지 줄이는 기능은 Knative 를 함께 쓰는 모드에만 있고, 이 글에서는 쓰지 않는다.

```yaml {title="values.yaml"}
kserve:
  controller:
    deploymentMode: Standard
    gateway:
      ingressGateway:
        enableGatewayApi: true
        createGateway: false
        kserveGateway: kserve/kserve-ingress-gateway
        className: istio
```

```bash {title="install.sh (핵심 부분)"}
VERSION=v0.21.0
BASE=https://github.com/kserve/kserve/releases/download/${VERSION}

helm template kserve-crd "${BASE}/helm-chart-kserve-crd-${VERSION}.tgz" -n kserve | kubectl apply --server-side -f -
helm template kserve "${BASE}/helm-chart-kserve-resources-${VERSION}.tgz" -n kserve -f values.yaml | kubectl apply --server-side -n kserve -f -
kubectl apply -f gateway.yaml
```

- **`deploymentMode: Standard`**: 위에서 말한 Deployment 방식이다.
- **`enableGatewayApi: true`**: 바깥에서 들어오는 요청의 길을 Kubernetes 의 Gateway API 로 만든다. `InferenceService` 를 만들 때마다 KServe 가 `HTTPRoute` 를 하나씩 붙인다.
- **`gateway.yaml`**: 요청이 들어오는 입구인 `Gateway` 이다. 클러스터에 이미 있는 Istio 의 GatewayClass 로 만든다.
- **필요한 것**: KServe 는 cert-manager 가 먼저 있어야 한다. 웹훅 인증서를 cert-manager 로 만든다.

```yaml {title="gateway.yaml"}
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: kserve-ingress-gateway
  namespace: kserve
spec:
  gatewayClassName: istio
  listeners:
    - name: http
      port: 80
      protocol: HTTP
      allowedRoutes:
        namespaces:
          from: All
```

```terminal {title="설치 결과"}
$ kubectl -n kserve get pods,gateway
NAME                                                READY   STATUS    RESTARTS   AGE
pod/kserve-controller-manager-557bc456dd-pqzjg      2/2     Running   0          56m
pod/kserve-ingress-gateway-istio-765f99986f-2d46w   1/1     Running   0          55m

NAME                                                       CLASS   ADDRESS         PROGRAMMED   AGE
gateway.gateway.networking.k8s.io/kserve-ingress-gateway   istio   192.168.0.248   True         55m
```

Pod 는 둘이다. `kserve-controller-manager` 는 `InferenceService` 를 지켜보다가 필요한 리소스를 만드는 컨트롤러이고, `kserve-ingress-gateway-istio` 는 요청을 실제로 받는 입구이다. 앞으로 모든 요청은 Gateway 의 주소 `192.168.0.248` 로 보낸다.

## 3. 모델을 돌리는 서버 만들기 (predictor)

### 3.1 서버 코드

KServe 의 Python SDK 는 `Model` 클래스를 준다. 이 클래스를 물려받아 모델을 읽는 `load` 와 예측하는 `predict` 두 메서드만 채우면 HTTP 서버가 된다.

```python {title="predictor.py (핵심 부분)"}
import mlflow
from kserve import Model, ModelServer, model_server
from kserve.errors import InvalidInput


class SuumoPredictor(Model):
    def __init__(self, name: str, model_dir: str):
        super().__init__(name)
        self.model_dir = model_dir
        self.load()

    def load(self):
        self.model = mlflow.pyfunc.load_model(self.model_dir)
        self.run_id = self.model.metadata.run_id          # 9장의 학습 run
        self.ready = True                                 # 이 값이 True 가 돼야 준비 완료로 본다

    def predict(self, payload: dict, headers: dict = None) -> dict:
        rows = payload.get("instances")
        if not rows:
            raise InvalidInput("instances 에 피처 행 목록을 넣는다")
        pred = self.model.predict(to_frame(rows))         # unit_price, low, high (만엔/m²)
        return {"predictions": pred.round(4).to_dict("records"), "run_id": self.run_id}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(parents=[model_server.parser])
    parser.add_argument("--model_dir", default="/mnt/models")
    args, _ = parser.parse_known_args()
    ModelServer().start([SuumoPredictor(args.model_name, args.model_dir)])
```

- **`mlflow.pyfunc.load_model`**: 9장에서 모델을 pyfunc 로 묶어 두었다. 서버 코드에는 LightGBM 도, 모델 파일이 몇 개인지도 나오지 않는다.
- **`self.ready = True`**: 모델을 다 읽었다는 표시이다. 이 값이 `True` 가 되기 전에는 서버가 준비되지 않았다고 답한다.
- **`payload["instances"]`**: KServe 가 정한 요청 형식이다. 예측할 행을 `instances` 목록에 담아 보내면 `predictions` 목록으로 돌아온다.
- **`run_id`**: 모델 폴더의 메타 정보에서 읽은 학습 run 의 ID 이다. 응답마다 붙여, 답을 낸 모델이 어느 run 에서 나왔는지 알 수 있게 한다.
- **`ModelServer().start`**: 서버를 띄운다. 주소는 모델 이름으로 정해져 `POST /v1/models/<이름>:predict` 가 된다.

`to_frame` 은 받은 행을 모델 서명에 맞추는 함수이다. 수치 컬럼은 실수로, 범주 컬럼은 문자열로 바꾸고 없는 값은 결측으로 둔다.

### 3.2 모델 파일 받아오기

모델 파일은 서버 코드가 받지 않는다. 모델이 있는 경로를 적어 두면, KServe 가 Pod 를 띄울 때 **storage initializer** 라는 init container 를 끼워 넣어 그 경로의 파일을 `/mnt/models` 에 받아 둔다. 서버는 그 폴더를 읽기만 한다.

경로는 레지스트리에서 `prod` 별칭이 가리키는 버전의 저장 위치이다.

```python {title="prod 모델의 저장 경로 찾기"}
client = mlflow.MlflowClient()
v = client.get_model_version_by_alias("suumo-unit-price", "prod")
print(v.version, client.get_model_version_download_uri("suumo-unit-price", v.version))
# 4 s3://mlflow-artifacts/chapter-4/4/models/m-a28f66ead1d24dc1b03ce3ca318a98f3/artifacts
```

버킷에 접속할 키는 Secret 에 넣고, ServiceAccount 가 그 Secret 을 가리키게 한다. 버킷 주소는 Secret 의 annotation 으로 알려 준다.

```terminal {title="버킷 접속 정보"}
$ kubectl -n suumo-serving create secret generic s3-credentials \
    --from-literal=AWS_ACCESS_KEY_ID=<ACCESS_KEY> --from-literal=AWS_SECRET_ACCESS_KEY=<SECRET_KEY>
$ kubectl -n suumo-serving annotate secret s3-credentials \
    serving.kserve.io/s3-endpoint=<버킷 서비스 주소>:9000 serving.kserve.io/s3-usehttps=0 serving.kserve.io/s3-region=us-east-1
```

```yaml {title="01-storage.yaml"}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: s3-reader
  namespace: suumo-serving
secrets:
  - name: s3-credentials
```

`InferenceService` 에 `serviceAccountName: s3-reader` 를 적으면 storage initializer 가 이 키로 버킷에서 파일을 받는다. 서버 컨테이너에는 키가 들어가지 않는다.

## 4. 주소로 받게 만들기 (transformer)

predictor 는 위도, 경도와 학습 때의 일본어 컬럼 이름을 받는다. 요청하는 쪽이 이것을 다 알기는 어렵다. transformer 가 앞에서 주소를 받아 predictor 가 읽을 모양으로 바꾼다.

요청하는 쪽이 보낼 값을 클래스로 정의한다. 필수는 주소, 면적, 준공 연도 셋이고 나머지는 비워도 된다.

```python {title="transformer.py (입력 정의)"}
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

transformer 도 predictor 와 같은 `Model` 클래스로 만든다.

```python {title="transformer.py (핵심 부분)"}
class AddressTransformer(Model):
    def __init__(self, name: str, chome_path: str):
        super().__init__(name)
        self.locate = make_locator(pd.read_parquet(chome_path))   # 초메(丁目) 5,390곳의 좌표
        self.ready = True

    def to_row(self, raw: dict):
        try:
            item = Listing(**raw)
        except ValidationError as e:
            raise InvalidInput(f"입력이 맞지 않는다: {e.errors()[0]['loc'][0]} ({e.errors()[0]['msg']})")
        found = self.locate(item.address)
        if found is None:
            raise InvalidInput(f"주소를 찾지 못했다. 도쿄 23구의 구, 동, 초메까지 적는다: {item.address}")
        lat, lon, key, level = found
        row = {"lat": lat, "lon": lon, "専有面積_m2": item.area, "築年": item.year, "所在階_階": item.floor,
               "総階数": item.floors, "最短徒歩分": item.walk, "間取り": item.layout, "構造": item.structure, "向き": item.facing}
        return item, row, {"chome_key": key, "geo_level": level}

    async def predict(self, payload: dict, headers: dict = None) -> dict:
        prepared = [self.to_row(raw) for raw in payload.get("instances", [])]
        answer = await super().predict({"instances": [row for _, row, _ in prepared]}, headers)   # predictor 호출
        out = []
        for (item, _, where), p in zip(prepared, answer["predictions"]):
            out.append({"address": item.address, **where, "unit_price": round(p["unit_price"], 1),
                        "price": int(round(p["unit_price"] * item.area, -1)),
                        "low": int(round(p["low"] * item.area, -1)), "high": int(round(p["high"] * item.area, -1))})
        return {"predictions": out, "run_id": answer["run_id"]}
```

- **`make_locator`**: 7장의 `address.py` 에 있는 함수이다. 데이터 준비 파이프라인이 매물 주소에 좌표를 붙일 때 쓴 것과 같은 코드이므로, 학습 때와 서빙 때 같은 주소가 같은 좌표로 바뀐다.
- **`chome_path`**: 주소를 좌표로 바꾸는 초메(丁目) 표이다. 7장의 파이프라인이 버킷에 남긴 파일이고, 모델 파일과 같은 방식으로 storage initializer 가 받아 둔다.
- **`InvalidInput`**: 이 예외를 던지면 KServe 가 응답 코드 400 과 메시지를 돌려준다. 받을 수 없는 입력은 predictor 까지 가지 않는다.
- **`super().predict`**: `Model` 클래스의 기본 `predict` 는 요청을 predictor 로 넘긴다. predictor 의 주소는 KServe 가 transformer 를 띄울 때 `--predictor_host` 인자로 넣어 준다. 코드에는 predictor 의 주소가 없다.

transformer 가 하는 일은 세 가지이다.

| 단계 | 코드 | 하는 일 |
| --- | --- | --- |
| 입력 검사 | `Listing(**raw)` | 필수 값이 있는지, 숫자 자리에 숫자가 왔는지 본다 |
| 모델 입력 만들기 | `self.locate`, `row` | 주소를 위도, 경도로 바꾸고, 모델이 학습 때 본 컬럼 이름으로 맞춘다 |
| 응답 만들기 | `out.append(...)` | 단가에 면적을 곱해 호가와 구간을 만엔 단위로 만든다 |

모델이 내는 값은 m²당 단가이고 사람이 알고 싶은 것은 가격이다. 이 차이를 메우는 코드가 transformer 에 있고, 모델은 건드리지 않는다.

> **핸즈온ML 보강**: [모델 저장과 서빙](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#model-serving) · [사용자 정의 변환기와 파이프라인](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#custom-transformer)

## 5. 클러스터에 배포하기

### 5.1 InferenceService

두 서버를 `InferenceService` 하나에 적는다.

```yaml {title="02-isvc.yaml"}
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: suumo-unit-price
  namespace: suumo-serving
spec:
  predictor:
    serviceAccountName: s3-reader
    containers:
      - name: kserve-container
        image: python:3.11-slim
        command: ["bash", "-c"]
        args:
          - |
            apt-get update -qq && apt-get install -y -qq libgomp1 >/dev/null
            pip install -q --no-cache-dir -r /app/requirements.txt
            exec python /app/predictor.py --model_name suumo-unit-price "$@"
          - "--"
        env:
          - name: STORAGE_URI          # storage initializer 가 이 경로를 /mnt/models 로 받아 둔다
            value: s3://mlflow-artifacts/chapter-4/4/models/m-a28f66ead1d24dc1b03ce3ca318a98f3/artifacts
          - name: OMP_NUM_THREADS     # CPU limit 이 1 이므로 LightGBM 스레드도 1 개로 맞춘다
            value: "1"
        resources:
          requests: {cpu: 500m, memory: 1Gi}
          limits: {cpu: "1", memory: 2Gi}
        volumeMounts:
          - {name: code, mountPath: /app}
    volumes:
      - name: code
        configMap: {name: suumo-serving-code}
  transformer:
    serviceAccountName: s3-reader
    containers:
      - name: kserve-container
        image: python:3.11-slim
        command: ["bash", "-c"]
        args:
          - |
            pip install -q --no-cache-dir -r /app/requirements.txt
            exec python /app/transformer.py "$@"
          - "--"
        env:
          - name: STORAGE_URI          # 주소를 좌표로 바꾸는 초메(丁目) 표
            value: s3://datasets/suumo/prepared/2026-11-13/chome.parquet
        resources:
          requests: {cpu: 250m, memory: 512Mi}
          limits: {cpu: "1", memory: 1Gi}
        volumeMounts:
          - {name: code, mountPath: /app}
    volumes:
      - name: code
        configMap: {name: suumo-serving-code}
```

- **`STORAGE_URI`**: predictor 에는 3.2절에서 찾은 v4 모델의 경로를, transformer 에는 초메(丁目) 표의 경로를 적는다. 둘 다 Pod 안에서는 `/mnt/models` 로 보인다.
- **`OMP_NUM_THREADS`**: LightGBM 은 기본으로 노드의 코어 수만큼 스레드를 띄운다. 컨테이너의 CPU limit 은 1 이라서, 스레드를 1개로 맞추지 않으면 limit 에 걸려 예측이 늦어진다. 이 값을 넣기 전후로 응답 시간 중앙값이 200ms 에서 17ms 로 달라졌다.
- **코드와 패키지**: 이 글에서는 이미지를 새로 만들지 않았다. 코드는 ConfigMap `suumo-serving-code` 로 넣고, 패키지는 컨테이너가 시작할 때 설치한다. 그래서 Pod 가 준비되기까지 80초쯤 걸린다. 실제로 운영할 때는 코드와 패키지를 이미지에 넣어 이 시간을 없앤다.
- **`"$@"`**: KServe 는 transformer 컨테이너의 인자 끝에 `--model_name`, `--predictor_host`, `--http_port` 를 붙인다. 시작 스크립트가 이 인자를 그대로 Python 에 넘긴다.

```text {title="requirements.txt"}
kserve==0.21.0
mlflow==3.16.0
lightgbm==4.7.0
pyarrow
```

MLflow 는 추적 서버와, LightGBM 은 8장 학습 이미지와 같은 버전이다. KServe 0.21.0 이 pandas 3 을 아직 받지 않아 pandas 는 2.3.3 이 들어온다. 예측 값은 9장의 노트북과 같다.

```terminal {title="배포"}
$ kubectl -n suumo-serving create configmap suumo-serving-code \
    --from-file=src/predictor.py --from-file=src/transformer.py --from-file=src/address.py --from-file=src/requirements.txt
$ kubectl apply -f 01-storage.yaml -f 02-isvc.yaml
serviceaccount/s3-reader created
inferenceservice.serving.kserve.io/suumo-unit-price created
$ kubectl -n suumo-serving get isvc suumo-unit-price
NAME               URL                                                 READY   AGE
suumo-unit-price   http://suumo-unit-price-suumo-serving.example.com   True    107s
```

### 5.2 KServe 가 만든 것

적은 것은 `InferenceService` 하나인데 클러스터에는 리소스가 여럿 생긴다.

```terminal {title="InferenceService 하나로 생긴 리소스"}
$ kubectl -n suumo-serving get deploy,svc,httproute,hpa
NAME                                           READY   UP-TO-DATE   AVAILABLE
deployment.apps/suumo-unit-price-predictor     1/1     1            1
deployment.apps/suumo-unit-price-transformer   1/1     1            1

NAME                                   TYPE        CLUSTER-IP      PORT(S)
service/suumo-unit-price-predictor     ClusterIP   10.110.19.29    80/TCP
service/suumo-unit-price-transformer   ClusterIP   10.110.209.55   80/TCP

NAME                                                               HOSTNAMES
httproute.gateway.networking.k8s.io/suumo-unit-price               ["suumo-unit-price-suumo-serving.example.com"]
httproute.gateway.networking.k8s.io/suumo-unit-price-predictor     ["suumo-unit-price-predictor-suumo-serving.example.com"]
httproute.gateway.networking.k8s.io/suumo-unit-price-transformer   ["suumo-unit-price-transformer-suumo-serving.example.com"]

NAME                                                               REFERENCE                                 MINPODS   MAXPODS
horizontalpodautoscaler.autoscaling/suumo-unit-price-predictor     Deployment/suumo-unit-price-predictor     1         1
horizontalpodautoscaler.autoscaling/suumo-unit-price-transformer   Deployment/suumo-unit-price-transformer   1         1
```

| 리소스 | 개수 | 하는 일 |
| --- | ---: | --- |
| Deployment | 2 | predictor 와 transformer 를 따로 띄운다 |
| Service | 2 | 각 Deployment 의 클러스터 안 주소이다. transformer 가 predictor 를 부를 때 쓴다 |
| HTTPRoute | 3 | Gateway 로 들어온 요청을 `Host` 헤더로 나눈다. 서비스 이름의 주소는 transformer 로 간다 |
| HorizontalPodAutoscaler | 2 | CPU 사용률 80% 를 기준으로 Pod 수를 조절한다. 기본값은 최소 1, 최대 1 이다 |

predictor 의 Pod 를 열어 보면 적지 않은 컨테이너가 하나 더 있다.

```terminal {title="predictor Pod 의 init container 와 로그"}
$ kubectl -n suumo-serving get pod -l serving.kserve.io/inferenceservice=suumo-unit-price,component=predictor -o jsonpath='{.items[0].spec.initContainers[*].name}'
storage-initializer
$ kubectl -n suumo-serving logs deploy/suumo-unit-price-predictor -c storage-initializer | tail -2
2026-11-20 14:52:24.783 1 storage.initializer INFO [kserve_storage.py:download():420] Successfully copied s3://mlflow-artifacts/chapter-4/4/models/m-a28f66ead1d24dc1b03ce3ca318a98f3/artifacts to /mnt/models
2026-11-20 14:52:24.783 1 storage.initializer INFO [kserve_storage.py:download():421] Model downloaded in 0.759687270008726 seconds.
```

`STORAGE_URI` 를 보고 KServe 가 끼워 넣은 storage initializer 이다. 모델 폴더를 0.76초에 받았고, transformer 쪽은 초메(丁目) 표를 0.46초에 받았다.

Gateway 는 주소 하나로 여러 서비스의 요청을 받고, 요청의 `Host` 헤더를 보고 어느 서비스로 보낼지 정한다. 이 글에서는 도메인을 따로 연결하지 않았으므로 `curl` 에 `Host` 헤더를 직접 적는다.

### 5.3 요청 보내기

조건은 8장, 9장과 같다. 전용 면적 70m², 2015년 준공, 10층 건물의 5층, 역까지 도보 7분, 3LDK, RC 구조, 남향(南)이다. `instances` 에 주소 네 곳을 한 번에 담아 보냈다.

| 주소 | 단가 (만엔/m²) | 추정 호가 (만엔) | 80% 구간 (만엔) |
| --- | ---: | ---: | --- |
| 미나토구 롯폰기(港区六本木) 3초메 | 404.0 | 28,280 | 11,860 ~ 32,060 |
| 세타가야구 산겐자야(世田谷区三軒茶屋) 2초메 | 214.6 | 15,020 | 10,210 ~ 17,550 |
| 가쓰시카구 가메아리(葛飾区亀有) 3초메 | 91.6 | 6,410 | 4,790 ~ 7,920 |
| 스기나미구 젠푸쿠지(杉並区善福寺) 2초메 (수집 매물 0건) | 161.6 | 11,310 | 8,570 ~ 12,800 |

네 주소 모두 9장 노트북에서 레지스트리의 모델을 직접 불러 뽑은 값과 같다.

필수 값 셋만 보내도 답이 나온다. 비운 조건은 결측으로 들어가고 LightGBM 이 그대로 처리한다.

```terminal {title="필수 값만 보낸 요청"}
$ curl -s http://192.168.0.248/v1/models/suumo-unit-price:predict \
    -H 'Host: suumo-unit-price-suumo-serving.example.com' -H 'Content-Type: application/json' \
    -d '{"instances":[{"address":"東京都世田谷区三軒茶屋2","area":70,"year":2015}]}'
{"predictions":[{"address":"東京都世田谷区三軒茶屋2","chome_key":"世田谷区三軒茶屋2","geo_level":"chome","unit_price":158.9,"price":11120,"low":7340,"high":13270}],"run_id":"45f21d1a4101421888532a9cbd3f0b1b"}
```

같은 자리, 같은 면적인데 단가가 214.6 에서 158.9 로 내려간다. 층, 역까지 거리, 방 구조를 모를 때 모델이 내는 값이므로, 조건을 채울수록 답이 달라진다는 것을 서비스 사용자에게 알려야 한다.

받을 수 없는 입력은 predictor 까지 가지 않고 transformer 에서 걸러진다.

| 요청 | 응답 코드 | 응답 |
| --- | ---: | --- |
| 23구 밖의 주소(`大阪府大阪市北区梅田1`) | 400 | `{"error":"주소를 찾지 못했다. 도쿄 23구의 구, 동, 초메까지 적는다: 大阪府大阪市北区梅田1"}` |
| 면적에 글자(`"area":"넓음"`) | 400 | `{"error":"입력이 맞지 않는다: area (Input should be a valid number, unable to parse string as a number)"}` |

좌표를 이미 가진 프로그램은 transformer 를 거치지 않고 predictor 를 바로 부를 수 있다. `Host` 헤더만 predictor 의 것으로 바꾼다.

```terminal {title="predictor 에 직접 두 행"}
$ curl -s http://192.168.0.248/v1/models/suumo-unit-price:predict \
    -H 'Host: suumo-unit-price-predictor-suumo-serving.example.com' -H 'Content-Type: application/json' \
    -d '{"instances":[{"lat":35.6436,"lon":139.6693,"専有面積_m2":70,"築年":2015,"所在階_階":5,"総階数":10,"最短徒歩分":7,"間取り":"3LDK","構造":"RC","向き":"南"},
                      {"lat":35.7664,"lon":139.8483,"専有面積_m2":55,"築年":1995}]}'
{"predictions":[{"unit_price":214.7775,"low":145.8863,"high":264.1875},{"unit_price":50.7366,"low":45.5587,"high":71.9312}],"run_id":"45f21d1a4101421888532a9cbd3f0b1b"}
```

| `Host` 헤더 | 받는 것 | 돌려주는 것 | 누가 쓰나 |
| --- | --- | --- | --- |
| `suumo-unit-price-...` | 주소와 조건 | 추정 호가, 구간, 찾은 초메, run ID | 사람, 화면 |
| `suumo-unit-price-predictor-...` | 피처 행 | 행마다 단가와 구간, run ID | 다른 프로그램, 배치 |

같은 요청을 50번씩 차례로 보냈을 때 응답 시간 중앙값은 transformer 를 거치는 경로가 17.6ms, predictor 직접 호출이 15.5ms 였다.

## 6. 모델 두 개를 나란히 띄워 비교하기

비교용으로 v1 모델의 서비스를 하나 더 띄운다. 8장과 같은 설정으로 학습한 모델이다. `02-isvc.yaml` 에서 이름과 모델 경로 두 곳만 바꾼다.

```yaml {title="03-isvc-v1.yaml (02-isvc.yaml 과 다른 부분)"}
metadata:
  name: suumo-unit-price-v1
...
            exec python /app/predictor.py --model_name suumo-unit-price-v1 "$@"
...
          - name: STORAGE_URI
            value: s3://mlflow-artifacts/chapter-4/4/models/m-5990e5427d844aa9ac9b042c5a2f1834/artifacts
```

```terminal {title="InferenceService 두 개"}
$ kubectl apply -f 03-isvc-v1.yaml
inferenceservice.serving.kserve.io/suumo-unit-price-v1 created
$ kubectl -n suumo-serving get isvc
NAME                  URL                                                    READY   AGE
suumo-unit-price      http://suumo-unit-price-suumo-serving.example.com      True    55m
suumo-unit-price-v1   http://suumo-unit-price-v1-suumo-serving.example.com   True    53m
```

두 서비스는 같은 Gateway 뒤에 있고 `Host` 헤더만 다르다. 같은 요청을 둘에 동시에 보내는 스크립트를 쓴다.

```python {title="compare.py (핵심 부분)"}
async def ask(client: httpx.AsyncClient, gateway: str, name: str) -> dict:
    r = await client.post(f"{gateway}/v1/models/{name}:predict", json={"instances": [LISTING]},
                          headers={"Host": f"{name}-suumo-serving.example.com"})   # Gateway 는 Host 로 서비스를 고른다
    body = r.json()
    return {"service": name, "run_id": body["run_id"][:8], **body["predictions"][0]}


async def main(gateway: str, names: list):
    async with httpx.AsyncClient(timeout=10) as client:
        for row in await asyncio.gather(*(ask(client, gateway, n) for n in names)):
            print(json.dumps(row, ensure_ascii=False))
```

`asyncio.gather` 는 두 요청을 차례로 기다리지 않고 한꺼번에 보낸 뒤 둘 다 끝나면 돌아온다.

```terminal {title="같은 요청을 두 서비스에"}
$ python compare.py http://192.168.0.248 suumo-unit-price suumo-unit-price-v1
{"service": "suumo-unit-price", "run_id": "45f21d1a", "address": "東京都世田谷区三軒茶屋2", "chome_key": "世田谷区三軒茶屋2", "geo_level": "chome", "unit_price": 214.6, "price": 15020, "low": 10210, "high": 17550}
{"service": "suumo-unit-price-v1", "run_id": "1f53c751", "address": "東京都世田谷区三軒茶屋2", "chome_key": "世田谷区三軒茶屋2", "geo_level": "chome", "unit_price": 206.8, "price": 14470, "low": 9920, "high": 16620}
```

| | prod (v4) | v1 |
| --- | ---: | ---: |
| 단가 (만엔/m²) | 214.6 | 206.8 |
| 추정 호가 (만엔) | 15,020 | 14,470 |
| 80% 구간 (만엔) | 10,210 ~ 17,550 | 9,920 ~ 16,620 |

v1 의 값은 8장 글의 같은 주소 결과(206.8, 14,470)와 같다. 새 모델을 `prod` 로 올리기 전에 지금 모델과 같은 요청으로 나란히 돌려 보는 용도로 쓸 수 있다.

레지스트리에서 `prod` 가 다른 버전으로 옮겨 가도 이미 띄운 서비스는 바뀌지 않는다. `STORAGE_URI` 에 버전의 저장 경로가 그대로 적혀 있기 때문이다. 배포된 서비스가 어느 모델로 답하는지는 이 경로와 응답의 `run_id` 로 정해지고, 거기서 9장의 run 과 데이터까지 거슬러 올라갈 수 있다.

> **핸즈온ML 보강**: [재현 가능하게 남기기](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#reproducibility)

## 7. 서비스 상태 확인하기

### 7.1 InferenceService 의 상태

`InferenceService` 는 자기 부품이 준비됐는지를 조건(condition)으로 적어 둔다.

```terminal {title="InferenceService 의 조건"}
$ kubectl -n suumo-serving get isvc suumo-unit-price \
    -o jsonpath='{range .status.conditions[*]}{.type}={.status}{"\n"}{end}'
IngressReady=True
PredictorReady=True
Ready=True
Stopped=False
TransformerReady=True
```

| 조건 | 뜻 |
| --- | --- |
| `PredictorReady` | predictor 의 Deployment 가 떴다 |
| `TransformerReady` | transformer 의 Deployment 가 떴다 |
| `IngressReady` | Gateway 로 들어오는 길(HTTPRoute)이 만들어졌다 |
| `Ready` | 위 셋이 모두 참이다. `kubectl get isvc` 의 `READY` 열이 이 값이다 |

### 7.2 상태 확인 주소

Kubernetes 는 Pod 가 살아 있는지, 요청을 받을 준비가 됐는지를 정해진 주소로 물어본다. KServe SDK 로 만든 서버에는 이 주소가 처음부터 들어 있다.

```terminal {title="상태 확인"}
$ H='Host: suumo-unit-price-suumo-serving.example.com'
$ curl -s -H "$H" http://192.168.0.248/v2/health/live
{"live":true}
$ curl -s -H "$H" http://192.168.0.248/v2/health/ready
{"ready":true}
$ curl -s -H "$H" http://192.168.0.248/v1/models/suumo-unit-price
{"name":"suumo-unit-price","ready":true}
```

| 주소 | 뜻 |
| --- | --- |
| `/v2/health/live` | 서버 프로세스가 살아 있다 |
| `/v2/health/ready` | 서버가 요청을 받을 수 있다 |
| `/v1/models/<이름>` | 그 이름의 모델이 준비됐다. 3.1절의 `self.ready` 값이다 |

Pod 가 준비되기 전에는 Service 가 그 Pod 로 요청을 보내지 않는다. 모델을 읽는 중에 요청이 들어오는 일을 이것으로 막는다.

### 7.3 지표

`/metrics` 는 Prometheus 형식의 지표를 내준다. 3장에서 FastAPI 앱에 지표 코드를 직접 넣었던 것과 달리 코드를 한 줄도 쓰지 않았다.

```terminal {title="predictor 의 /metrics (발췌)"}
$ curl -s -H 'Host: suumo-unit-price-predictor-suumo-serving.example.com' http://192.168.0.248/metrics | grep request_predict
request_predict_seconds_bucket{le="0.005",model_name="suumo-unit-price"} 0.0
request_predict_seconds_bucket{le="0.01",model_name="suumo-unit-price"} 203.0
request_predict_seconds_bucket{le="0.025",model_name="suumo-unit-price"} 210.0
request_predict_seconds_count{model_name="suumo-unit-price"} 210.0
request_predict_seconds_sum{model_name="suumo-unit-price"} 1.916993738966994
```

| 지표 | 내용 |
| --- | --- |
| `request_preprocess_seconds` | 입력을 다듬는 데 걸린 시간 분포 |
| `request_predict_seconds` | 예측에 걸린 시간 분포 |
| `request_postprocess_seconds` | 출력을 다듬는 데 걸린 시간 분포 |

predictor 가 받은 요청 210건 가운데 203건이 10ms 안에, 210건 모두가 25ms 안에 끝났다. 평균은 9.1ms 이다. transformer 와 predictor 가 지표를 따로 내므로, 느려졌을 때 주소 변환이 느린지 모델이 느린지를 가를 수 있다.

> **핸즈온ML 보강**: [모니터링과 재학습](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#monitoring)

## 8. MLflow 만으로 서빙하기

KServe 를 쓰지 않고 MLflow 만으로도 모델을 서비스로 띄울 수 있다. 서비스 코드를 쓰지 않고 명령 한 줄이면 된다. 이 절은 클러스터가 아니라 개발 PC 에서 실행했다.

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

같은 좌표와 조건을 KServe 의 predictor 에 직접 넣었을 때의 214.7775, 145.8863, 264.1875 와 같은 값이다. 9장에서 모델에 서명을 붙여 두었으므로 서버가 입력의 컬럼 이름과 타입을 서명에 맞춰 준다.

컨테이너로 만드는 명령도 있다. `mlflow models build-docker -m "models:/suumo-unit-price@prod" -n suumo-unit-price` 가 같은 서버를 담은 이미지를 만든다.

| | KServe InferenceService | MLflow 서빙 |
| --- | --- | --- |
| 준비한 것 | `predictor.py`, `transformer.py`, `InferenceService` 매니페스트 | 명령 한 줄 |
| 띄우는 곳 | Kubernetes 클러스터 | 명령을 실행한 곳 |
| 주소 | `/v1/models/<이름>:predict` | `/invocations` |
| 입력 | 주소와 조건 (predictor 직접 호출은 피처 행) | 위도, 경도와 학습 때의 컬럼 이름 |
| 출력 | 호가(만엔), 구간, 찾은 초메, run ID | m²당 단가와 구간 |
| 상태 확인 | `/v2/health/live`, `/v2/health/ready` | `/health`, `/ping` |
| 지표 | `/metrics` (Prometheus) | 기본으로는 없다 |
| 프로세스 | transformer 와 predictor 가 따로 | 서버 하나 |
| 모델을 읽는 시점 | Pod 가 뜰 때 버킷에서 받는다 | 띄울 때 레지스트리에서 받는다 |

MLflow 서빙은 준비할 것이 거의 없다. 대신 주소를 좌표로 바꾸는 일, 단가를 가격으로 바꾸는 일, 지표를 내는 일은 요청하는 쪽이나 다른 서비스가 맡아야 한다.

## 9. 세 도구 비교

모델 서빙 도구로 [6장](../mlpe-06-1-bentoml-yatai/)에서는 BentoML 을 썼다. BentoML 은 서비스 코드, 모델, 패키지를 Bento 라는 꾸러미로 묶고, Yatai 가 그것을 클러스터에 띄운다. 세 도구를 나란히 놓으면 이렇다.

|               | KServe                        | MLflow                   | BentoML                  |
| ------------- | ----------------------------- | ------------------------ | ------------------------ |
| 중심            | Kubernetes 위의 서빙 운영           | 실험부터 서빙까지 ML 수명주기 전체     | 모델을 서비스로 묶어 배포하기         |
| 서비스 코드        | 기본 런타임은 쓰지 않는다. 필요하면 SDK 로 쓴다 | 쓰지 않는다 (pyfunc 에 넣어야 한다) | Python 으로 자유롭게 쓴다        |
| 배포를 적는 곳      | `InferenceService` 매니페스트      | 명령의 인자                   | `bentofile.yaml`         |
| Kubernetes 지식 | 필요하다                          | 없어도 된다                   | 없어도 된다 (Yatai 가 맡는다)     |
| 실험 추적         | 없다                            | 있다                       | 없다                       |
| 스케일링          | 처음부터 들어 있다 (Knative 모드는 0 까지) | 직접 만든다                   | Yatai 나 직접 만든 Deployment |
| 이 스터디에서       | 10장 (이 글)                     | 9장, 10장                  | 6장                       |

이 프로젝트는 주소를 좌표로 바꾸는 코드가 모델 앞에 꼭 있어야 한다. KServe 에서는 그 코드를 transformer 로 떼어 내고, 모델의 버전과 출처는 MLflow 가 맡는 구성이 됐다. 모델에 좌표를 그대로 넣는 내부 배치 작업이라면 MLflow 서빙만으로 충분하다.

11장에서는 이 서비스에 모니터링과 드리프트 탐지를 붙인다.
