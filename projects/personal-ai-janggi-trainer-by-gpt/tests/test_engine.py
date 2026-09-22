import unittest

from janggi import GameState, Move, Side
from janggi.engine import (
    EngineAnalysis,
    EngineInfo,
    FirstLegalEngine,
    principal_variation_is_legal,
    validate_engine_analysis,
    validate_engine_move,
)


class JanggiEngineTests(unittest.TestCase):
    def test_first_legal_engine_exposes_metadata(self):
        engine = FirstLegalEngine()
        self.assertEqual(engine.info, EngineInfo(name="first-legal", version="1"))

    def test_first_legal_engine_returns_legal_non_pass_move(self):
        state = GameState.initial()
        engine = FirstLegalEngine()
        move = engine.choose_move(state)
        self.assertFalse(move.is_pass)
        self.assertTrue(state.is_legal(move))
        self.assertEqual(move, state.legal_moves(include_pass=False)[0])

    def test_validate_engine_move_rejects_illegal_result(self):
        state = GameState.initial()
        illegal = Move((0, 3), (0, 2))
        with self.assertRaises(ValueError):
            validate_engine_move(FirstLegalEngine(), state, illegal)

    def test_analysis_uses_current_turn_as_perspective(self):
        state = GameState.initial()
        analysis = FirstLegalEngine().analyze(state)
        self.assertIsInstance(analysis, EngineAnalysis)
        self.assertEqual(analysis.perspective, Side.CHO)
        self.assertEqual(analysis.best_move, state.legal_moves(include_pass=True)[0])

    def test_principal_variation_legality_is_checked_step_by_step(self):
        state = GameState.initial()
        first = state.legal_moves(include_pass=False)[0]
        next_state = state.apply(first)
        second = next_state.legal_moves(include_pass=False)[0]
        self.assertTrue(principal_variation_is_legal(state, (first, second)))
        self.assertFalse(principal_variation_is_legal(state, (first, Move((0, 3), (0, 2)))))

    def test_validate_engine_analysis_suppresses_bad_perspective_and_metadata(self):
        state = GameState.initial()
        move = state.legal_moves(include_pass=False)[0]
        analysis = EngineAnalysis(
            best_move=move,
            score_cp="bad",  # type: ignore[arg-type]
            depth=-1,
            nodes=True,  # type: ignore[arg-type]
            principal_variation=(move,),
            perspective="cho",  # type: ignore[arg-type]
        )

        normalized = validate_engine_analysis(state, analysis)

        self.assertIsNone(normalized.best_move)
        self.assertEqual(normalized.principal_variation, ())
        self.assertIsNone(normalized.score_cp)
        self.assertIsNone(normalized.depth)
        self.assertIsNone(normalized.nodes)
        self.assertEqual(normalized.perspective, Side.CHO)
    def test_validate_engine_analysis_rejects_opposite_valid_side(self):
        state = GameState.empty(turn=Side.CHO)
        move = Move((4, 0), (4, 1))
        analysis = EngineAnalysis(
            best_move=move,
            score_cp=25,
            depth=1,
            nodes=1,
            principal_variation=(move,),
            perspective=Side.HAN,
        )

        normalized = validate_engine_analysis(state, analysis)

        self.assertEqual(normalized, EngineAnalysis(perspective=Side.CHO))

    def test_validate_engine_analysis_degrades_non_analysis_output(self):
        state = GameState.initial()

        normalized = validate_engine_analysis(state, None)

        self.assertIsInstance(normalized, EngineAnalysis)
        self.assertIsNone(normalized.best_move)
        self.assertEqual(normalized.principal_variation, ())
        self.assertEqual(normalized.perspective, Side.CHO)
    def test_validate_engine_analysis_suppresses_illegal_best_move_and_pv(self):
        state = GameState.initial()
        invalid_move = Move((0, 3), (0, 2))
        analysis = EngineAnalysis(
            best_move=invalid_move,
            score_cp=25,
            depth=2,
            nodes=10,
            principal_variation=(invalid_move,),
            perspective=Side.CHO,
        )

        normalized = validate_engine_analysis(state, analysis)

        self.assertIsNone(normalized.best_move)
        self.assertEqual(normalized.principal_variation, ())
        self.assertEqual(normalized.score_cp, 25)
        self.assertEqual(normalized.depth, 2)
        self.assertEqual(normalized.nodes, 10)
        self.assertEqual(normalized.perspective, Side.CHO)

    def test_validate_engine_analysis_suppresses_pv_when_first_move_disagrees(self):
        state = GameState.initial()
        best = state.legal_moves(include_pass=False)[0]
        alternative = state.legal_moves(include_pass=False)[1]
        analysis = EngineAnalysis(
            best_move=best,
            score_cp=25,
            principal_variation=(alternative,),
            perspective=Side.CHO,
        )

        normalized = validate_engine_analysis(state, analysis)

        self.assertEqual(normalized.best_move, best)
        self.assertEqual(normalized.principal_variation, ())

    def test_validate_engine_analysis_tolerates_null_principal_variation(self):
        state = GameState.initial()
        move = state.legal_moves(include_pass=False)[0]
        analysis = EngineAnalysis(
            best_move=move,
            principal_variation=None,  # type: ignore[arg-type]
            perspective=Side.CHO,
        )

        normalized = validate_engine_analysis(state, analysis)

        self.assertEqual(normalized.best_move, move)
        self.assertEqual(normalized.principal_variation, ())
    def test_validate_engine_analysis_suppresses_pv_without_best_move(self):
        state = GameState.initial()
        first = state.legal_moves(include_pass=False)[0]
        analysis = EngineAnalysis(
            best_move=None,
            principal_variation=(first,),
            perspective=Side.CHO,
        )

        normalized = validate_engine_analysis(state, analysis)

        self.assertIsNone(normalized.best_move)
        self.assertEqual(normalized.principal_variation, ())
    def test_validate_engine_analysis_preserves_valid_analysis(self):
        state = GameState.initial()
        first = state.legal_moves(include_pass=False)[0]
        next_state = state.apply(first)
        second = next_state.legal_moves(include_pass=False)[0]
        analysis = EngineAnalysis(
            best_move=first,
            score_cp=25,
            depth=2,
            nodes=10,
            principal_variation=(first, second),
            perspective=Side.CHO,
        )

        self.assertEqual(validate_engine_analysis(state, analysis), analysis)

    def test_analysis_returns_no_move_for_terminal_position(self):
        state = GameState.empty(turn=Side.CHO)
        analysis = FirstLegalEngine().analyze(state)
        self.assertIsNone(analysis.best_move)


if __name__ == "__main__":
    unittest.main()
