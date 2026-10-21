# Personal AI Janggi Trainer — v1.0 Release Scope

**Decision date:** 2026-10-20  
**Status:** v1.0 release acceptance gates passed on 2026-10-21. All verified release gates are complete; non-blocking platform housekeeping remains outside the release scope.

## 1. Product definition

v1.0 is a stable, single-user Janggi training web app. It must let one person play Janggi against the existing search-based AI, understand mistakes through move analysis and review, practise selected positions, and see personal progress over time.

The v1.0 completion loop is:

`대국 준비 → 대국 및 AI 응수 → 착수 분석 → 복기 → 훈련 문제 → 결과·훈련 성과 누적 확인`

This is a product-completion target, not a claim that the AI has mastered Janggi or that all six difficulty levels have statistically calibrated playing strength.

## 2. Final module decision

Percentages below are engineering estimates of current implementation maturity, not automated metrics. They estimate how close the module is to the defined v1.0 scope, including remaining verification or integration work.

| Module | Current maturity estimate | v1.0 decision | Requirement to ship |
|---|---:|---|---|
| Board-first browser UI and setup | 90% | **USE** | Start screen, side/level/setup selection, readable board, replay setup, responsive core layout |
| Rules, legal moves and match lifecycle | 95% | **USE** | Legal move enforcement, correct turn ownership, termination/check/bikjang handling, undo and reset |
| Browser/API session boundary | 90% | **USE** | Isolate browser sessions; handle failed responses without leaving stale or invalid board state |
| Search-based gameplay AI | 80% | **USE** | Return a legal move when one is available, respect bounded search, expose thinking/error states, preserve engine/domain boundary |
| Six selectable AI profiles | 90% | **USE, WITH LIMITATION** | All six distinct search configurations remain selectable. Do not claim that the six profiles are a fully calibrated strength ladder |
| Move analysis and coaching | 70% | **USE** | Analyze a played legal move without mutating the match; keep recommendations validated and explanations appropriately conservative |
| Game review | 60% | **USE** | Replay the current completed record and summarize reviewed moves/reasons |
| Position training and answer checking | 60% | **USE** | Generate valid problems from reviewed positions, check answers, and show explanations |
| Training metrics and adaptive selection | 65% | **USE** | Preserve attempt/correctness metrics and session-level problem prioritization; add v1.0 cumulative progress storage below |
| Personal assessment and growth tracking | 20% | **USE — MINIMAL VERSION REQUIRED** | Store completed-game results by AI level and training attempt/correctness totals in browser-local storage; show cumulative results and simple progress |
| Player Elo / numerical skill rating | 20% | **DO NOT USE IN v1.0** | Do not show a numeric rating until the opponent rating and relevant AI-level evidence are calibrated |
| Self-play and training-dataset generation | 75% | **DO NOT USE IN THE PRODUCT FLOW** | Retain the research code and existing artifacts; no additional dataset generation is required to ship v1.0 |
| Learned policy/value model and production model promotion | 40% | **DO NOT USE IN v1.0** | Existing baseline search remains the production AI; no learned-model integration is a release dependency |
| AI-vs-AI evaluation, tournament and Elo research tools | 65–70% | **DO NOT USE IN THE USER EXPERIENCE** | Keep as development/research utilities; no further research-grade calibration is required for release |
| Dedicated calibration Runner and long calibration batches | 80% | **DO NOT USE FOR RELEASE** | Leave idle; do not launch another calibration batch as a prerequisite for v1.0 |
| Authentication, server database, cloud sync and multi-user features | 0–10% | **OUT OF SCOPE** | v1.0 remains anonymous, single-user and browser-local for growth data |
| Automated regression tests and CI | 85–90% | **USE / RELEASE GATE** | Compile, requirement-contract validation and full Janggi tests pass on the release candidate |
| Render deployment and runtime checks | 85% | **USE / RELEASE GATE** | Verify the live service is reachable, the health endpoint works, and the production smoke passes |

## 3. Minimum growth tracking included in v1.0

This is the one material completion item added by this scope review. The product's purpose includes helping the player observe improvement, so a result that disappears when a new game begins is not enough for v1.0.

The smallest acceptable implementation is:

- Persist the player's completed-game summary in that browser using versioned browser-local storage.
- Keep, at minimum, date, selected AI level, side, outcome, setup, and move count for each recorded completed game.
- Accumulate wins, draws and losses separately for each selected AI level. Keep all-time overall outcome totals separately from the bounded list of the latest 100 game details; label the per-level breakdown as recent-history data.
- Preserve all-time training attempt/correct totals separately from up to 365 days of daily summaries.
- Accumulate training attempts, correct answers and accuracy; retain enough dated summaries to show whether practice outcomes are changing over time.
- Provide a compact progress/history view that does not crowd the active board. Access it from setup or post-game flow, not as a permanent overlay during play.
- Make result recording idempotent so one completed game is not counted twice after rerender, reset, or repeated requests.
- Display these as **personal practice statistics**, not as an authoritative chess/Janggi skill rating. If the storage is empty, unavailable or invalid, show an honest empty/unavailable state rather than fabricated numbers.
- Explain in the UI or documentation that progress is saved only in this browser. Clearing browser site data may remove it. No account, server-side database, cloud backup or cross-device sync is required for v1.0.

Do not build a new backend persistence stack solely for this version.

## 4. AI-strength policy

- Preserve the six existing public search profiles.
- Preserve the compatible pair 2–3 evidence already collected, including its provenance and limitations.
- The current evidence does **not** prove a monotonic six-level strength ladder. Do not label it fully calibrated.
- Do not change public search budgets on the strength of a small or provenance-incompatible sample.
- Full statistical calibration of all five adjacent level pairs, learned-model training, and model promotion are post-v1.0 research tasks, not release blockers.
- Remove or revise any user-facing wording that implies a validated numeric player rating when the implementation can only report that the result is unrated.

## 5. Release acceptance checklist

v1.0 is complete only when all applicable gates below pass.

### Gameplay

- [x] Start a game in each player-side orientation and verify the correct side moves first.
- [x] Verify all four supported initial setups and all six AI level options can start a game.
- [x] Verify selection/legal-destination feedback and that the player's move is visibly rendered before the AI starts thinking.
- [x] Verify the AI-thinking indicator ends on success and the UI recovers on an API/search error.
- [x] Verify turn enforcement, illegal/out-of-turn move rejection, check/bikjang/terminal presentation, undo and replay/reset. Production browser smoke run `39531901117` passed all 11 methods, including `test_server_rejects_illegal_and_out_of_turn_moves_without_mutation`, `test_check_message_is_visible_after_ai_reply`, `test_bikjang_terminal_message_is_visible`, and `test_undo_reverts_a_full_turn_and_replay_applies_new_settings`.
- [x] Verify results are recorded only once after a completed game.

### User-visible learning surfaces

- [x] Move analysis/coaching details, review summaries and training problems/answer feedback are shown in a real visible panel or modal with readable headings and labels.
- [x] Post-game review/training buttons reveal the corresponding content and let the user return to the game/setup flow.
- [x] These panels are not left only inside the hidden runtime-compatibility container; the visible controls operate on the same authoritative result data.
- [x] Opening/closing the learning view preserves the game result and does not start/reset a game.

### Learning and progress

- [x] Verify analysis does not mutate the active match and invalid engine recommendations are never applied.
- [x] Verify review, generated training problems, answer checking and explanations on a representative game.
- [x] Verify training attempt/correctness metrics are accurate.
- [x] Verify completed-game and training summaries survive a page reload and a new match in the same browser.
- [x] Verify outcomes are separated by selected AI level and that no unsupported numeric rating is displayed.
- [x] Verify malformed/missing local progress data fails safely and does not prevent playing.

### Quality and deployment

- [x] `python -m compileall janggi tests tools` passes.
- [x] `python tools/validate_requirement_contracts.py` passes.
- [x] `python -m unittest discover -s tests -v` passes.
- [x] Run the required Workspace validation and Janggi validation CI on the release candidate (latest code head 9ebacdc1c4fb9733aa5550d5cdae401fbbfd3763: Workspace run 39519087955 and Janggi run 39519087947 both passed).
- [x] Verify the deployed Render service reaches `live`, and the live smoke preflight confirms the public root, `/api/health`, and expected UI marker for main commit `1034665caedbe997d859053eebab40def78e7fe2` (deployment `dep-dbc2003ncjis73ejm660`).
- [x] Verify live health behavior and post-deploy readiness. The latest release deployment reached `live`; `/api/health` passed the live smoke readiness preflight and all 11 production browser tests passed.
- [x] Perform post-deploy smoke against the released main commit. Run `39531901117` passed readiness and all 11 Playwright/Chromium methods in 137.872 seconds (`OK`); prior failures in turn return and post-game review did not recur.
- [x] Update release notes/current status/checkpoint so implemented, verified and deferred features are clearly separated.

### Evidence note — PR #149 candidate (2026-10-21)

- GitHub Actions ran the 10-method Playwright/Chromium acceptance suite against a locally started copy of the candidate (Janggi browser acceptance, run 39519088050); it succeeded on code head 9ebacdc1c4fb9733aa5550d5cdae401fbbfd3763. That run also checked that the player profile shows a game count rather than a numeric rating and that the result explicitly states numerical Rating is not provided.
- Subsequent branch-head CI at `d8725225a4e34a0e222d93de1ca2e5e98dd149c3` passed Workspace validation run `39519490460`, Janggi Python validation run `39519490378`, and browser acceptance run `39519490467`. The browser job passed and `live-browser-smoke` was skipped by design on the pull-request event. This is candidate-local evidence, not production Render smoke; any later candidate commit must pass its own branch-head checks before merge.
- These browser tests cover setup combinations, both player-side opening paths, human-move/AI-thinking sequence, analysis/review/training visibility, answer checking, per-level progress display, idempotent result recording, reload persistence, and malformed/unavailable browser storage. They are candidate-local CI evidence, not a production Render browser smoke.
- This candidate-local evidence was superseded by the main-push production smoke results below; the final live suite verifies the wider gameplay/legal-move regression.
- The PR-triggered workflow's live-browser-smoke job is skipped by design; it runs after a project-changing commit reaches main.


### Production browser smoke — 2026-10-21

- PR #149 merged as main commit `bc01e2eccf0c4a86529b8d7ccc80b0d6c6686500`; deployment `dep-dbc19cdg1s2s738ai9k0` reached `live`. Smoke run `39527295378` initially exposed two turn-return timeouts.
- PR #150 merged as main commit `1c2156d48612c09578c2327af67fc74e7ff29016`; deployment `dep-dbc1qb6q1p3s73bgsig0` reached `live`. Smoke run `39530751332` removed the turn-return timeouts but exposed a slow post-game review flow.
- PR #151 merged as app-fix commit `1034665caedbe997d859053eebab40def78e7fe2`; deployment `dep-dbc2003ncjis73ejm660` reached `live`. Smoke run `39531901117` passed all 11 browser methods in 137.872 seconds.
- Final documentation synchronization merged as `96001f6e533b05b48b15ae286ee43a01d9d9caca`; its latest Render deployment `dep-dbc26arm8hqs73bcbmbg` reached `live`. Main-push workflow run `39533158968` passed readiness and all 11 Playwright/Chromium tests in 128.597 seconds (`OK`). This repeat deployment test covers setup/level combinations, both sides, move/AI response, API error recovery, check/bikjang, illegal/out-of-turn rejection, review/training, local progress, and undo/replay.
- The two initial turn-return timeouts and the review-modal timeout do not recur. The gameplay, learning, persistence, legal-move and post-deploy smoke gates are passed.
- The live smoke verified public endpoint readiness and the complete browser suite. Optional platform housekeeping is tracked separately from release acceptance and is not a v1.0 blocker.
## 6. Explicit non-goals

The following are not part of v1.0 and must not keep the release open:

- Statistical strength certification for every adjacent AI level pair.
- Any claim that AI levels are monotonically stronger solely because their search parameters differ.
- Learned policy/value model training or integration into production search.
- Automatic self-play → train → evaluate → promote production-model loop.
- Numeric user Elo/rating while opponents are not calibrated.
- Accounts, authentication, shared/cloud game history, database persistence or cross-device synchronization.
- Multiplayer, social features, monetization, a full accessibility audit, or open-ended UI redesign.
- General-purpose performance research that does not fix an observed v1.0 blocker.

Research code and existing calibration artifacts may remain in the repository. A module marked **DO NOT USE** is excluded from the v1.0 product flow; it does not imply a required source-code deletion.

## 7. Estimate note

The **10–16 hour** figure was a planning estimate made when the v1.0 scope was defined on 2026-10-20, before visible learning surfaces and browser-local progress were implemented. It is not a current remaining-time estimate. All v1.0 acceptance gates now pass. The optional Render HTTP health-check configuration difference is a deferred P3 follow-up, not current open release work.

## 8. Final decision rule

Prefer the smallest change that closes a verified acceptance gap. Do not add new features or resume AI research during v1.0 stabilization unless the release checks expose a concrete blocker. All v1.0 release gates passed against the live deployment on 2026-10-21; v1.0 is complete. Optional platform housekeeping remains outside the release scope; future AI research must be a separately scoped task.
