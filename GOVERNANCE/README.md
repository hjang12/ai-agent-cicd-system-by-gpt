# AI Agent CI/CD Governance

이 디렉터리는 GPT 개발 Workspace에서 사용하는 공통 Governance를 관리합니다.

공통 Governance는 제품 코드와 분리된 운영 규칙이지만, 현재는 별도 Repository가 아니라 다음 단일 Workspace Repository 안에서 관리합니다.

`hjang12/ai-agent-cicd-system-by-gpt`

## Canonical structure

```text
GOVERNANCE/
├── AGENT_START.md
├── GOVERNANCE.md
├── VERSION
├── CHANGELOG.md
├── MIGRATION.md
├── docs/
│   ├── CURRENT_STATUS.md
│   ├── DEVELOPMENT_TASKS.md
│   ├── DEVELOPMENT_HISTORY.md
│   └── ADR/
└── templates/
```

프로젝트 코드는 `projects/<project>/` 아래에 있으며, 프로젝트별 상세 Architecture/Context는 각 프로젝트 디렉터리에서 관리합니다.

## Agent startup

새 Agent 또는 새 Chat에서는 전체 Repository를 대화 기록으로 복원하려 하지 않습니다.

1. `/AGENT_START.md`
2. `/GOVERNANCE/GOVERNANCE.md`
3. `/GOVERNANCE/docs/DEVELOPMENT_TASKS.md`에서 Request에 해당하는 Development Task를 식별
4. 해당 Task의 Workspace / Project Context와 Checkpoint 확인
5. 작업 대상 `projects/<project>/AGENT_START.md` / `AGENTS.md` / `docs/CURRENT_STATUS.md` 확인
6. 실제 코드 / 테스트 / CI / Render 상태

를 현재 Repository와 실행 결과를 기준으로 확인합니다.

## Operating principles

- GitHub Repository를 Source of Truth로 사용합니다.
- 프로젝트 간 디렉터리 경계를 유지합니다.
- 기존 코드를 이해한 후 최소 범위로 변경합니다.
- 코드 작성만으로 완료 처리하지 않고 Test / Regression / Deployment / Post-deployment 상태를 구분합니다.
- 중요한 결정과 운영 변경은 ADR, Change Record, Context, Commit 이력 등 적절한 형태로 남깁니다.
- 특정 AI 제품이나 IDE에 종속되는 개발 구조를 Governance에 포함하지 않습니다.

세부 규칙은 `GOVERNANCE/GOVERNANCE.md`가 공식 기준입니다.

## Development Work Continuity

이 Governance의 장기 개발 단위는 **Development Task**입니다. 특정 Chat이 장기 작업의 보존 단위가 되지 않도록 합니다.

Chat이 변경되거나 Agent Work가 중단되어도 다음 기록을 통해 작업을 복구합니다.

- DEVELOPMENT_TASKS.md — Development Task 식별과 Context / Checkpoint 경로 탐색
- CURRENT_STATUS.md — 현재 상태
- ACTIVE_ISSUES.md — 현재 미해결 이슈
- Checkpoint — 단기 복구 기준점
- DEVELOPMENT_HISTORY.md / ADR / Evidence — 결정과 장기 이력
- GitHub Commit / PR / CI / Deployment — 실제 실행 상태

새 Chat에서 작업을 재개할 때는 **Context Recovery**를 수행하고, 이전 Chat의 기억을 추측하여 상태를 복원하지 않습니다.
