# Agent instructions

> 이 템플릿은 canonical monorepo의 `projects/<project>/AGENTS.md`에 사용합니다.

- 공통 Governance: `../../GOVERNANCE/GOVERNANCE.md`
- 시작 절차와 Task 선택은 Workspace root `AGENT_START.md` 및 `GOVERNANCE/docs/DEVELOPMENT_TASKS.md`를 따른다.
- 프로젝트의 `AGENT_START.md`, `docs/CURRENT_STATUS.md`, 관련 Checkpoint / Requirement Contract를 확인한 후 실제 코드와 CI 상태를 검증한다.
- 실제 Repository 상태가 채팅 설명 또는 오래된 문서와 다르면 실제 상태를 우선하고 문서 불일치를 수정한다.
- 핵심 domain/source와 계층 경계를 유지하고 최소 변경을 우선한다.
- 변경 후 프로젝트에 맞는 compile/build/test 및 필요한 regression 검증을 수행한다.
- 외부 Dependency의 필요성·라이선스·운영 영향과 Production 변경 위험을 검토한다.
- Governance / Requirement / 승인된 Architecture 방향과 충돌하거나 권한을 벗어나는 변경은 임의 실행하지 않고 근거와 영향을 보고한다.
- 중요한 결정, 반복 장애, 검증 결과는 관련 Context / History에 간결하게 기록한다.
