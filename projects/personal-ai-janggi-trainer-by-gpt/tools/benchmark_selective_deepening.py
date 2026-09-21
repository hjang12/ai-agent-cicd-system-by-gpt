from __future__ import annotations

from dataclasses import dataclass

from janggi import GameState, Move, Piece, PieceType, Side
from janggi.search import MATE_SCORE, NegamaxEngine, SearchConfig


@dataclass(frozen=True)
class Fixture:
    name: str
    state: GameState


def _double_attack_fixture() -> Fixture:
    board = [None] * 90
    board[4] = Piece(Side.CHO, PieceType.GENERAL)
    board[85] = Piece(Side.HAN, PieceType.GENERAL)
    board[36] = Piece(Side.CHO, PieceType.CHARIOT)
    board[46] = Piece(Side.CHO, PieceType.CHARIOT)
    board[35] = Piece(Side.CHO, PieceType.SOLDIER)
    board[81] = Piece(Side.HAN, PieceType.CHARIOT)
    return Fixture("double_attack", GameState(tuple(board), turn=Side.CHO))


def _capture_fixture() -> Fixture:
    board = [None] * 90
    board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
    board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
    board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
    board[0 + 4 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
    board[2 + 3 * 9] = Piece(Side.CHO, PieceType.HORSE)
    return Fixture("capture", GameState(tuple(board), turn=Side.CHO))


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


def _reset(engine: NegamaxEngine) -> None:
    engine._nodes = 0
    engine._transposition.clear()
    engine._evaluation_cache.clear()
    engine._check_cache.clear()
    engine._legal_moves_cache.clear()


def _root_search(engine: NegamaxEngine, state: GameState) -> list[tuple[int, Move, tuple[Move, ...]]]:
    _reset(engine)
    moves = engine._ordered_moves(state, engine._legal_moves(state, include_pass=False))
    if not moves:
        return []
    alpha = -MATE_SCORE * 2
    beta = MATE_SCORE * 2
    results: list[tuple[int, Move, tuple[Move, ...]]] = []
    for move in moves:
        child = state.apply(move)
        child_noisy = engine._captured_value(state, move) > 0 or engine._gives_check(state, move)
        child_score, child_pv = engine._search(
            child,
            engine.config.depth - 1,
            -beta,
            -alpha,
            child_noisy,
        )
        score = -child_score
        results.append((score, move, (move,) + child_pv))
        alpha = max(alpha, score)
    return results


def _selective_deepening(
    state: GameState,
    *,
    base_depth: int = 2,
    refine_depth: int = 3,
    top_n: int = 4,
) -> tuple[Move | None, int, int, int | None, tuple[Move, ...]]:
    shallow_engine = NegamaxEngine(SearchConfig(depth=base_depth, mobility_weight=2))
    shallow = _root_search(shallow_engine, state)
    if not shallow:
        return None, shallow_engine._nodes, 0, None, ()

    ranked = sorted(
        enumerate(shallow),
        key=lambda item: (-item[1][0], item[0]),
    )
    finalists = ranked[:top_n]
    deep_engine = NegamaxEngine(SearchConfig(depth=refine_depth, mobility_weight=2))
    refined: list[tuple[int, int, Move, tuple[Move, ...]]] = []
    for shallow_rank, (_, (_, move, _)) in enumerate(finalists, start=1):
        child = state.apply(move)
        child_noisy = shallow_engine._captured_value(state, move) > 0 or shallow_engine._gives_check(state, move)
        child_score, child_pv = deep_engine._search(
            child,
            refine_depth - 1,
            -MATE_SCORE * 2,
            MATE_SCORE * 2,
            child_noisy,
        )
        refined.append((-child_score, shallow_rank, move, (move,) + child_pv))
    best_score, shallow_rank, best_move, best_pv = max(
        refined,
        key=lambda item: (item[0], -item[1]),
    )
    return (
        best_move,
        shallow_engine._nodes,
        deep_engine._nodes,
        best_score,
        best_pv,
    )


def main() -> None:
    fixtures = (
        _capture_fixture(),
        _double_attack_fixture(),
        _endgame_fixture(),
    )

    print("Selective root deepening probe")
    print("Base: depth 2. Refinement: depth 3 on top-4 shallow candidates.")
    print("This is an experiment; it is not production configuration.")
    print()
    print("fixture,shallow_best,full_depth3_best,selective_best,selective_shallow_rank,shallow_nodes,full_depth3_nodes,selective_total_nodes,selective_score,full_depth3_score,selective_matches_depth3_move,selective_matches_depth3_score,selective_nodes_reduction_vs_full_pct")

    for fixture in fixtures:
        shallow_engine = NegamaxEngine(SearchConfig(depth=2, mobility_weight=2))
        shallow = shallow_engine.analyze(fixture.state)

        deep_engine = NegamaxEngine(SearchConfig(depth=3, mobility_weight=2))
        deep = deep_engine.analyze(fixture.state)

        selective_best, shallow_nodes, refinement_nodes, selective_score, _ = _selective_deepening(
            fixture.state,
            top_n=4,
        )
        if selective_best is None or deep.best_move is None:
            raise AssertionError(f"fixture did not yield a move: {fixture.name}")

        selective_total_nodes = shallow_nodes + refinement_nodes
        selective_reduction = 100.0 * (deep.nodes - selective_total_nodes) / deep.nodes
        print(
            f"{fixture.name},{shallow.best_move},{deep.best_move},{selective_best},"
            f"{_rank_of_move(fixture.state, shallow_engine, deep.best_move, top_n=4)},"
            f"{shallow.nodes},{deep.nodes},{selective_total_nodes},"
            f"{selective_score},{deep.score_cp},{selective_best == deep.best_move},"
            f"{selective_score == deep.score_cp},{selective_reduction:.2f}"
        )


def _rank_of_move(
    state: GameState,
    engine: NegamaxEngine,
    target: Move | None,
    *,
    top_n: int,
) -> str:
    if target is None:
        return "none"
    results = _root_search(engine, state)
    ranked = sorted(
        enumerate(results),
        key=lambda item: (-item[1][0], item[0]),
    )
    for index, (_, (_, move, _)) in enumerate(ranked[:top_n], start=1):
        if move == target:
            return str(index)
    return ">4"


if __name__ == "__main__":
    main()
