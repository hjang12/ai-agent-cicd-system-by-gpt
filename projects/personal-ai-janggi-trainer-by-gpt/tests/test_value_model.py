import unittest

from janggi import GameState, Move, NegamaxEngine, SearchConfig, validate_value_score


class StubValueModel:
    def __init__(self, score: int) -> None:
        self.score = score
        self.states = []

    def predict_cp(self, state: GameState) -> int:
        self.states.append(state)
        return self.score


class FloatValueModel:
    def predict_cp(self, state: GameState) -> int:
        return 1.5  # type: ignore[return-value]


class MateRangeValueModel:
    def predict_cp(self, state: GameState) -> int:
        return 100_000


class ValueModelTests(unittest.TestCase):
    def test_value_model_can_replace_default_evaluation(self):
        state = GameState.initial().apply(Move.pass_move())
        model = StubValueModel(321)

        engine = NegamaxEngine(
            SearchConfig(depth=1, mobility_weight=0, quiescence_depth=0),
            value_model=model,
        )

        self.assertEqual(engine._evaluate(state), 321)
        self.assertEqual(len(model.states), 1)
        self.assertEqual(model.states[0].position_key(), state.position_key())
        self.assertEqual(model.states[0].history, ())

    def test_value_model_score_is_cached_by_position(self):
        state = GameState.initial()
        model = StubValueModel(123)
        engine = NegamaxEngine(
            SearchConfig(depth=1, mobility_weight=0, quiescence_depth=0),
            value_model=model,
        )

        self.assertEqual(engine._evaluate(state), 123)
        self.assertEqual(engine._evaluate(state), 123)
        self.assertEqual(len(model.states), 1)

    def test_default_search_behavior_is_unchanged_when_value_model_is_none(self):
        state = GameState.initial()
        config = SearchConfig(depth=2)

        default_engine = NegamaxEngine(config)
        explicit_none_engine = NegamaxEngine(config, value_model=None)

        self.assertEqual(default_engine.analyze(state), explicit_none_engine.analyze(state))

    def test_non_integer_value_model_score_is_rejected(self):
        state = GameState.initial()
        engine = NegamaxEngine(
            SearchConfig(depth=1),
            value_model=FloatValueModel(),
        )

        with self.assertRaises(ValueError):
            engine._evaluate(state)

    def test_reserved_mate_score_is_rejected(self):
        state = GameState.initial()
        engine = NegamaxEngine(
            SearchConfig(depth=1),
            value_model=MateRangeValueModel(),
        )

        with self.assertRaises(ValueError):
            engine._evaluate(state)

    def test_value_score_validation_accepts_non_mate_integer_range(self):
        self.assertEqual(validate_value_score(0), 0)
        self.assertEqual(validate_value_score(99_999), 99_999)
        self.assertEqual(validate_value_score(-99_999), -99_999)

        for invalid in (True, False, 1.0, 100_000, -100_000):
            with self.assertRaises(ValueError):
                validate_value_score(invalid)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
