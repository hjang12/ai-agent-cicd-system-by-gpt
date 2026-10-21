# Current Status

## Governance

- Governance Version: `1.4.4`
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
- Interaction has no fixed maximum duration; an Interaction ends with its final response, not with an intermediate progress report. A safe interruption may end it earlier after preserving recoverable state.
- Intermediate reports show actual status while Agent Work continues; after a final response, do not imply that the Agent is still working in the background. Any independently running external process is reported separately.
- Before a final response, re-check the ACTIVE Task's official Checkpoint and live execution state. Continue an explicit, authorized, feasible Next Action within the same Interaction; if work must stop, record the actual reason and distinguish a necessary boundary from avoidable Agent-side early termination.
- Report meaningful milestones using the current phase, verified outcomes, next action, and material plan changes; do not use a fixed total milestone count by default.
- For long-running or efficiency-sensitive work, distinguish total elapsed time from measured process/computation time and observed waiting; mark unmeasured intervals as unknown rather than inventing a breakdown.
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
- Deferred follow-ups stay in `GOVERNANCE/docs/ACTIVE_ISSUES.md`; do not duplicate them into current priorities or routine recovery summaries unless their recorded revisit condition is met.
- Render service metadata observability limitation is documented below as a known limitation, not as an active application or deployment issue.

This section is only a navigation summary. The authoritative current status, priority, next action, blocker, and verification date are maintained in `ACTIVE_ISSUES.md`.

## Project Status

### Personal AI Janggi Trainer

- Canonical path: `projects/personal-ai-janggi-trainer-by-gpt/`
- Historical imported source commit: `hjang12/personal-ai-janggi-trainer-by-gpt` @ `83932421217f149de46e6e23b89aff9d92467a11`
- Latest central fixes are included after migration.
- Domain, engine, search, coaching, training/evaluation, and browser/API layers are present as documented in the project Context.
- Current CI: `.github/workflows/janggi-validation.yml`
- Search benchmark: `.github/workflows/janggi-search-benchmark.yml`
- Workspace validation: `.github/workflows/workspace-validation.yml`
- Fast Janggi validation is maintained by `.github/workflows/janggi-validation.yml`; exact run IDs and result snapshots belong in dated verification/history records.
- Render cutover is complete: the existing service now points to the canonical monorepo and the project Root Directory.

### Time Dashboard

- Canonical path: `projects/time-dashboard-by-gpt/`
- Historical imported source commit: `hjang12/time-dashboard-by-gpt` @ `fb8e98baa7a81a610c2ccbf767f2995fb9af0a3f`
- Primary server: `timefolio_server.py`
- Backend regression test suite is preserved under `tests/`.
- Current CI: `.github/workflows/time-dashboard-ci.yml`
- Time Dashboard CI remains configured separately; no current review change was made to that project.
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

- Janggi validation — governed by the mandatory fast CI workflow; exact execution snapshots are recorded with the relevant commit.
- Janggi search benchmark — maintained by the dedicated search benchmark workflow; exact execution snapshots are recorded with the relevant commit.
- Time Dashboard CI — maintained by the dedicated project workflow; exact execution snapshots are recorded with the relevant commit.
- Workspace structure validation — mandatory monorepo structural gate; exact execution snapshots are recorded with the relevant commit.

The first monorepo Janggi validation/benchmark runs failed because the migrated test/benchmark files still reflected pre-monorepo assumptions. The subsequent fixes are now green. The actual current GitHub Actions result, not the historical failure, is the operative state.

## Render Cutover Snapshot — Verified 2026-10-01 (Historical)

Render workspace: `My Workspace` (`tea-da7sjdgu01pc73bsno6g`).

Render service cutover is complete. Both existing services now use the canonical monorepo with project-specific Root Directories:

| Service | Repository | Root Directory | Branch | Auto Deploy | State |
| --- | --- | --- | --- | --- | --- |
| `personal-ai-janggi-trainer-by-gpt` | `hjang12/ai-agent-cicd-system-by-gpt` | `projects/personal-ai-janggi-trainer-by-gpt` | `main` | yes | active |
| `time-dashboard-by-gpt` | `hjang12/ai-agent-cicd-system-by-gpt` | `projects/time-dashboard-by-gpt` | `main` | yes | active |

At the time of this dated cutover check, both services were active and their then-latest cutover deployments were `live`. This is historical evidence, not a current live-state assertion; verify Render directly when a task depends on current availability.

Historical deployment verification:
- The Janggi Render service has been independently verified live; exact deployment IDs and runtime snapshots belong in dated verification/history records.
- Time Dashboard deploy `dep-damckue7bikc73b4p7ng`: `live`; build succeeded; `python timefolio_server.py` started; a `HEAD /` request returned HTTP 200; Render reported the service live at its primary URL.
- Time Dashboard had one immediate cutover build failure because `requirements.txt` was not found, followed by a successful retry after the service Root Directory was correctly applied.
- Historical Render settings observations are retained in `DEVELOPMENT_HISTORY.md`; they are not current release blockers and are not repeated in this status summary.

At the time of cutover, the connected Render toolset did not expose an update operation for existing service Git Repository / Root Directory settings; the cutover was performed in the Render Dashboard and verified through the connected Render API/tooling. No duplicate services were created.

Migration state is **complete**: monorepo consolidation, Render cutover, and legacy source-repository cleanup were completed after the pre-deletion verification gate on 2026-09-18. References to former project repositories above are historical provenance only.

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
- Optional platform configuration follow-ups remain tracked only in `GOVERNANCE/docs/ACTIVE_ISSUES.md` and are excluded from current priorities unless their revisit conditions occur.
- The connected GitHub repository list currently exposes the GPT monorepo and the two historical project repositories; no active `personal-mcp-server` repository was present in that current list, so older documentation referring to it is treated as stale.

## Current Task State

- Governance detailed review: `TASK-20261021-0003` — **COMPLETED**. PR #159 was approved by the user and merged as `43a4e6a175949790ab974fd63456a35da0c6d7ae`; Governance version is `1.4.5`.
- Personal AI Janggi Trainer v1.0: `TASK-20261020-0001` — **COMPLETED**. Release acceptance and the 11-method live browser smoke passed.
- AI-level strength calibration: `TASK-20260930-0002` — **PAUSED** post-v1.0 research. Do not run further calibration or change public AI levels/search budgets unless this task is explicitly resumed.
- CI-success-before-deploy strict gate: `ISSUE-001` — **BLOCKED**; the authoritative details and last verification date are in `GOVERNANCE/docs/ACTIVE_ISSUES.md`.

No Development Task is currently active. Completed Task IDs remain available for history, not as current priorities.

## Potential Future Work (Not Active Tasks)

The items below are candidates only, not an execution queue. Do not start them automatically; create/select an ACTIVE Development Task from a new explicit request.

- Expand monorepo-wide validation only when a new shared boundary or deployment invariant is introduced.
- Add higher-value service smoke/browser checks where justified.
- Continue Janggi coaching/search work only from documented fixtures and regression evidence.
- Continue Time Dashboard parser/reliability improvements without crossing the UI/backend boundary.
