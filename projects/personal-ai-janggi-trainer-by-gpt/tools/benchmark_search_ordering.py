from __future__ import annotations

from dataclasses import dataclass

from janggi import GameState, Move, Piece, PieceType, Side
from janggi.search import NegamaxEngine, SearchConfig


@dataclass(frozen=True)
class Fixture:
    name: str
    state: GameState


class CoordinateOrderedEngine(NegamaxEngine):
    """Reference engine with stable coordinate ordering only."""

    def _ordered_moves(self, state: GameState, moves: tuple[Move, ...]) -> tuple[Move, ...]:
        return tuple(sorted(moves, key=lambda move: (move.src or (-1, -1), move.dst or (-1, -1))))


class StrongForcingOrderedEngine(NegamaxEngine):
    """Experiment with checks ahead of captures."""

    def _ordered_moves(self, state: GameState, moves: tuple[Move, ...]) -> tuple[Move, ...]:
        return tuple(
            sorted(
                moves,
                key=lambda move: (
                    -int(self._gives_check(state, move)),
                    -self._captured_value(state, move),
                    move.src or (-1, -1),
                    move.dst or (-1, -1),
                ),
            )
        )


class CaptureCheckOrderedEngine(NegamaxEngine):
    """Experiment with checking captures ahead of other forcing moves."""

    def _ordered_moves(self, state: GameState, moves: tuple[Move, ...]) -> tuple[Move, ...]:
        return tuple(
            sorted(
                moves,
                key=lambda move: (
                    -int(self._gives_check(state, move) and self._captured_value(state, move) > 0),
                    -int(self._captured_value(state, move) > 0),
                    -self._captured_value(state, move),
                    move.src or (-1, -1),
                    move.dst or (-1, -1),
                ),
            )
        )


class NoLegalMoveCacheEngine(NegamaxEngine):
    """Reference engine with legal-move caching disabled and counted."""

    def __init__(self, config: SearchConfig) -> None:
        super().__init__(config)
        self.legal_move_generations = 0

    def analyze(self, state: GameState):
        self.legal_move_generations = 0
        return super().analyze(state)

    def _legal_moves(self, state: GameState, include_pass: bool) -> tuple[Move, ...]:
        self.legal_move_generations += 1
        return state.legal_moves(include_pass=include_pass)


class CountingLegalMoveCacheEngine(NegamaxEngine):
    """Production ordering with counted cache misses."""

    def __init__(self, config: SearchConfig) -> None:
        super().__init__(config)
        self.legal_move_generations = 0

    def analyze(self, state: GameState):
        self.legal_move_generations = 0
        return super().analyze(state)

    def _legal_moves(self, state: GameState, include_pass: bool) -> tuple[Move, ...]:
        cache_key = (state.position_key(), include_pass)
        if cache_key not in self._legal_moves_cache:
            self.legal_move_generations += 1
        return super()._legal_moves(state, include_pass)


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


def _double_attack_fixture() -> Fixture:
    board = [None] * 90
    board[4] = Piece(Side.CHO, PieceType.GENERAL)
    board[85] = Piece(Side.HAN, PieceType.GENERAL)
    board[36] = Piece(Side.CHO, PieceType.CHARIOT)
    board[46] = Piece(Side.CHO, PieceType.CHARIOT)
    board[35] = Piece(Side.CHO, PieceType.SOLDIER)
    board[81] = Piece(Side.HAN, PieceType.CHARIOT)
    return Fixture("double_attack", GameState(tuple(board), turn=Side.CHO))


def _midgame_fixture() -> Fixture:
    """Representative non-initial position with mixed material and mobility."""
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


def _endgame_fixture() -> Fixture:
    """Representative reduced-material position for endgame search behavior."""
    board = [None] * 90
    board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
    board[2 + 4 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
    board[4 + 5 * 9] = Piece(Side.CHO, PieceType.SOLDIER)

    board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
    board[6 + 6 * 9] = Piece(Side.HAN, PieceType.CHARIOT)
    board[4 + 6 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
    board[3 + 9 * 9] = Piece(Side.HAN, PieceType.GUARD)
    return Fixture("endgame", GameState(tuple(board), turn=Side.CHO))


def _run(engine_cls: type[NegamaxEngine], fixture: Fixture, depth: int):
    engine = engine_cls(SearchConfig(depth=depth, mobility_weight=2))
    return engine, engine.analyze(fixture.state)


def main() -> None:
    fixtures = (
        _initial_fixture(),
        _capture_fixture(),
        _check_fixture(),
        _double_attack_fixture(),
        _midgame_fixture(),
        _endgame_fixture(),
    )
    expected_current_nodes = {
        ("initial", 2): 144,
        ("capture", 2): 56,
        ("capture", 3): 409,
        ("check", 2): 41,
        ("check", 3): 522,
        ("double_attack", 2): 118,
        ("double_attack", 3): 941,
        ("midgame", 2): 149,
        ("endgame", 2): 108,
        ("endgame", 3): 641,
    }

    print("Search benchmark: reference vs current vs check-first vs capture-check-first")
    print("All measurements use the same evaluation, caches, depth, and fixtures.")
    print("Depth 3 is limited to compact tactical/endgame fixtures to keep CI bounded.")
    print()
    print("fixture,depth,reference_nodes,current_nodes,check_first_nodes,capture_check_nodes,current_reduction_pct,check_first_reduction_pct,capture_check_reduction_pct,current_same_score,check_first_same_score,capture_check_same_score,current_same_best_move,check_first_same_best_move,capture_check_same_best_move")

    for fixture in fixtures:
        depths = (2, 3) if fixture.name in {"capture", "check", "double_attack", "endgame"} else (2,)
        for depth in depths:
            _, reference = _run(CoordinateOrderedEngine, fixture, depth)
            _, current = _run(NegamaxEngine, fixture, depth)
            _, check_first = _run(StrongForcingOrderedEngine, fixture, depth)
            _, capture_check = _run(CaptureCheckOrderedEngine, fixture, depth)
            current_reduction = 0.0
            check_first_reduction = 0.0
            capture_check_reduction = 0.0
            if reference.nodes:
                current_reduction = 100.0 * (reference.nodes - current.nodes) / reference.nodes
                check_first_reduction = 100.0 * (reference.nodes - check_first.nodes) / reference.nodes
                capture_check_reduction = 100.0 * (reference.nodes - capture_check.nodes) / reference.nodes
            expected_nodes = expected_current_nodes.get((fixture.name, depth))
            if expected_nodes is not None and current.nodes != expected_nodes:
                raise AssertionError(
                    f"current node baseline changed for {fixture.name} depth {depth}: "
                    f"expected {expected_nodes}, got {current.nodes}"
                )
            if current.score_cp != reference.score_cp:
                raise AssertionError(f"current ordering changed minimax score for {fixture.name} depth {depth}")
            # Equal-scored moves can legitimately differ between orderings because
            # alpha-beta pruning preserves score correctness, not a unique tie-break.
            if check_first.score_cp != reference.score_cp:
                raise AssertionError(f"check-first ordering changed minimax score for {fixture.name} depth {depth}")
            if capture_check.score_cp != reference.score_cp:
                raise AssertionError(f"capture-check ordering changed minimax score for {fixture.name} depth {depth}")
            print(
                f"{fixture.name},{depth},{reference.nodes},{current.nodes},{check_first.nodes},{capture_check.nodes},"
                f"{current_reduction:.2f},{check_first_reduction:.2f},{capture_check_reduction:.2f},"
                f"{current.score_cp == reference.score_cp},{check_first.score_cp == reference.score_cp},"
                f"{capture_check.score_cp == reference.score_cp},{current.best_move == reference.best_move},"
                f"{check_first.best_move == reference.best_move},{capture_check.best_move == reference.best_move}"
            )

    print()
    print("Legal-move generation benchmark: current cache vs disabled cache")
    print("Counts are deterministic underlying GameState.legal_moves() generations, not wall-clock timings.")
    print("fixture,depth,no_cache_generations,cached_generations,generation_reduction_pct,same_score")
    for fixture in fixtures:
        depths = (2, 3) if fixture.name in {"capture", "check", "double_attack", "endgame"} else (2,)
        for depth in depths:
            no_cache_engine, no_cache = _run(NoLegalMoveCacheEngine, fixture, depth)
            cached_engine, cached = _run(CountingLegalMoveCacheEngine, fixture, depth)
            reduction = 0.0
            if no_cache_engine.legal_move_generations:
                reduction = 100.0 * (
                    no_cache_engine.legal_move_generations - cached_engine.legal_move_generations
                ) / no_cache_engine.legal_move_generations
            if no_cache.score_cp != cached.score_cp:
                raise AssertionError(f"legal-move caching changed minimax score for {fixture.name} depth {depth}")
            print(
                f"{fixture.name},{depth},{no_cache_engine.legal_move_generations},"
                f"{cached_engine.legal_move_generations},{reduction:.2f},"
                f"{no_cache.score_cp == cached.score_cp}"
            )


if __name__ == "__main__":
    main()
