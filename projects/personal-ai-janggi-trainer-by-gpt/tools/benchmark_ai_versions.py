from __future__ import annotations

import argparse
from dataclasses import dataclass

from janggi import GameState, HeadToHeadTournament, Move, NegamaxEngine, Piece, PieceType, Side
from janggi.search import SearchConfig


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


FIXTURES = (_initial_fixture(), _capture_fixture(), _check_fixture(), _endgame_fixture())


def v1_config() -> SearchConfig:
    """Search stack immediately before the current ordering/quiescence refinements."""
    return SearchConfig(
        depth=2,
        mobility_weight=2,
        quiescence_depth=1,
        root_refinement_count=0,
        random_ties=False,
        adaptive_ordering=False,
        quiescence_check_extension=False,
    )


def v2_config() -> SearchConfig:
    """Current search stack with adaptive ordering and check-safe quiescence."""
    return SearchConfig(
        depth=2,
        mobility_weight=2,
        quiescence_depth=1,
        root_refinement_count=0,
        random_ties=False,
        adaptive_ordering=True,
        quiescence_check_extension=True,
    )


def _move_label(move: Move | None) -> str:
    if move is None:
        return "-"
    if move.is_pass:
        return "pass"
    return f"{move.src}->{move.dst}"


def run_position_comparison() -> None:
    print("AI v1 vs AI v2 position comparison")
    print("Same depth/evaluation/configuration; only the post-v1 search refinements differ.")
    print()
    print("fixture,v1_nodes,v2_nodes,node_change_pct,v1_score_cp,v2_score_cp,same_score,v1_best_move,v2_best_move,same_best_move")

    for fixture in FIXTURES:
        v1 = NegamaxEngine(v1_config())
        v2 = NegamaxEngine(v2_config())
        analysis_v1 = v1.analyze(fixture.state)
        analysis_v2 = v2.analyze(fixture.state)
        change_pct = 0.0
        if analysis_v1.nodes:
            change_pct = 100.0 * (analysis_v2.nodes - analysis_v1.nodes) / analysis_v1.nodes
        print(
            f"{fixture.name},{analysis_v1.nodes},{analysis_v2.nodes},{change_pct:.2f},"
            f"{analysis_v1.score_cp},{analysis_v2.score_cp},"
            f"{analysis_v1.score_cp == analysis_v2.score_cp},"
            f"{_move_label(analysis_v1.best_move)},{_move_label(analysis_v2.best_move)},"
            f"{analysis_v1.best_move == analysis_v2.best_move}"
        )


def run_head_to_head(games: int, max_plies: int) -> None:
    tournament = HeadToHeadTournament(
        NegamaxEngine(v1_config()),
        NegamaxEngine(v2_config()),
        first_model_id="ai-v1",
        second_model_id="ai-v2",
        max_plies=max_plies,
    )
    summary = tournament.run(games, alternate_colors=True)

    print()
    print(f"AI v1 vs AI v2 head-to-head: {games} games, {max_plies} plies cap")
    print("Colors alternate by game. Unfinished games are reported separately and are not draws.")
    print(
        "v1_score,v2_score,v1_wins,v2_wins,draws,completed,unfinished"
    )
    print(
        f"{summary.first_score},{summary.second_score},"
        f"{summary.first_wins},{summary.second_wins},{summary.draws},"
        f"{summary.completed},{summary.unfinished}"
    )

    completed = summary.completed
    observed = summary.first_wins + summary.second_wins + summary.draws
    if observed != completed:
        raise AssertionError(
            f"head-to-head accounting mismatch: observed={observed}, completed={completed}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare the pre-refinement Janggi search stack with the current stack."
    )
    parser.add_argument(
        "--games",
        type=int,
        default=4,
        help="Number of alternating-color head-to-head games.",
    )
    parser.add_argument(
        "--max-plies",
        type=int,
        default=64,
        help="Maximum plies per head-to-head game.",
    )
    args = parser.parse_args()

    if args.games < 1:
        raise SystemExit("--games must be at least 1")
    if args.max_plies < 1:
        raise SystemExit("--max-plies must be at least 1")

    run_position_comparison()
    run_head_to_head(args.games, args.max_plies)


if __name__ == "__main__":
    main()
