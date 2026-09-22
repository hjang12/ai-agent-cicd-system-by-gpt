# Search Benchmark History

## 2026-09-22 — AI v1 vs AI v2 head-to-head smoke benchmark

### Definition

- v1 and v2 use the same fixed depth, evaluation weights, quiescence depth, and root settings.
- v1 disables adaptive killer/history ordering and check-safe quiescence horizon handling.
- v2 enables both current refinements.
- Colors are alternated by the existing `HeadToHeadTournament`.

### Deterministic fixture result

| Fixture | v1 nodes | v2 nodes | Node change | v1 score | v2 score | Same best move |
| --- | ---: | ---: | ---: | ---: | ---: | :---: |
| initial | 88 | 81 | -7.95% | 0 | 0 | yes |
| capture | 56 | 56 | 0.00% | 1982 | 1982 | yes |
| check | 39 | 39 | 0.00% | 1959 | 1959 | yes |
| endgame | 104 | 104 | 0.00% | -269 | -269 | yes |

All four fixtures preserved the same minimax score and selected move. The measured node reduction is evidence for this fixture set only, not a direct playing-strength claim.

### Head-to-head smoke result

- 1 game, 4-ply cap, alternating-color tournament path.
- v1 score: 0.0; v2 score: 0.0.
- completed: 0; unfinished: 1.
- The unfinished game is intentionally not counted as a draw.

### Decision

Keep the benchmark as a regression/evidence harness. The CI job uses the lightweight 1-game/4-ply smoke configuration so search CI remains bounded. Larger strength experiments use the benchmark tool's default 4-game/64-ply configuration or a larger explicit game count.


## 2026-09-22 — Adaptive killer/history move ordering

### Method

- Production search keeps the bound-aware transposition table and TT-PV ordering.
- Quiet beta-cutoff moves now feed deterministic killer-move and history heuristics within a top-level analysis.
- Capture and checking moves remain ahead of killer/history candidates.
- Benchmark reference engines explicitly disable adaptive ordering so the comparison remains a coordinate/forcing-order reference rather than sharing the production heuristic state.
- Python 3.12 on GitHub Actions.

### Production baseline

| Fixture | Depth | Previous nodes | Adaptive-ordering nodes | Change |
| --- | ---: | ---: | ---: | ---: |
| initial | 2 | 88 | 81 | -7.95% |
| capture | 2 | 56 | 56 | 0.00% |
| capture | 3 | 409 | 404 | -1.22% |
| check | 2 | 39 | 39 | 0.00% |
| check | 3 | 472 | 473 | +0.21% |
| double_attack | 2 | 118 | 118 | 0.00% |
| double_attack | 3 | 945 | 945 | 0.00% |
| midgame | 2 | 153 | 153 | 0.00% |
| endgame | 2 | 104 | 104 | 0.00% |
| endgame | 3 | 637 | 638 | +0.16% |

All measured production positions preserved the coordinate-reference minimax score. The check depth-3 fixture produced an equal-score best-move tie difference; this changes the deterministic selected move without changing minimax score and is therefore treated as an ordering tie, not a correctness failure.

### Decision

Promote these node counts as the deterministic regression baseline. The heuristic combination provides a measurable reduction on the initial and capture depth-3 fixtures while remaining essentially neutral on the broader tactical/endgame matrix. It does not justify claiming a universal runtime or playing-strength gain; those require broader profiling and strength tests.

이 문서는 검색 최적화 실험의 재현 가능한 기준점과 의사결정을 별도로 기록합니다. `docs/SEARCH.md`는 현재 구조와 원칙을 설명하고, 이 문서는 실험 결과의 시간순 기록을 담당합니다.

## 2026-09-15 — Forcing-move ordering baseline

### Method

- Reference: coordinate-only move ordering
- Production candidate: capture-first, then checking moves, then stable coordinates
- Same `NegamaxEngine` search, evaluation, caches, and search configuration
- Python 3.12 on GitHub Actions
- Node count is used instead of wall-clock timing because it is deterministic for these fixtures

### Production baseline

| Fixture | Depth | Reference nodes | Production nodes | Reduction |
| --- | ---: | ---: | ---: | ---: |
| initial | 2 | 131 | 131 | 0.00% |
| capture | 2 | 50 | 43 | 14.00% |
| capture | 3 | 490 | 378 | 22.86% |
| check | 2 | 50 | 41 | 18.00% |
| check | 3 | 619 | 487 | 21.32% |
| double_attack | 2 | 133 | 81 | 39.10% |
| double_attack | 3 | 1032 | 896 | 13.18% |

All measured positions preserved the reference minimax score. A best-move difference in the `check` fixture was a deterministic tie-ordering difference because the scores were equal.

### Decision

Keep production ordering as capture-value-first, then checks. The measurements show useful alpha-beta node reduction without changing the measured minimax score.

## 2026-09-15 — Alternative ordering experiments

### Check-first

The experimental ordering places every checking move ahead of every capture. It matched the current ordering on the initial, capture, and check fixtures. It reduced `double_attack` depth 3 from 896 to 859 nodes, but did not provide a consistent benefit across the representative fixture set.

### Capture-check-first

The experimental ordering groups checking captures ahead of other captures/quiet moves.

| Fixture | Depth | Current nodes | Capture-check-first nodes |
| --- | ---: | ---: | ---: |
| initial | 2 | 131 | 131 |
| capture | 2 | 43 | 43 |
| capture | 3 | 378 | 370 |
| check | 2 | 41 | 50 |
| check | 3 | 487 | 619 |
| double_attack | 2 | 81 | 81 |
| double_attack | 3 | 896 | 917 |

All measured alternative-ordering scores matched the coordinate-only reference score. Because the capture-check-first variant regressed the check fixtures and the double-attack depth-3 fixture, it was not promoted to production.

## 2026-09-15 — Legal-move generation cache

### Method

Compare a cache-disabled engine with the production engine while counting underlying `GameState.legal_moves()` generations. The cache key is `(position_key, include_pass)` and is cleared for every top-level analysis.

### Result

| Fixture | Depth | No-cache generations | Cached generations | Reduction |
| --- | ---: | ---: | ---: | ---: |
| initial | 2 | 342 | 237 | 30.70% |
| capture | 2 | 92 | 68 | 26.09% |
| capture | 3 | 812 | 547 | 32.64% |
| check | 2 | 88 | 65 | 26.14% |
| check | 3 | 790 | 525 | 33.54% |
| double_attack | 2 | 164 | 123 | 25.00% |
| double_attack | 3 | 1768 | 1191 | 32.64% |

Every comparison preserved the same minimax score.

### Decision

Keep the per-analysis legal-move cache. The measured reduction in underlying legality generation is substantial enough to preserve the optimization, while elapsed-time speedup remains an explicitly unmeasured runtime property.

## 2026-09-15 — Midgame/endgame fixture expansion

### Method

Add two representative non-initial positions to the deterministic benchmark:

- `midgame`: mixed material and mobility, run at depth 2 to keep CI bounded.
- `endgame`: reduced material, run at depths 2 and 3.

The same four ordering variants and the same cached/uncached legal-move comparison are measured. Existing fixtures remain unchanged and their historical baselines are preserved.

### Search ordering result

| Fixture | Depth | Reference nodes | Production nodes | Reduction |
| --- | ---: | ---: | ---: | ---: |
| midgame | 2 | 262 | 108 | 58.78% |
| endgame | 2 | 144 | 72 | 50.00% |
| endgame | 3 | 2053 | 645 | 68.58% |

Production, check-first, and capture-check-first all preserved the reference minimax score on these new positions. The production ordering also preserved the reference best move on all three measurements.

### Legal-move generation result

| Fixture | Depth | No-cache generations | Cached generations | Reduction |
| --- | ---: | ---: | ---: | ---: |
| midgame | 2 | 251 | 180 | 28.29% |
| endgame | 2 | 165 | 119 | 27.88% |
| endgame | 3 | 1030 | 691 | 32.91% |

Every new comparison preserved the same minimax score.

### Decision

Promote the measured production node counts for `midgame` and `endgame` to deterministic regression baselines. Keep the current production move ordering unchanged. The fixture expansion provides a broader pre-change reference set before considering changes to move ordering or evaluation.

The measured node reduction is evidence for this fixture set only, not a universal runtime or playing-strength claim.

## 2026-09-15 — Midgame depth-3 runtime-bound experiment

A follow-up run temporarily expanded the midgame fixture to depth 3 so that it would be covered symmetrically with the compact tactical and endgame fixtures. The benchmark remained in the `Run search ordering benchmark` step substantially longer than the established bounded runs, without producing a completed result during the review window.

### Decision

Do not promote midgame depth 3 to the regular benchmark matrix. Keep the midgame fixture at depth 2 to preserve a bounded CI job. A future depth-3 midgame study should be run as an explicitly targeted/manual profiling experiment rather than as a mandatory regression gate.

## 2026-09-16 — History-independent checkmate scoring

The search position key intentionally contains only board contents and side-to-move, while checkmate scoring previously added `len(state.history)`. That made two identical positions with different historical move counts produce different cached checkmate values.

The checkmate score now derives mate distance from the configured search depth instead of the historical move count. A regression test constructs identical terminal positions with different history lengths and asserts equal search scores.

### Decision

Keep history out of the search position key and keep terminal scoring independent of `GameState.history`. Search values for a position are now consistent with the cache key's semantic identity.

## CI policy

`.github/workflows/search-benchmark.yml` runs automatically when `janggi/search.py`, `tools/benchmark_search_ordering.py`, or the benchmark workflow changes, and can also be run manually. The production node counts are treated as a deterministic regression baseline. Future changes to production search ordering must update the baseline only when a deliberate algorithmic change is made and the resulting minimax behavior has been reviewed.

Wall-clock timing is not currently used as a mandatory CI gate because hosted-runner timing is noisy. Add timing profiling only when a concrete latency target exists.


## 2026-09-21 — Evaluation v2 baseline

### Method

- Production evaluation changed from material + mobility to evaluation v2.
- Material calibration: chariot 13, cannon 7, horse 5, elephant 3, guard 3, soldier 2.
- Added bounded soldier progress/centrality, palace-guard stability, and check-pressure terms.
- The same ordering variants and deterministic fixtures were re-run.
- Scores were checked against the coordinate-only reference ordering for minimax consistency.

### Search ordering result

| Fixture | Depth | Reference nodes | Production nodes | Reduction |
| --- | ---: | ---: | ---: |
| initial | 2 | 144 | 144 | 0.00% |
| capture | 2 | 50 | 43 | 14.00% |
| capture | 3 | 536 | 393 | 26.68% |
| check | 2 | 50 | 41 | 18.00% |
| check | 3 | 605 | 587 | 2.98% |
| double_attack | 2 | 133 | 81 | 39.10% |
| double_attack | 3 | 1047 | 885 | 15.47% |
| midgame | 2 | 262 | 108 | 58.78% |
| endgame | 2 | 140 | 72 | 48.57% |
| endgame | 3 | 2073 | 635 | 69.37% |

All measured production, check-first, and capture-check-first variants preserved the coordinate-reference minimax score. Equal-score best-move differences remain permissible tie-order differences.

The legal-move-generation cache also remained score-equivalent after the evaluation change.

### Decision

Treat these node counts as the deterministic regression baseline for evaluation v2. The changed counts are expected because the evaluation now produces different alpha-beta cutoffs; the benchmark remains responsible for detecting unintended future search changes.

The benchmark measures deterministic search behavior, not playing strength. The evaluation upgrade therefore still requires targeted tactical/regression positions before deeper search changes are promoted.


## 2026-09-21 — Evaluation v3 / quiescence baseline

### Method

- Evaluation v2 remains unchanged.
- Leaf nodes reached through a capture/checking move receive a bounded `quiescence_depth=1` extension.
- Quiet leaves stop at stand-pat evaluation; check positions search legal evasions; forcing continuations are extended only one additional ply.
- The same deterministic ordering fixtures and score-equivalence checks were re-run.

### Search ordering result

| Fixture | Depth | Reference nodes | Production nodes | Reduction |
| --- | ---: | ---: | ---: | ---: |
| initial | 2 | 144 | 144 | 0.00% |
| capture | 2 | 63 | 56 | 11.11% |
| capture | 3 | 534 | 409 | 23.41% |
| check | 2 | 50 | 41 | 18.00% |
| check | 3 | 519 | 522 | -0.58% |
| double_attack | 2 | 170 | 118 | 30.59% |
| double_attack | 3 | 1063 | 941 | 11.48% |
| midgame | 2 | 235 | 149 | 36.60% |
| endgame | 2 | 186 | 108 | 41.94% |
| endgame | 3 | 2349 | 641 | 72.71% |

All measured orderings preserved the coordinate-reference minimax score. The check depth-3 production node count is slightly above the coordinate reference; this is an ordering-efficiency observation, not a correctness change.

The legal-move cache continued to preserve minimax scores.

### Decision

Keep bounded quiescence at depth 1 as the default. The extension materially increases the tactical search horizon while remaining bounded in the deterministic benchmark. The next AI-strength step should focus on targeted tactical fixtures and, only after those are stable, consider a larger principal search depth.


## 2026-09-21 — Positional evaluation symmetry correction

### Finding

The evaluation's material and mobility terms were zero-sum, but the positional score previously awarded positional bonuses only to the side to move. That meant an opponent's advanced/central soldier or palace guard bonus was not subtracted from the evaluation.

### Change

- keep the existing calibrated material and bounded positional constants;
- score the side to move's positional terms positively and the opponent's corresponding terms negatively;
- add a regression fixture asserting that an opponent's advanced center soldier lowers the side-to-move evaluation;
- keep the search protocol, legality boundary, and default depth unchanged.

### Deterministic search result

| Fixture | Depth | Reference nodes | Production nodes | Reduction |
| --- | ---: | ---: | ---: | ---: |
| initial | 2 | 129 | 129 | 0.00% |
| capture | 2 | 63 | 56 | 11.11% |
| capture | 3 | 534 | 409 | 23.41% |
| check | 2 | 50 | 41 | 18.00% |
| check | 3 | 519 | 522 | -0.58% |
| double_attack | 2 | 170 | 118 | 30.59% |
| double_attack | 3 | 1097 | 983 | 10.39% |
| midgame | 2 | 237 | 149 | 37.13% |
| endgame | 2 | 195 | 108 | 44.62% |
| endgame | 3 | 1965 | 634 | 67.74% |

All measured ordering variants preserved the coordinate-reference minimax score. Production best-move agreement remained unchanged on the fixtures where the benchmark checks deterministic agreement. The changed node counts are expected alpha-beta consequences of the corrected evaluation; they are not a runtime or playing-strength claim.

### Decision

Promote the new production node counts as the regression baseline for the corrected evaluation. Keep the current capture-value-first/check-second ordering unchanged.
