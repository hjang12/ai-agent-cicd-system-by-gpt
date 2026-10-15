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


## 2026-09-29 pre-batch PR smoke calibration result

Before calibration was changed to pair-scoped runs, the automated PR smoke used 2 games per adjacent pair with a 4-ply cap. All five adjacent pairs completed the benchmark harness successfully, but every game remained unfinished because the cap was intentionally short.

Therefore:

- completed games: 0
- unfinished games: 10
- no win/loss/draw strength conclusion is drawn
- the result validates the calibration pipeline only

The current PR smoke is intentionally narrower: it validates one adjacent pair with 2 games and a 4-ply cap. Full calibration is performed through the manual pair-scoped workflow.

A larger game/ply configuration remains required for actual level-strength evidence.

## Expert search budget

Lv6 Expert uses iterative deepening with a maximum depth of 3 and an 1200 ms wall-clock budget. The effective depth can be lower when a position is computationally expensive.


## Strength calibration workflow

The six public levels are not promoted to a calibrated strength ladder solely from search configuration.

The current validation path is:

1. deterministic fixture search benchmark for every level, maintained by the dedicated search benchmark workflow;
2. adjacent-level self-play with alternating colors;
3. repeat the comparison with enough completed games to reduce outcome noise;
4. record unfinished games separately rather than treating them as draws;
5. only then consider changing level search budgets or evaluation parameters.

The machine-readable evidence tool is `tools/benchmark_ai_levels.py`. CI treats the benchmark as evidence collection, not as a pass/fail strength gate. A benchmark result cannot by itself justify changing the public level ladder; changes must be supported by the measured results and regression tests.

## Calibration execution policy

A full six-level calibration is executed as five bounded adjacent-pair runs (`1-2`, `2-3`, `3-4`, `4-5`, `5-6`) rather than one long all-pairs job. The workflow accepts one pair, an even game count, and a ply cap. This avoids a single runner timeout hiding partial evidence.

The 2026-09-29 experiment that attempted 4 games × 64 plies across all five pairs was cancelled by the 20-minute GitHub Actions timeout before producing an artifact. It is treated as an incomplete experiment, not as a strength result.

Future calibration evidence should record the pair, seed, requested games, completed games, unfinished games, and repeated-run seed where applicable.

Each calibration artifact also records per-game terminal status, lower-level outcome, and ply count. This keeps completed-game evidence auditable instead of relying only on the aggregate pair summary. When the calibration workflow runs the optional deterministic search benchmark, those fixture rows are stored under `search_fixtures` in the same artifact; the normal calibration path skips this repeated benchmark because the dedicated search benchmark workflow already owns it.

Calibration runs use benchmark-only fixed-seed tie randomization by default. This does not change the public AI level configuration; it only varies equal-score move choices during self-play so repeated games are not forced to follow the same deterministic trajectory. The starting arrangement can also be selected explicitly (classic, left, right, or both) and is recorded in the evidence artifact. These controls make the experiment configuration repeatable, but level 6 remains wall-clock-sensitive because its production search uses an 800 ms budget, so identical seeds do not guarantee bit-for-bit identical outcomes across runner environments.
