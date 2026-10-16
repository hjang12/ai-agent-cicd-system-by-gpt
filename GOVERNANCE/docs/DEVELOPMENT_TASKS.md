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
| TASK-20260930-0001 | Workspace | Governance | Development Work Continuity와 Task Recovery 구조를 완성하고 새 Chat에서도 정확한 Task와 Context를 복구할 수 있는 운영 구조를 구축 | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20260930-0001.md | PR #63 merged | Governance 1.3.1 반영 완료. 다음 활성 Task는 TASK-20260930-0002 | 2026-09-30 |
| TASK-20260930-0002 | Project | personal-ai-janggi-trainer-by-gpt | 검색/평가/학습 구조를 기반으로 6개 공개 AI level의 측정 가능한 강도 차이를 확립하고 AI 성능을 단계적으로 강화 | ACTIVE | projects/personal-ai-janggi-trainer-by-gpt/docs/CURRENT_STATUS.md | projects/personal-ai-janggi-trainer-by-gpt/docs/checkpoints/TASK-20260930-0002.md | PR #135 open | Protocol-v3 pair 2-3 has 6 completed games / 3 seeds: Lv.2 0.5, Lv.3 5.5, 5 higher-level wins and 1 draw; INSUFFICIENT vs 20-game threshold. Merge PR #135 after latest CI passes, then run bounded seed 20261009 with runner disabled between batches; no public budget changes | 2026-10-16 |
| TASK-20261001-0001 | Workspace | Governance | 실제 운영 실패를 통해 검증된 원칙만 남기고, 증거 해석 오류와 과잉 복잡화를 방지하는 간결한 공통 Governance 운영체계를 확립 | COMPLETED | GOVERNANCE/docs/CURRENT_STATUS.md | GOVERNANCE/docs/checkpoints/TASK-20261001-0001.md | none | Governance 1.3.3 review completed; resume the Janggi calibration task | 2026-10-01 |
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
