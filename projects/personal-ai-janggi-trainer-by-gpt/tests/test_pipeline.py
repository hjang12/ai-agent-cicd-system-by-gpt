import unittest

from janggi import GameRecord, GameStatus, Move, RuleSet
from janggi.pipeline import (
    RecordSource,
    RecordValidator,
    TrainingDisposition,
    ValidationStatus,
)


class RecordPipelineTests(unittest.TestCase):
    def setUp(self):
        self.validator = RecordValidator(RuleSet(consecutive_passes_for_draw=2))

    def test_incomplete_record_is_analysis_eligible_but_not_training_candidate(self):
        record = GameRecord(source="personal")
        result = self.validator.validate(record)

        self.assertTrue(result.structural_valid)
        self.assertTrue(result.replay_valid)
        self.assertFalse(result.complete)
        self.assertEqual(result.status, ValidationStatus.INCOMPLETE)
        self.assertTrue(result.analysis_eligible)
        self.assertEqual(result.training_disposition, TrainingDisposition.EXCLUDED)
        self.assertEqual(result.terminal_status, GameStatus.PLAYING)
        self.assertIn("game_not_terminal", result.issues)

    def test_curated_human_completed_record_becomes_training_candidate(self):
        record = GameRecord(
            moves=(Move.pass_move(), Move.pass_move()),
            result="draw_consecutive_pass",
            source="curated-human",
        )
        validation = self.validator.validate(record)

        self.assertTrue(validation.structural_valid)
        self.assertTrue(validation.replay_valid)
        self.assertTrue(validation.complete)
        self.assertEqual(validation.status, ValidationStatus.VALID)
        self.assertEqual(validation.terminal_status, GameStatus.DRAW_CONSECUTIVE_PASS)
        self.assertTrue(validation.result_consistent)
        self.assertTrue(validation.training_eligible)
        self.assertEqual(validation.training_disposition, TrainingDisposition.CANDIDATE)

    def test_self_play_completed_record_becomes_training_candidate(self):
        record = GameRecord(
            moves=(Move.pass_move(), Move.pass_move()),
            result="DRAW_CONSECUTIVE_PASS",
            source="self-play",
        )
        validation = self.validator.validate(record)
        self.assertEqual(validation.source_class, RecordSource.SELF_PLAY)
        self.assertEqual(validation.training_disposition, TrainingDisposition.CANDIDATE)

    def test_personal_completed_record_is_not_ground_truth(self):
        record = GameRecord(
            moves=(Move.pass_move(), Move.pass_move()),
            result="draw_consecutive_pass",
            source="personal",
        )
        validation = self.validator.validate(record)

        self.assertTrue(validation.complete)
        self.assertTrue(validation.result_consistent)
        self.assertTrue(validation.analysis_eligible)
        self.assertFalse(validation.training_eligible)
        self.assertEqual(validation.training_disposition, TrainingDisposition.EXCLUDED)

    def test_result_mismatch_is_excluded_from_training(self):
        record = GameRecord(
            moves=(Move.pass_move(), Move.pass_move()),
            result="CHO_WIN",
            source="curated-human",
        )
        validation = self.validator.validate(record)

        self.assertEqual(validation.status, ValidationStatus.RESULT_MISMATCH)
        self.assertFalse(validation.result_consistent)
        self.assertEqual(validation.terminal_status, GameStatus.DRAW_CONSECUTIVE_PASS)
        self.assertFalse(validation.training_eligible)
        self.assertIn("result_mismatch", validation.issues)

    def test_completed_record_without_result_is_not_training_candidate(self):
        record = GameRecord(
            moves=(Move.pass_move(), Move.pass_move()),
            source="curated-human",
        )
        validation = self.validator.validate(record)

        self.assertEqual(validation.status, ValidationStatus.RESULT_MISSING)
        self.assertFalse(validation.result_consistent)
        self.assertFalse(validation.training_eligible)
        self.assertIn("result_missing", validation.issues)

    def test_invalid_replay_is_structured_failure(self):
        record = GameRecord(
            moves=(Move((0, 0), (0, 5)),),
            source="curated-human",
        )
        validation = self.validator.validate(record)

        self.assertTrue(validation.structural_valid)
        self.assertFalse(validation.replay_valid)
        self.assertEqual(validation.status, ValidationStatus.INVALID_REPLAY)
        self.assertFalse(validation.analysis_eligible)
        self.assertFalse(validation.training_eligible)
        self.assertIsNone(validation.final_state)

    def test_invalid_structure_is_rejected_before_replay(self):
        record = GameRecord(
            moves=(Move((0, 0), (9, 0)),),
            source="curated-human",
        )
        validation = self.validator.validate(record)

        self.assertFalse(validation.structural_valid)
        self.assertFalse(validation.replay_valid)
        self.assertEqual(validation.status, ValidationStatus.INVALID_STRUCTURE)
        self.assertFalse(validation.analysis_eligible)
        self.assertFalse(validation.training_eligible)
        self.assertIn("position_out_of_bounds:0", validation.issues)

    def test_unknown_source_does_not_get_promoted_to_training_truth(self):
        record = GameRecord(
            moves=(Move.pass_move(), Move.pass_move()),
            result="draw_consecutive_pass",
            source="imported-file",
        )
        validation = self.validator.validate(record)

        self.assertEqual(validation.source_class, RecordSource.UNKNOWN)
        self.assertEqual(validation.status, ValidationStatus.UNKNOWN_SOURCE)
        self.assertFalse(validation.training_eligible)
        self.assertIn("unknown_source", validation.issues)

    def test_rule_set_can_change_terminal_classification(self):
        record = GameRecord(
            moves=(Move.pass_move(), Move.pass_move()),
            result="draw_consecutive_pass",
            source="self-play",
        )
        validator_without_pass_draw = RecordValidator(RuleSet(consecutive_passes_for_draw=None))
        validation = validator_without_pass_draw.validate(record)

        self.assertFalse(validation.complete)
        self.assertEqual(validation.terminal_status, GameStatus.PLAYING)
        self.assertEqual(validation.status, ValidationStatus.INCOMPLETE)
        self.assertFalse(validation.training_eligible)


if __name__ == "__main__":
    unittest.main()
