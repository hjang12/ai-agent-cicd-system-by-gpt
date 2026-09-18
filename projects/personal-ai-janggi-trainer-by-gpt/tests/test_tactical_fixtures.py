import unittest

from janggi import GameState, Move, Side, TacticalMotif
from janggi.analysis import Analyzer, TacticalRisk
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


def analyzed_move(state: GameState, move: Move):
    after_state = state.apply(move)
    before = EngineAnalysis(best_move=move, score_cp=0, perspective=Side.CHO)
    after = EngineAnalysis(score_cp=0, perspective=Side.HAN)
    engine = ScriptedEngine({state.position_key(): before, after_state.position_key(): after})
    return Analyzer(engine).analyze_move(state, move)


class TacticalFixtureTests(unittest.TestCase):
    def test_clean_capture_has_no_destination_risk(self):
        board = [None] * BOARD_SIZE
        board[4] = Piece(Side.CHO, PieceType.GENERAL)
        board[85] = Piece(Side.HAN, PieceType.GENERAL)
        board[41] = Piece(Side.CHO, PieceType.CHARIOT)
        board[50] = Piece(Side.HAN, PieceType.SOLDIER)
        state = GameState(tuple(board), Side.CHO)

        result = analyzed_move(state, Move((5, 4), (5, 5)))

        self.assertEqual(result.captured_piece, PieceType.SOLDIER)
        self.assertFalse(result.destination_attacked)
        self.assertEqual(result.tactical_risk, TacticalRisk.NONE)

    def test_protected_exchange_is_not_a_hanging_piece(self):
        board = [None] * BOARD_SIZE
        board[4] = Piece(Side.CHO, PieceType.GENERAL)
        board[85] = Piece(Side.HAN, PieceType.GENERAL)
        board[18] = Piece(Side.CHO, PieceType.CHARIOT)
        board[27] = Piece(Side.CHO, PieceType.SOLDIER)
        board[45] = Piece(Side.HAN, PieceType.SOLDIER)
        state = GameState(tuple(board), Side.CHO)

        result = analyzed_move(state, Move((0, 3), (0, 4)))

        self.assertTrue(result.destination_attacked)
        self.assertEqual(result.tactical_risk, TacticalRisk.IMMEDIATE_CAPTURE)

    def test_unprotected_move_is_hanging(self):
        board = [None] * BOARD_SIZE
        board[4] = Piece(Side.CHO, PieceType.GENERAL)
        board[85] = Piece(Side.HAN, PieceType.GENERAL)
        board[27] = Piece(Side.CHO, PieceType.SOLDIER)
        board[45] = Piece(Side.HAN, PieceType.SOLDIER)
        state = GameState(tuple(board), Side.CHO)

        result = analyzed_move(state, Move((0, 3), (0, 4)))

        self.assertTrue(result.destination_attacked)
        self.assertEqual(result.tactical_risk, TacticalRisk.HANGING_PIECE)

    def test_non_immediate_threat_is_not_labeled_as_tactical_risk(self):
        board = [None] * BOARD_SIZE
        board[4] = Piece(Side.CHO, PieceType.GENERAL)
        board[85] = Piece(Side.HAN, PieceType.GENERAL)
        board[27] = Piece(Side.CHO, PieceType.SOLDIER)
        board[80] = Piece(Side.HAN, PieceType.CHARIOT)
        state = GameState(tuple(board), Side.CHO)

        result = analyzed_move(state, Move((0, 3), (0, 4)))

        self.assertFalse(result.destination_attacked)
        self.assertEqual(result.tactical_risk, TacticalRisk.NONE)

    def test_detects_bounded_double_attack_threat_for_mover(self):
        board = [None] * BOARD_SIZE
        board[4] = Piece(Side.CHO, PieceType.GENERAL)
        board[85] = Piece(Side.HAN, PieceType.GENERAL)
        board[40] = Piece(Side.CHO, PieceType.HORSE)
        board[51] = Piece(Side.HAN, PieceType.CHARIOT)
        board[53] = Piece(Side.HAN, PieceType.CHARIOT)
        board[35] = Piece(Side.CHO, PieceType.SOLDIER)
        board[80] = Piece(Side.HAN, PieceType.SOLDIER)
        state = GameState(tuple(board), Side.CHO)

        result = analyzed_move(state, Move((8, 3), (8, 4)))

        self.assertIn(TacticalMotif.DOUBLE_ATTACK, result.tactical_motifs)

    def test_does_not_reverse_double_attack_perspective(self):
        board = [None] * BOARD_SIZE
        board[4] = Piece(Side.CHO, PieceType.GENERAL)
        board[85] = Piece(Side.HAN, PieceType.GENERAL)
        board[40] = Piece(Side.HAN, PieceType.HORSE)
        board[51] = Piece(Side.CHO, PieceType.CHARIOT)
        board[53] = Piece(Side.CHO, PieceType.CHARIOT)
        board[35] = Piece(Side.CHO, PieceType.SOLDIER)
        board[80] = Piece(Side.HAN, PieceType.SOLDIER)
        state = GameState(tuple(board), Side.CHO)

        result = analyzed_move(state, Move((8, 3), (8, 4)))

        self.assertNotIn(TacticalMotif.DOUBLE_ATTACK, result.tactical_motifs)

    def test_pass_has_no_tactical_motif(self):
        state = GameState.initial()
        result = analyzed_move(state, Move.pass_move())
        self.assertEqual(result.tactical_motifs, ())


if __name__ == "__main__":
    unittest.main()
