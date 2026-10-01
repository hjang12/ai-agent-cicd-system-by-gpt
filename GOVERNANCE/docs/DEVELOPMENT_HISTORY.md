## 2026-10-01 — Governance v1.3.3: evidence discipline and simplicity review

### Trigger

Render service metadata에서 `healthCheckPath` 필드가 반환되지 않은 상황을 실제 empty configuration으로 해석한 운영 오판이 발생했다. 이후 오판을 방지하기 위해 추가한 Context consistency parser가 Markdown 표기와 Git checkout 조건을 잘못 가정하면서 자체 CI 실패를 반복했다.

### Root Cause

- Tool/API 응답에서 필드가 누락된 상태와 값이 실제 empty/null/false인 상태를 구분하는 명시적 Governance 규칙이 없었다.
- 기존 Governance의 '추측하지 않는다'는 원칙은 있었지만 Evidence의 관찰 범위를 형식화하지 않아 부분적인 Tool 응답을 과도하게 해석할 여지가 있었다.
- 첫 번째 대응에서 문제의 일반화 가능성과 기존 규칙의 충분성을 먼저 평가하지 않고 별도 parser와 CI gate를 추가하여 복잡성을 키웠다.

### Decision

- Evidence 상태를 Observed / Declared / Unknown으로 구분한다.
- Tool 응답에 없는 필드는 기본적으로 Unknown이며, empty/null/false/disabled 상태로 해석하지 않는다.
- 실패 발생 시 먼저 기존 Governance의 적용 여부를 확인하고, 규칙 공백이 확인될 때만 Governance 변경을 검토한다.
- Governance 변경은 가장 단순한 해법을 우선하며, 전용 parser / registry / workflow / 상태 계층 추가는 마지막 수단으로 둔다.
- 운영 제품인 Janggi 프로젝트는 Governance Task가 안정화될 때까지 일시 정지하고, Governance를 Workspace 최우선 Development Task로 승격한다.

### Implementation

- Governance Version `1.3.3` 반영.
- Context consistency parser와 full-history workspace checkout 변경 제거.
- Governance Gap 확인 및 Governance 변경 적합성 검토 규칙 추가.
- Render 오판을 유발한 Evidence 해석 규칙 추가.
- TASK-20260930-0002를 PAUSED로 전환하고 TASK-20261001-0001 Governance Task를 ACTIVE로 등록.

### Verification

- Workspace validation의 기존 구조 검증 경계는 유지하고 새로운 전용 parser는 제거했다.
- Governance 변경 자체는 제품 코드에 대한 추가 복잡한 runtime dependency나 별도 상태 저장 계층을 만들지 않는다.
- 다음 단계는 Governance 전체의 중복·충돌·불필요한 복잡성을 추가 검토하는 것이다.

### Review Rule

이번 변경의 핵심 기준은 '문제마다 규칙을 하나씩 추가하지 않는다'이다. 반복성, 일반화 가능성, 기존 규칙의 한계, 단순 대안의 부재, 검증 가능성 및 복잡성 비용을 함께 확인한 뒤에만 Governance를 확장한다.

## 2026-10-01 — Whole-product review: UI layout regression and Context-state drift root-cause correction

### Review Findings

이번 리뷰에서 두 종류의 반복 위험을 분리했다.

1. **UI 구조 위험**
   초기 trainer UI는 기능을 추가하는 과정에서 기존 v2 drawer/overlay 스타일 위에 후속 스타일을 누적하는 방식으로 진화했다. 그 결과 장기판을 가릴 수 있는 구형 layout 규칙과 새 game-first 규칙이 동시에 존재할 여지가 생겼고, UI 요구사항이 명시적인 non-overlap Contract로 승격되기 전까지는 구조적 회귀를 자동으로 충분히 제한하지 못했다. 실제 PR #89에서 이 구조를 단일 game-first layout으로 재구성했고, UX-004와 browser regression tests로 board-covering drawer 회귀를 보호했다.

2. **Context 상태 드리프트**
   CURRENT_STATUS 계열 문서에 Governance version, CI run, Render deployment 같은 빠르게 변하는 상태가 정적 Context와 함께 수동 복제되어 있었다. 이후 PR/commit/deploy가 연속으로 발생하면서 문서 갱신 시점과 실제 Repository/CI/Render 상태가 어긋날 수 있었고, Agent가 이 정적 문구를 현재 사실처럼 읽을 위험이 생겼다. 문제의 구조적 원인은 동적 운영 telemetry와 durable Context의 경계가 명확하지 않았고 이를 기계적으로 검증하는 CI gate가 없었던 것이다.

### Prevention

- UI 변경은 active UX Contract와 회귀 테스트를 함께 수정·검증하고, superseded CSS/layout rule을 같은 변경에서 제거한다.
- docs/CURRENT_STATUS.md는 durable product/context 상태만 유지한다. 정확한 CI run ID, Render deployment ID, 현재 live commit 등 mutable telemetry는 dated verification/history/checkpoint 기록으로 이동한다.
- tools/validate_context_consistency.py를 추가하고 Workspace validation에서 실행하여 Governance version, ACTIVE Task → Context/Checkpoint 연결, checkpoint commit 존재 여부, Active Issue authoritative index, Current Status telemetry boundary를 자동 검사한다.
- Project AGENTS.md에 UI layout 및 Current Status 운영 경계를 명문화하여 다음 Agent가 동일한 패턴을 반복하지 않도록 한다.

### Result

문서와 실제 상태의 불일치를 사람이 마지막에 발견하는 방식에서, Repository 변경 단계에서 구조적 drift를 자동 검출하는 방식으로 운영 경계를 강화했다. 이번 리뷰에서 확인된 1번 UI 문제는 UX-004 Contract와 regression tests로 보호되며, 6번 Context drift 문제는 dedicated consistency validation으로 재발 방지 장치를 추가했다.
# Development History

## 2026-09-30 — Governance v1.3.2 Continuity / Execution Path Refinement

### Requirement

반복되는 Chat 전환마다 긴 Continuation Prompt를 수동으로 복사하는 방식과, GitHub Actions 같은 Fast CI에서 장시간 AI calibration을 직접 수행하는 방식이 개발 연속성과 실행 안정성 측면에서 비효율적인 것으로 확인되었다.

### Observation

- Repository에는 Development Task / Context / Checkpoint / History가 이미 존재하므로 장기 상태의 공식 보존 수단은 Chat Prompt일 필요가 없다.
- 단순한 “계속 진행해” 요청에도 이전 Chat 내용을 다시 긴 Prompt로 전달해야 하는 운영은 Context 구조가 정상적으로 동작하는지 확인하는 기준을 흐린다.
- AI level calibration과 같은 장시간 계산은 Fast CI의 quota / timeout / execution constraints와 운영 목적이 다르다.
- 이번 Janggi calibration 작업에서 GitHub Actions quota가 장시간 계산의 실행 경로와 충돌하는 실제 사례가 확인되었다.

### Decision

1. Repository 기반 Context Recovery를 정상적인 Chat Continuity 경로로 확정하고, Continuation Prompt는 선택적 보조 수단으로만 취급한다.
2. 새 Chat에서 단순 재개 요청이 들어오면 ACTIVE Development Task를 Registry → Context → Checkpoint → 실제 Git / CI / Deployment 상태 순으로 복구하여 계속한다.
3. Fast CI는 bounded / repeatable validation에 집중하고, Benchmark / Calibration / Self-play / Training 등 장시간 실행은 별도의 Long-running Execution Path로 분리한다.
4. 실제 계산이 수행되지 않은 준비 상태는 성공 결과로 기록하지 않고, Execution Infrastructure Ready와 Computation Not Executed를 구분한다.
5. 장시간 실행 결과는 Evidence / Checkpoint / Context에 귀속하여 Repository를 Source of Truth로 유지한다.

### Result

Governance Version `1.3.2`에서 Chat Continuity와 장시간 실행의 운영 경계를 명문화했다. 향후 새 Chat 시작과 장시간 AI 평가 작업을 특정 Chat 또는 특정 CI 실행환경에 종속시키지 않도록 한다.

### Verification

- `GOVERNANCE/GOVERNANCE.md`에 Continuation Prompt 및 Fast CI / Long-running Execution 운영 규칙 반영
- `GOVERNANCE/CHANGELOG.md` 및 `GOVERNANCE/VERSION` 동기화
- `GOVERNANCE/docs/CURRENT_STATUS.md`에 현재 실행 모델 반영

### Next Step

실제 Janggi calibration 작업에서 Repository 기반 복구와 별도 Long-running Execution Path를 사용하고, 반복적인 Continuity 실패가 발견될 경우 추가 Governance 개선 근거로 승격한다.

## 2026-09-30 — Governance v1.3.0 Development Task Registry

### Requirement
- Support multiple concurrent or paused Development Tasks across Governance and multiple projects without relying on a single global last-task pointer.
- Allow a new Chat to identify the intended Development Task before reading project-specific Context.

### Problem / Context
v1.2.1 established Interaction boundaries and Context Recovery, but the Workspace did not yet have a canonical index connecting multiple Development Tasks to their respective Context and Checkpoint records. A new Chat could therefore recover a project Context but still lack a reliable way to determine which Task within the Workspace should be resumed.

### Decision
- Add the Workspace-level `GOVERNANCE/docs/DEVELOPMENT_TASKS.md` Registry.
- Use immutable `TASK-YYYYMMDD-NNNN` IDs with a four-digit daily sequence.
- Keep Task selection separate from recency; do not automatically restore the most recently updated Task.
- Keep the Registry integrated for discovery while storing detailed Context / Checkpoints in the owning Workspace or Project area.
- Ask only a minimal clarification when multiple relevant Tasks cannot be distinguished from the Request.

### Implementation
- Governance Version: `1.3.0`.
- Added Development Task Registry and Task lifecycle rules.
- Added initial registry entries for the active Governance continuity task and the ongoing Janggi AI development task.
- Added Task-specific Checkpoint files and Task ID to the reusable checkpoint template.
- Updated workspace/project startup instructions and validation requirements.
- Synchronized project Context Governance versions.

### Verification
- Repository structure, Context Recovery terminology, Task Registry rules, and checkpoint paths were re-read together.
- Existing Workspace validation remains the required CI gate for the new Registry path.

### Next Step
Use the Task Registry during the next Chat transition and create/update Task records as Development Tasks start, pause, resume, complete, or become blocked.
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

- Governance v1.0.0 PR은 `main`에 merge되지 않은 상태였다.
- GitHub Organization target은 아직 생성되지 않은 상태였다.
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

## 2026-09-15 — Governance v1.0.0 main 반영 및 Organization target 생성

### Verification

PR #1 `Establish AI Agent CI/CD governance v1.0.0`이 2026-09-15에 `main`으로 병합된 것을 직접 확인했다. Merge Commit은 `3090d0e84a9182a66d8eeeac285824543471ccf1`이다.

### User Action

사용자가 GitHub Organization `ai-ci-cd`를 생성했다.

### Decision

Organization은 생성했지만, 현재 연결된 GitHub 도구에서 해당 Organization membership이 조회되지 않으므로 Repository 이전은 보류한다. 기존 `hjang12/*` Repository에서 계속 개발하며, 연결 도구가 Organization을 실제로 접근할 수 있는지 확인된 후 이전 여부를 다시 결정한다.

### Current Result

- Governance v1.0.0: active on `main`
- PR #1: merged
- GitHub Organization `ai-ci-cd`: created by user
- Active Repository transfers: deferred
- Yeosamo retirement: still pending

### Next Step

1. 기존 Project Repository에 Governance Context 표준 적용
2. 각 Project의 현재 상태와 CI/CD/Render 연결을 점검
3. 여사모 retirement를 플랫폼에서 수행하고 실제 결과를 재검증
4. Organization 접근 가능 여부가 확인되면 active Repository 이전 검토
5. 실제 프로젝트 경험을 기반으로 Governance v1.1.0 후보 수집


## 2026-09-18 — GPT 개발 Workspace Monorepo 통합

### Requirement

프로젝트를 새로 시작할 때마다 별도 GitHub Repository 생성, Agent 접근 권한 연결, 공통 Governance 연결을 반복하는 운영 비용을 줄인다.

### User Decision

하나의 private GitHub Repository를 GPT 개발 Workspace로 사용하고, 공통 Governance는 `GOVERNANCE/`, 개별 제품은 `projects/<project>/` 아래에 둔다.

### Implementation

- `hjang12/ai-agent-cicd-system-by-gpt`를 canonical Workspace Repository로 사용
- Janggi를 `projects/personal-ai-janggi-trainer-by-gpt/`로 통합
- Time Dashboard를 `projects/time-dashboard-by-gpt/`로 통합
- 프로젝트별 GitHub Actions를 root `.github/workflows/`로 이동하고 path filter 적용
- root `render.yaml`에 서비스별 Root Directory를 선언
- 프로젝트별 Agent entrypoint와 Context 경로를 monorepo 기준으로 조정
- Time Dashboard binary icon 전달 제약으로 `assets/icon.png`를 self-contained `assets/icon.svg`로 대체하고 참조를 갱신
- 장기 의사결정을 `GOVERNANCE/docs/ADR/0002-ai-workspace-monorepo.md`에 기록

### Verification

- 중앙 `main`에 통합 구조가 존재함을 확인
- Janggi / Time Dashboard 원본 HEAD와 중앙 프로젝트 subtree를 비교
- Janggi 최신 중앙 validation: success
- Janggi 최신 중앙 search benchmark: success
- Time Dashboard migration CI: success

### Current Execution State

GitHub 통합은 완료되었다. 기존 `-by-gpt` 프로젝트 Repository는 역사적 snapshot으로 남아 있으며 canonical 개발 위치는 중앙 monorepo로 전환했다.

Render repository/root-directory 전환은 현재 workspace에서 live service mapping을 재확인한 뒤 완료 처리한다. 기존 Repository의 Archive/Delete도 별도 destructive action으로 남긴다.

### Lessons

Monorepo 통합 자체보다 중요한 것은 다음 Agent가 잘못된 이전 Repository에서 개발하지 않도록 canonical path를 명확히 문서화하는 것이다. 따라서 root `AGENT_START.md`, workspace `AGENTS.md`, 프로젝트별 entrypoint, CURRENT_STATUS, migration record를 함께 유지한다.


## 2026-09-18 — Render Monorepo Cutover 완료

### Requirement

GitHub monorepo 통합 이후에도 기존 Render Web Service를 유지하면서 각 서비스가 canonical monorepo의 해당 프로젝트 디렉터리를 배포하도록 전환한다.

### Execution

사용자가 Render Dashboard에서 기존 두 Service의 Git source와 Root Directory를 다음과 같이 변경했다.

- Janggi Service `personal-ai-janggi-trainer-by-gpt`
  - Repository: `hjang12/ai-agent-cicd-system-by-gpt`
  - Root Directory: `projects/personal-ai-janggi-trainer-by-gpt`
- Time Dashboard Service `time-dashboard-by-gpt`
  - Repository: `hjang12/ai-agent-cicd-system-by-gpt`
  - Root Directory: `projects/time-dashboard-by-gpt`

기존 Service 리소스와 URL은 유지했으며 중복 Service는 생성하지 않았다.

### Verification

- Janggi deployment `dep-damckfad0e5s73eu325g`: `live`
- Janggi build: `python -m compileall janggi tests` 성공
- Janggi start: `python app.py` 정상 기동
- Time Dashboard deployment `dep-damckue7bikc73b4p7ng`: `live`
- Time Dashboard build: `pip install -r requirements.txt` 성공
- Time Dashboard start: `python timefolio_server.py` 정상 기동
- Time Dashboard Render request logs: `HEAD /` HTTP 200 및 `GET /` HTTP 200 확인
- 두 서비스 모두 canonical monorepo와 project-specific Root Directory가 실제 Service 설정에 반영됨

Time Dashboard는 cutover 직후 첫 build에서 root directory 적용 시점의 `requirements.txt` 탐색 실패가 1회 발생했으나, 재배포에서 정상 완료되었다.

### Result

GitHub/Render topology는 다음 상태로 확정했다.

```text
GitHub: one canonical monorepo
  └── project-specific directories

Render: multiple deployment services
  ├── Janggi → Janggi Root Directory
  └── Time Dashboard → Time Dashboard Root Directory
```

### Operational Note

현재 연결된 Render tool interface는 기존 Service의 Repository / Root Directory 변경 작업을 노출하지 않으므로, 이번 source cutover는 Render Dashboard에서 실행하고 연결된 Render 조회 도구로 실제 설정과 deployment 결과를 검증했다.

Render `healthCheckPath`는 두 서비스 모두 현재 비어 있다. 애플리케이션 자체의 기동/HTTP 응답은 확인했으며, 명시적 platform health check path 설정은 후속 운영 개선사항으로 남긴다.

기존 GitHub 프로젝트 Repository는 현재 Render가 더 이상 참조하지 않으므로 historical snapshot으로 유지할 수 있다. Archive/Delete는 별도의 destructive action으로 취급한다.


## 2026-09-18 — Monorepo 운영 검증 및 Render 배포 범위 고정

### Requirement

Monorepo 전환 이후 프로젝트 경계가 문서에만 존재하지 않고 CI에서 지속적으로 검증되며, Render에서도 한 프로젝트의 변경이 다른 프로젝트 Service의 불필요한 자동 배포를 유발하지 않도록 운영 규칙을 명시적으로 고정한다.

### Implementation

- `tools/validate_workspace.py` 추가
  - 공통 Governance / Project entrypoint / Context / CI / Render Blueprint의 필수 경로 검증
  - Render 서비스별 `rootDir`, `healthCheckPath`, `buildFilter` 핵심 값 검증
  - 프로젝트 내부 nested `.git` 디렉터리 검증
- `.github/workflows/workspace-validation.yml` 추가
  - workspace 구조/배포 설정을 Python 3.12에서 자동 검증
  - validator 자체 변경도 workflow를 재실행하도록 trigger 포함
- root `render.yaml`에 서비스별 `buildFilter.paths` 추가
  - Janggi: `projects/personal-ai-janggi-trainer-by-gpt/**`
  - Time Dashboard: `projects/time-dashboard-by-gpt/**`
  - Blueprint 변경 자체는 Render의 규칙에 따라 별도로 처리됨

### Verification

- 초기 validator 실행에서 `.gitignore`를 nested Git metadata로 잘못 판정하는 검사 오류가 발견됨.
- 검사 조건을 실제 `.git` 디렉터리만 차단하도록 수정.
- 최종 workspace validation run #3 (`15fc705`) 성공.
- Janggi validation, Janggi search benchmark, Time Dashboard CI도 최신 완료 run에서 성공.
- 두 Render Service는 canonical monorepo와 project-specific Root Directory를 유지하며 정상 `live`.
- Time Dashboard health endpoint 추가 후 CI와 Render 배포 성공.

### Operational Note

현재 연결된 Render tool interface는 기존 Service의 `healthCheckPath` 또는 `buildFilter` mutation을 노출하지 않는다. 따라서 repository-side Blueprint에는 해당 운영 정책을 고정했으며, 실제 Service 설정 변경이 필요한 경우 Dashboard/API/CLI의 설정 동기화가 필요하다.

### Result

운영 기준은 다음으로 정리했다.

```text
one GitHub monorepo
  ├── project A
  └── project B

one Render workspace
  ├── Service A → project A root/filter
  └── Service B → project B root/filter

CI
  └── workspace invariant validation
```

향후 신규 프로젝트가 추가되면 동일한 패턴으로 project directory, CI, Render service, build filter, Context 문서를 함께 등록한다.


## 2026-09-18 — CI/CD 파이프라인 엄밀 검토 및 운영 Hardening

### Review Result

Canonical monorepo, GitHub Actions, Render Service mapping, live deployment state, and repository cleanup state were cross-checked against the current platform state.

### Implemented

- Project CI workflows now use `actions/checkout@v7` and `actions/setup-python@v7`.
- CI workflows explicitly request `contents: read` permissions.
- All four validation workflows have a bounded 5-minute job timeout.
- Janggi search benchmark now runs on pull requests and also triggers when the authoritative Janggi core changes.
- Time Dashboard CI installs the same `requirements.txt` used by Render before compilation/tests.
- Workspace validation now requires the workspace-validation workflow itself and validates project-specific Render build/start commands in addition to rootDir, healthCheckPath, and buildFilter.

### Remaining Platform-Level Limitations

- Render Services still report an empty live `healthCheckPath`; the repository Blueprint declares `/api/health`, but the current connected Render interface does not expose a mutation for this existing Service setting.
- Render autoDeploy remains commit-triggered. A strict CI-success-before-deploy gate is not currently enforced because the available Render interface does not expose the required existing-Service deployment policy mutation, and GitHub branch-protection/ruleset administration is unavailable through the connected integration for this private repository.

These are explicit operational limitations, not assumed-complete features.


## 2026-09-18 — Automation-First Agent 운영 원칙 확정

사용자는 일반적인 기술 작업에 대해 사전 승인을 요구하지 않고 AI가 자율적으로 분석, 수정, 검증, 문서화, CI 실행 및 안전한 복구까지 수행하는 운영 방식을 채택했다. Human Approval은 삭제, 비가역적 데이터 변경, 중대한 보안/권한 변경, 실질적 비용 증가, 법률/라이선스 판단, 대규모 Architecture·제품 방향 변경 등 높은 위험의 결정에만 둔다.

향후 일반적인 기술 이슈는 `발견 → 수정 → 검증 → 보고`를 기본 흐름으로 처리하며, AI는 문제를 숨기지 않고 해결되지 않은 기술적 한계를 결과와 함께 보고한다.

## 2026-09-18 — 자율 실행 판단 기준 및 정책·기획 충돌 Escalation 명확화

### Requirement

Automation First 운영에서는 AI가 일반적인 기술 작업을 스스로 처리하는 것만으로 충분하지 않다. AI가 기술적으로 해결할 수 없는 경우뿐 아니라, 해결은 가능하지만 Governance / 개발지침 / Project Plan / Requirement / Architecture Constraint와 충돌하는 경우에도 자동화가 진행되지 않도록 명확한 판단 기준이 필요하다.

### Implementation

GOVERNANCE/GOVERNANCE.md에 다음 원칙을 명문화했다.

- 자율 실행 전 Execution Capability → Policy / Project Compatibility → Authority / Risk를 독립적으로 확인
- 세 조건을 모두 충족할 때만 자율 실행
- Tool/권한/플랫폼 한계로 완료할 수 없는 경우 중단 후 보고
- 기술적으로 구현 가능하더라도 Governance, 개발지침, Project Plan, Requirement, Architecture Constraint와 충돌하면 임의 실행·우회 금지
- 상충하는 문서/요구사항을 AI가 임의 해석하여 진행하지 않고 보고
- 개선 제안도 지침·기획 변경이 필요한 순간에는 실행이 아니라 제안·보고로 전환
- 문제 상태를 임의로 완료/정상/검증됨으로 표시하지 않음
- 최종 원칙에 위 판단 기준을 추가

### Review

기존 Automation First 원칙인 발견 → 수정 → 검증 → 보고를 유지하면서, 자율 실행이 불가능하거나 허용되지 않는 경우의 별도 흐름을 발견 → 중단 → 원인/영향 정리 → 보고로 명확히 분리했다.

Governance Version은 1.0.0을 유지했다. Version 변경 자체는 사용자 합의가 필요한 별도 결정이므로 이번 변경에서는 Version 값을 임의로 증가시키지 않는다.

### Result

AI가 기술적으로 할 수 있다는 이유만으로 시스템의 지침이나 프로젝트 방향을 우회하는 것을 방지하면서, 일반적인 기술 작업에 대한 사전 승인 요구는 추가하지 않는다.

## 2026-09-18 — Active Issue 운영 인덱스 도입

### Requirement

장기 개발 이력에 문제를 계속 누적하는 방식은 과거 기록을 보존하는 데는 적합하지만, 현재 미해결 항목을 빠르게 파악하고 AI가 다음 작업을 복구하기에는 비효율적이다.

### Decision

현재 미해결 이슈와 장기 이력을 분리한다.

- `GOVERNANCE/docs/ACTIVE_ISSUES.md`: 현재 active issue와 상태의 authoritative source
- `GOVERNANCE/docs/DEVELOPMENT_HISTORY.md`: 중요한 개발 과정과 해결 이력
- GitHub Issue: 필요할 때 개별 이슈의 상세 논의/추적
- ADR: 구조적 의사결정

### Implementation

- `ACTIVE_ISSUES.md` 추가
- 현재 검증된 미해결 플랫폼/CI 문제 2건을 등록
- Governance의 Context 복구 순서에 Active Issues 추가
- Active Issue lifecycle과 등록 기준을 Governance에 명문화
- Current Status에서 Active Issue Index로 연결

### Version Note

Governance 변경은 의미상 Minor 변경 후보에 해당한다. 그러나 현재 Governance 규칙상 Version 값 변경은 사용자 합의가 필요한 별도 결정이므로 이번 작업에서는 `VERSION` 값을 변경하지 않고, `1.1.0` 변경 필요성을 별도 판단 항목으로 유지한다.


## 2026-09-18 — Governance / Version / Branch 운영의 선제적 제안 책임 명확화

### Requirement

사용자가 모든 Governance, Version, Branch 및 CI/CD 운영 개선사항을 먼저 제안하는 방식은 Automation First의 목적과 맞지 않다. AI가 현재 운영 상태를 지속적으로 관찰하고, 구조적 개선이 필요하면 먼저 제안해야 한다.

### Implementation

`GOVERNANCE/GOVERNANCE.md`에 다음 책임을 명문화했다.

- Governance 구조와 규칙의 누락·충돌·중복을 선제적으로 검토
- Project Version 및 Governance Version 변경 필요성을 먼저 검토하고 제안
- Branch 전략, Branch 수명, 불필요한 Branch를 선제적으로 점검
- CI/CD Quality Gate, Trigger, 검증 범위, 배포 경계를 선제적으로 점검
- Repository / Render / CI 구성의 구조적 Drift를 선제적으로 점검
- Governance 변경은 사용자 요청을 기다리지 않고 Proposal 단계까지 AI가 준비
- Version 값 확정은 기존 사용자 합의 원칙을 유지

### Result

향후 사용자가 먼저 제안하지 않아도 AI가 운영 구조를 지속적으로 검토하고 필요한 변경안을 먼저 제시한다. 단, 정책적 결정이나 Version 확정 등 사람의 결정이 필요한 부분은 제안과 실행 권한을 구분하여 처리한다.


## 2026-09-29 — Governance v1.2.1 Interaction / Execution Boundary Refinement

### Requirement
- Prevent canonical Interaction terminology from being mixed with non-canonical Session terminology.
- Clarify that Interaction does not use an arbitrary fixed time limit.
- Distinguish long-running Development Tasks from unbounded single Agent execution.
- Account for Context / Token / Tool / Runtime / external-job limits and user-requested pauses.

### Problem / Context
v1.2.0 established Development Work Continuity, Checkpoints, Context Recovery, and Long-running Agent Work, but the execution boundary of one Interaction was not explicit enough. A fixed Interaction time limit would introduce arbitrary forced stops, while an unlimited interpretation could ignore model/context/tool/runtime constraints. The canonical terminology also explicitly excludes Session and Turn.

### Decision
- Keep Interaction as the canonical unit `Request → Agent Work → Response`.
- Do not impose a fixed maximum duration on Interaction or Agent Work.
- Add Agent Work Segment as an execution-boundary concept for splitting long-running Agent Work safely.
- Treat Context / Token / Tool / Runtime / external-job limits as Platform Constraints.
- Treat user pause/stop as an explicit interruption signal, ending the current Interaction at the earliest safe point after state preservation.
- Continue Development Tasks across multiple Interaction / Agent Work Segment / Checkpoint cycles.

### Implementation
- Governance Version: `1.2.1`
- Updated `GOVERNANCE.md`, `CHANGELOG.md`, `VERSION`, Current Status, History, and Checkpoint template.
- Updated the Janggi project Current Status to the current Governance version.

### Verification
- Canonical terminology re-read against the implemented Governance text.
- Confirmed that `Session` and `Turn` remain explicitly non-canonical in Governance.
- Confirmed no fixed Interaction duration was introduced.

### Next Step
Use the refined boundary rules during the next Janggi development cycle and treat repeated continuity failures as evidence for further Governance improvements.
## 2026-09-29 — Add Chat-based Development Work Continuity

### Requirement

The workspace uses ChatGPT + AI Agent as the primary development interface. Long chats, interrupted Agent Work, platform limits, or the need to start a new Chat must not cause loss of development continuity.

### Problem / Context

Previous Governance already required Repository-based Context recovery, but it did not explicitly define the distinction between Chat, Agent Work, Development Task, Checkpoint, Context Recovery, and Development Work Continuity. It also did not specify how to handle long-running Agent Work without imposing an arbitrary time-based cutoff.

### AI Proposal

- Treat Chat as a temporary development interface rather than the project Source of Truth.
- Define Development Task as the continuity unit above Chat.
- Define Development Context, Checkpoint, Context Recovery, and Development Work Continuity as explicit operating concepts.
- Use state-based Checkpoints instead of fixed time-based forced stops.
- Define Long-running Agent Work handling so CI/benchmark waiting does not become indefinite Agent polling.
- Treat ChatGPT plan/model/tool limitations as Platform Constraints, not immutable Governance assumptions.
- Provide a reusable Checkpoint template.

### User Decision

Approved the full operating model and requested it to become part of Governance and to be continuously improved as new operational lessons emerge.

### Implementation

Governance Version 1.2.0 adds section 25-A and updates supporting templates and status documents.

### Verification

- Governance terminology and recovery workflow reviewed against the current Chat-based development model.
- Governance version, changelog, status, README, and templates updated consistently.

### Result

Development Work Continuity is now a formal Governance objective. Chat changes are treated as normal transitions; development state is preserved through Repository-backed Context, Checkpoints, and recovery procedures.

### Next Step

Apply the new continuity model during subsequent development work and promote recurring continuity failures into future Governance improvements.
