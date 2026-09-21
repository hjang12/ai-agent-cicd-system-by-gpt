import unittest
from pathlib import Path

from app import TrainerApplication
from janggi import EngineAnalysis, Move, Side


INDEX_HTML = Path(__file__).resolve().parents[1] / "index.html"


class NonAnalysisEngine:
    def analyze(self, state):
        return None

    def choose_move(self, state):
        raise AssertionError("choose_move should not be called")

    @property
    def info(self):
        raise AssertionError("info should not be read")

class InvalidAnalysisEngine:
    def analyze(self, state):
        return EngineAnalysis(
            best_move=Move((0, 0), (8, 9)),
            principal_variation=(Move((0, 0), (8, 9)),),
            perspective=Side.CHO,
        )

    def choose_move(self, state):
        raise AssertionError("choose_move should not be called")

    @property
    def info(self):
        raise AssertionError("info should not be read")


class TrainerApplicationTests(unittest.TestCase):
    def test_initial_snapshot_is_playing(self):
        app = TrainerApplication()
        snapshot = app.snapshot()
        self.assertEqual(snapshot["status"], "playing")
        self.assertEqual(snapshot["setup"], "classic")
        self.assertEqual(len(snapshot["state"]["board"]), 90)
        self.assertTrue(snapshot["legal_moves"])

    def test_reset_accepts_setup_variant(self):
        app = TrainerApplication()
        snapshot = app.reset("left")
        self.assertEqual(snapshot["setup"], "left")
        self.assertEqual(snapshot["state"]["setup"], "left")

    def test_snapshot_exposes_player_and_ai_sides(self):
        app = TrainerApplication()
        snapshot = app.snapshot()
        self.assertEqual(snapshot["player_side"], "han")
        self.assertEqual(snapshot["ai_side"], "cho")

    def test_reset_han_starts_with_no_history(self):
        app = TrainerApplication()
        snapshot = app.reset(player_side="han")
        self.assertEqual(snapshot["player_side"], "han")
        self.assertEqual(snapshot["ai_side"], "cho")
        self.assertEqual(snapshot["state"]["turn"], "han")
        self.assertEqual(len(snapshot["state"]["history"]), 0)
        self.assertEqual(snapshot["can_undo"], False)

    def test_han_player_turn_starts_immediately(self):
        app = TrainerApplication()
        snapshot = app.reset(player_side="han")
        move = snapshot["legal_moves"][0]
        response = app.play_player_turn({"src": move["src"], "dst": move["dst"]})
        self.assertEqual(response["snapshot"]["state"]["turn"], "han")
        self.assertEqual(len(response["snapshot"]["state"]["history"]), 2)

    def test_han_ai_recovery_is_available_after_player_move(self):
        app = TrainerApplication()
        snapshot = app.reset(player_side="han")
        move = snapshot["legal_moves"][0]
        app.play({"src": move["src"], "dst": move["dst"]})
        self.assertEqual(app.snapshot()["state"]["turn"], "cho")
        response = app.engine_move()
        self.assertTrue(response["analysis"]["best_move"])
        self.assertEqual(response["snapshot"]["state"]["turn"], "han")

    def test_cho_player_gets_han_opening(self):
        app = TrainerApplication()
        snapshot = app.reset(player_side="cho")
        self.assertEqual(snapshot["player_side"], "cho")
        self.assertEqual(snapshot["ai_side"], "han")
        self.assertEqual(snapshot["state"]["turn"], "cho")
        self.assertEqual(len(snapshot["state"]["history"]), 1)

        move = snapshot["legal_moves"][0]
        response = app.play_player_turn({"src": move["src"], "dst": move["dst"]})
        self.assertEqual(response["snapshot"]["state"]["turn"], "cho")
        self.assertEqual(len(response["snapshot"]["state"]["history"]), 3)

    def test_cho_player_causes_han_ai_to_open(self):
        app = TrainerApplication()
        snapshot = app.reset(player_side="cho")
        self.assertEqual(snapshot["state"]["turn"], "cho")
        self.assertEqual(len(snapshot["state"]["history"]), 1)
        self.assertEqual(snapshot["state"]["history"][0].src, (0, 6))
        self.assertEqual(snapshot["state"]["history"][0].dst, (0, 5))

        move = snapshot["legal_moves"][0]
        response = app.play_player_turn({"src": move["src"], "dst": move["dst"]})
        self.assertEqual(response["snapshot"]["state"]["turn"], "cho")
        self.assertEqual(len(response["snapshot"]["state"]["history"]), 3)

    def test_reset_rejects_unknown_player_side(self):
        app = TrainerApplication()
        with self.assertRaises(ValueError):
            app.reset(player_side="unknown")

    def test_play_rejects_missing_coordinates(self):
        app = TrainerApplication()
        with self.assertRaises(ValueError):
            app.play({"src": [0, 3]})

    def test_analyze_move_does_not_change_state(self):
        app = TrainerApplication()
        before = app.snapshot()
        response = app.analyze_move({"src": [0, 6], "dst": [0, 5]})
        self.assertIn("analysis", response)
        self.assertEqual(response["analysis"]["move"]["src"], [0, 3])
        self.assertEqual(response["analysis"]["move"]["dst"], [0, 4])
        self.assertEqual(response["snapshot"]["state"], before["state"])

    def test_analyze_move_reports_recommendation_coaching_tactical_risk_and_pv(self):
        app = TrainerApplication()
        response = app.analyze_move({"src": [0, 6], "dst": [0, 5]})
        self.assertIn("recommended_move", response["analysis"])
        self.assertIn("score_delta_cp", response["analysis"])
        self.assertIn("is_best_move", response["analysis"])
        self.assertIn("tactical_risk", response["analysis"])
        self.assertIn("tactical_motifs", response["analysis"])
        self.assertIn("principal_variation", response["analysis"])
        self.assertIsInstance(response["analysis"]["principal_variation"], list)
        self.assertIn("severity", response["coaching"])
        self.assertIn("message", response["coaching"])
        self.assertIn("next_action", response["coaching"])
        self.assertTrue(response["coaching"]["next_action"])
        self.assertIn("reason_codes", response["coaching"])
        self.assertIsInstance(response["coaching"]["reason_codes"], list)

    def test_player_turn_applies_human_move_and_ai_response(self):
        app = TrainerApplication()
        move = app.snapshot()["legal_moves"][0]

        response = app.play_player_turn({"src": move["src"], "dst": move["dst"]})

        self.assertIn("player_analysis", response)
        self.assertIn("player_coaching", response)
        self.assertIn("engine_analysis", response)
        self.assertTrue(response["engine_analysis"]["best_move"])
        self.assertIn("snapshot", response)
        self.assertEqual(response["snapshot"]["state"]["turn"], "han")
        self.assertEqual(len(response["snapshot"]["state"]["history"]), 2)

    def test_engine_move_returns_analysis_and_updates_state(self):
        app = TrainerApplication()
        player_move = app.snapshot()["legal_moves"][0]
        app.play({"src": player_move["src"], "dst": player_move["dst"]})
        before = app.snapshot()["state"]["turn"]

        response = app.engine_move()

        self.assertIn("analysis", response)
        self.assertIn("principal_variation", response["analysis"])
        self.assertIsInstance(response["analysis"]["principal_variation"], list)
        self.assertIn("snapshot", response)
        self.assertNotEqual(response["snapshot"]["state"]["turn"], before)
        self.assertEqual(len(response["snapshot"]["state"]["history"]), 2)

    def test_engine_move_rejects_player_turn(self):
        app = TrainerApplication()
        with self.assertRaises(ValueError):
            app.engine_move()

    def test_engine_move_degrades_non_analysis_engine_output(self):
        app = TrainerApplication()
        player_move = app.snapshot()["legal_moves"][0]
        app.play({"src": player_move["src"], "dst": player_move["dst"]})
        app.engine = NonAnalysisEngine()
        before = app.snapshot()

        response = app.engine_move()

        self.assertIsNone(response["analysis"]["best_move"])
        self.assertEqual(response["analysis"]["principal_variation"], [])
        self.assertEqual(response["snapshot"]["state"], before["state"])
    def test_engine_move_suppresses_malformed_engine_analysis(self):
        app = TrainerApplication()
        player_move = app.snapshot()["legal_moves"][0]
        app.play({"src": player_move["src"], "dst": player_move["dst"]})
        app.engine = InvalidAnalysisEngine()
        before = app.snapshot()

        response = app.engine_move()

        self.assertIsNone(response["analysis"]["best_move"])
        self.assertEqual(response["analysis"]["principal_variation"], [])
        self.assertEqual(response["snapshot"]["state"], before["state"])

    def test_review_aggregates_current_learner_moves(self):
        app = TrainerApplication()
        app.play({"src": [0, 6], "dst": [0, 5]})

        review = app.review({"limit": 5})

        self.assertEqual(review["total_moves"], 1)
        self.assertEqual(review["reviewed_moves"], 1)
        self.assertEqual(review["skipped_moves"], 0)
        self.assertIsInstance(review["reason_counts"], dict)
        self.assertIsInstance(review["severity_counts"], dict)
        self.assertEqual(len(review["entries"]), 1)
        self.assertEqual(review["entries"][0]["ply"], 1)
        self.assertEqual(review["entries"][0]["side"], "han")
        self.assertIn("reason_codes", review["entries"][0])

    def test_review_rejects_invalid_limit(self):
        app = TrainerApplication()
        with self.assertRaises(ValueError):
            app.review({"limit": 61})

    def test_training_problems_returns_bounded_problem_collection(self):
        app = TrainerApplication()
        result = app.training_problems({"review_limit": 5, "problem_limit": 5})
        self.assertIn("reviewed_moves", result)
        self.assertIn("problem_count", result)
        self.assertIsInstance(result["problems"], list)
        self.assertLessEqual(result["problem_count"], 5)

    def test_training_problems_do_not_expose_solution_by_default(self):
        app = TrainerApplication()
        result = app.training_problems({"review_limit": 5, "problem_limit": 5})
        for problem in result["problems"]:
            self.assertIn("state", problem)
            self.assertIn("legal_moves", problem)
            self.assertNotIn("target_move", problem)

    def test_training_problem_answer_rejects_unknown_problem(self):
        app = TrainerApplication()
        with self.assertRaises(ValueError):
            app.training_problem_answer({
                "problem_id": "missing",
                "src": [0, 3],
                "dst": [0, 4],
            })

    def test_record_exports_current_history(self):
        app = TrainerApplication()
        record = app.record()
        self.assertEqual(record["format"], "janggi-record-v1")
        self.assertEqual(record["setup"], "classic")
        self.assertEqual(record["source"], "personal")
        self.assertIsNone(record["result"])
        self.assertEqual(record["moves"], [])

    def test_record_exports_played_moves(self):
        app = TrainerApplication()
        app.play({"src": [0, 6], "dst": [0, 5]})
        record = app.record()
        self.assertEqual(len(record["moves"]), 1)
        self.assertEqual(record["moves"][0]["src"], [0, 6])
        self.assertEqual(record["moves"][0]["dst"], [0, 5])

    def test_undo_restores_previous_player_turn(self):
        app = TrainerApplication()
        initial = app.snapshot()
        move = initial["legal_moves"][0]
        app.play_player_turn({"src": move["src"], "dst": move["dst"]})
        undone = app.undo()
        self.assertEqual(undone["state"], initial["state"])
        self.assertEqual(undone["status"], "playing")

    def test_undo_without_history_is_rejected(self):
        app = TrainerApplication()
        with self.assertRaises(ValueError):
            app.undo()

    def test_browser_makes_turn_handoff_explicit_in_heading(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn("AI가 응수했습니다 · 내 차례", html)
        self.assertIn("AI 응수가 필요합니다 · AI 수 두기", html)
        self.assertIn("post('/api/player/turn', move)", html)
    def test_browser_localizes_terminal_status_and_engine_heading(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn("'cho_win':'초 승'", html)
        self.assertIn("'draw_consecutive_pass':'연속 한수쉼 무승부'", html)
        self.assertIn("statusLabels[snapshot.status] || snapshot.status", html)
        self.assertIn("로 대국이 종료되었습니다", html)

    def test_browser_engine_result_surfaces_evaluation_and_search_details(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn("result.score_cp === null || result.score_cp === undefined", html)
        self.assertIn("cp (${sideLabels[result.perspective] || result.perspective || '기준'} 기준)", html)
        self.assertIn("탐색 깊이 ${result.depth}.", html)
        self.assertIn("확인한 노드 ${result.nodes.toLocaleString()}개.", html)
    def test_browser_move_presentation_uses_board_notation(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn("function formatPosition(position)", html)
        self.assertIn("String.fromCharCode(97 + x)", html)
        self.assertIn("(index + 1) + '. ' + label + ' ' + formatMove(move)", html)
        self.assertIn("formatPrincipalVariation(result.principal_variation, result.perspective)", html)
        self.assertNotIn("move.src.join(',')", html)

    def test_training_metrics_are_available_and_reset_with_match(self):
        app = TrainerApplication()
        initial = app.training_metrics_snapshot()
        self.assertEqual(initial["attempts"], 0)
        self.assertEqual(initial["accuracy"], 0.0)

        metrics = app.training_metrics_snapshot()
        self.assertEqual(metrics["reason_attempts"], {})
        self.assertEqual(metrics["problem_attempts"], {})
        self.assertEqual(metrics["problem_incorrect"], {})

        app.reset("classic")
        self.assertEqual(app.training_metrics_snapshot()["attempts"], 0)

    def test_browser_position_training_contract_is_present(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('id="training"', html)
        self.assertIn('id="training-panel"', html)
        self.assertIn("post('/api/training/problems', {review_limit: 20, problem_limit: 5})", html)
        self.assertIn("post('/api/training/answer', {", html)
        self.assertIn("포지션 훈련 문제 준비 완료", html)
        self.assertIn("훈련 정답", html)
        self.assertIn("정답률", html)
        self.assertIn("renderTrainingMetrics(result.metrics)", html)
        self.assertIn("accuracy", html)
        self.assertIn("reasonAccuracySummary", html)
        self.assertIn("reason_correct", html)
        self.assertIn("problem_incorrect", html)
        self.assertIn("다른 문제도 함께 섞었습니다", html)
        self.assertIn("priority_reason_codes", html)
        self.assertIn("priority_problem_ids", html)
        self.assertIn("반복 오답 문제", html)
        self.assertIn("problem_incorrect", html)
        self.assertIn("낮은 정답률 reason", html)

    def test_browser_session_review_contract_is_present(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('id="review"', html)
        self.assertIn('id="review-panel"', html)
        self.assertIn("post('/api/review', {limit: 20})", html)
        self.assertIn("최근 대국 복기 완료", html)
        self.assertIn("reasonLabels", html)
        self.assertIn("reviewDetails", html)

    def test_browser_undo_contract_is_present(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('id="undo"', html)
        self.assertIn('class="analysis-row analysis-pv"', html)
        self.assertIn("undo.disabled = busy || !canUndo", html)
        self.assertIn("engine.disabled = busy || snapshot?.status !== 'playing' || snapshot?.state?.turn !== snapshot?.ai_side", html)
        self.assertIn("function displayToState(x, y)", html)
        self.assertIn("return boardSide() === 'cho' ? [8 - x, 9 - y] : [x, y];", html)
        self.assertIn("cell.addEventListener('click', () => clickCell(x, y));", html)
        self.assertIn("const [stateX, stateY] = displayToState(x, y)", html)
        self.assertIn("legalDestination(selected, [stateX, stateY])", html)
        self.assertIn("const move = {src:selected, dst:[stateX, stateY]};", html)
        self.assertIn("if (selected[0] === stateX && selected[1] === stateY)", html)
        self.assertIn("post('/api/undo', {})", html)
        self.assertIn("내 한 턴 되돌리기 완료", html)


if __name__ == "__main__":
    unittest.main()

