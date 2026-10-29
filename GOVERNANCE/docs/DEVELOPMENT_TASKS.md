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

| Task ID | Scope | Project / Area | Goal | Status | Context | Current Checkpoint | Active PR / Issue | State Summary | Last Updated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TASK-20261029-0001 | Project | soldier-gate-runner-by-gpt | Add selectable five-lane gameplay mode and fix overlapping topbar/HUD layout | COMPLETED | projects/soldier-gate-runner-by-gpt/docs/CURRENT_STATUS.md | projects/soldier-gate-runner-by-gpt/docs/checkpoints/TASK-20261029-0001.md | PR #229 merged; PR-head and main Game CI / Workspace validation passed; Render deploy LIVE | PR #229 merged as `62380e28239ea5f13b8826f9389a4340282cd1f5`. PR-head Game CI 40847927556 passed 35 browser acceptance tests; main Game CI 40848311436 passed 35 tests; PR/main Workspace validation 40847927665 and 40848311435 passed. Render deployment `dep-dbhguuvb9u1s739rir10` reached LIVE on the same merge commit after checks passed. Direct deployed-URL browser smoke remains UNVERIFIED because the agent environment could not access the public host; this is not evidence that the site is down. | 2026-10-29 |
| TASK-20261023-0003 | Project | soldier-gate-runner-by-gpt | Build a polished single-mission browser game with longer replayable content, without AI-model work or app-store release | COMPLETED | projects/soldier-gate-runner-by-gpt/docs/CURRENT_STATUS.md | projects/soldier-gate-runner-by-gpt/docs/checkpoints/TASK-20261023-0003.md | PR #222 merged; no active implementation PR | PR #222 merged as `e1237a49f8a10f52672c109a723df824a7030fef`, removing dedicated landscape/orientation-lock and fullscreen features while preserving ×1/×2/×3/×4 speed controls, RESET, steering, and responsive layout. PR Game CI 40823478762 and main Game CI 40823758797 each passed 33 browser acceptance tests; PR/main Workspace validation 40823478651 and 40823758798 passed. Render deployment dep-dbhdl1lckfvc73f95em0 for the merge commit reached LIVE at 2026-10-29 05:33:05 UTC. Feature work closed at user-approved scope; concrete bug/regression fixes only. Stale PR #200 remains open and is superseded; do not merge it. | 2026-10-29 |
| TASK-20261023-0002 | Workspace | Governance | Continue evidence-based Governance improvement using new operational evidence, without repeating closed audits or adding rules without evidence | ACTIVE | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261023-0002.md | PR #213 merged; ISSUE-003 IN PROGRESS | Governance 1.4.8 clarifies request intent and production smoke evidence; Gatefront current-facing status is reconciled. Render Build Filter paths are directly observed configured. Governance-only commit f04f29db passed Workspace validation and has no Render deployment record, though no explicit ignored-commit event was returned. Positive-path deploy verification awaits the next legitimate Gatefront runtime change. Production smoke automation remains deferred. | 2026-10-29 |
| TASK-20261023-0001 | Workspace | Governance / Context Recovery | Verify new-chat recovery of the Governance-improvement goal and executable Next Action from repository state using only the minimal continuation prompt | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261023-0001.md | none | Closed 2026-10-23: the fresh-chat test recovered the ACTIVE task, its broader/immediate purpose, and Next Action; PR #168 merge and Workspace validation run 39898493912 verified. No concrete Governance gap found; version 1.4.7 unchanged. | 2026-10-23 |
| TASK-20261022-0003 | Project | personal-ai-janggi-trainer-by-gpt | Improve the visual polish of the existing board-first trainer UI while preserving active UX contracts and v1.0 gameplay behavior | COMPLETED | projects/personal-ai-janggi-trainer-by-gpt/docs/CURRENT_STATUS.md | projects/personal-ai-janggi-trainer-by-gpt/docs/checkpoints/TASK-20261022-0003.md | none | Closed after PR #166 merged as `2feb15a00abd88e9170c731c6d868201d97a7310`. Workspace validation, Janggi Python/Requirement Contract tests, and Chromium browser acceptance all passed. Render deployment `dep-dbcs5m3bc2fs738pojfg` reached LIVE on the merge commit. | 2026-10-22 |
| TASK-20261022-0002 | Workspace | Governance / CI validation | Add regression guard for Governance version synchronization and trigger workspace validation for tools changes | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261022-0002.md | none | Closed 2026-10-22 after PR #164 merged as `fb1e0240ba4047a7097cbd0223d185eb315c1355`. Final PR-head Workspace validation run `39742003392` passed the 5 focused tests and existing workspace/Render checks. Post-merge push-run result was not directly observable through the available run query and is not claimed as passed. | 2026-10-22 |
| TASK-20261022-0001 | Workspace | Governance / CI-CD / Janggi release verification | Detailed Governance review, post-merge record reconciliation, implement and verify actual CI-gated Render deployment, and confirm Janggi v1.0 release remains stable | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261022-0001.md | none | Closed 2026-10-22. PR #161 merged as `d74f114149bf5c016e509ab94e3d08b887d00adb`; four CI checks passed, both Render services reported `checksPass`, and both deployments reached LIVE after the final CI check passed. ISSUE-001 resolved. v1.0 remains complete; calibration remains PAUSED. | 2026-10-22 |
| TASK-20261021-0002 | Workspace | Governance | Context Recovery에서 DEFERRED 항목 및 완료된 Checkpoint Next Action이 현재 작업으로 반복 노출되지 않도록 상태 권한과 보고 범위를 명확화 | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261021-0002.md | none | Closed; DEFERRED items remain only in the canonical issue index until directly requested or a revisit condition occurs. | 2026-10-21 |
| TASK-20261021-0001 | Workspace | Governance | 임시 작업 지침을 실제 작업에 적용하고 기존 규칙의 충분성·효율성을 검증한 뒤 정식 반영 여부 판단 | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261021-0001.md | none | Closed on 2026-10-21 at user direction; no separate temporary-guidance package remains active. | 2026-10-21 |
| TASK-20260930-0001 | Workspace | Governance | Development Work Continuity와 Task Recovery 구조를 완성하고 새 Chat에서도 정확한 Task와 Context를 복구할 수 있는 운영 구조를 구축 | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20260930-0001.md | PR #63 merged | Closed; Registry and Checkpoint structure was merged through PR #63. | 2026-09-30 |
| TASK-20261020-0001 | Project | personal-ai-janggi-trainer-by-gpt | Personal AI Janggi Trainer v1.0의 대국·학습·브라우저 로컬 성장 기록을 완성하고 출시 검증 | COMPLETED | projects/personal-ai-janggi-trainer-by-gpt/docs/V1_RELEASE_SCOPE.md | projects/personal-ai-janggi-trainer-by-gpt/docs/checkpoints/TASK-20261020-0001.md | none | v1.0 release gates and 11-method live browser smoke passed; AI-level calibration remains PAUSED as separate research. | 2026-10-21 |
| TASK-20260930-0002 | Project | personal-ai-janggi-trainer-by-gpt | 검색/평가/학습 구조를 기반으로 6개 공개 AI level의 측정 가능한 강도 차이를 확립하고 AI 성능을 단계적으로 강화 | PAUSED | projects/personal-ai-janggi-trainer-by-gpt/docs/CURRENT_STATUS.md | projects/personal-ai-janggi-trainer-by-gpt/docs/checkpoints/TASK-20260930-0002.md | PR #109 calibration trigger; PR #112 profiling; PR #119 draft candidate budget change (DO NOT MERGE) | Paused post-v1.0; preserved evidence is insufficient for adjacent pair 2-3. Do not run seeds or change public levels/budgets unless explicitly resumed. | 2026-10-20 |
| TASK-20261021-0003 | Workspace | Governance | Governance 1.4.4 상세 리뷰: 규칙 간 충돌, current-facing 상태의 정확성, 중복/복잡성 검토 및 명확한 문서 결함 수정 | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261021-0003.md | PR #159 merged | Completed through approved PR #159; Governance 1.4.5 was adopted. | 2026-10-21 |
| TASK-20261021-0004 | Workspace | Governance | 남은 Governance 모순 제거와 문서·템플릿 간소화, 권한·배포 경계 명확화 | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261021-0004.md | PR #160 merged (`a65ef98be8d83b2992e40c226159c2ef683cbb8c`) | Closed after Governance 1.4.6 was approved and squash-merged on 2026-10-22. Post-merge audit found stale Registry / Status / Checkpoint text; the follow-up reconciliation completed under TASK-20261022-0001. | 2026-10-22 |
| TASK-20261001-0001 | Workspace | Governance | 실제 운영 실패를 통해 검증된 원칙만 남기고, 증거 해석 오류와 과잉 복잡화를 방지하는 간결한 공통 Governance 운영체계를 확립 | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261001-0001.md | none | Closed with Governance 1.3.3; its former calibration handoff is historical, and the current calibration Task remains PAUSED. | 2026-10-01 |
| TASK-20261015-0001 | Workspace | Governance | Interaction 중간 보고·종료 상태·마일스톤 및 작업 효율 가시성 규칙을 명확히 하고 실제 작업 운영에 적용 | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261015-0001.md | PR #124 merged | Closed; Governance 1.4.2 progress-reporting rules were merged and verified. | 2026-10-15 |

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
12. `State Summary`는 Task 선택을 돕는 간단한 요약이며 실행 지시가 아닙니다. 실제 실행 단계는 Registry가 가리키는 Checkpoint의 `Next Action` 한곳에만 기록합니다. `COMPLETED` / `ARCHIVED` 요약은 종료 결과, `PAUSED` / `BLOCKED` 요약은 재개 조건 또는 Blocker만 담습니다. Status와 Checkpoint가 불일치하면 먼저 문서를 동기화하고, 과거 요약을 대체 지시로 실행하지 않습니다.
