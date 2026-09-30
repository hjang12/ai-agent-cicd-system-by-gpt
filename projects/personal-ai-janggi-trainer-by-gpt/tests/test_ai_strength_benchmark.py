import unittest

from janggi.evaluation import EvaluationGame
from janggi.match import GameStatus
from tools.benchmark_ai_strength import summarize_games
from tools.benchmark_ai_levels import validate_benchmark_args


class AiStrengthBenchmarkTests(unittest.TestCase):
    def test_unfinished_games_do_not_change_strength_statistics(self):
        games = (
            EvaluationGame("ai-v1", "ai-v2", (), GameStatus.CHO_WIN),
            EvaluationGame("ai-v1", "ai-v2", (), GameStatus.HAN_WIN),
            EvaluationGame("ai-v1", "ai-v2", (), GameStatus.DRAW_BIKJANG),
            EvaluationGame("ai-v1", "ai-v2", (), GameStatus.PLAYING),
        )

        result = summarize_games(games, initial_rating=1000, k_factor=16)

        self.assertEqual(result["games"], 4)
        self.assertEqual(result["completed"], 3)
        self.assertEqual(result["unfinished"], 1)
        self.assertEqual(result["v1_wins"], 1)
        self.assertEqual(result["v2_wins"], 1)
        self.assertEqual(result["draws"], 1)
        self.assertEqual(result["v1_score"], 1.5)
        self.assertEqual(result["v1_score_pct"], 50.0)
        self.assertEqual(result["final_v1_rating"] + result["final_v2_rating"], 2000)
        self.assertIsNone(result["game_results"][-1]["rating_update"])


    def test_level_calibration_accepts_only_known_adjacent_pairs(self):
        for pair in ("1-2", "2-3", "3-4", "4-5", "5-6"):
            validate_benchmark_args(2, 48, pair, "classic")

        for pair in ("1-3", "0-1", "6-7"):
            with self.assertRaises(ValueError):
                validate_benchmark_args(2, 48, pair, "classic")


if __name__ == "__main__":
    unittest.main()


    def test_level_calibration_accepts_supported_starting_arrangements(self):
        for setup in ("classic", "left", "right", "both"):
            validate_benchmark_args(2, 48, "1-2", setup)

        with self.assertRaises(ValueError):
            validate_benchmark_args(2, 48, "1-2", "unknown")
