# AI Levels

The browser trainer exposes six AI levels. A level changes only the search profile; Janggi legality remains authoritative in GameState.

| Level | Name | Search profile |
| --- | --- | --- |
| 1 | 입문 | depth 1, no quiescence, no root refinement, mobility 0 |
| 2 | 초급 | depth 1, no quiescence, no root refinement, mobility 2 |
| 3 | 중급 | depth 2, no quiescence, no root refinement, mobility 2 |
| 4 | 고급 | depth 2, quiescence 1, no root refinement, mobility 2 |
| 5 | 상급 | depth 2, quiescence 1, root refinement 2, mobility 2 |
| 6 | 전문 | depth 3, quiescence 1, no root refinement, mobility 2 |

## Important distinction

The six levels are a search-complexity ladder, not yet a validated playing-strength ladder.

A higher level performs more search work and is expected to have access to a larger tactical horizon, but a configuration change alone is not evidence that the resulting engine wins more games.

Strength should be validated through:

1. deterministic search fixtures;
2. adjacent-level self-play;
3. repeated head-to-head evaluation with color alternation;
4. Elo-style tracking;
5. later, learned evaluation versions.

## Runtime policy

Level 1 is the default gameplay profile because the Render service is latency-sensitive.

Levels 2–5 increase search quality incrementally. Level 6 is a deeper search profile and may require substantially more computation on the current Render instance.

The level is applied when a new match is initialized. Changing the selector does not alter an in-progress match until reset.

## Future AI versions

The level system is intentionally separate from future model/version promotion:

AI v1 -> AI v2 -> AI v3 -> ...

A version change may improve evaluation, move ordering, search, or learned parameters while preserving the same public level ladder.

The evaluation/tournament pipeline should decide whether a new version is strong enough to replace the previous one; the browser level should remain the user's difficulty control.


## Expert search budget

Lv6 Expert uses iterative deepening with a maximum depth of 3 and an 800 ms wall-clock budget. The effective depth can be lower when a position is computationally expensive.


## Strength calibration workflow

The six public levels are not promoted to a calibrated strength ladder solely from search configuration.

The current validation path is:

1. deterministic fixture search benchmark for every level;
2. adjacent-level self-play with alternating colors;
3. repeat the comparison with enough completed games to reduce outcome noise;
4. record unfinished games separately rather than treating them as draws;
5. only then consider changing level search budgets or evaluation parameters.

The machine-readable evidence tool is `tools/benchmark_ai_levels.py`. CI treats the benchmark as evidence collection, not as a pass/fail strength gate. A benchmark result cannot by itself justify changing the public level ladder; changes must be supported by the measured results and regression tests.
