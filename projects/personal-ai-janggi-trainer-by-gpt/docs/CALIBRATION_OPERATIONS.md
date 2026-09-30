# Calibration Operations

## Purpose

Long-running adjacent AI-level self-play calibration is an evidence-generation workload, not a CI correctness gate.

GitHub Actions remains the path for fast deterministic validation and ordinary pull-request checks. Calibration compute must be executable without consuming the CI quota.

## Current boundary

- GitHub Actions quota is currently exhausted.
- Do not launch additional long-running calibration workflows through Actions while the quota is exhausted.
- Existing valid evidence remains authoritative as recorded in `docs/AI_LEVEL_CALIBRATION_EVIDENCE.md`.
- The 1-2 pair is evidence-sufficient: 21/22 games completed, 4.545% unfinished, 2 seeds.
- Pairs 2-3, 3-4, 4-5, and 5-6 remain uncalibrated.

## Off-CI execution

The existing benchmark CLI already supports the required pair-scoped, seeded experiment. It can be run outside GitHub Actions without changing the engine or public AI-level configuration:

```bash
cd projects/personal-ai-janggi-trainer-by-gpt

python tools/benchmark_ai_levels.py \
  --tournament-games 12 \
  --max-plies 96 \
  --pair 2-3 \
  --seed 20261002 \
  --setup classic \
  --skip-search-benchmark \
  --output artifacts/ai-level-strength-2-3-seed-20261002-classic.json
```

Run a second distinct seed for the same pair, then aggregate both artifacts:

```bash
python tools/evaluate_ai_level_evidence.py \
  artifacts/ai-level-strength-2-3-seed-20261002-classic.json \
  artifacts/ai-level-strength-2-3-seed-20261003-classic.json
```

The same pattern applies to 3-4, 4-5, and 5-6.

The 12-games-per-run value is an initial bounded operating point, not a fixed requirement. A calibration artifact is uniquely identified by pair + seed + setup; existing artifacts are validated and reused rather than overwritten. Review completion rate first; add another run when the pair has not yet reached the evidence threshold.
## Provenance and compatibility

Every new artifact records the calibrated pair's public AI-level configuration fingerprint, Engine version, source revision when available, and calibration protocol version.

The evaluator uses these fields to prevent incompatible experiments from being aggregated. Changing public search configuration or calibration protocol therefore requires a fresh evidence set rather than silently extending an old one.

## Review rule

An adjacent pair is evidence-sufficient only when all default evidence-review thresholds are met:

- at least 20 completed games;
- unfinished rate at or below 25%;
- at least 2 distinct seeds.

An unfinished game is retained as experiment evidence but does not contribute to a completed-game strength score.

The evaluator's result is descriptive evidence only. It does not authorize changing public AI-level search budgets or difficulty behavior.

## Artifact handling

For every off-CI run, preserve:

1. the raw calibration JSON artifact;
2. its experiment identity (pair + seed + setup);
3. the aggregation output used for review;
4. the resulting status in `docs/AI_LEVEL_CALIBRATION_EVIDENCE.md`;
5. a checkpoint/history entry describing the run and decision boundary.

Do not rewrite or discard previously collected evidence. New runs must remain independently identifiable.

## Separation principle

`fast CI validation` != `long-running strength calibration`

This separation prevents experimental workload from consuming the quota required for normal regression checks and keeps calibration results reproducible and reviewable as versioned evidence.


## Resumable runner

Use `tools/run_ai_level_calibration.py` when several experiments must be executed outside CI:

```bash
python tools/run_ai_level_calibration.py \
  --pair 2-3 \
  --seed 20261002,20261003 \
  --games 12 \
  --max-plies 96
```

The runner:

- skips an existing raw artifact so interrupted work can resume;
- never overwrites an existing experiment artifact, preserving evidence history;
- keeps each experiment uniquely identified by pair, seed, and setup;
- aggregates each requested pair after the raw runs;
- writes a `manifest.json` describing the execution set and any failures;
- never changes public AI level configuration.

Changing the game-count or ply-cap for an already-used `pair + seed + setup` identity requires a separately reviewed experiment policy; do not overwrite the existing artifact.
