import unittest

from janggi.evaluation import EvaluationGame
from janggi.match import GameStatus
from tools.benchmark_ai_strength import summarize_games
from tools.benchmark_ai_levels import validate_benchmark_args


class AiStrengthBenchmarkTests(unittest.TestCase):
    def test_level_benchmark_requires_balanced_game_count(self):
        validate_benchmark_args(0, 16)
        validate_benchmark_args(2, 16)
        validate_benchmark_args(4, 32)

        with self.assertRaises(ValueError):
            validate_benchmark_args(1, 16)
        with self.assertRaises(ValueError):
            validate_benchmark_args(3, 16)
        with self.assertRaises(ValueError):
            validate_benchmark_args(2, 0)

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


if __name__ == "__main__":
    unittest.main()
