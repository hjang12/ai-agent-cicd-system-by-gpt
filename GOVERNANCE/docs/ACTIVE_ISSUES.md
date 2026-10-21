# Active Issues

> AI 운영용 현재 이슈 인덱스.
>
> 이 문서는 **현재 해결되지 않았거나 추적이 필요한 항목만** 관리한다.
> 상세 원인·논의·결정의 원본은 관련 GitHub Issue, ADR, `DEVELOPMENT_HISTORY.md` 또는 프로젝트 문서를 참조한다.
>
> **Authoritative rule:** 이 파일은 Workspace의 "현재 active issue 목록과 상태"에 대한 Source of Truth다.

## Status Model

| Status | Meaning |
| --- | --- |
| `OPEN` | 해결 작업이 아직 본격적으로 시작되지 않음 |
| `IN PROGRESS` | AI가 현재 해결 작업을 수행 중 |
| `BLOCKED` | 외부 권한·플랫폼·사용자 판단 등으로 진행이 중단됨 |
| `DEFERRED` | 현재는 의도적으로 미룸 |
| `RESOLVED` | 해결 및 검증 완료. Active 목록에서 제거 가능 |

## Issue Model

각 이슈는 가능한 한 다음 필드를 유지한다.

| Field | Purpose |
| --- | --- |
| `ID` | Workspace에서 영구 추적할 Issue 식별자 |
| `Status` | 현재 상태 |
| `Priority` | `P0` / `P1` / `P2` / `P3` |
| `Scope` | `Governance` / `Workspace` / `Project` / `CI/CD` / `Platform` 등 |
| `Summary` | 한 줄 요약 |
| `Impact` | 해결되지 않았을 때의 현재 영향 |
| `Next Action` | AI가 다음에 수행할 작업 |
| `Blocker` | 진행을 막는 조건. 없으면 `None` |
| `Last Verified` | 마지막으로 실제 상태를 확인한 날짜 |
| `Related` | 관련 ADR / Issue / Commit / 문서 경로 |

## Active Issue Register

| ID | Status | Priority | Scope | Summary | Impact | Next Action | Blocker | Last Verified | Related |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ISSUE-001` | `BLOCKED` | `P1` | `CI/CD` | CI 성공을 Render 배포의 필수 선행조건으로 강제하는 strict gate 미구현 | CI 실패와 Render auto deploy가 독립적으로 발생할 수 있어 배포 신뢰성 경계가 완전하지 않음. Requirement Contract CI guard는 추가했지만, main branch protection이 꺼져 있어 직접 push를 merge 전 차단하지는 못함 | GitHub branch protection / ruleset 및 Render deployment policy의 자동화 가능 범위를 재검토하고 가능한 경로 설계 | 현재 연결된 GitHub/Render 도구에서 필요한 기존 설정 mutation을 제공하지 않음 | 2026-09-29 | `GOVERNANCE/docs/CURRENT_STATUS.md`, PR #50, `GOVERNANCE/docs/DEVELOPMENT_HISTORY.md` |
| `ISSUE-002` | `DEFERRED` | `P3` | `Platform` | Janggi Render service metadata has empty `healthCheckPath` while the repository Blueprint declares `/api/health` | This is confirmed configuration drift, but no current release impact is observed. Render documents HTTP health checks as optional for web services; when no HTTP path is configured, default TCP checks apply. Latest deployment `dep-dbc26arm8hqs73bcbmbg` is `live`; the public `/api/health` readiness check and all 11 live-browser smoke tests passed in run `39533158968`. This is configuration hygiene, not evidence of an outage or a blocker for v1.0. | Revisit only if the service is brought under active Blueprint synchronization, HTTP-level readiness monitoring becomes an explicit requirement, or a live health/browser smoke regression occurs. Do not block v1.0 or surface this as the current task. | None for the current release. The connected Render integration cannot mutate this existing setting, but no such mutation is required to close v1.0 under the verified live behavior. | 2026-10-21 | `render.yaml`, `projects/personal-ai-janggi-trainer-by-gpt/app.py`, `projects/personal-ai-janggi-trainer-by-gpt/docs/V1_RELEASE_SCOPE.md`, Render Health Checks docs (`https://render.com/docs/health-checks`), deployment `dep-dbc26arm8hqs73bcbmbg`, smoke run `39533158968` |

## Operating Rules

1. AI는 새로운 문제나 개선 필요성을 발견하면 먼저 이 목록에 추가할 필요성이 있는지 판단한다.
2. 일회성 오류, 이미 해결된 문제, 단순 작업 메모는 Active Issue로 만들지 않는다.
3. 해결된 이슈는 검증 후 Active 목록에서 제거하고 `DEVELOPMENT_HISTORY.md`에 중요한 해결 사실을 기록한다.
4. `BLOCKED`는 단순히 작업을 안 한 상태가 아니라 **AI가 현재 권한·도구·외부 조건 때문에 진행할 수 없는 상태**에만 사용한다.
5. `DEFERRED`는 의도적인 우선순위 조정이며, 가능한 경우 이유와 재검토 조건을 남긴다.
6. `Next Action`은 가능한 한 현재 AI가 실제로 수행할 수 있는 다음 행동을 적는다.
7. 동일 문제를 여러 문서에 독립적으로 복제하지 않는다. 이 문서는 현재 상태를 요약하고, 상세 기록은 원본 문서로 연결한다.
8. 상태가 변경되면 `Last Verified`와 필요 시 `Related`를 함께 갱신한다.
9. `DEFERRED` 항목은 이 목록에 보존하되 일반 Context Recovery / 무관한 상태 보고에 반복하지 않는다. 사용자 직접 질문, 기록된 Revisit Condition 발생 또는 위험을 바꾸는 새 직접 증거가 있을 때만 보고한다. 그 외 문서에 현재 Blocker나 Active Task로 복제하지 않는다.
