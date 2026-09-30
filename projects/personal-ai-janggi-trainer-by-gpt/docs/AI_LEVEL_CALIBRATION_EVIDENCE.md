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

## Provenance compatibility

New calibration artifacts record:

- public AI-level configuration fingerprint for the calibrated pair;
- engine version;
- source revision when available;
- calibration protocol version.

The evaluator rejects incompatible AI-level configuration fingerprints, engine versions, or calibration protocol versions within the same adjacent pair. It also rejects mixing legacy artifacts without provenance metadata with provenance-aware artifacts, or mixing legacy artifacts with protocol-aware artifacts.

Legacy 1-2 evidence remains valid as a historical evidence set because both artifacts share the same legacy schema. New calibration runs should use provenance-aware artifacts.

## Collected evidence

### Adjacent pair 1-2

The first bounded evidence attempt at 48 plies was insufficient (1 completed / 9 unfinished). A 96-ply cap was then used for the evidence runs.

| Seed | Games | Completed | Unfinished | Lower score | Higher score |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 20260930 | 10 | 9 | 1 | 4.0 | 5.0 |
| 20261001 | 12 | 12 | 0 | 5.5 | 6.5 |
| **Aggregate** | **22** | **21** | **1** | **9.5** | **11.5** |

The aggregate meets the default evidence thresholds (21 completed games, 4.545% unfinished, 2 seeds). The score relationship is descriptive evidence only: it does not authorize public level promotion or search-budget changes. Adjacent pairs 2-3 through 5-6 have not yet met the evidence threshold.

## Important limitation

Level 6 uses an 800 ms wall-clock search budget. Seeded experiments are therefore configuration-repeatable but not guaranteed to be bit-for-bit identical across different runner environments.
