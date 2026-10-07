import unittest

from janggi.ai_level import AI_LEVELS, AILevel, ai_level_configuration_fingerprint, ai_level_payload, get_ai_level
from tools.benchmark_ai_levels import validate_benchmark_args


class AILevelTests(unittest.TestCase):
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

    def test_level_benchmark_accepts_tactical_fixture_mode(self):
        validate_benchmark_args(8, 96, pair="5-6", fixture_mode="tactical")

    def test_all_levels_have_unique_order_and_metadata(self):
        self.assertEqual([spec.level for spec in AI_LEVELS], list(AILevel))
        self.assertEqual(len({spec.name for spec in AI_LEVELS}), len(AI_LEVELS))
        self.assertTrue(all(spec.description for spec in AI_LEVELS))

    def test_levels_progress_through_search_complexity(self):
        configs = [spec.config for spec in AI_LEVELS]
        for earlier, later in zip(configs, configs[1:]):
            self.assertGreaterEqual(later.depth, earlier.depth)
            self.assertGreaterEqual(later.quiescence_depth, earlier.quiescence_depth)

    def test_every_public_level_has_a_distinct_search_configuration(self):
        fingerprints = [ai_level_configuration_fingerprint(spec) for spec in AI_LEVELS]
        self.assertEqual(len(fingerprints), 6)
        self.assertEqual(len(set(fingerprints)), 6)

    def test_beginner_and_expert_use_materially_different_search_budgets(self):
        beginner = get_ai_level("1").config
        expert = get_ai_level("6").config
        self.assertEqual(beginner.depth, 1)
        self.assertEqual(beginner.mobility_weight, 0)
        self.assertEqual(beginner.quiescence_depth, 0)
        self.assertEqual(expert.depth, 3)
        self.assertEqual(expert.mobility_weight, 2)
        self.assertEqual(expert.quiescence_depth, 1)
        self.assertEqual(expert.time_limit_ms, 800)

    def test_named_level_lookup(self):
        spec = get_ai_level("5")
        self.assertEqual(spec.level, AILevel.ADVANCED)
        self.assertEqual(spec.name, "상급")
        self.assertEqual(spec.config.root_refinement_count, 2)

    def test_enum_level_lookup(self):
        spec = get_ai_level(AILevel.EXPERT)
        self.assertEqual(spec.level, AILevel.EXPERT)
        self.assertEqual(spec.config.depth, 3)

    def test_invalid_level_is_rejected(self):
        with self.assertRaises(ValueError):
            get_ai_level("0")
        with self.assertRaises(ValueError):
            get_ai_level("7")
        with self.assertRaises(ValueError):
            get_ai_level(3)  # type: ignore[arg-type]

    def test_configuration_fingerprint_is_stable_and_pair_specific(self):
        first = ai_level_configuration_fingerprint(get_ai_level("2"), get_ai_level("3"))
        repeat = ai_level_configuration_fingerprint(get_ai_level("2"), get_ai_level("3"))
        different = ai_level_configuration_fingerprint(get_ai_level("3"), get_ai_level("4"))
        self.assertEqual(first, repeat)
        self.assertNotEqual(first, different)
        self.assertEqual(len(first), 64)

    def test_payload_is_serializable_and_complete(self):
        payload = ai_level_payload()
        self.assertEqual(len(payload), 6)
        self.assertEqual(payload[0]["level"], "1")
        self.assertEqual(payload[0]["name"], "입문")
        self.assertEqual(payload[-1]["level"], "6")
        self.assertIn("description", payload[0])
        self.assertIn("root_refinement_count", payload[-1])


if __name__ == "__main__":
    unittest.main()
