import unittest
from types import SimpleNamespace

from janggi import FEATURE_NAMES, LinearValueModel, Outcome, get_ai_level
from janggi.match import GameStatus
from tools.benchmark_linear_value_model import summarize_games


class LinearValueBenchmarkTests(unittest.TestCase):
    def test_summary_excludes_unfinished_games(self):
        completed_win = SimpleNamespace(
            status=GameStatus.CHO_WIN,
            outcome_for_first=Outcome.WIN,
            moves=(1, 2, 3),
        )
        completed_draw = SimpleNamespace(
            status=GameStatus.DRAW_BIKJANG,
            outcome_for_first=Outcome.DRAW,
            moves=(1, 2),
        )
        unfinished = SimpleNamespace(
            status=GameStatus.PLAYING,
            outcome_for_first=__import__("janggi").Outcome.DRAW,
            moves=(1,),
        )

        summary = summarize_games(
            (completed_win, completed_draw, unfinished),
            initial_rating=1000,
            k_factor=16,
        )

        self.assertEqual(summary["completed"], 2)
        self.assertEqual(summary["unfinished"], 1)
        self.assertEqual(summary["first_wins"], 1)
        self.assertEqual(summary["draws"], 1)
        self.assertEqual(summary["first_score_pct"], 75.0)
        self.assertEqual(summary["games"], 3)

    def test_public_level_profile_is_available_for_benchmark(self):
        spec = get_ai_level("4")

        self.assertEqual(spec.level.value, "4")
        self.assertEqual(spec.config.depth, 2)
        self.assertEqual(spec.config.quiescence_depth, 1)

    def test_candidate_model_matches_expected_feature_schema(self):
        model = LinearValueModel(
            weights=tuple(0.0 for _ in FEATURE_NAMES),
            bias=0.0,
        )

        self.assertEqual(len(model.weights), len(FEATURE_NAMES))


if __name__ == "__main__":
    unittest.main()
