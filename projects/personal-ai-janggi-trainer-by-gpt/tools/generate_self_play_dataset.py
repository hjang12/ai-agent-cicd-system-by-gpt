from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Iterable

from janggi import (
    AILevelSpec,
    NegamaxEngine,
    SelfPlayGenerator,
    SelfPlayResult,
    TrainingDataset,
    TrainingDatasetBuilder,
    get_ai_level,
)


def build_search_config(
    spec: AILevelSpec,
    *,
    seed: int,
    random_ties: bool,
):
    """Return a reproducible copy of the public level search profile."""
    return replace(
        spec.config,
        seed=seed,
        random_ties=random_ties,
    )


def generate_training_dataset(
    *,
    games: int,
    max_plies: int,
    level: str,
    setup: str,
    seed: int,
    random_ties: bool,
) -> tuple[TrainingDataset, dict[str, object]]:
    if games < 1:
        raise ValueError("games must be at least 1")
    if max_plies < 1:
        raise ValueError("max_plies must be at least 1")

    spec = get_ai_level(level)
    cho_engine = NegamaxEngine(
        build_search_config(spec, seed=seed, random_ties=random_ties)
    )
    han_engine = NegamaxEngine(
        build_search_config(spec, seed=seed + 1, random_ties=random_ties)
    )
    generator = SelfPlayGenerator(
        cho_engine,
        han_engine,
        max_plies=max_plies,
    )
    results = generator.generate_many(count=games, setup=setup)

    eligible_results = tuple(result for result in results if result.training_eligible)
    dataset = TrainingDatasetBuilder().build_many(
        result.record for result in eligible_results
    )
    summary = summarize_results(
        results,
        dataset=dataset,
        level=spec,
        games=games,
        max_plies=max_plies,
        seed=seed,
        random_ties=random_ties,
    )
    return dataset, summary


def summarize_results(
    results: Iterable[SelfPlayResult],
    *,
    dataset: TrainingDataset,
    level: AILevelSpec,
    games: int,
    max_plies: int,
    seed: int,
    random_ties: bool,
) -> dict[str, object]:
    materialized = tuple(results)
    terminal_games = sum(
        1 for result in materialized if result.record.result is not None
    )
    training_eligible_games = sum(
        1 for result in materialized if result.training_eligible
    )
    unfinished_games = games - terminal_games
    return {
        "generator": {
            "level": level.level.value,
            "level_name": level.name,
            "setup": materialized[0].record.setup if materialized else "classic",
            "games": games,
            "max_plies": max_plies,
            "seed_cho": seed,
            "seed_han": seed + 1,
            "random_ties": random_ties,
            "search_profile": {
                "depth": level.config.depth,
                "mobility_weight": level.config.mobility_weight,
                "quiescence_depth": level.config.quiescence_depth,
                "root_refinement_count": level.config.root_refinement_count,
                "time_limit_ms": level.config.time_limit_ms,
            },
        },
        "results": {
            "terminal_games": terminal_games,
            "unfinished_games": unfinished_games,
            "training_eligible_games": training_eligible_games,
            "training_examples": len(dataset),
        },
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate validated Janggi self-play training data."
    )
    parser.add_argument(
        "--games",
        type=int,
        default=8,
        help="Number of self-play games to generate.",
    )
    parser.add_argument(
        "--max-plies",
        type=int,
        default=128,
        help="Maximum plies per game; unfinished games are excluded from training.",
    )
    parser.add_argument(
        "--level",
        choices=("1", "2", "3", "4", "5", "6"),
        default="4",
        help="Public AI level used by both self-play sides.",
    )
    parser.add_argument(
        "--setup",
        choices=("classic", "left", "right", "both"),
        default="classic",
        help="Initial board arrangement.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260929,
        help="Seed for the Cho engine; Han uses seed+1.",
    )
    parser.add_argument(
        "--random-ties",
        action="store_true",
        help="Enable fixed-seed random tie-breaking for additional game diversity.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("self-play-training.json"),
        help="Output path for the raw janggi-training-v1 dataset.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=None,
        help="Optional output path for generator metadata and eligibility counts.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    dataset, summary = generate_training_dataset(
        games=args.games,
        max_plies=args.max_plies,
        level=args.level,
        setup=args.setup,
        seed=args.seed,
        random_ties=args.random_ties,
    )
    if not dataset.examples:
        raise SystemExit(
            "No training-eligible self-play examples were generated. "
            "Increase --max-plies or adjust the AI level."
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        dataset.to_json() + "\n",
        encoding="utf-8",
    )

    summary_output = args.summary_output
    if summary_output is None:
        summary_output = args.output.with_suffix(".summary.json")
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Self-play training dataset generated")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"dataset: {args.output}")
    print(f"summary: {summary_output}")


if __name__ == "__main__":
    main()
