from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = (
    Path("AGENT_START.md"),
    Path("AGENTS.md"),
    Path("GOVERNANCE/GOVERNANCE.md"),
    Path("GOVERNANCE/docs/CURRENT_STATUS.md"),
    Path("GOVERNANCE/docs/DEVELOPMENT_HISTORY.md"),
    Path("GOVERNANCE/docs/ADR/0002-ai-workspace-monorepo.md"),
    Path("projects/personal-ai-janggi-trainer-by-gpt/AGENT_START.md"),
    Path("projects/personal-ai-janggi-trainer-by-gpt/AGENTS.md"),
    Path("projects/personal-ai-janggi-trainer-by-gpt/docs/CURRENT_STATUS.md"),
    Path("projects/time-dashboard-by-gpt/AGENT_START.md"),
    Path("projects/time-dashboard-by-gpt/AGENTS.md"),
    Path("projects/time-dashboard-by-gpt/docs/CURRENT_STATUS.md"),
    Path("projects/personal-ai-janggi-trainer-by-gpt/app.py"),
    Path("projects/time-dashboard-by-gpt/timefolio_server.py"),
    Path(".github/workflows/janggi-validation.yml"),
    Path(".github/workflows/janggi-search-benchmark.yml"),
    Path(".github/workflows/time-dashboard-ci.yml"),
    Path("render.yaml"),
)


REQUIRED_RENDER_SERVICES = {
    "personal-ai-janggi-trainer-by-gpt": {
        "rootDir": "projects/personal-ai-janggi-trainer-by-gpt",
        "healthCheckPath": "/api/health",
    },
    "time-dashboard-by-gpt": {
        "rootDir": "projects/time-dashboard-by-gpt",
        "healthCheckPath": "/api/health",
    },
}


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
            if f"{key}: {value}" not in block:
                errors.append(
                    f"render.yaml service {service_name} missing {key}: {value}"
                )

    return errors


def validate_project_boundaries() -> list[str]:
    errors = []
    for project in (
        "personal-ai-janggi-trainer-by-gpt",
        "time-dashboard-by-gpt",
    ):
        project_root = ROOT / "projects" / project
        if not project_root.is_dir():
            continue
        for child in project_root.iterdir():
            if child.name.startswith(".git"):
                errors.append(f"nested Git metadata is not allowed: {child}")
    return errors


def main() -> int:
    errors = validate_paths()
    errors.extend(validate_render_blueprint())
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
