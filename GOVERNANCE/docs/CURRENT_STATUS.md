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
- Workspace validation: `.github/workflows/workspace-validation.yml`
- Latest Janggi validation during this maintenance sequence: success on `91c7ef5`.
- Render cutover is complete: the existing service now points to the canonical monorepo and the project Root Directory.

### Time Dashboard

- Canonical path: `projects/time-dashboard-by-gpt/`
- Source snapshot: `hjang12/time-dashboard-by-gpt` @ `fb8e98baa7a81a610c2ccbf767f2995fb9af0a3f`
- Primary server: `timefolio_server.py`
- Backend regression test suite is preserved under `tests/`.
- Current CI: `.github/workflows/time-dashboard-ci.yml`
- The source repository's latest CI before migration was successful on `fb8e98...`.
- Render cutover is complete: the existing service now points to the canonical monorepo and the project Root Directory.

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

Render service cutover is complete. Both existing services now use the canonical monorepo with project-specific Root Directories:

| Service | Repository | Root Directory | Branch | Auto Deploy | Latest Live Deploy |
| --- | --- | --- | --- | --- | --- |
| `personal-ai-janggi-trainer-by-gpt` | `hjang12/ai-agent-cicd-system-by-gpt` | `projects/personal-ai-janggi-trainer-by-gpt` | `main` | yes | `51fc3322121167f1c48eb339bbe91bf69858c551` |
| `time-dashboard-by-gpt` | `hjang12/ai-agent-cicd-system-by-gpt` | `projects/time-dashboard-by-gpt` | `main` | yes | `51fc3322121167f1c48eb339bbe91bf69858c551` |

Both services are active and their latest cutover deployments are `live`.

Deployment verification:
- Janggi deploy `dep-damckfad0e5s73eu325g`: `live`; build succeeded; `python app.py` started; Render reported the service live at its primary URL.
- Time Dashboard deploy `dep-damckue7bikc73b4p7ng`: `live`; build succeeded; `python timefolio_server.py` started; a `HEAD /` request returned HTTP 200; Render reported the service live at its primary URL.
- Time Dashboard had one immediate cutover build failure because `requirements.txt` was not found, followed by a successful retry after the service Root Directory was correctly applied.
- Current Render service `healthCheckPath` remains empty for both services. The applications expose Janggi `/api/health`; Time Dashboard has a root endpoint returning HTTP 200. Explicit Render health-check configuration is therefore still a platform-setting improvement, not a deployment blocker.

The available Render toolset still does not expose an update operation for existing service Git Repository / Root Directory settings; the actual cutover was performed in the Render Dashboard and then verified through the connected Render API/tooling. No duplicate services were created.

Current migration state is **GitHub-complete / Render-cutover-complete / legacy-repository-cleanup-pending**.

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
- Pre-deletion gate verification completed on 2026-09-18: both legacy repositories retain only their historical migration snapshot heads; both Render services point to the canonical monorepo; latest relevant CI runs are green; no duplicate Render services were created.
- The connected GitHub repository list currently exposes the GPT monorepo and the two historical project repositories; no active `personal-mcp-server` repository was present in that current list, so older documentation referring to it is treated as stale.

## Current Priority

1. Keep Render repository/root-directory mapping synchronized with the canonical monorepo.
2. Keep post-deployment health/smoke verification synchronized with live services.
3. Synchronize project Context documents with the final live deployment state.
4. Freeze the old project repositories as historical sources; archive/delete only through an explicit destructive-action step.
5. Continue future development only under `projects/<project>/`.

## Next Development Candidates

- Expand monorepo-wide validation only when a new shared boundary or deployment invariant is introduced.
- Add higher-value service smoke/browser checks where justified.
- Continue Janggi coaching/search work only from documented fixtures and regression evidence.
- Continue Time Dashboard parser/reliability improvements without crossing the UI/backend boundary.
