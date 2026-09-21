# Training Session Metrics

`janggi/training_metrics.py` keeps a minimal, in-memory measurement of position-training attempts for the currently running trainer process.

## Metrics

- `attempts` — legal training answers submitted;
- `correct` / `incorrect` — answer outcome counts;
- `unique_problems` — distinct session-local problem identifiers attempted;
- `accuracy` — correct divided by attempts, or `0.0` when there are no attempts;
- `reason_attempts` — coaching reason codes associated with attempted problems.

## Lifecycle

Metrics are reset together with the active match on `POST /api/reset`. They are not written to disk, a database, or a user profile.

`POST /api/training/problems` returns the current metric snapshot. `POST /api/training/answer` updates the snapshot after a legal answer and returns the updated metrics. `GET /api/training/metrics` reads the current snapshot without changing state.

## Boundary

These metrics are intentionally too small to represent mastery, learning gain, streaks, or model-training evidence. They exist to make the current training interaction measurable before persistence requirements are introduced.