from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path

from janggi import HeadToHeadTournament, LinearValueModel, NegamaxEngine, get_ai_level
from janggi.match import GameStatus
from janggi.rating import update_ratings
from janggi.training import Outcome


def summarize_games(games, *, initial_rating: int, k_factor: int) -> dict[str, object]:
    first_rating = initial_rating
    second_rating = initial_rating
    first_wins = 0
    second_wins = 0
    draws = 0
    unfinished = 0
    rows: list[dict[str, object]] = []

    for index, game in enumerate(games, start=1):
        if game.status is GameStatus.PLAYING:
            unfinished += 1
            rows.append(
                {
                    "game": index,
                    "status": game.status.value,
                    "outcome_for_first": None,
                    "plies": len(game.moves),
                }
            )
            continue

        outcome = game.outcome_for_first
        if outcome is Outcome.WIN:
            first_wins += 1
        elif outcome is Outcome.LOSS:
            second_wins += 1
        else:
            draws += 1

        update = update_ratings(
            first_rating,
            second_rating,
            outcome,
            k_factor=k_factor,
        )
        first_rating = update.first_rating
        second_rating = update.second_rating
        rows.append(
            {
                "game": index,
                "status": game.status.value,
                "outcome_for_first": outcome.value,
                "plies": len(game.moves),
                "rating_delta_first": update.first_delta,
                "rating_first": update.first_rating,
                "rating_second": update.second_rating,
            }
        )

    completed = first_wins + second_wins + draws
    score = first_wins + draws * 0.5
    score_pct = (100.0 * score / completed) if completed else None

    return {
        "games": len(rows),
        "completed": completed,
        "unfinished": unfinished,
        "first_wins": first_wins,
        "second_wins": second_wins,
        "draws": draws,
        "first_score": score,
        "second_score": completed - score,
        "first_score_pct": score_pct,
        "initial_rating": initial_rating,
        "final_first_rating": first_rating,
        "final_second_rating": second_rating,
        "rating_delta": first_rating - initial_rating,
        "game_results": rows,
    }


def run_linear_value_benchmark(
    *,
    model: LinearValueModel,
    games: int,
    max_plies: int,
    level: str,
    setup: str,
    seed: int,
    random_ties: bool,
    initial_rating: int = 1000,
    k_factor: int = 16,
) -> dict[str, object]:
    if games < 2 or games % 2:
        raise ValueError("games must be an even integer of at least 2")
    if max_plies < 1:
        raise ValueError("max_plies must be at least 1")

    spec = get_ai_level(level)
    candidate_config = replace(
        spec.config,
        seed=seed,
        random_ties=random_ties,
    )
    baseline_config = replace(
        spec.config,
        seed=seed + 1,
        random_ties=random_ties,
    )

    candidate = NegamaxEngine(candidate_config, value_model=model)
    baseline = NegamaxEngine(baseline_config)

    summary = HeadToHeadTournament(
        candidate,
        baseline,
        first_model_id="linear-value",
        second_model_id="heuristic",
        max_plies=max_plies,
    ).run(
        games,
        alternate_colors=True,
        setup=setup,
    )

    return {
        "experiment": {
            "name": "LinearValueModel vs heuristic evaluator",
            "method": "HeadToHeadTournament with alternating colors",
            "model_format": "janggi-linear-value-v1",
            "ai_level": spec.level.value,
            "ai_level_name": spec.name,
            "setup": setup,
            "games": games,
            "max_plies": max_plies,
            "seed_candidate": seed,
            "seed_baseline": seed + 1,
            "random_ties": random_ties,
            "search_profile": {
                "depth": spec.config.depth,
                "mobility_weight": spec.config.mobility_weight,
                "quiescence_depth": spec.config.quiescence_depth,
                "root_refinement_count": spec.config.root_refinement_count,
                "time_limit_ms": spec.config.time_limit_ms,
            },
            "same_search_budget": True,
            "unfinished_games_excluded_from_score": True,
            "move_validation": "HeadToHeadEvaluator validates every engine move through GameState",
        },
        "results": summarize_games(
            summary.games,
            initial_rating=initial_rating,
            k_factor=k_factor,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare a LinearValueModel against the current heuristic evaluator."
    )
    parser.add_argument("--model", type=Path, required=True, help="Linear value model JSON.")
    parser.add_argument("--games", type=int, default=4, help="Even number of alternating-color games.")
    parser.add_argument("--max-plies", type=int, default=64, help="Maximum plies per game.")
    parser.add_argument(
        "--level",
        choices=("1", "2", "3", "4", "5", "6"),
        default="4",
        help="Public search level used by both engines.",
    )
    parser.add_argument(
        "--setup",
        choices=("classic", "left", "right", "both"),
        default="classic",
    )
    parser.add_argument("--seed", type=int, default=20260929)
    parser.add_argument(
        "--random-ties",
        action="store_true",
        help="Enable fixed-seed random tie-breaking for game diversity.",
    )
    parser.add_argument("--output", type=Path, default=Path("linear-value-strength.json"))
    args = parser.parse_args()

    model = LinearValueModel.from_json(args.model.read_text(encoding="utf-8"))
    payload = run_linear_value_benchmark(
        model=model,
        games=args.games,
        max_plies=args.max_plies,
        level=args.level,
        setup=args.setup,
        seed=args.seed,
        random_ties=args.random_ties,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
