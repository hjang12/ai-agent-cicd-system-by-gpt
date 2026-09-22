from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Iterable

from janggi import HeadToHeadTournament, NegamaxEngine
from janggi.match import GameStatus
from janggi.rating import update_ratings
from janggi.training import Outcome

from tools.benchmark_ai_versions import v1_config, v2_config


def summarize_games(
    games: Iterable,
    *,
    initial_rating: int,
    k_factor: int,
) -> dict:
    v1_rating = initial_rating
    v2_rating = initial_rating
    v1_wins = 0
    v2_wins = 0
    draws = 0
    unfinished = 0
    game_rows: list[dict] = []

    for index, game in enumerate(games, start=1):
        if game.status is GameStatus.PLAYING:
            unfinished += 1
            game_rows.append(
                {
                    "game": index,
                    "status": game.status.value,
                    "outcome_for_v1": None,
                    "plies": len(game.moves),
                    "rating_update": None,
                }
            )
            continue

        outcome = game.outcome_for_first
        if outcome is Outcome.WIN:
            v1_wins += 1
        elif outcome is Outcome.LOSS:
            v2_wins += 1
        else:
            draws += 1

        update = update_ratings(
            v1_rating,
            v2_rating,
            outcome,
            k_factor=k_factor,
        )
        v1_rating = update.first_rating
        v2_rating = update.second_rating
        game_rows.append(
            {
                "game": index,
                "status": game.status.value,
                "outcome_for_v1": outcome.value,
                "plies": len(game.moves),
                "rating_update": {
                    "v1_delta": update.first_delta,
                    "v2_delta": update.second_delta,
                    "v1_rating": update.first_rating,
                    "v2_rating": update.second_rating,
                },
            }
        )

    completed = v1_wins + v2_wins + draws
    requested = completed + unfinished
    v1_score = v1_wins + draws * 0.5
    score_pct = (100.0 * v1_score / completed) if completed else None

    if v1_wins + v2_wins + draws != completed:
        raise AssertionError("completed-game result accounting mismatch")
    if requested != len(game_rows):
        raise AssertionError("game count accounting mismatch")
    if v1_rating + v2_rating != 2 * initial_rating:
        raise AssertionError("Elo updates must preserve total rating")

    return {
        "games": requested,
        "completed": completed,
        "unfinished": unfinished,
        "v1_wins": v1_wins,
        "v2_wins": v2_wins,
        "draws": draws,
        "v1_score": v1_score,
        "v2_score": completed - v1_score,
        "v1_score_pct": score_pct,
        "initial_rating": initial_rating,
        "final_v1_rating": v1_rating,
        "final_v2_rating": v2_rating,
        "rating_delta": v1_rating - initial_rating,
        "game_results": game_rows,
    }


def run_strength_benchmark(
    *,
    games: int,
    max_plies: int,
    seed: int,
    initial_rating: int,
    k_factor: int,
    setup: str,
    random_ties: bool,
) -> dict:
    if games < 2 or games % 2:
        raise ValueError("games must be an even integer of at least 2 for balanced colors")
    if max_plies < 1:
        raise ValueError("max_plies must be at least 1")

    v1 = NegamaxEngine(
        replace(
            v1_config(),
            random_ties=random_ties,
            seed=seed,
        )
    )
    v2 = NegamaxEngine(
        replace(
            v2_config(),
            random_ties=random_ties,
            seed=seed + 1,
        )
    )

    summary = HeadToHeadTournament(
        v1,
        v2,
        first_model_id="ai-v1",
        second_model_id="ai-v2",
        max_plies=max_plies,
    ).run(
        games,
        alternate_colors=True,
        setup=setup,
    )
    result = summarize_games(
        summary.games,
        initial_rating=initial_rating,
        k_factor=k_factor,
    )

    return {
        "experiment": {
            "name": "AI v1 vs AI v2 strength benchmark",
            "method": "existing HeadToHeadTournament with alternating colors",
            "setup": setup,
            "games": games,
            "max_plies": max_plies,
            "random_ties": random_ties,
            "seed_v1": seed,
            "seed_v2": seed + 1,
            "initial_rating": initial_rating,
            "k_factor": k_factor,
            "search_version_control": "same depth/evaluation/quiescence/root settings; only adaptive ordering and check-safe quiescence differ",
            "unfinished_games_excluded_from_score_and_rating": True,
            "move_validation": "HeadToHeadEvaluator validates every engine move through GameState",
        },
        "results": result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure AI v1 vs v2 playing strength with reproducible self-play."
    )
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Even number of alternating-color games.",
    )
    parser.add_argument(
        "--max-plies",
        type=int,
        default=128,
        help="Maximum plies per game; unfinished games are excluded from strength statistics.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260922,
        help="Master seed for reproducible root tie-breaking.",
    )
    parser.add_argument(
        "--initial-rating",
        type=int,
        default=1000,
        help="Initial Elo rating for both models.",
    )
    parser.add_argument(
        "--k-factor",
        type=int,
        default=16,
        help="Sequential Elo K-factor for completed games.",
    )
    parser.add_argument(
        "--setup",
        choices=("classic", "left", "right", "both"),
        default="classic",
        help="Starting arrangement used for every game in the experiment.",
    )
    parser.add_argument(
        "--deterministic-ties",
        action="store_true",
        help="Disable random tie-breaking. The default uses fixed-seed tie-breaking for game diversity.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON output path.",
    )
    args = parser.parse_args()

    payload = run_strength_benchmark(
        games=args.games,
        max_plies=args.max_plies,
        seed=args.seed,
        initial_rating=args.initial_rating,
        k_factor=args.k_factor,
        setup=args.setup,
        random_ties=not args.deterministic_ties,
    )

    print("AI v1 vs AI v2 strength benchmark")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
