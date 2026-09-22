from __future__ import annotations

import argparse
from dataclasses import dataclass
from time import perf_counter

from janggi import AI_LEVELS, GameState, HeadToHeadTournament, Move, NegamaxEngine, Piece, PieceType, Side


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


def run_search_benchmark() -> None:
    fixtures = (_initial_fixture(), _capture_fixture(), _check_fixture(), _endgame_fixture())

    print("AI level search benchmark")
    print("This measures search complexity, not playing strength.")
    print()
    print("level,name,fixture,depth,nodes,score_cp,best_move,elapsed_ms")

    for spec in AI_LEVELS:
        engine = NegamaxEngine(spec.config)
        for fixture in fixtures:
            started = perf_counter()
            analysis = engine.analyze(fixture.state)
            elapsed_ms = (perf_counter() - started) * 1000.0
            print(
                f"{spec.level.value},{spec.name},{fixture.name},"
                f"{analysis.depth},{analysis.nodes},{analysis.score_cp},"
                f"{_move_label(analysis.best_move)},{elapsed_ms:.2f}"
            )


def run_adjacent_tournaments(games: int, max_plies: int) -> None:
    print()
    print(f"Adjacent-level self-play benchmark: {games} games, {max_plies} plies cap")
    print("Results are exploratory strength evidence, not a certified rating.")
    print("lower_level,higher_level,lower_score,higher_score,draws,completed,unfinished")

    for lower, higher in zip(AI_LEVELS, AI_LEVELS[1:]):
        lower_engine = NegamaxEngine(lower.config)
        higher_engine = NegamaxEngine(higher.config)
        summary = HeadToHeadTournament(
            lower_engine,
            higher_engine,
            first_model_id=f"level-{lower.level.value}",
            second_model_id=f"level-{higher.level.value}",
            max_plies=max_plies,
        ).run(
            games,
            alternate_colors=True,
        )
        print(
            f"{lower.level.value},{higher.level.value},"
            f"{summary.first_score},{summary.second_score},{summary.draws},"
            f"{summary.completed},{summary.unfinished}"
        )


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
    args = parser.parse_args()

    if args.tournament_games < 0:
        raise SystemExit("--tournament-games must be non-negative")
    if args.max_plies < 1:
        raise SystemExit("--max-plies must be at least 1")

    run_search_benchmark()
    if args.tournament_games:
        run_adjacent_tournaments(args.tournament_games, args.max_plies)


if __name__ == "__main__":
    main()
