# Calibration Operations

## Purpose

Long-running adjacent AI-level self-play calibration is an evidence-generation workload, not a CI correctness gate.

GitHub Actions remains the path for fast deterministic validation and ordinary pull-request checks. Calibration compute must be executable without consuming the CI quota.

The adjacent-level calibration workload has a dedicated Render execution service. GitHub Actions may remain available for bounded/manual diagnostics, but pull requests and ordinary pushes must not launch long-running calibration compute automatically.

## Current boundary

- Fast GitHub Actions validation is operational, but long-running calibration remains intentionally off-CI.
- Do not move adjacent-level calibration back into the normal PR/push validation path; preserve the fast-correctness vs strength-evidence separation.
- Existing valid evidence remains authoritative as recorded in `docs/AI_LEVEL_CALIBRATION_EVIDENCE.md`.
- The 1-2 pair is evidence-sufficient: 21/22 games completed, 4.545% unfinished, 2 seeds.
- Pairs 2-3, 3-4, 4-5, and 5-6 remain uncalibrated under the current provenance-aware protocol.

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

## Dedicated Render calibration runner

The project now includes `tools/calibration_runner_service.py`, a dependency-free HTTP wrapper around `tools/run_ai_level_calibration.py`.

Render service:

- name: `personal-ai-janggi-calibration-runner`;
- region: Singapore;
- plan: Free;
- auto deploy: disabled;
- root: `projects/personal-ai-janggi-trainer-by-gpt`;
- start command: `python tools/calibration_runner_service.py`;
- health check: `/api/health`.

The runner executes one explicitly configured calibration request at service start and then remains available for status/artifact retrieval. It does not expose a remote "run arbitrary calibration" API.

The Render Free Web Service is not a durable long-running worker. It may stop after 15 minutes without inbound traffic, and its local filesystem is ephemeral across stop/restart/redeploy. An initial 12-game, multi-seed service-start request produced no completed artifact, so it is not counted as evidence. The bounded operating unit is one seed with 2 games at the 96-ply cap, followed by immediate evidence retrieval and preservation before any redeploy. Do not bundle multiple seeds or the 12-game default into a single Free Web Service run. Keep each artifact's original pair + seed + setup identity and source provenance. If this minimum batch cannot complete reliably, move the execution workload to a durable worker/job with persistent output rather than adding more polling or state layers to the web service.

Configuration is provided through Render environment variables:

```text
CALIBRATION_ENABLED=true
CALIBRATION_PAIR=2-3
CALIBRATION_SEEDS=20261002
CALIBRATION_SETUP=classic
CALIBRATION_GAMES=2
CALIBRATION_MAX_PLIES=96
```

Operational endpoints are read-only:

- `GET /api/health` — runner health;
- `GET /api/status` — request state and produced artifact names;
- `GET /api/artifacts/<filename>` — retrieve a generated JSON artifact.

The normal operating sequence is:

1. set the next pair/seed request in the runner environment;
2. manually deploy the runner service with exactly one seed and a 2-game batch;
3. wait for the status to reach `completed` or `failed` without redeploying the service;
4. retrieve the raw JSON and aggregate report before any subsequent deploy, then commit them to the evidence branch;
5. update `docs/AI_LEVEL_CALIBRATION_EVIDENCE.md` and the task checkpoint from the collected evidence.

Never treat an absent artifact after a stopped/restarted service as a completed experiment. Record it as an execution failure and do not aggregate it. The raw artifact and aggregate output in the repository are the durable record; the Render service's local files are only staging.

The runner itself never changes public AI level configuration and never treats a higher-scoring result as authorization for a search-budget change.

## Current execution constraint

The execution path is now implemented and source-controlled. New strength evidence is not considered collected until the dedicated Render runner has completed the requested experiments and the resulting artifacts have passed the existing provenance-aware evaluator.


## 2026-10-15 — Free runner interruption and bounded evidence recovery

- A 12-game, two-seed request on the Free Web Service emitted the first seed's command but no completion/artifact output before execution logs stopped. It is explicitly not counted.
- A bounded 2-game request for pair `2-3`, seed `20261002`, setup `classic`, source revision `aa872c77a07d64ea86273b59903c3bce296300e4` completed with return code 0 in about 6m7s.
- Observed result: 2/2 completed, 0 unfinished, Level 2 score 0.0 and Level 3 score 2.0. This remains insufficient evidence under the 20-completed-game / 2-seed threshold.
- The raw artifact, aggregate report, and manifest were preserved on branch `calibration/evidence-20261015`.
- Root cause is execution-path mismatch: a free web service with ephemeral local storage was used for bounded-but-still-long benchmark work. Further runs are seed-scoped and small, with immediate evidence preservation before any redeploy. If this is still unreliable, use a durable job/worker execution path; do not claim that a live HTTP server proves a calibration process completed.
