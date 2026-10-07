from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from janggi import AI_LEVELS, GameState, Piece, PieceType, Side, ai_level_configuration_fingerprint
from janggi.search import NegamaxEngine


@dataclass(frozen=True)
class Fixture:
    name: str
    state: GameState


class ProfiledEngine(NegamaxEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_ordering_calls = 0
        self.root_check_calls = 0
        self.check_cache_hits = 0
        self.check_cache_misses = 0
        self.legal_cache_hits = 0
        self.legal_cache_misses = 0
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
        cache_key = (state.position_key(), move)
        if cache_key in self._check_cache:
            self.check_cache_hits += 1
        else:
            self.check_cache_misses += 1
        return super()._gives_check(state, move)

    def _legal_moves(self, state, include_pass):
        cache_key = (state.position_key(), include_pass)
        if cache_key in self._legal_moves_cache:
            self.legal_cache_hits += 1
        else:
            self.legal_cache_misses += 1
        return super()._legal_moves(state, include_pass)


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


def _midgame_fixture() -> Fixture:
    board = [None] * 90
    board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
    board[3] = Piece(Side.CHO, PieceType.GUARD)
    board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
    board[1 + 2 * 9] = Piece(Side.CHO, PieceType.CANNON)
    board[2 + 2 * 9] = Piece(Side.CHO, PieceType.HORSE)
    board[4 + 4 * 9] = Piece(Side.CHO, PieceType.SOLDIER)

    board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
    board[5 + 9 * 9] = Piece(Side.HAN, PieceType.GUARD)
    board[8 + 6 * 9] = Piece(Side.HAN, PieceType.CHARIOT)
    board[7 + 7 * 9] = Piece(Side.HAN, PieceType.CANNON)
    board[6 + 7 * 9] = Piece(Side.HAN, PieceType.HORSE)
    board[4 + 5 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
    return Fixture("midgame", GameState(tuple(board), turn=Side.CHO))


FIXTURES = (
    Fixture("initial", GameState.initial()),
    _capture_fixture(),
    _check_fixture(),
    _endgame_fixture(),
    _midgame_fixture(),
)


def main() -> None:
    fingerprints = [ai_level_configuration_fingerprint(spec) for spec in AI_LEVELS]
    if len(set(fingerprints)) != len(AI_LEVELS):
        raise AssertionError("public AI level configuration fingerprints must be unique")

    print("AI level search-profile benchmark")
    print("This is deterministic search-profile evidence, not a playing-strength rating.")
    print("Wall-clock timing is informational because runner performance is not a stable CI contract.")
    print()
    print(
        "level,name,configured_depth,time_limit_ms,mobility_weight,"
        "quiescence_depth,root_refinement_count,fixture,effective_depth,"
        "nodes,score_cp,best_move,elapsed_ms,root_ordering_calls,"
        "root_check_calls,check_cache_hits,check_cache_misses,"
        "legal_cache_hits,legal_cache_misses"
    )

    for spec in AI_LEVELS:
        for fixture in FIXTURES:
            engine = ProfiledEngine(spec.config)
            started = perf_counter()
            analysis = engine.analyze(fixture.state)
            elapsed_ms = (perf_counter() - started) * 1000.0
            best_move = analysis.best_move
            best_move_label = (
                "pass"
                if best_move is not None and best_move.is_pass
                else str((best_move.src, best_move.dst))
                if best_move is not None
                else "-"
            )
            print(
                f"{spec.level.value},{spec.name},{spec.config.depth},"
                f"{spec.config.time_limit_ms or 0},{spec.config.mobility_weight},"
                f"{spec.config.quiescence_depth},{spec.config.root_refinement_count},"
                f"{fixture.name},{analysis.depth},{analysis.nodes},"
                f"{analysis.score_cp},{best_move_label},{elapsed_ms:.2f},"
                f"{engine.root_ordering_calls},{engine.root_check_calls},"
                f"{engine.check_cache_hits},{engine.check_cache_misses},"
                f"{engine.legal_cache_hits},{engine.legal_cache_misses}"
            )


if __name__ == "__main__":
    main()
