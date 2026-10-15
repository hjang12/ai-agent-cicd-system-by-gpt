from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PAIR_IDS = ("1-2", "2-3", "3-4", "4-5", "5-6")
SETUPS = ("classic", "left", "right", "both")
FIXTURE_MODES = ("initial", "capture", "check", "endgame", "tactical")
CALIBRATION_PROTOCOL_VERSION = "2"


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


def _artifact_path(
    output_dir: Path,
    pair: str,
    seed: int,
    setup: str,
    fixture_mode: str = "tactical",
) -> Path:
    return output_dir / (
        f"ai-level-strength-{pair}-seed-{seed}-{setup}"
        f"-v{CALIBRATION_PROTOCOL_VERSION}-{fixture_mode}.json"
    )


def _run(
    command: list[str],
    *,
    cwd: Path,
) -> None:
    print("$", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def _validate_artifact_identity(
    artifact: Path,
    *,
    pair: str,
    seed: int,
    setup: str,
    fixture_mode: str = "tactical",
    source_revision: str | None = None,
) -> None:
    try:
        payload = json.loads(artifact.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{artifact}: existing artifact is not valid JSON") from exc

    experiment = payload.get("experiment")
    if not isinstance(experiment, dict):
        raise ValueError(f"{artifact}: existing artifact has no experiment metadata")

    expected = {
        "pair": pair,
        "seed": seed,
        "setup": setup,
        "fixture": fixture_mode,
        "calibration_protocol_version": CALIBRATION_PROTOCOL_VERSION,
    }
    if source_revision:
        expected["source_revision"] = source_revision
    actual = {key: experiment.get(key) for key in expected}
    if actual != expected:
        raise ValueError(
            f"{artifact}: experiment identity mismatch: "
            f"expected={expected}, actual={actual}"
        )


def _run_experiment(
    *,
    project_root: Path,
    artifact: Path,
    pair: str,
    seed: int,
    setup: str,
    games: int,
    max_plies: int,
    fixture_mode: str = "tactical",
    source_revision: str | None = None,
) -> None:
    if artifact.exists():
        _validate_artifact_identity(
            artifact,
            pair=pair,
            seed=seed,
            setup=setup,
            fixture_mode=fixture_mode,
            source_revision=source_revision,
        )
        print(f"SKIP existing artifact: {artifact}")
        return

    command = [
        sys.executable,
        "-m",
        "tools.benchmark_ai_levels",
        "--tournament-games",
        str(games),
        "--max-plies",
        str(max_plies),
        "--pair",
        pair,
        "--seed",
        str(seed),
        "--setup",
        setup,
        "--fixture",
        fixture_mode,
        "--skip-search-benchmark",
        "--output",
        str(artifact),
    ]
    if source_revision:
        command.extend(["--source-revision", source_revision])
    _run(command, cwd=project_root)

    if not artifact.exists():
        raise RuntimeError(
            f"Calibration command completed without producing expected artifact: {artifact}"
        )

    _validate_artifact_identity(
        artifact,
        pair=pair,
        seed=seed,
        setup=setup,
        fixture_mode=fixture_mode,
        source_revision=source_revision,
    )

def _resolve_source_revision(explicit_revision: str | None = None) -> str | None:
    revision = (explicit_revision or os.environ.get("CALIBRATION_SOURCE_REVISION") or "").strip()
    if revision:
        return revision
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or None


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
        "--fixture",
        choices=FIXTURE_MODES,
        default="tactical",
        help="Protocol-v2 fixture mode; tactical cycles capture/check/endgame positions.",
    )
    parser.add_argument(
        "--source-revision",
        default=None,
        help="Explicit code/configuration revision being evaluated.",
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
    if args.fixture != "initial" and args.setup != "classic":
        parser.error("non-initial fixtures require --setup classic")

    project_root = Path(__file__).resolve().parents[1]
    output_dir = (project_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    completed_artifacts: list[Path] = []
    failures: list[dict[str, object]] = []

    for pair in pairs:
        for seed in seeds:
            artifact = _artifact_path(output_dir, pair, seed, args.setup, args.fixture)
            experiment_succeeded = False
            try:
                _run_experiment(
                    project_root=project_root,
                    artifact=artifact,
                    pair=pair,
                    seed=seed,
                    setup=args.setup,
                    games=args.games,
                    max_plies=args.max_plies,
                    fixture_mode=args.fixture,
                    source_revision=args.source_revision,
                )
                experiment_succeeded = True
            except (subprocess.CalledProcessError, ValueError, RuntimeError) as exc:
                failure = {
                    "pair": pair,
                    "seed": seed,
                    "setup": args.setup,
                    "fixture": args.fixture,
                    "calibration_protocol_version": CALIBRATION_PROTOCOL_VERSION,
                    "returncode": (
                        exc.returncode
                        if isinstance(exc, subprocess.CalledProcessError)
                        else 1
                    ),
                    "artifact": str(artifact),
                    "error": str(exc),
                }
                failures.append(failure)
                if not args.keep_going:
                    raise
            if experiment_succeeded and artifact.exists():
                completed_artifacts.append(artifact)

    aggregate_reports: dict[str, str] = {}
    for pair in pairs:
        pair_artifacts = [
            _artifact_path(output_dir, pair, seed, args.setup, args.fixture)
            for seed in seeds
            if _artifact_path(output_dir, pair, seed, args.setup, args.fixture).exists()
        ]
        if not pair_artifacts:
            continue

        aggregate = output_dir / f"aggregate-{pair}-{args.setup}-v{CALIBRATION_PROTOCOL_VERSION}-{args.fixture}.json"
        command = [
            sys.executable,
            "-m",
            "tools.evaluate_ai_level_evidence",
            *(str(path) for path in pair_artifacts),
            "--output",
            str(aggregate),
        ]
        _run(command, cwd=project_root)
        aggregate_reports[f"{pair}:{args.fixture}"] = str(aggregate)

    manifest = {
        "method": "off-CI resumable adjacent-level calibration runner",
        "pairs": pairs,
        "seeds": seeds,
        "setup": args.setup,
        "fixture": args.fixture,
        "calibration_protocol_version": CALIBRATION_PROTOCOL_VERSION,
        "source_revision": _resolve_source_revision(args.source_revision),
        "games_per_experiment": args.games,
        "max_plies": args.max_plies,
        "artifacts": [str(path) for path in completed_artifacts],
        "aggregate_reports": aggregate_reports,
        "failures": failures,
        "resume_rule": (
            "Existing raw evidence artifacts are reused and never overwritten. "
            "Each protocol-v2 experiment is uniquely identified by pair, seed, setup, protocol, and fixture mode."
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
