import unittest

from janggi import FirstLegalEngine, GameStatus, HeadToHeadEvaluator, Outcome


class EvaluationTests(unittest.TestCase):
    def test_evaluator_requires_distinct_model_ids(self):
        with self.assertRaises(ValueError):
            HeadToHeadEvaluator(
                FirstLegalEngine(),
                FirstLegalEngine(),
                first_model_id="same",
                second_model_id="same",
            )

    def test_capped_game_preserves_model_ids_and_has_no_rating_update(self):
        evaluator = HeadToHeadEvaluator(
            FirstLegalEngine(),
            FirstLegalEngine(),
            first_model_id="first",
            second_model_id="second",
            max_plies=1,
        )

        result = evaluator.play_game(first_rating=1000, second_rating=1000)

        self.assertEqual(result.first_model_id, "first")
        self.assertEqual(result.second_model_id, "second")
        self.assertEqual(len(result.moves), 1)
        self.assertEqual(result.status, GameStatus.PLAYING)
        self.assertIsNone(result.rating_update)
        with self.assertRaises(ValueError):
            _ = result.outcome_for_first

    def test_terminal_outcome_mapping_is_exposed_for_rating_flow(self):
        evaluator = HeadToHeadEvaluator(
            FirstLegalEngine(),
            FirstLegalEngine(),
            first_model_id="first",
            second_model_id="second",
            max_plies=1,
        )
        result = evaluator.play_game()

        # A capped game is intentionally not rating-eligible until it reaches a
        # terminal match status.
        self.assertNotIn(result.status, {GameStatus.CHO_WIN, GameStatus.HAN_WIN})
        self.assertNotEqual(result.outcome_for_first if result.status is not GameStatus.PLAYING else Outcome.DRAW, Outcome.WIN)


if __name__ == "__main__":
    unittest.main()
