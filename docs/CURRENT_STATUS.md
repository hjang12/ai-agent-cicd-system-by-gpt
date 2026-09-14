# Current Status

## Governance

- Governance Version: `1.0.0`
- Status: Initial baseline / review candidate
- Working Branch: `governance-v1.0.0`
- Target Branch: `main`
- PR: `#1`

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

## Context Recovery Order

새로운 Agent가 기존 프로젝트를 이어받을 때는 다음 순서로 확인한다.

```text
1. AI Agent Governance
2. 대상 프로젝트 CURRENT_STATUS.md
3. 대상 프로젝트 README.md
4. 대상 프로젝트 ARCHITECTURE.md
5. 대상 프로젝트 DEVELOPMENT_HISTORY.md
6. 대상 프로젝트 ADR/
7. 필요 시 Evidence
8. 실제 Source Code
9. CI / Deployment 상태
```

## Known Limitations

- Governance v1.0.0은 아직 초기 기준선이며 실제 프로젝트 적용 경험이 충분히 누적되지 않음
- Governance 자체를 자동으로 검사하는 CI 규칙은 아직 없음
- Evidence 표준 및 자동 수집 도구는 초기 원칙만 정의됨
- Context 문서의 최신 상태를 자동으로 강제하는 장치는 아직 없음

## Next Development Target

1. 실제 프로젝트에 Governance를 적용
2. Agent Context 복구 문제 관찰
3. Evidence / Traceability 운영 문제 관찰
4. Git / CI / Deployment 승인 흐름 검증
5. 반복되는 문제를 Governance 개선안으로 전환
6. 필요 시 템플릿·검증 도구·자동화 추가
7. 다음 Governance Version 결정
