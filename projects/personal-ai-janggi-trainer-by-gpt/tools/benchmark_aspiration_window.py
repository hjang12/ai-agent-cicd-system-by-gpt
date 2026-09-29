from __future__ import annotations

from dataclasses import dataclass

from janggi import GameState, Piece, PieceType, Side
from janggi.search import NegamaxEngine, SearchConfig


@dataclass(frozen=True)
class Fixture:
    name: str
    state: GameState
    max_depth: int


def _initial_fixture() -> Fixture:
    return Fixture("initial", GameState.initial(), 2)


def _capture_fixture() -> Fixture:
    board = [None] * 90
    board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
    board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
    board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
    board[0 + 4 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
    board[2 + 3 * 9] = Piece(Side.CHO, PieceType.HORSE)
    return Fixture("capture", GameState(tuple(board), turn=Side.CHO), 3)


def _double_attack_fixture() -> Fixture:
    board = [None] * 90
    board[4] = Piece(Side.CHO, PieceType.GENERAL)
    board[85] = Piece(Side.HAN, PieceType.GENERAL)
    board[36] = Piece(Side.CHO, PieceType.CHARIOT)
    board[46] = Piece(Side.CHO, PieceType.CHARIOT)
    board[35] = Piece(Side.CHO, PieceType.SOLDIER)
    board[81] = Piece(Side.HAN, PieceType.CHARIOT)
    return Fixture("double_attack", GameState(tuple(board), turn=Side.CHO), 3)


def _endgame_fixture() -> Fixture:
    board = [None] * 90
    board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
    board[2 + 4 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
    board[4 + 5 * 9] = Piece(Side.CHO, PieceType.SOLDIER)
    board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
    board[6 + 6 * 9] = Piece(Side.HAN, PieceType.CHARIOT)
    board[4 + 6 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
    board[3 + 9 * 9] = Piece(Side.HAN, PieceType.GUARD)
    return Fixture("endgame", GameState(tuple(board), turn=Side.CHO), 3)


def _run_iterative(
    engine: NegamaxEngine,
    state: GameState,
    max_depth: int,
    *,
    aspiration_delta: int | None,
) -> tuple[int, object, int, int]:
    moves = engine._legal_moves(state, include_pass=True)
    best_score = 0
    best_move = None
    retries = 0
    preferred_move = None

    for depth in range(1, max_depth + 1):
        if depth > 1:
            engine._transposition.clear()
        engine._active_search_depth = depth

        if aspiration_delta is None or depth == 1:
            score, move, _ = engine._search_root(
                state,
                moves,
                depth,
                preferred_move,
            )
        else:
            alpha = best_score - aspiration_delta
            beta = best_score + aspiration_delta
            score, move, _ = engine._search_root(
                state,
                moves,
                depth,
                preferred_move,
                alpha,
                beta,
            )
            if score <= alpha or score >= beta:
                retries += 1
                score, move, _ = engine._search_root(
                    state,
                    moves,
                    depth,
                    preferred_move,
                )

        best_score = score
        best_move = move
        preferred_move = move

    return best_score, best_move, engine._nodes, retries


def main() -> None:
    aspiration_delta = 50
    print("Aspiration-window probe")
    print("Production engine behavior is unchanged; this benchmark only probes iterative root windows.")
    print(f"Aspiration delta: ±{aspiration_delta} centipawn-equivalent")
    print()
    print("fixture,max_depth,full_nodes,aspiration_nodes,node_change_pct,full_score,aspiration_score,same_score,same_best_move,retries")

    for fixture in (
        _initial_fixture(),
        _capture_fixture(),
        _double_attack_fixture(),
        _endgame_fixture(),
    ):
        full_engine = NegamaxEngine(SearchConfig(depth=fixture.max_depth, mobility_weight=2))
        aspiration_engine = NegamaxEngine(SearchConfig(depth=fixture.max_depth, mobility_weight=2))

        full_score, full_move, full_nodes, _ = _run_iterative(
            full_engine,
            fixture.state,
            fixture.max_depth,
            aspiration_delta=None,
        )
        aspiration_score, aspiration_move, aspiration_nodes, retries = _run_iterative(
            aspiration_engine,
            fixture.state,
            fixture.max_depth,
            aspiration_delta=aspiration_delta,
        )

        if aspiration_score != full_score:
            raise AssertionError(
                f"aspiration window changed final score for {fixture.name}: "
                f"full={full_score}, aspiration={aspiration_score}"
            )
        if full_move is None or aspiration_move is None:
            raise AssertionError(f"missing best move for {fixture.name}")
        if not fixture.state.is_legal(aspiration_move):
            raise AssertionError(f"aspiration move is illegal for {fixture.name}")

        change_pct = 0.0
        if full_nodes:
            change_pct = 100.0 * (full_nodes - aspiration_nodes) / full_nodes

        print(
            f"{fixture.name},{fixture.max_depth},{full_nodes},{aspiration_nodes},"
            f"{change_pct:.2f},{full_score},{aspiration_score},"
            f"{aspiration_score == full_score},{aspiration_move == full_move},{retries}"
        )


if __name__ == "__main__":
    main()
