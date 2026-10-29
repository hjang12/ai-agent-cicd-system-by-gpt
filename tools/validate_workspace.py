from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = (
    Path("AGENT_START.md"),
    Path("AGENTS.md"),
    Path("GOVERNANCE/GOVERNANCE.md"),
    Path("GOVERNANCE/VERSION"),
    Path("GOVERNANCE/CHANGELOG.md"),
    Path("GOVERNANCE/docs/CURRENT_STATUS.md"),
    Path("GOVERNANCE/docs/DEVELOPMENT_TASKS.md"),
    Path("GOVERNANCE/docs/DEVELOPMENT_HISTORY.md"),
    Path("GOVERNANCE/docs/ADR/0002-ai-workspace-monorepo.md"),
    Path("projects/personal-ai-janggi-trainer-by-gpt/AGENT_START.md"),
    Path("projects/personal-ai-janggi-trainer-by-gpt/AGENTS.md"),
    Path("projects/personal-ai-janggi-trainer-by-gpt/docs/CURRENT_STATUS.md"),
    Path("projects/time-dashboard-by-gpt/AGENT_START.md"),
    Path("projects/time-dashboard-by-gpt/AGENTS.md"),
    Path("projects/time-dashboard-by-gpt/docs/CURRENT_STATUS.md"),
    Path("projects/soldier-gate-runner-by-gpt/AGENT_START.md"),
    Path("projects/soldier-gate-runner-by-gpt/AGENTS.md"),
    Path("projects/soldier-gate-runner-by-gpt/docs/CURRENT_STATUS.md"),
    Path("projects/soldier-gate-runner-by-gpt/docs/checkpoints/TASK-20261023-0003.md"),
    Path("projects/soldier-gate-runner-by-gpt/index.html"),
    Path("projects/soldier-gate-runner-by-gpt/styles.css"),
    Path("projects/soldier-gate-runner-by-gpt/game.js"),
    Path("projects/soldier-gate-runner-by-gpt/tests/browser_acceptance.py"),
    Path(".github/workflows/soldier-gate-game-ci.yml"),
    Path("projects/personal-ai-janggi-trainer-by-gpt/app.py"),
    Path("projects/time-dashboard-by-gpt/timefolio_server.py"),
    Path(".github/workflows/janggi-validation.yml"),
    Path(".github/workflows/janggi-search-benchmark.yml"),
    Path(".github/workflows/janggi-browser-acceptance.yml"),
    Path(".github/workflows/time-dashboard-ci.yml"),
    Path(".github/workflows/workspace-validation.yml"),
    Path("render.yaml"),
)


REQUIRED_RENDER_SERVICES = {
    "personal-ai-janggi-trainer-by-gpt": {
        "rootDir": "projects/personal-ai-janggi-trainer-by-gpt",
        "autoDeployTrigger": "checksPass",
        "healthCheckPath": "/api/health",
        "buildCommand": "python -m compileall janggi tests",
        "startCommand": "python app.py",
        "buildFilterPath": "projects/personal-ai-janggi-trainer-by-gpt/**",
    },
    "time-dashboard-by-gpt": {
        "rootDir": "projects/time-dashboard-by-gpt",
        "autoDeployTrigger": "checksPass",
        "healthCheckPath": "/api/health",
        "buildCommand": "pip install -r requirements.txt",
        "startCommand": "python timefolio_server.py",
        "buildFilterPath": "projects/time-dashboard-by-gpt/**",
    },
    "soldier-gate-runner-by-gpt": {
        "runtime": "static",
        "autoDeployTrigger": "checksPass",
        "buildCommand": 'echo "No build step required"',
        "staticPublishPath": "projects/soldier-gate-runner-by-gpt",
        "buildFilterPath": "projects/soldier-gate-runner-by-gpt/**",
    },
}


GAME_CI_DOC_EXCLUSIONS = (
    "projects/soldier-gate-runner-by-gpt/AGENT_START.md",
    "projects/soldier-gate-runner-by-gpt/AGENTS.md",
    "projects/soldier-gate-runner-by-gpt/README.md",
    "projects/soldier-gate-runner-by-gpt/docs/**",
)


def validate_game_ci_doc_exclusions(workflow_text: str) -> list[str]:
    """Prevent documentation-only Gatefront changes from running the full browser suite."""
    errors = []
    for path in GAME_CI_DOC_EXCLUSIONS:
        marker = f"      - '!{path}'"
        if workflow_text.count(marker) < 2:
            errors.append(
                f"Gatefront Game CI must exclude {path} from both pull_request and push path filters"
            )
    return errors


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"workspace validation: cannot read {path}: {exc}") from exc


def validate_paths() -> list[str]:
    errors = []
    for relative in REQUIRED_PATHS:
        path = ROOT / relative
        if not path.exists():
            errors.append(f"missing required path: {relative}")
    return errors


def validate_render_blueprint() -> list[str]:
    text = read_text(ROOT / "render.yaml")
    errors = []
    for service_name, expected in REQUIRED_RENDER_SERVICES.items():
        marker = f"name: {service_name}"
        start = text.find(marker)
        if start < 0:
            errors.append(f"render.yaml missing service: {service_name}")
            continue

        next_service = text.find("\n  - type:", start + len(marker))
        block = text[start:next_service if next_service >= 0 else len(text)]

        for key, value in expected.items():
            if key == "buildFilterPath":
                if f"- {value}" not in block:
                    errors.append(
                        f"render.yaml service {service_name} missing buildFilter path: {value}"
                    )
                continue
            if f"{key}: {value}" not in block:
                errors.append(
                    f"render.yaml service {service_name} missing {key}: {value}"
                )

    return errors


def validate_governance_version_values(
    version: str,
    governance_text: str,
    changelog_text: str,
    current_status_text: str,
) -> list[str]:
    """Ensure current-facing Governance version references match the canonical version."""
    errors = []
    version = version.strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        return [f"GOVERNANCE/VERSION must contain a semantic version (X.Y.Z), got: {version!r}"]

    header_match = re.search(
        r"^\*\*Governance Version:\s*(\d+\.\d+\.\d+)\*\*\s*$",
        governance_text,
        re.MULTILINE,
    )
    if not header_match:
        errors.append("GOVERNANCE/GOVERNANCE.md is missing its Governance Version header")
    elif header_match.group(1) != version:
        errors.append(
            f"GOVERNANCE/GOVERNANCE.md version {header_match.group(1)} "
            f"does not match GOVERNANCE/VERSION {version}"
        )

    changelog_match = re.search(
        r"^## \[(\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}\s*$",
        changelog_text,
        re.MULTILINE,
    )
    if not changelog_match:
        errors.append("GOVERNANCE/CHANGELOG.md is missing a dated release header")
    elif changelog_match.group(1) != version:
        errors.append(
            f"GOVERNANCE/CHANGELOG.md latest version {changelog_match.group(1)} "
            f"does not match GOVERNANCE/VERSION {version}"
        )

    status_match = re.search(
        r"^- Governance (\d+\.\d+\.\d+) is active on `main`",
        current_status_text,
        re.MULTILINE,
    )
    if not status_match:
        errors.append(
            "GOVERNANCE/docs/CURRENT_STATUS.md must identify the active Governance version on main"
        )
    elif status_match.group(1) != version:
        errors.append(
            f"GOVERNANCE/docs/CURRENT_STATUS.md active version {status_match.group(1)} "
            f"does not match GOVERNANCE/VERSION {version}"
        )

    return errors



def validate_completed_task_verification(registry_text: str) -> list[str]:
    """Reject completed Task rows that label a required check UNVERIFIED."""
    errors = []
    header = None
    for line in registry_text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if "Task ID" in cells and "Status" in cells and "State Summary" in cells:
            header = {name: index for index, name in enumerate(cells)}
            continue
        if header is None or len(cells) <= max(header.values()):
            continue
        task_id = cells[header["Task ID"]]
        status = cells[header["Status"]]
        summary = cells[header["State Summary"]]
        if status == "COMPLETED" and re.search(
            r"\b(?:required|mandatory)\b[^.;|]{0,120}\bUNVERIFIED\b"
            r"|\bUNVERIFIED\b[^.;|]{0,120}\b(?:required|mandatory)\b",
            summary,
            re.IGNORECASE,
        ):
            errors.append(
                f"{task_id} is COMPLETED but its State Summary records UNVERIFIED verification"
            )
    return errors


def validate_governance_version() -> list[str]:
    return validate_governance_version_values(
        read_text(ROOT / "GOVERNANCE/VERSION"),
        read_text(ROOT / "GOVERNANCE/GOVERNANCE.md"),
        read_text(ROOT / "GOVERNANCE/CHANGELOG.md"),
        read_text(ROOT / "GOVERNANCE/docs/CURRENT_STATUS.md"),
    )


def validate_project_boundaries() -> list[str]:
    errors = []
    for project in (
        "personal-ai-janggi-trainer-by-gpt",
        "time-dashboard-by-gpt",
        "soldier-gate-runner-by-gpt",
    ):
        project_root = ROOT / "projects" / project
        if not project_root.is_dir():
            continue
        for child in project_root.iterdir():
            if child.is_dir() and child.name == ".git":
                errors.append(f"nested Git metadata is not allowed: {child}")
    return errors


def validate_ci_gate_workflows() -> list[str]:
    errors = []
    for relative in (
        Path('.github/workflows/janggi-validation.yml'),
        Path('.github/workflows/time-dashboard-ci.yml'),
        Path('.github/workflows/janggi-browser-acceptance.yml'),
        Path('.github/workflows/soldier-gate-game-ci.yml'),
    ):
        workflow = read_text(ROOT / relative)
        if workflow.count("      - 'render.yaml'") < 2:
            errors.append(f"{relative} must run for both push and pull_request changes to render.yaml")

    browser = read_text(ROOT / '.github/workflows/janggi-browser-acceptance.yml')
    if "if: github.event_name == 'pull_request' || github.event_name == 'push'" not in browser:
        errors.append('Janggi browser-acceptance must run local browser tests for pull_request and push events')
    if "if: github.event_name == 'workflow_dispatch'" not in browser:
        errors.append('Janggi live-browser-smoke must be workflow_dispatch-only to avoid a CI/deploy cycle')
    return errors

def main() -> int:
    errors = validate_paths()
    errors.extend(validate_render_blueprint())
    errors.extend(validate_governance_version())
    errors.extend(validate_completed_task_verification(read_text(ROOT / "GOVERNANCE/docs/DEVELOPMENT_TASKS.md")))
    errors.extend(validate_ci_gate_workflows())
    errors.extend(validate_game_ci_doc_exclusions(read_text(ROOT / '.github/workflows/soldier-gate-game-ci.yml')))
    errors.extend(validate_project_boundaries())

    if errors:
        print("Workspace validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Workspace validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
