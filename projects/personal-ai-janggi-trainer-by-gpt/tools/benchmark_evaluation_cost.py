from __future__ import annotations

from time import perf_counter

from janggi import GameState, NegamaxEngine, SearchConfig


class ProfiledState(GameState):
    pass


def main() -> None:
    state = GameState.initial()
    config = SearchConfig(depth=1, mobility_weight=2, quiescence_depth=0)
    engine = NegamaxEngine(config)

    counters = {"evaluate": 0, "legal_moves": 0, "is_in_check": 0}
    original_evaluate = engine._evaluate
    original_legal_moves = engine._legal_moves
    original_is_in_check = GameState.is_in_check

    def count_evaluate(current_state):
        counters["evaluate"] += 1
        return original_evaluate(current_state)

    def count_legal_moves(current_state, include_pass):
        counters["legal_moves"] += 1
        return original_legal_moves(current_state, include_pass)

    def count_is_in_check(current_state, side=None):
        counters["is_in_check"] += 1
        return original_is_in_check(current_state, side)

    engine._evaluate = count_evaluate
    engine._legal_moves = count_legal_moves
    GameState.is_in_check = count_is_in_check
    try:
        started = perf_counter()
        analysis = engine.analyze(state)
        elapsed_ms = (perf_counter() - started) * 1000.0
    finally:
        engine._evaluate = original_evaluate
        engine._legal_moves = original_legal_moves
        GameState.is_in_check = original_is_in_check

    print("fixture,depth,nodes,elapsed_ms,evaluate_calls,legal_moves_calls,is_in_check_calls")
    print(
        f"initial,{analysis.depth},{analysis.nodes},{elapsed_ms:.2f},"
        f"{counters['evaluate']},{counters['legal_moves']},{counters['is_in_check']}"
    )


if __name__ == "__main__":
    main()
