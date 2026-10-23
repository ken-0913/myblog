# 아이콘

| 디렉터리 | 내용 | 출처 |
| --- | --- | --- |
| `kubernetes/` | Kubernetes 로고, 리소스·컨트롤 플레인·인프라 아이콘(pod, svc, ing, crd 등) | kubernetes/kubernetes, kubernetes/community |
| `cncf/` | CNCF 프로젝트 로고 58종(Argo, Istio, Cilium, Kubeflow, Prometheus, OpenTelemetry, KServe, llm-d 등) | cncf/artwork |
| `grafana/` | Grafana 아이콘 | grafana/grafana |

모두 상표다. 기술 설명·다이어그램에서 그 프로젝트를 가리키는 용도로만 쓰고, 색과 모양을 바꾸지 않는다. 자세한 조건은 각 디렉터리의 README 와 LICENSE 를 본다.

## 다이어그램 안의 작은 마크 (Simple Icons)

`diagrams/` 와 글의 SVG 다이어그램에 넣는 제품 마크(GitHub, GitHub Actions, Docker, Argo, Kubernetes 조타륜)는 [Simple Icons](https://simpleicons.org)(CC0 1.0) 의 24×24 단일 path 를 브랜드 색으로 채워 쓴다. 파일로 두지 않고 다이어그램 SVG 안에 `<svg viewBox="0 0 24 24">` 로 바로 넣는다. Kubernetes 리소스(Pod, Service, Deployment, Secret, Namespace)는 위 `kubernetes/icons/resources/unlabeled/` 의 공식 아이콘을 중첩 `<svg>` 로 넣는다. 넣는 스크립트는 `diagrams/mlpe/inject_icons.py` 다(노드 상자 오른쪽 위, 컨테이너 라벨 오른쪽). Simple Icons 파일은 `https://cdn.simpleicons.org/<slug>` 에서 받아 디렉터리로 넘긴다.
