# Project Inventory

정리 작업의 기준이 되는 현재 프로젝트 및 배포 자산 목록이다. 이 문서는 2026-09-15 실제 GitHub/Render 상태를 기준으로 작성하며, 변경 시 확인 결과를 갱신한다.

## Active projects

| Project | GitHub Repository | Default Branch | Render | Status |
|---|---|---|---|---|
| AI Janggi Trainer | `hjang12/personal-ai-janggi-trainer` | `main` | `personal-ai-janggi-trainer` Web Service | Active |
| Time Dashboard | `hjang12/time-dashboard` | `main` | `time-dashboard` Web Service | Active |
| Personal MCP Server | `hjang12/personal-mcp-server` | `main` | No Render service confirmed | Active / tooling |

## Governance

| Asset | Purpose | Status |
|---|---|---|
| `hjang12/ai-agent-cicd-system` | Common AI Coding Agent Governance | Review candidate v1.0.0 |
| `governance-v1.0.0` | Governance working branch | Active |
| PR #1 | Governance v1.0.0 proposal | Open |
| Issue #2 | Platform cleanup / Yeosamo retirement | Open |

## Retiring project

| Project | GitHub Repository | Render Service(s) | Status |
|---|---|---|---|
| Project Yeosamo | `hjang12/project-yeosamo` | `project-yeosamo`, `project-yeosamo-app` | Retiring |

### Render details confirmed

- Workspace: `My Workspace`
- `personal-ai-janggi-trainer`: Web Service, Python, `main`, auto deploy, Singapore, free plan
- `time-dashboard`: Web Service, Python, `main`, auto deploy, Oregon, free plan
- `project-yeosamo`: Static Site, `main`, auto deploy, `dist` publish path, Oregon, free plan
- `project-yeosamo-app`: Web Service, Node, `main`, auto deploy, Oregon, free plan

Both Yeosamo Render services point to the same GitHub Repository. The duplication is considered legacy configuration unless a documented purpose exists.

## Target topology

```text
GitHub Organization / Account Namespace
├── ai-agent-cicd-system
├── personal-ai-janggi-trainer
├── time-dashboard
└── personal-mcp-server

Render Workspace
├── personal-ai-janggi-trainer Project
│   └── Production → personal-ai-janggi-trainer Service
├── time-dashboard Project
│   └── Production → time-dashboard Service
└── personal-mcp-server Project (when deployment is required)
```

## Cleanup execution state — 2026-09-15

### Completed

- Actual GitHub Repository list verified.
- Actual Render Workspace/Service list verified.
- Yeosamo resources identified as retiring targets.
- Governance topology/lifecycle rules documented.
- Cleanup tracking recorded in Issue #2.

### Not completed

- `project-yeosamo` Render Service deletion.
- `project-yeosamo-app` Render Service deletion.
- `hjang12/project-yeosamo` Archive/Delete.
- GitHub Organization creation.
- Active Repository transfer to an Organization.
- Render Project/Environment restructuring.

The connected tool set does not expose these destructive/migration operations directly. Do not mark them complete until the actual platform resource state is rechecked.

## Verification rule

Never mark a resource as deleted, migrated, or retired merely because a plan or code change exists. The resource must be checked directly in the relevant platform and the result recorded.
