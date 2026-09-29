#!/usr/bin/env python3
"""Validate project Requirement Contracts and enforce explicit contract-change declarations."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable


ALLOWED_STATUS = {"ACTIVE", "SUPERSEDED", "RETIRED"}
CONTRACT_CHANGE_RE = r"CONTRACT-CHANGE\s*:\s*([A-Z0-9._-]+)"


def load_registry(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON registry: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("registry schema_version must be 1")
    contracts = data.get("contracts")
    if not isinstance(contracts, list):
        raise ValueError("registry contracts must be a list")
    return data


def python_symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()

    def walk(nodes: Iterable[ast.AST], prefix: str = "") -> None:
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualified = f"{prefix}{node.name}"
                found.add(qualified)
                walk(node.body, f"{qualified}.")
            elif isinstance(node, ast.ClassDef):
                walk(node.body, f"{prefix}{node.name}.")
            elif isinstance(node, ast.If):
                walk(node.body, prefix)
                walk(node.orelse, prefix)

    walk(tree.body)
    return found


def validate_registry(project_root: Path, registry_path: Path, contract_doc: Path) -> list[str]:
    errors: list[str] = []
    data = load_registry(registry_path)
    contracts = data["contracts"]
    ids: set[str] = set()

    for contract in contracts:
        if not isinstance(contract, dict):
            errors.append("contract entries must be objects")
            continue

        cid = contract.get("id")
        status = contract.get("status")
        for field in (
            "id",
            "title",
            "requirement",
            "source",
            "protected_paths",
            "regression_tests",
            "change_policy",
        ):
            if not contract.get(field):
                errors.append(f"{cid or '<unknown>'}: missing required field {field}")

        if cid in ids:
            errors.append(f"duplicate contract id: {cid}")
        if cid:
            ids.add(cid)

        if status not in ALLOWED_STATUS:
            errors.append(f"{cid or '<unknown>'}: invalid status {status!r}")

        protected_paths = contract.get("protected_paths") or []
        if not isinstance(protected_paths, list):
            errors.append(f"{cid}: protected_paths must be a list")
        else:
            for rel in protected_paths:
                path = project_root / rel
                if not path.is_file():
                    errors.append(f"{cid}: protected path does not exist: {rel}")

        regressions = contract.get("regression_tests") or []
        if not isinstance(regressions, list):
            errors.append(f"{cid}: regression_tests must be a list")
        elif status == "ACTIVE":
            for spec in regressions:
                rel = spec.get("file") if isinstance(spec, dict) else None
                symbol = spec.get("symbol") if isinstance(spec, dict) else None
                if not rel or not symbol:
                    errors.append(f"{cid}: regression test entries require file + symbol")
                    continue
                test_path = project_root / rel
                if not test_path.is_file():
                    errors.append(f"{cid}: regression test file does not exist: {rel}")
                    continue
                try:
                    symbols = python_symbols(test_path)
                except (OSError, SyntaxError) as exc:
                    errors.append(f"{cid}: cannot parse regression test file {rel}: {exc}")
                    continue
                if symbol not in symbols and not any(
                    name.endswith("." + symbol) for name in symbols
                ):
                    errors.append(f"{cid}: regression test symbol not found: {rel}:{symbol}")

        if status == "ACTIVE" and contract.get("change_policy") != "INTENTIONAL_CHANGE_REQUIRES_REPORT":
            errors.append(f"{cid}: ACTIVE contracts must use INTENTIONAL_CHANGE_REQUIRES_REPORT")

    doc_text = contract_doc.read_text(encoding="utf-8") if contract_doc.is_file() else ""
    if not doc_text:
        errors.append(f"contract document does not exist: {contract_doc}")
    for contract in contracts:
        if contract.get("status") == "ACTIVE":
            cid = contract.get("id", "<unknown>")
            title = contract.get("title", "")
            if cid not in doc_text:
                errors.append(f"{cid}: not documented in {contract_doc.relative_to(project_root)}")
            if title and title not in doc_text:
                errors.append(f"{cid}: title not documented in {contract_doc.relative_to(project_root)}")

    return errors


def git_changed_files(base_ref: str | None) -> list[str]:
    if not base_ref:
        return []
    for base in (f"origin/{base_ref}", base_ref):
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    raise RuntimeError(f"could not resolve git diff base ref: {base_ref}")


def pull_request_body(event_path: str | None) -> str:
    if not event_path:
        return ""
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    return ((event.get("pull_request") or {}).get("body") or "")


def declared_contract_ids(text: str) -> set[str]:
    return {match.group(1) for match in re.finditer(CONTRACT_CHANGE_RE, text or "")}


def enforce_change_control(
    data: dict,
    event_name: str,
    base_ref: str | None,
    event_path: str | None,
) -> None:
    contracts = [c for c in data.get("contracts", []) if c.get("status") == "ACTIVE"]
    if not contracts:
        return

    changed = git_changed_files(base_ref)
    if not changed:
        return

    registry_rel = "docs/requirement_contracts.json"
    doc_rel = "docs/REQUIREMENT_CONTRACTS.md"
    test_to_contracts: dict[str, set[str]] = {}
    protected_to_contracts: dict[str, set[str]] = {}

    for contract in contracts:
        cid = contract["id"]
        for path in contract.get("protected_paths", []):
            protected_to_contracts.setdefault(path, set()).add(cid)
        for spec in contract.get("regression_tests", []):
            test_to_contracts.setdefault(spec["file"], set()).add(cid)

    affected: set[str] = set()
    weakened: set[str] = set()

    for path in changed:
        affected.update(protected_to_contracts.get(path, set()))
        weakened.update(test_to_contracts.get(path, set()))
        if path in {registry_rel, doc_rel}:
            weakened.update(c["id"] for c in contracts)

    if not affected and not weakened:
        return

    declared: set[str] = set()
    if event_name == "pull_request":
        declared = declared_contract_ids(pull_request_body(event_path))
    elif event_name == "push":
        result = subprocess.run(
            ["git", "rev-list", "--parents", "-n", "1", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
        parents = result.stdout.strip().split()
        if len(parents) <= 2:
            message = subprocess.run(
                ["git", "log", "-1", "--pretty=%B"],
                check=False,
                capture_output=True,
                text=True,
            )
            declared = declared_contract_ids(message.stdout)

    missing = sorted(weakened - declared)
    if missing:
        raise RuntimeError(
            "Requirement Contract change control failed for "
            + ", ".join(missing)
            + ". Add 'CONTRACT-CHANGE: <ID>' to the Pull Request description "
              "or direct-push commit message, and report the intentional behavior change "
              "before superseding the Contract."
        )

    for cid in sorted(affected):
        print(
            f"::warning::Protected Requirement Contract {cid} is in this change set. "
            "Preserve its user-visible behavior and keep its regression tests passing."
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
    )
    parser.add_argument("--contracts", default="docs/requirement_contracts.json", type=Path)
    parser.add_argument("--contract-doc", default="docs/REQUIREMENT_CONTRACTS.md", type=Path)
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    registry = (
        (project_root / args.contracts).resolve()
        if not args.contracts.is_absolute()
        else args.contracts.resolve()
    )
    contract_doc = (
        (project_root / args.contract_doc).resolve()
        if not args.contract_doc.is_absolute()
        else args.contract_doc.resolve()
    )

    try:
        registry_data = load_registry(registry)
        errors = validate_registry(project_root, registry, contract_doc)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1

        enforce_change_control(
            registry_data,
            os.environ.get("GITHUB_EVENT_NAME", ""),
            os.environ.get("GITHUB_BASE_REF") or None,
            os.environ.get("GITHUB_EVENT_PATH") or None,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("Requirement Contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
