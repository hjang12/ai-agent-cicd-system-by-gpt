# AI Agent CI/CD System

AI Coding Agent를 활용한 소프트웨어 개발·검증·배포 운영 체계를 정의하고, 실제 프로젝트 경험을 통해 그 운영 체계 자체를 지속적으로 개선하기 위한 공통 Governance 저장소입니다.

## 핵심 목적

이 저장소는 특정 제품의 소스 코드를 관리하지 않습니다.

대신 AI Coding Agent가 다음 전체 개발 사이클을 안정적으로 수행할 수 있도록 공통 원칙, 개발 지침, 검증 방식, 권한 원칙, 변경 관리 방식과 이력 관리 방식을 정의합니다.

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

## 가장 먼저 읽을 문서

새 Agent 또는 새 ChatGPT 대화가 프로젝트에 참여할 때는 이 저장소 전체를 먼저 읽을 필요가 없습니다.

1. `AGENT_START.md`
2. `GOVERNANCE.md`
3. 대상 프로젝트의 Context 문서
4. 대상 프로젝트의 `README.md`
5. 대상 프로젝트의 `DEVELOPMENT_HISTORY.md`
6. 필요하면 대상 프로젝트의 ADR 및 Architecture 문서

`AGENT_START.md`는 새 Agent에게 전달할 최소 시작 프롬프트를 정의합니다.

## 문서 구조

```text
AGENT_START.md
GOVERNANCE.md
VERSION
CHANGELOG.md

docs/
├── CURRENT_STATUS.md
├── DEVELOPMENT_HISTORY.md
└── ADR/

templates/
├── CURRENT_STATUS.md
├── DEVELOPMENT_HISTORY.md
├── ADR.md
└── CHANGE_RECORD.md
```

공통 Governance 문서는 이 저장소에서 관리하고, 프로젝트별 상세 Context와 Architecture는 각 프로젝트 Repository에 둡니다.

## 운영 모델

```text
GitHub Repository
      ↓
개발지침 / Context
      ↓
AI Coding Agent
      ↓
Code Change
      ↓
CI / Verification
      ↓
Deployment
      ↓
Post-deployment Verification
```

GitHub Repository를 공식 Source of Truth로 사용합니다. 별도의 GitHub Organization, Repository 간 상하위 구조 또는 특정 배포 플랫폼에 대한 의존성은 Governance의 필수 조건이 아닙니다.

실제 프로젝트에서 필요한 플랫폼 구성은 각 프로젝트의 Repository 문서와 배포 플랫폼 설정을 기준으로 확인합니다.

## Project lifecycle

프로젝트는 다음 lifecycle을 사용합니다.

```text
Planned
→ Active
→ Maintenance
→ Retiring
→ Archived / Deleted
```

삭제나 retirement 같은 파괴적 작업은 별도의 실행 대상이며, Governance Repository에 실시간 자산 목록을 유지하는 것을 필수로 하지 않습니다.

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
- 프로젝트별 Context가 실제 코드/CI/CD 상태와 일치하도록 유지합니다.
- 가능한 작업은 자동화하고, 사람이 수행해야 하는 작업은 계정 권한·결제·삭제·이전 등 필요한 경우로 한정합니다.

자세한 규칙은 `GOVERNANCE.md`를 공식 기준으로 봅니다.
