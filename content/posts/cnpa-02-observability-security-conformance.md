---
title: "CNPA 시험 정리 (2) Observability & Security — OpenTelemetry, mTLS, 정책 엔진, SLSA"
date: 2026-07-15T08:00:00+09:00
draft: false
tags: ["CNPA", "Observability", "Security", "OpenTelemetry", "CNCF"]
categories: ["자격시험"]
---

이번 편은 **Domain 2: Platform Observability, Security, and Conformance (20%)** 를 정리한다.
핵심 메시지는 관측성과 보안이 사후 추가가 아니라 **처음부터 내장(built-in, not an afterthought)** 되어야 한다는 것이다.
반복 철학은 **Zero Trust, Shift Left, Least Privilege(최소 권한)** 다.

## 관측성 기초 (Observability Fundamentals)

전통적 **Monitoring**은 **무엇이(what)** 고장났는지 보여준다.
**Observability**는 **왜(why)** 고장났는지 보여준다.

3대 기둥(Three Pillars)은 다음과 같이 구분한다.

| 신호 | 역할 | 핵심 특징 |
|------|------|----------|
| **Metrics** | 숫자·추세 | Counter(감소 불가), Gauge(증감), Histogram(분포), Summary(백분위) |
| **Logs** | 상태 변화(state changes) 기록 | 구조화 로깅 + 상관 ID(trace ID) |
| **Traces** | 요청의 end-to-end 흐름 | span 단위로 지연·병목 추적 |

시험은 "어떤 신호를 써야 하는가"를 자주 묻는다.
숫자 추세는 metrics, 상태 변화는 logs, end-to-end 흐름은 traces다.

### Prometheus와 OpenTelemetry

**Prometheus**는 Kubernetes 기반 플랫폼의 사실상 표준 메트릭 도구이며 **Pull 모델**로 메트릭을 scrape한다.
단명(short-lived) 애플리케이션은 scrape할 수 없으므로 **Push Gateway**를 사용한다.

**OpenTelemetry(OTel)** 는 시험 전반에 등장하는 최중요 개념이다.
**벤더 중립(vendor-neutral) 통합 계측 표준** 으로, auto-instrumentation과 **OTel Collector**를 통해 코드 변경 없이 metrics·logs·traces를 주입한다.

### SLA / SLO / SLI / Error Budget

- **SLA**(Service Level Agreement): 비즈니스 계약 — 상위 목표 문서
- **SLO**(Service Level Objective): 지켜야 하는 수치 경계
- **SLI**(Service Level Indicator): 실제 측정 지표
- **Error Budget**: 기능 속도와 신뢰성의 균형 도구

## 안전한 서비스 통신 (Secure Service Communication)

**Zero Trust**는 경계 방어가 아니라 **서비스 신원(service identity)** 기반으로 모든 상호작용을 명시적으로 검증한다.
**Service Mesh**는 서비스 간(east-west) 통신을 담당하는 전용 인프라 레이어로, 애플리케이션 코드 변경 없이 동작한다.

Service Mesh는 **Data plane**(사이드카 프록시)과 **Control plane**(설정·인증서 배포)으로 나뉜다.

### mTLS (Mutual TLS)

표준 TLS는 서버만 인증서를 제시한다.
**mTLS는 클라이언트와 서버 양쪽이 인증서를 교환·검증** 하여 상호 신원을 확인하고 전송 중 암호화를 제공한다.

주의할 점은 **eBPF는 인증서 관리를 하지 않는다**는 것이다(서비스 메시가 담당).

| 제품 | 특징 |
|------|------|
| **Istio** | 기능 풍부, 고급 트래픽 관리 |
| **Linkerd** | 경량·단순·고성능(Rust) |
| **Envoy** | 많은 메시의 기반 프록시 |
| **Cilium** | eBPF 기반 CNI |

## 네트워킹과 Gateway API

**East-West**는 클러스터 내부 트래픽, **North-South**는 외부 노출 트래픽이다.
서비스 디스커버리는 **CoreDNS**가 자동 처리한다.

전통 Ingress는 canary 미지원과 벤더별 어노테이션 문제가 있다.
**Gateway API**는 역할 기반(GatewayClass → Gateway → HTTPRoute)이며, 트래픽 분할·헤더 라우팅을 벤더 중립적으로 지원한다.

## 정책 엔진 (Policy Engines)

**Policy as Code**는 보안 규칙을 선언적으로 정의·버전 관리하며, **Shift Left**로 결함을 상류에서 차단한다.
3대 정책 엔진은 다음과 같이 암기한다.

| 엔진 | 언어 | 특징 |
|------|------|------|
| **OPA** | **Rego** | 범용 정책 엔진 — K8s 외에서도 사용 가능 |
| **Gatekeeper** | Rego | OPA의 Kubernetes 전용 구현 |
| **Kyverno** | **YAML** | Kubernetes-native, 새 언어 불필요 |

**Validation** 정책은 리소스를 허용/거부만 하고, **Mutation** 정책은 리소스를 수정한다.
일반적으로 Kyverno로 시작해 규모가 커지면 OPA/Gatekeeper로 이동한다.

## Kubernetes 보안 필수사항

**RBAC**는 Subject(user/ServiceAccount) + Role(권한) + RoleBinding(연결)으로 구성된다.
**ServiceAccount**는 파드가 실행되는 신원이며, **Least Privilege** 원칙을 적용한다.

Admission Controller는 **Mutating → Validating 순서**로 요청을 가로챈다.
**PSP(Pod Security Policy)는 deprecated**되었고 **Pod Security Admission**이 대체한다.

시크릿 관리는 시험에 확정적으로 출제된다.
**Kubernetes Secrets는 base64 인코딩(encoding)일 뿐 암호화(encryption)가 아니다.**
etcd encryption at rest를 켜거나 Vault, Sealed Secrets 같은 외부 스토어를 사용해야 한다.

## CI/CD 파이프라인 보안

**SLSA**(Supply chain Levels for Software Artifacts, "살사")는 공급망 보안의 사실상 표준이다.
**Attestation은 암호학적 증명(cryptographic proof)** 이다.

| 레벨 | 의미 |
|------|------|
| Level 1 | 기본 attestation (서명된 불변 기록) |
| Level 2 | 빌드 환경(build environment)의 신뢰 검증 |
| Level 3 | 소스 코드 보호 (브랜치 보호, 서명된 커밋) |
| Level 4 | Hermetic builds (완전 격리·재현 가능) |

도구-역할 매칭도 자주 출제된다.

- 취약점 스캔: **Trivy**
- **SBOM** 생성: **Syft** (형식: SPDX=Linux Foundation, CycloneDX=OWASP)
- 서명·검증: **Sigstore + Cosign**
- 빌드 provenance: **Tekton Chains**
- 시크릿 유출 탐지: **TruffleHog, Gitleaks**
- IaC 스캔: **Checkov**

시크릿은 **빌드 타임이 아니라 배포/런타임(deploy/runtime)** 에 주입하며, Git이나 이미지에 절대 포함하지 않는다.

## 예상 문제 (영어 + 한글 해석)

**Q1.** Which observability signal should you use to track the end-to-end flow of a request across microservices?
(마이크로서비스 전반의 요청 흐름을 추적하려면 어떤 신호를 사용해야 하는가?)
→ **Traces** ✅ — metrics는 수치 추세, logs는 상태 변화.

**Q2.** A short-lived batch job cannot be scraped by Prometheus. What should it use?
(단명 배치 작업은 Prometheus가 scrape할 수 없다. 무엇을 사용해야 하는가?)
→ **Prometheus Push Gateway** ✅

**Q3.** How are Kubernetes Secrets stored by default?
(Kubernetes Secret은 기본적으로 어떻게 저장되는가?)
→ **Base64로 인코딩될 뿐 암호화되지 않는다.** ✅

**Q4.** Which policy engine uses the Rego language?
(Rego 언어를 사용하는 정책 엔진은?)
→ **OPA (Open Policy Agent)** ✅ — Kyverno는 YAML을 사용한다.

**Q5.** In mutual TLS, what distinguishes it from standard TLS?
(mTLS가 표준 TLS와 다른 점은?)
→ **클라이언트와 서버 모두 인증서를 교환하고 서로 검증한다.** ✅

**Q6.** Which SLSA level requires hermetic, fully reproducible builds?
(밀폐되고 완전히 재현 가능한 빌드를 요구하는 SLSA 레벨은?)
→ **Level 4** ✅

**Q7.** What replaced the deprecated Pod Security Policy (PSP)?
(폐기된 PSP를 대체한 것은?)
→ **Pod Security Admission (Pod Security Standards)** ✅

**Q8.** A team wants policy enforcement without learning a new language. Which tool fits best?
(새 언어 학습 없이 정책을 시행하려는 팀에 가장 적합한 도구는?)
→ **Kyverno** (YAML 기반) ✅

**Q9.** When should secrets be injected into an application?
(시크릿은 언제 애플리케이션에 주입해야 하는가?)
→ **배포/런타임 시점** — Git이나 이미지에 포함 금지. ✅

## 핵심 요약

Observability는 why를 답하고, OpenTelemetry는 벤더 중립 계측 표준이다.
mTLS는 양방향 인증서 교환이며, K8s Secrets는 base64 인코딩일 뿐임을 기억한다.
정책 엔진(OPA=Rego, Kyverno=YAML)과 SLSA 레벨, 공급망 도구 매칭은 반드시 정리한다.

다음 편은 **Domain 3: Continuous Delivery** — 배포 전략, Argo CD, 인시던트 대응을 다룬다.
