# Current Status

## Governance

- Governance Version: `1.3.2`
- Status: Active baseline on `main`
- Current canonical workspace repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Default / working branch: `main`
- Main branch protection: not enabled
- CI/CD strict deploy gate: not enforced; Render remains commit-triggered auto deploy

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

- `AGENT_START.md` — workspace-level agent startup entrypoint
- `AGENTS.md` — workspace-level agent rules
- `GOVERNANCE/GOVERNANCE.md` — common operating rules
- `GOVERNANCE/docs/CURRENT_STATUS.md` — this workspace status
- `GOVERNANCE/docs/ACTIVE_ISSUES.md` — AI-managed current unresolved issue index
- `GOVERNANCE/docs/DEVELOPMENT_TASKS.md` — Workspace Development Task Registry
- `GOVERNANCE/docs/DEVELOPMENT_HISTORY.md` — long-term governance/workspace history
- `GOVERNANCE/docs/ADR/` — architecture and operating decisions
- `projects/<project>/AGENT_START.md` — project Chat startup entrypoint
- `projects/<project>/AGENTS.md` — project-specific agent rules
- `projects/<project>/docs/CURRENT_STATUS.md` — project context
- `.github/workflows/` — monorepo CI and benchmark workflows
- `render.yaml` — monorepo Render Blueprint


## Development Work Continuity

This workspace uses ChatGPT + AI Agent as the primary interactive development interface.

- Chat is a temporary working interface; GitHub and project Context documents remain the Source of Truth.
- Current development continuity is managed through Development Task, Development Task Registry, Development Context, Checkpoint, and Context Recovery.
- Chat transitions are allowed whenever platform/context constraints or work structure make a new Chat safer or more efficient.
- No fixed time-based forced Chat cutoff is used. Checkpoints are state-based.
- Interaction has no fixed maximum duration; an Interaction normally ends when a Response is returned, and a safe interruption may end it earlier after preserving recoverable state.
- Agent Work may be divided into Agent Work Segments when Context / Token / Tool / Runtime / external-work boundaries make continued execution unsafe or inefficient.
- Long-running Agent Work is supported as part of long-running Development Tasks, but does not imply unbounded or uninterrupted execution.
- User pause/stop requests are honored at the earliest safe interruption point, with Checkpoint / Context preservation when needed.
- Current platform/plan/model limits are treated as Platform Constraints rather than hard-coded Governance invariants.

Canonical continuity records:
- GOVERNANCE/docs/DEVELOPMENT_TASKS.md
- projects/<project>/docs/CURRENT_STATUS.md
- GOVERNANCE/docs/ACTIVE_ISSUES.md
- DEVELOPMENT_HISTORY.md
- ADR / Requirement Contract / evidence records
- GitHub Commit / PR / CI state

## Development Execution Paths

The workspace separates short validation from long-running computation.

- Fast CI is the default path for bounded, repeatable Build / Test / Regression / structural validation.
- Long-running work such as Janggi AI level calibration, large benchmarks, self-play, and training/data generation uses a separate execution path when CI runtime/quota is not appropriate.
- Long-running execution results are recorded as Evidence / Checkpoint / Context with execution conditions and version metadata.
- A prepared runner or workflow is not treated as executed computation until actual results are produced.
- Continuation across Chat changes is Repository-based; a long manual Continuation Prompt is not required for normal recovery.

## Active Issues

Current Active Issue Index: `GOVERNANCE/docs/ACTIVE_ISSUES.md`

Current active items are maintained in `GOVERNANCE/docs/ACTIVE_ISSUES.md`:

- `ISSUE-001` — CI-success-before-deploy strict gate is not enforced; the current verification date is maintained in the Active Issue Index.
- `ISSUE-002` — Render live `healthCheckPath` is empty while repository Blueprint declares an explicit health endpoint; the current verification date is maintained in the Active Issue Index.

This section is only a navigation summary. The authoritative current status, priority, next action, blocker, and verification date are maintained in `ACTIVE_ISSUES.md`.

## Project Status

### Personal AI Janggi Trainer

- Canonical path: `projects/personal-ai-janggi-trainer-by-gpt/`
- Source snapshot: `hjang12/personal-ai-janggi-trainer-by-gpt` @ `83932421217f149de46e6e23b89aff9d92467a11`
- Latest central fixes are included after migration.
- Domain, engine, search, coaching, training/evaluation, and browser/API layers are present as documented in the project Context.
- Current CI: `.github/workflows/janggi-validation.yml`
- Search benchmark: `.github/workflows/janggi-search-benchmark.yml`
- Workspace validation: `.github/workflows/workspace-validation.yml`
- Latest Janggi validation: success on `44c67cc` (run #27).
- Render cutover is complete: the existing service now points to the canonical monorepo and the project Root Directory.

### Time Dashboard

- Canonical path: `projects/time-dashboard-by-gpt/`
- Source snapshot: `hjang12/time-dashboard-by-gpt` @ `fb8e98baa7a81a610c2ccbf767f2995fb9af0a3f`
- Primary server: `timefolio_server.py`
- Backend regression test suite is preserved under `tests/`.
- Current CI: `.github/workflows/time-dashboard-ci.yml`
- Latest Time Dashboard CI: success on `44c67cc` (run #27).
- Render cutover is complete: the existing service now points to the canonical monorepo and the project Root Directory.

## Migration Record

The monorepo consolidation was committed to `main` on 2026-09-18.

Key commits:

- `1d91810ba4389205801e751ef0856eb82e4dd583` — consolidate Governance and GPT projects
- `92cf6a38532886a6cb92afacc3d3e817c65b3571` — fix monorepo agent metadata and PWA icon type
- `dbd6b52432a628a4b92e4fd586be0fae26672325` — fix validation/benchmark semantics

The former project repositories were deleted after the pre-deletion verification gate on 2026-09-18. Their commit references remain in the governance history as historical source metadata. The canonical development location is the monorepo.

## CI/CD State

Current root workflows:

- Janggi validation — success on current `main`
- Janggi search benchmark — success on current `main` (run #20)
- Time Dashboard CI — success on current `main` (run #27)
- Workspace structure validation — success on current `main` (run #6)

The first monorepo Janggi validation/benchmark runs failed because the migrated test/benchmark files still reflected pre-monorepo assumptions. The subsequent fixes are now green. The actual current GitHub Actions result, not the historical failure, is the operative state.

## Render State — Verified 2026-09-18

Render workspace: `My Workspace` (`tea-da7sjdgu01pc73bsno6g`).

Render service cutover is complete. Both existing services now use the canonical monorepo with project-specific Root Directories:

| Service | Repository | Root Directory | Branch | Auto Deploy | Latest Live Deploy |
| --- | --- | --- | --- | --- | --- |
| `personal-ai-janggi-trainer-by-gpt` | `hjang12/ai-agent-cicd-system-by-gpt` | `projects/personal-ai-janggi-trainer-by-gpt` | `main` | yes | `f07095ca8f86d7376e925b22e8801f8dfc7522f4` |
| `time-dashboard-by-gpt` | `hjang12/ai-agent-cicd-system-by-gpt` | `projects/time-dashboard-by-gpt` | `main` | yes | `7a7cd7636e50f69deccb4928db1dd20dd4344c77` |

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

## Known Limitations / Pending Work

- The former `personal-ai-janggi-trainer-by-gpt` and `time-dashboard-by-gpt` source repositories were deleted after the pre-deletion verification gate on 2026-09-18.
- Destructive cleanup is complete; future development must target the canonical monorepo only.
- Pre-deletion gate verification completed on 2026-09-18: both Render services pointed to the canonical monorepo, latest relevant CI runs were green, and no duplicate Render services existed.
- A strict CI-success-before-deploy gate is not currently enforced. Render remains commit-triggered auto deploy, so CI and deployment are independently triggered.
- Live Render `healthCheckPath` is still empty for both services even though the repository Blueprint declares `/api/health`; this is a platform-setting hardening item.
- The connected GitHub repository list currently exposes the GPT monorepo and the two historical project repositories; no active `personal-mcp-server` repository was present in that current list, so older documentation referring to it is treated as stale.

## Current Priority

1. Keep Render repository/root-directory mapping synchronized with the canonical monorepo.
2. Keep post-deployment health/smoke verification synchronized with live services.
3. Synchronize project Context documents with the final live deployment state.
4. Monitor and improve CI/CD gating and live health-check configuration as tracked Active Issues.
5. Continue future development only under `projects/<project>/`.

## Next Development Candidates

- Expand monorepo-wide validation only when a new shared boundary or deployment invariant is introduced.
- Add higher-value service smoke/browser checks where justified.
- Continue Janggi coaching/search work only from documented fixtures and regression evidence.
- Continue Time Dashboard parser/reliability improvements without crossing the UI/backend boundary.
