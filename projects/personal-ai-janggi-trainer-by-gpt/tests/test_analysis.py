import unittest

from janggi import GameState, Move, Side
from janggi.analysis import Analyzer, MoveAnalysis, TacticalRisk
from janggi.core import BOARD_SIZE, Piece, PieceType
from janggi.engine import EngineAnalysis, EngineInfo


class ScriptedEngine:
    def __init__(self, analyses):
        self._analyses = analyses

    @property
    def info(self):
        return EngineInfo(name="scripted", version="test")

    def choose_move(self, state):
        return state.legal_moves(include_pass=True)[0]

    def analyze(self, state):
        return self._analyses.get(state.position_key(), EngineAnalysis(perspective=state.turn))


class AnalysisTests(unittest.TestCase):
    def test_analysis_marks_recommended_move(self):
        state = GameState.initial()
        move = state.legal_moves(include_pass=False)[0]
        before = EngineAnalysis(best_move=move, score_cp=35, depth=7, nodes=1000, perspective=Side.CHO)
        after_state = state.apply(move)
        after = EngineAnalysis(score_cp=20, depth=7, nodes=1200, perspective=Side.HAN)
        engine = ScriptedEngine({state.position_key(): before, after_state.position_key(): after})

        result = Analyzer(engine).analyze_move(state, move)

        self.assertIsInstance(result, MoveAnalysis)
        self.assertTrue(result.is_best_move)
        self.assertEqual(result.score_before_cp, 35)
        self.assertEqual(result.score_after_cp, -20)
        self.assertEqual(result.score_delta_cp, -55)
        self.assertEqual(result.depth, 7)
        self.assertEqual(result.nodes, 1000)
        self.assertEqual(result.perspective, Side.CHO)
        self.assertEqual(result.moved_piece, state.piece_at(move.src).kind)
        self.assertIsNone(result.captured_piece)
        self.assertFalse(result.gives_check)
        self.assertFalse(result.destination_attacked)
        self.assertEqual(result.tactical_risk, TacticalRisk.NONE)

    def test_analysis_normalizes_score_to_mover_perspective(self):
        state = GameState.initial()
        move = state.legal_moves(include_pass=False)[0]
        before = EngineAnalysis(best_move=move, score_cp=-10, perspective=Side.HAN)
        after_state = state.apply(move)
        after = EngineAnalysis(score_cp=5, perspective=Side.CHO)
        engine = ScriptedEngine({state.position_key(): before, after_state.position_key(): after})

        result = Analyzer(engine).analyze_move(state, move)

        self.assertEqual(result.score_before_cp, 10)
        self.assertEqual(result.score_after_cp, 5)
        self.assertEqual(result.score_delta_cp, -5)

    def test_analysis_reports_capture_and_check(self):
        board = [None] * BOARD_SIZE
        board[4] = Piece(Side.CHO, PieceType.GENERAL)
        board[85] = Piece(Side.HAN, PieceType.GENERAL)
        board[49] = Piece(Side.CHO, PieceType.CHARIOT)
        board[58] = Piece(Side.HAN, PieceType.SOLDIER)
        state = GameState(tuple(board), Side.CHO)
        move = Move((4, 5), (4, 6))
        after_state = state.apply(move)
        before = EngineAnalysis(best_move=move, score_cp=0, perspective=Side.CHO)
        after = EngineAnalysis(score_cp=0, perspective=Side.HAN)
        engine = ScriptedEngine({state.position_key(): before, after_state.position_key(): after})

        result = Analyzer(engine).analyze_move(state, move)

        self.assertEqual(result.moved_piece, PieceType.CHARIOT)
        self.assertEqual(result.captured_piece, PieceType.SOLDIER)
        self.assertTrue(result.gives_check)

    def test_analysis_reports_hanging_piece(self):
        board = [None] * BOARD_SIZE
        board[4] = Piece(Side.CHO, PieceType.GENERAL)
        board[85] = Piece(Side.HAN, PieceType.GENERAL)
        board[27] = Piece(Side.CHO, PieceType.SOLDIER)
        board[45] = Piece(Side.HAN, PieceType.SOLDIER)
        state = GameState(tuple(board), Side.CHO)
        move = Move((0, 3), (0, 4))
        after_state = state.apply(move)
        before = EngineAnalysis(best_move=move, score_cp=0, perspective=Side.CHO)
        after = EngineAnalysis(score_cp=0, perspective=Side.HAN)
        engine = ScriptedEngine({state.position_key(): before, after_state.position_key(): after})

        result = Analyzer(engine).analyze_move(state, move)

        self.assertTrue(result.destination_attacked)
        self.assertEqual(result.tactical_risk, TacticalRisk.HANGING_PIECE)

    def test_analysis_reports_immediate_capture_risk_when_recapture_exists(self):
        board = [None] * BOARD_SIZE
        board[4] = Piece(Side.CHO, PieceType.GENERAL)
        board[85] = Piece(Side.HAN, PieceType.GENERAL)
        board[18] = Piece(Side.CHO, PieceType.CHARIOT)
        board[27] = Piece(Side.CHO, PieceType.SOLDIER)
        board[45] = Piece(Side.HAN, PieceType.SOLDIER)
        state = GameState(tuple(board), Side.CHO)
        move = Move((0, 3), (0, 4))
        after_state = state.apply(move)
        before = EngineAnalysis(best_move=move, score_cp=0, perspective=Side.CHO)
        after = EngineAnalysis(score_cp=0, perspective=Side.HAN)
        engine = ScriptedEngine({state.position_key(): before, after_state.position_key(): after})

        result = Analyzer(engine).analyze_move(state, move)

        self.assertTrue(result.destination_attacked)
        self.assertEqual(result.tactical_risk, TacticalRisk.IMMEDIATE_CAPTURE)

    def test_analysis_rejects_illegal_move(self):
        state = GameState.initial()
        illegal = Move((0, 3), (0, 2))
        with self.assertRaises(ValueError):
            Analyzer(ScriptedEngine({})).analyze_move(state, illegal)

    def test_invalid_engine_pv_is_suppressed(self):
        state = GameState.initial()
        move = state.legal_moves(include_pass=False)[0]
        invalid_pv = (move, Move((0, 3), (0, 2)))
        before = EngineAnalysis(best_move=move, score_cp=12, principal_variation=invalid_pv, perspective=Side.CHO)
        after_state = state.apply(move)
        after = EngineAnalysis(score_cp=0, perspective=Side.HAN)
        engine = ScriptedEngine({state.position_key(): before, after_state.position_key(): after})

        result = Analyzer(engine).analyze_move(state, move)

        self.assertEqual(result.principal_variation, ())

    def test_position_analysis_validates_principal_variation(self):
        state = GameState.initial()
        move = state.legal_moves(include_pass=False)[0]
        expected = EngineAnalysis(best_move=move, score_cp=12, principal_variation=(move,), perspective=Side.CHO)
        engine = ScriptedEngine({state.position_key(): expected})

        self.assertEqual(Analyzer(engine).analyze_position(state), expected)


if __name__ == "__main__":
    unittest.main()
