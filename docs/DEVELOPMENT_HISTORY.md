# Development History

## 2026-09-15 — Governance v1.0.0 수립

### Requirement

AI Coding Agent를 활용하는 프로젝트의 개발·검증·배포·운영 방식을 별도로 버전 관리하고, 실제 개발 경험을 통해 운영 규칙 자체도 지속적으로 개선할 수 있는 기반이 필요했다.

### Context

기존 프로젝트에서는 개발 규칙이 대화와 개별 프로젝트 문서에 흩어질 수 있었고, 새로운 ChatGPT 대화에서 이전 결정사항을 복원하거나 테스트 Evidence를 찾는 데 비용이 발생할 수 있었다.

### Decision

공통 운영 규칙을 별도 GitHub Repository `ai-agent-cicd-system`에서 관리한다. 초기 기준 버전은 `1.0.0`으로 한다.

### Repository Structure

- `AGENT_START.md`: 새 Agent에게 전달할 최소 시작 안내
- `GOVERNANCE.md`: 현재 적용할 공식 운영 규칙
- `VERSION`: 현재 Governance 버전
- `CHANGELOG.md`: 버전별 변경 이력
- `docs/CURRENT_STATUS.md`: 빠른 Context 복구용 현재 상태
- `docs/DEVELOPMENT_HISTORY.md`: 운영 규칙의 장기 개발 이력
- `docs/ADR/`: 중요한 운영 의사결정 기록
- `templates/`: 프로젝트 문서 표준화에 사용할 템플릿

### Documentation Refinement

초기 지침에는 프로젝트 시작 시 전달해야 하는 내용이 지나치게 길어질 가능성이 있었다.

### Decision

운영 규칙 전체는 GitHub의 `GOVERNANCE.md`에 보존하고, Agent 시작 시 전달하는 프롬프트는 Repository 위치와 문서 확인 지시만 포함하도록 최소화한다.

### Reason

- 긴 시작 프롬프트의 중복을 방지
- Governance 변경 시 모든 프로젝트의 시작 프롬프트를 수정할 필요를 줄임
- 새로운 Agent가 항상 최신 Governance를 Repository에서 읽도록 유도
- 채팅 Context보다 공식 Repository 문서를 우선하는 운영 원칙 강화

### Implementation

`AGENT_START.md`를 추가하고 `GOVERNANCE.md`에 최소 시작 프롬프트 원칙을 명시했다.

`CURRENT_STATUS.md`는 빠른 상태 복구에 집중하고, `DEVELOPMENT_HISTORY.md`는 장기 이력에 집중하도록 역할을 명확히 했다.

### Verification

문서가 작업 Branch에 반영되었으며 PR #1에 포함되도록 구성했다. Governance 문서, Version, Changelog, Current Status, Development History 간 내용 일관성을 확인했다.

### Next Step

실제 프로젝트에 Governance를 적용하고, 적용 과정에서 발생하는 Context 복구, Evidence, 승인, CI/CD 및 문서 동기화 문제를 다음 Governance 개선의 근거로 축적한다.
