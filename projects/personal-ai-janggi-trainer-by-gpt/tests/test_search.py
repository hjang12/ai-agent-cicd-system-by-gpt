import unittest

from janggi import GameState, Move, Piece, PieceType, Side
from janggi.search import MATE_SCORE, NegamaxEngine, PIECE_VALUES, SearchConfig


class SearchEngineTests(unittest.TestCase):
    def test_search_config_validates_depth(self):
        with self.assertRaises(ValueError):
            SearchConfig(depth=0)
        with self.assertRaises(ValueError):
            SearchConfig(mobility_weight=-1)
        with self.assertRaises(ValueError):
            SearchConfig(quiescence_depth=-1)
        with self.assertRaises(ValueError):
            SearchConfig(root_refinement_count=-1)
        with self.assertRaises(ValueError):
            SearchConfig(time_limit_ms=0)

    def test_search_config_validates_variant_flags(self):
        with self.assertRaises(ValueError):
            SearchConfig(adaptive_ordering=1)
        with self.assertRaises(ValueError):
            SearchConfig(quiescence_check_extension=0)

        current = SearchConfig()
        self.assertTrue(current.adaptive_ordering)
        self.assertTrue(current.quiescence_check_extension)

    def test_piece_values_follow_janggi_material_order(self):
        self.assertEqual(PIECE_VALUES[PieceType.CHARIOT], 1300)
        self.assertEqual(PIECE_VALUES[PieceType.CANNON], 700)
        self.assertEqual(PIECE_VALUES[PieceType.HORSE], 500)
        self.assertEqual(PIECE_VALUES[PieceType.ELEPHANT], 300)
        self.assertEqual(PIECE_VALUES[PieceType.GUARD], 300)
        self.assertEqual(PIECE_VALUES[PieceType.SOLDIER], 200)

    def test_evaluation_rewards_advanced_center_soldier(self):
        board = [None] * 90
        board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
        board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        board[4 + 3 * 9] = Piece(Side.CHO, PieceType.SOLDIER)
        early = GameState(tuple(board), turn=Side.CHO)

        board[4 + 3 * 9] = None
        board[4 + 5 * 9] = Piece(Side.CHO, PieceType.SOLDIER)
        advanced = GameState(tuple(board), turn=Side.CHO)

        engine = NegamaxEngine(SearchConfig(depth=1, mobility_weight=0))

        self.assertGreater(engine._evaluate(advanced), engine._evaluate(early))

    def test_evaluation_penalizes_opponent_advanced_center_soldier(self):
        board = [None] * 90
        board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
        board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        board[4 + 6 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
        quiet = GameState(tuple(board), turn=Side.CHO)

        board[4 + 6 * 9] = None
        board[4 + 4 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
        advanced = GameState(tuple(board), turn=Side.CHO)

        engine = NegamaxEngine(SearchConfig(depth=1, mobility_weight=0, quiescence_depth=0))

        self.assertGreater(engine._evaluate(quiet), engine._evaluate(advanced))

    def test_evaluation_rewards_check_pressure(self):
        quiet_board = [None] * 90
        quiet_board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
        quiet_board[4 + 9 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        quiet_board[3 + 7 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
        quiet = GameState(tuple(quiet_board), turn=Side.CHO)

        checking_board = list(quiet_board)
        checking_board[3 + 7 * 9] = None
        checking_board[4 + 7 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
        checking = GameState(tuple(checking_board), turn=Side.CHO)

        self.assertFalse(quiet.is_in_check(Side.HAN))
        self.assertTrue(checking.is_in_check(Side.HAN))

        engine = NegamaxEngine(SearchConfig(depth=1, mobility_weight=0))

        self.assertGreaterEqual(
            engine._evaluate(checking) - engine._evaluate(quiet),
            80,
        )

    def test_activity_score_rewards_unblocked_major_piece(self):
        board = [None] * 90
        board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
        board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        board[1 + 2 * 9] = Piece(Side.CHO, PieceType.HORSE)
        board[1 + 1 * 9] = Piece(Side.CHO, PieceType.SOLDIER)
        blocked = GameState(tuple(board), turn=Side.CHO)

        board[1 + 1 * 9] = None
        unblocked = GameState(tuple(board), turn=Side.CHO)

        engine = NegamaxEngine(SearchConfig(depth=1, mobility_weight=0))
        blocked_moves = engine._legal_moves(blocked, include_pass=False)
        unblocked_moves = engine._legal_moves(unblocked, include_pass=False)

        self.assertGreater(
            engine._activity_score_for_state(unblocked, Side.CHO, unblocked_moves),
            engine._activity_score_for_state(blocked, Side.CHO, blocked_moves),
        )

    def test_capture_pressure_rewards_immediate_material_threat(self):
        board = [None] * 90
        board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
        board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
        board[0 + 4 * 9] = Piece(Side.HAN, PieceType.CANNON)
        threatened = GameState(tuple(board), turn=Side.CHO)

        board[0 + 4 * 9] = None
        quiet = GameState(tuple(board), turn=Side.CHO)

        engine = NegamaxEngine(SearchConfig(depth=1, mobility_weight=0))
        threatened_moves = engine._legal_moves(threatened, include_pass=False)
        quiet_moves = engine._legal_moves(quiet, include_pass=False)

        self.assertGreater(
            engine._capture_pressure(threatened_moves, threatened),
            engine._capture_pressure(quiet_moves, quiet),
        )

    def test_palace_pressure_rewards_reaching_opponent_palace(self):
        board = [None] * 90
        board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
        board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        board[4 + 5 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
        pressured = GameState(tuple(board), turn=Side.CHO)

        board[4 + 5 * 9] = None
        board[0 + 5 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
        quiet = GameState(tuple(board), turn=Side.CHO)

        engine = NegamaxEngine(SearchConfig(depth=1, mobility_weight=0))
        pressured_moves = engine._legal_moves(pressured, include_pass=False)
        quiet_moves = engine._legal_moves(quiet, include_pass=False)

        self.assertGreater(
            engine._palace_pressure(pressured_moves, Side.HAN),
            engine._palace_pressure(quiet_moves, Side.HAN),
        )

    def test_evaluation_penalizes_vulnerable_chariot(self):
        board = [None] * 90
        board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
        board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        board[0 + 4 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
        board[0 + 8 * 9] = Piece(Side.HAN, PieceType.CHARIOT)
        exposed = GameState(tuple(board), turn=Side.CHO)

        board[0 + 4 * 9] = None
        board[1 + 4 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
        safe = GameState(tuple(board), turn=Side.CHO)

        engine = NegamaxEngine(SearchConfig(depth=1, mobility_weight=0, quiescence_depth=0))

        safe_han_moves = engine._legal_moves(safe, include_pass=False)
        exposed_han_moves = engine._legal_moves(exposed, include_pass=False)
        self.assertGreater(
            engine._capture_pressure(exposed_han_moves, exposed),
            engine._capture_pressure(safe_han_moves, safe),
        )

    def test_iterative_deepening_completes_tiny_position_with_time_budget(self):
        board = [None] * 90
        board[4] = Piece(Side.CHO, PieceType.GENERAL)
        board[85] = Piece(Side.HAN, PieceType.GENERAL)
        board[4 + 4 * 9] = Piece(Side.CHO, PieceType.SOLDIER)
        state = GameState(tuple(board), turn=Side.CHO)

        engine = NegamaxEngine(
            SearchConfig(
                depth=2,
                mobility_weight=0,
                quiescence_depth=0,
                time_limit_ms=1000,
            )
        )
        analysis = engine.analyze(state)

        self.assertEqual(analysis.depth, 2)
        self.assertIsNotNone(analysis.best_move)
        self.assertTrue(state.is_legal(analysis.best_move))
        self.assertGreater(analysis.nodes, 0)
        self.assertEqual(analysis.principal_variation[0], analysis.best_move)

    def test_negamax_exposes_metadata_and_returns_legal_move(self):
        state = GameState.initial()
        engine = NegamaxEngine(SearchConfig(depth=1))

        analysis = engine.analyze(state)

        self.assertEqual(analysis.perspective, Side.CHO)
        self.assertEqual(analysis.depth, 1)
        self.assertGreater(analysis.nodes, 0)
        self.assertIsNotNone(analysis.best_move)
        self.assertTrue(state.is_legal(analysis.best_move))
        self.assertEqual(engine.choose_move(state), analysis.best_move)

    def test_root_refinement_is_deterministic_and_reports_effective_depth(self):
        board = [None] * 90
        board[4] = Piece(Side.CHO, PieceType.GENERAL)
        board[85] = Piece(Side.HAN, PieceType.GENERAL)
        board[36] = Piece(Side.CHO, PieceType.CHARIOT)
        board[46] = Piece(Side.CHO, PieceType.CHARIOT)
        board[35] = Piece(Side.CHO, PieceType.SOLDIER)
        board[81] = Piece(Side.HAN, PieceType.CHARIOT)
        state = GameState(tuple(board), turn=Side.CHO)

        shallow = NegamaxEngine(SearchConfig(depth=2, root_refinement_count=0))
        refined = NegamaxEngine(SearchConfig(depth=2, root_refinement_count=3))
        deep = NegamaxEngine(SearchConfig(depth=3, root_refinement_count=0))

        shallow_analysis = shallow.analyze(state)
        refined_analysis = refined.analyze(state)
        deep_analysis = deep.analyze(state)

        self.assertIsNotNone(shallow_analysis.best_move)
        self.assertIsNotNone(refined_analysis.best_move)
        self.assertIsNotNone(deep_analysis.best_move)
        self.assertEqual(refined_analysis.score_cp, deep_analysis.score_cp)
        self.assertEqual(refined_analysis.score_cp, 99997)
        self.assertTrue(state.is_legal(refined_analysis.best_move))
        self.assertEqual(refined_analysis.depth, 3)
        self.assertGreater(refined_analysis.nodes, shallow_analysis.nodes)
        self.assertLess(refined_analysis.nodes, deep_analysis.nodes)

    def test_root_refinement_zero_preserves_base_depth(self):
        state = GameState.initial()
        base = NegamaxEngine(SearchConfig(depth=2, root_refinement_count=0))
        explicit_zero = NegamaxEngine(SearchConfig(depth=2, root_refinement_count=0))

        first = base.analyze(state)
        second = explicit_zero.analyze(state)

        self.assertEqual(first, second)
        self.assertEqual(first.depth, 2)

    def test_negamax_is_deterministic(self):
        state = GameState.initial()
        engine = NegamaxEngine(SearchConfig(depth=2))

        first = engine.analyze(state)
        second = engine.analyze(state)

        self.assertEqual(first.best_move, second.best_move)
        self.assertEqual(first.score_cp, second.score_cp)
        self.assertEqual(first.principal_variation, second.principal_variation)

    def test_principal_variation_starts_with_best_move(self):
        state = GameState.initial()
        engine = NegamaxEngine(SearchConfig(depth=2))

        analysis = engine.analyze(state)

        self.assertIsNotNone(analysis.best_move)
        self.assertTrue(analysis.principal_variation)
        self.assertEqual(analysis.principal_variation[0], analysis.best_move)
        self.assertLessEqual(
            len(analysis.principal_variation),
            analysis.depth + engine.config.quiescence_depth,
        )

    def test_quiescence_extension_is_configurable(self):
        state = GameState.initial()

        without_extension = NegamaxEngine(SearchConfig(depth=1, quiescence_depth=0))
        with_extension = NegamaxEngine(SearchConfig(depth=1, quiescence_depth=1))

        first = without_extension.analyze(state)
        second = with_extension.analyze(state)

        self.assertIsNotNone(first.best_move)
        self.assertIsNotNone(second.best_move)
        self.assertGreaterEqual(second.nodes, first.nodes)
        self.assertLessEqual(len(second.principal_variation), 2)

    def test_evaluation_cache_reuses_position_result(self):
        state = GameState.initial()
        engine = NegamaxEngine(SearchConfig(depth=1))

        first = engine._evaluate(state)
        cache_size_after_first = len(engine._evaluation_cache)
        second = engine._evaluate(state)

        self.assertEqual(first, second)
        self.assertEqual(cache_size_after_first, 1)
        self.assertEqual(len(engine._evaluation_cache), 1)

    def test_legal_move_cache_reuses_result(self):
        state = GameState.initial()
        engine = NegamaxEngine(SearchConfig(depth=1))

        first = engine._legal_moves(state, include_pass=False)
        cache_size_after_first = len(engine._legal_moves_cache)
        second = engine._legal_moves(state, include_pass=False)

        self.assertEqual(first, second)
        self.assertEqual(cache_size_after_first, 1)
        self.assertEqual(len(engine._legal_moves_cache), 1)

    def test_legal_move_cache_separates_pass_policy(self):
        state = GameState.initial()
        engine = NegamaxEngine(SearchConfig(depth=1))

        without_pass = engine._legal_moves(state, include_pass=False)
        with_pass = engine._legal_moves(state, include_pass=True)

        self.assertFalse(without_pass[-1].is_pass)
        self.assertTrue(with_pass[-1].is_pass)
        self.assertEqual(len(engine._legal_moves_cache), 2)

    def test_transposition_lower_bound_reuse_preserves_full_window_score(self):
        board = [None] * 90
        board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
        board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
        board[0 + 4 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
        state = GameState(tuple(board), turn=Side.CHO)

        engine = NegamaxEngine(SearchConfig(depth=1, mobility_weight=0, quiescence_depth=0))
        narrow_score, _ = engine._search(state, 1, -100, 100)
        entry = engine._transposition[(state.position_key(), 1, False)]

        self.assertGreaterEqual(narrow_score, 100)
        self.assertEqual(entry.bound, "lower")

        reused_score, _ = engine._search(state, 1, -MATE_SCORE * 2, MATE_SCORE * 2)
        reference_engine = NegamaxEngine(SearchConfig(depth=1, mobility_weight=0, quiescence_depth=0))
        reference_score, _ = reference_engine._search(
            state, 1, -MATE_SCORE * 2, MATE_SCORE * 2
        )

        self.assertEqual(reused_score, reference_score)
        self.assertGreater(engine._tt_hits, 0)

    def test_transposition_upper_bound_reuse_preserves_full_window_score(self):
        board = [None] * 90
        board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
        board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
        board[0 + 4 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
        state = GameState(tuple(board), turn=Side.CHO)

        reference_engine = NegamaxEngine(SearchConfig(depth=1, mobility_weight=0, quiescence_depth=0))
        reference_score, _ = reference_engine._search(
            state, 1, -MATE_SCORE * 2, MATE_SCORE * 2
        )

        engine = NegamaxEngine(SearchConfig(depth=1, mobility_weight=0, quiescence_depth=0))
        upper_score, _ = engine._search(
            state,
            1,
            reference_score + 1,
            reference_score + 100,
        )
        entry = engine._transposition[(state.position_key(), 1, False)]

        self.assertLessEqual(upper_score, reference_score + 1)
        self.assertEqual(entry.bound, "upper")

        reused_score, _ = engine._search(state, 1, -MATE_SCORE * 2, MATE_SCORE * 2)
        self.assertEqual(reused_score, reference_score)

    def test_analysis_returns_no_move_for_truly_terminal_position(self):
        board = [None] * 90
        board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        state = GameState(tuple(board), turn=Side.CHO)
        engine = NegamaxEngine(SearchConfig(depth=1))

        analysis = engine.analyze(state)

        self.assertIsNone(analysis.best_move)
        self.assertLess(analysis.score_cp, 0)

    def test_checkmate_score_does_not_depend_on_history_length(self):
        board = [None] * 90
        board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        empty_history_state = GameState(tuple(board), turn=Side.CHO)
        history_state = GameState(
            tuple(board),
            turn=Side.CHO,
            history=(Move.pass_move(), Move.pass_move(), Move.pass_move()),
        )
        engine = NegamaxEngine(SearchConfig(depth=3))

        empty_history_score, _ = engine._search(
            empty_history_state, 1, -MATE_SCORE * 2, MATE_SCORE * 2
        )
        history_score, _ = engine._search(
            history_state, 1, -MATE_SCORE * 2, MATE_SCORE * 2
        )

        self.assertEqual(empty_history_score, history_score)

    def test_quiescence_variant_flag_can_reproduce_pre_v2_check_horizon(self):
        board = [None] * 90
        board[0] = Piece(Side.CHO, PieceType.GENERAL)
        board[4 + 9 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
        board[8] = Piece(Side.CHO, PieceType.HORSE)
        state = GameState(tuple(board), turn=Side.CHO)
        checked_state = state.apply(Move((0, 3), (4, 3)))
        self.assertTrue(checked_state.is_in_check(Side.HAN))

        v1 = NegamaxEngine(
            SearchConfig(
                depth=1,
                quiescence_depth=1,
                adaptive_ordering=False,
                quiescence_check_extension=False,
            )
        )
        v2 = NegamaxEngine(
            SearchConfig(
                depth=1,
                quiescence_depth=1,
                adaptive_ordering=True,
                quiescence_check_extension=True,
            )
        )

        v1._evaluate = lambda current_state: 1_000 if current_state is checked_state else 0
        v2._evaluate = lambda current_state: 1_000 if current_state is checked_state else 0

        v1_score, _ = v1._quiescence(
            checked_state,
            0,
            -MATE_SCORE * 2,
            100,
        )
        v2_score, v2_pv = v2._quiescence(
            checked_state,
            0,
            -MATE_SCORE * 2,
            100,
        )

        self.assertEqual(v1_score, 1_000)
        self.assertEqual(v2_score, 0)
        self.assertTrue(v2_pv)

    def test_quiescence_extends_check_evasion_at_horizon(self):
        board = [None] * 90
        board[0] = Piece(Side.CHO, PieceType.GENERAL)
        board[4 + 9 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
        board[8] = Piece(Side.CHO, PieceType.HORSE)
        state = GameState(tuple(board), turn=Side.CHO)

        checking_move = Move((0, 3), (4, 3))
        checked_state = state.apply(checking_move)
        self.assertTrue(checked_state.is_in_check(Side.HAN))
        self.assertTrue(checked_state.legal_moves(include_pass=False))

        engine = NegamaxEngine(SearchConfig(depth=1, quiescence_depth=0))
        original_evaluate = engine._evaluate
        engine._evaluate = lambda current_state: 1_000 if current_state is checked_state else 0
        try:
            score, principal_variation = engine._quiescence(
                checked_state,
                0,
                -MATE_SCORE * 2,
                100,
            )
        finally:
            engine._evaluate = original_evaluate

        self.assertEqual(score, 0)
        self.assertTrue(principal_variation)
    def test_search_can_prefer_a_free_capture(self):
        board = [None] * 90
        board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
        board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
        board[0 + 4 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
        state = GameState(tuple(board), turn=Side.CHO)
        engine = NegamaxEngine(SearchConfig(depth=1, mobility_weight=0))

        analysis = engine.analyze(state)

        self.assertEqual(analysis.best_move, Move((0, 3), (0, 4)))

    def test_adaptive_ordering_prefers_killer_before_history_for_quiet_moves(self):
        state = GameState.initial()
        engine = NegamaxEngine(SearchConfig(depth=2, mobility_weight=0, quiescence_depth=0))
        quiet_moves = tuple(
            move
            for move in state.legal_moves(include_pass=False)
            if engine._captured_value(state, move) == 0
            and not engine._gives_check(state, move)
        )
        self.assertGreaterEqual(len(quiet_moves), 3)
        history_move = quiet_moves[0]
        killer_move = quiet_moves[1]

        engine._history_scores[(state.turn, history_move)] = 100
        engine._killer_moves[0] = [killer_move]
        ordered = engine._ordered_search_moves(
            state,
            quiet_moves[:3],
            preferred_move=None,
            depth=engine.config.depth,
        )

        self.assertEqual(ordered[0], killer_move)
        self.assertGreater(engine._killer_hits, 0)

    def test_adaptive_ordering_uses_history_for_non_killer_quiet_moves(self):
        state = GameState.initial()
        engine = NegamaxEngine(SearchConfig(depth=2, mobility_weight=0, quiescence_depth=0))
        quiet_moves = tuple(
            move
            for move in state.legal_moves(include_pass=False)
            if engine._captured_value(state, move) == 0
            and not engine._gives_check(state, move)
        )
        self.assertGreaterEqual(len(quiet_moves), 2)
        preferred_history_move = quiet_moves[1]

        engine._history_scores[(state.turn, preferred_history_move)] = 50
        ordered = engine._ordered_search_moves(
            state,
            quiet_moves[:2],
            preferred_move=None,
            depth=engine.config.depth,
        )

        self.assertEqual(ordered[0], preferred_history_move)
        self.assertGreater(engine._history_hits, 0)

    def test_ordered_moves_put_captures_first(self):
        board = [None] * 90
        board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
        board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
        board[0 + 4 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
        board[2 + 3 * 9] = Piece(Side.CHO, PieceType.HORSE)
        state = GameState(tuple(board), turn=Side.CHO)
        moves = state.legal_moves(include_pass=False)

        engine = NegamaxEngine(SearchConfig(depth=1))
        ordered = engine._ordered_moves(state, moves)

        capture_values = [
            PIECE_VALUES[state.piece_at(move.dst).kind] if move.dst is not None and state.piece_at(move.dst) else 0
            for move in ordered
        ]
        self.assertEqual(capture_values[0], PIECE_VALUES[PieceType.SOLDIER])
        self.assertTrue(all(
            capture_values[index] >= capture_values[index + 1]
            for index in range(len(capture_values) - 1)
        ))

    def test_ordered_moves_prioritize_check_after_equal_capture_value(self):
        board = [None] * 90
        board[0] = Piece(Side.CHO, PieceType.GENERAL)
        board[4 + 9 * 9] = Piece(Side.HAN, PieceType.GENERAL)
        board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
        board[8] = Piece(Side.CHO, PieceType.HORSE)
        state = GameState(tuple(board), turn=Side.CHO)

        check_move = Move((0, 3), (4, 3))
        quiet_move = Move((8, 0), (7, 2))
        self.assertTrue(state.is_legal(check_move))
        self.assertTrue(state.is_legal(quiet_move))
        self.assertFalse(state.apply(check_move).is_in_check(Side.CHO))
        self.assertTrue(state.apply(check_move).is_in_check(Side.HAN))
        self.assertFalse(state.apply(quiet_move).is_in_check(Side.HAN))

        engine = NegamaxEngine(SearchConfig(depth=1))
        ordered = engine._ordered_moves(state, (quiet_move, check_move))

        self.assertEqual(ordered[0], check_move)


if __name__ == "__main__":
    unittest.main()
