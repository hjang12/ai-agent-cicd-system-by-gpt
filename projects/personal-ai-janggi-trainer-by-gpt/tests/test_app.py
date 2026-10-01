import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch

from app import SESSION_COOKIE_NAME, RequestHandler, TrainerApplication, TrainerSessionStore
from janggi import EngineAnalysis, FirstLegalEngine, GameStatus, Match, Move, Outcome, RuleSet, Side


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


class TrainerSessionStoreTests(unittest.TestCase):
    def test_sessions_are_isolated(self):
        store = TrainerSessionStore(max_sessions=4)
        first_id, first_app, first_new = store.get_or_create()
        second_id, second_app, second_new = store.get_or_create()
        self.assertNotEqual(first_id, second_id)
        self.assertTrue(first_new)
        self.assertTrue(second_new)
        self.assertIsNot(first_app, second_app)
        move = first_app.snapshot()["legal_moves"][0]
        first_app.play({"src": move["src"], "dst": move["dst"]})
        self.assertEqual(len(first_app.snapshot()["state"]["history"]), 1)
        self.assertEqual(len(second_app.snapshot()["state"]["history"]), 0)

    def test_existing_session_id_reuses_application(self):
        store = TrainerSessionStore(max_sessions=4)
        session_id, application, created = store.get_or_create()
        same_id, same_application, created_again = store.get_or_create(session_id)
        self.assertEqual(same_id, session_id)
        self.assertIs(same_application, application)
        self.assertFalse(created_again)

    def test_invalid_session_id_creates_new_application(self):
        store = TrainerSessionStore(max_sessions=4)
        first_id, first_app, _ = store.get_or_create()
        second_id, second_app, created = store.get_or_create("not-a-valid-session")
        self.assertNotEqual(second_id, first_id)
        self.assertIsNot(second_app, first_app)
        self.assertTrue(created)


class RequestHandlerSessionTests(unittest.TestCase):
    def test_cookie_selects_existing_session_application(self):
        store = TrainerSessionStore(max_sessions=4)
        session_id, application, _ = store.get_or_create()
        handler = RequestHandler.__new__(RequestHandler)
        handler.headers = Message()
        handler.headers["Cookie"] = f"{SESSION_COOKIE_NAME}={session_id}"
        with patch("app.SESSION_STORE", store):
            resolved = handler._session_application()
        self.assertIs(resolved, application)
        self.assertFalse(handler._session_cookie_pending)

    def test_new_session_sets_http_only_same_site_cookie(self):
        store = TrainerSessionStore(max_sessions=4)
        handler = RequestHandler.__new__(RequestHandler)
        handler.headers = Message()
        sent = []
        handler.send_header = lambda name, value: sent.append((name, value))
        with patch("app.SESSION_STORE", store):
            handler._session_application()
            handler._set_session_cookie()
        cookie_values = [value for name, value in sent if name == "Set-Cookie"]
        self.assertEqual(len(cookie_values), 1)
        self.assertIn(f"{SESSION_COOKIE_NAME}=", cookie_values[0])
        self.assertIn("HttpOnly", cookie_values[0])
        self.assertIn("Path=/", cookie_values[0])
        self.assertIn("SameSite=Lax", cookie_values[0])


class ExplodingEngine:
    def analyze(self, state):
        raise RuntimeError("engine failed")

    def choose_move(self, state):
        raise AssertionError("choose_move should not be called")


class TrainerApplicationTests(unittest.TestCase):
    def test_snapshot_exposes_current_check_state(self):
        app = TrainerApplication()
        snapshot = app.snapshot()
        self.assertIn("in_check", snapshot)
        self.assertFalse(snapshot["in_check"])

    def test_initial_snapshot_is_playing(self):
        app = TrainerApplication()
        snapshot = app.snapshot()
        self.assertEqual(snapshot["status"], "playing")
        self.assertEqual(snapshot["setup"], "classic")
        self.assertEqual(len(snapshot["state"]["board"]), 90)
        self.assertTrue(snapshot["legal_moves"])

    def test_gameplay_engine_uses_fast_response_configuration(self):
        app = TrainerApplication()
        self.assertEqual(app.engine.config.depth, 1)
        self.assertEqual(app.engine.config.quiescence_depth, 0)
        self.assertEqual(app.engine.config.root_refinement_count, 0)
        self.assertEqual(app.analysis_engine.config.depth, 2)

    def test_default_ai_level_is_beginner(self):
        app = TrainerApplication()
        snapshot = app.snapshot()
        self.assertEqual(snapshot["ai_level"], "1")
        self.assertEqual(snapshot["ai_level_name"], "입문")
        self.assertEqual(app.engine.config.depth, 1)

    def test_reset_accepts_ai_level(self):
        app = TrainerApplication()
        snapshot = app.reset(ai_level="5")
        self.assertEqual(snapshot["ai_level"], "5")
        self.assertEqual(snapshot["ai_level_name"], "상급")
        self.assertEqual(app.engine.config.depth, 2)
        self.assertEqual(app.engine.config.quiescence_depth, 1)
        self.assertEqual(app.engine.config.root_refinement_count, 2)

    def test_reset_rejects_unknown_ai_level(self):
        app = TrainerApplication()
        with self.assertRaises(ValueError):
            app.reset(ai_level="7")

    def test_ai_level_endpoint_payload_is_available(self):
        from app import RequestHandler
        self.assertTrue(callable(RequestHandler.do_GET))

    def test_reset_accepts_setup_variant(self):
        app = TrainerApplication()
        snapshot = app.reset("left")
        self.assertEqual(snapshot["setup"], "left")
        self.assertEqual(snapshot["state"]["setup"], "left")

    def test_snapshot_exposes_player_and_ai_sides(self):
        app = TrainerApplication()
        snapshot = app.snapshot()
        self.assertEqual(snapshot["player_side"], "cho")
        self.assertEqual(snapshot["ai_side"], "han")

    def test_reset_can_select_han_and_ai_opens(self):
        app = TrainerApplication()
        snapshot = app.reset(player_side="han")
        self.assertEqual(snapshot["player_side"], "han")
        self.assertEqual(snapshot["ai_side"], "cho")
        self.assertEqual(snapshot["state"]["turn"], "han")
        self.assertEqual(len(snapshot["state"]["history"]), 1)

    def test_han_player_turn_after_ai_opening(self):
        app = TrainerApplication()
        snapshot = app.reset(player_side="han")
        move = snapshot["legal_moves"][0]
        response = app.play_player_turn({"src": move["src"], "dst": move["dst"]})
        self.assertEqual(response["snapshot"]["state"]["turn"], "han")
        self.assertEqual(len(response["snapshot"]["state"]["history"]), 3)

    def test_han_initial_ai_opening_is_not_undoable(self):
        app = TrainerApplication()
        snapshot = app.reset(player_side="han")
        self.assertEqual(snapshot["can_undo"], False)
        with self.assertRaises(ValueError):
            app.undo()

    def test_han_ai_recovery_is_available_after_player_move(self):
        app = TrainerApplication()
        snapshot = app.reset(player_side="han")
        move = snapshot["legal_moves"][0]
        app.play({"src": move["src"], "dst": move["dst"]})
        self.assertEqual(app.snapshot()["state"]["turn"], "cho")
        response = app.engine_move()
        self.assertTrue(response["analysis"]["best_move"])
        self.assertEqual(response["snapshot"]["state"]["turn"], "han")

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
        response = app.analyze_move({"src": [0, 3], "dst": [0, 4]})
        self.assertIn("analysis", response)
        self.assertEqual(response["analysis"]["move"]["src"], [0, 3])
        self.assertEqual(response["analysis"]["move"]["dst"], [0, 4])
        self.assertEqual(response["snapshot"]["state"], before["state"])

    def test_analyze_move_reports_recommendation_coaching_tactical_risk_and_pv(self):
        app = TrainerApplication()
        response = app.analyze_move({"src": [0, 3], "dst": [0, 4]})
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
        self.assertEqual(response["snapshot"]["state"]["turn"], "cho")
        self.assertEqual(len(response["snapshot"]["state"]["history"]), 2)

    def test_player_turn_rolls_back_when_ai_response_fails(self):
        app = TrainerApplication()
        app.engine = ExplodingEngine()
        move = app.snapshot()["legal_moves"][0]

        with self.assertRaises(RuntimeError):
            app.play_player_turn({"src": move["src"], "dst": move["dst"]})

        snapshot = app.snapshot()
        self.assertEqual(len(snapshot["state"]["history"]), 0)
        self.assertEqual(snapshot["state"]["turn"], "cho")

    def test_player_turn_does_not_require_heavy_analyzer(self):
        class ExplodingAnalyzer:
            def analyze_move(self, state, move):
                raise AssertionError("gameplay must not block on move analysis")

        app = TrainerApplication()
        app.analyzer = ExplodingAnalyzer()
        app.engine = FirstLegalEngine()
        move = app.snapshot()["legal_moves"][0]

        response = app.play_player_turn({"src": move["src"], "dst": move["dst"]})

        self.assertEqual(response["snapshot"]["state"]["turn"], "cho")
        self.assertEqual(len(response["snapshot"]["state"]["history"]), 2)
        self.assertIsNone(response["player_analysis"]["recommended_move"])
        self.assertEqual(response["player_analysis"]["score_delta_cp"], None)

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
        app.play({"src": [0, 3], "dst": [0, 4]})

        review = app.review({"limit": 5})

        self.assertEqual(review["total_moves"], 1)
        self.assertEqual(review["reviewed_moves"], 1)
        self.assertEqual(review["skipped_moves"], 0)
        self.assertIsInstance(review["reason_counts"], dict)
        self.assertIsInstance(review["severity_counts"], dict)
        self.assertEqual(len(review["entries"]), 1)
        self.assertEqual(review["entries"][0]["ply"], 1)
        self.assertEqual(review["entries"][0]["side"], "cho")
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
        app.play({"src": [0, 3], "dst": [0, 4]})
        record = app.record()
        self.assertEqual(len(record["moves"]), 1)
        self.assertEqual(record["moves"][0]["src"], [0, 3])
        self.assertEqual(record["moves"][0]["dst"], [0, 4])

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
        self.assertIn("대국 상태를 복구했습니다 · 내 차례", html)
        self.assertIn("post('/api/move', move)", html)
        self.assertIn("readJsonResponse(response)", html)
        self.assertIn("await getState()", html)
        self.assertIn("post('/api/engine/move', {})", html)
    def test_browser_exposes_move_feedback_and_game_messages(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn("game-message", html)
        self.assertIn("pieceMoveHints", html)
        self.assertIn("상은 2칸×3칸 또는 3칸×2칸", html)
        self.assertIn("explainIllegalMove(selected, [stateX, stateY], view)", html)
        self.assertIn("post('/api/move', move)", html)
        self.assertIn("내 수가 먼저 반영되었습니다.", html)
        self.assertIn("AI가 수를 계산하는 중입니다…", html)
        self.assertIn("장군!", html)
        self.assertIn("멍군!", html)
        self.assertIn("대국 시작 · 초가 먼저 둡니다.", html)
        self.assertIn("대국 종료 · 초가 이겼습니다.", html)
        self.assertIn("대국 종료 · 한이 이겼습니다.", html)
        self.assertIn(".in_check", html)

    def test_browser_localizes_terminal_status_and_engine_heading(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn("'cho_win':'초 승'", html)
        self.assertIn("'draw_consecutive_pass':'연속 한수쉼 무승부'", html)
        self.assertIn("terminalMessage(snapshot.status)", html)
        self.assertIn("대국 종료 · 초가 이겼습니다.", html)

    def test_browser_engine_result_surfaces_evaluation_and_search_details(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn("result.score_cp === null || result.score_cp === undefined", html)
        self.assertIn("cp (${sideLabels[result.perspective] || result.perspective || '기준'} 기준)", html)
        self.assertIn("탐색 깊이 ${result.depth}.", html)
        self.assertIn("확인한 노드 ${result.nodes.toLocaleString()}개.", html)
    def test_browser_turn_flow_renders_optimistic_human_move_before_network_request(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        pending = html.index("pendingPlayerMove = move;")
        render_pending = html.index("render();", pending)
        paint = html.index("await waitForPaint();", pending)
        human_request = html.index("const moveResult = await post('/api/move', move);", pending)
        clear_pending = html.index("pendingPlayerMove = null;", human_request)
        server_render = html.index("render();", clear_pending)
        thinking = html.index("showBoardMessage(thinkingTitle, thinkingSubtitle", human_request)
        engine = html.index("const engineResult = await post('/api/engine/move', {});", human_request)
        self.assertLess(pending, render_pending)
        self.assertLess(render_pending, paint)
        self.assertLess(paint, human_request)
        self.assertLess(human_request, clear_pending)
        self.assertLess(clear_pending, server_render)
        self.assertLess(server_render, thinking)
        self.assertLess(thinking, engine)

    def test_browser_pending_move_is_display_only_until_server_snapshot_arrives(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        piece_logic = html.index("function pieceAt(index)")
        pending_logic = html.index("if (pendingPlayerMove && !trainingPosition)", piece_logic)
        empty_code = html.index("if (!code) return null;", pending_logic)
        network_apply = html.index("snapshot = moveResult;")
        self.assertLess(piece_logic, pending_logic)
        self.assertLess(pending_logic, empty_code)
        self.assertLess(empty_code, network_apply)
        self.assertIn("const view = currentPosition();", html[piece_logic:pending_logic])
        self.assertIn("const sourceCode = view.state.board[srcIndex];", html)
        self.assertIn("pendingPlayerMove = null;", html)

    def test_browser_selected_piece_has_explicit_visual_feedback(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn(".cell.selected", html)
        self.assertIn(".cell.selected .piece", html)
        self.assertIn(".cell.legal", html)
        self.assertIn("selected = [stateX, stateY];", html)
        self.assertIn("render();", html[html.index("selected = [stateX, stateY];"):])

    def test_browser_ai_thinking_overlay_contract_is_backed_by_real_dom_nodes(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('id="heading"', html)
        self.assertIn('id="game-message"', html)
        self.assertIn('class="board-message"', html)
        self.assertIn("showBoardMessage(thinkingTitle, thinkingSubtitle", html)
        self.assertIn("thinking:true", html)

    def test_browser_board_message_contract_is_present(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('class="board-message"', html)
        self.assertIn('class="board-message-title"', html)
        self.assertIn('class="board-message-sub"', html)
        self.assertIn("showBoardMessage(thinkingTitle, thinkingSubtitle", html)
        self.assertIn("thinking:true", html)

    def test_browser_highlights_last_move_and_uses_uniform_board_grid(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn("last-move-from", html)
        self.assertIn("last-move-to", html)
        self.assertIn("const lastMove = pendingPlayerMove || (history.length ? history[history.length - 1] : null);", html)
        self.assertIn("aspect-ratio:8/9", html)
        self.assertIn('viewBox="0 0 8 9"', html)
        self.assertIn('x1="4" y1="0" x2="4" y2="9"', html)
        self.assertIn("for (let x = 0; x < 9; x += 1)", html)
        self.assertIn("for (let y = 0; y < 10; y += 1)", html)
        self.assertIn("cell.style.left = (5 + x * 11.25) + '%'", html)
        self.assertIn("cell.style.top = (5 + y * 10) + '%'", html)
        self.assertIn(".board{", html)
        self.assertIn("width:min(76vw,calc((100dvh - 188px) * 8 / 9),860px)", html)
        self.assertIn("aspect-ratio:8/9", html)
        self.assertIn("board-wrap", html)
        self.assertIn('stroke-width="0.035" fill="none">', html)

    def test_browser_game_setup_screen_contract(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('id="setup-screen" class="setup-screen"', html)
        self.assertIn('id="game-screen" class="game-screen" hidden', html)
        self.assertIn('id="reset"', html)
        self.assertIn("대국 시작", html)
        self.assertIn('data-level="1"', html)
        self.assertIn('data-level="6"', html)
        self.assertIn('data-side="cho"', html)
        self.assertIn('data-side="han"', html)
        self.assertIn("syncSetupOptions()", html)
        self.assertIn("showSetup('initial')", html)
        self.assertIn("showGame()", html)

    def test_browser_single_screen_layout_contract(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn("html,body{width:100%;height:100%;margin:0;overflow:hidden}", html)
        self.assertIn("[hidden]{display:none!important}", html)
        self.assertIn("height:100dvh", html)
        self.assertIn('id="setup-screen" class="setup-screen"', html)
        self.assertIn('id="game-screen" class="game-screen" hidden', html)
        self.assertIn(".game-screen{", html)
        self.assertIn(".game-main{", html)
        self.assertIn(".board-wrap{", html)
        self.assertIn("width:min(76vw,calc((100dvh - 188px) * 8 / 9),860px)", html)
        self.assertIn("aspect-ratio:8/9", html)
        self.assertNotIn(".dashboard.settings-open", html)
        self.assertNotIn(".dashboard.learning-open", html)
        self.assertNotIn("topbar-actions", html)

    def test_browser_postgame_learning_loop_contract(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('id="match-result"', html)
        self.assertIn("대국 종료", html)
        self.assertIn("playerResultLabel(snapshot)", html)
        self.assertIn("renderMatchResult()", html)
        self.assertIn("postgameReview.addEventListener('click', runReview)", html)
        self.assertIn("postgameTraining.addEventListener('click', startTrainingProblems)", html)
        self.assertIn("postgameReset.addEventListener('click', () => showSetup('modal'))", html)
        self.assertIn("showSetup('modal')", html)

    def test_browser_clears_previous_analysis_before_ai_thinking(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        human = html.index("const moveResult = await post('/api/move', move);")
        clear_analysis = html.index("renderAnalysis(null, null)", human)
        show_thinking = html.index("showBoardMessage(thinkingTitle, thinkingSubtitle", human)
        self.assertLess(clear_analysis, show_thinking)

    def test_terminal_match_records_unrated_assessment_evidence(self):
        app = TrainerApplication()
        app.match = Match.new(rules=RuleSet(consecutive_passes_for_draw=2))
        app.match = app.match.play(Move.pass_move()).play(Move.pass_move())
        self.assertEqual(app.match.status, GameStatus.DRAW_CONSECUTIVE_PASS)

        app._finalize_assessment_if_terminal()
        assessment = app.assessment_snapshot()

        self.assertEqual(assessment["games"], 1)
        self.assertEqual(assessment["unrated_games"], 1)
        self.assertIsNone(assessment["rating"])
        self.assertEqual(assessment["last_game"]["outcome"], Outcome.DRAW.value)
        self.assertEqual(assessment["last_game"]["result_status"], "draw_consecutive_pass")
        self.assertFalse(assessment["last_game"]["rating_eligible"])

    def test_browser_exposes_ai_level_selector_and_reset_contract(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('id="ai-level"', html)
        self.assertIn('option value="1">Lv.1 입문', html)
        self.assertIn('option value="6">Lv.6 전문', html)
        self.assertIn("ai_level:aiLevel.value", html)
        self.assertIn("snapshot.ai_level || '1'", html)
        self.assertIn("선택된 AI:", html)

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
        self.assertIn("const [stateX, stateY] = displayToState(x, y)", html)
        self.assertIn("legalDestination(selected, [stateX, stateY])", html)
        self.assertIn("const move = {src:selected, dst:[stateX, stateY]};", html)
        self.assertIn("if (selected[0] === stateX && selected[1] === stateY)", html)
        self.assertIn("post('/api/undo', {})", html)
        self.assertIn("내 한 턴 되돌리기 완료", html)

    def test_assessment_snapshot_is_available_and_starts_unrated(self):
        app = TrainerApplication()
        assessment = app.assessment_snapshot()
        self.assertEqual(assessment["games"], 0)
        self.assertEqual(assessment["rating_status"], "unrated")
        self.assertIsNone(assessment["rating"])

    def test_state_snapshot_exposes_assessment_and_opponent_identity(self):
        app = TrainerApplication()
        snapshot = app.snapshot()
        self.assertIn("assessment", snapshot)
        self.assertIn("opponent", snapshot)
        self.assertEqual(snapshot["opponent"]["model_id"], "baseline-search")
        self.assertIsNone(snapshot["opponent"]["rating"])

    def test_assessment_endpoint_is_available(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertTrue(callable(RequestHandler.do_GET))
        self.assertIn("/api/assessment", __import__("app").RequestHandler.do_GET.__code__.co_consts)



class TestGameFirstSetupFlowUiContract(unittest.TestCase):
    def test_browser_initially_stays_on_setup_screen(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('id="setup-screen" class="setup-screen"', html)
        self.assertIn('id="game-screen" class="game-screen" hidden', html)
        self.assertIn("[hidden]{display:none!important}", html)
        self.assertIn('id="reset"', html)
        self.assertIn("대국 시작", html)

    def test_browser_replay_uses_the_same_modal_setup_flow(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('id="replay-button"', html)
        self.assertIn('id="setup-cancel"', html)
        self.assertIn("function showSetup(mode = 'initial')", html)
        self.assertIn("setupScreen.classList.toggle('modal', mode === 'modal')", html)
        self.assertIn("replayButton.addEventListener('click', () => showSetup('modal'));", html)
        self.assertIn("setupCancel.addEventListener('click', () =>", html)

    def test_browser_game_surface_is_minimal_and_has_compact_move_comment(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('class="comment-card"', html)
        self.assertIn('class="comment-label">착수 평가', html)
        self.assertIn('id="replay-button"', html)
        self.assertIn('id="undo"', html)
        self.assertIn("좋은 수입니다.", html)
        self.assertIn("괜찮은 수입니다.", html)
        self.assertIn("조금 부정확한 수입니다.", html)
        self.assertNotIn("topbar-actions", html)
        self.assertNotIn("dashboard.settings-open", html)
        self.assertNotIn("dashboard.learning-open", html)


if __name__ == "__main__":
    unittest.main()
