---
title: "Datadog Workflow Automation으로 GitHub Issue 자동 생성하기"
date: 2026-07-14T21:00:00+09:00
draft: true
tags: ["Datadog", "GitHub", "Workflow Automation"]
categories: ["Observability"]
featuredImage: images/banners/datadog-github-issue-workflow-automation-48168016.png
---

Datadog Monitor가 알림을 발생시켰을 때 대응 기록을 GitHub Issue로 남기면 추적이 쉬워진다.
**Workflow Automation**을 쓰면 이 과정을 사람 개입 없이 자동화할 수 있다.
이 글은 Monitor 알림을 Trigger로 삼아 GitHub Issue를 생성하는 Workflow를 만드는 과정을 다룬다.

## Workflow Automation이란

Workflow Automation은 Datadog에서 **Trigger**와 **Action**을 연결해 작업을 자동화하는 기능이다.
Trigger는 Workflow를 시작시키는 조건이고, Action은 실제로 수행되는 동작이다.
GitHub, Slack, Jira 등 다양한 서비스에 대한 Action이 blueprint 형태로 제공된다.

## 사전 준비

시작 전에 두 가지가 준비되어야 한다.

- Datadog의 **GitHub Integration**이 설치되어 있어야 한다.
- Issue를 생성할 GitHub repository에 대한 쓰기 권한이 있는 Connection이 등록되어 있어야 한다.

Connection은 Datadog이 GitHub에 인증하기 위해 사용하는 자격 증명이다.
Integration을 설치하는 과정에서 함께 구성하거나, **Connections** 화면에서 별도로 추가할 수 있다.

## 1. Workflow 생성

Datadog에서 **Service Mgmt > Workflow Automation**으로 이동한다.
**New Workflow**를 선택하고 빈 Workflow에서 시작한다.
이름은 목적이 드러나도록 `Create GitHub Issue from Monitor` 정도로 지정한다.

## 2. Trigger 설정

Workflow의 시작점으로 **Monitor Trigger**를 추가한다.
Monitor Trigger는 지정한 Monitor가 알림 상태로 전환될 때 Workflow를 실행한다.
연결할 Monitor를 선택하고, 필요하면 `Alert`, `Warn` 등 실행 대상 상태를 지정한다.

Monitor 쪽에서 알림 메시지에 `@workflow-<Workflow 이름>` 을 추가하는 방식으로도 연결할 수 있다.
이 방식은 여러 Monitor를 하나의 Workflow에 묶을 때 유용하다.

## 3. GitHub Issue 생성 Action 추가

Trigger 다음 단계로 **Create Issue** Action을 추가한다.
Action 목록에서 `GitHub`을 검색하면 관련 blueprint가 나온다.
Action을 추가한 뒤 앞서 등록한 **Connection**을 선택한다.

## 4. Issue 필드 매핑

Action의 입력 필드에 Issue 내용을 채운다.
Trigger에서 전달된 값은 **context variable**로 참조할 수 있다.

- **Repository**: Issue를 생성할 대상 저장소 (예: `my-org/my-repo`)
- **Title**: `{{ trigger.monitor.name }}` 처럼 Monitor 이름을 그대로 사용
- **Body**: Monitor 상태와 링크를 조합해 본문 구성

Body 예시는 다음과 같다.

```
Monitor **{{ trigger.monitor.name }}** 가 알림 상태로 전환되었다.

- 상태: {{ trigger.monitor.transition }}
- 링크: {{ trigger.monitor.event_url }}
```

변수 이름은 Trigger 종류와 Datadog 버전에 따라 다르므로, 편집기의 자동 완성으로 확인한다.

## 5. 테스트

Workflow 편집 화면에서 **Run** 또는 **Test**를 실행해 동작을 확인한다.
테스트 실행 후 대상 repository에 Issue가 생성되었는지 확인한다.
각 단계의 실행 로그에서 입력값과 출력값을 함께 볼 수 있다.

## 6. 배포

테스트가 정상이면 Workflow를 **Publish**해 활성화한다.
이후 연결된 Monitor가 알림을 발생시키면 GitHub Issue가 자동으로 생성된다.
중복 Issue를 막으려면 조건 분기나 태그 기반 필터를 Action 앞에 추가한다.

## 마무리

Workflow Automation은 Monitor 알림을 GitHub Issue로 연결하는 작업을 코드 없이 구성하게 해준다.
Trigger와 Action의 조합을 바꾸면 Slack 알림, Jira 티켓 생성 등으로 확장할 수 있다.
운영 대응을 기록으로 남기는 출발점으로 활용할 수 있다.
