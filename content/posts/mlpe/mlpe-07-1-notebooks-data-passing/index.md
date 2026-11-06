---
title: "MLPE 스터디 3주차 - Ch7.1 ~ 7.2 Kubeflow 노트북과 KFP 데이터 전달"
date: 2026-11-06T22:30:00+09:00
draft: false
tags: ["MLOps", "MLPE", "Kubeflow", "Kubeflow Notebooks", "PodDefault", "Kubeflow Pipelines", "KFP", "Artifact", "Kubernetes"]
categories: ["MLOps"]
series: ["MLPE 3주차"]
---
`Machine Learning Platform Engineering` 파트 3은 1 ~ 6장에서 갖춘 플랫폼을 **실제 프로젝트**에 적용한다. 캡스톤 프로젝트는 세 개이고, 7장은 그중 **신분증 객체 탐지기**와 **영화 추천 시스템**의 첫 단계인 **데이터 분석과 준비**를 다룬다. 이 글은 7장의 앞부분인 7.1절 Kubeflow 노트북과 7.2절 KFP 데이터 전달을 정리하고, 1 ~ 6주차 홈랩 Kubernetes 위에 직접 올리고 돌린 결과를 함께 적는다.

## 1. 한눈에 보기

MLOps 파이프라인 그림에서 7장은 **데이터 수집·준비** 자리다. 7.1절은 그 단계를 사람이 노트북으로 탐색하는 방법이고, 7.2절은 같은 단계를 KFP 컴포넌트로 나눴을 때 컴포넌트 사이로 데이터를 넘기는 방법이다.

![MLOps 파이프라인 그림에서 7장이 채우는 자리. 데이터 수집·준비 상자가 초록으로 강조돼 있고 부제는 Kubeflow 노트북 · EDA 다. 파이프라인 오케스트레이션 점선 상자는 KFP 색으로 켜져 있고, 데이터 수집·준비에서 모델 학습으로 가는 화살표에 값 .output, 경로 .path 라고 적혀 있다. 모델 학습은 다음 장 학습 파이프라인으로 점선 표시돼 있다. 데이터 수집·준비에서 실험 추적(MLFLOW_TRACKING_URI)으로 PodDefault 주입 점선 화살표가 간다. 오른쪽 카드는 Notebook CR 이 StatefulSet 과 PVC 를 만들고, PodDefault 가 MLflow 와 KFP 주소를 env 로 넣으며, 작은 값은 반환값과 .output, 큰 데이터는 Output[Artifact].path 로 넘긴다고 정리하고, 캡스톤은 신분증 탐지와 영화 추천이라고 적는다](notebook-pipeline-overview.svg)

| 절 | 다루는 것 | 핵심 |
|---|---|---|
| 7.1 | Kubeflow 노트북 | 노트북 서버를 클러스터 안에 띄우고 PodDefault 로 설정을 주입한다 |
| 7.2 | KFP 데이터 전달 | 작은 값은 반환값으로, 큰 데이터는 아티팩트 경로로 넘긴다 |
| 7.3 | 캡스톤 데이터 준비 | 신분증 탐지(YOLO)와 MovieLens 추천의 데이터 준비 파이프라인 (다음 글) |

## 2. 7장과 캡스톤 프로젝트

새 아키텍처는 매주 나온다. 예전에는 YOLO 와 ResNet 이, 지금은 LLM 과 VLM 이 화제의 중심이다. 그래도 결과의 품질은 결국 **입력 데이터의 품질**에 달려 있고, 7장은 그래서 데이터 준비부터 시작한다.

| 캡스톤 | 데이터 | 7장에서 하는 일 |
|---|---|---|
| **1. 신분증 탐지** | 신분증 이미지 | YOLO 변형 모델로 객체를 탐지하기 위한 데이터 준비 파이프라인 |
| **2. 영화 추천** | MovieLens | 테이블 형식 데이터를 다루는 컴포넌트 6개를 하나의 데이터 준비 파이프라인으로 묶는다 |

책은 캡스톤에 바로 들어가지 않고 **농담 생성 파이프라인**이라는 작은 예제로 개념을 먼저 잡는다. 노트북 데이터 분석, 파이프라인 안의 데이터 전달, 데이터를 넘기는 컴포넌트 작성이 그 예제에서 나온다. 캡스톤 구현은 7.3절에서 다룬다.

## 3. 7.1 데이터 분석과 Kubeflow 노트북

### 3.1 왜 노트북을 클러스터에 띄우나

데이터 분석은 인프라에 두 가지 요구를 동시에 건다. 데이터셋이 아무리 커도 다룰 수 있게 **데이터 가까이에서** 돌아야 하고, GPU 처럼 비싼 자원을 필요할 때만 **대화식으로** 켜고 꺼야 한다. 예를 들어 학습 데이터에 대한 객체 탐지 결과를 보다가 노트북에서 모델을 불러 바로 추론해 보고 싶을 때가 있다.

여기에 배포 환경과 비슷한 환경에서 실험하고, 버전 관리와 CI/CD 를 적용하라는 권장까지 더해진다. 기존 방식이라면 팀 하나가 붙어야 하는 일이다.

**Kubeflow 노트북**은 이 요구를 한 번에 받는다. 브라우저에서 Jupyter, VS Code(code-server), RStudio 를 띄우고, 파이프라인과 **같은 베이스 이미지**를 쓸 수 있어 배포 환경과 차이가 작다. 노트북 이미지도 파이프라인·배포 컨테이너와 같은 CI 에서 빌드하면 버전 관리까지 맞춰진다.

### 3.2 노트북 서버 실행

Kubeflow UI 의 Notebooks 메뉴에서 **NEW NOTEBOOK** 을 누르면 생성 화면이 나온다. 이때 고르는 **네임스페이스**는 리소스 할당량, 볼륨 마운트, Secret 에 모두 영향을 주므로 주의해서 고른다.

| 항목 | 의미 |
|---|---|
| Image | 띄울 컨테이너 이미지. 지금은 샘플을 쓰고 커스텀 이미지는 3.6절에서 다룬다 |
| CPU / Memory | Kubernetes 의 requests 와 limits 그대로다. 테스트할 때 메모리 한도를 너무 낮게 잡지 않는다 |
| GPUs | GPU 나 TPU 같은 가속기 수량. 오버프로비저닝이 없으면 노트북이 그 자원을 다른 Pod 에게서 막는다 |

GPU 를 노트북에 붙이면 **유휴 상태일 때 Pod 를 종료하는 수명주기 규칙**(culling)을 함께 둔다. 노트북은 켜 두고 잊기 쉬운데, 그동안 비싼 GPU 가 묶여 있기 때문이다.

### 3.3 워크스페이스와 데이터 볼륨

노트북을 만들면 Kubeflow 가 **워크스페이스 볼륨**을 `/home/jovyan` 에 마운트한다. 환경 파일과 설정 파일이 여기에 남으므로 컨테이너를 바꿔도 작업 내용이 유지된다.

| 볼륨 | 만들어지는 방식 | 용도 |
|---|---|---|
| 워크스페이스 볼륨 | 시작할 때 기본 StorageClass 로 새 PVC 를 만든다 (기존 것을 고를 수도 있다) | 홈 디렉터리, 설정, 노트북 파일 |
| 데이터 볼륨 | 대부분 이미 있는 PVC 를 런타임에 마운트한다 | 데이터셋처럼 여러 노트북이 함께 쓰는 데이터 |

PVC 는 컨테이너가 스토리지를 요청하는 수단이다. 애플리케이션은 PVC 만 요청하고, 실제 볼륨은 클러스터의 프로비저너가 만들어 붙인다.

### 3.4 PodDefault, 어피니티, 톨러레이션

생성 화면의 Configurations 는 네임스페이스에 있는 **PodDefault** 목록이다. PodDefault 는 라벨이 맞는 Pod 가 생성될 때 env, 볼륨, Secret 같은 설정을 **주입**(injection)하는 리소스다. 책 리스팅 7.1 은 프록시 변수를 넣는 예제이고, 여기서는 이후 장에서 중요해지는 `MLFLOW_TRACKING_URI` 만 남겼다.

```yaml {title="Listing 7.1 변형: PodDefault"}
apiVersion: kubeflow.org/v1alpha1
kind: PodDefault
metadata:
  name: add-ml-env
  namespace: kubeflow
spec:
  desc: add MLflow endpoint
  env:
    - name: MLFLOW_TRACKING_URI
      value: http://mlflow.kubeflow.svc.cluster.local:5000
  selector:
    matchLabels:
      add-ml-env: "true"
```

노트북을 만들 때 이 설정을 고르면 Pod 에 `add-ml-env: "true"` 라벨이 붙고, 웹훅이 env 를 넣는다. 같은 방식으로 인증 정보, 특수 설정, 볼륨 마운트도 넣을 수 있다. 경로와 PVC 이름을 클러스터 쪽에서 정해 두므로 사용자에게 볼륨을 고르게 하는 가장 간단한 방법이기도 하다.

**어피니티**(affinity)와 **톨러레이션**(toleration)은 Kubernetes 기능 그대로다. 어피니티는 Pod 를 특정 라벨의 노드로 끌어당기고, 톨러레이션은 **테인트**(taint)가 걸린 노드에 Pod 가 들어갈 수 있게 한다. 가장 흔한 용도는 GPU 노드 접근을 제어하는 것이다.

마지막으로 공유 메모리를 켤지 정하고 Launch 를 누른다. 분산 학습이나 메모리 캐시를 쓰는 데이터 로더는 공유 메모리의 이점을 본다. Pod 안을 보면 메인 컨테이너와 초기화 컨테이너 외에 **Istio 사이드카**도 있는데, Kubeflow 가 노트북 네트워킹을 이것으로 감춘다.

노트북은 `kubeflow.org` 그룹의 CRD 로 관리된다.

```bash
kubectl get crd -o=name | grep kubeflow.org
# customresourcedefinition.apiextensions.k8s.io/notebooks.kubeflow.org
```

### 3.5 메뉴 커스터마이징

관리자는 노트북 생성 화면의 기본값과 선택지를 바꿀 수 있다. 대표적인 예가 배포 환경과 맞춘 이미지 목록만 보여 주는 것이다. 설정은 `kubeflow` 네임스페이스의 `jupyter-web-app-config` 로 시작하는 ConfigMap 에 있다.

```bash
kubectl get cm -n kubeflow | grep jupyter-web-app-config
```

항목마다 기본값(`value`)과 `readOnly` 태그가 있고, `readOnly` 인 항목은 사용자가 바꿀 수 없다. 이미지는 그룹으로 나뉜다.

```yaml {title="Listing 7.2 jupyter-web-app ConfigMap (일부)"}
spawner_ui_config.yaml: |
  spawnerFormDefaults:
    image:                      # Jupyter
      value: kubeflownotebookswg/jupyter-scipy:v1.6.1
      options:
        - asia.gcr.io/kubeflow-notebook-servers/jupyter-tensorflow:2.6.0
        - asia.gcr.io/kubeflow-notebook-servers/jupyter-pytorch:1.9.0
    imageGroupOne:              # code-server
      - kubeflownotebookswg/codeserver-python:v1.6.1
    imageGroupTwo:              # RStudio
      - kubeflownotebookswg/rstudio-tidyverse:v1.6.1
```

`options` 목록을 CD 파이프라인이 고치게 하면 새 이미지가 빌드될 때 노트북 메뉴에도 자동으로 올라간다. 이미지 필드를 편집 불가로 두면 사용자는 목록에 있는 이미지만 고를 수 있다.

어피니티도 선택지로 만들 수 있다. 노드마다 CPU 성능이 다르다면 `compute=small`, `compute=xl` 라벨에 맞춘 선택지를 두 개 둔다.

<details class="orca-details">
<summary>Listing 7.3 노드 어피니티 선택지</summary>

```yaml
affinityConfig:
  value: ""
  options:
    - configKey: "small-cpu-selector"
      displayName: "small-cpu-node"
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: "compute"
                    operator: "In"
                    values: ["small"]
    - configKey: "xl-cpu-selector"
      displayName: "xl-cpu-node"
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: "compute"
                    operator: "In"
                    values: ["xl"]
```

</details>

기본값을 small 로 두면 노트북은 평소 소형 노드에 가고, 고성능 노드는 필요한 노트북을 위해 남는다. 다만 어피니티만으로는 다른 Pod 가 고성능 노드에 들어가는 것을 막지 못한다. 접근을 막아야 하면 노드에 테인트를 걸고 톨러레이션 설정을 함께 둔다.

### 3.6 커스텀 노트북 이미지

커스텀 이미지는 세 층으로 이뤄진다: 베이스 이미지 위에 Jupyter 나 code-server 가 쓰는 **의존성**, **런타임** 자체, 그리고 Kubeflow 와 맞물리도록 노트북 서버를 띄우는 **설정 파일**이다. 프로젝트 저장소에는 베이스 이미지를 인자로 받아 두 런타임 중 하나를 빌드하는 멀티스테이지 Dockerfile 이 있다. 조직에 들일 때는 이 Dockerfile 을 검토해 이미지 크기부터 줄인다.

노트북은 로컬에서 일하던 데이터 과학자에게 가장 익숙한 화면이다. 커스텀 이미지와 묶으면 Git 기반 워크플로로 옮겨 가는 길이 짧아진다.

## 4. 홈랩 실습: Kubeflow Notebooks 경량 설치

홈랩 KFP 는 **standalone 2.17.3** 이라 Central Dashboard, Jupyter Web App, Istio, Profile 이 없다. 전체 Kubeflow 를 올리기에는 amd64 워커(worker1-gpu) 메모리가 모자라므로 **notebook-controller 와 PodDefault 웹훅만 설치**하고 Notebook 과 PodDefault CR 을 직접 만들어 7.1.1 ~ 7.1.3 을 재현했다. 매니페스트는 홈랩 레포 `kubeflow-notebooks/` 에 단계별로 두었다.

### 4.1 자리 만들기

설치 전 worker1-gpu 의 메모리 requests 는 **94%(30Gi)** 였다. 그중 절반인 15.6Gi 를 지금 쓰지 않는 llm-d(vLLM decode Pod 2개 8Gi, 6Gi 와 EPP)가 잡고 있어서, 지우지 않고 replicas 0 으로 내렸다. requests 는 **46%(14.3Gi)** 로 떨어졌다.

```bash
kubectl -n llm-d scale deploy optimized-baseline-nvidia-gpu-vllm-decode small-vllm-decode \
  llm-d-epp llm-d-small-epp payload-processor --replicas=0
```

`llm-d-inference-gateway-istio` 는 Gateway 리소스가 소유해 0 으로 내려도 Istio 가 되살리므로 남겼다. 다시 쓰려면 같은 Deployment 를 `--replicas=1` 로 올리면 된다.

### 4.2 핵심 개념

| 항목 | 내용 |
|---|---|
| 설치 범위 | `notebook-controller:v1.11.0` 과 `poddefaults-webhook:v2.0.0` 만. kubeflow/manifests **26.03.1** 의 kustomize 를 원격으로 참조한다 |
| 웹훅 위치 | PodDefault 웹훅은 `applications/dashboard/upstream/poddefaults-webhooks` 에 있다 (notebooks-v1 이 아니다) |
| 인증서 | 홈랩에 이미 있는 cert-manager v1.21.3 이 웹훅 인증서를 발급하고 CA 를 웹훅 설정에 넣는다 |
| 대상 네임스페이스 | 웹훅 `namespaceSelector` 는 `app.kubernetes.io/part-of=kubeflow-profile` 라벨이 붙은 네임스페이스만 본다. Profile 컨트롤러가 없으니 라벨을 직접 붙인다 |
| 주입 조건 | Notebook CR 의 `metadata.labels` 가 Pod 로 전파되고, PodDefault `selector.matchLabels` 와 맞으면 env 와 볼륨이 들어간다 |
| Istio | 없으므로 `USE_ISTIO=false`. 접속 경로 앞에는 `NB_PREFIX`(`/notebook/<ns>/<name>`)가 붙고, 이 접두사 없이 접속하면 404 다 |
| 유휴 정지 | 책 3.2절의 culling 을 켰다. 커널 활동이 120분 없으면 StatefulSet 을 0 으로 내린다 |

웹훅의 `failurePolicy` 는 `Fail` 이다. 웹훅이 죽으면 라벨 붙은 네임스페이스의 **Pod 생성 자체가 막히므로**, 라벨은 노트북 전용 `kubeflow-user` 에만 붙였다. 2주차 JupyterLab 이 있는 `mlflow` 네임스페이스에는 붙이지 않고, 그 노트북도 그대로 두었다.

### 4.3 컨트롤러와 웹훅

두 kustomization 은 upstream 오버레이를 그대로 가져와 설정만 덮는다. 둘 다 amd64 노드에 고정했다.

```yaml {title="01-notebook-controller/kustomization.yaml"}
resources:
  - https://github.com/kubeflow/manifests/applications/notebooks-v1/upstream/notebook-controller/overlays/kubeflow?ref=26.03.1

configMapGenerator:
  - name: config
    behavior: merge
    literals:
      - USE_ISTIO=false
      - ISTIO_GATEWAY=
      - ENABLE_CULLING=true
      - CULL_IDLE_TIME=120         # 분
      - IDLENESS_CHECK_PERIOD=5

patches:
  - target: {kind: Deployment, name: notebook-controller-deployment}
    patch: |-
      - op: add
        path: /spec/template/spec/nodeSelector
        value: {kubernetes.io/arch: amd64}
```

```yaml {title="02-poddefaults-webhook/kustomization.yaml"}
resources:
  - https://github.com/kubeflow/manifests/applications/dashboard/upstream/poddefaults-webhooks/overlays/cert-manager?ref=26.03.1

patches:
  - target: {kind: Deployment, name: poddefaults-webhook-deployment}
    patch: |-
      - op: add
        path: /spec/template/spec/nodeSelector
        value: {kubernetes.io/arch: amd64}
```

CRD 스키마가 커서 `--server-side` 로 적용한다.

```bash
kubectl apply --server-side --force-conflicts -k 01-notebook-controller/
kubectl apply --server-side --force-conflicts -k 02-poddefaults-webhook/
kubectl -n kubeflow wait --for=condition=Ready certificate/poddefaults-webhook-cert --timeout=2m
```

### 4.4 네임스페이스와 PodDefault

책 리스팅 7.1 에서 프록시 변수를 빼고, PodDefault 를 역할별로 두 개 만들었다. `add-ml-env` 는 MLflow 와 KFP 주소를, `add-rustfs-creds` 는 RustFS(S3) 주소와 키를 넣는다. 키는 Secret 참조라 매니페스트에 값이 없다.

```yaml {title="03-user-namespace/poddefaults.yaml"}
apiVersion: kubeflow.org/v1alpha1
kind: PodDefault
metadata:
  name: add-ml-env
  namespace: kubeflow-user
spec:
  desc: MLflow, KFP 주소
  selector:
    matchLabels:
      add-ml-env: "true"
  env:
    - name: MLFLOW_TRACKING_URI
      value: http://mlflow.mlflow.svc.cluster.local:5000
    - name: KF_PIPELINES_ENDPOINT
      value: http://ml-pipeline.kubeflow.svc.cluster.local:8888
---
apiVersion: kubeflow.org/v1alpha1
kind: PodDefault
metadata:
  name: add-rustfs-creds
  namespace: kubeflow-user
spec:
  desc: RustFS(S3) 주소와 키
  selector:
    matchLabels:
      add-rustfs-creds: "true"
  env:
    - name: MLFLOW_S3_ENDPOINT_URL
      value: http://rustfs.mlflow.svc.cluster.local:9000
    - name: AWS_ENDPOINT_URL
      value: http://rustfs.mlflow.svc.cluster.local:9000
    - name: AWS_ACCESS_KEY_ID
      valueFrom:
        secretKeyRef: {name: rustfs-credentials, key: AWS_ACCESS_KEY_ID}
    - name: AWS_SECRET_ACCESS_KEY
      valueFrom:
        secretKeyRef: {name: rustfs-credentials, key: AWS_SECRET_ACCESS_KEY}
```

6.1절 Yatai 는 env 의 `valueFrom` 을 버려서 ServiceAccount 로 우회했다. PodDefault 는 env 를 Pod 스펙에 그대로 합치므로 `valueFrom` 이 살아 있다. Secret 은 `kubeflow` 네임스페이스의 `rustfs-credentials` 를 값을 찍지 않고 복사했다.

### 4.5 Notebook

Notebook CR 의 `image`, `resources`, `volumeMounts` 가 책 7.1.1 ~ 7.1.2 생성 화면의 항목에 대응한다. 라벨 두 개로 PodDefault 를 고른다.

```yaml {title="04-notebook/notebook.yaml"}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-nb-workspace
  namespace: kubeflow-user
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: local-path-worker1
  resources:
    requests:
      storage: 5Gi
---
apiVersion: kubeflow.org/v1
kind: Notebook
metadata:
  name: test-nb
  namespace: kubeflow-user
  labels:
    add-ml-env: "true"
    add-rustfs-creds: "true"
spec:
  template:
    spec:
      nodeSelector:
        kubernetes.io/arch: amd64
      containers:
        - name: test-nb
          image: ghcr.io/kubeflow/kubeflow/notebook-servers/jupyter-scipy:v1.11.0
          resources:
            requests: {cpu: "500m", memory: 1Gi}
            limits: {cpu: "2", memory: 4Gi}
          volumeMounts:
            - name: workspace
              mountPath: /home/jovyan     # 워크스페이스 볼륨
      volumes:
        - name: workspace
          persistentVolumeClaim:
            claimName: test-nb-workspace
```

<details class="orca-details">
<summary>scripts/install.sh: 단계별 설치 (controller webhook namespace notebook)</summary>

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
STAGES="${1:-controller webhook namespace notebook}"

for s in ${STAGES}; do
  case "$s" in
    controller)
      kubectl apply --server-side --force-conflicts -k "${BASE_DIR}/01-notebook-controller/"
      kubectl -n kubeflow rollout status deploy/notebook-controller-deployment --timeout=5m ;;
    webhook)
      kubectl apply --server-side --force-conflicts -k "${BASE_DIR}/02-poddefaults-webhook/"
      kubectl -n kubeflow wait --for=condition=Ready certificate/poddefaults-webhook-cert --timeout=2m
      kubectl -n kubeflow rollout status deploy/poddefaults-webhook-deployment --timeout=5m ;;
    namespace)
      kubectl apply -f "${BASE_DIR}/03-user-namespace/namespace.yaml"
      # 키 값은 화면에 찍지 않고 kubeflow 네임스페이스의 Secret 을 그대로 복사한다
      kubectl -n kubeflow get secret rustfs-credentials -o json \
        | python3 -c 'import json,sys; s=json.load(sys.stdin); m=s["metadata"]; s["metadata"]={"name":m["name"],"namespace":"kubeflow-user"}; print(json.dumps(s))' \
        | kubectl apply -f -
      kubectl apply -f "${BASE_DIR}/03-user-namespace/poddefaults.yaml" ;;
    notebook)
      kubectl apply -f "${BASE_DIR}/04-notebook/notebook.yaml"
      kubectl -n kubeflow-user rollout status sts/test-nb --timeout=10m ;;
  esac
done
```

</details>

### 4.6 결과

컨트롤러가 Notebook CR 을 보고 StatefulSet 과 Service 를 만들고, Pod 가 생길 때 웹훅이 PodDefault 두 개를 합쳤다. Pod annotation 에 적용된 PodDefault 가 기록된다.

```bash
kubectl -n kubeflow-user get notebook,sts,pod,pvc
# notebook.kubeflow.org/test-nb
# statefulset.apps/test-nb                   1/1
# pod/test-nb-0                              1/1   Running   worker1-gpu
# persistentvolumeclaim/test-nb-workspace    Bound   5Gi   RWO   local-path-worker1

kubectl -n kubeflow-user get pod test-nb-0 -o jsonpath='{.metadata.annotations}'
# poddefault.admission.kubeflow.org/poddefault-add-ml-env: "26998020"
# poddefault.admission.kubeflow.org/poddefault-add-rustfs-creds: "26998021"
```

접속은 port-forward 로 한다. Istio 인증이 없는 구성이라 **토큰 없이 열리므로** LoadBalancer 로 내놓지 않았다.

```bash
kubectl -n kubeflow-user port-forward svc/test-nb 18888:80
# 브라우저: http://localhost:18888/notebook/kubeflow-user/test-nb/lab
```

노트북 안에서 주입된 env 만으로 홈랩 서비스 세 곳에 붙었다. `kfp.Client()` 를 **인자 없이** 불러 실험 4개와 최근 run 을 조회했고, MLflow 실험 2개와 RustFS 버킷 7개도 보였다.

![홈랩 Kubeflow 노트북 test-nb 의 JupyterLab 화면. ch07-poddefault-check.ipynb 의 첫 셀은 주입된 환경 변수를 출력한다: NB_PREFIX /notebook/kubeflow-user/test-nb, MLFLOW_TRACKING_URI http://mlflow.mlflow.svc.cluster.local:5000, KF_PIPELINES_ENDPOINT http://ml-pipeline.kubeflow.svc.cluster.local:8888, MLFLOW_S3_ENDPOINT_URL http://rustfs.mlflow.svc.cluster.local:9000, AWS_ACCESS_KEY_ID 설정됨. 둘째 셀은 kfp.Client() 를 인자 없이 만들어 실험 Default, smoke, income-classifier, ch07-data-passing 과 최근 run(hl-val-10k RUNNING, hl-a2-42, hl-a1, income-classifier-drift-homelab-1, income-classifier-homelab SUCCEEDED)을 보여 준다. 셋째 셀은 MLflow 실험 income-classifier, Default 와 RustFS 버킷 목록을 출력한다](homelab-notebook-poddefault.jpg)

| 사용 메모 | 내용 |
|---|---|
| 노트북 추가 | `notebook.yaml` 을 복사해 이름, 이미지, 리소스, PVC 만 바꾼다 |
| PodDefault 변경 | 주입은 Pod 생성 시점에만 일어나므로 바꾼 뒤 Pod 를 다시 만든다 |
| 패키지 | 이미지에 kfp, mlflow 가 없다. `pip install` 은 `/opt/conda` 에 깔려 **Pod 를 다시 만들면 사라진다**. 남기려면 `pip install --user`(홈 디렉터리 = PVC)나 커스텀 이미지를 쓴다 |
| 정리 | `kubectl -n kubeflow-user delete notebook test-nb`. PVC 는 남는다 |

## 5. 7.2 KFP 데이터 전달

### 5.1 왜 따로 배워야 하나

KFP 의 컴포넌트는 각각 **별도의 Kubernetes Pod** 에서 돈다. 메모리를 공유하지 않으니 앞 컴포넌트의 결과를 뒤로 넘길 장치가 따로 있어야 한다. 처음 쓰는 사람도, 오래 쓴 사람도 자주 헷갈리는 부분이다.

| 넘기는 것 | 방식 | 저장되는 곳 |
|---|---|---|
| 작은 값 (str, int 등) | 함수 반환값과 `.output` | 파라미터로 MLMD 와 Pod 명령 인자에 들어간다 |
| 큰 데이터 (파일, 디렉터리) | `Output[Artifact]` / `Input[Artifact]` 의 `.path` | 객체 스토리지 (책은 MinIO, 홈랩은 RustFS 의 `mlpipeline` 버킷) |
| 메트릭 (`Metrics`, `ClassificationMetrics`) | 아티팩트 타입 | 파일 없이 MLMD(MySQL `metadb`)에만 |

### 5.2 시나리오 1: 단순 값 전달

농담을 만들고(`generate_joke`), 단어를 세고(`count_words`), 결과를 출력하는(`output_result`) 함수 세 개를 컴포넌트로 만든다. 함수의 `import` 는 반드시 **함수 안에** 쓴다. 함수 본문만 컨테이너로 옮겨지기 때문에 바깥의 import 는 따라가지 않는다.

책 리스팅 7.5 는 그대로 돌리면 실패한다. `output_result = output_result(...)` 가 함수 이름을 같은 이름의 변수로 덮고, 앞에서 `count_word` 로 받은 결과를 뒤에서 `count_word_op` 로 부른다. 아래는 이름을 고친 버전이다.

```python {title="a1_values_pipeline.py (Listing 7.4 ~ 7.5 수정본)"}
import kfp.dsl as dsl

@dsl.component(packages_to_install=["pyjokes"], base_image="python:3.11")
def generate_joke() -> str:
    import pyjokes                    # import 는 함수 안에서
    return pyjokes.get_joke()

@dsl.component
def count_words(input: str) -> int:
    return len(input.split())

@dsl.component
def output_result(count: int) -> str:
    return f"Word count: {count}"

@dsl.pipeline(name="joke-pipeline-values", description="simple pipeline demonstrating value passing")
def pipeline():
    generate_joke_op = generate_joke()
    count_word_op = count_words(input=generate_joke_op.output)     # 반환값을 다음 컴포넌트로
    output_result_op = output_result(count=count_word_op.output)

if __name__ == "__main__":
    from kfp import compiler
    compiler.Compiler().compile(pipeline_func=pipeline, package_path="a1_values_pipeline.yaml")
```

컴포넌트에 표준 라이브러리 밖의 패키지가 필요하면 세 방법 중 하나를 쓴다.

| 방법 | 설명 |
|---|---|
| `base_image` | 패키지가 깔린 이미지를 지정한다. 경량 컴포넌트는 Python 3.5 이상이 있으면 된다 |
| `packages_to_install` | 실행 시 pip 로 설치한다. requirements.txt 와 비슷하다. 위 예제의 pyjokes 가 이 방식이다 |
| 함수 안에서 직접 설치 | `subprocess` 로 `pip install` 을 부른다. 의존성이 드러나지 않아 권하지 않는다 |

### 5.3 컴파일된 YAML 안에서 일어나는 일

컴파일된 YAML 의 `deploymentSpec.executors` 에 컴포넌트마다 실행자가 하나씩 생긴다. `exec-count-words` 의 `container.command` 를 보면 KFP 가 **코드 인젝션**으로 함수를 Pod 에 옮기는 과정이 그대로 보인다.

```yaml {title="Listing 7.6 exec-count-words (요약)"}
exec-count-words:
  container:
    args: [--executor_input, '{{$}}', --function_to_execute, count_words]
    command:
      - sh
      - -c
      - |                                        # ① pip 확인 후 kfp 설치
        if ! [ -x "$(command -v pip)" ]; then python3 -m ensurepip || ...; fi
        PIP_DISABLE_PIP_VERSION_CHECK=1 python3 -m pip install --quiet \
          --no-warn-script-location 'kfp==2.17.3' '--no-deps' \
          'typing-extensions>=3.7.4,<5; python_version<"3.9"' && "$0" "$@"
      - sh
      - -ec
      - |                                        # ② 임시 파일로 쓰고 실행자로 실행
        program_path=$(mktemp -d)
        printf "%s" "$0" > "$program_path/ephemeral_component.py"
        _KFP_RUNTIME=true python3 -m kfp.dsl.executor_main \
          --component_module_path "$program_path/ephemeral_component.py" "$@"
      - |                                        # ③ 주입된 함수 코드
        import kfp
        from kfp import dsl
        from kfp.dsl import *
        from typing import *

        def count_words(input: str) -> int:
            return len(input.split())
    image: python:3.11
```

| 블록 | 하는 일 |
|---|---|
| ① 첫 command | pip 가 있는지 보고 kfp 와 typing-extensions 를 조용히 설치한다. `packages_to_install` 이 있으면 그 패키지를 먼저 설치하는 pip install 이 앞에 붙는다 |
| ② 둘째 command | 임시 디렉터리에 함수 코드를 `ephemeral_component.py` 로 쓰고 `kfp.dsl.executor_main` 이 실행한다 |
| ③ 마지막 인자 | 데코레이터를 뗀 함수 본문. 타입 힌트(`str` → `int`)를 보고 KFP 가 직렬화를 맡는다 |

YAML 의 세 부분은 역할이 나뉜다. `components.comp-count-words` 는 입출력 타입을 선언하는 **인터페이스**, `deploymentSpec` 은 **런타임 환경과 구현**, `root.dag.tasks.count-words` 는 `taskOutputParameter` 로 `generate-joke` 의 출력을 받는 **DAG 연결과 캐시 설정**이다. `count_words` 를 빼고 남는 코드가 KFP 가 넣은 코드라고 보면 된다.

홈랩 SDK 2.17.3 은 `base_image` 를 주지 않은 컴포넌트에 `python:3.11` 을 쓴다. 책 출력(SDK 2.11.0)은 `python:3.9` 였고, 컴파일할 때 "2027년 10월 1일부터 기본값이 `python:3.12` 로 바뀐다"는 경고가 나온다. 기본값에 기대지 말고 `base_image` 를 적는 편이 안전하다.

### 5.4 홈랩 실습 결과

홈랩 KFP 2.17.3(SDK 2.17.3, 아티팩트는 RustFS `mlpipeline` 버킷)에서 실험 `ch07-data-passing` 으로 캐시를 끄고 run 16개를 돌렸다. 코드는 [MLOps-study `k8s/kubeflow-pipelines/07-data-passing/`](https://github.com/ken-0913/MLOps-study/tree/main/k8s/kubeflow-pipelines/07-data-passing) 에 있다. A2 이후는 7.2.2 ~ 7.2.3 의 내용으로, 다음 글에서 자세히 다룬다.

| 단계 | 실험 | 결과 | 관찰 |
|---|---|---|---|
| A1 | 값 전달 (리스팅 7.5 수정본) | 성공 80초 | 농담 15단어 → `Word count: 15` |
| A2 | 경로 전달, num_jokes=42 / 5 | 성공 70초 | 606 / 60단어. 디렉터리 아티팩트가 `output_jokes/jokes.txt` 키로 저장된다 |
| A2b | 값 전달 10KB, 60KB, **100KB** | 성공 약 50초 | 스터디 공용 환경(KFP 2.4.1)은 100KB 에서 `argument list too long` 으로 실패했다 |
| A2b | 값 전달 250KB, 500KB, 1MB | **실패** | 받는 쪽 executor 에서 `configmaps is forbidden` |
| A2b | 값 전달 10MB | **실패** | 받는 쪽 driver 에서 `Request entity too large: limit is 3145728` |
| A2b | 경로 전달 10MB, 200MB | 성공 60초 | 200MB 도 문제없다 |
| A3 | 책 코드 그대로 (`np.save`) | **실패** | 만드는 쪽은 성공, 받는 쪽이 `FileNotFoundError` |
| A3 | 수정본 (파일 핸들로 저장) | 성공 61초 | `shape=(100, 4)`, metadata `samples`, `shape` 전달 |
| A4 | 아티팩트 타입 7종 | 성공 80초 | accuracy 0.9561, f1 0.9655. MLMD 에 `system.*` 7종 등록 |

#### 값 전달은 어디서 깨지나

값은 받는 쪽 Pod 의 **명령 인자**(`--executor_input`)에 그대로 들어간다. A1 의 driver 로그에서 앞 태스크의 농담 문장이 `parameterValues` 안에 들어간 Pod 스펙이 보인다.

```json {title="count-words driver 가 만든 Pod 스펙 (일부)"}
{"command": ["/kfp-launcher/launch", "--pipeline_name", "joke-pipeline-values",
  "--executor_input", "{\"inputs\":{\"parameterValues\":{\"input\":\"There are II types of people: Those who understand Roman Numerals and those who don't.\"}}, ...}"]}
```

홈랩에서 깨진 지점은 두 곳이다. 250KB 부터는 Argo 컨트롤러가 받는 쪽 executor 를 만들면서 `kubeflow` 네임스페이스에 ConfigMap 을 만들려다 권한이 없어 멈췄다. 홈랩은 KFP 번들 Argo 대신 기존 Argo Workflows v4.1.4 를 공유하는데(ADR-013), 그 컨트롤러 ServiceAccount 에 이 권한이 없다.

```bash
kubectl -n argo logs deploy/argo-workflows-workflow-controller | grep forbidden
# task '...root.use-value.executor' errored: configmaps is forbidden:
#   User "system:serviceaccount:argo:argo-workflows-workflow-controller"
#   cannot create resource "configmaps" in API group "" in the namespace "kubeflow"
```

10MB 는 그보다 앞, 받는 쪽 driver 단계에서 API 서버의 요청 크기 한도(3MiB)에 걸렸다. 권한을 열어 줘도 이 한도는 남는다. 숫자는 환경마다 다르지만 결론은 같다: **값 전달은 수백 KB 안쪽에서 끝나고, 경로 전달은 200MB 도 통과한다.**

#### A3: v1 습관을 v2 에 옮기면

v1 예제처럼 `np.save(out.path, arr)` 를 쓰면 NumPy 가 경로 끝에 `.npy` 를 붙인다. KFP 가 옮기는 것은 `out.path` 이므로 받는 쪽에서 파일이 없다.

```python {title="a3_v1_to_v2.py (핵심)"}
@dsl.component(base_image="python:3.11", packages_to_install=["numpy"])
def make_data_asis(n: int, out: Output[Dataset]):
    import numpy as np
    np.save(out.path, np.random.rand(n, 4))          # 실제 파일은 out.path + ".npy"

@dsl.component(base_image="python:3.11", packages_to_install=["numpy"])
def make_data_fixed(n: int, out: Output[Dataset]):
    import numpy as np
    arr = np.random.rand(n, 4)
    with open(out.path, "wb") as f:                  # 파일 핸들이면 이름이 그대로다
        np.save(f, arr)
    out.metadata["samples"] = n                      # 작은 정보는 아티팩트 metadata 로
    out.metadata["shape"] = list(arr.shape)
```

```bash
# as-is: 만드는 쪽 로그
[ch07] np.save(/minio/mlpipeline/v2/artifacts/v1-to-v2-asis/.../out) exists=False npy=True
# as-is: 받는 쪽 로그
FileNotFoundError: [Errno 2] No such file or directory: '/minio/mlpipeline/v2/artifacts/v1-to-v2-asis/.../out'
# fixed: 받는 쪽 로그
[ch07] shape=(100, 4) metadata={'display_name': 'out', 'samples': 100, 'shape': {'list': [100, 4]}, ...}
```

KFP 2.17 은 업로드할 파일이 없어도 만드는 쪽 태스크를 **성공으로 끝낸다**. 실패는 받는 쪽에서야 드러나므로, 원인을 찾으려면 앞 태스크 로그까지 거슬러 올라가야 한다. metadata 의 리스트는 MLMD 구조체를 거치며 `{'list': [...]}` 로 감싸져 돌아온다.

#### 아티팩트가 실제로 저장되는 곳

아티팩트 경로는 `/minio/mlpipeline/v2/artifacts/<파이프라인>/<run_id>/<태스크>/<실행 UUID>/<이름>` 꼴이다. 이름은 `/minio` 지만 이 로컬 경로를 런처가 만들고, 실제 파일은 RustFS `mlpipeline` 버킷의 같은 키로 올라간다. 노트북에서 boto3 로 버킷을 조회했다.

| run | 키 (`<태스크>/<uuid>/` 아래) | 크기 |
|---|---|---|
| A2 (42개) | `generate-joke/…/output_jokes/jokes.txt` | 3,400 B |
| A2b 경로 200MB | `make-file/…/out` | 204,800,000 B |
| A4 | `train/…/dataset`, `model`, `report_html`, `report_md`, `raw` | 121,385 / 1,588 / 69 / 85 / 27 B |
| A4 | `train/…/metrics`, `cls_metrics` | **없음** |
| 모든 태스크 | `…/executor-logs-0` | 약 2 ~ 6KB |

`Metrics` 와 `ClassificationMetrics` 는 파일이 없고 **MLMD(MySQL `metadb`)에만** 저장된다. KFP UI 도 `cls_metrics` 의 URI 옆에 "This is an empty file by default" 라고 표시한다. 2.17 에서 새로 보이는 것은 태스크마다 붙는 `executor-logs` 아티팩트로, 런처의 `--publish_logs true` 가 실행 로그를 객체 스토리지에 올린다.

```bash
kubectl -n kubeflow exec deploy/mysql -- mysql -uroot -N -e \
  'select t.name, substring_index(a.uri,"/",-1) from metadb.Artifact a
   join metadb.Type t on t.id=a.type_id where a.uri like "%56263271%"'
# system.Artifact               raw
# system.ClassificationMetrics  cls_metrics
# system.Dataset                dataset
# system.HTML                   report_html
# system.Markdown               report_md
# system.Metrics                metrics
# system.Model                  model
```

![홈랩 KFP UI 2.17.3 에서 run hl-a4 의 그래프 화면. train 태스크에서 cls_metrics, dataset, metrics, model, raw, report_html, report_md 아티팩트 노드가 나오고 dataset 과 model 이 evaluate 태스크로 이어진다. 오른쪽 패널은 cls_metrics 아티팩트의 Visualization 탭으로, ROC Curve: cls_metrics 그래프가 fpr 0 근처에서 tpr 이 0.97 이상으로 바로 올라가는 곡선을 보여 준다](homelab-kfp-a4-roc.jpg)

<details class="orca-details">
<summary>a2b_large_value.py: 같은 크기를 값과 경로로 넘겨 비교</summary>

```python
from kfp import dsl
from kfp.dsl import Artifact, Input, Output

@dsl.component(base_image="python:3.11")
def make_value(size_kb: int) -> str:
    return "x" * (size_kb * 1024)

@dsl.component(base_image="python:3.11")
def use_value(s: str) -> int:
    return len(s)

@dsl.component(base_image="python:3.11")
def make_file(size_kb: int, out: Output[Artifact]):
    with open(out.path, "w") as f:
        f.write("x" * (size_kb * 1024))

@dsl.component(base_image="python:3.11")
def use_file(inp: Input[Artifact]) -> int:
    import os
    return os.path.getsize(inp.path)

@dsl.pipeline(name="large-value-by-value")
def by_value(size_kb: int = 100):
    use_value(s=make_value(size_kb=size_kb).output)

@dsl.pipeline(name="large-value-by-artifact")
def by_artifact(size_kb: int = 100):
    use_file(inp=make_file(size_kb=size_kb).outputs["out"])
```

</details>

<details class="orca-details">
<summary>a4_artifact_types.py: 아티팩트 타입 7종</summary>

```python
from kfp import dsl
from kfp.dsl import HTML, Artifact, ClassificationMetrics, Dataset, Input, Markdown, Metrics, Model, Output

@dsl.component(base_image="python:3.11", packages_to_install=["scikit-learn==1.5.2", "pandas"])
def train(dataset: Output[Dataset], model: Output[Model], metrics: Output[Metrics],
          cls_metrics: Output[ClassificationMetrics], report_html: Output[HTML],
          report_md: Output[Markdown], raw: Output[Artifact]):
    import json, pickle
    from sklearn.datasets import load_breast_cancer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, roc_curve
    from sklearn.model_selection import train_test_split

    data = load_breast_cancer(as_frame=True)
    data.frame.to_csv(dataset.path, index=False)
    dataset.metadata.update({"rows": len(data.frame), "cols": data.frame.shape[1]})

    X_tr, X_te, y_tr, y_te = train_test_split(data.data, data.target, test_size=0.2, random_state=42)
    clf = LogisticRegression(max_iter=5000).fit(X_tr, y_tr)
    with open(model.path, "wb") as f:
        pickle.dump(clf, f)

    pred = clf.predict(X_te)
    acc, f1 = accuracy_score(y_te, pred), f1_score(y_te, pred)
    metrics.log_metric("accuracy", round(float(acc), 4))           # MLMD 에만 저장
    metrics.log_metric("f1", round(float(f1), 4))
    cls_metrics.log_confusion_matrix(["malignant", "benign"], confusion_matrix(y_te, pred).tolist())
    fpr, tpr, thr = roc_curve(y_te, clf.predict_proba(X_te)[:, 1])
    step = max(1, len(fpr) // 20)
    cls_metrics.log_roc_curve(fpr[::step].tolist(), tpr[::step].tolist(),
                              [min(float(t), 1.0) for t in thr][::step])

    with open(report_html.path, "w") as f:
        f.write(f"<h2>breast_cancer</h2><p>accuracy <b>{acc:.4f}</b>, f1 <b>{f1:.4f}</b></p>")
    with open(report_md.path, "w") as f:
        f.write(f"| metric | value |\n|---|---|\n| accuracy | {acc:.4f} |\n| f1 | {f1:.4f} |\n")
    with open(raw.path, "w") as f:
        json.dump({"train": len(X_tr), "test": len(X_te)}, f)

@dsl.component(base_image="python:3.11", packages_to_install=["scikit-learn==1.5.2", "pandas"])
def evaluate(dataset: Input[Dataset], model: Input[Model]) -> float:
    import pickle
    import pandas as pd
    df = pd.read_csv(dataset.path)
    with open(model.path, "rb") as f:
        clf = pickle.load(f)
    return float((clf.predict(df.drop(columns="target")) == df["target"]).mean())

@dsl.pipeline(name="artifact-types")
def pipeline():
    t = train()
    evaluate(dataset=t.outputs["dataset"], model=t.outputs["model"])
```

</details>

실행은 컴파일한 YAML 을 `create_run_from_pipeline_package` 로 제출하고 끝날 때까지 기다린 뒤, 태스크 상태와 실행 Pod 의 `[ch07]` 로그를 모으는 `submit.py` 로 했다. driver Pod 로그에는 주입된 함수 코드와 Pod 스펙이 통째로 찍히므로 실행(impl) Pod 의 줄만 골랐다.

```bash
export KFP_HOST=http://192.168.0.242
python a1_values_pipeline.py && python submit.py a1_values_pipeline.yaml hl-a1
python submit.py a2_artifact_pipeline.yaml hl-a2-42 num_jokes=42
python submit.py a2b_by_value.yaml hl-val-100k size_kb=100        # 성공
python submit.py a2b_by_value.yaml hl-val-250k size_kb=250        # 실패 (configmaps is forbidden)
python submit.py a2b_by_artifact.yaml hl-art-200000k size_kb=200000   # 200MB 성공
python submit.py a3_asis.yaml hl-a3-asis                          # 실패 재현
python submit.py a4_artifact_types.yaml hl-a4
```

## 6. 정리

| 질문 | 답 |
|---|---|
| 노트북을 왜 클러스터에 띄우나 | 데이터 가까이에서, 비싼 자원을 필요할 때만, 배포와 같은 이미지로 실험하기 위해서다 |
| PodDefault 는 무엇을 하나 | 라벨이 맞는 Pod 가 생길 때 env, 볼륨, Secret 을 넣는다. 라벨 붙은 네임스페이스에서만 동작한다 |
| 노트북 메뉴는 어디서 바꾸나 | `jupyter-web-app-config` ConfigMap. 이미지 목록과 어피니티 선택지를 둔다 |
| 컴포넌트 함수는 어떻게 Pod 로 가나 | 컴파일러가 함수 본문을 YAML 에 넣고, Pod 가 임시 파일로 써서 실행자로 돌린다 |
| 값과 경로는 언제 쓰나 | 작은 값만 반환값으로. 홈랩은 250KB, 공용 환경은 100KB 에서 깨졌고 경로는 200MB 도 통과했다 |

다음 글에서는 7.2.2 ~ 7.2.3 의 경로 전달, v1 에서 v2 로 바뀐 점, 아티팩트 타입을 정리하고 7.3절 캡스톤 데이터 준비 파이프라인으로 넘어간다.
