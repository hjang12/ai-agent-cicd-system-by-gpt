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
| `ISSUE-002` | `BLOCKED` | `P2` | `Platform` | Janggi Render 서비스의 live `healthCheckPath`가 비어 있음 | 2026-10-20 read-only 재조회에서 service `srv-dajolip594qs73d1bkr0`의 metadata `healthCheckPath`는 여전히 빈 문자열. latest observed deployment `dep-dbbf251srm7s73858b5g` (commit `0338d442d04dba1521af19631360b01705d5e1e1`)는 `live`이고 startup logs는 port `10000` 바인딩을 보여 줌. 2026-10-20 사용자가 실제 브라우저에서 공개 앱 URL과 `/api/health`를 모두 열어 정상이라고 확인함. 반면 agent runtime에서는 앱 도메인뿐 아니라 `google.com`, `github.com`, `status.render.com` DNS도 실패하고 `curl`은 HTTP 전에 exit 6 (`Could not resolve host`)으로 중단됨. 따라서 agent runtime의 외부 DNS/네트워크 경로 문제는 강하게 확인됐으며, 해당 오류를 Render 서비스 장애로 분류하지 않음. 사용자 확인은 단순 공개 도달성 증거이며 상세 대국·학습 UX smoke를 대신하지 않음 | Render Dashboard의 해당 서비스 Settings → Health Checks → Edit에서 `/api/health`를 저장하도록 안내된 경로를 사용한 뒤 metadata/deploy를 재확인하고 `/api/health`와 실제 사용자 흐름 smoke 수행 | 연결된 Render MCP에는 기존 service의 health-check path mutation이 없고 이 실행 환경에는 Dashboard UI 조작/브라우저 세션이 없음. 공개 앱 URL과 `/api/health` 응답은 사용자가 브라우저에서 정상 접근했다고 확인했으므로 서비스가 전면 다운된 상태는 아님. agent runtime의 DNS/HTTP 확인 실패는 실행 환경 문제로 분리함. 이와 별개로 실제 `healthCheckPath`는 아직 빈 값이고 서비스 설정은 변경하지 않았음 | 2026-10-20 | `render.yaml`, `projects/personal-ai-janggi-trainer-by-gpt/app.py`, project release checkpoint, Render Health Checks docs (`https://render.com/docs/health-checks`), failed deploy `dep-dbbdol4s728c73bb450g`, verified-live deploy snapshot `dep-dbbf251srm7s73858b5g` |


## Operating Rules

1. AI는 새로운 문제나 개선 필요성을 발견하면 먼저 이 목록에 추가할 필요성이 있는지 판단한다.
2. 일회성 오류, 이미 해결된 문제, 단순 작업 메모는 Active Issue로 만들지 않는다.
3. 해결된 이슈는 검증 후 Active 목록에서 제거하고 `DEVELOPMENT_HISTORY.md`에 중요한 해결 사실을 기록한다.
4. `BLOCKED`는 단순히 작업을 안 한 상태가 아니라 **AI가 현재 권한·도구·외부 조건 때문에 진행할 수 없는 상태**에만 사용한다.
5. `DEFERRED`는 의도적인 우선순위 조정이며, 가능한 경우 이유와 재검토 조건을 남긴다.
6. `Next Action`은 가능한 한 현재 AI가 실제로 수행할 수 있는 다음 행동을 적는다.
7. 동일 문제를 여러 문서에 독립적으로 복제하지 않는다. 이 문서는 현재 상태를 요약하고, 상세 기록은 원본 문서로 연결한다.
8. 상태가 변경되면 `Last Verified`와 필요 시 `Related`를 함께 갱신한다.
