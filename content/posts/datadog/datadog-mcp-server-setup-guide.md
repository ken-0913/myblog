---
title: "Datadog MCP Server 설정 가이드: AI 에이전트와 연결하기"
date: 2026-07-16T14:00:00+09:00
draft: false
tags: ["Datadog", "MCP", "AI", "Observability"]
categories: ["Observability"]
featuredImage: images/banners/datadog-mcp-server-setup-guide-9d9623fb.png
---

**Datadog MCP Server**는 AI 에이전트가 Datadog의 telemetry 데이터를 조회하고 플랫폼 기능을 다루도록 연결하는 서버이다.
이 글은 공식 문서를 바탕으로 설정 흐름을 쉽게 정리한 가이드이다.
Claude, Claude Code, Cursor, Codex 등 여러 client에서 공통으로 적용되는 패턴을 중심으로 다룬다.

## 시작 전 확인할 것

Datadog MCP Server는 **선택한 Datadog site**에 따라 지원 여부가 다르다.
`app.ddog-gov.com`, `us2.ddog-gov.com` 같은 **정부(gov) site는 지원되지 않는다**.
ChatGPT 연동은 Preview 단계이며 현재 **US1 고객만** 사용할 수 있다.

MCP Server의 endpoint URL은 site마다 다르다.
따라서 아래 예시의 `<YOUR_MCP_SERVER_ENDPOINT>`는 공식 문서의 **Datadog Site selector**에서 자신의 site에 맞는 값으로 바꿔야 한다.

## 연결 방식은 두 가지로 나뉜다

client가 무엇이든 연결 방식은 크게 두 가지다.
하나는 **공식 plugin/connector 설치**, 다른 하나는 **MCP endpoint 직접 설정**이다.

| 방식 | 설명 | 대상 client |
|------|------|-------------|
| Plugin / Connector | 마켓플레이스에서 설치, 자동 업데이트 | Claude, Claude Code, Cursor, Copilot, OpenCode 등 |
| Endpoint 직접 설정 | 설정 파일에 MCP Server URL 직접 입력 | Codex, Gemini CLI, Kiro, Warp, 기타 |

**공식 plugin이 있으면 plugin 사용이 권장된다.**
과거에 MCP Server를 수동으로 설정했다면, 충돌을 피하기 위해 기존 설정을 제거한 뒤 plugin을 설치한다.

## 대표 client 설정

### Claude / Claude Code

Claude는 **Datadog Connector**(Claude Connectors Directory), Claude Code는 **Datadog plugin**(Anthropic Plugin Marketplace)을 설치하는 것이 권장된다.
Claude Code에서는 다음처럼 plugin을 설치하고 최초 설정을 진행한다.

```bash
/plugin install datadog@claude-plugins-official
```

설치 후 `/ddsetup`으로 site 선택과 OAuth 로그인을 진행한다.
`/ddtoolsets`로 사용할 tool 그룹을 켜고 끄며, 설정 변경 후에는 `/reload-plugins`로 다시 로드한다.

### Endpoint 직접 설정 (Codex, Gemini CLI 등)

plugin이 없는 client는 설정 파일에 MCP Server URL을 직접 넣는다.
아래는 HTTP transport로 endpoint를 등록하는 공통 형태이다.

```json
{
  "mcpServers": {
    "datadog": {
      "type": "http",
      "url": "<YOUR_MCP_SERVER_ENDPOINT>"
    }
  }
}
```

Codex는 `~/.codex/config.toml`, Gemini CLI는 `~/.gemini/settings.json`처럼 client마다 파일 위치가 다르다.
등록 후에는 각 client의 로그인 명령으로 **OAuth 인증**을 완료한다.

## Toolsets로 필요한 도구만 사용

**Toolset**은 필요한 MCP tool만 골라 쓰는 기능이다.
불필요한 tool 정의를 줄여 **context window 공간을 절약**할 수 있다.
endpoint URL 끝에 `toolsets` query parameter를 붙여 지정한다(remote 인증에서만 동작).

```text
<YOUR_MCP_SERVER_ENDPOINT>?toolsets=apm,llmobs
```

`toolsets=all`은 일반 공개된 모든 toolset을 켠다.
이 옵션은 tool 필터링을 지원하는 client(예: Claude Code)에서 가장 잘 동작한다.

특정 tool만 제외하려면 `omit_tools`를 사용한다.
두 parameter가 함께 있으면 `toolsets`를 먼저 적용한 뒤 `omit_tools`에 지정된 tool을 제거한다.

```text
<YOUR_MCP_SERVER_ENDPOINT>?toolsets=all&omit_tools=create_datadog_notebook
```

## 주요 Toolset 종류

toolset은 여러 종류가 있으며, 지정하지 않으면 기본값인 `core`가 적용된다.
대표적인 toolset은 다음과 같다.

| Toolset | 용도 |
|---------|------|
| `core` | logs, metrics, traces, dashboards, monitors, incidents 등 기본 |
| `dashboards` | dashboard 조회·생성·수정·삭제 |
| `ddsql` | DDSQL로 Datadog 데이터 질의 |
| `security` | 코드 보안 스캔, security signal/finding 검색 |
| `kubernetes` | Kubernetes 리소스 검색 및 manifest 조회 |
| `synthetics` | Synthetic test 관련 |
| `software-delivery` | CI Visibility, Test Optimization |

**Preview 단계 toolset**도 있으며 별도 신청이 필요하다.
`apm`(APM trace 분석), `code-exec`(샌드박스에서 TypeScript 실행), `remote-actions`(호스트 진단)가 여기에 해당한다.

## 필요 권한

MCP Server tool은 다음 **role 권한**을 요구한다.

| 권한 | 필요한 작업 |
|------|-------------|
| `mcp_read` | Datadog 데이터를 읽는 tool (monitor 조회, log 검색 등) |
| `mcp_write` | 리소스를 생성·수정하는 tool (monitor 생성, host mute 등) |

`mcp_read`/`mcp_write` 외에 **대상 리소스의 표준 권한**도 함께 필요하다.
예를 들어 monitor를 읽는 tool은 `mcp_read`와 **Monitors Read** 권한을 모두 요구한다.
Datadog Standard Role은 두 MCP 권한을 기본으로 가지지만, custom role은 수동으로 추가해야 한다.

## 인증 방식

대부분의 사용자에게는 **OAuth 2.0**이 권장된다.
client가 설정 과정에서 OAuth flow를 자동으로 처리하므로 장기 자격증명을 직접 관리할 필요가 없다.

서버나 CI 환경처럼 OAuth를 완료하기 어려운 경우 header 기반 인증을 사용한다.
우선순위는 다음과 같다.

- **Personal / Service Access Token (PAT/SAT)**: `Authorization` header에 bearer token으로 전달하며 API key 불필요. header 방식 중 권장.
- **API key + Application key**: `DD_API_KEY`, `DD_APPLICATION_KEY` header로 전달.

보안을 위해 필요한 권한만 가진 **service account**의 scoped key를 사용하는 것이 좋다.
또한 org의 [IP allowlist](https://docs.datadoghq.com/account_management/org_settings/ip_allowlist.md)를 켜면 승인되지 않은 origin의 접속을 차단할 수 있다.

## 연결 테스트

설정이 끝나면 **MCP inspector**로 연결을 확인할 수 있다.

```bash
npx @modelcontextprotocol/inspector
```

웹 UI에서 Transport Type을 **Streamable HTTP**로 선택하고, URL에 자신의 site endpoint를 입력한다.
**Connect**를 누른 뒤 **Tools > List Tools**에서 tool 목록이 나타나면 정상 연결된 것이다.

## 정리

Datadog MCP Server 연결은 **① client 방식 선택(plugin 또는 endpoint) → ② 인증(OAuth 권장) → ③ toolset 지정 → ④ 연결 테스트** 순서로 진행된다.
plugin이 있는 client는 plugin을, 없는 client는 endpoint 직접 설정을 사용한다.
site별 endpoint와 지원 여부는 반드시 공식 문서의 Site selector로 확인한다.

> 참고: [Datadog MCP Server 공식 문서](https://docs.datadoghq.com/mcp_server/setup/)
