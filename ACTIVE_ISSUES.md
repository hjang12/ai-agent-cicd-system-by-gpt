# Active Issues

Updated: 2026-10-01

| ID | Status | Scope | Impact | Resolution boundary |
| --- | --- | --- | --- | --- |
| ISSUE-004 | BLOCKED / ENVIRONMENT | Render live verification | Current-commit production health/UI smoke test cannot be confirmed through the connected Render tool session because no Render workspace is selected; the available web verifier also cannot fetch the service URL. | Select the correct Render workspace in a future session or provide another read-only deployment/health verification path. No product-code workaround is appropriate. |
| ISSUE-005 | BLOCKED / ENVIRONMENT | Off-CI AI calibration | Provenance-aware 2-3 through 5-6 evidence requires actual self-play execution. The repository runner exists, but this runtime cannot execute the private monorepo outside GitHub Actions. | Run `tools/run_ai_level_calibration.py` in an approved off-CI execution environment and preserve the raw JSON + aggregate artifacts. Do not substitute CI smoke tests or old legacy evidence. |

## Closed / resolved reference

- GitHub Actions fast-validation execution issue (#85) is resolved; current post-merge validation run #358 passed compile, Requirement Contract validation, and 303 unit tests.
- PR #89 UI redesign is merged to `main` and is no longer an active implementation issue.