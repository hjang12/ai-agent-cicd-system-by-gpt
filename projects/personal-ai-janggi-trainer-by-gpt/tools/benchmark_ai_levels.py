from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path
from time import perf_counter

from janggi import AI_LEVELS, GameState, HeadToHeadTournament, Move, NegamaxEngine, Piece, PieceType, Side
from janggi.match import GameStatus


@dataclass(frozen=True)
class Fixture:
    name: str
    state: GameState


def _initial_fixture() -> Fixture:
    return Fixture("initial", GameState.initial())


def _capture_fixture() -> Fixture:
    board = [None] * 90
    board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
    board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
    board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
    board[0 + 4 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
    board[2 + 3 * 9] = Piece(Side.CHO, PieceType.HORSE)
    return Fixture("capture", GameState(tuple(board), turn=Side.CHO))


def _check_fixture() -> Fixture:
    board = [None] * 90
    board[0] = Piece(Side.CHO, PieceType.GENERAL)
    board[4 + 9 * 9] = Piece(Side.HAN, PieceType.GENERAL)
    board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
    board[8] = Piece(Side.CHO, PieceType.HORSE)
    return Fixture("check", GameState(tuple(board), turn=Side.CHO))


def _endgame_fixture() -> Fixture:
    board = [None] * 90
    board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
    board[2 + 4 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
    board[4 + 5 * 9] = Piece(Side.CHO, PieceType.SOLDIER)
    board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
    board[6 + 6 * 9] = Piece(Side.HAN, PieceType.CHARIOT)
    board[4 + 6 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
    board[3 + 9 * 9] = Piece(Side.HAN, PieceType.GUARD)
    return Fixture("endgame", GameState(tuple(board), turn=Side.CHO))


def _move_label(move: Move | None) -> str:
    if move is None:
        return "-"
    if move.is_pass:
        return "pass"
    return f"{move.src}->{move.dst}"


def run_search_benchmark() -> list[dict[str, object]]:
    fixtures = (_initial_fixture(), _capture_fixture(), _check_fixture(), _endgame_fixture())

    print("AI level search benchmark")
    print("This measures search complexity, not playing strength.")
    print()
    print("level,name,fixture,depth,nodes,score_cp,best_move,elapsed_ms")

    rows: list[dict[str, object]] = []
    for spec in AI_LEVELS:
        engine = NegamaxEngine(spec.config)
        for fixture in fixtures:
            started = perf_counter()
            analysis = engine.analyze(fixture.state)
            elapsed_ms = (perf_counter() - started) * 1000.0
            row = {
                "level": spec.level.value,
                "name": spec.name,
                "fixture": fixture.name,
                "depth": analysis.depth,
                "nodes": analysis.nodes,
                "score_cp": analysis.score_cp,
                "best_move": _move_label(analysis.best_move),
                "elapsed_ms": round(elapsed_ms, 2),
            }
            rows.append(row)
            print(
                f"{spec.level.value},{spec.name},{fixture.name},"
                f"{analysis.depth},{analysis.nodes},{analysis.score_cp},"
                f"{_move_label(analysis.best_move)},{elapsed_ms:.2f}"
            )
    return rows


def run_adjacent_tournaments(
    games: int,
    max_plies: int,
    pair: str | None = None,
    *,
    seed: int = 20260930,
    setup: str = "classic",
    random_ties: bool = True,
) -> list[dict[str, object]]:
    print()
    print(f"Adjacent-level self-play benchmark: {games} games, {max_plies} plies cap")
    print("Results are exploratory strength evidence, not a calibrated rating.")
    print("lower_level,higher_level,lower_score,higher_score,lower_wins,higher_wins,draws,completed,unfinished")

    rows: list[dict[str, object]] = []
    for lower, higher in zip(AI_LEVELS, AI_LEVELS[1:]):
        pair_id = f"{lower.level.value}-{higher.level.value}"
        if pair is not None and pair_id != pair:
            continue
        lower_engine = NegamaxEngine(
            replace(
                lower.config,
                random_ties=random_ties,
                seed=seed + int(lower.level.value),
            )
        )
        higher_engine = NegamaxEngine(
            replace(
                higher.config,
                random_ties=random_ties,
                seed=seed + int(higher.level.value),
            )
        )
        summary = HeadToHeadTournament(
            lower_engine,
            higher_engine,
            first_model_id=f"level-{lower.level.value}",
            second_model_id=f"level-{higher.level.value}",
            max_plies=max_plies,
        ).run(
            games,
            alternate_colors=True,
            setup=setup,
        )
        game_results = []
        for index, game in enumerate(summary.games, start=1):
            game_results.append(
                {
                    "game": index,
                    "status": game.status.value,
                    "outcome_for_lower": (
                        None if game.status is GameStatus.PLAYING else game.outcome_for_first.value
                    ),
                    "plies": len(game.moves),
                }
            )

        row = {
            "lower_level": lower.level.value,
            "lower_name": lower.name,
            "higher_level": higher.level.value,
            "higher_name": higher.name,
            "games": games,
            "max_plies": max_plies,
            "lower_score": summary.first_score,
            "higher_score": summary.second_score,
            "lower_wins": summary.first_wins,
            "higher_wins": summary.second_wins,
            "draws": summary.draws,
            "completed": summary.completed,
            "unfinished": summary.unfinished,
            "game_results": game_results,
        }
        rows.append(row)
        print(
            f"{lower.level.value},{higher.level.value},"
            f"{summary.first_score},{summary.second_score},"
            f"{summary.first_wins},{summary.second_wins},{summary.draws},"
            f"{summary.completed},{summary.unfinished}"
        )
    return rows



def validate_benchmark_args(
    tournament_games: int,
    max_plies: int,
    pair: str | None = None,
    setup: str = "classic",
) -> None:
    if tournament_games < 0:
        raise ValueError("tournament_games must be non-negative")
    if tournament_games == 1 or tournament_games % 2:
        raise ValueError("tournament_games must be 0 or an even integer of at least 2")
    if max_plies < 1:
        raise ValueError("max_plies must be at least 1")
    if pair is not None and pair not in {"1-2", "2-3", "3-4", "4-5", "5-6"}:
        raise ValueError("pair must be one of 1-2, 2-3, 3-4, 4-5, 5-6")
    if setup not in {"classic", "left", "right", "both"}:
        raise ValueError("setup must be one of classic, left, right, both")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark configured Janggi AI levels.")
    parser.add_argument(
        "--tournament-games",
        type=int,
        default=0,
        help="Also run adjacent-level self-play games.",
    )
    parser.add_argument(
        "--max-plies",
        type=int,
        default=128,
        help="Maximum plies per tournament game.",
    )
    parser.add_argument(
        "--pair",
        choices=("1-2", "2-3", "3-4", "4-5", "5-6"),
        default=None,
        help="Run one adjacent-level pair only; useful for bounded repeated calibration runs.",
    )
    parser.add_argument(
        "--skip-search-benchmark",
        action="store_true",
        help="Skip deterministic fixture search benchmarking and run only the tournament portion.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260930,
        help="Master seed for reproducible calibration tie-breaking.",
    )
    parser.add_argument(
        "--setup",
        choices=("classic", "left", "right", "both"),
        default="classic",
        help="Starting arrangement used for every calibration game.",
    )
    parser.add_argument(
        "--deterministic-ties",
        action="store_true",
        help="Disable benchmark-only random tie-breaking. The default uses fixed-seed tie-breaking for game diversity.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON evidence output path.",
    )
    args = parser.parse_args()

    try:
        validate_benchmark_args(args.tournament_games, args.max_plies, args.pair, args.setup)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    search_rows = run_search_benchmark() if not args.skip_search_benchmark else []
    tournament_rows = (
        run_adjacent_tournaments(
            args.tournament_games,
            args.max_plies,
            args.pair,
            seed=args.seed,
            setup=args.setup,
            random_ties=not args.deterministic_ties,
        )
        if args.tournament_games
        else []
    )
    if args.output is not None:
        payload = {
            "experiment": {
                "name": "adjacent AI level strength benchmark",
                "method": "HeadToHeadTournament with alternating colors",
                "games_per_adjacent_pair": args.tournament_games,
                "max_plies": args.max_plies,
                "pair": args.pair,
                "setup": args.setup,
                "seed": args.seed,
                "random_ties": not args.deterministic_ties,
                "interpretation": "exploratory evidence only; not calibrated player or model rating",
                "seeded_experiment": True,
                "runtime_reproducibility": "wall_clock_sensitive_for_time_bounded_levels",
                "benchmark_only_random_ties": True,
                "search_benchmark_included": not args.skip_search_benchmark,
            },
            "pairs": tournament_rows,
            "search_fixtures": search_rows,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
