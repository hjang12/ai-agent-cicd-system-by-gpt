import unittest

from janggi import (
    FEATURE_NAMES,
    GameState,
    LinearValueModel,
    LinearValueTrainer,
    Move,
    NegamaxEngine,
    SearchConfig,
    TrainingDataset,
    TrainingExample,
    extract_value_features,
)


class LinearValueModelTests(unittest.TestCase):
    def test_feature_schema_is_stable_and_initial_position_is_bounded(self):
        state = GameState.initial()
        features = extract_value_features(state)

        self.assertEqual(len(features), len(FEATURE_NAMES))
        self.assertEqual(len(set(FEATURE_NAMES)), len(FEATURE_NAMES))
        self.assertTrue(all(-1.0 <= value <= 1.0 for value in features))
        self.assertEqual(features, extract_value_features(GameState(state.board, state.turn)))

    def test_initial_position_is_symmetric_from_opposite_side(self):
        state = GameState.initial()
        opposite = GameState(board=state.board, turn=state.turn.opponent)

        features = extract_value_features(state)
        opposite_features = extract_value_features(opposite)

        for first, second in zip(features, opposite_features):
            self.assertAlmostEqual(first, -second, places=8)

    def test_model_prediction_is_mate_safe(self):
        model = LinearValueModel(
            weights=tuple(100_000.0 for _ in FEATURE_NAMES),
            bias=100_000.0,
        )

        score = model.predict_cp(GameState.initial())

        self.assertGreaterEqual(score, -(100_000 - 1))
        self.assertLessEqual(score, 100_000 - 1)

    def test_model_serialization_round_trip_preserves_prediction(self):
        model = LinearValueModel(
            weights=tuple(index * 1.25 for index in range(len(FEATURE_NAMES))),
            bias=17.5,
            target_scale_cp=2500.0,
        )

        restored = LinearValueModel.from_json(model.to_json())

        self.assertEqual(restored, model)
        self.assertEqual(
            restored.predict_cp(GameState.initial()),
            model.predict_cp(GameState.initial()),
        )

    def test_trainer_fits_non_empty_dataset(self):
        state_a = GameState.initial()
        state_b = state_a.apply(Move.pass_move())
        dataset = TrainingDataset(
            (
                TrainingExample(
                    state=state_a,
                    move=Move.pass_move(),
                    outcome=__import__("janggi").Outcome.WIN,
                    source="self-play",
                ),
                TrainingExample(
                    state=state_b,
                    move=Move.pass_move(),
                    outcome=__import__("janggi").Outcome.LOSS,
                    source="self-play",
                ),
            )
        )

        model = LinearValueTrainer(ridge=1.0, target_scale_cp=3000.0).fit(dataset)

        self.assertIsInstance(model, LinearValueModel)
        self.assertEqual(len(model.weights), len(FEATURE_NAMES))
        self.assertTrue(all(isinstance(weight, float) for weight in model.weights))
        self.assertTrue(isinstance(model.predict_cp(state_a), int))
        self.assertTrue(isinstance(model.predict_cp(state_b), int))

    def test_empty_dataset_is_rejected(self):
        with self.assertRaises(ValueError):
            LinearValueTrainer().fit(TrainingDataset())

    def test_malformed_model_schema_is_rejected(self):
        with self.assertRaises(ValueError):
            LinearValueModel.from_dict(
                {
                    "format": "janggi-linear-value-v1",
                    "feature_names": [],
                    "weights": [],
                    "bias": 0,
                }
            )

    def test_linear_model_can_be_injected_into_search(self):
        state = GameState.initial()
        model = LinearValueModel(
            weights=tuple(0.0 for _ in FEATURE_NAMES),
            bias=321.0,
        )
        engine = NegamaxEngine(
            SearchConfig(depth=1, mobility_weight=0, quiescence_depth=0),
            value_model=model,
        )

        self.assertEqual(engine._evaluate(state), 321)


if __name__ == "__main__":
    unittest.main()
