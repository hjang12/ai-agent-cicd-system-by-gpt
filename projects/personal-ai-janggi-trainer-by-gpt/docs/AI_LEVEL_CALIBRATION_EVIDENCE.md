# AI Level Calibration Evidence

This document defines how adjacent-level calibration artifacts are reviewed after bounded self-play runs.

## Evidence unit

Each calibration JSON artifact contains one adjacent level pair and one experiment identity:

pair + seed + setup + calibration protocol version + fixture mode (protocol-v2 runs)

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

Legacy 1-2 evidence remains valid as a historical evidence set because both artifacts share the same legacy schema. Protocol-v1 evidence for pair 2-3 remains a separate historical/exploratory set. New calibration runs should use protocol-v2 provenance-aware artifacts and must not mix protocol-v1 and protocol-v2 evidence.

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

### Protocol-v2 exploratory evidence: adjacent pair 2-3, seed 20261005

This protocol-v2 run used source revision `535598c4445f2bb9d8edaef05bb9cc90b1ad1279`, engine version `7`, the recorded configuration fingerprint, `classic` setup, `tactical` fixture mode, a 96-ply cap, and two requested games.

| Game | Fixture | Terminal status | Plies | Lower outcome |
| ---: | --- | --- | ---: | ---: |
| 1 | capture | `draw_bikjang` | 2 | 0 |
| 2 | check | `draw_bikjang` | 3 | 0 |

The process returned code 0 and both games were technically completed, producing a score of Lv.2 `1.0` : Lv.3 `1.0`. However, both games ended in bikjang after only 2 and 3 plies. **This is retained as raw exploratory evidence but should not be treated as an informative playing-strength sample.** The result remains `INSUFFICIENT`; it is not evidence that the two levels are equal.

Artifacts reconstructed from the matching Render log `BEGIN/END` frames:
- `artifacts/ai-level-calibration/ai-level-strength-2-3-seed-20261005-classic-v2-tactical.json`
- `artifacts/ai-level-calibration/aggregate-2-3-classic-v2-tactical.json`
- `artifacts/ai-level-calibration/manifest-v2-tactical-classic-seed-20261005.json`

Runner wall time from its own timestamps was 5.605054 seconds; this is process elapsed time, not CPU time. The runner was disabled immediately after the run. The early bikjang outcomes identify a fixture-quality gap: synthetic fixtures need a more realistic blocker/material layout and a regression guard against trivial early bikjang before another batch is run. These protocol-v2 results must remain separate from protocol-v1 and any corrected future fixture protocol.

## Protocol transition

Protocol-v2 introduced explicit initial/capture/check/endgame/tactical fixture metadata. Seed 20261005 is preserved but both tactical games ended in bikjang after only 2 and 3 plies, so the result is low-information and not a strength conclusion.

Protocol-v3 rebuilds the synthetic capture/check fixtures to retain normal material and blockers, rejects synthetic bikjang before 8 plies, scopes each manifest by pairs/seeds/setup/fixture/games/plies/source revision, and limits completion logs to artifacts listed by the matching request manifest. Protocol-v3 results form a separate evidence set. Protocol-v1 and protocol-v2 evidence remain preserved and must not be mixed into protocol-v3 conclusions.


## Protocol-v3 pilot — Seed 20261006

### Run conditions

- Source revision: `e7651d557fb6fd13f6f110d3e7604360225d15d3`
- Pair: 2-3 (`초급` vs `중급`); seed: `20261006`; setup: classic; fixture mode: tactical; protocol: 3.
- Requested games: 2; maximum plies: 96; engine version: 7.
- AI-level configuration fingerprint: `12679f7a449e00888979a5dc4ff5a398697785372f3a870ac5fa99d020aee3fd`
- Runner returned code 0. Its own timestamps span 7 minutes 25.598 seconds; this is process wall time, not CPU time.
- The runner was reset to `CALIBRATION_ENABLED=false`; reset deployment `dep-db8lu0m89jmc73bu1oeg` reached `live`, and startup logs confirmed idle mode.

### Results

| Game | Fixture | Terminal result | Plies | Outcome for Lv.2 |
| --- | --- | --- | ---: | ---: |
| 1 | capture | `han_win` | 68 | -1 |
| 2 | check | `cho_win` | 69 | -1 |

Both games completed without an unfinished game. Lv.3 won both games, including after the lower-level engine's starting side was alternated. Combined score was Lv.2 `0.0` : Lv.3 `2.0`, with no draws. Neither game ended in early bikjang, so the protocol-v3 fixture-quality guard passed for the capture/check fixtures exercised by this two-game batch.

### Interpretation and preserved artifacts

The aggregate evaluator still reports `INSUFFICIENT`: only 2 completed games and 1 unique seed are available for pair 2-3, below the existing thresholds of 20 completed games and 2 unique seeds. The result is directionally consistent with Lv.3 being stronger in this small sample, but does not establish calibrated strength or authorize public level/search-budget changes. Protocol-v1, protocol-v2, and protocol-v3 results remain separate.

- Raw: `artifacts/ai-level-calibration/ai-level-strength-2-3-seed-20261006-classic-v3-tactical.json`
- Aggregate: `artifacts/ai-level-calibration/aggregate-2-3-classic-v3-tactical.json`
- Manifest: `artifacts/ai-level-calibration/manifest-v3-pairs-2_3-seeds-20261006-setup-classic-fixture-tactical-g2-p96-src-e7651d557fb6.json`

Next action: continue protocol-v3 evidence collection for pair 2-3 with a fresh seed, retaining the disabled-first / bounded-run / preserve-artifacts / disable-after-run procedure. Do not change public AI-level budgets from this pilot.


### Protocol-v3 follow-up — seed 20261007

#### Run conditions

- Code source revision: `a0bc620181e8101331110e457219174f6c90d413`; protocol v3; engine version 7.
- Pair: 2-3 (`초급` vs `중급`); seed: `20261007`; classic setup; tactical fixtures; 2 games; 96-ply cap.
- AI-level configuration fingerprint: `12679f7a449e00888979a5dc4ff5a398697785372f3a870ac5fa99d020aee3fd`.
- Runner return code: 0. Its timestamps span 7 minutes 7.084 seconds of process wall time (not CPU time).
- The unique aggregate output path was exercised: `aggregate-v3-pair-2_3-seeds-20261007-setup-classic-fixture-tactical-g2-p96-src-a0bc620181e8.json`. It did not reuse seed 20261006's report filename.

#### Results

| Game | Fixture | Terminal result | Plies | Outcome for Lv.2 |
| --- | --- | --- | ---: | ---: |
| 1 | capture | `draw_bikjang` | 70 | 0 |
| 2 | check | `cho_win` | 41 | -1 |

Both games completed; there were 0 unfinished games. Combined score for this run: Lv.2 `0.5` : Lv.3 `1.5`, with one draw and one Lv.3 win. The capture fixture's bikjang occurred at 70 plies and did not trigger the protocol-v3 early-bikjang guard.

#### Cumulative protocol-v3 snapshot for pair 2-3

Across seeds `20261006` and `20261007`, the raw run results tally to 4 completed games / 0 unfinished across 2 unique seeds: Lv.2 wins 0, Lv.3 wins 3, draws 1; descriptive score Lv.2 `0.5` : Lv.3 `3.5`. This cross-run tally is descriptive, calculated from the two preserved raw files; the per-request aggregate files remain run-scoped by design.

Calibration remains `INSUFFICIENT`: only 4 completed games are available against the existing 20-game threshold. Do not infer a final rating/order or change public AI level/search-budget settings. Keep protocol-v1, v2, and v3 evidence separate.

- Raw: `artifacts/ai-level-calibration/ai-level-strength-2-3-seed-20261007-classic-v3-tactical.json`
- Aggregate: `artifacts/ai-level-calibration/aggregate-v3-pair-2_3-seeds-20261007-setup-classic-fixture-tactical-g2-p96-src-a0bc620181e8.json`
- Manifest: `artifacts/ai-level-calibration/manifest-v3-pairs-2_3-seeds-20261007-setup-classic-fixture-tactical-g2-p96-src-a0bc620181e8.json`

The runner reset deploy `dep-db8miufavr4c73dga81g` reached `live` and logs confirmed `CALIBRATION_ENABLED=false` / idle mode. Next action: preserve and merge these files/context, then continue pair 2-3 with fresh protocol-v3 seed `20261008` using the same disabled-first, two-game bounded procedure.
