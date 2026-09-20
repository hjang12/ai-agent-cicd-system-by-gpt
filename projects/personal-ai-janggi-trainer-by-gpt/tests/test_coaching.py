import unittest

from janggi import CoachingReason
from janggi.analysis import MoveAnalysis, TacticalMotif, TacticalRisk
from janggi.coaching import CoachingSeverity, coach_move
from janggi.core import Move, PieceType, Side


class CoachingTests(unittest.TestCase):
    def _analysis(
        self,
        *,
        delta,
        best=False,
        recommendation=True,
        tactical_risk=TacticalRisk.NONE,
        tactical_motifs=(),
        moved_piece=None,
        captured_piece=None,
        gives_check=False,
        destination_attacked=False,
    ):
        move = Move((0, 3), (0, 4))
        recommended = move if best else Move((0, 6), (0, 5))
        if not recommendation:
            recommended = None
        return MoveAnalysis(
            move=move,
            recommended_move=recommended,
            score_before_cp=0 if delta is not None else None,
            score_after_cp=delta if delta is not None else None,
            score_delta_cp=delta,
            depth=2,
            nodes=10,
            perspective=Side.CHO,
            moved_piece=moved_piece,
            captured_piece=captured_piece,
            gives_check=gives_check,
            destination_attacked=destination_attacked,
            tactical_risk=tactical_risk,
            tactical_motifs=tactical_motifs,
        )

    def test_recommended_move(self):
        insight = coach_move(self._analysis(delta=0, best=True))
        self.assertEqual(insight.severity, CoachingSeverity.RECOMMENDED)
        self.assertIn("추천수", insight.message)
        self.assertIn("목적과 다음 진행", insight.next_action)
        self.assertEqual(insight.reason_codes, ())

    def test_recommended_capture_and_check_explain_both_features(self):
        insight = coach_move(
            self._analysis(delta=0, best=True, captured_piece=PieceType.SOLDIER, gives_check=True)
        )
        self.assertIn("잡기와 장군을 동시에", insight.message)
        self.assertIn("다음 반격", insight.next_action)
        self.assertEqual(
            insight.reason_codes,
            (CoachingReason.CAPTURE, CoachingReason.CHECK),
        )

    def test_recommended_tactical_motif_has_machine_readable_signal(self):
        insight = coach_move(
            self._analysis(
                delta=0,
                best=True,
                tactical_motifs=(TacticalMotif.DOUBLE_ATTACK,),
            )
        )
        self.assertEqual(insight.reason_codes, (CoachingReason.DOUBLE_ATTACK,))

    def test_acceptable_alternative(self):
        insight = coach_move(self._analysis(delta=-25))
        self.assertEqual(insight.severity, CoachingSeverity.ACCEPTABLE)
        self.assertIn("목적과 다음 진행", insight.next_action)
        self.assertEqual(insight.reason_codes, (CoachingReason.SCORE_DEVIATION,))

    def test_acceptable_alternative_encourages_comparison(self):
        insight = coach_move(self._analysis(delta=-25))
        self.assertIn("추천수와 무엇이 다른지", insight.message)

    def test_inaccuracy(self):
        insight = coach_move(self._analysis(delta=-26))
        self.assertEqual(insight.severity, CoachingSeverity.INACCURACY)
        self.assertIn("반격", insight.next_action)
        self.assertEqual(insight.reason_codes, (CoachingReason.SCORE_DEVIATION,))

    def test_inaccuracy_encourages_checking_counterplay(self):
        insight = coach_move(self._analysis(delta=-26))
        self.assertIn("반격을 한 수 더 확인", insight.message)

    def test_major_mistake(self):
        insight = coach_move(self._analysis(delta=-151))
        self.assertEqual(insight.severity, CoachingSeverity.MAJOR_MISTAKE)
        self.assertIn("즉각적인 반격", insight.next_action)
        self.assertEqual(insight.reason_codes, (CoachingReason.SCORE_DEVIATION,))

    def test_hanging_piece_is_explained_as_major_mistake(self):
        insight = coach_move(
            self._analysis(delta=-20, tactical_risk=TacticalRisk.HANGING_PIECE)
        )
        self.assertEqual(insight.severity, CoachingSeverity.MAJOR_MISTAKE)
        self.assertIn("전술 위험", insight.message)
        self.assertIn("잡을 수 있는 수를 먼저 확인", insight.message)
        self.assertIn("기물을 보호", insight.message)
        self.assertIn("기물 보호", insight.next_action)
        self.assertEqual(
            insight.reason_codes,
            (CoachingReason.HANGING_PIECE, CoachingReason.SCORE_DEVIATION),
        )

    def test_immediate_capture_risk_explanation_is_not_score_blended(self):
        insight = coach_move(
            self._analysis(delta=-20, tactical_risk=TacticalRisk.IMMEDIATE_CAPTURE)
        )
        self.assertEqual(insight.severity, CoachingSeverity.ACCEPTABLE)
        self.assertIn("바로 잡을 수 있습니다", insight.message)
        self.assertIn("되잡을 수 있는지", insight.message)
        self.assertIn("되잡", insight.next_action)
        self.assertEqual(
            insight.reason_codes,
            (CoachingReason.IMMEDIATE_CAPTURE, CoachingReason.SCORE_DEVIATION),
        )

    def test_large_score_loss_still_uses_score_classification_with_immediate_capture(self):
        insight = coach_move(
            self._analysis(delta=-151, tactical_risk=TacticalRisk.IMMEDIATE_CAPTURE)
        )
        self.assertEqual(insight.severity, CoachingSeverity.MAJOR_MISTAKE)
        self.assertIn("교환을 의도한 수라면", insight.message)
        self.assertIn("되잡", insight.next_action)
        self.assertEqual(
            insight.reason_codes,
            (CoachingReason.IMMEDIATE_CAPTURE, CoachingReason.SCORE_DEVIATION),
        )

    def test_feature_explanation_combines_move_facts(self):
        insight = coach_move(
            self._analysis(
                delta=-10,
                moved_piece=PieceType.CHARIOT,
                captured_piece=PieceType.SOLDIER,
                gives_check=True,
                tactical_risk=TacticalRisk.IMMEDIATE_CAPTURE,
                destination_attacked=True,
            )
        )
        self.assertIn("차를 이동했습니다", insight.message)
        self.assertIn("상대 졸/병을 잡았습니다", insight.message)
        self.assertIn("장군을 걸었습니다", insight.message)
        self.assertIn("바로 잡을 수 있습니다", insight.message)
        self.assertEqual(
            insight.reason_codes,
            (
                CoachingReason.IMMEDIATE_CAPTURE,
                CoachingReason.CAPTURE,
                CoachingReason.CHECK,
                CoachingReason.SCORE_DEVIATION,
            ),
        )

    def test_double_attack_motif_is_explained_without_changing_severity(self):
        insight = coach_move(
            self._analysis(
                delta=-20,
                tactical_motifs=(TacticalMotif.DOUBLE_ATTACK,),
            )
        )
        self.assertEqual(insight.severity, CoachingSeverity.ACCEPTABLE)
        self.assertIn("두 기물을 동시에 공격", insight.message)
        self.assertEqual(
            insight.reason_codes,
            (CoachingReason.DOUBLE_ATTACK, CoachingReason.SCORE_DEVIATION),
        )

    def test_unavailable_without_recommendation_keeps_available_feature_signals(self):
        insight = coach_move(
            self._analysis(
                delta=-300,
                recommendation=False,
                tactical_risk=TacticalRisk.HANGING_PIECE,
                gives_check=True,
            )
        )
        self.assertEqual(insight.severity, CoachingSeverity.UNAVAILABLE)
        self.assertIn("추천수가 생긴 뒤", insight.next_action)
        self.assertEqual(
            insight.reason_codes,
            (CoachingReason.HANGING_PIECE, CoachingReason.CHECK),
        )

    def test_unavailable_without_score_keeps_feature_reason_codes(self):
        insight = coach_move(
            self._analysis(
                delta=None,
                tactical_risk=TacticalRisk.IMMEDIATE_CAPTURE,
                captured_piece=PieceType.SOLDIER,
            )
        )
        self.assertEqual(insight.severity, CoachingSeverity.UNAVAILABLE)
        self.assertEqual(
            insight.reason_codes,
            (CoachingReason.IMMEDIATE_CAPTURE, CoachingReason.CAPTURE),
        )


if __name__ == "__main__":
    unittest.main()
