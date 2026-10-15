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


### Legacy exploratory evidence: adjacent pair 2-3

A previously completed calibration artifact from workflow run #46 / PR #80 was recovered for seed 20261002. It contains 10/10 completed games at a 96-ply cap, with the lower level scoring 0.0 and the higher level scoring 10.0.

This artifact predates the provenance-aware calibration format and contains no AI-level configuration fingerprint, engine version, source revision, or calibration protocol version. It is therefore retained as historical/exploratory evidence only and is not mixed into the current provenance-aware aggregation threshold.

| Seed | Games | Completed | Unfinished | Lower score | Higher score | Evidence class |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 20261002 | 10 | 10 | 0 | 0.0 | 10.0 | legacy / exploratory only |

## Important limitation

Level 6 uses an 800 ms wall-clock search budget. Seeded experiments are therefore configuration-repeatable but not guaranteed to be bit-for-bit identical across different runner environments.


### Provenance-aware exploratory evidence: adjacent pair 2-3 (2026-10-15)

Three seed-scoped Render runner batches completed using source revision `aa872c77a07d64ea86273b59903c3bce296300e4`, engine version `7`, calibration protocol `1`, setup `classic`, and AI-level configuration fingerprint `12679f7a449e00888979a5dc4ff5a398697785372f3a870ac5fa99d020aee3fd`.

| Seed | Games | Completed | Unfinished | Lower score (Lv.2) | Higher score (Lv.3) | Outcome |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 20261002 | 2 | 2 | 0 | 0.0 | 2.0 | Level 3 won both games |
| 20261003 | 4 | 4 | 0 | 0.0 | 4.0 | Level 3 won all four games |
| 20261004 | 2 | 2 | 0 | 0.5 | 1.5 | One draw, one Level 3 win |
| **Aggregate** | **8** | **8** | **0** | **0.5** | **7.5** | **Exploratory only** |

Per-game evidence:
- Seed `20261002`: `han_win` at 52 and 23 plies.
- Seed `20261003`: `han_win` at 36, 25, 52, and 23 plies.
- Seed `20261004`: `draw_bikjang` at 36 plies and `han_win` at 25 plies.

All eight raw artifacts include matching configuration fingerprint, Engine version, source revision, and protocol version. The raw artifacts and per-seed aggregate/manifest files are preserved on `calibration/evidence-20261015`:
- `artifacts/ai-level-calibration/ai-level-strength-2-3-seed-20261002-classic.json`
- `artifacts/ai-level-calibration/ai-level-strength-2-3-seed-20261003-classic.json`
- `artifacts/ai-level-calibration/ai-level-strength-2-3-seed-20261004-classic.json`

The latest combined evaluator-shaped snapshot is `artifacts/ai-level-calibration/aggregate-2-3-classic-seeds-20261002-20261004.json`.

The combined status is still `INSUFFICIENT`: 8 completed games do not meet the 20-completed-game threshold, although the 3-seed and unfinished-rate requirements are satisfied. This evidence is not mixed with the historical legacy 2-3 artifact. The observed 7.5–0.5 score is descriptive only, not a calibrated strength conclusion or authorization to change public level configuration.

The initial 12-game/multi-seed request emitted no completed artifact and is excluded entirely. The 2-game batches completed in approximately 6m7s and 5m35s; the 4-game batch completed in approximately 13m9s and is too close to the Free Web Service idle limit to be the standard batch size. The runner is now disabled.