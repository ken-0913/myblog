---
title: "ICA 시험 정리 (5) Observability: Prometheus, Grafana, Jaeger, Kiali"
date: 2026-07-16T08:40:00+09:00
draft: false
tags: ["Istio", "ICA", "Observability", "Prometheus", "Jaeger"]
categories: ["자격시험"]
---

ICA 시험 정리 시리즈 마지막 편이다.
Istio는 Data Plane의 Envoy proxy가 모든 트래픽을 관리하면서 서비스 간 통신마다 상세한 telemetry를 생성한다.
덕분에 observability 솔루션을 처음부터 구축하지 않고도 **metrics**, **distributed tracing**, **시각화**를 얻는다.

## Observability 3요소

Istio observability는 세 가지 도구로 구성된다.
각 도구의 역할 구분이 시험 포인트다.

| 도구 | 역할 |
|------|------|
| **Prometheus / Grafana** | metrics 수집 및 시각화 |
| **Jaeger** | distributed tracing |
| **Kiali** | Mesh 토폴로지 및 동작 분석 |

이 도구들은 `kubectl apply -f samples/addons`로 함께 설치되며, 데모 용도이므로 프로덕션 성능·보안에는 튜닝되어 있지 않다.

## Prometheus와 Grafana

**Prometheus**는 metrics를 수집·저장·질의하는 모니터링 도구다.
Istio는 표준 metrics를 Prometheus로 자동 export하므로 별도 계측 없이 데이터를 수집한다.

```bash
istioctl dashboard prometheus
```

대표 metric은 전체 요청 수를 추적하는 `istio_requests_total`이다.
이 metric은 `destination_service`, `response_code`, `source_workload` 등 여러 dimension으로 필터링할 수 있다.
Prometheus는 질의에 강하지만 그래프 표현은 제한적이므로, 시각화는 **Grafana**가 담당한다.

Grafana는 Istio add-on으로 다음 대시보드를 제공한다.

| 대시보드 | 표시 내용 |
|----------|-----------|
| **Control Plane** | CPU, 메모리, goroutine, 설정 동기화 오류 |
| **Mesh** | 전체 요청량, 성공률, 서비스·정책 통계 |
| **Service** | Data Plane 관점의 서비스별 metrics |
| **Workload** | 특정 워크로드의 요청량, 성공률, 요청 시간 |
| **Performance** | 컴포넌트별 메모리, vCPU, 디스크 사용량 |

```bash
kubectl get svc prometheus -n istio-system   # 9090/TCP
kubectl get svc grafana -n istio-system      # 3000/TCP
```

## Jaeger로 Distributed Tracing

**Jaeger**는 요청이 여러 서비스를 거치는 경로를 추적하는 distributed tracing 도구다.

```bash
istioctl dashboard jaeger
```

핵심 개념은 **trace**와 **span**이다.
하나의 trace는 여러 span으로 구성되며, 각 **span**은 하나의 논리적 작업 단위를 나타낸다.
span을 펼치면 상세 타이밍 정보와 필터링용 tag를 확인할 수 있다.

Jaeger는 성능 문제 진단에 유용하다.
예를 들어 Details 서비스에 지연을 주입하면, Product Page가 3초를 기다린 뒤 에러를 반환하는 과정을 trace로 확인할 수 있다.
고부하 상황에서는 Jaeger가 몇 초 분량만 sampling한다는 점도 알아두면 좋다.

## Kiali

**Kiali**는 Mesh 동작을 종합적으로 분석하는 시각화 도구다.
Prometheus·Jaeger가 수집한 데이터를 바탕으로 트래픽 흐름, 오류 서비스, 설정 상태를 그래픽으로 보여준다.
Fault Injection을 적용하면 Graph view에서 문제 있는 서비스에 오류 표시가 나타난다.

## Service Mesh Interface (SMI)

시험에 참고로 등장하는 개념이 **SMI(Service Mesh Interface)**다.
SMI는 다양한 Service Mesh 구현 위에 표준 추상화 계층을 제공하여 **vendor lock-in**을 줄인다.

2019년 **Microsoft**가 주도하여 시작했다.
traffic management, telemetry, traffic policy에 대한 공통 기능 집합을 정의하여 이식성과 상호운용성을 높인다.
Istio를 포함한 주요 Service Mesh 제공자들이 이 표준을 채택했다.

## 시리즈 마무리

다섯 편에 걸쳐 ICA 시험 범위를 정리했다.
기초(Service, Sidecar, Envoy)에서 시작해 Istio 아키텍처, Traffic Management, Security, Observability까지 이어진다.
각 편의 리소스 종류와 필드, 정책 적용 범위를 손으로 직접 작성해보는 연습이 시험 대비에 가장 효과적이다.
