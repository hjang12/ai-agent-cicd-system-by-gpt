# Search

## Current backend

The current engine is the dependency-free `NegamaxEngine` in `janggi/search.py`.

```text
GameState
  ↓
legal moves
  ↓
move ordering
  ↓
Negamax + Alpha-Beta
  ↓
Material + Mobility + positional evaluation
```

## Search configuration

`SearchConfig` currently supports:

- `depth`
- `mobility_weight`
- `random_ties`
- `seed`

The baseline engine metadata version is now `2`, reflecting the upgraded evaluation contract.

## Evaluation v2

The evaluation now combines material, mobility, and small domain-aware positional terms:

- material values are calibrated to common Janggi point ordering: chariot 13, cannon 7, horse 5, elephant 3, guard 3, soldier 2;
- advanced soldiers receive a modest forward-progress bonus, with a small central-file preference;
- guards retained inside their own palace receive a small defensive bonus;
- checking pressure receives a bounded score bonus, while being in check receives the corresponding penalty.

These terms are deliberately small relative to material and mate scores. They improve leaf-position discrimination without moving legality or terminal-state decisions out of `GameState`.

The default behavior remains deterministic unless root-level random tie breaking is explicitly enabled.

## Move ordering

Search considers tactical forcing moves before quiet moves using this priority:

1. captures, ordered by captured piece value;
2. checking moves;
3. stable source/destination coordinates for deterministic ties.

Check status is determined through `GameState.apply()` and `is_in_check()`, so authoritative Janggi legality remains in the domain layer. A small per-analysis check cache avoids recomputing the same move's check status while the tree is being ordered.

This ordering does not change the minimax score. Its purpose is to expose useful alpha-beta cutoffs earlier.

## Ordering benchmark

A deterministic reference benchmark is kept in `tools/benchmark_search_ordering.py`. It compares the production ordering against a coordinate-only ordering while keeping the same search, evaluation, caches, and search depth. The benchmark also includes two non-production experiments: all checks ahead of captures, and checking captures ahead of other forcing moves. The workflow is `.github/workflows/search-benchmark.yml`, and it runs automatically when search or benchmark files change, as well as on manual dispatch.

The representative fixture set now includes the initial position, compact tactical positions, a mixed-material midgame position, and a reduced-material endgame position. The midgame fixture is intentionally depth-2 only; the compact tactical fixtures and endgame fixture also run at depth 3 to keep CI bounded.

Baseline measurements on GitHub Actions (Python 3.12) for the production ordering are:

| Fixture | Depth | Reference nodes | Production nodes | Node reduction |
| --- | ---: | ---: | ---: | ---: |
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

All measured positions preserved the reference minimax score. The `check` fixture still has deterministic best-move differences caused by equal-score tie ordering rather than a score change. The new midgame/endgame fixtures matched the reference best move at the measured depths.

The latest alternative-ordering experiment remains informative rather than production guidance. Check-first reduced the compact `double_attack` depth-3 fixture from 896 to 859 nodes but did not provide a consistent benefit across the earlier fixture set. Capture-check-first reduced capture depth 3 from 378 to 370 but regressed the check fixtures and was worse on `double_attack` depth 3 (917 vs 896). The expanded midgame/endgame fixture results are now part of the regression baseline before any future production ordering change.

The benchmark treats the production node counts as deterministic regression baselines. A future production-ordering change causes the benchmark job to fail when a baseline count changes unexpectedly; this makes search regressions visible without relying on wall-clock timing. Alternative ordering experiments remain informational until a stronger and more representative fixture set justifies a production change.

Detailed time-ordered experiment records are kept in `docs/SEARCH_BENCHMARK_HISTORY.md`.

These measurements support keeping the current forcing-move ordering. They are evidence for node reduction, not a performance guarantee across all positions; the current evaluation's mobility generation remains a major cost center. Re-run the benchmark before adopting a materially different move-ordering scheme.

## Legal move generation cache

Within one top-level `analyze()` call, the engine now caches `GameState.legal_moves()` results by position key and the `include_pass` policy. This is an engine-side cache: `GameState` remains the authoritative legality implementation.

The cache avoids repeating identical legality generation when move ordering and evaluation inspect the same position. It is cleared at the beginning of each top-level analysis, so independent searches do not share cached state.

A deterministic benchmark also compares the cached engine with a no-cache reference by counting underlying `GameState.legal_moves()` generations. The latest automated run measured:

| Fixture | Depth | No-cache generations | Cached generations | Reduction |
| --- | ---: | ---: | ---: | ---: |
| initial | 2 | 342 | 237 | 30.70% |
| capture | 2 | 92 | 68 | 26.09% |
| capture | 3 | 812 | 547 | 32.64% |
| check | 2 | 88 | 65 | 26.14% |
| check | 3 | 790 | 525 | 33.54% |
| double_attack | 2 | 164 | 123 | 25.00% |
| double_attack | 3 | 1768 | 1191 | 32.64% |
| midgame | 2 | 251 | 180 | 28.29% |
| endgame | 2 | 165 | 119 | 27.88% |
| endgame | 3 | 1030 | 691 | 32.91% |

All of these comparisons preserved the same minimax score. These are counts of underlying legality generations, not elapsed-time guarantees; wall-clock profiling can be added later when a runtime target requires it.

This optimization does not intentionally change node counts or minimax results. Its expected benefit is lower repeated legality/mobility work, so the generation counts should be reviewed alongside later profiling rather than treated as a universal runtime guarantee.

## Transposition table

The search backend maintains a per-analysis transposition table keyed by:

```text
(position_key, remaining_depth)
```

Only exact results are cached. Nodes where alpha-beta cut off the remaining moves are deliberately not cached as exact values because a cutoff result is only a bound under the current search window.

The table is cleared for each top-level `analyze()` call so results remain isolated between analyses.

## Evaluation cache

The material/mobility evaluation is also cached per `position_key` within a top-level analysis. The key includes board state and side to move, which are the inputs that affect the current evaluation.

This avoids repeating the two-side mobility generation when the same position is evaluated through multiple search paths. The cache is cleared together with the transposition table for each top-level analysis.

## Performance boundary

The current evaluation function still computes legal-move mobility for both sides. This is intentionally simple and dependency-free, but mobility generation remains a major cost center for deeper search.

The current optimization sequence is:

1. capture-first move ordering;
2. exact-result transposition caching;
3. per-analysis evaluation caching;
4. checking-move ordering with per-analysis check caching;
5. measure ordering impact with representative deterministic fixtures;
6. preserve deterministic node-count baselines for regression detection;
7. per-analysis legal move caching to reduce repeated mobility generation;
8. evaluate alternative forcing-order schemes before production adoption;
9. bounded multi-ply tactical analysis for coaching;
10. stronger evaluation features only after representative regression positions exist;
11. evaluation v2 with calibrated material and bounded positional terms.

Search optimization must not move authoritative move legality out of `GameState` or couple the domain layer to the search implementation.
