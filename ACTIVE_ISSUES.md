# Active Issues

Updated: 2026-10-01

| ID | Status | Scope | Impact | Resolution boundary |
| --- | --- | --- | --- | --- |
| ISSUE-004 | PARTIAL / ENVIRONMENT | Render external HTTP/UI smoke verification | Render workspace access is restored and the current main deployment is confirmed "live", with normal build/start logs. External HTTP/UI verification remains unavailable because the connected web verifier rejects the service URL and this runtime cannot resolve the public Render hostname. | Use a browser or external network path that can reach https://personal-ai-janggi-trainer.onrender.com and verify the UI/game loop. No product-code workaround is appropriate. |
| ISSUE-005 | BLOCKED / ENVIRONMENT | Off-CI AI calibration | Provenance-aware 2-3 through 5-6 evidence still requires a fresh executable experiment. Historical run #46 provides 10 completed 2-3 games, but its artifact predates provenance-aware metadata. The gameplay-critical files search.py, tournament.py, and match.py are byte-identical between that run's source revision and current main; this makes the result useful historical evidence, but not current provenance-aware evidence. | Run tools/run_ai_level_calibration.py in an approved execution environment against current main and preserve the raw JSON + aggregate artifacts. Do not relabel legacy evidence as current. |
| ISSUE-006 | OPEN / CONFIG DRIFT | Render health-check configuration | Repository source of truth declares healthCheckPath: /api/health, and the application exposes that endpoint, but the connected Render service metadata currently reports an empty health-check path. Deployment is live, but the service-level health-check configuration is not aligned with the Blueprint. | Reconcile the existing Render service configuration with render.yaml using an authorized Render service/Blueprint configuration path. Do not change application health endpoint behavior to hide the infrastructure drift. |

## Closed / resolved reference

- GitHub Actions fast-validation execution issue (#85) is resolved; post-merge validation for commit 05ebd50 succeeded for Workspace structure validation and Janggi Python validation.
- PR #89 UI redesign is merged to main and is no longer an active implementation issue.
- Render workspace-selection issue from the previous verification session is resolved; the approved workspace is My Workspace.
- Historical calibration run #46 (workflow run 46, seed 20261002, pair 2-3) is retained as legacy/exploratory evidence only; it must not be aggregated into the current provenance-aware threshold.
