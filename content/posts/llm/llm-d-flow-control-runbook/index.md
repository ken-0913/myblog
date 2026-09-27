---
title: "LLM 스터디 7주차 - llm-d Flow Control 재현 매뉴얼"
date: 2026-09-27T14:00:00+09:00
draft: false
tags: ["LLM", "llm-d", "vLLM", "Kubernetes", "Flow Control", "EPP", "Runbook", "Benchmark"]
categories: ["LLM"]
---
[Flow Control 실측 글](../llm-d-flow-control-lab/)에서 얻은 결과를 **그대로 다시 만들기 위한 절차서**다. 분석과 해석은 그 글에 있고, 이 문서에는 명령과 스크립트만 순서대로 담는다.

GPU 1장짜리 kind 클러스터를 기준으로 쓴다. 기본 배포까지는 [kind에 llm-d 올리기](../llm-d-prefix-cache-lab/)를 따라온 상태를 전제한다.

## 0. 전제 조건

아래가 이미 떠 있어야 한다.

| 항목 | 값 |
| --- | --- |
| 클러스터 | kind, GPU 노출 완료(`nvidia.com/gpu` 광고됨) |
| llm-d Router | chart `llm-d-router-standalone` `v0`, release `optimized-baseline` |
| 배포 모드 | Standalone (EPP 파드에 Envoy 사이드카) |
| 모델 서버 | vLLM 1 replica, `Qwen/Qwen3-0.6B` |
| 네임스페이스 | `llm-d-lab` |
| 저장소 | `~/llm-d` (guides 포함) |

```bash {title="0-1. 시작 상태 확인"}
$ export REPO_ROOT=~/llm-d
$ export NAMESPACE=llm-d-lab

$ kubectl get pod -n $NAMESPACE
NAME                                                         READY   STATUS
optimized-baseline-epp-5fbd7457f9-9xcr7                      2/2     Running
optimized-baseline-nvidia-gpu-vllm-decode-7978d9d5c9-h59gz   1/1     Running

$ helm list -n $NAMESPACE
NAME                 CHART                       STATUS
optimized-baseline   llm-d-router-standalone     deployed
```

> **컨텍스트를 먼저 확인한다.** kind 클러스터를 여러 개 쓰면 `kubectl config current-context`가 엉뚱한 곳을 가리키기 쉽다. 모든 명령에 `--context kind-gpu-lab`을 붙이거나 `kubectl config use-context`로 고정해둔다.

## 1. 기준값 찾기 — maxConcurrency는 측정값이다

가이드 기본값은 `maxConcurrency: 132`인데 **replica 8개(GPU 16장) 기준**이다. replica 1개로는 도달할 수 없어 게이트가 항상 열려 있다.

기준점은 vLLM이 기동 로그에 찍어준다.

```bash {title="1-1. 모델 서버의 실질 동시 처리 한계"}
$ kubectl logs -n $NAMESPACE deploy/optimized-baseline-nvidia-gpu-vllm-decode \
    | grep -E "KV cache size|Maximum concurrency"
[kv_cache_utils.py:2177] GPU KV cache size: 20,032 tokens
[kv_cache_utils.py:2178] Maximum concurrency for 2,048 tokens per request: 9.78x
```

이 환경에서는 **9.78x**가 나왔다. 실험용으로는 큐가 쌓이는 모습을 보려고 **4**로 낮추고, 마지막에 **10**으로 되돌린다.

## 2. CRD 설치 — InferenceObjective

우선순위는 `InferenceObjective`에서 나온다. **이 CRD가 없으면 모든 요청이 priority 0으로 떨어져 대역 실험이 성립하지 않는다.**

```bash {title="2-1. CRD 적용"}
$ kubectl apply -f https://github.com/llm-d/llm-d-router/releases/latest/download/manifests.yaml
customresourcedefinition.apiextensions.k8s.io/inferencemodelrewrites.llm-d.ai created
customresourcedefinition.apiextensions.k8s.io/inferenceobjectives.llm-d.ai created

$ kubectl get crd | grep objective
inferenceobjectives.llm-d.ai
```

## 3. 우선순위 클래스 3종

`poolRef`는 **기존 InferencePool 이름**과 맞춰야 한다. 가이드 원본은 `flow-control`이라는 별도 풀을 만들지만, GPU가 1장이면 모델 서버를 더 띄울 수 없으므로 기존 풀에 얹는다.

```yaml {title="3-1. objectives.yaml"}
apiVersion: llm-d.ai/v1alpha2
kind: InferenceObjective
metadata: {name: premium-traffic}
spec:
  priority: 100
  poolRef: {name: optimized-baseline}
---
apiVersion: llm-d.ai/v1alpha2
kind: InferenceObjective
metadata: {name: standard-traffic}
spec:
  priority: 0
  poolRef: {name: optimized-baseline}
---
apiVersion: llm-d.ai/v1alpha2
kind: InferenceObjective
metadata: {name: best-effort-traffic}
spec:
  priority: -10          # 음수 = sheddable
  poolRef: {name: optimized-baseline}
```

```bash {title="3-2. 적용 및 확인"}
$ kubectl apply -n $NAMESPACE -f objectives.yaml

$ kubectl get inferenceobjective -n $NAMESPACE
NAME                  INFERENCE POOL       PRIORITY
best-effort-traffic   optimized-baseline   -10
premium-traffic       optimized-baseline   100
standard-traffic      optimized-baseline   0
```

## 4. EPP에 Flow Control 켜기

기존 릴리스에 values 파일 하나를 **추가로 얹는** 방식이다. 원래 쓰던 values 두 개를 같이 넘겨야 기존 설정이 유지된다.

```yaml {title="4-1. flow-control-lab.values.yaml"}
router:
  epp:
    flags:
      v: 2
      metrics-endpoint-auth: false      # :9090/metrics 가 기본 401 이다
    pluginsConfigFile: "flow-control-lab.yaml"
    pluginsCustomConfig:
      flow-control-lab.yaml: |
        apiVersion: llm-d.ai/v1alpha1
        kind: EndpointPickerConfig
        featureGates:
        - flowControl                   # 기능 게이트를 명시적으로 켠다
        plugins:
        - type: approx-prefix-cache-producer
        - type: inflight-load-producer
        - type: prefix-cache-affinity-filter
        - type: token-load-scorer
        - type: round-robin-fairness-policy
        - type: fcfs-ordering-policy
        - type: concurrency-detector
          parameters:
            maxConcurrency: 4           # 실험용. 마지막에 10 으로 되돌린다
            concurrencyMode: requests
            headroom: 0.0
        schedulingProfiles:
        - name: default
          plugins:
          - pluginRef: prefix-cache-affinity-filter
          - pluginRef: token-load-scorer
        flowControl:
          maxBytes: "1Gi"
          maxRequests: "1k"
          defaultRequestTTL: "60s"
          saturationDetector:
            pluginRef: concurrency-detector
          priorityBands:
          - {priority: 100, maxRequests: "500", fairnessPolicyRef: round-robin-fairness-policy, orderingPolicyRef: fcfs-ordering-policy}
          - {priority: 0,   maxRequests: "200", fairnessPolicyRef: round-robin-fairness-policy, orderingPolicyRef: fcfs-ordering-policy}
          - {priority: -10, maxRequests: "50",  fairnessPolicyRef: round-robin-fairness-policy, orderingPolicyRef: fcfs-ordering-policy}
```

`saturationDetector`를 `flowControl` **아래**에 둔 점을 주의한다. 공식 문서 페이지는 최상위에 두지만, 저장소의 `guides/flow-control/router/flow-control.values.yaml`은 이 위치를 쓴다. EPP 이미지와 같은 스냅샷인 저장소 쪽을 따랐다.

```bash {title="4-2. helm upgrade"}
$ helm upgrade optimized-baseline oci://ghcr.io/llm-d/charts/llm-d-router-standalone \
    -f ${REPO_ROOT}/guides/recipes/router/base.values.yaml \
    -f ${REPO_ROOT}/guides/optimized-baseline/router/optimized-baseline.values.yaml \
    -f ~/flow-control-lab.values.yaml \
    -n $NAMESPACE --version v0

$ kubectl rollout status deploy/optimized-baseline-epp -n $NAMESPACE
deployment "optimized-baseline-epp" successfully rolled out
```

```bash {title="4-3. 활성화 검증"}
$ kubectl logs -n $NAMESPACE deploy/optimized-baseline-epp -c epp | grep -i "Flow Control"
{"body":"Initializing Flow Control layer","service.name":"llm-d-epp"}

$ kubectl logs -n $NAMESPACE deploy/optimized-baseline-epp -c epp | grep -o 'FeatureGates: {flowControl}'
FeatureGates: {flowControl}
```

> **EPP는 핫 리로드가 없다.** 설정을 바꿀 때마다 파드가 재시작되고, `failureMode: FailOpen`이라 그 순간 요청은 **플로우 컨트롤 없이 통과**한다. 재시작 직후 몇 초간의 측정값은 버린다.

## 5. 측정 스크립트

두 개를 쓴다. `burst.py`는 동시 부하의 파도를 재고, `scenario.py`는 테넌트·우선순위 시나리오를 만든다.

둘 다 **vLLM 파드 안에서 실행한다.** 그 이미지에 python3와 필요한 표준 라이브러리가 들어 있어 별도 준비가 필요 없다.

```python {title="5-1. burst.py — 동시 부하와 파도 측정"}
import json, time, threading, urllib.request, sys, statistics as st

EPP = "http://optimized-baseline-epp.llm-d-lab.svc.cluster.local:80"
VLLM = "http://localhost:8000"
MODEL = "Qwen/Qwen3-0.6B"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 16
LABEL = sys.argv[2] if len(sys.argv) > 2 else "run"

results, samples = [], []
lock = threading.Lock()
stop = False

def sampler():
    """vLLM 의 running/waiting 을 0.15초 간격으로 훔쳐본다"""
    while not stop:
        try:
            with urllib.request.urlopen(VLLM + "/metrics", timeout=5) as r:
                txt = r.read().decode()
            run = wait = 0.0
            for line in txt.splitlines():
                if line.startswith("vllm:num_requests_running{"):
                    run = float(line.rsplit(" ", 1)[1])
                elif line.startswith("vllm:num_requests_waiting{"):
                    wait = float(line.rsplit(" ", 1)[1])
            samples.append((run, wait))
        except Exception:
            pass
        time.sleep(0.15)

def worker(i):
    body = json.dumps({"model": MODEL,
                       "prompt": f"Request {i}: explain container networking in detail.",
                       "max_tokens": 128, "temperature": 0, "stream": True}).encode()
    req = urllib.request.Request(EPP + "/v1/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter(); ttft = None; code = 200
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            for raw in resp:
                if raw.startswith(b"data: ") and b"[DONE]" not in raw and ttft is None:
                    ttft = time.perf_counter() - t0
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception:
        code = -1
    with lock:
        results.append({"i": i, "code": code,
                        "ttft": round(ttft * 1000, 1) if ttft else None,
                        "e2e": round((time.perf_counter() - t0) * 1000, 1)})

threading.Thread(target=sampler, daemon=True).start()
t_start = time.perf_counter()
ths = [threading.Thread(target=worker, args=(i,)) for i in range(N)]
for t in ths: t.start()
for t in ths: t.join()
wall = (time.perf_counter() - t_start) * 1000
stop = True; time.sleep(0.3)

ok = [r for r in results if r["code"] == 200 and r["ttft"]]
ttfts = sorted(r["ttft"] for r in ok)
print(f"=== {LABEL} : 동시 {N}건 ===")
print("전체 소요(ms)", round(wall, 1))
print("상태코드 분포", {c: sum(1 for r in results if r["code"] == c)
                        for c in sorted({r["code"] for r in results})})
if ttfts:
    print("TTFT min/p50/max (ms)", ttfts[0], st.median(ttfts), ttfts[-1])
    print("TTFT 전체", ttfts)
if samples:
    print("vLLM running max/avg", max(s[0] for s in samples),
          round(st.mean([s[0] for s in samples]), 2))
    print("vLLM waiting max/avg", max(s[1] for s in samples),
          round(st.mean([s[1] for s in samples]), 2))
```

```python {title="5-2. scenario.py — 테넌트·우선순위 시나리오"}
import json, time, threading, urllib.request, sys

EPP = "http://optimized-baseline-epp.llm-d-lab.svc.cluster.local:80"
MODEL = "Qwen/Qwen3-0.6B"
MODE = sys.argv[1]          # fairness | priority | shed
results = []
lock = threading.Lock()
T0 = None

def send(tag, fairness=None, objective=None, idx=0, max_tokens=128):
    h = {"Content-Type": "application/json"}
    if fairness:  h["x-llm-d-inference-fairness-id"] = fairness
    if objective: h["x-llm-d-inference-objective"] = objective
    body = json.dumps({"model": MODEL,
                       "prompt": f"{tag}-{idx}: explain container networking in detail.",
                       "max_tokens": max_tokens, "temperature": 0, "stream": True}).encode()
    req = urllib.request.Request(EPP + "/v1/completions", data=body, headers=h)
    t_send = time.perf_counter() - T0
    ttft = None; code = 200; reason = None
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            for raw in resp:
                if raw.startswith(b"data: ") and b"[DONE]" not in raw and ttft is None:
                    ttft = time.perf_counter() - T0
                    # 스트림은 끝까지 읽는다. 중도 종료하면 점유가 즉시 풀려 포화가 생기지 않는다
    except urllib.error.HTTPError as e:
        code = e.code
        reason = e.headers.get("x-llm-d-request-dropped-reason")
    except Exception:
        code = -1
    with lock:
        results.append({"tag": tag, "idx": idx, "code": code, "reason": reason,
                        "sent_ms": round(t_send * 1000, 1),
                        "first_token_ms": round(ttft * 1000, 1) if ttft else None})

T0 = time.perf_counter()
ths = []

if MODE == "fairness":
    # tenant-a 가 12건으로 먼저 점유 → 0.4초 뒤 tenant-b 가 2건
    for i in range(12):
        t = threading.Thread(target=send, args=("tenant-a",),
                             kwargs={"fairness": "tenant-a", "idx": i}); t.start(); ths.append(t)
    time.sleep(0.4)
    for i in range(2):
        t = threading.Thread(target=send, args=("tenant-b",),
                             kwargs={"fairness": "tenant-b", "idx": i}); t.start(); ths.append(t)

elif MODE == "priority":
    # best-effort 12건으로 큐를 만든 뒤 premium 4 + standard 4 를 동시 투입
    for i in range(12):
        t = threading.Thread(target=send, args=("best-effort",),
                             kwargs={"fairness": "batch", "objective": "best-effort-traffic",
                                     "idx": i}); t.start(); ths.append(t)
    time.sleep(2.0)
    for i in range(4):
        t = threading.Thread(target=send, args=("premium",),
                             kwargs={"fairness": "vip", "objective": "premium-traffic",
                                     "idx": i}); t.start(); ths.append(t)
    for i in range(4):
        t = threading.Thread(target=send, args=("standard",),
                             kwargs={"fairness": "std", "objective": "standard-traffic",
                                     "idx": i}); t.start(); ths.append(t)

elif MODE == "shed":
    # 대역 용량과 TTL 을 조인 뒤 best-effort 24건을 한꺼번에
    for i in range(24):
        t = threading.Thread(target=send, args=("best-effort",),
                             kwargs={"fairness": "batch", "objective": "best-effort-traffic",
                                     "idx": i}); t.start(); ths.append(t)

for t in ths: t.join()

print(f"=== {MODE} ===")
for r in sorted(results, key=lambda x: (x["first_token_ms"] is None, x["first_token_ms"] or 0)):
    print(f"{r['tag']:<12} #{r['idx']:<2} 보냄 {r['sent_ms']:>7.1f}ms  "
          f"첫토큰 {str(r['first_token_ms']):>8}ms  code={r['code']} {r['reason'] or ''}")
```

### 실행 방법

파일을 파드에 복사하지 않고 **표준 입력으로 밀어 넣는다.**

```bash {title="5-3. 스크립트 실행"}
$ V=$(kubectl get pod -n $NAMESPACE -l llm-d.ai/role=decode \
        -o jsonpath='{.items[0].metadata.name}')

# 동시 16건, 라벨을 붙여 결과를 구분한다
$ kubectl exec -i -n $NAMESPACE $V -- python3 - 16 "maxConcurrency=4" < burst.py

# 시나리오
$ kubectl exec -i -n $NAMESPACE $V -- python3 - fairness < scenario.py
$ kubectl exec -i -n $NAMESPACE $V -- python3 - priority < scenario.py
```

## 6. 실험 순서

### 6-1. 기준선 — Flow Control 없이

`featureGates`를 빼고 `helm upgrade`한 상태에서 먼저 잰다. **비교 기준이 없으면 좋아졌는지 알 수 없다.**

```bash {title="기대 출력"}
=== BEFORE (flow control 비활성) : 동시 16건 ===
전체 소요(ms) 2250.8
TTFT 전체 [238.8, 256.6, ... 262.5]      ← 24ms 폭에 전부 몰린다
vLLM running max/avg 16.0 13.87          ← 16건이 한꺼번에 GPU 로 들어갔다
```

### 6-2. 게이트를 걸었을 때

`maxConcurrency: 4`로 올린 뒤 같은 명령을 돌린다.

```bash {title="기대 출력"}
TTFT 전체 [253.7, 259.7, 265.3, 267.8, 268.2, 268.6,   ← 1파도
           2230.4, 2246.4, 2248.0, 2249.6,             ← 2파도
           4229.7, 4243.1, 4243.5, 4245.0,             ← 3파도
           6206.4, 6223.8]                             ← 4파도
vLLM running max/avg 6.0 3.81
```

### 6-3. 공정성

```bash {title="fairness 모드 — tenant-b 가 언제 나가는지 본다"}
$ kubectl exec -i -n $NAMESPACE $V -- python3 - fairness < scenario.py

tenant-a  #7  보냄     2.6ms  첫토큰     45.4ms
...
tenant-b  #1  보냄   406.0ms  첫토큰   2126.0ms   ← 늦게 왔는데 2파도에 들어갔다
tenant-b  #0  보냄   405.8ms  첫토큰   2126.0ms
tenant-a  #4  보냄     1.7ms  첫토큰   4087.8ms   ← 먼저 온 a 가 뒤로 밀렸다
```

### 6-4. 우선순위

```bash {title="priority 모드 — premium 이 standard 보다 먼저인지 본다"}
$ kubectl exec -i -n $NAMESPACE $V -- python3 - priority < scenario.py

premium   #0  첫토큰  2060.4ms      premium   #2  첫토큰  4008.6ms
premium   #1  첫토큰  2060.4ms      premium   #3  첫토큰  4026.5ms
standard  #1  첫토큰  4026.6ms      standard  #2  첫토큰  6027.0ms
standard  #0  첫토큰  4026.6ms      standard  #3  첫토큰  6043.0ms
# best-effort 12건은 그 뒤로 밀림
```

## 7. 부하 차단과 TTL 만료

낮은 대역의 큐를 의도적으로 좁히고 TTL을 짧게 줄인다. **실험용 극단값이므로 끝나면 되돌린다.**

```bash {title="7-1. 설정 조이기"}
# flow-control-lab.values.yaml 에서 두 값만 바꾼다
#   defaultRequestTTL: "60s"  ->  "3s"
#   priority -10 의 maxRequests: "50"  ->  "5"

$ helm upgrade optimized-baseline oci://ghcr.io/llm-d/charts/llm-d-router-standalone \
    -f ${REPO_ROOT}/guides/recipes/router/base.values.yaml \
    -f ${REPO_ROOT}/guides/optimized-baseline/router/optimized-baseline.values.yaml \
    -f ~/flow-control-lab.values.yaml \
    -n $NAMESPACE --version v0
$ kubectl rollout status deploy/optimized-baseline-epp -n $NAMESPACE
```

```bash {title="7-2. shed 모드 실행"}
$ kubectl exec -i -n $NAMESPACE $V -- python3 - shed < scenario.py

best-effort #12 첫토큰   250.5ms  code=200
... (8건 성공)
best-effort #23 첫토큰     None   code=429 rejected-saturated      ← 15건
best-effort #20 첫토큰     None   code=429 rejected-ttl-expired    ← 1건
```

문서는 TTL 만료를 **503**으로 매핑한다고 적지만 실제 응답은 **429**였다. 드롭 사유 헤더와 메트릭은 문서대로 나온다.

## 8. 메트릭 조회

`metrics-endpoint-auth: false`를 켜두었으므로 인증 없이 읽힌다.

```bash {title="8-1. Flow Control 메트릭"}
$ kubectl exec -n $NAMESPACE $V -- \
    curl -s optimized-baseline-epp.$NAMESPACE.svc.cluster.local:9090/metrics \
    | grep '^llm_d_epp_flow_control' | grep -vE '_bucket|_created|_sum|_count'

llm_d_epp_flow_control_requests_total{outcome="Dispatched",       priority="-10"} 8
llm_d_epp_flow_control_requests_total{outcome="RejectedCapacity", priority="-10"} 15
llm_d_epp_flow_control_requests_total{outcome="EvictedTTL",       priority="-10"} 1
llm_d_epp_flow_control_queue_size{fairness_id="batch",priority="-10",...} 0
llm_d_epp_flow_control_pool_saturation{stage="effective",...} 0
```

클라이언트가 받은 상태코드와 이 카운터가 일치하는지 대조하면 측정이 제대로 됐는지 확인된다.

## 9. 되돌리기

실험용 극단값을 걷어내고 측정 기준값으로 정리한다.

```bash {title="9-1. 튜닝값으로 복귀"}
# flow-control-lab.values.yaml
#   maxConcurrency: 4   ->  10      (vLLM 실측 9.78x 기준)
#   defaultRequestTTL:  ->  "60s"
#   priority -10 maxRequests -> "50"

$ helm upgrade optimized-baseline ... -f ~/flow-control-lab.values.yaml -n $NAMESPACE --version v0

$ kubectl exec -i -n $NAMESPACE $V -- python3 - 16 "TUNED" < burst.py
전체 소요(ms) 4219.0
vLLM running max/avg 10.0 7.43        ← 설정값과 정확히 일치
```

```bash {title="9-2. 완전히 내릴 때"}
# GPU 를 다른 실습에 쓰려면 파드만 0 으로 내린다 (릴리스와 설정은 유지)
$ kubectl scale deploy/optimized-baseline-nvidia-gpu-vllm-decode -n $NAMESPACE --replicas=0
$ kubectl scale deploy/optimized-baseline-epp -n $NAMESPACE --replicas=0

# 되살릴 때
$ kubectl scale deploy/optimized-baseline-nvidia-gpu-vllm-decode -n $NAMESPACE --replicas=1
$ kubectl scale deploy/optimized-baseline-epp -n $NAMESPACE --replicas=1
```

## 10. 걸렸던 것 모음

재현하다 막히면 이 목록을 먼저 본다.

| 증상 | 원인과 해결 |
| --- | --- |
| 게이트가 전혀 동작하지 않는다 | `maxConcurrency` 기본값 132는 GPU 16장 기준이다. 1 replica면 도달 불가 → 실측 동시성 근처로 낮춘다 |
| 모든 요청이 같은 대역으로 간다 | `InferenceObjective` CRD 미설치. 없으면 전부 priority 0 |
| `poolRef` 가 안 먹는다 | 가이드 원본은 `flow-control` 풀을 가리킨다. 기존 풀 이름으로 바꿔야 한다 |
| 메트릭이 401 | EPP는 기본적으로 메트릭 인증을 요구한다 → `metrics-endpoint-auth: false` |
| 설정을 바꿨는데 반영이 안 된다 | EPP는 핫 리로드가 없다. 파드 재시작이 필요하고 재시작 중에는 FailOpen 으로 통과한다 |
| 부하를 넣어도 큐가 안 쌓인다 | 스트림을 첫 토큰에서 끊으면 점유가 바로 풀린다. **응답을 끝까지 읽어야** 포화가 생긴다 |
| 설정값보다 많이 통과한다 | 요청마다 `fairness-id`를 다르게 주면(flow 다수) 초기 버스트가 게이트를 넘는다. 테넌트 수를 줄여 재확인한다 |
| EPP 파드가 Pending | EPP 하나가 CPU 8코어를 요청한다(Envoy `--concurrency 8`). 다른 EPP를 내리거나 노드 CPU를 확인한다 |

측정값의 의미와 해석은 [Flow Control 실측 글](../llm-d-flow-control-lab/)에 정리해 두었다.
