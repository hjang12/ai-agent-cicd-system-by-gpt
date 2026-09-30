# AI Level Calibration Evidence

This document defines how adjacent-level calibration artifacts are reviewed after bounded self-play runs.

## Evidence unit

Each calibration JSON artifact contains one adjacent level pair and one experiment identity:

pair + seed + setup

The artifact records both aggregate results and every game's terminal status, lower-level outcome, and ply count.

## Aggregation

Use:

python tools/evaluate_ai_level_evidence.py <artifact>...

The evaluator combines multiple non-duplicate experiment identities and reports each adjacent pair separately.

Default evidence review thresholds are deliberately conservative:

- at least 20 completed games per adjacent pair;
- unfinished games at or below 25%;
- at least 2 distinct seeds per adjacent pair.

These are evidence-review defaults, not public level-promotion rules. They can be overridden for exploratory work.

## Interpretation

INSUFFICIENT means the collected evidence is not enough to support an adjacent-level playing-strength conclusion under the selected thresholds.

HIGHER_SCORED, LOWER_SCORED, and EQUAL_SCORE describe the completed-game score relationship only.

candidate_monotonic_higher_levels=true means every adjacent pair with the required evidence is currently HIGHER_SCORED. It is a descriptive evidence flag only. Public AI level search budgets, evaluation parameters, and difficulty behavior must not be changed solely because this flag is true.

## Important limitation

Level 6 uses an 800 ms wall-clock search budget. Seeded experiments are therefore configuration-repeatable but not guaranteed to be bit-for-bit identical across different runner environments.
