---
title: "MLPE 스터디 2주차 - Ch4. Kubernetes에 MLflow 설치하기 (RustFS + Postgres + JupyterLab)"
date: 2026-10-24T20:00:00+09:00
draft: false
tags: ["MLOps", "MLPE", "MLflow", "Kubernetes", "Helm", "RustFS", "PostgreSQL", "JupyterLab", "Model Registry", "Experiment Tracking"]
categories: ["MLOps"]
series: ["MLPE 2주차"]
featuredImage: images/banners/mlpe-04-mlflow-install-01f7e9a6.png
---
`Machine Learning Platform Engineering` 4장은 MLflow로 실험을 추적하고 모델을 레지스트리에 등록한다. 책은 로컬에서 띄운 `mlflow ui`(SQLite)와 Kubeflow에 딸린 MinIO로 진행하는데, 로컬 인스턴스로는 팀이 같은 실험 기록을 볼 수 없다. 그래서 4장의 도전과제가 "Kubernetes에 MLflow를 설치하라"다.

이 글은 홈랩 Kubernetes 클러스터(v1.36.5, 노드 3대)의 `mlflow` 네임스페이스에 MLflow 추적 서버를 올린 기록이다. 매니페스트와 스크립트는 홈랩 저장소 `~/k8s/mlflow/`에 있고, 결정 배경은 ADR-045에 남겼다.

| 구성요소 | 버전 | 어디에 | 역할 |
| --- | --- | --- | --- |
| **RustFS** | 1.0.3 | worker2-arm64, PV 20Gi | S3 호환 객체 스토리지. 버킷 `mlflow-artifacts`, `mlflow-datasets` |
| **Postgres** | 18.6 | worker1-gpu, PV 5Gi | MLflow 백엔드 스토어(run, 지표, 레지스트리 메타데이터) |
| **MLflow server** | 3.16.0 (community-charts/mlflow 1.11.7) | 노드 무관 | 추적 서버 + 모델 레지스트리 + UI |
| **JupyterLab** | scipy-notebook python-3.13.17 | worker1-gpu, 홈 PV 20Gi | 책 노트북을 클러스터 안에서 실행 |

책과 다른 점은 네 가지다. MinIO 대신 RustFS, SQLite 대신 Postgres, 로컬 노트북 대신 클러스터 안 JupyterLab, 그리고 책의 고정 버전(mlflow 3.0.0, xgboost 1.7.6) 대신 최신 버전을 쓴다. S3 호환이면 책의 minio SDK와 boto3 코드가 그대로 돌고, Python 3.13에는 옛 고정 버전의 휠이 없다.

## 1. 구성

![홈 LAN 안의 홈랩 클러스터 mlflow 네임스페이스에 JupyterLab, MLflow server 3.16.0, Postgres 18.6, RustFS 1.0.3 을 올린 구성. 노트북은 MLflow 서버에 run·파라미터·지표를 REST 로 기록하고 아티팩트와 데이터셋 CSV 는 RustFS 에 S3 로 직접 올린다. MLflow 서버는 Postgres 를 백엔드 스토어로 쓰고 default-artifact-root 로 RustFS 버킷을 가리킨다. 세 서비스는 Cilium LB IPAM 으로 192.168.0.237~239 에 노출되고 monitoring 네임스페이스의 Prometheus 가 ServiceMonitor 로 /metrics 를 긁는다](homelab-mlflow.svg)

핵심은 **아티팩트가 MLflow 서버를 거치지 않는다**는 점이다. 노트북이 `log_artifacts()`나 `log_model()`을 부르면 run과 지표 같은 메타데이터만 MLflow 서버(Postgres)로 가고, 파일은 노트북 Pod가 RustFS에 직접 올린다. 책의 MinIO 구성과 같은 비프록시 방식이다.

그래서 Jupyter Pod에는 MLflow 주소뿐 아니라 `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `MLFLOW_S3_ENDPOINT_URL`이 환경변수로 들어가 있다. MLflow 서버의 `--default-artifact-root`는 run을 만들 때 artifact URI를 기록하고 UI에서 아티팩트를 읽을 때만 쓴다.

![4.1절 노트북이 MLflow 서버, Postgres, RustFS 와 주고받는 12단계. 실험과 run 생성, log_input·log_metric·log_params, logged model 생성, register_model 같은 메타데이터는 MLflow 서버를 거쳐 Postgres 에 쌓이고(회색), 데이터셋 CSV, EDA 그림, MLmodel·model.skops 는 노트북 Pod 가 RustFS 에 S3 로 직접 올린다(주황). log_model 은 run 아티팩트가 아니라 chapter-4/(exp)/models/m-… 에 저장되고, register_model(runs:/…/income-classifier) 은 그 logged model 을 source 로 버전을 만든다](homelab-mlflow-seq.svg)

노드 배치에는 이유가 있다. RustFS 데이터는 worker1-gpu의 디스크 부담을 덜려고 worker2-arm64(Raspberry Pi)에 뒀다.

Postgres도 거기 두려 했지만 worker2의 메모리 요청이 98%(keycloak 2대 3.4Gi, istiod 2Gi)라 256Mi 요청도 스케줄되지 않아 worker1-gpu로 옮겼다. Jupyter는 xgboost 휠이 amd64용이라 worker1-gpu에만 올라간다.

## 2. 설치 순서

설치는 `scripts/install.sh` 하나로 한다. 멱등이라 다시 실행하면 바뀐 것만 적용되고, 비밀값은 처음 한 번 무작위로 만들어 Secret에만 저장한다. 매니페스트와 Helm values에는 `secretKeyRef`와 `existingSecret` 참조만 둔다.

```bash {title="scripts/install.sh (요지)"}
NS=mlflow
CHART_VERSION=${CHART_VERSION:-1.11.7}

rand() { python3 -c "import secrets;print(secrets.token_hex($1))"; }
ensure_secret() {  # name key=value ...  (이미 있으면 건드리지 않는다)
  local name=$1; shift
  if kubectl -n $NS get secret "$name" >/dev/null 2>&1; then echo "secret $name: 있음 (유지)"; return; fi
  local args=(); for kv in "$@"; do args+=(--from-literal="$kv"); done
  kubectl -n $NS create secret generic "$name" "${args[@]}" >/dev/null && echo "secret $name: 생성"
}

# 1. 네임스페이스와 Secret
kubectl get ns $NS >/dev/null 2>&1 || kubectl create ns $NS
ensure_secret rustfs-credentials "AWS_ACCESS_KEY_ID=mlflow$(rand 4)" "AWS_SECRET_ACCESS_KEY=$(rand 20)"
ensure_secret mlflow-postgres "username=mlflow" "password=$(rand 16)" "database=mlflow"
ensure_secret jupyter-token "token=$(rand 24)"

# 2. RustFS 와 버킷
kubectl apply -f 00-rustfs/rustfs.yaml
kubectl -n $NS rollout status deploy/rustfs --timeout=5m
kubectl apply -f 00-rustfs/buckets-job.yaml
kubectl -n $NS wait --for=condition=complete job/rustfs-make-buckets --timeout=5m

# 3. Postgres
kubectl apply -f 01-postgres/postgres.yaml
kubectl -n $NS rollout status deploy/mlflow-postgres --timeout=5m

# 4. MLflow (Helm)
helm repo add community-charts https://community-charts.github.io/helm-charts
helm upgrade --install mlflow community-charts/mlflow --version "$CHART_VERSION" -n $NS \
  -f 02-mlflow/values.yaml --wait --timeout 10m

# 5. JupyterLab
kubectl apply -f 03-jupyter/jupyter.yaml
kubectl -n $NS rollout status deploy/jupyter --timeout=15m
```

| Secret | 키 | 쓰는 곳 |
| --- | --- | --- |
| `rustfs-credentials` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | RustFS 루트 계정, MLflow 서버, Jupyter, 버킷 Job |
| `mlflow-postgres` | `username`, `password`, `database` | Postgres, MLflow 서버 |
| `jupyter-token` | `token` | JupyterLab 로그인 |

## 3. 매니페스트 요점

**RustFS**는 Deployment 하나와 Service 둘이다. PV가 RWO라 롤링 업데이트가 교착되므로 `Recreate` 전략을 쓰고, 계정은 Secret에서만 읽는다. 클러스터 안에서는 `rustfs.mlflow.svc:9000`, LAN에서는 Cilium LB IPAM이 고정해 준 192.168.0.237로 접근한다.

```yaml {title="00-rustfs/rustfs.yaml (요지)"}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rustfs
  namespace: mlflow
spec:
  replicas: 1
  strategy:
    type: Recreate   # PV 가 RWO 라 롤링은 교착된다
  template:
    spec:
      nodeSelector:
        kubernetes.io/hostname: worker2-arm64
      containers:
        - name: rustfs
          image: rustfs/rustfs:1.0.3
          env:
            - name: RUSTFS_ADDRESS
              value: ":9000"
            - name: RUSTFS_CONSOLE_ADDRESS
              value: ":9001"
            - name: RUSTFS_VOLUMES
              value: /data
            - name: RUSTFS_ACCESS_KEY
              valueFrom:
                secretKeyRef: { name: rustfs-credentials, key: AWS_ACCESS_KEY_ID }
            - name: RUSTFS_SECRET_KEY
              valueFrom:
                secretKeyRef: { name: rustfs-credentials, key: AWS_SECRET_ACCESS_KEY }
          volumeMounts:
            - name: data
              mountPath: /data
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: rustfs-data
---
apiVersion: v1
kind: Service
metadata:
  name: rustfs-lb
  namespace: mlflow
  annotations:
    lbipam.cilium.io/ips: "192.168.0.237"
spec:
  type: LoadBalancer
  selector:
    app: rustfs
  ports:
    - { name: s3, port: 9000 }
    - { name: console, port: 9001 }
```

버킷은 aws-cli 이미지로 도는 Job이 만든다. `head-bucket`으로 있는지 먼저 보고 없을 때만 만들기 때문에 install.sh를 다시 돌려도 안전하다. 4.2절 Feast용 버킷(`feature-data-sets`, `feature-registry`)은 [Feast 글](../mlpe-04-mlflow-feast/)의 설치 Job이 같은 방식으로 따로 만든다.

```yaml {title="00-rustfs/buckets-job.yaml (요지)"}
apiVersion: batch/v1
kind: Job
metadata:
  name: rustfs-make-buckets
  namespace: mlflow
spec:
  ttlSecondsAfterFinished: 3600
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: aws
          image: amazon/aws-cli:2.38.5
          envFrom:
            - secretRef:
                name: rustfs-credentials
          env:
            - { name: AWS_DEFAULT_REGION, value: us-east-1 }
            - { name: AWS_ENDPOINT_URL, value: http://rustfs:9000 }
            - { name: BUCKETS, value: "mlflow-artifacts mlflow-datasets" }
          command: ["/bin/sh", "-c"]
          args:
            - |
              set -eu
              for b in $BUCKETS; do
                aws s3api head-bucket --bucket "$b" 2>/dev/null && echo "exists: $b" \
                  || { aws s3api create-bucket --bucket "$b" && echo "created: $b"; }
              done
```

**MLflow**는 community-charts의 Helm 차트로 올린다. 공식 이미지에는 psycopg2와 boto3가 없어 Postgres와 S3를 쓰려면 직접 빌드해야 하는데, 이 차트의 이미지(`burakince/mlflow`)는 둘을 포함하고 `existingSecret`도 지원한다. values 파일에 비밀값이 한 줄도 들어가지 않는 이유다.

```yaml {title="02-mlflow/values.yaml"}
image:
  repository: burakince/mlflow
  tag: "3.16.0"              # 릴리스 최신은 3.17.2 지만 이미지가 아직 없다

backendStore:
  databaseMigration: true          # init 컨테이너가 mlflow db upgrade 를 먼저 실행
  databaseConnectionCheck: true    # Postgres 가 뜰 때까지 기다리는 init 컨테이너
  postgres:
    enabled: true
    host: mlflow-postgres
    port: 5432
    database: mlflow
  existingDatabaseSecret:
    name: mlflow-postgres
    usernameKey: username
    passwordKey: password

artifactRoot:
  proxiedArtifactStorage: false    # 책과 같이 클라이언트가 S3 에 직접 쓴다
  s3:
    enabled: true
    bucket: mlflow-artifacts
    path: chapter-4
    existingSecret:
      name: rustfs-credentials
      keyOfAccessKeyId: AWS_ACCESS_KEY_ID
      keyOfSecretAccessKey: AWS_SECRET_ACCESS_KEY

extraEnvVars:
  MLFLOW_S3_ENDPOINT_URL: http://rustfs:9000
  AWS_DEFAULT_REGION: us-east-1

service:
  type: LoadBalancer
  port: 5000
  annotations:
    lbipam.cilium.io/ips: "192.168.0.238"

serviceMonitor:
  enabled: true                    # 켜면 차트가 --expose-prometheus=/mlflow/metrics 를 붙인다
  namespace: mlflow
  labels:
    release: kube-prometheus-stack

# 루트 파일시스템이 읽기 전용이라 /mlflow/metrics 를 못 만들어 기동이 실패한다. emptyDir 을 붙여 준다.
extraVolumes:
  - name: metrics
    emptyDir: {}
extraVolumeMounts:
  - name: metrics
    mountPath: /mlflow/metrics

# uvicorn 워커 4개가 각각 MLflow 를 로드해 2Gi 를 넘겨 OOMKilled 됐다. 워커 2개로 줄이고 제한을 올린다.
extraArgs:
  workers: "2"
  # MLflow 3.x 보안 미들웨어가 Host 헤더를 검사한다. 기본 허용은 localhost 와 사설 IP 패턴뿐이라
  # 클러스터 안 이름(mlflow:5000)은 403 이 났다. 포트까지 정확 일치라 ":*" 를 붙인다.
  allowedHosts: "localhost:*,127.0.0.1:*,mlflow:*,mlflow.mlflow:*,mlflow.mlflow.svc:*,mlflow.mlflow.svc.cluster.local:*,192.168.*,10.*"
  # 같은 미들웨어의 CORS 검사. 브라우저 UI 가 LAN IP 로 접속하면 POST /ajax-api 에 Origin 헤더가 붙는데
  # 기본 허용 origin 이 localhost 뿐이라 Runs 탭이 403 Request error 가 났다. 화면 origin 을 그대로 적는다.
  corsAllowedOrigins: "http://192.168.0.238:5000,http://mlflow:5000,http://mlflow.mlflow.svc:5000"
resources:
  requests:
    cpu: 100m
    memory: 512Mi   # worker1-gpu 요청량이 꽉 차 있어 요청은 최소로, 제한은 넉넉히
  limits:
    memory: 4Gi
```

이 values로 만들어진 Pod의 실제 명령은 다음과 같다. init 컨테이너 둘이 Postgres 연결 확인과 스키마 마이그레이션을 먼저 하고, 본 컨테이너가 서버를 띄운다.

```terminal {title="kubectl -n mlflow get pod -l app.kubernetes.io/name=mlflow -o jsonpath=..."}
init: dbchecker            /script/dbchecker.sh
init: mlflow-db-migration  python /opt/mlflow/migrations.py
main: burakince/mlflow:3.16.0
  mlflow server --host=0.0.0.0 --port=5000
    --backend-store-uri=postgresql://
    --default-artifact-root=s3://mlflow-artifacts/chapter-4
    --expose-prometheus=/mlflow/metrics
    --allowed-hosts=localhost:*,127.0.0.1:*,mlflow:*,mlflow.mlflow:*,mlflow.mlflow.svc:*,...,192.168.*,10.*
    --workers=2
```

**JupyterLab**은 `scipy-notebook` 이미지에 ConfigMap으로 시작 hook 하나를 꽂았다. docker-stacks의 `start.sh`가 노트북 서버를 띄우기 직전에 `/usr/local/bin/before-notebook.d/*.sh`를 실행하는데, 이 hook이 chapter-4 저장소를 clone하고 venv에 최신 mlflow, xgboost, plotnine, minio를 설치해 `chapter-4` 커널로 등록한다. 홈 디렉터리가 PVC라 재시작해도 남는다.

```yaml {title="03-jupyter/jupyter.yaml (요지)"}
apiVersion: v1
kind: ConfigMap
metadata:
  name: jupyter-hooks
  namespace: mlflow
data:
  10-chapter4.sh: |
    #!/bin/bash
    # start.sh 가 이 파일을 source 하므로 set -e/-u 나 exit 를 쓰면 노트북 서버까지 죽는다
    REPO_DIR="$HOME/practical-mlops/chapter-4"
    VENV="$HOME/.venvs/chapter-4"
    if [ ! -d "$REPO_DIR/.git" ]; then
      git clone --depth 1 https://github.com/practical-mlops/chapter-4.git "$REPO_DIR"
    fi
    if [ ! -f "$VENV/.ready" ]; then
      python -m venv --system-site-packages "$VENV" \
        && "$VENV/bin/pip" install --quiet ${CHAPTER4_PACKAGES} \
        && "$VENV/bin/python" -m ipykernel install --user --name chapter-4 --display-name "chapter-4 (latest)" \
        && touch "$VENV/.ready"
    fi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jupyter
  namespace: mlflow
spec:
  template:
    spec:
      nodeSelector:
        kubernetes.io/arch: amd64       # xgboost 휠. 유일한 amd64 워커는 worker1-gpu
      enableServiceLinks: false         # Service 이름이 jupyter 라 JUPYTER_PORT=tcp://... 가 주입돼 기동이 깨진다
      containers:
        - name: jupyter
          image: quay.io/jupyter/scipy-notebook:python-3.13.17
          env:
            - name: JUPYTER_TOKEN
              valueFrom:
                secretKeyRef: { name: jupyter-token, key: token }
            - { name: MLFLOW_TRACKING_URI, value: http://mlflow:5000 }
            - { name: MLFLOW_S3_ENDPOINT_URL, value: http://rustfs:9000 }
            - { name: AWS_ENDPOINT_URL, value: http://rustfs:9000 }
            - { name: AWS_DEFAULT_REGION, value: us-east-1 }
            - { name: MINIO_ENDPOINT, value: "rustfs:9000" }
            - { name: CHAPTER4_PACKAGES, value: "mlflow boto3 s3fs minio plotnine xgboost scikit-learn pandas matplotlib pyarrow ipykernel" }
          envFrom:
            - secretRef:
                name: rustfs-credentials       # AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
          resources:
            requests: { cpu: 100m, memory: 512Mi }   # worker1-gpu 요청량이 꽉 차 있어 최소로
            limits: { memory: 8Gi }
          volumeMounts:
            - { name: home, mountPath: /home/jovyan }
            - { name: hooks, mountPath: /usr/local/bin/before-notebook.d/10-chapter4.sh, subPath: 10-chapter4.sh }
```

## 4. 겪은 문제

- **MLflow Pod가 `OSError: Read-only file system: '/mlflow/metrics'`로 죽음.** `serviceMonitor.enabled`를 켜면 차트가 `--expose-prometheus=/mlflow/metrics`를 붙이는데 컨테이너 루트 파일시스템이 읽기 전용이다. `extraVolumes`로 emptyDir을 그 경로에 붙였다.
- **MLflow Pod가 기동 8초 만에 OOMKilled(exit 137).** uvicorn 워커 기본 4개가 각각 MLflow를 로드해 2Gi를 넘겼다. `extraArgs.workers: "2"`(문자열이어야 차트 스키마를 통과한다)와 limit 4Gi로 해결했다.
- **Postgres가 worker2-arm64에 스케줄되지 않음.** 노드 메모리 요청이 98%라 256Mi 요청도 못 들어갔다. worker1-gpu로 옮겼다.
- **`helm --wait` 도중 values를 고쳐 다시 올리면 `another operation is in progress`.** 기다리던 helm을 끊으면 릴리스가 failed로 남아 `upgrade --install`이 안 된다. `helm uninstall` 뒤 다시 설치해야 했다.
- **Jupyter가 worker1-gpu에 스케줄되지 않음.** 유일한 amd64 워커인데 CPU 요청 98%(vLLM 2대 4000m, rag embedding 1000m 등), 메모리 요청 99%(vLLM 2대 14Gi 등)였다. 실제 사용량은 21G/31G라 여유가 있지만 스케줄은 요청 기준이다. Jupyter 요청을 500m/2Gi에서 100m/512Mi로, MLflow 요청을 1Gi에서 512Mi로 낮췄고, MLflow는 RollingUpdate의 새 Pod가 자리를 못 잡아 `strategy: Recreate`로 바꿨다. 근본적으로는 worker1-gpu에 몰린 요청을 정리해야 한다.
- **Jupyter hook에서 `JUPYTER_DOCKER_STACKS_QUIET: unbound variable`.** docker-stacks의 start.sh는 hook을 `source`하므로 hook의 `set -u`가 부모 스크립트에 적용돼 노트북 서버까지 죽었다. hook에서는 `set -e/-u`와 `exit`를 쓰지 않는다.
- **Jupyter가 `ValueError: invalid literal for int(): 'tcp://10.97.194.103:8888'`로 죽음.** Service 이름이 `jupyter`라 Kubernetes가 `JUPYTER_PORT=tcp://<ClusterIP>:8888`을 환경변수로 주입하고 start-notebook.py가 그것을 포트 번호로 읽는다. `enableServiceLinks: false`로 막았다.
- **클러스터 안에서 MLflow API가 403 `Invalid Host header - possible DNS rebinding attack detected`.** MLflow 3.x 보안 미들웨어의 기본 허용 호스트는 localhost와 사설 IP 패턴(`192.168.*`, `10.*`)뿐이라 LAN IP는 되고 `mlflow:5000`은 안 됐다. 비교가 포트 포함 정확 일치(또는 `*` fnmatch)라 `extraArgs.allowedHosts`에 `mlflow:*,mlflow.mlflow.svc:*` 같은 패턴을 넣었다.
- **UI의 Runs 탭만 "Request error".** 같은 미들웨어의 CORS 검사다. 실험 목록(GET)은 보이는데 run 목록을 가져오는 `POST /ajax-api/2.0/mlflow/runs/search`가 403이고, 서버 로그에 `Blocked cross-origin request from http://192.168.0.238:5000`이 찍힌다. 브라우저가 POST에 붙이는 `Origin` 헤더를 허용 목록(기본 localhost)과 비교하기 때문이다. `extraArgs.corsAllowedOrigins`에 화면 주소 `http://192.168.0.238:5000`을 넣어 해결했다(플래그 `--cors-allowed-origins`).

## 5. 확인

네 구성요소가 모두 올라와 있다. `/health`가 OK, `/version`이 3.16.0을 돌려주고, Jupyter Pod 안에는 `chapter-4` 커널과 clone된 저장소가 있다. 버킷 생성 Job은 끝난 뒤 TTL(1시간)로 지워져 목록에 없다.

```terminal
$ kubectl -n mlflow get pods -o wide
NAME                               READY   STATUS     NODE
jupyter-69964b676f-dcb75           1/1     Running    worker1-gpu
mlflow-58fd9c79f4-8ct97            1/1     Running    worker1-gpu
mlflow-postgres-64f54d5574-gxj8z   1/1     Running    worker1-gpu
rustfs-7856589f8b-lpgwv            1/1     Running    worker2-arm64
$ kubectl -n mlflow get svc
NAME             TYPE          EXTERNAL-IP     PORT(S)
jupyter          LoadBalancer  192.168.0.239   8888:31668/TCP
mlflow           LoadBalancer  192.168.0.238   5000:31250/TCP
mlflow-postgres  ClusterIP     <none>          5432/TCP
rustfs           ClusterIP     <none>          9000/TCP,9001/TCP
rustfs-lb        LoadBalancer  192.168.0.237   9000:30830/TCP,9001:32380/TCP
$ curl -s http://192.168.0.238:5000/health; echo; curl -s http://192.168.0.238:5000/version
OK
3.16.0
```

Jupyter Pod 안에서 `chapter-4` venv로 책 코드가 쓰는 호출을 처음부터 끝까지 한 번 돌려 봤다. 점검용 실험과 모델은 확인 후 지웠다.

| 단계 | 결과 |
| --- | --- |
| `mlflow.set_experiment(...)` | Postgres에 실험 생성, artifact_location `s3://mlflow-artifacts/chapter-4/1` |
| minio SDK `put_object` → `mlflow-datasets/...` | 업로드되고 `list_objects`로 보인다 |
| `log_params`, `log_metric`, `log_artifacts`, `log_input` | run에 기록, 아티팩트가 RustFS 키 `chapter-4/1/<run>/artifacts/`에 있다 |
| `mlflow.sklearn.log_model(...)` | logged model이 `chapter-4/1/models/m-.../artifacts/MLmodel`로 저장 |
| `register_model("models:/<model_id>", ...)` → `pyfunc.load_model` → predict | v1 등록, 로드, 예측까지 통과 |
| Host 헤더 | `mlflow:5000`, `mlflow.mlflow.svc:5000`, `192.168.0.238:5000`은 200, 엉뚱한 호스트는 403 |

Jupyter 토큰은 화면에 출력되니 필요할 때만 꺼낸다.

```bash
kubectl -n mlflow get secret jupyter-token -o jsonpath='{.data.token}' | base64 -d; echo
```

MLflow UI와 RustFS 콘솔에는 인증이 없거나 루트 계정 하나뿐이다. LAN 안에서만 쓰고 Keycloak 연동은 과제로 남긴다.

이 환경에서 책의 4.1절 노트북을 실제로 돌린 기록은 [홈랩 MLflow로 실험 추적과 모델 레지스트리 실습하기](../mlpe-04-1-mlflow-practice/)에, 같은 RustFS 위에 Feast를 올려 4.2절을 따라 한 기록은 [홈랩 Kubernetes에 Feast 올리고 실습하기](../mlpe-04-mlflow-feast/)에 있다.
