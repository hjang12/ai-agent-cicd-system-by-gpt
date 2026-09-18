# Current Status

## Governance

- Common Governance Repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Governance Version: `1.0.0`
- Governance status: active baseline on `main`
- Project context entrypoint: `AGENT_START.md`

## Product

- Project: Time Dashboard
- Canonical Repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Project Path: `projects/time-dashboard-by-gpt/`
- Default branch: `main`
- Current runtime: Python
- Production service: Render Web Service `time-dashboard-by-gpt`
- Current operating model: personal web dashboard / PWA-style browser experience

## Project Structure

- `timefolio_server.py` — primary HTTP server and backend/data handling
- `timefolio_dashboard.html` — dashboard UI
- `install.html` — installation / PWA-oriented landing page
- `manifest.json` — web app manifest
- `assets/` — web assets
- `tests/` — backend regression tests

## CI/CD

GitHub Actions workflow: `../../.github/workflows/time-dashboard-ci.yml` (repository-root path `.github/workflows/time-dashboard-ci.yml`)

- Trigger: push to `main` and pull requests
- Python: `3.12`
- Compile: `python -m py_compile timefolio_server.py`
- Test: `python -m unittest discover -s tests -p 'test_*.py'`

Render target Blueprint:

- Root Blueprint: `../../render.yaml`
- Service name: `time-dashboard-by-gpt`
- Desired Repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Desired Root Directory: `projects/time-dashboard-by-gpt`
- Branch: `main`
- Region: Oregon
- Build: `pip install -r requirements.txt`
- Start: `python timefolio_server.py`

Verified live Render state on 2026-09-18:
- Service: `time-dashboard-by-gpt`
- Repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Root Directory: `projects/time-dashboard-by-gpt`
- Branch: `main`
- Auto Deploy: enabled
- Latest live deployment commit: `51fc3322121167f1c48eb339bbe91bf69858c551`
- Deployment: `dep-damckue7bikc73b4p7ng`
- Deployment status: `live`
- Build: succeeded (`pip install -r requirements.txt`)
- Start: `python timefolio_server.py`
- Smoke: Render logs show `HEAD /` and `GET /` returning HTTP 200
- URL: `https://time-dashboard.onrender.com`

The service is now running from the canonical monorepo. Render `healthCheckPath` remains empty; root endpoint smoke verification is available from Render request logs.

## Monorepo Operation

This project is developed under the canonical workspace repository `hjang12/ai-agent-cicd-system-by-gpt`. The sibling project boundaries are maintained by project-local paths and root-level CI path filters.

## Development Rules

- `timefolio_server.py` is the primary backend reference.
- Changes to external TimeETF data parsing must keep parser tests aligned.
- Keep web UI concerns separate from data collection/parsing logic.
- Prefer minimal changes and review the need/license implications of new dependencies.
- Preserve the current Render `main` auto-deploy setup unless there is a deliberate operational change.

## Explicitly Deferred / Not Yet Established

- Separate database persistence
- Authentication / multi-user functionality
- Production-grade observability and rate limiting
- Additional automated browser/end-to-end coverage
- Agentic execution inside GitHub Actions

## Known Next Targets

1. Verify and strengthen the backend parser/data handling behavior with regression coverage.
2. Improve dashboard reliability without unnecessarily coupling UI and backend data logic.
3. Add higher-value automated smoke or browser checks when the product justifies them.
4. Keep deployment and Context documentation synchronized with actual GitHub/Render state.
