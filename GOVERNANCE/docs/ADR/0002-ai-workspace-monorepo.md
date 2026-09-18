# ADR 0002 — AI Workspace Monorepo

- Status: Accepted
- Date: 2026-09-18
- Scope: Workspace Repository structure
- Related: `GOVERNANCE/MIGRATION.md`

## Context

GPT를 이용해 여러 장기 프로젝트를 반복적으로 개발하면서 프로젝트마다 별도 GitHub Repository를 생성하고 Agent 접근 권한을 연결하는 운영 비용이 커졌다.

기존 구조는 다음과 같은 독립 Repository였다.

```text
ai-agent-cicd-system-by-gpt
personal-ai-janggi-trainer-by-gpt
time-dashboard-by-gpt
```

공통 Governance와 여러 프로젝트가 서로 다른 Repository에 분산되면 새 프로젝트마다 Repository 생성, 권한 연결, CI 구성, Context 연결, 배포 Repository 연결을 반복해야 한다.

## Decision

GPT 개발 작업의 기본 Workspace를 하나의 private GitHub monorepo로 운영한다.

```text
hjang12/ai-agent-cicd-system-by-gpt/
├── GOVERNANCE/
├── projects/
│   ├── personal-ai-janggi-trainer-by-gpt/
│   └── time-dashboard-by-gpt/
├── .github/workflows/
└── render.yaml
```

공통 Governance는 `GOVERNANCE/`에 두고, 각 제품은 독립된 `projects/<project>/` 경계를 유지한다.

프로젝트별 CI workflow는 root `.github/workflows/`에 두고 해당 프로젝트 경로를 대상으로 한다.

Render는 monorepo를 하나의 Git source로 사용하되 서비스별 Root Directory를 프로젝트 디렉터리로 분리한다.

## Consequences

### Positive

- GitHub 접근 권한과 Source of Truth를 Workspace 하나로 단순화한다.
- 새 프로젝트는 `projects/<project>/`를 추가하는 방식으로 시작할 수 있다.
- 공통 Governance와 프로젝트 Context를 같은 Repository에서 함께 추적할 수 있다.
- 프로젝트별 CI가 path filter를 사용하므로 무관한 프로젝트 변경으로 검증 범위를 불필요하게 넓히지 않는다.
- Render 서비스는 각 프로젝트 Root Directory를 통해 배포 경계를 유지할 수 있다.

### Negative / Trade-offs

- 하나의 Repository에 여러 프로젝트가 존재하므로 root 수준의 문서·CI 변경 영향 범위를 명확히 관리해야 한다.
- Repository 전체 history가 각 원본 Project Repository의 Git history를 그대로 보존하지는 않는다.
- Binary 파일 이동/변환 시 source snapshot과 byte-for-byte 동일성이 깨질 수 있다. Time Dashboard icon이 이에 해당한다.
- Destructive cleanup of old repositories remains a separate lifecycle step.

## Migration

원본 Snapshot:

- Governance: `hjang12/ai-agent-cicd-system-by-gpt` @ `a3fd6fe90f8fe9be3a84436e7a66894d9628b5d8`
- Janggi: `hjang12/personal-ai-janggi-trainer-by-gpt` @ `83932421217f149de46e6e23b89aff9d92467a11`
- Time Dashboard: `hjang12/time-dashboard-by-gpt` @ `fb8e98baa7a81a610c2ccbf767f2995fb9af0a3f`

Migration implementation commit:

- `1d91810ba4389205801e751ef0856eb82e4dd583`

Follow-up fixes:

- `92cf6a38532886a6cb92afacc3d3e817c65b3571`
- `dbd6b52432a628a4b92e4fd586be0fae26672325`

The source repositories remain available as historical snapshots. Future development should target the monorepo paths, not the old repositories.

## Verification

- Central directory structure exists on `main`.
- Janggi and Time Dashboard source trees were compared against their source HEAD trees.
- Janggi migration-specific test/benchmark adjustments were verified by GitHub Actions.
- Current monorepo Janggi validation: success.
- Current monorepo Janggi search benchmark: success.
- Time Dashboard migrated CI workflow: successful during the migration commit sequence.

## Pending

- Render workspace/service repository mapping must be verified in the live workspace.
- Old source repositories have not been archived/deleted.
