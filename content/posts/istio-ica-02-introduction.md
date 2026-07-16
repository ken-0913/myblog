---
title: "ICA 시험 정리 (2) Istio 입문: 아키텍처와 설치"
date: 2026-07-16T08:10:00+09:00
draft: false
tags: ["Istio", "ICA", "Istiod", "Envoy", "Kiali"]
categories: ["자격시험"]
---

ICA 시험 정리 시리즈 두 번째 편이다.
이번 편은 **Monolith에서 Microservice로의 전환**, **Service Mesh**, **Istio 아키텍처**, **설치 흐름**, **Kiali**를 다룬다.
시험에서는 Control Plane 구성 요소와 Sidecar 주입 과정이 자주 등장한다.

## Monolith에서 Microservice로

Monolith는 모든 기능을 하나의 코드베이스에 통합하므로, 작은 변경에도 전체 재배포가 필요하다.
Microservice로 전환하면 각 모듈을 독립적인 언어로 구현하고 독립적으로 배포·확장할 수 있다.
시험 예제로 자주 쓰이는 **Bookinfo** 애플리케이션은 Details, Reviews, Ratings, Product Page 4개 모듈로 구성된다.

전환에는 대가가 따른다.
인증, 인가, 로깅, 모니터링, 트래픽 관리 같은 **횡단 관심사(cross-cutting concerns)**가 각 서비스마다 중복 구현된다.
이 문제를 해결하는 전용 인프라 계층이 **Service Mesh**다.

## Service Mesh

Service Mesh는 비즈니스 코드를 수정하지 않고 서비스 간 통신을 관리하는 인프라 계층이다.
각 서비스 옆에 **Sidecar proxy**를 배치하여 네트워킹·보안·관찰 가능성을 애플리케이션에서 분리한다.
구조는 실제 트래픽을 처리하는 **Data Plane**과 이를 중앙에서 설정하는 **Control Plane**으로 나뉜다.

주요 기능은 service discovery, health check, load balancing, **mTLS 보안**, observability다.
이 기능들은 모두 애플리케이션 코드 변경 없이 proxy 계층에서 제공된다.

## Istio 아키텍처

Istio는 고성능 proxy인 **Envoy**를 Data Plane으로 사용하는 오픈소스 Service Mesh다.
각 Pod 옆에 배포된 Envoy proxy가 load balancing, 보안, observability를 처리한다.

Control Plane은 **Istiod**라는 단일 데몬으로 통합되어 있다.
초기에는 세 컴포넌트로 분리되어 있었고, 각각의 역할은 시험에서 자주 물어본다.

| 구성 요소 | 역할 |
|-----------|------|
| **Pilot** | service discovery 및 라우팅 설정 배포 |
| **Citadel** | 인증서 발급 및 보안 통신 관리 |
| **Galley** | 설정 파일 검증 |

각 Pod 안에서는 **Istio agent**가 Envoy proxy와 함께 동작하며 설정과 secret을 전달한다.

## 설치 흐름 (4단계)

### 1. istioctl 설치

```bash
curl -L https://istio.io/downloadIstio | sh -
export PATH=$PWD/bin:$PATH
istioctl version
```

### 2. Istio 설치 (demo profile)

```bash
istioctl install --set profile=demo -y
istioctl verify-install
```

이 명령은 `istio-system` namespace에 Istiod, Ingress Gateway, Egress Gateway, 그리고 여러 CRD를 배포한다.

### 3. Bookinfo 배포

```bash
kubectl apply -f samples/bookinfo/platform/kube/bookinfo.yaml
kubectl get pods
```

이 시점의 Pod는 **1/1**로 표시된다.
Sidecar 주입이 아직 활성화되지 않았기 때문이다.

### 4. Sidecar 주입 활성화

```bash
kubectl label namespace default istio-injection=enabled
kubectl delete -f samples/bookinfo/platform/kube/bookinfo.yaml
kubectl apply -f samples/bookinfo/platform/kube/bookinfo.yaml
```

namespace에 `istio-injection=enabled` label을 붙이고 재배포하면 Envoy Sidecar가 주입된다.
재배포 후 Pod가 **2/2**로 표시되면 주입이 정상적으로 완료된 것이다.
문제 진단에는 `istioctl analyze` 명령을 사용한다.

## Kiali로 시각화

**Kiali**는 Istio용 웹 기반 시각화 도구다.
마이크로서비스 연결 관계, Mesh 토폴로지, 요청 라우팅과 지연 정보를 그래픽으로 보여준다.

```bash
kubectl apply -f samples/addons          # Kiali, Grafana, Jaeger, Prometheus 설치
istioctl dashboard kiali                 # 대시보드 실행 (포트 20001)
```

주요 메뉴는 Applications, Workloads, Services, Istio Config, Graph다.
특히 **Graph**는 트래픽이 흐르고 있을 때만 의미 있는 시각화를 보여준다.
Product Page의 Deployment를 삭제하면 해당 노드가 빨간색으로 변하고 요청이 500 에러를 반환하는데, 이것이 Kiali의 진단 능력을 보여주는 핵심 데모다.

## 전체 흐름

```
Monolith → Microservice (횡단 관심사 문제)
   → Service Mesh (Sidecar로 관심사 분리)
   → Istio (Envoy + Istiod)
   → istioctl 설치 → Istio 설치 → 앱 배포 → Sidecar 주입 → Kiali 시각화
```

다음 편은 애플리케이션 코드를 수정하지 않고 트래픽을 제어하는 **Traffic Management**를 다룬다.
