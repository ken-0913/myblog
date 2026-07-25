---
title: "ICA 시험 정리 (4) Security: mTLS, 인증, 인가, 인증서 관리"
date: 2026-07-16T08:30:00+09:00
draft: false
tags: ["Istio", "ICA", "Security", "mTLS", "AuthorizationPolicy"]
categories: ["자격시험"]
featuredImage: images/banners/istio-ica-04-security-49d67983.png
---

ICA 시험 정리 시리즈 네 번째 편이다.
Istio Security는 **Authentication(인증)**, **Authorization(인가)**, **mTLS**, **Certificate Management**로 구성된다.
시험에서 리소스 종류와 정책 적용 범위, mTLS 모드가 특히 자주 출제된다.

## 보안 아키텍처

핵심 컴포넌트는 **Istiod** 내부의 CA(Certification Authority)다.
CA는 인증서 유효성을 검증하고 CSR(Certificate Signing Request)을 승인·서명한다.
워크로드가 시작되면 Envoy proxy가 Istio agent에게 인증서와 키를 요청하여 통신이 처음부터 암호화·인증된다.

**Configuration API Server**는 인증·인가·보안 명명 정책을 Mesh 전체에 배포한다.
정책은 Sidecar, Ingress, Egress proxy 모두에 적용된다.
모든 proxy에 계층적으로 정책을 적용하는 이 방식이 **Defense-in-Depth(심층 방어)** 전략이다.

## Authentication (인증)

Istio는 두 가지 차원의 인증을 지원한다.

| 구분 | 대상 | 메커니즘 | 리소스 |
|------|------|----------|--------|
| 서비스 간 인증 | Service-to-Service | **mTLS** | `PeerAuthentication` |
| 최종 사용자 인증 | End-User | **JWT / OpenID Connect** | `RequestAuthentication` |

mTLS에서 각 서비스는 Istiod가 자동으로 관리하는 고유 ID(인증서/키 쌍)를 부여받는다.
End-User 인증은 JWT 검증 또는 Ory Hydra, Keycloak, Firebase, Google 같은 OpenID Connect 제공자를 사용한다.

### mTLS 모드

`PeerAuthentication`의 `mtls.mode`로 지정하며, 세 모드의 차이는 반드시 암기해야 한다.

| 모드 | 동작 | 사용 시나리오 |
|------|------|---------------|
| **STRICT** | mTLS 트래픽만 허용 | 프로덕션 보안 |
| **PERMISSIVE** | mTLS와 평문 모두 허용 | 마이그레이션 중 |
| **DISABLE** | mTLS 비활성화 | 트러블슈팅 |

### 정책 적용 범위

적용 범위는 우선순위가 높은 순서로 세 단계다.
좁은 범위부터 적용한 뒤 확장하는 것이 모범 사례다.

1. **Workload-specific**: `selector`로 특정 label 워크로드에만 적용
2. **Namespace-wide**: `selector`를 제거하면 해당 namespace 전체에 적용
3. **Mesh-wide**: 루트 namespace(`istio-system`)에 적용하면 Mesh 전체에 적용

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: "example-peer-policy"
  namespace: "book-info"
spec:
  selector:
    matchLabels:
      app: reviews
  mtls:
    mode: STRICT
```

## Authorization (인가)

인가는 inbound(**East-West**) 트래픽을 제어하여 서비스 간 통신을 보호한다.
Istio는 인가 로직을 Envoy proxy에 통합하므로 애플리케이션 코드를 수정하지 않는다.
리소스는 `AuthorizationPolicy`이며 네 가지 액션을 지원한다.

| 액션 | 설명 |
|------|------|
| **ALLOW** | 일치하면 허용 |
| **DENY** | 일치하면 거부 |
| **CUSTOM** | 외부 인가 서비스 호출 |
| **AUDIT** | 로그만 기록 (허용·차단 아님) |

정책 규칙은 요청자 조건인 `from`, 대상 조건인 `to`, 추가 조건인 `when`으로 구성된다.

```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: "details-viewer"
  namespace: default
spec:
  selector:
    matchLabels:
      app: details
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/default/sa/bookinfo-productpage"]
    to:
    - operation:
        methods: ["GET"]
```

`source.principals`는 Service Account를 식별하며 형식은 다음과 같다.

```
cluster.local/ns/<namespace>/sa/<service-account>
```

### 시험에서 자주 틀리는 함정

- 빈 `spec: {}` 정책은 namespace의 **모든 트래픽을 거부**한다(deny-all).
- 첫 ALLOW 정책이 적용되면, 명시적으로 허용되지 않은 트래픽은 **기본 거부**된다.
- `selector` 없는 `PeerAuthentication`은 namespace 전체에 적용된다.
- `istio-system`의 정책은 Mesh 전체에 영향을 준다.

## Certificate Management

인증서 발급은 7단계로 진행되며, 흐름 자체가 시험에 나온다.

```
1. Istio Agent: 개인 키 + CSR 생성
2. Agent → Istiod: CSR + 자격증명 전송
3. Istiod CA: 자격증명 검증
4. Istiod CA: CSR 서명 + 인증서 발급
5. Agent → Envoy: 서명된 인증서 + 개인 키 전달
6. Agent: 인증서 만료 모니터링
7. 주기적 반복으로 자동 회전
```

한 문장으로 요약하면 다음과 같다.

```
Istio Agent → CSR 생성 → Istiod CA 검증 → 서명 → Envoy 전달 → 자동 회전
```

프로덕션에서는 root 인증서를 직접 쓰지 않고 **Intermediate(중간) CA**를 두어 보안과 폐기 용이성을 확보한다.
인증서 체인은 `Root CA → Intermediate CA → Workload Certificate` 구조이며, HashiCorp Vault 같은 외부 CA 통합도 고려된다.

## 핵심 요약

Istio Security의 4대 축은 인증(누구인가), 인가(무엇을 할 수 있는가), mTLS(통신은 안전한가), 인증서 관리(신뢰는 어떻게 보장되는가)다.
리소스는 `PeerAuthentication`(mTLS), `RequestAuthentication`(JWT), `AuthorizationPolicy`(인가) 세 가지를 구분해서 기억한다.

다음 편은 마지막으로 **Observability** — Prometheus, Grafana, Jaeger, Kiali를 다룬다.
