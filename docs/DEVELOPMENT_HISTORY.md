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
- `docs/PLATFORM_TOPOLOGY.md`: GitHub/Render topology 및 lifecycle 규칙
- `docs/PROJECT_INVENTORY.md`: 실제 Repository/Deployment 자산 inventory
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

## 2026-09-15 — Repository / Deployment Topology 정리 기준 추가 및 실제 정리 착수

### Requirement

Governance와 여러 Project Repository가 모두 개인 GitHub 계정의 동일 레벨에 있고, Render Workspace 아래에 서비스가 직접 나열되면서 프로젝트의 소유 관계와 배포 관계를 한눈에 파악하기 어려웠다.

또한 실제 Render 상태를 확인한 결과 동일한 GitHub Repository `project-yeosamo`를 가리키는 `project-yeosamo` Static Site와 `project-yeosamo-app` Web Service가 동시에 존재했다.

### AI Proposal

1. 모든 프로젝트를 하나의 GitHub Monorepo로 통합한다.
2. 개인 계정의 형제 Repository 구조를 그대로 유지한다.
3. GitHub Organization을 상위 Namespace로 사용하고 Governance와 Project Repository를 형제 Repository로 관리한다.
4. Render는 하나의 Workspace 아래 제품별 Project → Environment → Service 구조로 정리한다.

### User Decision

GitHub Organization 기반 구조를 목표로 하고, Render는 제품별 Project/Environment/Service 구조로 정리한다. 여사모 프로젝트는 종료 대상으로 분류한다.

### Decision / Reason

GitHub Repository는 다른 Repository의 하위 저장소가 될 수 없으므로 Organization을 상위 경계로 사용하는 것이 가장 자연스럽다. Governance는 Repository의 부모가 아니라 공통 정책으로 동작해야 하며, 각 Project Repository의 독립 lifecycle을 유지해야 한다.

Render에서는 Workspace를 전체 개발 자산의 상위 경계로 유지하고 제품별 Project 및 Environment를 사용하면 서비스 중복과 오래된 자산을 식별하기 쉬워진다.

### Implementation

다음 문서를 추가/갱신했다.

- `docs/PLATFORM_TOPOLOGY.md`
- `docs/PROJECT_INVENTORY.md`
- `docs/ADR/0002-platform-topology-and-lifecycle.md`
- `docs/CURRENT_STATUS.md`
- `README.md`
- `Issue #2`: 플랫폼 정리 추적

### Verification

2026-09-15 GitHub Repository 목록 및 Render Workspace/Service 목록을 직접 재확인했다.

현재 확인된 GitHub Repository는 `ai-agent-cicd-system`, `personal-ai-janggi-trainer`, `project-yeosamo`, `time-dashboard`, `personal-mcp-server`이다.

현재 Render Workspace는 `My Workspace`이며 확인된 서비스는 `personal-ai-janggi-trainer`, `time-dashboard`, `project-yeosamo`, `project-yeosamo-app`이다.

GitHub 연결 계정에서는 Organization membership이 확인되지 않았다.

### Execution Result

- Governance topology/lifecycle 규칙: 완료
- 실제 플랫폼 inventory: 완료
- 여사모 Retiring 분류: 완료
- 정리 Issue #2: 완료
- GitHub Organization 생성/Repository 이전: 미완료
- 여사모 Render Service 삭제: 미완료
- 여사모 GitHub Repository Archive/Delete: 미완료

현재 연결된 GitHub 도구에는 Organization 생성, Repository Archive/Delete 기능이 없고, Render 연결 도구에도 Service 삭제와 Workspace/Project 구조 변경 기능이 없어 플랫폼 리소스 자체를 직접 제거할 수 없다.

따라서 삭제/이전을 수행한 것으로 기록하지 않으며, 실제 플랫폼 콘솔에서 수행한 뒤 결과를 다시 검증하는 것을 완료 조건으로 유지한다.

### Known Issues

- Governance v1.0.0 PR은 아직 `main`에 merge되지 않았다.
- GitHub Organization target은 아직 생성되지 않았다.
- 여사모 Render 서비스는 아직 삭제되지 않았다.
- `project-yeosamo` Repository도 아직 삭제/Archive되지 않았다.

### Next Step

1. 여사모 데이터 및 외부 연동 보존 여부 최종 확인
2. Render의 여사모 Service 삭제
3. GitHub Organization 생성 및 Repository 이전
4. 실제 이전/삭제 결과 검증
5. 각 Project Repository의 Context 문서 최신화
6. Render Project/Environment/Service 구성 검증
7. GitHub ↔ CI/CD ↔ Render 연결 및 Post-deployment Verification
