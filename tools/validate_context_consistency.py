from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
GOV = ROOT / "GOVERNANCE" / "GOVERNANCE.md"
STATUS = ROOT / "GOVERNANCE" / "docs" / "CURRENT_STATUS.md"
TASKS = ROOT / "GOVERNANCE" / "docs" / "DEVELOPMENT_TASKS.md"
ISSUES = ROOT / "GOVERNANCE" / "docs" / "ACTIVE_ISSUES.md"
PROJECT_STATUS = ROOT / "projects/personal-ai-janggi-trainer-by-gpt/docs/CURRENT_STATUS.md"
PROJECT_AGENTS = ROOT / "projects/personal-ai-janggi-trainer-by-gpt/AGENTS.md"
ROOT_ISSUES = ROOT / "ACTIVE_ISSUES.md"

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def version(text: str) -> str | None:
    for line in text.splitlines():
        normalized = line.strip()
        if "Governance Version:" in normalized:
            value = normalized.split("Governance Version:", 1)[1].strip()
            return value.strip("`* ") or None
    return None

def git_exists(sha: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", sha + "^{commit}"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode == 0

def active_task(text: str) -> tuple[str, str, str] | None:
    for line in text.splitlines():
        if not line.strip().startswith("| TASK-"):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) < 7 or parts[4] != "ACTIVE":
            continue
        return parts[0], parts[5], parts[6]
    return None


def main() -> int:
    errors: list[str] = []
    gv = version(read(GOV))
    pv = version(read(PROJECT_STATUS))
    if not gv or not pv or gv != pv:
        errors.append("workspace/project Governance Version mismatch")
    task = active_task(read(TASKS))
    if not task:
        errors.append("no parseable ACTIVE Task row")
    else:
        task_id, context, checkpoint = task
        context_path = ROOT / context.strip()
        checkpoint_path = ROOT / checkpoint.strip()
        if not context_path.exists():
            errors.append("ACTIVE Task context file missing: " + context.strip())
        if not checkpoint_path.exists():
            errors.append("ACTIVE Task checkpoint file missing: " + checkpoint.strip())
        else:
            checkpoint_text = read(checkpoint_path)
            if "- Task ID: " + task_id not in checkpoint_text:
                errors.append("checkpoint Task ID does not match Registry")
            branch = re.search(r"- Current Branch:\s*([^\n]+)", checkpoint_text)
            if not branch or branch.group(1).strip() != "main":
                errors.append("checkpoint Current Branch is not main")
            commit = re.search(r"- Current Commit:\s*([0-9a-f]{40})\b", checkpoint_text)
            if not commit or not git_exists(commit.group(1)):
                errors.append("checkpoint Current Commit is missing or absent from git")
    root_issues = read(ROOT_ISSUES)
    if "GOVERNANCE/docs/ACTIVE_ISSUES.md" not in root_issues:
        errors.append("root ACTIVE_ISSUES.md does not point to authoritative index")
    if "## Active Issue Register" in root_issues or "| ISSUE-" in root_issues:
        errors.append("root ACTIVE_ISSUES.md duplicates authoritative issue registry")
    if "## Active Issue Register" not in read(ISSUES):
        errors.append("authoritative ACTIVE_ISSUES.md register missing")
    for path in (STATUS, PROJECT_STATUS):
        text = read(path)
        for pattern in (r"Latest .* validation:.*run\s*#\d+", r"Current live deployment commit:\s*`?[0-9a-f]{40}", r"Latest live deploy:\s*`?[0-9a-f]{40}"):
            if re.search(pattern, text, re.IGNORECASE):
                errors.append(str(path.relative_to(ROOT)) + " contains mutable CI/deployment telemetry")
    if "CURRENT_STATUS" not in read(PROJECT_AGENTS):
        errors.append("project AGENTS.md does not document the CURRENT_STATUS boundary")
    if errors:
        print("Context consistency validation failed:")
        for error in errors:
            print("- " + error)
        return 1
    print("Context consistency validation passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
