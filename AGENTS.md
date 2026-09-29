# Workspace Agent Instructions

- 공통 Governance는 `GOVERNANCE/GOVERNANCE.md`를 기준으로 한다.
- `GOVERNANCE/docs/DEVELOPMENT_TASKS.md`에서 Request에 해당하는 Development Task를 먼저 식별하고, 그 Task의 Context / Checkpoint를 복구한다.
- 현재 미해결 이슈와 다음 조치는 `GOVERNANCE/docs/ACTIVE_ISSUES.md`에서 확인한다.
- 실제 작업은 해당 `projects/<project>/` 하위에서 수행한다.
- 프로젝트 간 경계를 유지한다.
- 가장 최근에 갱신된 Task를 자동으로 선택하지 않으며, Request의 Project / Scope / 작업 목적과 Registry를 기준으로 Task를 선택한다.
- 변경 후 해당 프로젝트의 기존 검증 명령을 실행한다.
- Render 설정은 실제 서비스 상태와 `render.yaml`을 함께 확인한다.
- 불확실한 동작은 추측하지 말고 실제 구현/테스트/배포 결과를 확인한다.
