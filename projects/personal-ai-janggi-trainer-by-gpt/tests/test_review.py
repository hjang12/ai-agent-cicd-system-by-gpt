import unittest

from janggi import GameRecord, GameState, MoveAnalysis, Side, TacticalRisk, CoachingReason, CoachingSeverity, review_record


class StubAnalyzer:
    def __init__(self, analyses):
        self.analyses = analyses

    def analyze_move(self, state, move):
        return self.analyses[state.position_key()]


class ReviewTests(unittest.TestCase):
    def setUp(self):
        initial = GameState.initial(starting_side=Side.HAN)
        first = initial.legal_moves(include_pass=False)[0]
        after_first = initial.apply(first)
        second = after_first.legal_moves(include_pass=False)[0]
        self.record = GameRecord(setup="classic", moves=(first, second), source="personal")
        self.analysis = {
            initial.position_key(): MoveAnalysis(
                move=first,
                recommended_move=first,
                score_before_cp=0,
                score_after_cp=0,
                score_delta_cp=0,
                depth=2,
                nodes=10,
                perspective=Side.HAN,
            ),
            after_first.position_key(): MoveAnalysis(
                move=second,
                recommended_move=after_first.legal_moves(include_pass=False)[1],
                score_before_cp=0,
                score_after_cp=-200,
                score_delta_cp=-200,
                depth=2,
                nodes=10,
                perspective=Side.HAN,
                tactical_risk=TacticalRisk.HANGING_PIECE,
            ),
        }

    def test_review_aggregates_recent_moves(self):
        result = review_record(self.record, StubAnalyzer(self.analysis), max_moves=2)
        self.assertEqual(result.total_moves, 2)
        self.assertEqual(result.reviewed_moves, 2)
        self.assertEqual(result.skipped_moves, 0)
        self.assertEqual(len(result.entries), 2)
        self.assertEqual(result.reason_counts, ((CoachingReason.HANGING_PIECE, 1), (CoachingReason.SCORE_DEVIATION, 1)))
        self.assertEqual(
            result.severity_counts,
            ((CoachingSeverity.RECOMMENDED, 1), (CoachingSeverity.MAJOR_MISTAKE, 1)),
        )

    def test_review_limits_to_recent_moves_and_filters_learner_side(self):
        result = review_record(
            self.record,
            StubAnalyzer(self.analysis),
            max_moves=1,
            side=Side.CHO,
        )
        self.assertEqual(result.total_moves, 2)
        self.assertEqual(result.reviewed_moves, 1)
        self.assertEqual(result.skipped_moves, 0)
        self.assertEqual(result.entries[0].ply, 2)
        self.assertEqual(result.entries[0].side, Side.CHO)

    def test_review_reports_skipped_matching_moves(self):
        result = review_record(self.record, StubAnalyzer(self.analysis), max_moves=1)
        self.assertEqual(result.reviewed_moves, 1)
        self.assertEqual(result.skipped_moves, 1)
        self.assertEqual(result.entries[0].ply, 2)

    def test_review_rejects_unbounded_limit(self):
        with self.assertRaises(ValueError):
            review_record(self.record, StubAnalyzer(self.analysis), max_moves=61)

    def test_review_rejects_boolean_limit(self):
        with self.assertRaises(ValueError):
            review_record(self.record, StubAnalyzer(self.analysis), max_moves=True)

if __name__ == "__main__":
    unittest.main()
