# Changelog

## [1.3.2] - 2026-09-30

### Added

- Repository 기반 Context Recovery를 Continuation Prompt보다 우선하는 운영 원칙을 명문화.
- 새 Chat에서 단순한 재개 요청이 들어오면 ACTIVE Development Task를 Registry / Context / Checkpoint / 실제 상태 검증을 통해 복구하는 기본 절차를 명문화.
- Fast CI와 Long-running Execution을 분리하고, Benchmark / Calibration / Self-play / Training 같은 장시간 계산을 별도 실행 경로에서 수행할 수 있도록 했다.
- 장시간 계산 결과를 Evidence / Checkpoint / Context에 귀속하고, 실제 계산 미수행 상태를 성공 결과와 구분하도록 했다.

### Clarified

- 긴 수동 Continuation Prompt는 필수 보존 수단이 아니며 보조적인 작업 전달 수단으로만 사용한다.
- CI quota / timeout / platform execution limit 때문에 장시간 계산이 전체 개발 흐름을 불필요하게 막지 않도록 실행 경로를 분리한다.
- Fast CI는 bounded / repeatable validation을 담당하며, 장시간 실행 결과는 별도 Evidence로 관리한다.

## [1.3.1] - 2026-09-30

### Clarified

- `PAUSED` Task는 명시적인 재개 의도 없이 자동으로 재개하지 않으며, `BLOCKED` Task도 일반적인 작업 재개 요청만으로 실행 대상으로 선택하지 않는다.
- `ACTIVE` Task만 하나의 후보일 때 자동 복구·재개 대상으로 사용할 수 있도록 Task 선택 규칙을 명확히 했다.
- Context Checkpoint template에 immutable Task ID 필드를 명시했다.
- 완료된 Governance Task의 Checkpoint가 완료 상태와 일치하도록 정리했다.

## [1.3.0] - 2026-09-30

### Added

- Workspace-level `GOVERNANCE/docs/DEVELOPMENT_TASKS.md` Development Task Registry.
- Immutable Task ID format `TASK-YYYYMMDD-NNNN` with 4-digit daily sequence.
- Task status model and explicit Task → Context → Checkpoint references.
- Context Recovery rules for selecting a Development Task across multiple projects/tasks.

### Clarified

- Development Tasks are not identified by a global "last task" pointer.
- The Registry is an integrated navigation/index layer, while detailed Context and Checkpoints remain in the Workspace/Project area that owns the Task.
- New development goals create a new Task entry when no existing Task matches.
- Ambiguous multiple Task candidates are not resolved by recency; only the minimum necessary user clarification is requested.


## [1.2.1] - 2026-09-29

### Clarified

- `Session`과 `Turn`은 비정식 용어로 유지하고 Governance의 canonical terminology에서 사용하지 않는다.
- `Interaction`은 `Request → Agent Work → Response`의 상호작용 단위이며 고정된 최대 시간으로 제한하지 않는다.
- `Agent Work Segment`를 정의하여 하나의 Agent Work가 Context / Token / Tool / Runtime / 외부 작업 대기 등의 실행 경계에 따라 안전하게 분할될 수 있도록 했다.
- Long-running Agent Work는 장기적인 Development Task를 지원하는 방식이며 무제한 또는 무중단 실행을 의미하지 않는다.
- 사용자의 일시정지/중단 요청과 플랫폼 실행 경계를 안전한 Checkpoint 및 후속 Interaction으로 연결하는 운영 규칙을 명문화했다.


## [1.2.0] - 2026-09-29

### Added

- Chat-based Agent development operating model with canonical terminology for Chat, Request, Agent Work, Response, Interaction, Development Task, Development Context, Checkpoint, Context Recovery, Development Work Continuity, and Long-running Agent Work.
- Explicit Development Work Continuity policy so a Development Task can continue across Chat changes, Agent Work interruption, Context limits, or platform constraints.
- State-based Checkpoint rules without a fixed time-based forced-stop interval.
- Context Recovery procedure and minimum recovery-state requirements for new Chat / resumed Agent Work.
- Long-running Agent Work guidance separating development work from indefinite waiting on CI, benchmark, or other external execution.
- Platform Constraint guidance separating ChatGPT/plan/model limitations and Personalization from project Development Context.
- GOVERNANCE/templates/CONTEXT_CHECKPOINT.md as a reusable Checkpoint template.

### Clarified

- Chat is a temporary development interface, not a project Source of Truth.
- Chat transition is a normal operational mechanism, not a loss of the Development Task.
- Session and Turn are not canonical Governance terms; concrete terms such as Chat, Interaction, and Agent Work are used instead.
- Development Work Continuity is the operational goal; Context Recovery and Checkpoints are mechanisms for achieving it.
- Continuity problems are treated as Governance improvement signals when they recur.


### Added

- `GOVERNANCE/docs/ACTIVE_ISSUES.md` as the AI-managed current unresolved issue index
- explicit autonomous execution gates for capability, policy/project compatibility, and authority/risk
- explicit escalation rules for technical capability limits and policy/project conflicts
- proactive AI responsibility for Governance, Version, Branch, and CI/CD operating reviews
- Branch lifecycle management guidance
- Active Issue lifecycle and separation of current state from long-term history

### Clarified

- Technically possible changes must not bypass Governance or project direction.
- Current unresolved issues are maintained separately from historical development records.
이 문서는 AI Agent CI/CD System 운영 규칙의 버전별 변경 이력을 기록합니다.

## [1.1.0] - 2026-09-29

### Added

- Requirement Contract protection and change-control rules for user-requested behavior that must persist across later development.
- CI expectations for protecting active regression contracts and requiring explicit CONTRACT-CHANGE: <ID> declarations when contract definitions or regression tests are intentionally changed.

### Clarified

- Implementations may be refactored while an active Contract remains behaviorally intact.
- A later task must not silently revert an active user-requested behavior.
- Conflicting requirements require an explicit report and user decision before the active Contract is superseded.

## [1.0.0] - 2026-09-15

### Added

- AI Coding Agent 프로젝트 개발 및 운영의 기본 목적 정의
- 프로젝트 시작 시 환경·권한·코드·CI/CD·배포 상태를 우선 확인하는 절차 정의
- GitHub를 Source of Truth로 사용하는 원칙 정의
- Agent Harness 개념과 구성 요소 정의
- 모듈화·인터페이스 분리·교체 가능성을 우선하는 Architecture 원칙 정의
- 반복적인 변경과 자동 수정 루프를 전제로 한 개발 원칙 정의
- CI/CD를 Quality Gate로 활용하는 원칙 정의
- 검증 Evidence와 Traceability 관리 원칙 정의
- Reproducibility 요구사항 정의
- 변경 범위 최소화 원칙 정의
- Human Approval이 필요한 변경 유형 정의
- Version 및 외부 Dependency 관리 원칙 정의
- 최소 권한과 Production 보호 원칙 정의
- Deployment 및 Post-deployment Verification 원칙 정의
- Observability 원칙 정의
- 개발 과정에서 운영 규칙 자체를 지속적으로 개선하는 원칙 정의
- 프로젝트 지식 및 개발 이력 관리 원칙 정의
- 실패 및 복구 기록 원칙 정의
- Agent Context 복구 순서 정의
- 프로젝트별 예외 관리 원칙 정의
- Governance 자체의 변경 관리 원칙 정의
- 새 Agent 시작 시 긴 Governance 전문을 복사하지 않는 최소 시작 프롬프트 원칙 정의
- `AGENT_START.md` 추가
- `CURRENT_STATUS.md`를 빠른 Context 복구 문서로 명확히 정의
- GitHub Organization / Repository topology 원칙 정립
- Render Workspace / Project / Environment / Service topology 원칙 정립
- Project lifecycle의 Active / Maintenance / Retiring / Archived / Deleted 상태 정의
- Retiring 프로젝트 삭제 전 보존 대상과 외부 연결 확인 절차 정의
- `docs/PLATFORM_TOPOLOGY.md` 추가
- `docs/PROJECT_INVENTORY.md` 추가
- `docs/ADR/0002-platform-topology-and-lifecycle.md` 추가
- 플랫폼 정리 추적 Issue `#2` 기록

### Clarified

- 계획, AI 추론, 사용자 결정, 실제 구현, 실제 테스트 결과, 실제 배포 결과를 구분하도록 명시
- 코드 작성 완료와 실제 작업 완료를 구분하도록 명시
- 배포 성공과 서비스 정상 동작을 구분하도록 명시
- 기존 프로젝트 구조를 먼저 이해한 후 최소 변경하도록 명시
- Governance의 개선은 실제 프로젝트 경험을 근거로 수행하도록 명시
- Governance Repository는 Product Repository의 부모가 아니라 공통 정책 Repository이며, 상위 묶음이 필요할 경우 GitHub Organization을 사용한다.
- Render는 Source of Truth가 아니라 실행/배포 환경이며 GitHub → CI/Verification → Render → Post-deployment Verification 관계를 유지한다.
- 동일 Repository를 가리키는 중복 Render Service는 명확한 역할이 없으면 유지하지 않는다.
- 현재 여사모 자산은 삭제 완료가 아니라 `Retiring` 상태로 기록하며, 실제 삭제 여부는 플랫폼에서 확인한 뒤 기록한다.
- 현재 연결된 도구에서 직접 수행할 수 없는 Organization 생성/Repository 이전/Service 삭제 등의 작업은 실제 실행 없이 완료로 기록하지 않는다.
