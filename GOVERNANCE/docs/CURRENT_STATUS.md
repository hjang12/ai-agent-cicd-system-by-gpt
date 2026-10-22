# Current Status

## Canonical Workspace

- Repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Default branch: `main`
- Common Governance rule: `GOVERNANCE/GOVERNANCE.md`
- Canonical Governance version file: `GOVERNANCE/VERSION`
- Governance 1.4.6 is active on `main`, adopted by PR #160 squash merge `a65ef98be8d83b2992e40c226159c2ef683cbb8c` on 2026-10-22.
- `main` branch protection is not enabled. A strict CI-success-before-deploy gate is not enforced; authoritative status and blocker are in `GOVERNANCE/docs/ACTIVE_ISSUES.md` (`ISSUE-001`).

## Canonical Navigation

- `AGENT_START.md` / `AGENTS.md` — Workspace startup and operating instructions
- `GOVERNANCE/GOVERNANCE.md` — shared rules
- `GOVERNANCE/docs/DEVELOPMENT_TASKS.md` — Task selection and Status
- `GOVERNANCE/docs/ACTIVE_ISSUES.md` — current unresolved Workspace issues
- `GOVERNANCE/docs/checkpoints/` and each Task's listed Checkpoint — recoverable task state
- `projects/<project>/AGENT_START.md`, `AGENTS.md`, and `docs/CURRENT_STATUS.md` — project-specific navigation and current facts
- `GOVERNANCE/docs/DEVELOPMENT_HISTORY.md`, ADRs and project Evidence — historical decisions and detailed results
- `GOVERNANCE/CHANGELOG.md` — Governance version history

These files have distinct responsibilities. Do not copy the same current status or executable Next Action into multiple current-facing documents.

## Current Task State

- Governance consistency/simplicity review: `TASK-20261021-0004` — **COMPLETED** through PR #160, merged as `a65ef98be8d83b2992e40c226159c2ef683cbb8c` on 2026-10-22.
- Post-1.4.6 audit / `ISSUE-001` / Janggi live-smoke reconciliation: `TASK-20261022-0001` — **ACTIVE**; Checkpoint: `GOVERNANCE/docs/checkpoints/TASK-20261022-0001.md`.
- Previous Governance review: `TASK-20261021-0003` — **COMPLETED** through PR #159.
- Personal AI Janggi Trainer v1.0: `TASK-20261020-0001` — **COMPLETED**; final production browser smoke passed 11/11 tests. Project release evidence is in `projects/personal-ai-janggi-trainer-by-gpt/docs/V1_RELEASE_SCOPE.md` and its final Checkpoint.
- Janggi AI-level calibration: `TASK-20260930-0002` — **PAUSED** post-v1.0 research. Do not run more seeds or change public AI-level/search-budget settings unless explicitly resumed.
- No separate active Janggi feature task is registered.

The Task Registry Status is authoritative for whether a Next Action may run. Completed Task summaries and historical Checkpoint actions are not current instructions.

## Projects and Verification

### Personal AI Janggi Trainer
- Canonical path: `projects/personal-ai-janggi-trainer-by-gpt/`
- Required Python / contract validation: `.github/workflows/janggi-validation.yml`
- Browser acceptance: `.github/workflows/janggi-browser-acceptance.yml`
- Search benchmark: `.github/workflows/janggi-search-benchmark.yml`
- Concise current product state: `projects/personal-ai-janggi-trainer-by-gpt/docs/CURRENT_STATUS.md`

### Time Dashboard
- Canonical path: `projects/time-dashboard-by-gpt/`
- CI: `.github/workflows/time-dashboard-ci.yml`
- Project-specific status: `projects/time-dashboard-by-gpt/docs/CURRENT_STATUS.md`

### Workspace and deployment
- Workspace structural validation: `.github/workflows/workspace-validation.yml`
- Render service topology and desired configuration: root `render.yaml` and project status documents.
- Commits touching project paths can trigger documentation-only Render deployments. Verify the current deployment directly after relevant merges; dated LIVE snapshots in history are not current-state evidence.
- The configured Render auto-deploy path is not proof that deployment waits for CI success. Track the strict-gate limitation under `ISSUE-001`; do not claim enforced CI-before-deploy.

## Latest verification snapshot — 2026-10-22

- `main` at audit start: `a65ef98be8d83b2992e40c226159c2ef683cbb8c`.
- Main-push checks: Workspace validation [39701830359](https://github.com/hjang12/ai-agent-cicd-system-by-gpt/actions/runs/39701830359) PASS; Time Dashboard CI [39701830301](https://github.com/hjang12/ai-agent-cicd-system-by-gpt/actions/runs/39701830301) PASS; Janggi Python validation [39701830357](https://github.com/hjang12/ai-agent-cicd-system-by-gpt/actions/runs/39701830357) PASS.
- Janggi live-browser smoke [39701830336](https://github.com/hjang12/ai-agent-cicd-system-by-gpt/actions/runs/39701830336) failed its undo/replay assertion on the live app. The retry is tracked in `TASK-20261022-0001`; do not describe the latest production smoke as clean until resolved.
- Actual Render metadata still reports commit-triggered auto-deploy for both Janggi and Time Dashboard. `ISSUE-001` remains BLOCKED until the actual service setting is changed and enforcement is verified; `render.yaml` is declarative configuration, not evidence that an existing service has adopted it.

## Migration Status

Monorepo consolidation and deletion of the two former project repositories completed on 2026-09-18 after the pre-deletion verification gate. Original source commit SHAs are provenance only; they do not imply the former repositories or their full Git histories remain accessible. The canonical development location is this monorepo. Details belong in `GOVERNANCE/MIGRATION.md` and ADR-0002.

## Context Recovery

Use the single procedure in §25-A-7 of `GOVERNANCE/GOVERNANCE.md`: identify the Request-matching Task and Status first, then read its designated Context / Checkpoint and verify actual GitHub / CI / Deployment state. Open the detailed project/architecture/history documents only when the Task needs them.

