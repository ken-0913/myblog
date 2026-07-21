---
title: "CNPA 시험 정리 (5) IDP & Developer Experience — Backstage, 서비스 카탈로그, AIOps"
date: 2026-07-18T08:00:00+09:00
draft: false
tags: ["CNPA", "Backstage", "Developer Experience", "AIOps", "CNCF"]
categories: ["자격시험"]
---

이번 편은 **Domain 5: IDPs and Developer Experience (8%)** 를 정리한다.
핵심 메시지는 플랫폼 성공의 최고 지표가 **자발적 채택(voluntary adoption)** 이라는 것이다.
개발자의 **인지 부하(cognitive load)를 낮추는** 단순·발견 가능·일관된 인터페이스가 IDP의 핵심이다.

## 단순화된 접근 (Simplified Access)

개발자는 하루 15개 이상의 도구를 전환하며, 플랫폼이 이 부담을 줄여야 한다.
복잡하면 개발자는 채택하지 않으므로, **채택이 곧 플랫폼의 생존** 이다.

CLI 설계의 핵심 원칙은 **Web UI, CLI, IDE 플러그인이 모두 동일한 기반 API를 호출** 한다는 것이다.
이는 일관성과 확장성을 보장한다.

**템플릿(Templates)** 은 시니어 엔지니어의 전문 지식을 코드화(codify)해 전파한다.
파라미터는 검증되고 스코프가 제한되어야 한다(replicas 1~10, 환경은 dev/staging/production만).

## 서비스 카탈로그

마이크로서비스가 150개 이상이면 발견(discovery)이 혼란스러워진다.
**발견이 나쁘면 채택이 떨어지고 비인가 대안(unauthorized alternatives, shadow IT)이 증가** 한다는 것이 시험 신호다.

**서비스 카탈로그**는 동적·권위 있는(authoritative) 목록으로, 서비스가 온라인일 때 자동 등록된다.
메타데이터로 SLA, 의존성, 담당자, OpenAPI 명세를 포함한다.

셀프서비스 원칙은 **일상적 요청의 인간 병목을 제거** 하고 예외 상황에만 인간 감독을 유지하는 것이다.
포털은 오케스트레이션 레이어로서 하나의 인터페이스가 K8s, Argo CD, Crossplane 등 다중 백엔드를 호출한다.

## 개발자 포털: Backstage

이 부분은 시험에 확정적으로 출제된다.
**Backstage는 CNCF incubating 프로젝트이자 Spotify가 개발** 한 개발자 포털의 사실상 업계 표준 프레임워크다.

흩어진 문서와 발견성 문제를 해결하는 **"Single pane of glass"** 를 제공한다.
4대 핵심 기능은 반드시 암기한다.

| 기능 | 내용 |
|------|------|
| **Software Catalog** | 통합 서비스 레지스트리 — 소유권·메타데이터·의존성. lifecycle 필드(experimental/production/deprecated) |
| **Software Templates (Scaffolding)** | 원클릭 서비스 생성 — 리포·파이프라인·보안 설정 사전 구성 |
| **TechDocs** | 마크다운 기반 **docs-as-code** 자동 게시 |
| **Plugin Architecture** | REST/GraphQL API가 있는 어떤 도구든 통합 |

도입 전략은 **작게 시작** 하여 점진 확대하는 것이며, 기존 도구를 대체하지 않고 통합한다.

## 플랫폼 운영의 AI/ML

**AIOps**는 기존 IT 운영에 AI를 주입하는 것이다(Artificial Intelligence for IT Operations).
MLOps(ML 워크로드 운영), LLMOps(LLM 운영)와 혼동하지 않는다.

주요 적용 영역은 다음과 같다.

- **이상 탐지(Anomaly Detection)**: 시계열·패턴 학습으로 오탐 감소
- **근본 원인 분석**: **K8sGPT** — LLM으로 클러스터 문제를 진단·설명
- **예측 스케일링**: **KEDA의 external scaler로 ML 예측 연동**
- **비용 인텔리전스**: 유휴 환경 축소, spot 가격 예측
- **지능형 알림**: 실제 문제만 페이징하여 알림 피로 감소

핵심 관점은 AI가 인간 역량을 **대체가 아니라 강화(enhance, not replace)** 한다는 것이다.
목표는 반응형(reactive)에서 선제적·자가 최적화(proactive, self-optimizing) 플랫폼으로의 전환이다.

## 예상 문제 (영어 + 한글 해석)

**Q1.** Which CNCF project is the industry-standard framework for building developer portals?
(개발자 포털 구축의 업계 표준 CNCF 프레임워크는?)
→ **Backstage** (Spotify 개발, CNCF incubating) ✅

**Q2.** What are the four core capabilities of Backstage?
(Backstage의 4대 핵심 기능은?)
→ **Software Catalog, Software Templates(Scaffolding), TechDocs, Plugin Architecture** ✅

**Q3.** Developers can't find existing platform services and start building their own unauthorized alternatives. What platform capability is missing?
(개발자들이 기존 서비스를 찾지 못해 비인가 대안을 만들기 시작한다. 부족한 플랫폼 역량은?)
→ **Service discovery / Service catalog** (발견성) ✅

**Q4.** Why should the web portal, CLI, and IDE plugins all call the same APIs?
(웹 포털, CLI, IDE 플러그인이 모두 같은 API를 호출해야 하는 이유는?)
→ **일관성(consistency) 보장과 쉬운 확장** — 인터페이스가 달라도 동작·거버넌스가 동일하다. ✅

**Q5.** What does AIOps mean?
(AIOps의 의미는?)
→ **기존 IT 운영에 AI를 적용** 하는 것 — MLOps(ML 운영)와 구분한다. ✅

**Q6.** Which tool uses LLMs to diagnose and explain Kubernetes cluster issues?
(LLM으로 Kubernetes 클러스터 문제를 진단·설명하는 도구는?)
→ **K8sGPT** ✅

**Q7.** In Backstage's catalog, what does the lifecycle field indicate?
(Backstage 카탈로그의 lifecycle 필드는 무엇을 나타내는가?)
→ 서비스의 상태 — **experimental / production / deprecated** 등. ✅

**Q8.** What is the platform engineering principle for approval workflows in self-service portals?
(셀프서비스 포털의 승인 워크플로에 대한 플랫폼 엔지니어링 원칙은?)
→ **일상적·표준 요청은 자동화하고, 인간 감독은 예외 상황에만 유지** 한다. ✅

## 핵심 요약

DX가 플랫폼의 생존을 결정하며, UI·CLI·IDE는 같은 API를 호출한다.
Backstage(CNCF incubating, Spotify)의 4대 기능과 AIOps 정의, K8sGPT는 반드시 정리한다.

다음 편은 마지막으로 **Domain 6: Measuring your Platform** — DORA 메트릭, 성숙도 모델을 다룬다.
