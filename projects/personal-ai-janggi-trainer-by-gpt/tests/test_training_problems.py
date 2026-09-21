import unittest

from janggi import (
    CoachingInsight,
    CoachingReason,
    CoachingReview,
    CoachingSeverity,
    GameState,
    Move,
    MoveAnalysis,
    PositionTrainingProblem,
    Side,
    generate_training_problems,
)


class TrainingProblemTests(unittest.TestCase):
    def _entry(self, ply, state, move, recommended, severity):
        analysis = MoveAnalysis(
            move=move,
            recommended_move=recommended,
            score_before_cp=0,
            score_after_cp=-200 if severity is CoachingSeverity.MAJOR_MISTAKE else 0,
            score_delta_cp=-200 if severity is CoachingSeverity.MAJOR_MISTAKE else -25,
            depth=2,
            nodes=10,
            perspective=Side.CHO,
        )
        insight = CoachingInsight(
            severity=severity,
            message="테스트 설명",
            score_delta_cp=analysis.score_delta_cp,
            next_action="다음 수를 확인하세요.",
            reason_codes=(CoachingReason.SCORE_DEVIATION,),
        )
        from janggi.review import ReviewEntry
        return ReviewEntry(
            ply=ply,
            side=Side.CHO,
            state=state,
            move=move,
            analysis=analysis,
            insight=insight,
        )

    def test_generates_problem_from_non_recommended_move(self):
        state = GameState.initial()
        move = state.legal_moves(include_pass=False)[0]
        recommended = state.legal_moves(include_pass=False)[1]
        review = CoachingReview(
            total_moves=1,
            reviewed_moves=1,
            skipped_moves=0,
            entries=(self._entry(1, state, move, recommended, CoachingSeverity.INACCURACY),),
            reason_counts=((CoachingReason.SCORE_DEVIATION, 1),),
            severity_counts=((CoachingSeverity.INACCURACY, 1),),
        )

        problems = generate_training_problems(review, max_problems=5)

        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0].problem_id, "ply-1")
        self.assertEqual(problems[0].state, state)
        self.assertEqual(problems[0].target_move, recommended)
        self.assertEqual(problems[0].original_move, move)
        self.assertEqual(problems[0].reason_codes, (CoachingReason.SCORE_DEVIATION,))
        self.assertEqual(problems[0].side, Side.CHO)

    def test_skips_recommended_and_unavailable_entries(self):
        state = GameState.initial()
        first = state.legal_moves(include_pass=False)[0]
        second = state.legal_moves(include_pass=False)[1]
        recommended_entry = self._entry(1, state, first, first, CoachingSeverity.RECOMMENDED)
        unavailable_entry = self._entry(2, state, second, None, CoachingSeverity.UNAVAILABLE)
        review = CoachingReview(
            total_moves=2,
            reviewed_moves=2,
            skipped_moves=0,
            entries=(recommended_entry, unavailable_entry),
            reason_counts=(),
            severity_counts=(),
        )
        problems = generate_training_problems(review)
        self.assertEqual(problems, ())

    def test_problem_limit_is_bounded_and_boolean_rejected(self):
        review = CoachingReview(
            total_moves=0, reviewed_moves=0, skipped_moves=0, entries=(),
            reason_counts=(), severity_counts=(),
        )
        with self.assertRaises(ValueError):
            generate_training_problems(review, max_problems=21)
        with self.assertRaises(ValueError):
            generate_training_problems(review, max_problems=True)

    def test_problem_target_must_be_legal(self):
        state = GameState.initial()
        illegal = Move((0, 0), (8, 9))
        with self.assertRaises(ValueError):
            PositionTrainingProblem(
                problem_id="bad",
                ply=1,
                state=state,
                side=Side.CHO,
                target_move=illegal,
                original_move=state.legal_moves(include_pass=False)[0],
                severity=CoachingSeverity.INACCURACY,
                reason_codes=(),
                prompt="수",
                explanation="설명",
                next_action="다음 수",
            )


if __name__ == "__main__":
    unittest.main()
