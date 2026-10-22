# Kubernetes 공식 아이콘 모음

아키텍처 다이어그램과 배너에 쓰는 Kubernetes 공식 아이콘이다. 두 곳에서 가져왔고, 각 디렉터리에 원본 LICENSE 를 그대로 두었다.

| 디렉터리 | 출처 | 라이선스 |
| --- | --- | --- |
| `logo/` | [kubernetes/kubernetes `logo/`](https://github.com/kubernetes/kubernetes/tree/master/logo) | Apache-2.0 또는 CC-BY-4.0 중 택일. 상표 사용은 `logo/usage_guidelines.md`(Linux Foundation 상표 지침)를 따른다 |
| `icons/` | [kubernetes/community `icons/svg/`](https://github.com/kubernetes/community/tree/master/icons) | Apache-2.0 |

## logo/

- `logo.svg`, `logo.png`: 조타륜(헬름) 아이콘. 배너 장식은 `scripts/gen_banners.py` 가 `logo.png` 를 읽어 쓴다.
- `logo_with_border.svg`: 흰 테두리 버전(어두운 배경용).
- `name_blue.svg`, `name_white.svg`: "kubernetes" 워드마크.
- `colors.md`: 공식 색상(파랑 `#326ce5`).

## icons/

`labeled/` 는 아이콘 안에 약어가 적혀 있고, `unlabeled/` 는 그림만 있다. 다이어그램에서 이름을 따로 적을 때는 unlabeled 를 쓴다.

| 디렉터리 | 내용 |
| --- | --- |
| `resources/` | pod, svc, deploy, rs, sts, ds, job, cronjob, ing, netpol, ns, cm, secret, sa, pv, pvc, sc, vol, hpa, limits, quota, ep, crd, role, rb, c-role, crb, psp, group, user |
| `control_plane_components/` | api, sched, c-m, c-c-m, kubelet, k-proxy |
| `infrastructure_components/` | control-plane, node, etcd |

파일명은 `kubectl` 약어와 같다(`svc` = Service, `ing` = Ingress, `crd` = CustomResourceDefinition, `sts` = StatefulSet, `c-m` = controller-manager, `c-c-m` = cloud-controller-manager).

## 쓰는 법

- 글 안에서: `assets/` 아래라 Hugo 가 `resources.Get "images/icons/kubernetes/icons/resources/unlabeled/pod.svg"` 로 읽을 수 있다. 다이어그램 SVG(`diagrams/`)에서는 파일을 열어 `<path>` 를 복사하거나 `<image href>` 로 참조한다.
- 원본을 수정하지 않는다. 색을 바꿔야 하면 복사본을 만든다.
