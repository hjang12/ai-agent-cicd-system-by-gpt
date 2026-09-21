import unittest

from janggi import CoachingReason, TrainingSessionMetrics


class TrainingMetricsTests(unittest.TestCase):
    def test_empty_metrics_are_zeroed(self):
        metrics = TrainingSessionMetrics().snapshot()
        self.assertEqual(metrics.attempts, 0)
        self.assertEqual(metrics.correct, 0)
        self.assertEqual(metrics.incorrect, 0)
        self.assertEqual(metrics.unique_problems, 0)
        self.assertEqual(metrics.accuracy, 0.0)
        self.assertEqual(metrics.reason_attempts, ())

    def test_records_attempts_and_reason_counts(self):
        session = TrainingSessionMetrics()
        session.record_attempt(
            problem_id="ply-3",
            correct=False,
            reason_codes=(CoachingReason.HANGING_PIECE, CoachingReason.SCORE_DEVIATION),
        )
        session.record_attempt(
            problem_id="ply-3",
            correct=True,
            reason_codes=(CoachingReason.HANGING_PIECE,),
        )
        snapshot = session.snapshot()
        self.assertEqual(snapshot.attempts, 2)
        self.assertEqual(snapshot.correct, 1)
        self.assertEqual(snapshot.incorrect, 1)
        self.assertEqual(snapshot.unique_problems, 1)
        self.assertEqual(snapshot.accuracy, 0.5)
        self.assertEqual(
            snapshot.reason_attempts,
            ((CoachingReason.HANGING_PIECE, 2), (CoachingReason.SCORE_DEVIATION, 1)),
        )
        self.assertEqual(
            snapshot.reason_correct,
            ((CoachingReason.HANGING_PIECE, 1),),
        )

    def test_reset_clears_session_metrics(self):
        session = TrainingSessionMetrics()
        session.record_attempt(problem_id="ply-1", correct=True, reason_codes=())
        session.reset()
        self.assertEqual(session.snapshot().attempts, 0)

    def test_invalid_attempt_inputs_are_rejected(self):
        session = TrainingSessionMetrics()
        with self.assertRaises(ValueError):
            session.record_attempt(problem_id="", correct=True, reason_codes=())
        with self.assertRaises(ValueError):
            session.record_attempt(problem_id="ply-1", correct=1, reason_codes=())


if __name__ == "__main__":
    unittest.main()
