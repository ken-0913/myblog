---
title: "ICA 시험 정리 (1) 서비스 메시 기초: Kubernetes Service, Sidecar, Envoy"
date: 2026-07-16T08:00:00+09:00
draft: false
tags: ["Istio", "ICA", "Kubernetes", "Service Mesh", "Envoy"]
categories: ["자격시험"]
featuredImage: images/banners/istio-ica-01-prerequisites-76560b35.png
---

ICA(Istio Certified Associate) 시험을 준비하기 위한 정리 시리즈의 첫 편이다.
이번 편은 Service Mesh를 이해하기 위한 전제 개념인 **Kubernetes Service**, **Sidecar**, **Envoy**를 다룬다.
세 개념은 결국 Istio 아키텍처로 이어지는 밑바탕이 된다.

## Kubernetes Service

**Pod**는 Kubernetes의 가장 작은 배포 단위이지만 **일시적(ephemeral)**이다.
Deployment의 의도 상태를 유지하는 과정에서 Pod가 동적으로 생성·종료되며, 이때 Pod의 IP가 계속 변경된다.
그래서 프론트엔드가 개별 Pod IP를 직접 추적하는 방식은 현실적이지 않다.

Service는 **안정적인 IP(stable IP)**를 가지고 Pod 집합으로 트래픽을 라우팅하는 추상화 계층이다.
대상 Pod는 보통 **label**로 선택되므로, Pod에 올바른 label이 지정되어 있어야 Service가 정상 동작한다.

### Service의 3가지 유형

| 유형 | 노출 범위 | 주 용도 |
|------|-----------|---------|
| **ClusterIP** | 클러스터 내부 IP | 클러스터 내 통신 (기본값) |
| **NodePort** | 모든 Node의 특정 포트 | Node IP를 통한 외부 접근 |
| **LoadBalancer** | 외부 로드밸런서 | 클라우드 환경의 외부 트래픽 분산 |

**ClusterIP**가 기본값이며 클러스터 내부 통신에 사용된다.
**NodePort**는 모든 Node에 특정 포트를 열어 외부 접근을 허용한다.
**LoadBalancer**는 클라우드 제공자의 외부 로드밸런서를 프로비저닝하여 NodePort 기능을 확장한다.

## Sidecar

**Sidecar 컨테이너**는 Pod 안에서 메인 컨테이너에 부가 기능을 더하는 컨테이너다.
메인 컨테이너는 핵심 비즈니스 로직을 수행하고, Sidecar는 보조 작업을 담당한다.
주요 역할은 **log shipping**, **monitoring**, **file loading**, **proxying**이다.

Sidecar는 메인 컨테이너와 **동일한 network namespace 및 storage volume을 공유**한다.
그러나 격리된 환경에서 동작하므로 모듈성과 유지보수성이 보장된다.
이러한 **관심사의 분리(separation of concerns)**가 성능을 높이고 문제 해결을 단순화한다.

```yaml
containers:
  - name: nginx-container
    image: nginx
    volumeMounts:
      - name: shared-data
        mountPath: /usr/share/nginx/html
  - name: sidecar-container
    image: fluent/fluentd
    volumeMounts:
      - name: shared-data
        mountPath: /pod-data
```

두 컨테이너가 동일한 `shared-data` volume을 마운트하여 데이터를 공유한다.

## Envoy

**Proxy**는 사용자와 애플리케이션 사이의 중개자(intermediary)다.
TLS 암호화, 인증, 요청 재시도 같은 기능을 애플리케이션 대신 proxy에 위임할 수 있다.
그 결과 개발자는 핵심 비즈니스 로직에만 집중할 수 있다.

**Envoy**는 마이크로서비스 환경을 위해 설계된 오픈소스 proxy다.
2015년 **Lyft**에서 개발했고, 2017년 CNCF에 가입, 2018년 Graduate 등급을 달성했다.
단순 proxy를 넘어 고급 라우팅 기능을 가진 **communication bus**로도 동작한다.

Envoy는 일반적으로 **Sidecar 컨테이너**로 배포되어 Pod의 모든 inbound/outbound 트래픽을 관리한다.
이 방식은 모든 마이크로서비스에 일관된 트래픽 관리를 제공하는 모범 사례다.
**Istio**는 이 Envoy를 데이터 플레인으로 활용하는 대표적인 Service Mesh다.

## 세 개념의 연결

세 개념은 하나의 Service Mesh 아키텍처로 이어진다.
**Kubernetes Service**가 동적인 Pod IP를 안정적인 엔드포인트로 추상화한다.
그 위에서 **Envoy**가 **Sidecar** 패턴으로 배포되어 TLS·인증·라우팅·재시도를 처리한다.

| 계층 | 역할 |
|------|------|
| Kubernetes Service | 안정적인 통신 엔드포인트 제공 |
| Sidecar 패턴 | 부가 기능을 별도 컨테이너로 분리 |
| Envoy | Sidecar로 배포되어 통신 제어 |

이 세 가지가 결합되어 Istio 같은 Service Mesh가 완성된다.
다음 편은 이 위에서 동작하는 **Istio 아키텍처와 설치**를 다룬다.
