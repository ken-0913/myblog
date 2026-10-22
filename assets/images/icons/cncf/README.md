# CNCF 프로젝트 아이콘 모음

아키텍처 다이어그램과 글에 쓰는 CNCF 프로젝트 공식 로고다. [cncf/artwork](https://github.com/cncf/artwork) 의 `projects/` 에서 SVG 만 골라 디렉터리 구조 그대로 가져왔다. PNG 는 SVG 로 대신할 수 있어서 넣지 않았다.

Kubernetes 자체 로고와 리소스 아이콘(Pod, Service, CRD 등)은 `../kubernetes/` 에 따로 있다.

## 사용 조건

`LICENSE.md` 그대로다. 모든 로고는 Linux Foundation 상표 사용 지침을 따른다. 기술 설명과 다이어그램에는 쓸 수 있지만, 이 블로그가 해당 프로젝트나 CNCF 의 후원·보증을 받는 것처럼 보이게 쓰면 안 된다. 색과 비율을 바꾸지 않는다.

## 구조

대부분 `<프로젝트>/<레이아웃>/<색>/<이름>.svg` 다.

- 레이아웃: `icon`(정사각 심볼), `horizontal`(심볼 + 이름 가로), `stacked`(심볼 위 + 이름 아래)
- 색: `color`, `black`, `white`(어두운 배경용)

다이어그램 노드에는 `icon/color`, 글 머리나 표에는 `horizontal/color` 를 쓴다. 다크 모드 배경에서는 `white` 를 쓴다.

일부 프로젝트(kubeflow-hub, kubeflow-model-registery, kubeflow-spark-operator)는 원본 저장소 구조가 달라 위 규칙을 따르지 않는다. `kubeflow-model-registery` 는 원본 저장소의 철자 그대로다.

## 프로젝트별 대표 아이콘

| 프로젝트 | 컬러 아이콘 |
| --- | --- |
| argo | `argo/icon/color/argo-icon-color.svg` |
| backstage | `backstage/icon/color/backstage-icon-color.svg` |
| cert-manager | `cert-manager/icon/color/cert-manager-icon-color.svg` |
| cilium | `cilium/icon/color/cilium_icon-color.svg` |
| cloudevents | `cloudevents/icon/color/cloudevents-icon-color-reversed.svg` |
| cni | `cni/icon/color/cni-icon-color.svg` |
| containerd | `containerd/icon/color/containerd-icon-color.svg` |
| coredns | `coredns/icon/color/coredns-icon-color.svg` |
| crio | `crio/icon/color/crio-icon-color.svg` |
| crossplane | `crossplane/icon/color/crossplane-icon-color.svg` |
| dapr | `dapr/icon/color/dapr-icon-color.svg` |
| envoy | `envoy/icon/color/envoy-icon-color.svg` (Envoy Gateway 는 `envoy/envoy-gateway/`) |
| etcd | `etcd/icon/color/etcd-icon-color.svg` |
| external-secrets-operator | `external-secrets-operator/icon/color/eso-icon-color.svg` |
| falco | `falco/icon/color/falco-icon-color.svg` |
| flux | `flux/flagger/icon/color/flagger-icon-color.svg` |
| grpc | `grpc/icon/color/grpc-icon-color.svg` |
| hami | `hami/icon/color/hami-icon-color.svg` |
| harbor | `harbor/icon/color/harbor-icon-color.svg` |
| helm | `helm/icon/color/helm-icon-color.svg` |
| istio | `istio/icon/color/istio-icon-color.svg` |
| jaeger | `jaeger/icon/color/jaeger-icon-color.svg` |
| kagent | `kagent/icon/color/kagent-icon-color.svg` |
| kai-scheduler | `kai-scheduler/icon/color/kai-scheduler-icon-color-negative.svg` |
| kaito | `kaito/icon/color/kaito-icon.svg` |
| keda | `keda/icon/color/keda-icon-color.svg` |
| keycloak | `keycloak/icon/color/keycloak-icon-color.svg` |
| kgateway | `kgateway/icon/color/kgateway-icon-color.svg` |
| knative | `knative/icon/color/knative-icon-color.svg` |
| kserve | `kserve/icon/color/k-serve-icon-color.svg` |
| kubeflow | `kubeflow/icon/color/kubeflow-icon.svg` |
| kubeflow-hub | `kubeflow-hub/kubeflow_hub_stacked-color.svg` |
| kubeflow-model-registery | `kubeflow-model-registery/Kubeflow-ModelRegistry-Logo_stacked-color.svg` |
| kubeflow-notebooks | `kubeflow-notebooks/icon/color/icon-color.svg` |
| kubeflow-pipelines | `kubeflow-pipelines/icon/color/kubeflow-pipelines-icon-color.svg` |
| kubeflow-spark-operator | `kubeflow-spark-operator/horizontal/svg/horizontal-color.svg` |
| kubeflow-trainer | `kubeflow-trainer/icon/color/Kubeflow-Trainer-Logo_icon-color.svg` |
| kuberay | `kuberay/icon/color/kuberay-icon-color.svg` |
| kubevirt | `kubevirt/icon/color/kubevirt-icon-color.svg` |
| kyverno | `kyverno/icon/color/kyverno-icon-color.svg` |
| linkerd | `linkerd/icon/color/linkerd-icon-color.svg` |
| llm-d | `llm-d/icon/color/llm-d-icon-color.svg` |
| longhorn | `longhorn/icon/color/longhorn-icon-color.svg` |
| metallb | `metallb/icon/color/metallb-icon-color.svg` |
| nats | `nats/icon/color/nats-icon-color.svg` |
| open-policy-agent | `open-policy-agent/icon/color/opa-icon-color.svg` |
| opencost | `opencost/icon/color/Opencost_Icon_Color.svg` |
| opengitops | `opengitops/icon/color/opengitops-icon-color.svg` |
| opentelemetry | `opentelemetry/icon/color/opentelemetry-icon-color.svg` |
| perses | `perses/icon/color/perses-icon-color.svg` |
| prometheus | `prometheus/icon/color/prometheus-icon-color.svg` |
| rook | `rook/icon/color/rook-icon-color.svg` |
| spiffe | `spiffe/icon/color/spiffe-icon-color.svg` |
| spire | `spire/icon/color/spire-icon-color.svg` |
| tekton | `tekton/icon/color/tekton-icon-color.svg` |
| thanos | `thanos/icon/color/thanos-icon-color.svg` |
| volcano | `volcano/icon/color/volcano-icon-color.svg` |

## 다시 받기 / 추가하기

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/cncf/artwork.git
cd artwork && git sparse-checkout set projects/<프로젝트>
```

받은 뒤 `projects/<프로젝트>` 아래의 `*.svg` 만 이 디렉터리로 복사하고 위 표에 한 줄 추가한다. 프로젝트 이름 목록은 저장소의 `projects/` 디렉터리를 보면 된다.
