import unittest

from janggi import Outcome
from janggi.rating import RatingUpdate, expected_score, update_ratings


class RatingTests(unittest.TestCase):
    def test_equal_ratings_have_equal_expectation(self):
        self.assertAlmostEqual(expected_score(1000, 1000), 0.5)

    def test_stronger_player_has_higher_expectation(self):
        self.assertGreater(expected_score(1200, 1000), 0.5)
        self.assertLess(expected_score(1000, 1200), 0.5)

    def test_win_and_loss_updates_are_opposite(self):
        update = update_ratings(1000, 1000, Outcome.WIN, k_factor=32)

        self.assertIsInstance(update, RatingUpdate)
        self.assertGreater(update.first_rating, 1000)
        self.assertLess(update.second_rating, 1000)
        self.assertEqual(update.first_delta, -update.second_delta)

    def test_draw_keeps_equal_ratings_unchanged(self):
        update = update_ratings(1000, 1000, Outcome.DRAW, k_factor=32)

        self.assertEqual(update.first_rating, 1000)
        self.assertEqual(update.second_rating, 1000)
        self.assertEqual(update.first_delta, 0)
        self.assertEqual(update.second_delta, 0)

    def test_validation_rejects_invalid_inputs(self):
        with self.assertRaises(ValueError):
            expected_score(-1, 1000)
        with self.assertRaises(ValueError):
            expected_score(1000, 1000.5)
        with self.assertRaises(ValueError):
            update_ratings(1000, 1000, Outcome.WIN, k_factor=0)
        with self.assertRaises(ValueError):
            update_ratings(1000, 1000, 1)  # type: ignore[arg-type]

    def test_k_factor_must_be_integer(self):
        with self.assertRaises(ValueError):
            update_ratings(1000, 1000, Outcome.WIN, k_factor=32.5)
        with self.assertRaises(ValueError):
            update_ratings(1000, 1000, Outcome.WIN, k_factor=True)


if __name__ == "__main__":
    unittest.main()
