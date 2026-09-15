# AI Agent CI/CD System

AI Coding Agent를 활용한 소프트웨어 개발·검증·배포 운영 체계를 정의하고, 실제 프로젝트 경험을 통해 그 운영 체계 자체를 지속적으로 개선하기 위한 공통 Governance 저장소입니다.

## 핵심 목적

이 저장소는 특정 제품의 소스 코드를 관리하지 않습니다.

대신 AI Coding Agent가 다음 전체 개발 사이클을 안정적으로 수행할 수 있도록 공통 원칙, 문서 구조, 검증 방식, 권한 원칙, 변경 관리 방식과 이력 관리 방식을 정의합니다.

```text
Requirement
→ AI Coding Agent
→ Development
→ Verification
→ GitHub
→ CI/CD
→ Deployment
→ Post-deployment Verification
→ Feedback / Improvement
```

운영 규칙 자체도 실제 프로젝트 경험을 통해 지속적으로 개선합니다.

## 가장 먼저 읽을 문서

새 Agent 또는 새 ChatGPT 대화가 프로젝트에 참여할 때는 이 저장소 전체를 먼저 읽을 필요가 없습니다.

1. `AGENT_START.md`
2. `GOVERNANCE.md`
3. 대상 프로젝트의 `CURRENT_STATUS.md`
4. 대상 프로젝트의 `README.md`
5. 대상 프로젝트의 `ARCHITECTURE.md`
6. 대상 프로젝트의 `DEVELOPMENT_HISTORY.md`
7. 대상 프로젝트의 `ADR/`
8. 필요하면 `docs/PLATFORM_TOPOLOGY.md`, `docs/PROJECT_INVENTORY.md`, `docs/RETIREMENT_CHECKLIST.md`

`AGENT_START.md`는 새 Agent에게 전달할 **최소 시작 프롬프트**를 정의합니다.

## 문서 구조

```text
AGENT_START.md
GOVERNANCE.md
VERSION
CHANGELOG.md

... / docs
├── CURRENT_STATUS.md
├── DEVELOPMENT_HISTORY.md
├── PLATFORM_TOPOLOGY.md
├── PROJECT_INVENTORY.md
├── RETIREMENT_CHECKLIST.md
├── AGENT_HARNESS.md
├── VERIFICATION.md
├── EVIDENCE.md
├── TRACEABILITY.md
└── ADR/

... / templates
├── CURRENT_STATUS.md
├── DEVELOPMENT_HISTORY.md
├── ADR.md
└── CHANGE_RECORD.md
```

`docs/PLATFORM_TOPOLOGY.md`는 Repository와 Deployment Platform의 계층 및 lifecycle을 정의하는 Governance의 상세 운영 문서이고, `docs/PROJECT_INVENTORY.md`는 실제 자산 상태를 기록하는 inventory입니다. `docs/RETIREMENT_CHECKLIST.md`는 프로젝트/서비스 종료 시 필요한 보존·삭제·검증 절차를 표준화합니다.

## Governance의 적용

각 실제 프로젝트는 이 저장소의 공통 규칙을 따르되, 프로젝트 특성에 맞게 구체적인 구현 수준을 결정합니다.

프로젝트별 문서는 프로젝트 Repository에 둡니다.

```text
GitHub Organization / Account Namespace
        ↓
Governance Repository + Project Repositories
        ↓
Project-specific Context / Architecture / History
        ↓
CI / Verification
        ↓
Render Workspace
        ↓
Render Project
        ↓
Environment
        ↓
Service
```

GitHub는 Repository의 공식 Source of Truth이고, Render는 실행 및 배포 환경입니다. Governance는 각 Project Repository에 공통 적용되며, 특정 Repository를 다른 Repository의 하위 저장소로 만들지 않습니다.

공통 규칙과 프로젝트별 예외가 충돌하는 경우 그 사실과 예외 사유를 문서화합니다.

## Platform topology

권장 GitHub 구조:

```text
GitHub Organization
├── ai-agent-cicd-system
├── personal-ai-janggi-trainer
├── time-dashboard
└── personal-mcp-server
```

권장 Render 구조:

```text
Render Workspace
├── personal-ai-janggi-trainer Project
│   └── Production → personal-ai-janggi-trainer Service
├── time-dashboard Project
│   └── Production → time-dashboard Service
└── personal-mcp-server Project (when deployed)
```

같은 Repository를 가리키는 중복 Service는 명확한 역할이 없으면 만들지 않습니다.

## Project lifecycle

프로젝트는 다음 lifecycle을 사용합니다.

```text
Planned
→ Active
→ Maintenance
→ Retiring
→ Archived / Deleted
```

삭제 전에는 데이터, Domain/DNS, Secret, 외부 API/OAuth/Webhook, CI/CD, 다른 서비스의 참조, 보존할 Git history와 문서를 확인합니다.

## 버전 관리

현재 Governance 기준 버전은 `1.0.0`입니다.

버전 변경은 실제 프로젝트의 운영 경험을 근거로 합니다.

- Major: 운영 원칙 또는 구조의 큰 변경
- Minor: 기존 원칙과 호환되는 기능·절차·표준의 추가 또는 개선
- Patch: 문서 오류 수정, 명확화, 오탈자 등 비기능적 수정

Governance 변경 시 다음을 함께 관리합니다.

```text
Problem / Context
→ Change Proposal
→ Decision
→ Version
→ Changelog
→ Implementation
→ Verification
→ Result
```

## 중요한 운영 원칙

- GitHub를 공식 Source of Truth로 사용합니다.
- 기존 코드를 이해하기 전에 대규모 수정을 하지 않습니다.
- 최소 변경을 우선합니다.
- 코드 작성보다 요구사항 충족과 검증을 중요하게 봅니다.
- 위험한 변경은 Human Approval 대상으로 분리합니다.
- 실제 수행 결과와 AI의 추론을 구분합니다.
- 중요한 결과는 가능한 범위에서 재현 가능하고 추적 가능해야 합니다.
- 실패와 복구도 프로젝트 지식으로 기록합니다.
- 프로젝트의 개발 경험을 Governance 개선으로 다시 연결합니다.
- 플랫폼 자산의 이름과 연결 관계는 문서로 확인 가능해야 합니다.
- 사용하지 않는 Project/Service/Repository는 Retirement 절차를 거친 후 정리합니다.

자세한 규칙은 `GOVERNANCE.md`, 플랫폼 구조는 `docs/PLATFORM_TOPOLOGY.md`를 공식 기준으로 봅니다.
