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
    TrainingSessionMetrics,
    adaptive_problem_priority,
    adaptive_reason_priority,
    generate_training_problems,
    select_adaptive_training_problems,
)


class TrainingProblemTests(unittest.TestCase):
    def _entry(self, ply, state, move, recommended, severity, reason=CoachingReason.SCORE_DEVIATION):
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
            reason_codes=(reason,),
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

    def _review(self, entries):
        return CoachingReview(
            total_moves=len(entries),
            reviewed_moves=len(entries),
            skipped_moves=0,
            entries=tuple(entries),
            reason_counts=(),
            severity_counts=(),
        )

    def test_generates_problem_from_non_recommended_move(self):
        state = GameState.initial(starting_side=Side.CHO)
        move = state.legal_moves(include_pass=False)[0]
        recommended = state.legal_moves(include_pass=False)[1]
        review = self._review((
            self._entry(1, state, move, recommended, CoachingSeverity.INACCURACY),
        ))

        problems = generate_training_problems(review, max_problems=5)

        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0].problem_id, "ply-1")
        self.assertEqual(problems[0].state, state)
        self.assertEqual(problems[0].target_move, recommended)
        self.assertEqual(problems[0].original_move, move)
        self.assertEqual(problems[0].reason_codes, (CoachingReason.SCORE_DEVIATION,))
        self.assertEqual(problems[0].side, Side.CHO)

    def test_skips_recommended_and_unavailable_entries(self):
        state = GameState.initial(starting_side=Side.CHO)
        first = state.legal_moves(include_pass=False)[0]
        second = state.legal_moves(include_pass=False)[1]
        recommended_entry = self._entry(1, state, first, first, CoachingSeverity.RECOMMENDED)
        unavailable_entry = self._entry(2, state, second, None, CoachingSeverity.UNAVAILABLE)
        review = self._review((recommended_entry, unavailable_entry))
        problems = generate_training_problems(review)
        self.assertEqual(problems, ())

    def test_problem_limit_is_bounded_and_boolean_rejected(self):
        review = self._review(())
        with self.assertRaises(ValueError):
            generate_training_problems(review, max_problems=21)
        with self.assertRaises(ValueError):
            generate_training_problems(review, max_problems=True)

    def test_problem_target_must_be_legal(self):
        state = GameState.initial(starting_side=Side.CHO)
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

    def test_adaptive_selection_prioritizes_low_accuracy_reasons(self):
        state = GameState.initial(starting_side=Side.CHO)
        legal = state.legal_moves(include_pass=False)
        entries = (
            self._entry(1, state, legal[0], legal[1], CoachingSeverity.INACCURACY, CoachingReason.SCORE_DEVIATION),
            self._entry(2, state, legal[1], legal[2], CoachingSeverity.INACCURACY, CoachingReason.HANGING_PIECE),
            self._entry(3, state, legal[2], legal[3], CoachingSeverity.INACCURACY, CoachingReason.DOUBLE_ATTACK),
            self._entry(4, state, legal[3], legal[4], CoachingSeverity.INACCURACY, CoachingReason.SCORE_DEVIATION),
        )
        problems = generate_training_problems(self._review(entries), max_problems=20)
        metrics = TrainingSessionMetrics()
        metrics.record_attempt(
            problem_id="ply-2", correct=False, reason_codes=(CoachingReason.HANGING_PIECE,)
        )
        metrics.record_attempt(
            problem_id="ply-1", correct=True, reason_codes=(CoachingReason.SCORE_DEVIATION,)
        )
        metrics.record_attempt(
            problem_id="ply-4", correct=False, reason_codes=(CoachingReason.SCORE_DEVIATION,)
        )
        metrics.record_attempt(
            problem_id="ply-4", correct=True, reason_codes=(CoachingReason.SCORE_DEVIATION,)
        )

        snapshot = metrics.snapshot()
        selected = select_adaptive_training_problems(
            problems, snapshot, max_problems=2
        )

        self.assertEqual([problem.problem_id for problem in selected], ["ply-4", "ply-2"])
        self.assertEqual(
            adaptive_reason_priority(snapshot),
            (CoachingReason.HANGING_PIECE, CoachingReason.SCORE_DEVIATION),
        )

    def test_adaptive_selection_prioritizes_repeated_problem_mistakes(self):
        state = GameState.initial(starting_side=Side.CHO)
        legal = state.legal_moves(include_pass=False)
        entries = (
            self._entry(1, state, legal[0], legal[1], CoachingSeverity.INACCURACY, CoachingReason.SCORE_DEVIATION),
            self._entry(2, state, legal[1], legal[2], CoachingSeverity.INACCURACY, CoachingReason.HANGING_PIECE),
            self._entry(3, state, legal[2], legal[3], CoachingSeverity.INACCURACY, CoachingReason.DOUBLE_ATTACK),
        )
        problems = generate_training_problems(self._review(entries), max_problems=20)
        metrics = TrainingSessionMetrics()
        metrics.record_attempt(
            problem_id="ply-3",
            correct=False,
            reason_codes=(CoachingReason.DOUBLE_ATTACK,),
        )
        metrics.record_attempt(
            problem_id="ply-3",
            correct=False,
            reason_codes=(CoachingReason.DOUBLE_ATTACK,),
        )
        metrics.record_attempt(
            problem_id="ply-2",
            correct=False,
            reason_codes=(CoachingReason.HANGING_PIECE,),
        )

        snapshot = metrics.snapshot()
        selected = select_adaptive_training_problems(
            problems, snapshot, max_problems=2
        )

        self.assertEqual(adaptive_problem_priority(snapshot), ("ply-3", "ply-2"))
        self.assertEqual([problem.problem_id for problem in selected], ["ply-3", "ply-2"])

    def test_adaptive_selection_bounds_repeated_mistake_share(self):
        state = GameState.initial(starting_side=Side.CHO)
        legal = state.legal_moves(include_pass=False)
        entries = tuple(
            self._entry(
                ply,
                state,
                legal[ply - 1],
                legal[ply],
                CoachingSeverity.INACCURACY,
                CoachingReason.HANGING_PIECE if ply <= 2 else CoachingReason.SCORE_DEVIATION,
            )
            for ply in range(1, 6)
        )
        problems = generate_training_problems(self._review(entries), max_problems=20)
        metrics = TrainingSessionMetrics()
        for problem_id in ("ply-5", "ply-4", "ply-3", "ply-2"):
            metrics.record_attempt(
                problem_id=problem_id,
                correct=False,
                reason_codes=(CoachingReason.HANGING_PIECE,),
            )

        selected = select_adaptive_training_problems(
            problems, metrics.snapshot(), max_problems=5
        )

        selected_ids = [problem.problem_id for problem in selected]
        self.assertEqual(selected_ids[:3], ["ply-2", "ply-3", "ply-4"])
        self.assertIn("ply-1", selected_ids)
        self.assertEqual(len(selected), 5)

    def test_adaptive_selection_mixes_unrepeated_reason_when_available(self):
        state = GameState.initial(starting_side=Side.CHO)
        legal = state.legal_moves(include_pass=False)
        entries = (
            self._entry(1, state, legal[0], legal[1], CoachingSeverity.INACCURACY, CoachingReason.HANGING_PIECE),
            self._entry(2, state, legal[1], legal[2], CoachingSeverity.INACCURACY, CoachingReason.SCORE_DEVIATION),
            self._entry(3, state, legal[2], legal[3], CoachingSeverity.INACCURACY, CoachingReason.DOUBLE_ATTACK),
            self._entry(4, state, legal[3], legal[4], CoachingSeverity.INACCURACY, CoachingReason.CHECK),
        )
        problems = generate_training_problems(self._review(entries), max_problems=20)
        metrics = TrainingSessionMetrics()
        metrics.record_attempt(
            problem_id="ply-4",
            correct=False,
            reason_codes=(CoachingReason.CHECK,),
        )
        metrics.record_attempt(
            problem_id="ply-3",
            correct=False,
            reason_codes=(CoachingReason.DOUBLE_ATTACK,),
        )
        metrics.record_attempt(
            problem_id="ply-3",
            correct=False,
            reason_codes=(CoachingReason.DOUBLE_ATTACK,),
        )

        selected = select_adaptive_training_problems(
            problems, metrics.snapshot(), max_problems=3
        )

        selected_ids = [problem.problem_id for problem in selected]
        self.assertEqual(selected_ids[0], "ply-3")
        self.assertIn("ply-2", selected_ids)
        self.assertEqual(len(selected), 3)

    def test_adaptive_selection_falls_back_to_recent_order_without_mistakes(self):
        state = GameState.initial(starting_side=Side.CHO)
        legal = state.legal_moves(include_pass=False)
        entries = (
            self._entry(1, state, legal[0], legal[1], CoachingSeverity.INACCURACY),
            self._entry(2, state, legal[1], legal[2], CoachingSeverity.INACCURACY),
            self._entry(3, state, legal[2], legal[3], CoachingSeverity.INACCURACY),
        )
        problems = generate_training_problems(self._review(entries), max_problems=20)

        selected = select_adaptive_training_problems(
            problems, TrainingSessionMetrics().snapshot(), max_problems=2
        )

        self.assertEqual([problem.problem_id for problem in selected], ["ply-3", "ply-2"])

    def test_adaptive_selection_limit_is_bounded_and_boolean_rejected(self):
        problems = ()
        metrics = TrainingSessionMetrics().snapshot()
        with self.assertRaises(ValueError):
            select_adaptive_training_problems(problems, metrics, max_problems=21)
        with self.assertRaises(ValueError):
            select_adaptive_training_problems(problems, metrics, max_problems=True)


if __name__ == "__main__":
    unittest.main()
