from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

PAIR_IDS = ("1-2", "2-3", "3-4", "4-5", "5-6")


def _pair_id(pair: dict[str, object]) -> str:
    return f"{pair['lower_level']}-{pair['higher_level']}"


def _load(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: evidence root must be an object")
    return payload


def _validate_game_results(path: Path, pair: dict[str, object]) -> tuple[int, int, int, int]:
    results = pair.get("game_results")
    if not isinstance(results, list):
        raise ValueError(f"{path}: pair {_pair_id(pair)} has no game_results list")

    completed = lower_wins = higher_wins = unfinished = 0

    for game in results:
        if not isinstance(game, dict):
            raise ValueError(f"{path}: malformed game result in pair {_pair_id(pair)}")
        status = game.get("status")
        outcome = game.get("outcome_for_lower")

        if status == "playing":
            unfinished += 1
            if outcome is not None:
                raise ValueError(
                    f"{path}: unfinished game in pair {_pair_id(pair)} has an outcome"
                )
            continue

        if outcome not in (-1, 0, 1):
            raise ValueError(
                f"{path}: invalid completed outcome {outcome!r} in pair {_pair_id(pair)}"
            )

        completed += 1
        if outcome == 1:
            lower_wins += 1
        elif outcome == -1:
            higher_wins += 1

    expected_completed = pair.get("completed")
    expected_unfinished = pair.get("unfinished")
    expected_games = pair.get("games")
    expected_lower_wins = pair.get("lower_wins")
    expected_higher_wins = pair.get("higher_wins")
    expected_draws = pair.get("draws")

    if expected_games != len(results):
        raise ValueError(
            f"{path}: pair {_pair_id(pair)} games mismatch: "
            f"summary={expected_games}, games={len(results)}"
        )
    if expected_completed != completed:
        raise ValueError(
            f"{path}: pair {_pair_id(pair)} completed mismatch: "
            f"summary={expected_completed}, games={completed}"
        )
    if expected_unfinished != unfinished:
        raise ValueError(
            f"{path}: pair {_pair_id(pair)} unfinished mismatch: "
            f"summary={expected_unfinished}, games={unfinished}"
        )
    if expected_lower_wins != lower_wins:
        raise ValueError(
            f"{path}: pair {_pair_id(pair)} lower_wins mismatch: "
            f"summary={expected_lower_wins}, games={lower_wins}"
        )
    if expected_higher_wins != higher_wins:
        raise ValueError(
            f"{path}: pair {_pair_id(pair)} higher_wins mismatch: "
            f"summary={expected_higher_wins}, games={higher_wins}"
        )
    actual_draws = completed - lower_wins - higher_wins
    if expected_draws != actual_draws:
        raise ValueError(
            f"{path}: pair {_pair_id(pair)} draws mismatch: "
            f"summary={expected_draws}, games={actual_draws}"
        )

    return completed, unfinished, lower_wins, higher_wins


def aggregate_evidence(
    paths: Iterable[Path],
    *,
    min_completed: int = 20,
    max_unfinished_rate: float = 0.25,
    min_unique_seeds: int = 2,
) -> dict[str, object]:
    if min_completed < 1:
        raise ValueError("min_completed must be at least 1")
    if not 0 <= max_unfinished_rate < 1:
        raise ValueError("max_unfinished_rate must be in [0, 1)")
    if min_unique_seeds < 1:
        raise ValueError("min_unique_seeds must be at least 1")

    seen_experiments: set[tuple[str, int, str]] = set()
    pair_buckets: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "experiments": 0,
            "games": 0,
            "completed": 0,
            "unfinished": 0,
            "lower_wins": 0,
            "higher_wins": 0,
            "draws": 0,
            "lower_score": 0.0,
            "seeds": set(),
            "setups": set(),
            "config_fingerprints": set(),
            "engine_versions": set(),
            "source_revisions": set(),
        }
    )

    for path in paths:
        payload = _load(path)
        experiment = payload.get("experiment")
        pairs = payload.get("pairs")
        if not isinstance(experiment, dict) or not isinstance(pairs, list):
            raise ValueError(f"{path}: invalid evidence structure")

        pair_id = experiment.get("pair")
        seed = experiment.get("seed")
        setup = experiment.get("setup")
        if pair_id not in PAIR_IDS:
            raise ValueError(f"{path}: invalid pair {pair_id!r}")
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise ValueError(f"{path}: seed must be an integer")
        if not isinstance(setup, str) or not setup:
            raise ValueError(f"{path}: setup must be a non-empty string")

        config_fingerprint = experiment.get("ai_level_config_fingerprint")
        engine_version = experiment.get("engine_version")
        source_revision = experiment.get("source_revision")
        for field_name, value in (
            ("ai_level_config_fingerprint", config_fingerprint),
            ("engine_version", engine_version),
            ("source_revision", source_revision),
        ):
            if value is not None and not isinstance(value, str):
                raise ValueError(f"{path}: {field_name} must be a string when present")
        identity = (pair_id, seed, setup)
        if identity in seen_experiments:
            raise ValueError(
                f"duplicate experiment identity: pair={pair_id}, seed={seed}, setup={setup}"
            )
        seen_experiments.add(identity)

        matching = [
            item for item in pairs
            if isinstance(item, dict) and _pair_id(item) == pair_id
        ]
        if len(matching) != 1:
            raise ValueError(
                f"{path}: expected exactly one pair row for {pair_id}, found {len(matching)}"
            )

        pair = matching[0]
        completed, unfinished, lower_wins, higher_wins = _validate_game_results(path, pair)
        draws = completed - lower_wins - higher_wins
        lower_score = lower_wins + draws * 0.5

        bucket = pair_buckets[pair_id]
        bucket["experiments"] = int(bucket["experiments"]) + 1
        bucket["games"] = int(bucket["games"]) + len(pair["game_results"])
        bucket["completed"] = int(bucket["completed"]) + completed
        bucket["unfinished"] = int(bucket["unfinished"]) + unfinished
        bucket["lower_wins"] = int(bucket["lower_wins"]) + lower_wins
        bucket["higher_wins"] = int(bucket["higher_wins"]) + higher_wins
        bucket["draws"] = int(bucket["draws"]) + draws
        bucket["lower_score"] = float(bucket["lower_score"]) + lower_score
        if config_fingerprint is not None:
            cast_fingerprints = bucket["config_fingerprints"]
            assert isinstance(cast_fingerprints, set)
            cast_fingerprints.add(config_fingerprint)
        if engine_version is not None:
            cast_engine_versions = bucket["engine_versions"]
            assert isinstance(cast_engine_versions, set)
            cast_engine_versions.add(engine_version)
        if source_revision is not None:
            cast_revisions = bucket["source_revisions"]
            assert isinstance(cast_revisions, set)
            cast_revisions.add(source_revision)
        cast_seeds = bucket["seeds"]
        cast_setups = bucket["setups"]
        assert isinstance(cast_seeds, set)
        assert isinstance(cast_setups, set)
        cast_seeds.add(seed)
        cast_setups.add(setup)

    pair_reports: list[dict[str, object]] = []
    for pair_id in PAIR_IDS:
        bucket = pair_buckets.get(pair_id)
        if bucket is None:
            pair_reports.append({"pair": pair_id, "status": "INSUFFICIENT", "reason": "no evidence"})
            continue

        completed = int(bucket["completed"])
        unfinished = int(bucket["unfinished"])
        games = completed + unfinished
        lower_wins = int(bucket["lower_wins"])
        higher_wins = int(bucket["higher_wins"])
        draws = int(bucket["draws"])
        lower_score = float(bucket["lower_score"])
        higher_score = completed - lower_score
        unfinished_rate = unfinished / games if games else 1.0
        decisive = lower_wins + higher_wins
        seeds = sorted(bucket["seeds"])
        config_fingerprints = sorted(bucket["config_fingerprints"])
        engine_versions = sorted(bucket["engine_versions"])
        source_revisions = sorted(bucket["source_revisions"])

        if len(config_fingerprints) > 1:
            raise ValueError(
                f"{pair_id}: incompatible AI level configuration fingerprints: "
                f"{config_fingerprints}"
            )
        if len(engine_versions) > 1:
            raise ValueError(
                f"{pair_id}: incompatible engine versions: {engine_versions}"
            )
        setups = sorted(bucket["setups"])

        sufficient = (
            completed >= min_completed
            and unfinished_rate <= max_unfinished_rate
            and len(seeds) >= min_unique_seeds
        )

        if not sufficient:
            status = "INSUFFICIENT"
        elif higher_score > lower_score:
            status = "HIGHER_SCORED"
        elif lower_score > higher_score:
            status = "LOWER_SCORED"
        else:
            status = "EQUAL_SCORE"

        pair_reports.append(
            {
                "pair": pair_id,
                "status": status,
                "experiments": int(bucket["experiments"]),
                "games": games,
                "completed": completed,
                "unfinished": unfinished,
                "unfinished_rate": unfinished_rate,
                "lower_wins": lower_wins,
                "higher_wins": higher_wins,
                "draws": draws,
                "decisive_games": decisive,
                "lower_score": lower_score,
                "higher_score": higher_score,
                "higher_score_pct": (100.0 * higher_score / completed) if completed else None,
                "seeds": seeds,
                "setups": setups,
                "ai_level_config_fingerprints": config_fingerprints,
                "engine_versions": engine_versions,
                "source_revisions": source_revisions,
            }
        )

    candidate_monotonic = all(
        report.get("status") == "HIGHER_SCORED" for report in pair_reports
    )

    return {
        "method": "aggregate adjacent-level calibration evidence",
        "thresholds": {
            "min_completed_games_per_pair": min_completed,
            "max_unfinished_rate": max_unfinished_rate,
            "min_unique_seeds_per_pair": min_unique_seeds,
        },
        "pairs": pair_reports,
        "candidate_monotonic_higher_levels": candidate_monotonic,
        "interpretation": (
            "Descriptive evidence aggregation only. A candidate monotonic ordering "
            "does not by itself authorize public level or search-budget changes."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate adjacent-level Janggi AI calibration evidence."
    )
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--min-completed", type=int, default=20)
    parser.add_argument("--max-unfinished-rate", type=float, default=0.25)
    parser.add_argument("--min-unique-seeds", type=int, default=2)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    result = aggregate_evidence(
        args.paths,
        min_completed=args.min_completed,
        max_unfinished_rate=args.max_unfinished_rate,
        min_unique_seeds=args.min_unique_seeds,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output is not None:
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
