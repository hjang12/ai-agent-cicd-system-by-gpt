# Changelog

## [1.4.7] - 2026-10-22

### Maintenance and Documentation

- Remove the root `ACTIVE_ISSUES.md` pointer; `GOVERNANCE/docs/ACTIVE_ISSUES.md` remains the single canonical Workspace issue index.
- Remove `GOVERNANCE/templates/CHANGE_RECORD.md` after checking that no repository references or instantiated records depend on it; retain `DEVELOPMENT_HISTORY.md` and task Checkpoints as the record formats.
- Mark the obsolete 2026-09-18 deployment-policy statement in ADR-0002 as historical and link to the current status and verification history.
- Add `MODELS.md` and `RATINGS.md` to Janggi project documentation navigation; the implementation modules and documentation remain preserved.

### Review Trigger

- The 2026-10-22 unused-file audit found an obsolete root issue-index pointer, an unreferenced Change Record template duplicating existing record structures, a historical ADR statement that read as current, and model documents lacking navigation links.

### Decision

- No new validator, registry, workflow, state layer, application feature, or deployment configuration was added.
- The user approved Governance version 1.4.7 and PR #163 on 2026-10-22.

## [1.4.6] - 2026-10-21

### Corrected and Simplified

- §9의 자율 실행·중단 기준을 §14와 중복 정의하지 않고 단일 승인 정책을 참조하도록 정리.
- §25 및 §30의 별도 복구 순서·시작 프롬프트 규칙을 제거하고 §25-A-7 / §25-A-13 / §25-A-14를 단일 기준으로 지정.
- §26의 중복 Evidence / Traceability 흐름을 §11, §20, §27 참조로 축약.
- §25-A의 연속성 규칙을 14개 기존 참조 번호를 유지하면서 약 350줄에서 145줄로 압축하고, 핵심 Task 상태·복구·Next Action·중단·보고 조건을 보존.
- §22의 개발 흐름과 §32의 최종 원칙을 반복된 정책 정의가 아닌 짧은 탐색·해석 기준으로 정리.
- 기존 자동 배포와 Gate 우회·직접 Production 변경의 승인 경계를 구분하고, CI→배포 순서는 플랫폼에서 실제로 강제되는지 별도로 검증하도록 명확화.
- Task Registry의 `State Summary`를 탐색용 요약으로 한정하고, 실행 가능한 상세 `Next Action`은 지정된 Checkpoint 한곳에만 두도록 정리.
- 템플릿과 ADR / Migration / Checkpoint의 오래된 Repository 경로, 작업 상태, 중복 필드를 정리.
- Current Status의 Governance 버전 중복 표기를 줄이고 canonical `GOVERNANCE/VERSION`을 단일 원본으로 지정.
- Governance 본문을 43.1KB / 1,759줄에서 32.8KB / 1,425줄로 줄이고, Janggi CURRENT_STATUS를 33.0KB에서 5.7KB로 축약.
- Workspace CURRENT_STATUS를 약 13.3KB에서 간결한 상태·탐색 인덱스로 축약하고, Migration / Task / CI 세부 기록을 각 원본 문서로 되돌림.
- Time Dashboard CURRENT_STATUS의 2026-09-18 Render 검증을 명시적으로 과거 기록으로 표시하고, 미래 개선 후보를 활성 Task 목록과 분리.
- DEFERRED `ISSUE-002`의 오래된 “latest deployment” 인용을 가장 최근에 직접 검증된 main 배포와 live-browser smoke Evidence로 갱신하되, 상태 및 재검토 조건은 유지.
- Janggi `CURRENT_STATUS.md`를 현재 상태 중심 요약으로 줄이고, 상세 UI·아키텍처·benchmark·calibration 기록은 기존 전용 문서에서 관리.
- 실행하지 않은 calibration seed 20261016을 현재 지시가 아닌 과거 계획으로 표시하고, DNS incident를 현재 서비스 상태가 아닌 날짜가 있는 History에 보존.
- AI 캘리브레이션의 447줄 PAUSED Checkpoint를 짧은 상태·증거·재개 게이트·원본 경로 요약으로 축약. Seed별 실행 결과는 기존 Development History / Evidence와 Artifact에 보존하고, 역사적 Next Action은 실행 불가한 과거 계획으로 명시.

### Review Trigger

- 2026-10-21 상세 Governance 리뷰에서 현재 규칙과 별개로 구형 템플릿 경로, 완료 Checkpoint의 오래된 실행 지시, ADR / Migration 기록의 현재형 모순, 여러 위치에 복제된 동일 규칙이 확인됨.

### Decision

- 새 validator, parser, workflow, Registry 또는 상태 계층은 추가하지 않는다.
- 기존 문서의 단일 원본을 명확히 하고, 역사적 사실은 날짜를 명시하며, 실행 가능한 Next Action은 ACTIVE Task에만 둔다.
- Governance 1.4.6은 사용자가 2026-10-22 승인했고 PR #160으로 squash-merge되어 `main`의 활성 버전이 됨. Merge commit: `a65ef98be8d83b2992e40c226159c2ef683cbb8c`.

## [1.4.5] - 2026-10-21

### Corrected

- Context Recovery의 일반 개요가 오래된 별도 순서 대신 §25-A-7의 단일 절차를 따르도록 정리.
- 중복 번호였던 실패 및 복구 기록을 §24-A로 구분.
- Workspace CURRENT_STATUS에서 완료된 저장소 정리 작업을 대기 상태로 표시하던 문구와 날짜가 지난 Render 상태를 현재 사실처럼 읽을 수 있는 표현을 바로잡음.
- 완료된 Governance Task에 남아 있던 캘리브레이션 재개 문구를 종료 기록으로 변경해 현재 PAUSED 상태와 분리.
- CHANGELOG 중간의 중복 최상위 제목을 제거하여 1.3.3 검토 완료 항목을 해당 버전 기록 아래에 유지.
- CI/deploy strict gate 이슈의 실제 확인 날짜와 현재 관찰 결과를 갱신.

### Review Trigger

- 2026-10-21 상세 리뷰에서 1.4.4의 상태 권한 규칙은 올바르지만, 일부 요약 문서가 이전 상태나 별도의 복구 순서를 계속 보유하고 있는 것을 확인함.

### Decision

- 기존 Task Registry / Active Issue Index / CURRENT_STATUS / Checkpoint / History 역할을 유지한다.
- 새 parser, registry, workflow 또는 state layer를 추가하지 않는다.
- Governance §15에 따라 사용자 승인을 받은 뒤 PR #159를 2026-10-21에 squash-merge했다. Merge commit: `43a4e6a175949790ab974fd63456a35da0c6d7ae`.

## [1.4.4] - 2026-10-21

### Clarified

- Context Recovery에서 Task Registry의 현재 Status를 Checkpoint의 Next Action보다 우선하고, `ACTIVE` Task의 현재 Next Action만 실행 대상으로 검토하도록 명확화.
- `DEFERRED` 항목은 일반 복구·무관한 작업 보고에서 반복하지 않고, 직접 질문·명시된 재검토 조건·위험을 바꾸는 새 증거가 있을 때만 다시 보고하도록 명확화.
- Current Status / Checkpoint에 누적된 과거 중간 상태를 현재 지시로 취급하지 않고, current-facing 문서의 상충·중복을 정리하며 상세 이력은 History에 보존하도록 명확화.

### Review Trigger

- 2026-10-21: 이미 완료된 v1.0 Task와 `DEFERRED`로 분류된 플랫폼 후속 항목이 Registry, 프로젝트 CURRENT_STATUS, 완료 Checkpoint에 중복·상충된 상태로 남아, 새 Chat의 정상 복구에서도 무관한 후속 보고로 반복 노출됨.

### Decision

- 새 registry, parser, workflow 또는 state layer는 추가하지 않는다.
- 기존 Task Registry / Active Issue Index / CURRENT_STATUS / Checkpoint / DEVELOPMENT_HISTORY의 역할과 우선순위를 명확히 하고, 중복된 current-facing 내용을 정리한다.
- `DEFERRED` 후속 항목은 명시된 재검토 조건이 충족되기 전까지 현재 Task / Blocker로 취급하지 않는다.

## [1.4.3] - 2026-10-16

### Clarified

- 하위 작업이 끝났더라도 ACTIVE Development Task의 Checkpoint에 실행 가능한 Next Action이 명시되어 있으면, 이를 자동으로 완료 처리하지 않고 같은 Interaction에서 계속하도록 최종 응답 전 점검 규칙을 추가.
- 배치 종료 및 외부 Runner의 idle 확인은 그 자체로 Interaction 종료 사유가 아니며, 불가피한 중단은 실제 원인과 남은 Next Action을 Checkpoint에 기록하도록 명확화.
- Agent가 기술적 Blocker 없이 먼저 종료한 경우 이를 플랫폼/기술 제약으로 잘못 기록하지 않고, 피할 수 있었던 Agent 측 조기 종료로 분류하도록 명확화.

### Review Trigger

- 2026-10-16: seed 20261007 배치 종료 후 Render Runner의 disabled / idle 상태를 검증했으나, Checkpoint에 이미 다음 seed 20261008이 명시되어 있었음에도 Agent가 다음 Action을 실행하지 않고 최종 응답을 반환함. 사용자 중단 요청이나 기술적 Blocker는 없었음.

### Decision

- 기존 Interaction / Agent Work Segment / Checkpoint 구조만 명확히 하고 새 registry, parser, workflow, state layer는 추가하지 않는다.
- 사용자 중단, 실제 권한·정책·기술 제약 또는 실행 안전 경계가 없는 한, 완료 가능한 다음 Action을 같은 Interaction에서 계속한다.

## [1.4.2] - 2026-10-15

### Clarified

- 중간 진행 보고와 최종 응답의 차이를 명문화하여 중간 보고 후 동일 Interaction에서 작업을 계속할 수 있고, 최종 응답은 Interaction을 종료함을 명확히 함.
- 최종 응답 이후 Agent가 백그라운드에서 계속 작업하는 것처럼 표현하지 않고, 계속 실행되는 외부 프로세스가 있을 때만 별도 상태로 보고하도록 명문화.
- 고정된 마일스톤 총량이나 진행률 분모 대신 현재 단계·완료 결과·다음 작업·계획 변경을 보고하며, 필요할 때 경과시간·측정된 실행시간·관찰 가능한 대기시간을 분리하도록 명문화.
- 의미 있는 마일스톤에서 진행 상황과 효율을 점검하고, 진척 없는 반복 실행 또는 긴 미설명 간격이 나타나면 방식을 재평가하도록 명문화.

### Review Trigger

- 2026-10-15 사용자 운영 피드백: 장시간 캘리브레이션 Interaction에서 중간 보고와 최종 종료의 구분, 작업시간과 대기시간의 관찰 가능 범위, 계획 변화에 견디는 마일스톤 표현이 명확하지 않았음.

### Decision

- 기존 Interaction / Agent Work Segment / Checkpoint 구조를 유지하고 새 registry, parser, workflow 또는 state layer를 추가하지 않는다.
- 상호작용의 총 시간 제한이나 고정 보고 주기를 도입하지 않는다. 실제 상태와 검증 가능한 진척을 기준으로 보고한다.

## [1.4.1] - 2026-10-08

### Clarified

- 새 Chat에서 전체 프로젝트 상태를 수동 복사하지 않고 Repository 기반 Context Recovery를 수행하도록 **최소 Continuation Message 형식**을 명문화.
- 정상 재개에는 Governance / Development Task / Context / Checkpoint를 Agent가 자동 복구하는 것을 기본으로 하고, 필요할 때만 canonical repository 식별자를 한 줄 추가하도록 명확화.
- Agent가 최소 메시지로 Context를 복구하지 못하는 경우 사용자의 긴 Prompt 작성을 요구하기 전에 Context Recovery / Governance 문제로 검토하도록 명문화.

### Review Trigger

- 2026-10-08 사용자 운영 피드백: Governance에 Repository 기반 Continuity 원칙은 이미 존재했지만, 실제 새 Chat에서 사용할 최소 메시지 형식이 명시적으로 제공되지 않아 긴 Continuation Prompt를 다시 요청할 가능성이 남아 있었음.

### Decision

- 새로운 registry / parser / workflow / state layer를 추가하지 않는다.
- 기존 Context Recovery 원칙을 명확한 최소 메시지 예시로 구체화한다.

## [1.4.0] - 2026-10-08

### Added

- 외부 Platform Tool의 실행 Context(workspace/project/environment/service 선택 상태)와 실제 Resource 상태를 분리하는 운영 규칙 추가.
- 가능한 경우 호출 단위의 안정적인 Resource ID를 사용하고, 외부 상태 변경 전 read-only Scope 확인을 수행하도록 명문화.
- "no workspace selected" 등 Tool Context 오류를 Platform 장애나 Resource 변경으로 오판하지 않고 Context 재구성 및 직접 검증을 거치도록 명확화.

### Review Trigger

- 2026-10-08 Render 검증 과정에서 실제 Render workspace와 서비스는 정상인데 Tool의 선택 Context가 초기화되어 "no workspace selected"가 발생하는 사례가 확인됨.
- 기존 1.3.3의 Observed / Declared / Unknown 원칙은 증거 해석에는 충분했지만, Tool 실행 Context와 외부 Resource Scope를 구분하는 구체적인 운영 절차는 명시하지 않았음.

### Decision

- 새로운 registry / parser / workflow / state layer를 추가하지 않고 기존 Evidence 원칙과 외부 Platform 검증 절차를 구체화한다.
- Tool Context 문제와 Platform Resource 상태를 분리하여 판단하고, 실제 Resource 조회 결과를 Source of Truth로 사용한다.

## [1.3.3] - 2026-10-01

### Added

- Tool/API Evidence를 Observed / Declared / Unknown으로 구분하고, 응답에 없는 필드를 실제 빈 값·false·disabled 상태로 추론하지 않는 운영 원칙을 명문화.
- 실패 발생 시 기존 Governance가 이미 문제를 다루고 있었는지 먼저 확인하도록 Governance Gap 검토 절차를 추가.
- Governance 변경 전 일반화 가능성, 기존 규칙의 충분성, 단순 대안, 복잡성 비용, 검증 가능성 및 제거 조건을 검토하는 단순성 기준을 추가.

### Changed

- 한 번의 운영 오류를 해결하기 위한 전용 parser / registry / workflow / 상태 계층 추가를 마지막 수단으로 제한.
- 이번 review에서 시범 도입한 Context consistency parser와 추가 CI checkout 변경을 제거하여 Governance 운영 구조를 단순화.
- Render healthCheckPath 관련 과거 기록에서 Tool 응답 미노출을 실제 empty 상태로 단정한 부분을 정정 대상으로 기록.

### Review Trigger

- Render service metadata 응답에 healthCheckPath 필드가 반환되지 않은 것을 실제 빈 설정으로 오판한 사례.
- 오판 후 추가된 context consistency validator 자체가 문서 형식과 Git checkout 조건을 잘못 가정하면서 연속 CI 실패를 만든 사례.

### Review Completion

- 2차 Governance review에서 Context Recovery의 중복 ACTIVE_ISSUES 단계를 제거하고, resolved issue를 Active Issue Index에서 제거.
- 추가적인 Governance parser / registry / workflow / state layer는 필요하지 않다고 재확인.
- Governance 1.3.3을 현재 공통 운영 기준으로 확정하고 다음 Development Task를 Janggi calibration으로 전환.

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
