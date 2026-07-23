---
title: "CNPA 시험 정리 (4) Platform APIs — 조정 루프, CRD, Operator, 오토스케일링"
date: 2026-07-17T08:00:00+09:00
draft: false
tags: ["CNPA", "Kubernetes", "CRD", "Operator", "CNCF"]
categories: ["자격시험"]
featuredImage: images/banners/cnpa-04-platform-apis-provisioning-6018cc5d.png
---

이번 편은 **Domain 4: Platform APIs and Provisioning Infrastructure (12%)** 를 정리한다.
핵심은 Kubernetes의 **API + 조정 루프(reconciliation loop)** 가 플랫폼 엔지니어링의 엔진이라는 것이다.
CRD·Operator·프로비저닝 도구로 Kubernetes를 확장해 셀프서비스 API를 만든다.

## Kubernetes API와 조정 루프

모든 도구(kubectl, 대시보드, 커스텀 훅)가 동일한 API와 상호작용한다.
오브젝트는 **spec(원하는 상태)** 과 **status(Kubernetes가 채우는 관측 상태)** 로 구성된다.

조정 루프의 4단계는 핵심이다.

**Observe(관찰) → Compare(원하는 상태와 비교) → Act(차이가 있으면 조치) → Repeat(반복)**

이 루프는 **폴링이 아니라 이벤트 기반(event-driven)** 이다.
컨트롤러는 변경 이벤트에 반응하며, **Informer**가 watch로 감시하고 캐싱한다.

모든 변경은 **API Server를 경유** 하여 etcd에 저장된다.
컨트롤러는 파드와 직접 대화하지 않고 API 서버를 통해서만 감시·업데이트한다.

## 셀프서비스를 위한 CRD

표준 K8s 추상화는 조직의 멘탈 모델과 다르다.
개발자는 "DB 하나 만들기"를 원하지 15개 리소스 관리를 원하지 않는다.

**CRD(Custom Resource Definition)** 는 Kubernetes에 조직의 비즈니스 개념을 가르치는 것이다.
새 리소스 타입이 네이티브처럼 동작하며, **OpenAPI v3 스키마 검증** 과 RBAC 통합을 제공한다.

주의할 점은 **CRD는 스키마만 제공하며, 동작하려면 컨트롤러가 필요** 하다는 것이다.
복잡도 사다리는 **ConfigMap(단순 설정) < CRD(스키마+검증) < Operator(스키마+로직)** 순이다.

CRD 스키마는 **하위 호환성(backward compatibility)** 을 위해 추가(additive) 방식으로만 진화해야 한다.

## Operator 패턴

Operator의 공식은 반드시 암기한다.

> **Operator = CRD(스키마) + Controller(운영 로직)**

Operator는 **인간의 운영 지식(operational knowledge)을 소프트웨어로 인코딩** 한다.
예를 들어 PostgreSQL operator는 컨테이너만 띄우는 것이 아니라 failover, 백업, point-in-time recovery까지 안다.

대표 Operator로는 **Prometheus Operator, Strimzi(Kafka), cert-manager** 가 있다.
개발 프레임워크로는 **Kubebuilder**(공식)와 **Operator SDK**(Red Hat)가 있다.

## 인프라 프로비저닝

3대 접근법은 반드시 구분한다.

| 도구 | 관리 대상 | 특징 |
|------|----------|------|
| **Crossplane** | 모든 클라우드 리소스 | CNCF, K8s-native. 클라우드 리소스를 CRD로 표현. Composition + Claim |
| **Terraform / OpenTofu** | 모든 클라우드 리소스 | 외부 IaC 도구, HCL + state. OpenTofu는 CNCF 포크 |
| **Cluster API (CAPI)** | **Kubernetes 클러스터만** | CNCF graduated, 클러스터 라이프사이클 전용 |

**Crossplane**은 "CNCF의 universal cloud API"로, 클라우드 리소스가 K8s 오브젝트가 되어 조정 루프가 적용된다.
**Cluster API는 클라우드 리소스(DB, 네트워크)를 관리하지 못한다** 는 점이 함정 보기로 자주 나온다.

## 리소스 관리와 스케일링

출제 빈도가 높은 영역이다.
**Request**는 스케줄링용 예약이고, **Limit**은 런타임 상한이다.
암기 문장은 "**Requests affect scheduling, limits affect runtime behavior**" 다.

오토스케일러는 스케일 대상으로 구분한다.

| 도구 | 스케일 대상 | 기준 |
|------|------------|------|
| **HPA** | 파드 수 | CPU/메모리, scale-to-zero 불가 |
| **Cluster Autoscaler** | 노드 수 | Pending 파드 발생 시 노드 추가 |
| **KEDA** | 파드 수 (이벤트 기반) | 큐 깊이·Kafka lag, **scale-to-zero 가능** |
| **Karpenter** | 노드 (AWS) | 워크로드 인지 just-in-time |
| **DRA** | 파드 리소스 | GPU 부분 할당, VPA 후계 |

트러블슈팅 시, HPA 미동작은 metrics-server 문제, Cluster Autoscaler 미동작은 대개 클라우드 권한(permissions) 문제다.

## 비용과 가치

**OpenCost**는 Kubernetes 비용의 실시간·세분화 가시성을 제공하는 CNCF 프로젝트다.
**Kubecost**는 그 상용 형제다.

**FinOps**는 비용 최적화를 전원의 책임으로 만드는 문화다.
Scale-to-zero, spot 인스턴스, rightsizing이 대표적인 최적화 기법이다.

## 예상 문제 (영어 + 한글 해석)

**Q1.** What are the four steps of the Kubernetes reconciliation loop?
(Kubernetes 조정 루프의 4단계는?)
→ **Observe → Compare → Act → Repeat** ✅

**Q2.** How do Kubernetes controllers detect changes — polling or events?
(Kubernetes 컨트롤러는 변경을 어떻게 감지하는가 — 폴링 vs 이벤트?)
→ **이벤트 기반(event-driven)** — Informer가 watch로 감시하며 캐싱한다. ✅

**Q3.** What distinguishes an Operator from a plain CRD?
(Operator와 단순 CRD의 차이는?)
→ CRD는 **스키마만** 정의하고, Operator는 **CRD + 컨트롤러(운영 로직)** 다. ✅

**Q4.** Which CNCF project represents cloud resources as Kubernetes custom resources for provisioning?
(클라우드 리소스를 K8s 커스텀 리소스로 표현해 프로비저닝하는 CNCF 프로젝트는?)
→ **Crossplane** ✅ — Cluster API는 K8s 클러스터만 관리한다.

**Q5.** In a pod spec, what is the difference between requests and limits?
(파드 스펙에서 requests와 limits의 차이는?)
→ **Requests는 스케줄링에 영향(예약), Limits는 런타임 동작을 제한(상한)** 한다. ✅

**Q6.** A queue-based workload should scale to zero when idle. Which autoscaler fits?
(큐 기반 워크로드가 유휴 시 0으로 스케일해야 한다. 적합한 오토스케일러는?)
→ **KEDA** — HPA는 최소 replica를 유지한다. ✅

**Q7.** Pods are stuck Pending and the Cluster Autoscaler isn't adding nodes. What's the most common cause?
(파드가 Pending에 멈추고 Cluster Autoscaler가 노드를 추가하지 않는다. 가장 흔한 원인은?)
→ **클라우드 권한(permissions) 문제** 또는 요청 크기가 가용 노드 타입 초과. ✅

**Q8.** Which CNCF project provides granular, real-time Kubernetes cost visibility?
(세분화된 실시간 Kubernetes 비용 가시성을 제공하는 CNCF 프로젝트는?)
→ **OpenCost** ✅ — Kubecost는 상용.

**Q9.** Which tool manages only Kubernetes cluster lifecycles declaratively?
(Kubernetes 클러스터 라이프사이클만 선언적으로 관리하는 도구는?)
→ **Cluster API** ✅

## 핵심 요약

조정 루프는 Observe→Compare→Act→Repeat이며 이벤트 기반이다.
Operator = CRD + Controller, Crossplane은 클라우드 리소스를 CRD로 표현한다.
Requests/Limits와 오토스케일러 구분(KEDA=scale-to-zero), OpenCost는 반드시 정리한다.

다음 편은 **Domain 5: IDPs and Developer Experience** — Backstage, 서비스 카탈로그, AIOps를 다룬다.
