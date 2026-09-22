# AI v1 vs AI v2 Strength Benchmark

## Purpose

The deterministic AI v1/v2 benchmark isolates search-algorithm changes by keeping depth, evaluation, quiescence depth, and root settings equal. It demonstrates fixture-level node-count and minimax-score behavior, but it is not a playing-strength measurement.

This document defines the larger self-play experiment used to collect exploratory playing-strength evidence.

## Method

- Reuse the existing `HeadToHeadTournament`; no second tournament engine is introduced.
- Alternate colors on every game.
- v1 and v2 retain the same fixed depth/evaluation/root configuration used by the A/B benchmark.
- Adaptive move ordering and check-safe quiescence remain the only version switches.
- Deterministic tie-breaking is the default for strength measurement so search changes are not mixed with RNG/tie-order effects.
- Optional stochastic self-play uses fixed seeds and a separate seed stream for each model; it is a distinct experiment mode.
- Unfinished games are reported separately and are excluded from win/draw score and Elo updates.
- Every engine move is still validated by `HeadToHeadEvaluator` through the authoritative `GameState` legality boundary.
- Elo starts at 1000/1000 and uses the existing `rating.update_ratings()` primitive with K=16 by default.
- The manual experiment supports staged sample sizes such as 8, 20, 50, and 100 games. Use the smaller samples for iteration and the larger samples only after the benchmark is stable. The default full experiment remains 100 games with a 128-ply cap from the classic starting arrangement.

## CI policy

Pull requests run only a 2-game/8-ply smoke benchmark so the normal CI path remains bounded.

The full 100-game experiment is manual through:

`.github/workflows/janggi-ai-strength-benchmark.yml`

The workflow stores the JSON result as a GitHub Actions artifact and writes the result to the Actions job summary.

## Result interpretation

The full experiment must be reported with:

- games requested;
- completed and unfinished counts;
- v1 wins, v2 wins, and draws;
- v1 score percentage over completed games;
- final sequential Elo values and rating delta;
- v1 score percentage with an approximate 95% confidence interval;
- setup, seed, max-plies, K-factor, and tie-breaking mode.

A single 100-game run is exploratory evidence, not proof of a universal strength advantage. A second seed or larger sample should be considered before making a broader conclusion, especially when unfinished-game frequency is material.

## Current status — 2026-09-22

The benchmark harness and PR smoke workflow are implemented.

No full 100-game result has been recorded yet. Until the manual run is completed and its JSON evidence is reviewed, no playing-strength conclusion is recorded.

The PR smoke benchmark is intentionally short and is not a strength claim. The next measurement sequence should be deterministic first (8/20/50/100 games as needed), followed by a separate stochastic self-play run when practical game diversity is being studied.
