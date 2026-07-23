---
title: "CNPA 시험 정리 (6) Measuring your Platform — DORA 메트릭, 성숙도 모델"
date: 2026-07-19T08:00:00+09:00
draft: false
tags: ["CNPA", "DORA", "Platform Maturity", "SRE", "CNCF"]
categories: ["자격시험"]
featuredImage: images/banners/cnpa-06-measuring-your-platform-6156a41f.png
---

이 시리즈의 마지막 편은 **Domain 6: Measuring your Platform (8%)** 를 정리한다.
핵심 메시지는 측정이 플랫폼을 **비용 센터(cost center)에서 전략적 조력자(strategic enabler)로** 전환한다는 것이다.
감이 아니라 **데이터 기반(data-driven)** 플랫폼 엔지니어링을 지향한다.

## 측정의 3대 기둥

측정은 세 축으로 이뤄진다.

- **Business Impact**: 속도, 품질, 혁신
- **Developer Experience**: 생산성, 만족도, 채택률
- **Operational Efficiency**: 비용 최적화, 인시던트 감소, 인프라 활용률

개발자 만족도 지표로는 **NPS**, 채택률, **Time to First Success/Deploy**, 지원 요청 빈도가 있다.
측정 원칙은 **자동 수집 필수** 이며, 수동 수집은 실패한다.

## DORA 메트릭

반드시 암기해야 하는 최중요 항목이다.
출처는 Google **DORA**(DevOps Research and Assessment)이며 「Accelerate」에서 정립됐다.

4대 메트릭은 속도 2개 + 안정성 2개로 구성된다.

| 분류 | 메트릭 | 의미 |
|------|--------|------|
| **속도** | **Deployment Frequency** | 프로덕션 배포 빈도 |
| **속도** | **Lead Time for Changes** | 커밋 → 프로덕션 소요 시간 |
| **안정성** | **Change Failure Rate** | 배포 중 서비스 저하 비율 |
| **안정성** | **MTTR** | 장애 감지→복구 평균 시간 |

성과 등급은 **Elite / High / Medium / Low** 로 분류된다.
Elite는 하루 여러 번 배포, 리드 타임 <1시간, 실패율 <15%, MTTR <1시간이다.

핵심 통찰은 DORA가 인프라 성능이 아니라 **플랫폼이 개발팀의 성공을 얼마나 가능하게 하는지** 측정한다는 것이다.
주의점으로 메트릭 게이밍 금지, 속도-안정성 균형, **개인 평가에 사용 금지(팀 단위로)** 를 기억한다.

## 복구와 인시던트 관리

**Resilience(회복탄력성)** 는 장애에도 계속 작동하는 것이다(자동 재시작, 이중화).
**Recovery(복구)** 는 장애 후 정상으로 복귀하는 것이다(백업 복원).

핵심 용어는 반드시 암기한다.

| 용어 | 의미 |
|------|------|
| **RTO** (Recovery Time Objective) | 최대 허용 다운타임 |
| **RPO** (Recovery Point Objective) | 최대 허용 데이터 손실 |
| **MTTR** | 실제 평균 복구 시간 |

**Nines**: 99.9%(three nines)는 연간 약 9시간 다운타임을 허용하며, 9가 늘수록 비용은 기하급수적으로 증가한다.
**Chaos Engineering**(예: Netflix Chaos Monkey)은 장애 전에 복구 절차를 검증하며, 대응 가능한 **업무 시간에** 실험한다.
**Blameless Postmortem**은 48~72시간 내 실시하고 시스템에 초점을 맞춘다.

## 메트릭 기반 지속적 개선

플랫폼은 정적이면 죽는다.
개선 사이클은 데이터 리뷰 → 갭 분석 → 우선순위 → **Fix / Enhance / Build / Retire** 다.

함정 회피가 중요하다.
**vanity metrics(허영 지표) 금지**, 메트릭 게이밍 금지, 분석 마비 금지를 지키며, 기능 사용량이 아닌 개발자 **성과(outcome)** 를 측정한다.
문화가 기술을 이기며, 순서는 Culture → People → Process → Technology다.

## CNCF 플랫폼 성숙도 모델

**CNCF TAG App Delivery** 워킹그룹의 업계 표준 프레임워크다.
4단계 레벨은 순서가 중요하므로 반드시 암기한다.

1. **Provisional**(=Foundational): 수동 프로세스 위주, 제한된 CI/CD
2. **Operational**: 표준화된 워크플로·런북, 일부 자동화
3. **Scalable**: **셀프서비스, GitOps**, SLO 연계 메트릭
4. **Optimizing**: **AI/ML 자동 원격 복구**, 비즈니스 KPI 연결

5대 평가 차원은 **Provisioning, Development, Security, Deployment, Observability** 다.
2025년 기준 대부분의 성숙 조직은 Scalable을 달성했으나 Optimizing은 미달이다.

## 예상 문제 (영어 + 한글 해석)

**Q1.** What are the four DORA metrics?
(DORA 4대 메트릭은?)
→ **Deployment Frequency, Lead Time for Changes, Change Failure Rate, MTTR** ✅

**Q2.** Which two DORA metrics measure stability?
(안정성을 측정하는 두 DORA 메트릭은?)
→ **Change Failure Rate, MTTR** ✅ — 배포 빈도·리드 타임은 속도.

**Q3.** A team backs up its database every 2 hours. What does this define?
(팀이 2시간마다 DB를 백업한다. 이것이 정의하는 것은?)
→ **RPO(Recovery Point Objective) ≈ 2시간** — 최대 허용 데이터 손실. ✅

**Q4.** What is the difference between resilience and recovery?
(회복탄력성과 복구의 차이는?)
→ Resilience는 **장애에도 계속 작동**, Recovery는 **장애 후 정상 복귀** 다. ✅

**Q5.** Approximately how much annual downtime does 99.9% availability allow?
(가용성 99.9%는 연간 약 얼마의 다운타임을 허용하는가?)
→ **약 9시간/년** ✅

**Q6.** What are the four levels of the CNCF Platform Engineering Maturity Model, in order?
(CNCF 플랫폼 성숙도 모델의 4단계를 순서대로?)
→ **Provisional(Foundational) → Operational → Scalable → Optimizing** ✅

**Q7.** Which practice validates recovery procedures by intentionally injecting failures before they happen naturally?
(자연 발생 전에 의도적으로 장애를 주입해 복구 절차를 검증하는 실천법은?)
→ **Chaos Engineering** (예: Netflix Chaos Monkey) ✅

**Q8.** How should DORA metrics NOT be used?
(DORA 메트릭을 사용하면 안 되는 방식은?)
→ **개인 성과 평가** — 팀 단위로 평가하고 단일 메트릭 게이밍을 금지한다. ✅

**Q9.** When should a blameless postmortem be conducted, and what is its focus?
(비난 없는 사후 분석은 언제 실시하며 초점은?)
→ **인시던트 후 48~72시간 이내**, 개인이 아닌 **시스템 실패의 학습** 에 초점. ✅

**Q10.** A platform has self-service, GitOps, and SLO-linked metrics, but no AI-driven auto-remediation. What maturity level is it?
(셀프서비스·GitOps·SLO 연계 메트릭은 있으나 AI 자동 복구는 없는 플랫폼의 성숙도 레벨은?)
→ **Scalable (Level 3)** — Optimizing은 자동 원격 복구 + 비즈니스 KPI 연결이 필요하다. ✅

## 핵심 요약

DORA 4대 메트릭(속도 2 + 안정성 2)과 등급(Elite~Low), 개인 평가 금지 원칙을 기억한다.
RTO/RPO 구분, Resilience vs Recovery, 성숙도 모델(Provisional→Operational→Scalable→Optimizing)은 반드시 정리한다.

이것으로 CNPA 6개 도메인 정리 시리즈를 마친다.
