# Current Status

## Governance

- Governance Version: `1.0.0`
- Status: Active baseline on `main`
- Current canonical workspace repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Default / working branch: `main`
- Main branch protection: not enabled

## Canonical Workspace

The GPT development workspace is a private GitHub monorepo.

```text
hjang12/ai-agent-cicd-system-by-gpt/
├── GOVERNANCE/
├── projects/
│   ├── personal-ai-janggi-trainer-by-gpt/
│   └── time-dashboard-by-gpt/
├── .github/workflows/
└── render.yaml
```

### Canonical paths

- `AGENT_START.md` — workspace-level session entrypoint
- `AGENTS.md` — workspace-level agent rules
- `GOVERNANCE/GOVERNANCE.md` — common operating rules
- `GOVERNANCE/docs/CURRENT_STATUS.md` — this workspace status
- `GOVERNANCE/docs/DEVELOPMENT_HISTORY.md` — long-term governance/workspace history
- `GOVERNANCE/docs/ADR/` — architecture and operating decisions
- `projects/<project>/AGENT_START.md` — project session entrypoint
- `projects/<project>/AGENTS.md` — project-specific agent rules
- `projects/<project>/docs/CURRENT_STATUS.md` — project context
- `.github/workflows/` — monorepo CI and benchmark workflows
- `render.yaml` — monorepo Render Blueprint

## Project Status

### Personal AI Janggi Trainer

- Canonical path: `projects/personal-ai-janggi-trainer-by-gpt/`
- Source snapshot: `hjang12/personal-ai-janggi-trainer-by-gpt` @ `83932421217f149de46e6e23b89aff9d92467a11`
- Latest central fixes are included after migration.
- Domain, engine, search, coaching, training/evaluation, and browser/API layers are present as documented in the project Context.
- Current CI: `.github/workflows/janggi-validation.yml`
- Search benchmark: `.github/workflows/janggi-search-benchmark.yml`
- Latest central validation and benchmark runs for `dbd6b52432a628a4b92e4fd586be0fae26672325`: both `success`.
- Render cutover to the monorepo repository/root directory is pending final live-service verification.

### Time Dashboard

- Canonical path: `projects/time-dashboard-by-gpt/`
- Source snapshot: `hjang12/time-dashboard-by-gpt` @ `fb8e98baa7a81a610c2ccbf767f2995fb9af0a3f`
- Primary server: `timefolio_server.py`
- Backend regression test suite is preserved under `tests/`.
- Current CI: `.github/workflows/time-dashboard-ci.yml`
- The source repository's latest CI before migration was successful on `fb8e98...`.
- Render cutover to the monorepo repository/root directory is pending final live-service verification.

## Migration Record

The monorepo consolidation was committed to `main` on 2026-09-18.

Key commits:

- `1d91810ba4389205801e751ef0856eb82e4dd583` — consolidate Governance and GPT projects
- `92cf6a38532886a6cb92afacc3d3e817c65b3571` — fix monorepo agent metadata and PWA icon type
- `dbd6b52432a628a4b92e4fd586be0fae26672325` — fix validation/benchmark semantics

The original project repositories remain available as historical source snapshots. They are not the canonical development locations after migration.

## CI/CD State

Current root workflows:

- Janggi validation — success on current `main`
- Janggi search benchmark — success on current `main`
- Time Dashboard CI — last executed successfully on the migration commit sequence

The first monorepo Janggi validation/benchmark runs failed because the migrated test/benchmark files still reflected pre-monorepo assumptions. The subsequent fixes are now green. The actual current GitHub Actions result, not the historical failure, is the operative state.

## Render State — Verified 2026-09-18

Render workspace: `My Workspace` (`tea-da7sjdgu01pc73bsno6g`).

The current live services are still connected to the historical project repositories, not the monorepo:

| Service | Repository | Root Directory | Branch | Auto Deploy | Latest Live Deploy |
| --- | --- | --- | --- | --- | --- |
| `personal-ai-janggi-trainer-by-gpt` | `hjang12/personal-ai-janggi-trainer-by-gpt` | empty | `main` | yes | `83932421217f149de46e6e23b89aff9d92467a11` |
| `time-dashboard-by-gpt` | `hjang12/time-dashboard-by-gpt` | empty | `main` | yes | `fb8e98baa7a81a610c2ccbf767f2995fb9af0a3f` |

Both services are active and their latest listed deployment has status `live`.

The repository `render.yaml` already defines the desired monorepo Root Directories, but **Render has not been switched to that configuration yet**.

Current migration state is therefore **GitHub-complete / Render-cutover-pending**.

The available Render toolset can inspect and deploy existing services but does not expose an update operation for changing an existing service's Git Repository or Root Directory. Do not create duplicate services merely to simulate the cutover.

After the service settings are changed in Render, re-run verification for repository mapping, Root Directory, latest deployment, logs, and health/smoke behavior.

## Canonical Operating Model

```text
Requirement
→ AI Coding Agent
→ Monorepo project path
→ CI / Verification
→ Render deployment
→ Post-deployment verification
→ Documentation / History update
```

Chat history is temporary. The monorepo Repository is the long-term Source of Truth.

## Known Limitations / Pending Cleanup

- The old `-by-gpt` source repositories have not been archived or deleted; they remain historical snapshots until an explicit cleanup action is performed.
- No destructive repository deletion is performed as part of this migration record.
- Render service cutover has not yet been verified in the current workspace session.
- The connected GitHub repository list currently exposes the GPT monorepo and the two historical project repositories; no active `personal-mcp-server` repository was present in that current list, so older documentation referring to it is treated as stale.

## Current Priority

1. Verify and complete Render repository/root-directory cutover for both services.
2. Run post-deployment health/smoke checks and record the result.
3. Synchronize project Context documents with the final live deployment state.
4. Freeze the old project repositories as historical sources; archive/delete only through an explicit destructive-action step.
5. Continue future development only under `projects/<project>/`.

## Next Development Candidates

- Strengthen monorepo-wide validation of required project boundaries and deployment configuration.
- Add higher-value service smoke/browser checks where justified.
- Continue Janggi coaching/search work only from documented fixtures and regression evidence.
- Continue Time Dashboard parser/reliability improvements without crossing the UI/backend boundary.
