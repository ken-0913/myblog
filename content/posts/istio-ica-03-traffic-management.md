---
title: "ICA 시험 정리 (3) Traffic Management"
date: 2026-07-16T10:20:00+09:00
draft: false
tags: ["Istio", "ICA", "Traffic Management", "VirtualService", "DestinationRule"]
categories: ["자격시험"]
---

ICA 시험 정리 시리즈 세 번째 편이다.
Istio는 애플리케이션 코드를 수정하지 않고 트래픽을 제어한다.
이번 편은 핵심 컴포넌트인 **Gateway**, **Virtual Service**, **Destination Rule**과 고급 기법인 Timeout, Retry, Fault Injection, Circuit Breaking, A/B Testing을 정리한다.

## 핵심 컴포넌트 3종

세 리소스의 역할 구분이 시험의 핵심이다.
**Gateway**는 트래픽을 받기만 하고, 실제 라우팅은 **Virtual Service**가 정의하며, 라우팅 이후 정책은 **Destination Rule**이 담당한다.

| 컴포넌트 | 역할 | 주요 필드 |
|----------|------|-----------|
| **Gateway** | Mesh 가장자리에서 inbound/outbound 트래픽 수용 | `selector`, `servers.hosts`, `servers.port` |
| **Virtual Service** | 라우팅 규칙, 가중치, 헤더 매칭, Timeout, Retry, Fault | `hosts`, `gateways`, `http.match`, `http.route` |
| **Destination Rule** | 라우팅 이후 정책: Subset, LB, TLS, Circuit Breaking | `host`, `subsets`, `trafficPolicy` |

## Gateway

Istio Gateway는 Mesh 가장자리에서 동작하는 로드밸런서다.
전통적인 Kubernetes Ingress가 NGINX 같은 컨트롤러를 쓰는 것과 달리, Istio Ingress Gateway는 **Envoy proxy**로 inbound 트래픽을 가로챈다.

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway   # 기본 Istio Ingress Gateway 사용
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "bookinfo.app"
```

Gateway와 Virtual Service의 `hosts`는 반드시 일치해야 한다.

## Virtual Service

Virtual Service는 라우팅 규칙을 정의하는 핵심 리소스다.
Kubernetes만으로는 트래픽 비율을 **Pod 개수**로만 조절할 수 있어 1% 같은 세밀한 제어가 불가능하다.
Istio는 **weight** 기반 라우팅으로 Pod 개수와 무관하게 비율을 결정한다.

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
    - reviews
  http:
    - route:
        - destination:
            host: reviews
            subset: v1
          weight: 99
        - destination:
            host: reviews
            subset: v2
          weight: 1
```

Header 기반 라우팅도 가능하다.
아래는 `end-user: kodekloud` 헤더를 가진 요청만 v2로 보내고 나머지는 v1로 보내는 예시다.

```yaml
http:
- match:
  - headers:
      end-user:
        exact: kodekloud
  route:
  - destination:
      host: reviews
      subset: v2
- route:
  - destination:
      host: reviews
      subset: v1
```

## Destination Rule

Destination Rule은 트래픽이 서비스로 라우팅된 **이후** 적용되는 정책을 정의한다.
Subset 정의, load balancing, TLS, Circuit Breaking을 다룬다.
**Subset**은 Pod의 label로 그룹을 나눈 것으로, Virtual Service의 `subset`이 이것을 참조한다.

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: reviews-destination
spec:
  host: reviews
  subsets:
    - name: v1
      labels:
        version: v1
    - name: v2
      labels:
        version: v2
```

다른 namespace를 가리킬 때는 `host: reviews.default.svc.cluster.local`처럼 **FQDN**을 사용한다.

## Timeout과 Retry

**Timeout**은 응답이 일정 시간 안에 오지 않으면 자동으로 실패 처리하여 장애 전파를 막는다.
Virtual Service의 `http.timeout`에 `3s`처럼 지정한다.

**Retry**는 일시적 연결 실패를 자동으로 재시도한다.
기본값은 25ms 간격으로 2회 재시도이며, 다음 필드로 조정한다.

| 필드 | 설명 | 예시 |
|------|------|------|
| `attempts` | 재시도 횟수 | `3` |
| `perTryTimeout` | 각 시도의 타임아웃 | `2s` |

```yaml
retries:
  attempts: 3
  perTryTimeout: 2s
```

## Fault Injection

Fault Injection은 의도적으로 오류를 발생시켜 회복성을 검증하는 테스트 기법이다.
두 가지 오류 유형을 지원한다.

- **Delay**: 지연 주입
- **Abort**: 특정 에러 코드로 요청 중단

```yaml
http:
- fault:
    delay:
      percentage:
        value: 70.0
      fixedDelay: 7s
  route:
  - destination:
      host: details
      subset: v1
```

Timeout 검증에도 자주 결합된다.
예를 들어 5초 지연을 주입하면 3초 Timeout이 걸린 서비스는 `upstream request timeout`을 반환한다.

## Circuit Breaking

Circuit Breaking은 **연쇄 장애(cascading failure)**를 방지하는 패턴이다.
응답하지 않는 서비스에 대한 요청을 즉시 실패 처리하여 큐가 쌓이는 것을 막는다.
Istio에서는 **Destination Rule**의 `trafficPolicy.connectionPool`로 설정한다.

```yaml
spec:
  host: productpage
  trafficPolicy:
    connectionPool:
      http:
        maxPendingRequests: 1
        maxRequestsPerConnection: 1
      tcp:
        maxConnections: 1
```

- `maxConnections`: 최대 TCP 연결 수
- `maxPendingRequests`: 대기 요청 최대 수
- `maxRequestsPerConnection`: 연결당 요청 최대 수

동시 접속 수가 한계를 넘으면 초과 요청이 거부되며, `h2load` 같은 도구로 부하를 걸어 확인할 수 있다.

## A/B Testing

A/B Testing은 서로 다른 버전으로 트래픽을 분산해 실제 데이터로 의사결정을 내리는 기법이다.
Virtual Service의 weight 라우팅으로 구현하며, v2 Pod 개수가 늘어도 분배 비율은 유지된다.
이는 Kubernetes 단독으로는 불가능한 세밀한 제어이며, header 기반 라우팅과 결합해 특정 사용자 그룹만 신규 버전으로 보낼 수 있다.

다음 편은 **Security** — mTLS, 인증, 인가, 인증서 관리를 다룬다.
