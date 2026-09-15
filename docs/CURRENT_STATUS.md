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
- 프로젝트 lifecycle 원칙
- 자동화 우선 원칙

## Current Direction

이 저장소의 역할은 **AI Coding Agent가 프로젝트를 일관된 규칙으로 개발하도록 하는 Repository 기반 개발지침의 Source of Truth**입니다.

별도의 GitHub Organization 생성, Repository 이전, 전체 플랫폼 inventory 유지 등은 Governance의 필수 범위에서 제외합니다.

실제 프로젝트의 현재 상태와 배포 구성은 각 프로젝트 Repository 및 해당 배포 플랫폼에서 직접 확인합니다.

## Automation Direction

목표 운영 흐름은 다음과 같습니다.

```text
Repository Context
→ AI Coding Agent
→ Code Change
→ Commit / PR
→ Automated CI / Verification
→ Deployment
→ Post-deployment Verification
```

사람의 반복적인 수동 작업을 최소화하고, 계정 권한·결제·파괴적 변경처럼 명시적인 승인이 필요한 작업만 사람의 개입 대상으로 둡니다.

## Known Limitations

- Governance 자체를 자동으로 검사하는 별도 validator는 아직 없음
- Context 문서의 최신 상태를 자동으로 강제하는 장치는 아직 없음
- 일부 계정 수준의 GitHub/Render 관리 작업은 현재 연결된 도구의 권한 및 기능 범위를 벗어날 수 있음

## Next Development Target

1. Repository 기반 개발지침을 실제 프로젝트에 일관되게 적용
2. GitHub Actions를 이용한 자동 검증 강화
3. Agent가 Context를 읽고 개발·검증·PR까지 수행하는 흐름 검증
4. 실제 프로젝트 운영에서 반복되는 수동 작업을 자동화 대상으로 전환
5. 관찰된 문제를 다음 Governance Version 개선안으로 반영
