from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PAIR_IDS = ("1-2", "2-3", "3-4", "4-5", "5-6")
SETUPS = ("classic", "left", "right", "both")


def _parse_csv(value: str, *, allowed: tuple[str, ...]) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    invalid = [item for item in items if item not in allowed]
    if invalid:
        raise ValueError(f"unsupported value(s): {', '.join(invalid)}")
    if not items:
        raise ValueError("at least one value is required")
    return items


def _parse_seeds(value: str) -> list[int]:
    try:
        seeds = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise ValueError("seeds must be comma-separated integers") from exc
    if not seeds:
        raise ValueError("at least one seed is required")
    if len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be unique")
    return seeds


def _artifact_path(output_dir: Path, pair: str, seed: int, setup: str) -> Path:
    return output_dir / f"ai-level-strength-{pair}-seed-{seed}-{setup}.json"


def _run(
    command: list[str],
    *,
    cwd: Path,
) -> None:
    print("$", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run resumable off-CI adjacent-level calibration experiments."
    )
    parser.add_argument(
        "--pair",
        default="2-3",
        help="Comma-separated adjacent pairs to run.",
    )
    parser.add_argument(
        "--seed",
        default="20261002,20261003",
        help="Comma-separated unique integer seeds.",
    )
    parser.add_argument(
        "--setup",
        choices=SETUPS,
        default="classic",
        help="Starting arrangement used for every calibration game.",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=12,
        help="Games per pair/seed experiment.",
    )
    parser.add_argument(
        "--max-plies",
        type=int,
        default=96,
        help="Maximum plies per game.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/ai-level-calibration"),
        help="Directory for raw evidence artifacts and aggregate reports.",
    )
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue to the next experiment after a failed subprocess.",
    )
    args = parser.parse_args()

    try:
        pairs = _parse_csv(args.pair, allowed=PAIR_IDS)
        seeds = _parse_seeds(args.seed)
    except ValueError as exc:
        parser.error(str(exc))

    if args.games < 2 or args.games % 2:
        parser.error("--games must be an even integer of at least 2")
    if args.max_plies < 1:
        parser.error("--max-plies must be at least 1")

    project_root = Path(__file__).resolve().parents[1]
    output_dir = (project_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    completed_artifacts: list[Path] = []
    failures: list[dict[str, object]] = []

    for pair in pairs:
        for seed in seeds:
            artifact = _artifact_path(output_dir, pair, seed, args.setup)
            if artifact.exists():
                print(f"SKIP existing artifact: {artifact}")
            else:
                command = [
                    sys.executable,
                    "tools/benchmark_ai_levels.py",
                    "--tournament-games",
                    str(args.games),
                    "--max-plies",
                    str(args.max_plies),
                    "--pair",
                    pair,
                    "--seed",
                    str(seed),
                    "--setup",
                    args.setup,
                    "--skip-search-benchmark",
                    "--output",
                    str(artifact),
                ]
                try:
                    _run(command, cwd=project_root)
                except subprocess.CalledProcessError as exc:
                    failure = {
                        "pair": pair,
                        "seed": seed,
                        "setup": args.setup,
                        "returncode": exc.returncode,
                        "artifact": str(artifact),
                    }
                    failures.append(failure)
                    if not args.keep_going:
                        raise
            if artifact.exists():
                completed_artifacts.append(artifact)

    aggregate_reports: dict[str, str] = {}
    for pair in pairs:
        pair_artifacts = [
            path
            for path in completed_artifacts
            if f"ai-level-strength-{pair}-" in path.name
        ]
        if not pair_artifacts:
            continue

        aggregate = output_dir / f"aggregate-{pair}-{args.setup}.json"
        command = [
            sys.executable,
            "tools/evaluate_ai_level_evidence.py",
            *(str(path) for path in pair_artifacts),
            "--output",
            str(aggregate),
        ]
        _run(command, cwd=project_root)
        aggregate_reports[pair] = str(aggregate)

    manifest = {
        "method": "off-CI resumable adjacent-level calibration runner",
        "pairs": pairs,
        "seeds": seeds,
        "setup": args.setup,
        "games_per_experiment": args.games,
        "max_plies": args.max_plies,
        "artifacts": [str(path) for path in completed_artifacts],
        "aggregate_reports": aggregate_reports,
        "failures": failures,
        "resume_rule": (
            "Existing raw evidence artifacts are reused and never overwritten. "
            "Each experiment remains uniquely identified by pair, seed, and setup."
        ),
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Manifest: {manifest_path}")

    if failures:
        print(f"Completed with {len(failures)} failed experiment(s).")
        return 1

    print("All requested calibration experiments completed or were already present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
