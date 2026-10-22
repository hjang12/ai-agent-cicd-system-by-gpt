# Current Status

## Source of Truth

- Workspace: `hjang12/ai-agent-cicd-system-by-gpt`
- Project path: `projects/personal-ai-janggi-trainer-by-gpt/`
- Branch: `main`
- Common Governance version: read `GOVERNANCE/VERSION`; do not maintain a duplicate value here.
- This file is a concise current-state index. Detailed requirements, architecture, historical decisions, benchmarks and calibration artifacts belong in the linked documents below.

## Product Status

Personal AI Janggi Trainer v1.0 is **complete**. No v1.0 release action remains open. The user-facing goal is an individual learner practising through games, move analysis, review, training problems and personal progress tracking.

### Main Capabilities

- Janggi domain rules, legality, terminal state, match lifecycle, undo and game-record handling.
- Baseline search engine with alpha-beta, transposition/evaluation/check/legal-move caching, normalized engine analysis and deterministic benchmark fixtures.
- Move analysis, bounded tactical warnings, learner-oriented coaching, session review and adaptive practice problems.
- Player skill-assessment/evaluation foundations, self-play data generation and an experimental linear value model; learned models remain evidence-only and are not promoted to production.
- Browser trainer and HTTP API with isolated in-memory sessions; browser-local progress is not a cloud account or cross-device history.

Detailed design: `ARCHITECTURE.md`, `AI_MODEL_ARCHITECTURE.md`, `SEARCH.md`, `COACHING.md`, `EVALUATION.md`, `PLAYER_ASSESSMENT.md`, `TRAINING_PROBLEMS.md` and `API.md`.

## UI / Requirement Contracts

- Setup-first, board-focused, single-screen mobile-game presentation; choose side and AI level before starting.
- The human move must be visibly rendered before AI calculation begins (`UX-001`).
- Selected piece / legal destinations are visible and AI thinking remains explicit until response completion or recovery (`UX-002`).
- `UX-005` is the active setup/replay-modal contract; `UX-004` is superseded.
- The requirement registry is `docs/requirement_contracts.json`; human-readable contract context is `docs/REQUIREMENT_CONTRACTS.md`.
- Current UI behavior is frozen for the v1.0 scope except bug fixes or explicit new requirements. Detailed product acceptance is in `V1_RELEASE_SCOPE.md`.

## Release Verification

- Application release commit: `1034665caedbe997d859053eebab40def78e7fe2`; deployment `dep-dbc2003ncjis73ejm660` reached `live`.
- Final release evidence synchronization: `96001f6e533b05b48b15ae286ee43a01d9d9caca`.
- At v1.0 release closure (2026-10-21), main-push live-browser smoke run [39533158968](https://github.com/hjang12/ai-agent-cicd-system-by-gpt/actions/runs/39533158968) passed readiness and all 11 Playwright/Chromium tests in 128.597 seconds.
- Post-Governance-1.4.6 deployment smoke (2026-10-22), run [39701830336](https://github.com/hjang12/ai-agent-cicd-system-by-gpt/actions/runs/39701830336) initially failed the undo/replay assertion, then passed all 11 tests on retry attempt 2 in 127.605 seconds; the failure did not reproduce and no application-source change was made.
- At release closure, Workspace validation run `39533158998` and Janggi Python validation run `39533159009` passed.
- Subsequent changes to this file are documentation-only; verify the current CI and deployment directly when a new change is made.

## CI / Benchmarks

- Required project CI: `.github/workflows/janggi-validation.yml`; Python compile, browser JavaScript syntax, Requirement Contract validation and unit tests.
- Search benchmark: `.github/workflows/janggi-search-benchmark.yml`; deterministic node/legal-move work, with historical results in `SEARCH_BENCHMARK_HISTORY.md`.
- Workspace structural validation: `.github/workflows/workspace-validation.yml`.
- Browser acceptance: `.github/workflows/janggi-browser-acceptance.yml`; PR and main-push events run local Chromium tests as a pre-deploy CI gate; `workflow_dispatch` runs the production live smoke after deployment, avoiding a circular wait with Render's CI-gated deployment.
- Do not infer that CI blocks production deployment: root Render services currently use commit-triggered auto-deploy, and the Workspace's strict CI-success-before-deploy gate remains tracked separately as `ISSUE-001`.

## Render Deployment

- Service: `personal-ai-janggi-trainer-by-gpt`
- Canonical repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Root Directory: `projects/personal-ai-janggi-trainer-by-gpt`
- Branch: `main`; build: `python -m compileall janggi tests`; start: `python app.py`
- URL: https://personal-ai-janggi-trainer.onrender.com
- The project-path build filter includes documentation, so documentation-only merges can trigger Render deployment. Confirm the deployment result after merges that change this project path; do not treat a historical LIVE state as current.

## Explicitly Deferred

- Persistent accounts, cloud synchronization, database-backed history and cross-device skill profiles.
- Production promotion/hosting of a trained policy or value model.
- Full mobile accessibility audit, social features, monetization and expanded multi-ply tactical detection.
- Production observability, rate limiting and further deployment hardening.

## AI-Level Calibration — PAUSED

- Development Task `TASK-20260930-0002` is **PAUSED** post-v1.0 research, not an unfinished v1.0 release gate.
- The compatible protocol-v3 pair 2-3 cohort for seeds `20261007–20261015` has 18 completed games / 0 unfinished; descriptive score is Lv.2 `1.5` : Lv.3 `16.5`. It remains `INSUFFICIENT` against the 20-game threshold.
- Seed `20261016` was proposed as the next run in the 2026-10-16 evidence snapshot but was not executed before the task was paused on 2026-10-20. Do not run further seeds or change public AI-level/search budgets unless the task is explicitly resumed.
- Evidence source: `AI_LEVEL_CALIBRATION_EVIDENCE.md`; runner instructions: `CALIBRATION_OPERATIONS.md`. Treat dated batch plans as historical, not executable commands.

## Current Work State

No active Janggi Development Task is registered. Start future project work only from a matching ACTIVE Task or a new explicit request. Completed v1.0 checkpoints and historical Next Action text are evidence only; AI-level calibration remains PAUSED.
