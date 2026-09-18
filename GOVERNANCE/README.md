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
│   ├── DEVELOPMENT_HISTORY.md
│   └── ADR/
└── templates/
```

프로젝트 코드는 `projects/<project>/` 아래에 있으며, 프로젝트별 상세 Architecture/Context는 각 프로젝트 디렉터리에서 관리합니다.

## Agent startup

새 Agent 또는 새 ChatGPT 세션에서는 전체 Repository를 대화 기록으로 복원하려 하지 않습니다.

1. `/AGENT_START.md`
2. `/GOVERNANCE/GOVERNANCE.md`
3. 작업 대상 `projects/<project>/AGENT_START.md`
4. 작업 대상 `projects/<project>/AGENTS.md`
5. 작업 대상 `projects/<project>/docs/CURRENT_STATUS.md`
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
