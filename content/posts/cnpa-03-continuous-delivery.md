---
title: "CNPA 시험 정리 (3) Continuous Delivery — 배포 전략, GitOps, Argo CD, 인시던트 대응"
date: 2026-07-16T08:00:00+09:00
draft: false
tags: ["CNPA", "Continuous Delivery", "GitOps", "Argo CD", "CNCF"]
categories: ["자격시험"]
featuredImage: images/banners/cnpa-03-continuous-delivery-91a293f7.png
---

이번 편은 **Domain 3: Continuous Delivery & Platform Engineering (16%)** 를 정리한다.
핵심은 플랫폼 엔지니어가 CI/CD를 직접 구현하는 것이 아니라 개발팀에게 **CI/CD를 서비스로(as a Service)** 제공한다는 것이다.
4대 요구사항은 속도와 안전의 균형, 내장 보안, 관측성, 일관성이다.

## 파이프라인 아키텍처

파이프라인은 **Commit → Build → Test → Security Scan → Package → Deploy → Post-deployment Validation** 순서로 진행된다.
각 단계는 **품질 게이트(quality gate)** 이며, 어느 단계든 실패하면 파이프라인을 중지하는 **Fail Fast** 원칙을 따른다.

테스트 피라미드는 아래로 갈수록 많고 빠르다.

| 테스트 | 특징 |
|--------|------|
| **Unit** | 가장 많고 빠름, 최우선 실행 |
| **Integration** | 서비스 간 검증 |
| **End-to-end** | 사용자 여정 전체, 후반 실행 |
| **UI** | 가장 느리고 적음 |

## 아티팩트 관리

아티팩트는 코드의 **불변(immutable) 시점 스냅샷** 이며, 동일 바이너리가 dev→QA→staging→prod로 이동한다.
버전은 절대 덮어쓰지 않고 전진만 한다(10→11→12).

**Harbor**는 CNCF의 클라우드 네이티브 컨테이너 레지스트리다.
기출 유형으로 "cloud native artifact registry는?"에 대해 Harbor가 정답이며, containerd(런타임)·Notary(서명)·OCI(스펙)는 오답 보기다.

## 지속적 전달 vs 지속적 배포

이 구분은 반드시 암기한다.

| 구분 | Continuous Delivery | Continuous Deployment |
|------|--------------------|-----------------------|
| 범위 | 프로덕션 **직전까지** 자동 | **프로덕션까지 전부** 자동 |
| 게이트 | 사람의 승인(human gate) | 승인 없음 |
| 요건 | 포괄적 테스트 | 매우 높은 테스트 커버리지 |

**롤백이 배포보다 중요** 하다는 점이 반복 강조된다.
백업보다 복원이 중요하듯, 롤백 시스템이 견고하면 배포도 견고하다.

## 배포 유형과 전략

이 부분은 시나리오 매칭 문제로 반드시 출제된다.
4대 핵심 개념은 deployment target, traffic routing, health checking, **rollback(가장 중요)** 이다.

| 전략 | 방식 | 특징 |
|------|------|------|
| **Rolling** | 인스턴스를 하나씩 교체 (K8s 기본값) | 추가 인프라 불필요, 롤백 느림 |
| **Blue/Green** | 환경 전체 복제 후 전환 | 즉시 롤백, **2배 용량 비용** |
| **Canary** | 소량 트래픽만 신버전 | 위험 최소화, **Argo Rollouts**가 대표 도구 |
| **Recreate** | 전부 중지 후 재배포 | 가장 단순, 짧은 다운타임 |

**A/B 테스트는 배포 전략이 아니라 기능 관리(feature management)** 다.
**Feature Flag**는 배포(deploy)와 릴리스(release)를 분리하여, 문제 시 재배포 없이 플래그만 끈다.

## GitOps와 Argo CD

**Git 리포지토리가 단일 진실 공급원(Single Source of Truth)** 이다.
전통 CI/CD는 프로덕션에 push하지만, GitOps는 클러스터 내 에이전트가 원하는 상태를 지속적으로 **pull**한다.

**Reconciliation loop(조정 루프)** 는 실제 상태와 원하는 상태를 지속 비교하여 드리프트를 자동 수정한다.

**Argo CD**는 CNCF graduated 프로젝트이자 업계 표준 GitOps operator다.
구성 요소는 API Server, Repository Server, **Application Controller(조정 루프)** 다.
보안상 클러스터 직접 접근이 불필요하며, **롤백은 git revert** 후 자동 sync로 이뤄진다.

### 환경별 구성: Kustomize vs Helm

- **Kustomize**: base + overlay(패치) 모델
- **Helm**: 템플릿 + values 파일 모델

**Ephemeral 환경** 은 PR이 열리면 테스트 네임스페이스를 자동 생성하고 테스트 후 정리한다.
자동 승격(promotion)이 선호되며, 수동 게이트는 중요 배포의 인적 감독용이다.

## 인시던트 대응

**MTTR(Mean Time To Recovery)** 은 Detection → Response → Resolution → Recovery 4단계로 구성된다.
심각도(severity) 기준은 **비즈니스가 결정** 한다(Sev1 <15분 등).

인시던트 대응 흐름은 **Detect → Contain → Investigate → Remediate → Learn** 이다.
**Runbook**은 증상→조사→수정→검증의 플레이북이며, 자동화 수준을 Level 1(수동)에서 Level 3(자동)로 올리는 것이 목표다.

**Blameless Postmortem(비난 없는 사후 분석)** 은 개인이 아닌 시스템에 초점을 맞춘다.
온콜 도구(PagerDuty, Opsgenie)는 상용이며 CNCF 공식 온콜 도구는 없다.
**KEDA**는 CPU/메모리를 넘어 이벤트 기반 오토스케일링을 제공한다.

## 예상 문제 (영어 + 한글 해석)

**Q1.** What is the key difference between continuous delivery and continuous deployment?
(지속적 전달과 지속적 배포의 핵심 차이는?)
→ Delivery는 프로덕션 직전까지 자동화하고 **사람의 승인 게이트**가 있으며, Deployment는 **프로덕션까지 완전 자동** 이다. ✅

**Q2.** Which deployment strategy requires double the infrastructure but allows instant rollback?
(인프라가 2배 필요하지만 즉시 롤백이 가능한 배포 전략은?)
→ **Blue/Green** ✅

**Q3.** Which CNCF project provides advanced canary deployment management with automated analysis and rollback?
(자동 분석·롤백을 갖춘 고급 canary 배포 관리를 제공하는 CNCF 프로젝트는?)
→ **Argo Rollouts** ✅

**Q4.** Which of the following is a cloud native artifact registry? (containerd / Notary / Harbor / OCI)
(다음 중 클라우드 네이티브 아티팩트 레지스트리는?)
→ **Harbor** ✅

**Q5.** In GitOps, why is the pull-based model preferred over push-based?
(GitOps에서 pull 기반 모델이 push 기반보다 선호되는 이유는?)
→ 클러스터 내 에이전트가 원하는 상태를 지속 pull·조정하므로 외부에서 클러스터 직접 접근이 불필요하다. ✅

**Q6.** A developer opens a pull request and needs a realistic test environment without permanent cost. What should the platform provide?
(개발자가 PR을 열고 영구 비용 없이 현실적인 테스트 환경이 필요하다. 플랫폼은 무엇을 제공해야 하는가?)
→ **Ephemeral environment** ✅

**Q7.** Which tool uses a base + overlay model for environment-specific configuration?
(환경별 구성에 base + overlay 모델을 사용하는 도구는?)
→ **Kustomize** ✅ — Helm은 템플릿 + values.

**Q8.** What does MTTR measure and what are its phases?
(MTTR은 무엇을 측정하며 단계는?)
→ 평균 복구 시간 — **Detection, Response, Resolution, Recovery** ✅

**Q9.** Which CNCF tool enables event-driven autoscaling beyond CPU and memory?
(CPU·메모리를 넘어 이벤트 기반 오토스케일링을 가능하게 하는 CNCF 도구는?)
→ **KEDA** ✅

## 핵심 요약

Continuous Delivery는 사람 승인 게이트가 있고 Deployment는 완전 자동이다.
배포 전략(Rolling·Blue/Green·Canary·Recreate)과 Argo CD, MTTR 4단계는 반드시 정리한다.

다음 편은 **Domain 4: Platform APIs** — 조정 루프, CRD, Operator, 오토스케일링을 다룬다.
