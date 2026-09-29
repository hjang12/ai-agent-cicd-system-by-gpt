import unittest
from types import SimpleNamespace

from janggi import AILevel, GameState, TrainingDataset, get_ai_level
from tools.generate_self_play_dataset import build_search_config, summarize_results


class SelfPlayDatasetToolTests(unittest.TestCase):
    def test_build_search_config_preserves_public_level_and_sets_seed(self):
        spec = get_ai_level(AILevel.HARD)
        config = build_search_config(spec, seed=1234, random_ties=True)

        self.assertEqual(config.depth, spec.config.depth)
        self.assertEqual(config.mobility_weight, spec.config.mobility_weight)
        self.assertEqual(config.quiescence_depth, spec.config.quiescence_depth)
        self.assertEqual(config.root_refinement_count, spec.config.root_refinement_count)
        self.assertEqual(config.seed, 1234)
        self.assertTrue(config.random_ties)

    def test_summary_keeps_unfinished_games_out_of_training_eligible_count(self):
        terminal = SimpleNamespace(
            record=SimpleNamespace(setup="classic", result="cho_win"),
            training_eligible=True,
        )
        unfinished = SimpleNamespace(
            record=SimpleNamespace(setup="classic", result=None),
            training_eligible=False,
        )

        summary = summarize_results(
            (terminal, unfinished),
            dataset=TrainingDataset(),
            level=get_ai_level("4"),
            games=2,
            max_plies=128,
            seed=20260929,
            random_ties=False,
        )

        self.assertEqual(summary["results"]["terminal_games"], 1)
        self.assertEqual(summary["results"]["unfinished_games"], 1)
        self.assertEqual(summary["results"]["training_eligible_games"], 1)
        self.assertEqual(summary["results"]["training_examples"], 0)
        self.assertEqual(summary["generator"]["level"], "4")
        self.assertEqual(summary["generator"]["seed_han"], 20260930)

    def test_state_import_remains_available_for_dataset_consumers(self):
        self.assertIsInstance(GameState.initial(), GameState)


if __name__ == "__main__":
    unittest.main()
