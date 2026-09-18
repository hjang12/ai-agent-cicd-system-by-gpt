# AI Workspace by GPT

이 저장소는 GPT 기반 개발 작업의 단일 Source of Truth입니다.

## 구조

- `GOVERNANCE/` — 공통 운영 규칙, Agent 시작 문서, 설계 기록, 템플릿
- `projects/` — 개별 프로젝트
  - `personal-ai-janggi-trainer-by-gpt/`
  - `time-dashboard-by-gpt/`
- `.github/workflows/` — 프로젝트별 CI/benchmark
- `render.yaml` — 모노레포 기준 Render 서비스 구성

## 작업 순서

1. `GOVERNANCE/GOVERNANCE.md` 확인
2. 작업 대상 프로젝트의 `AGENT_START.md`와 `AGENTS.md` 확인
3. 해당 프로젝트의 `docs/CURRENT_STATUS.md`, 코드, 테스트, CI 상태 확인
4. 최소 변경 → 테스트 → 커밋 → Render 배포 검증

프로젝트 간 경계를 유지하고 다른 프로젝트의 동작을 불필요하게 변경하지 않습니다.

자세한 통합 기록은 `GOVERNANCE/MIGRATION.md`를 확인하세요.
