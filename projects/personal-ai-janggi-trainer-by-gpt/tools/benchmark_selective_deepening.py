from __future__ import annotations

from dataclasses import dataclass

from janggi import GameState, Piece, PieceType, Side
from janggi.search import NegamaxEngine, SearchConfig


@dataclass(frozen=True)
class Fixture:
    name: str
    state: GameState
    compare_full_depth: bool = True


def _initial_fixture() -> Fixture:
    return Fixture("initial", GameState.initial(), compare_full_depth=False)


def _capture_fixture() -> Fixture:
    board = [None] * 90
    board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
    board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
    board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
    board[0 + 4 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
    board[2 + 3 * 9] = Piece(Side.CHO, PieceType.HORSE)
    return Fixture("capture", GameState(tuple(board), turn=Side.CHO))


def _double_attack_fixture() -> Fixture:
    board = [None] * 90
    board[4] = Piece(Side.CHO, PieceType.GENERAL)
    board[85] = Piece(Side.HAN, PieceType.GENERAL)
    board[36] = Piece(Side.CHO, PieceType.CHARIOT)
    board[46] = Piece(Side.CHO, PieceType.CHARIOT)
    board[35] = Piece(Side.CHO, PieceType.SOLDIER)
    board[81] = Piece(Side.HAN, PieceType.CHARIOT)
    return Fixture("double_attack", GameState(tuple(board), turn=Side.CHO))


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


def main() -> None:
    fixtures = (
        _initial_fixture(),
        _capture_fixture(),
        _double_attack_fixture(),
        _endgame_fixture(),
    )

    print("Selective root deepening benchmark")
    print("Production candidate: depth 2 with root_refinement_count=3.")
    print("The candidate searches all root moves at depth 2, then refines the top 3 with one additional full ply.")
    print("Full depth-3 comparison is applied only to compact tactical/endgame fixtures to keep CI bounded.")
    print()
    print(
        "fixture,shallow_nodes,selective_nodes,selective_score,selective_depth,"
        "full_depth3_nodes,full_depth3_score,selective_matches_depth3_score,"
        "selective_nodes_reduction_vs_full_pct"
    )

    for fixture in fixtures:
        shallow = NegamaxEngine(
            SearchConfig(depth=2, mobility_weight=2, root_refinement_count=0)
        ).analyze(fixture.state)
        selective = NegamaxEngine(
            SearchConfig(depth=2, mobility_weight=2, root_refinement_count=3)
        ).analyze(fixture.state)

        if selective.best_move is None:
            raise AssertionError(f"selective refinement returned no move for {fixture.name}")
        if selective.depth != 3:
            raise AssertionError(f"selective refinement did not report effective depth 3 for {fixture.name}")
        if selective.nodes <= shallow.nodes:
            raise AssertionError(f"selective refinement did not perform deeper work for {fixture.name}")

        if fixture.compare_full_depth:
            full = NegamaxEngine(SearchConfig(depth=3, mobility_weight=2)).analyze(fixture.state)
            if full.best_move is None:
                raise AssertionError(f"full depth-3 search returned no move for {fixture.name}")
            if selective.score_cp != full.score_cp:
                raise AssertionError(
                    f"selective refinement changed full-depth score for {fixture.name}: "
                    f"selective={selective.score_cp}, full={full.score_cp}"
                )
            reduction = 100.0 * (full.nodes - selective.nodes) / full.nodes
            print(
                f"{fixture.name},{shallow.nodes},{selective.nodes},{selective.score_cp},{selective.depth},"
                f"{full.nodes},{full.score_cp},{selective.score_cp == full.score_cp},{reduction:.2f}"
            )
        else:
            print(
                f"{fixture.name},{shallow.nodes},{selective.nodes},{selective.score_cp},{selective.depth},"
                "n/a,n/a,n/a,n/a"
            )


if __name__ == "__main__":
    main()
