# Current Status

## Governance

- Governance Version: `1.0.0`
- Status: Active baseline
- Working Branch: `main`
- Target Branch: `main`
- PR #1: Merged
- Merge Commit: `3090d0e84a9182a66d8eeeac285824543471ccf1`

## Repository

- Repository: `hjang12/ai-agent-cicd-system`
- Visibility: private
- Purpose: AI Coding Agent 공통 개발·검증·배포 운영 규칙과 그 발전 이력 관리

## Current Canonical Documents

- `AGENT_START.md` — 새 Agent에게 전달할 최소 시작 프롬프트
- `GOVERNANCE.md` — 현재 적용할 공식 운영 규칙
- `VERSION` — 현재 Governance 버전
- `CHANGELOG.md` — Governance 버전별 변경 이력
- `docs/CURRENT_STATUS.md` — 빠른 Context 복구용 현재 상태
- `docs/DEVELOPMENT_HISTORY.md` — Governance 개발 이력
- `docs/ADR/` — 주요 운영 의사결정
- `templates/` — 프로젝트 문서 표준 템플릿

## Implemented Baseline

- AI Coding Agent 개발 및 운영의 기본 목적
- 프로젝트 시작 시 환경·권한·코드·CI/CD·배포 상태 확인 절차
- GitHub Source of Truth 원칙
- Agent Harness 개념
- 모듈화·Interface·교체 가능성 중심의 Architecture 원칙
- 반복 변경 및 자동 수정 루프 원칙
- 프로젝트 특성에 따른 CI/CD Quality Gate 원칙
- Verification / Evidence / Traceability 원칙
- Reproducibility 원칙
- 최소 변경 원칙
- Human Approval 원칙
- Version 관리 원칙
- Open Source / Dependency 검토 원칙
- Least Privilege 및 Production 보호 원칙
- Deployment / Post-deployment Verification 원칙
- Observability 원칙
- 프로젝트 지식 및 개발 이력 관리 원칙
- Agent Context 복구 원칙
- Governance 자체의 지속적 개선 원칙
- Governance 변경 이력 관리 원칙
- 최소 시작 프롬프트 원칙
- Repository 기반 개발지침 원칙
- Project Retirement / Delete lifecycle 원칙

## Platform state confirmed on 2026-09-15

### GitHub

현재 연결된 계정에서 확인된 활성 Repository:

- `hjang12/ai-agent-cicd-system`
- `hjang12/personal-ai-janggi-trainer`
- `hjang12/time-dashboard`
- `hjang12/personal-mcp-server`

종료한 Yeosamo Repository는 현재 Repository 목록에 존재하지 않는다.
GitHub Organization은 필수 요소로 사용하지 않으며 개발지침과 프로젝트 Context의 Source of Truth는 각 GitHub Repository에 둔다.

### Render

현재 Workspace: `My Workspace`

2026-09-15 재확인 결과 활성 Service는 다음 2개다.

- `personal-ai-janggi-trainer` — Web Service / Python / `main` / Singapore / Free / auto deploy
  - Repository: `hjang12/personal-ai-janggi-trainer`
  - Latest cleanup deployment: live
- `time-dashboard` — Web Service / Python / `main` / Oregon / Free / auto deploy
  - Repository: `hjang12/time-dashboard`
  - Latest cleanup deployment: live

Yeosamo 관련 Render Service는 모두 삭제되었다.

## Target Operating Topology

```text
GitHub Repository
├── ai-agent-cicd-system
├── personal-ai-janggi-trainer
├── time-dashboard
└── personal-mcp-server

Render Workspace
├── personal-ai-janggi-trainer Service
│   └── → hjang12/personal-ai-janggi-trainer
├── time-dashboard Service
│   └── → hjang12/time-dashboard
└── personal-mcp-server Service (when deployment is required)
```

기본 naming rule은 GitHub Repository와 Render Service의 이름을 동일하게 유지한다. 같은 Repository에 연결된 중복 Service는 명확한 운영 목적이 없으면 만들지 않는다.

## Automation Baseline

각 Project Repository는 가능한 한 다음 표준 Context 진입 구조를 가진다.

- `AGENT_START.md` — 새 Agent 세션에서 공통 Governance와 프로젝트 Context를 읽는 시작점
- `AGENTS.md` — 도구에 독립적인 Agent 작업 규칙
- `docs/CURRENT_STATUS.md` — 현재 프로젝트 상태 및 다음 작업 복구용 Context
- GitHub Actions — push/PR에서 자동 검증
- Render — 배포 대상 서비스의 `main` push 자동 배포

현재 적용 상태:

- `personal-ai-janggi-trainer`: `AGENT_START.md` + `AGENTS.md` + `docs/CURRENT_STATUS.md` + Python validation + Render auto deploy
- `time-dashboard`: `AGENTS.md` + existing Python CI + Render auto deploy; `AGENT_START.md`/`docs/CURRENT_STATUS.md` 보완 필요
- `personal-mcp-server`: `AGENTS.md` + Python compile CI; `AGENT_START.md`/`docs/CURRENT_STATUS.md` 보완 필요

Copilot 전용 Repository 지침은 현재 운영 구조에 포함하지 않는다.

AI Agent 자체를 GitHub Actions에서 추론 실행하는 Agentic Workflow는 AI 엔진 계정/인증이 필요한 별도 선택 사항이며 무료 GitHub Actions만으로 강제하지 않는다.

## Context Continuity Rule

채팅 기록은 일시적인 작업 인터페이스이고, 프로젝트의 장기 기억은 GitHub Repository에 남긴다.

중요한 요구사항, 설계 결정, 운영 변경, 실패 원인, 검증 결과, 미완료 작업이 다음 Agent 세션에 필요하다면 가능한 범위에서 Repository 문서 또는 Commit/PR 이력으로 기록한다.

새 채팅 또는 다른 AI Agent로 전환할 때는 이전 채팅을 완전하게 복원하려고 하지 않고, 공통 Governance와 프로젝트 Repository의 현재 Context를 읽어 현재 상태를 재구성한다.

`CURRENT_STATUS.md`는 현재 상태에 집중하고, `DEVELOPMENT_HISTORY.md`/ADR/Commit/PR은 장기적인 결정과 변경 이력을 보존하는 역할로 구분한다.

## Cleanup Execution Status

2026-09-15 기준 정리 작업:

- Governance PR #1 병합: 완료
- Repository 기반 개발지침 구조로 단순화: 완료
- 초기 Organization / Repository 이전 계획 폐기: 완료
- Yeosamo GitHub Repository 삭제: 확인 완료
- Yeosamo Render Service 삭제: 확인 완료
- 활성 Render 서비스와 GitHub Repository 매핑 재확인: 완료
- Agent 표준 지침을 활성 프로젝트에 적용: 진행 완료
- `personal-mcp-server` 자동 CI 추가: 완료
- Copilot 전용 Repository 지침 제거: 완료
- `personal-ai-janggi-trainer` Copilot 제거 후 Render auto deploy: live 확인
- `time-dashboard` Copilot 제거 후 Render auto deploy: live 확인

## Known Limitations

- GitHub Agentic Workflow의 AI 추론 실행은 별도 AI 엔진 인증/비용 정책이 필요함
- 현재 연결된 GitHub 도구에서는 Repository 자체의 Archive/Delete와 Organization 생성/이전을 수행할 수 없음
- 현재 연결된 Render 도구에서는 기존 Service 삭제 및 일부 Dashboard 구조 변경을 직접 수행할 수 없음

## Next Development Target

1. `time-dashboard`와 `personal-mcp-server`에 표준 Agent 시작점과 Current Status Context 적용
2. 새 Agent 세션에서 각 Repository의 Context를 실제로 읽고 작업 품질 검증
3. 각 프로젝트의 GitHub Actions 결과와 Render auto deploy 결과 확인
4. 반복되는 작업 중 AI Agent 자동화를 더 적용할 영역을 선별
5. 필요할 때만 유료/외부 AI Agent 실행 환경을 추가
