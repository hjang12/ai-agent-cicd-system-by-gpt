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
- `docs/PLATFORM_TOPOLOGY.md` — GitHub/Render topology 및 lifecycle 규칙
- `docs/PROJECT_INVENTORY.md` — 실제 Repository/Deployment 자산 inventory
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
- GitHub Organization / Repository topology 원칙
- Render Workspace / Project / Environment / Service topology 원칙
- Project Retirement / Archive / Delete lifecycle 원칙

## Platform state confirmed on 2026-09-15

### GitHub

현재 연결된 계정에서 확인된 Repository:

- `hjang12/ai-agent-cicd-system`
- `hjang12/personal-ai-janggi-trainer`
- `hjang12/project-yeosamo`
- `hjang12/time-dashboard`
- `hjang12/personal-mcp-server`

사용자 보고 기준 GitHub Organization `ai-ci-cd`가 생성되었다. 다만 현재 연결된 GitHub 도구에서는 해당 Organization membership이 조회되지 않아, Organization 내부 Repository 이전 여부는 미검증 상태로 유지한다.

### Render

현재 Workspace: `My Workspace`

확인된 서비스:

- `personal-ai-janggi-trainer` — Web Service / Python / `main` / Singapore / auto deploy
- `time-dashboard` — Web Service / Python / `main` / Oregon / auto deploy
- `project-yeosamo` — Static Site / `main` / Oregon / auto deploy
- `project-yeosamo-app` — Web Service / Node / `main` / Oregon / auto deploy

`project-yeosamo`와 `project-yeosamo-app`은 동일 GitHub Repository를 가리키며, 여사모 종료 결정에 따라 Retiring 대상으로 분류했다.

## Target Platform Topology

```text
GitHub Organization / Account Namespace
└── ai-ci-cd (created; repository transfer pending verification)
    ├── ai-agent-cicd-system
    ├── personal-ai-janggi-trainer
    ├── time-dashboard
    └── personal-mcp-server

Render Workspace
├── personal-ai-janggi-trainer Project
│   └── Production → personal-ai-janggi-trainer Service
├── time-dashboard Project
│   └── Production → time-dashboard Service
└── personal-mcp-server Project (when deployed)
```

## Cleanup Execution Status

2026-09-15 기준 정리 작업을 실행했다.

- Governance에 Repository/Deployment topology와 project lifecycle 규칙 반영: 완료
- 실제 플랫폼 상태 inventory 기록: 완료
- 정리 추적 Issue #2 생성: 완료
- Governance PR #1 병합: 완료
- GitHub Organization `ai-ci-cd` 생성: 사용자 작업으로 완료 보고됨, 연결 도구에서 membership 미검증
- 활성 Repository의 Organization 이전: 미완료
- 여사모 Render Service 2개를 Retiring 대상으로 기록: 완료
- 여사모 Render Service 실제 삭제: 미완료 — 현재 연결된 Render 도구에 삭제 명령이 없음
- 여사모 GitHub Repository 실제 Archive/Delete: 미완료 — 현재 연결된 GitHub 도구에 Repository 삭제/Archive 명령이 없음
- Render Project/Environment restructuring: 미완료

## Cleanup Plan

1. 여사모 데이터/외부 연동/Domain/Secret 보존 여부 확인
2. 여사모 Render Service 종료/삭제
3. 필요한 경우 여사모 GitHub Repository 보존 후 Archive 또는 삭제 결정
4. Organization `ai-ci-cd` 접근 가능 여부를 연결 도구에서 확인
5. 활성 프로젝트를 Organization 체계로 이전할지 최종 결정하고, 가능해진 경우 이전 후 검증
6. 각 Project Repository의 CURRENT_STATUS/README/DEVELOPMENT_HISTORY를 실제 상태와 일치시킴
7. Render Project/Environment/Service naming을 표준화
8. 최종 GitHub ↔ Render 연결 및 배포 검증

## Known Limitations

- Governance 자체를 자동으로 검사하는 CI 규칙은 아직 없음
- Evidence 표준 및 자동 수집 도구는 초기 원칙만 정의됨
- Context 문서의 최신 상태를 자동으로 강제하는 장치는 아직 없음
- 현재 연결된 GitHub 도구에서는 Organization 생성, Repository Organization 이전, Repository Archive/Delete를 수행할 수 없음
- 현재 연결된 Render 도구에서는 Service 삭제와 Workspace/Project 구조 변경을 직접 수행할 수 없음
- 현재 연결된 GitHub 도구에서는 새 Organization `ai-ci-cd` membership이 아직 조회되지 않음

## Next Development Target

1. GitHub Organization `ai-ci-cd`와 연결 도구의 접근 가능 상태 재검증
2. 여사모 retirement 수행 및 실제 삭제 결과 검증
3. 활성 프로젝트의 Context 문서 표준 적용
4. Git / CI / Deployment 승인 흐름 검증
5. Evidence / Traceability 운영 문제 관찰
6. 반복되는 문제를 다음 Governance Version 개선안으로 전환
