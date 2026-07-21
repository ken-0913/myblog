---
title: "CNPA 시험 정리 (1) Platform Engineering Core Fundamentals — 선언적 관리, GitOps, 8대 역량"
date: 2026-07-14T08:00:00+09:00
draft: false
tags: ["CNPA", "Platform Engineering", "Kubernetes", "GitOps", "CNCF"]
categories: ["자격시험"]
---

CNPA(Certified Cloud Native Platform Engineering Associate)는 CNCF가 주관하는 플랫폼 엔지니어링 자격 시험이다.
시험은 영어로 출제되므로, 이 시리즈는 핵심 개념을 정리하고 예상 문제를 **영어 원문 + 한글 해석** 형태로 제시한다.
첫 편은 시험 비중이 가장 큰 **Domain 1: Platform Engineering Core Fundamentals (36%)** 를 다룬다.

## 선언적 vs 명령적 (Declarative vs Imperative)

**Imperative(명령적)** 는 레시피처럼 단계별로 **How**를 지시한다.
**Declarative(선언적)** 는 메뉴 주문처럼 원하는 결과, 즉 **desired state(원하는 상태)** 만 선언한다.

플랫폼 엔지니어링은 **선언적 접근을 선호(preferred)** 한다.
선언된 상태는 **control loop(제어 루프)** 가 감시하며 실제 상태를 원하는 상태로 **reconcile(조정)** 한다.

| 구분 | Imperative | Declarative |
|------|-----------|-------------|
| 초점 | How (어떻게) | What (원하는 상태) |
| 재실행 | 중복 생성 위험 | 멱등성(idempotency) |
| 예시 | `kubectl create deployment` | Kubernetes YAML, Terraform HCL |
| 장점 | 직접 제어, 빠른 실험 | 버전 관리, 반복 가능, 감사 가능 |

Imperative가 여전히 유효한 경우는 **디버깅, 긴급 핫픽스(emergency hotfix), 긴급 스케일링, 실험** 정도다.
단, 이후 반드시 선언적 정의로 반영(backfill)해야 한다.

## 가변 vs 불변 인프라 (Mutable vs Immutable)

**Mutable(가변)** 은 서버에 SSH로 접속해 in-place로 패치한다.
**Immutable(불변)** 은 새 이미지로 전체를 교체(replace)한다.

**Immutable이 플랫폼 엔지니어링의 기본값(default)** 이다.
변경이 필요하면 아티팩트가 아니라 아티팩트를 만든 **upstream 시스템(Dockerfile, Packer golden image)** 을 수정한 뒤 재배포한다.

컨테이너와 Serverless(Lambda 등)는 태생적으로 immutable하다.
트러블슈팅 중 수동 변경은 반드시 immutable 파이프라인에 backfill해야 하며, 핵심은 **의도성(intentionality)과 거버넌스**다.

## DevOps 실천법과 Three Ways

플랫폼 엔지니어링은 DevOps를 **대체(replace)하는 것이 아니라 확장(extend)·확산(scale)** 시킨다.
이는 시험에 자주 등장하는 문장이다.

Gene Kim의 **The Three Ways**는 다음과 같다.

1. **Flow(흐름)**: 커밋에서 프로덕션까지 마찰 없는 워크플로 최적화
2. **Feedback(피드백)**: 모든 단계에서 짧고 빠른 피드백 루프
3. **Continuous Experimentation & Learning(지속적 실험과 학습)**: 실험과 개선의 반복

**Small Batches(작은 배치)** 는 변경 규모를 줄여 실패의 **blast radius(폭발 반경)** 를 축소한다.
문화가 도구를 이기며, 채택은 강제(mandate)가 아니라 가치로 유도한다.

## 애플리케이션 환경 (Application Environments)

환경은 **Development → Testing/QA → Staging → Production** 계층으로 구성된다.
각 환경은 **논리적으로 동일(logically similar)** 하며 용량(capacity)만 다르다.

**Staging**은 프로덕션과 거의 동일한 복사본으로, **ephemeral(단명)** 로 운영하는 것이 권장된다.
IaC 없이는 환경 복제가 불가능하므로, 선언적이고 버전 관리되는 템플릿이 필수다.

## 제품으로서의 플랫폼 (Platform as a Product)

플랫폼은 "구축 후 방치"가 아니라 지속 투자하는 전략적 **제품(product)** 으로 다뤄야 한다.
내부 고객을 만족(delight)시키는 것이 목표다.

4대 KPI는 다음과 같이 암기한다.

| KPI | 의미 |
|-----|------|
| **Velocity** | 개발자 속도 (mean time to production) |
| **Reliability** | 신뢰성 (가동률) |
| **Adoption** | 채택률 — evangelism으로 견인, mandate 금지 |
| **Satisfaction** | 만족도 — **NPS**(Net Promoter Score) |

## 플랫폼 아키텍처의 8대 핵심 역량 (8 Essential Capabilities)

이 부분은 시험에서 최소 1문제 이상 출제되는 최중요 항목이다.
개별 요소가 아니라 **함께 작동**해야 한다는 점이 핵심이다.

1. **API-Driven Design**: UI·CLI·자동화가 동일한 API 엔드포인트를 사용
2. **Declarative Model**: 매니페스트를 Git에 저장 (Policy/IaC/App as Code)
3. **Automation & Orchestration**: CI/CD, 이벤트 기반 무인 운영
4. **Self-Service**: 티켓 없음, 대기 없음, 수동 설정 없음
5. **Observability**: Traces, Logs, Metrics
6. **Security & Compliance**: 사후 추가가 아닌 내재화
7. **Extensibility**: 플러그인, CRD, webhook 확장
8. **Modularity**: 명확한 경계와 테넌트 격리

## 지속적 통합과 GitOps

CI 파이프라인은 **아티팩트 생성 → 품질 보증(QA) → 배포 준비** 순서로 진행된다.
아티팩트는 고유 태그/SHA 해시로 레지스트리에 push되어 영구히 동일한 이미지가 된다.

**GitOps의 4대 핵심 원칙**은 반드시 암기한다.

1. **Declarative** — 원하는 상태를 선언적으로 정의
2. **Automated Reconciliation** — 자동 조정 루프
3. **Pull-based Deployment** — push가 아닌 pull 기반
4. **Complete Audit Trail** — 완전한 감사 추적

GitOps 컨트롤러로는 **Argo CD, Flux, Rancher Fleet**가 있다.
GitOps 용어는 **Weaveworks가 2017년에 명명**했고, Backstage는 **Spotify**, Three Ways는 **Gene Kim**이 만들었다.

### 배포 전략 (Deployment Strategies)

| 전략 | 방식 |
|------|------|
| **Canary** | 소량 트래픽(1~5%)을 새 버전으로 보낸 뒤 확대 |
| **Linear** | 일정 시간마다 일정 비율씩 증가 |
| **Blue/Green** | 구버전(blue)을 유지한 채 신버전(green)으로 전환 — 즉시 롤백 가능 |
| **A/B, Shadow** | 일부 사용자/복제 트래픽으로 검증 |

## 예상 문제 (영어 + 한글 해석)

**Q1.** Which approach is preferred in modern platform engineering for managing resources?
(현대 플랫폼 엔지니어링에서 리소스 관리에 선호되는 접근 방식은?)
→ **Declarative definitions stored in Git** ✅ — Imperative는 troubleshooting 용도.

**Q2.** A container in production has a bug. Following immutable infrastructure principles, what should you do?
(프로덕션 컨테이너에 버그가 있다. 불변 인프라 원칙에 따라 무엇을 해야 하는가?)
→ **Fix the upstream source/image and redeploy** — 컨테이너를 직접 수정하지 않고 upstream을 고쳐 재배포한다. ✅

**Q3.** What are the "Three Ways" of DevOps?
(DevOps의 "Three Ways"는?)
→ **Flow, Feedback, Continuous Experimentation and Learning** ✅

**Q4.** Which is NOT one of the four GitOps principles?
(GitOps 4대 원칙이 아닌 것은?)
→ **Push-based deployment** ✅ — 원칙은 pull-based다.

**Q5.** Which deployment strategy keeps the old environment fully running for instant rollback?
(구버전 환경을 그대로 유지해 즉시 롤백이 가능한 배포 전략은?)
→ **Blue/Green deployment** ✅

**Q6.** Why should platform adoption be driven by evangelism rather than mandate?
(플랫폼 채택이 강제가 아닌 전도로 이뤄져야 하는 이유는?)
→ 강제 시 저항(resistance)이 발생하며, 신뢰·평판·가치가 채택과 NPS를 견인한다. ✅

**Q7.** Which tool defines CI pipelines as Kubernetes Custom Resource Definitions (CRDs)?
(CI 파이프라인을 Kubernetes CRD로 정의하는 도구는?)
→ **Tekton** ✅

## 핵심 요약

Declarative는 선호되고 Immutable은 기본값이며, 플랫폼 엔지니어링은 DevOps의 확장이다.
8대 역량과 GitOps 4원칙, 4대 KPI(Velocity·Reliability·Adoption·Satisfaction)는 반드시 암기한다.

다음 편은 **Domain 2: Observability, Security, and Conformance** — OpenTelemetry, mTLS, 정책 엔진, SLSA를 다룬다.
