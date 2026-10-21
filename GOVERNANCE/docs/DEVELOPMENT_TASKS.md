# Development Task Registry

이 문서는 Workspace 전체의 Development Task를 식별하고 Context Recovery를 시작하기 위한 통합 Registry입니다.

상세 개발 내용과 장기 이력은 Registry에 중복 저장하지 않고 각 Task가 속한 Workspace / Project의 공식 Context, Checkpoint, History에서 관리합니다.

## Task ID

형식: TASK-YYYYMMDD-NNNN

- YYYYMMDD: Task가 Registry에 처음 등록된 날짜
- NNNN: 해당 날짜의 4자리 일련번호
- Task ID는 생성 후 변경하지 않습니다.
- Project 이름, 상태, Chat 이름은 Task ID에 포함하지 않습니다.

## Status

| Status | 의미 |
| --- | --- |
| ACTIVE | 현재 진행 대상 |
| PAUSED | 상태를 보존한 채 의도적으로 일시정지 |
| BLOCKED | 외부 제약 또는 결정 대기로 진행 불가 |
| COMPLETED | 목표 달성 및 검증 완료 |
| ARCHIVED | 완료/취소 후 장기 보관 |

현재 작업 후보를 탐색할 때는 ACTIVE / PAUSED / BLOCKED 상태를 확인할 수 있지만, **자동으로 재개할 수 있는 상태는 ACTIVE뿐입니다.**
- ACTIVE: Request가 해당 Task로 식별되면 자동으로 복구·재개할 수 있습니다.
- PAUSED: 의도적으로 일시정지된 상태이므로 명시적인 재개 의도가 확인될 때까지 자동으로 실행 Task로 선택하지 않습니다.
- BLOCKED: 현재 진행할 수 없는 상태이므로 일반적인 "계속해" 요청만으로 실행 Task로 재개하지 않습니다. Blocker 해소 여부를 확인합니다.
- COMPLETED / ARCHIVED: 기본 작업 후보에서 제외하며 명시적인 이력 조회 또는 후속 작업 요청이 있을 때만 참조합니다.

완료/보관 Task의 ID와 이력은 유지합니다.

## Current Task Registry

| Task ID | Scope | Project / Area | Goal | Status | Context | Current Checkpoint | Active PR / Issue | Next Action | Last Updated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TASK-20261021-0002 | Workspace | Governance | Context Recovery에서 DEFERRED 항목 및 완료된 Checkpoint Next Action이 현재 작업으로 반복 노출되지 않도록 상태 권한과 보고 범위를 명확화 | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261021-0002.md | none | Governance 1.4.4과 current-facing 문서 정리 완료. DEFERRED 항목은 Revisit Condition이 충족되거나 사용자가 직접 묻기 전까지 일반 복구/무관한 보고에서 제외. 완료 Task의 오래된 Next Action은 실행하지 않음. | 2026-10-21 |
| TASK-20261021-0001 | Workspace | Governance | 임시 작업 지침을 실제 작업에 적용하고 기존 규칙의 충분성·효율성을 검증한 뒤 정식 반영 여부 판단 | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261021-0001.md | none | Closed on 2026-10-21 at user direction: no independent, measurable benefit from continuing the temporary guidance was established; existing Governance §§25-A-8, 27 and 28 remain unchanged. Do not automatically resume this trial. Reconsider only if repeated evidence identifies a genuine gap. | 2026-10-21 |
| TASK-20260930-0001 | Workspace | Governance | Development Work Continuity와 Task Recovery 구조를 완성하고 새 Chat에서도 정확한 Task와 Context를 복구할 수 있는 운영 구조를 구축 | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20260930-0001.md | PR #63 merged | Governance 1.3.1 반영 완료. 이후 활성 Task는 Governance/docs/DEVELOPMENT_TASKS.md에서 확인 | 2026-09-30 |
| TASK-20261020-0001 | Project | personal-ai-janggi-trainer-by-gpt | Personal AI Janggi Trainer v1.0의 대국·학습·브라우저 로컬 성장 기록을 완성하고 출시 검증 | COMPLETED | projects/personal-ai-janggi-trainer-by-gpt/docs/V1_RELEASE_SCOPE.md | projects/personal-ai-janggi-trainer-by-gpt/docs/checkpoints/TASK-20261020-0001.md | none | v1.0 release gates passed; live browser smoke run 39533158968 passed all 11 methods. No remaining v1.0 action; AI-strength calibration remains PAUSED. | 2026-10-21 |
| TASK-20260930-0002 | Project | personal-ai-janggi-trainer-by-gpt | 검색/평가/학습 구조를 기반으로 6개 공개 AI level의 측정 가능한 강도 차이를 확립하고 AI 성능을 단계적으로 강화 | PAUSED | projects/personal-ai-janggi-trainer-by-gpt/docs/CURRENT_STATUS.md | projects/personal-ai-janggi-trainer-by-gpt/docs/checkpoints/TASK-20260930-0002.md | PR #109 calibration trigger; PR #112 profiling; PR #119 draft candidate budget change (DO NOT MERGE) | Paused by the finalized v1.0 scope. Existing pair 2-3 evidence remains preserved; no seed 20261017 and no public AI-level/search-budget change. Reopen only as separate post-v1.0 research | 2026-10-20 |
| TASK-20261021-0003 | Workspace | Governance | Governance 1.4.4 상세 리뷰: 규칙 간 충돌, current-facing 상태의 정확성, 중복/복잡성 검토 및 명확한 문서 결함 수정 | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261021-0003.md | PR #159 merged | User approved Governance 1.4.5; PR #159 merged as `43a4e6a175949790ab974fd63456a35da0c6d7ae`. PR Workspace validation `39561842230` passed; post-merge main validation pending at completion of this checkpoint update. | 2026-10-21 |
| TASK-20261001-0001 | Workspace | Governance | 실제 운영 실패를 통해 검증된 원칙만 남기고, 증거 해석 오류와 과잉 복잡화를 방지하는 간결한 공통 Governance 운영체계를 확립 | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261001-0001.md | none | COMPLETED. Governance 1.3.3 review closed; its former calibration-resumption suggestion is historical only. The current calibration Task `TASK-20260930-0002` is PAUSED and is authoritative for execution eligibility. | 2026-10-01 |
| TASK-20261015-0001 | Workspace | Governance | Interaction 중간 보고·종료 상태·마일스톤 및 작업 효율 가시성 규칙을 명확히 하고 실제 작업 운영에 적용 | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261015-0001.md | PR #124 merged | Governance 1.4.2 merged to main; apply progress-reporting rules to future long-running work | 2026-10-15 |

## Operating Rules

1. Registry는 통합 탐색/선택 인덱스이며 상세 Source of Truth가 아닙니다.
2. Task의 상세 Context와 Checkpoint는 해당 Workspace/Project 영역에 저장합니다.
3. 같은 Project에 여러 Development Task가 존재할 수 있습니다.
4. Last Updated가 가장 최근이라는 이유만으로 해당 Task를 자동 선택하지 않습니다.
5. Request에서 Project, 작업 목적 또는 Task ID가 명확하면 그 Task를 선택합니다.
6. 관련 Task가 하나뿐이면 해당 Task를 복구합니다.
7. 여러 Task가 후보이고 Request로 구분할 수 없으면 최소한의 사용자 확인을 받습니다.
8. 기존 Task가 없고 새로운 개발 목표를 시작하는 경우 새 Task ID를 생성하고 Registry에 등록합니다.
9. Task가 완료되면 Registry에서 상태를 COMPLETED로 기록하고 상세 결과는 History에 남깁니다.
10. Task를 재개할 때는 Registry → Context → Checkpoint → 실제 GitHub/CI/Deployment 순으로 현재 상태를 검증합니다.
11. `Next Action`은 Registry Status가 `ACTIVE`인 Task에서만 실행 가능하다. 완료 Task의 Checkpoint는 결과 증거로만 읽으며, `DEFERRED` 이슈는 기록된 재검토 조건 없이는 일반 복구의 작업 후보로 올리지 않는다.
