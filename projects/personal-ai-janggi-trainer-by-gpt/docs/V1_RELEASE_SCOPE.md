# Personal AI Janggi Trainer — v1.0 Release Scope

**Decision date:** 2026-10-20  
**Status:** Final scope for v1.0; implementation and release verification remain in progress.

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
| Move analysis and coaching | 85% | **USE** | Analyze a played legal move without mutating the match; keep recommendations validated and explanations appropriately conservative |
| Game review | 85% | **USE** | Replay the current completed record and summarize reviewed moves/reasons |
| Position training and answer checking | 80% | **USE** | Generate valid problems from reviewed positions, check answers, and show explanations |
| Training metrics and adaptive selection | 75% | **USE** | Preserve attempt/correctness metrics and session-level problem prioritization; add v1.0 cumulative progress storage below |
| Personal assessment and growth tracking | 35% | **USE — MINIMAL VERSION REQUIRED** | Store completed-game results by AI level and training attempt/correctness totals in browser-local storage; show cumulative results and simple progress |
| Player Elo / numerical skill rating | 20% | **DO NOT USE IN v1.0** | Do not show a numeric rating until the opponent rating and relevant AI-level evidence are calibrated |
| Self-play and training-dataset generation | 75% | **DO NOT USE IN THE PRODUCT FLOW** | Retain the research code and existing artifacts; no additional dataset generation is required to ship v1.0 |
| Learned policy/value model and production model promotion | 40% | **DO NOT USE IN v1.0** | Existing baseline search remains the production AI; no learned-model integration is a release dependency |
| AI-vs-AI evaluation, tournament and Elo research tools | 65–70% | **DO NOT USE IN THE USER EXPERIENCE** | Keep as development/research utilities; no further research-grade calibration is required for release |
| Dedicated calibration Runner and long calibration batches | 80% | **DO NOT USE FOR RELEASE** | Leave idle; do not launch another calibration batch as a prerequisite for v1.0 |
| Authentication, server database, cloud sync and multi-user features | 0–10% | **OUT OF SCOPE** | v1.0 remains anonymous, single-user and browser-local for growth data |
| Automated regression tests and CI | 85–90% | **USE / RELEASE GATE** | Compile, requirement-contract validation and full Janggi tests pass on the release candidate |
| Render deployment and runtime checks | 85% | **USE / RELEASE GATE** | Live service is reachable; health-check configuration drift is resolved or explicitly shown not to affect live health; run the release smoke scenario |

## 3. Minimum growth tracking included in v1.0

This is the one material completion item added by this scope review. The product's purpose includes helping the player observe improvement, so a result that disappears when a new game begins is not enough for v1.0.

The smallest acceptable implementation is:

- Persist the player's completed-game summary in that browser using versioned browser-local storage.
- Keep, at minimum, date, selected AI level, side, outcome, setup, and move count for each recorded completed game.
- Accumulate wins, draws and losses separately for each selected AI level.
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

- [ ] Start a game in each player-side orientation and verify the correct side moves first.
- [ ] Verify all four supported initial setups and all six AI level options can start a game.
- [ ] Verify selection/legal-destination feedback and that the player's move is visibly rendered before the AI starts thinking.
- [ ] Verify the AI-thinking indicator ends on success and the UI recovers on an API/search error.
- [ ] Verify turn enforcement, legal move validation, check/bikjang/terminal presentation, undo and replay/reset.
- [ ] Verify results are recorded only once after a completed game.

### Learning and progress

- [ ] Verify analysis does not mutate the active match and invalid engine recommendations are never applied.
- [ ] Verify review, generated training problems, answer checking and explanations on a representative game.
- [ ] Verify training attempt/correctness metrics are accurate.
- [ ] Verify completed-game and training summaries survive a page reload and a new match in the same browser.
- [ ] Verify outcomes are separated by selected AI level and that no unsupported numeric rating is displayed.
- [ ] Verify malformed/missing local progress data fails safely and does not prevent playing.

### Quality and deployment

- [ ] `python -m compileall janggi tests tools` passes.
- [ ] `python tools/validate_requirement_contracts.py` passes.
- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] Run the required Workspace validation and Janggi validation CI on the release candidate.
- [ ] Verify the Render service is live and the `/api/health` check/configuration is consistent.
- [ ] Perform the available post-deploy smoke test against the live app; distinguish any test the Agent cannot execute from a test that passed.
- [ ] Update release notes/current status/checkpoint so implemented, verified and deferred features are clearly separated.

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

## 7. Estimated remaining effort

A reasonable planning estimate after this scope decision is **approximately 7–12 hours of engineering work**, assuming no major gameplay defect is found. This includes implementing minimal browser-local growth tracking, final integration/regression work, deployment checks and documentation. It is an estimate of active work, not a promise about elapsed time.

## 8. Final decision rule

Prefer the smallest change that closes a verified acceptance gap. Do not add new features or resume AI research during v1.0 stabilization unless the release checks expose a concrete blocker. After every release gate passes and the live deployment is confirmed, mark v1.0 complete; future AI research should be a separately scoped task.
