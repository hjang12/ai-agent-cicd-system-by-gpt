import unittest

from janggi import FirstLegalEngine, GameStatus, Move, RuleSet
from janggi.engine import EngineAnalysis, EngineInfo
from janggi.self_play import SelfPlayGenerator, SelfPlayResult, generate_self_play_games


class PassTwiceEngine:
    @property
    def info(self):
        return EngineInfo(name="pass-twice", version="test")

    def choose_move(self, state):
        return Move.pass_move()

    def analyze(self, state):
        return EngineAnalysis(perspective=state.turn)


class IllegalEngine:
    @property
    def info(self):
        return EngineInfo(name="illegal", version="test")

    def choose_move(self, state):
        return Move((0, 0), (9, 0))

    def analyze(self, state):
        return EngineAnalysis(perspective=state.turn)


class SelfPlayTests(unittest.TestCase):
    def test_completed_self_play_game_is_training_eligible(self):
        result = SelfPlayGenerator(
            PassTwiceEngine(),
            rules=RuleSet(consecutive_passes_for_draw=2),
        ).generate()

        self.assertIsInstance(result, SelfPlayResult)
        self.assertEqual(result.record.source, "self-play")
        self.assertEqual(result.record.moves, (Move.pass_move(), Move.pass_move()))
        self.assertEqual(result.record.result, GameStatus.DRAW_CONSECUTIVE_PASS.value)
        self.assertTrue(result.validation.replay_valid)
        self.assertTrue(result.validation.complete)
        self.assertTrue(result.training_eligible)

    def test_max_plies_marks_record_incomplete(self):
        result = SelfPlayGenerator(
            FirstLegalEngine(),
            max_plies=1,
            rules=RuleSet(consecutive_passes_for_draw=None),
        ).generate()

        self.assertEqual(len(result.record.moves), 1)
        self.assertIsNone(result.record.result)
        self.assertFalse(result.validation.complete)
        self.assertEqual(result.validation.status.value, "incomplete")
        self.assertFalse(result.training_eligible)

    def test_engine_output_is_validated_before_match_play(self):
        with self.assertRaises(ValueError):
            SelfPlayGenerator(IllegalEngine()).generate()

    def test_different_engines_can_be_used_by_side(self):
        cho = PassTwiceEngine()
        han = PassTwiceEngine()
        result = SelfPlayGenerator(cho, han).generate()
        self.assertEqual(result.record.moves, (Move.pass_move(), Move.pass_move()))
        self.assertEqual(result.validation.terminal_status, GameStatus.DRAW_CONSECUTIVE_PASS)

    def test_batch_generation_returns_requested_number(self):
        results = generate_self_play_games(
            PassTwiceEngine(),
            count=3,
            rules=RuleSet(consecutive_passes_for_draw=2),
        )
        self.assertEqual(len(results), 3)
        self.assertTrue(all(result.training_eligible for result in results))

    def test_invalid_counts_are_rejected(self):
        with self.assertRaises(ValueError):
            SelfPlayGenerator(FirstLegalEngine()).generate_many(0)
        with self.assertRaises(ValueError):
            generate_self_play_games(FirstLegalEngine(), count=0)

    def test_invalid_max_plies_is_rejected(self):
        with self.assertRaises(ValueError):
            SelfPlayGenerator(FirstLegalEngine(), max_plies=0)


if __name__ == "__main__":
    unittest.main()
