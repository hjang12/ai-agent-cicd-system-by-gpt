from __future__ import annotations

from time import perf_counter

from janggi import AI_LEVELS, GameState, Piece, PieceType, Side
from janggi.search import NegamaxEngine


class ProfiledEngine(NegamaxEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_ordering_calls = 0
        self.root_check_calls = 0
        self._profiling_root_ordering = False

    def _ordered_search_moves(self, state, moves, preferred_move, depth):
        root = depth == self._active_search_depth
        if root:
            self.root_ordering_calls += 1
        previous = self._profiling_root_ordering
        self._profiling_root_ordering = root
        try:
            return super()._ordered_search_moves(state, moves, preferred_move, depth)
        finally:
            self._profiling_root_ordering = previous

    def _gives_check(self, state, move):
        if self._profiling_root_ordering:
            self.root_check_calls += 1
        return super()._gives_check(state, move)


def _capture_fixture() -> GameState:
    board = [None] * 90
    board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
    board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
    board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
    board[0 + 4 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
    board[2 + 3 * 9] = Piece(Side.CHO, PieceType.HORSE)
    return GameState(tuple(board), turn=Side.CHO)


def _check_fixture() -> GameState:
    board = [None] * 90
    board[0] = Piece(Side.CHO, PieceType.GENERAL)
    board[4 + 9 * 9] = Piece(Side.HAN, PieceType.GENERAL)
    board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
    board[8] = Piece(Side.CHO, PieceType.HORSE)
    return GameState(tuple(board), turn=Side.CHO)


FIXTURES = (
    ("initial", GameState.initial()),
    ("capture", _capture_fixture()),
    ("check", _check_fixture()),
)

EXPERT = next(spec for spec in AI_LEVELS if spec.level.value == "6")


def main() -> None:
    print("Timed Lv6 profile")
    print("fixture,effective_depth,nodes,score_cp,elapsed_ms,root_ordering_calls,root_check_calls")
    for name, state in FIXTURES:
        engine = ProfiledEngine(EXPERT.config)
        started = perf_counter()
        analysis = engine.analyze(state)
        elapsed_ms = (perf_counter() - started) * 1000.0
        print(
            f"{name},{analysis.depth},{analysis.nodes},{analysis.score_cp},"
            f"{elapsed_ms:.2f},{engine.root_ordering_calls},{engine.root_check_calls}"
        )


if __name__ == "__main__":
    main()
