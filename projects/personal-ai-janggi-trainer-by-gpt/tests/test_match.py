import unittest

from janggi import GameState, GameStatus, Match, Move, Piece, PieceType, RuleSet, Side


class JanggiMatchTests(unittest.TestCase):
    def test_new_match_starts_with_han(self):
        match = Match.new()
        self.assertEqual(match.state.turn, Side.HAN)

    def test_new_match_is_playing(self):
        match = Match.new()
        self.assertEqual(match.status, GameStatus.PLAYING)
        self.assertTrue(match.legal_moves())

    def test_consecutive_pass_draw_is_policy_driven(self):
        match = Match.new(rules=RuleSet(consecutive_passes_for_draw=2))
        match = match.play(Move.pass_move())
        self.assertEqual(match.status, GameStatus.PLAYING)
        match = match.play(Move.pass_move())
        self.assertEqual(match.status, GameStatus.DRAW_CONSECUTIVE_PASS)
        self.assertEqual(match.consecutive_pass_count(), 2)

    def test_repetition_draw_can_be_enabled_independently(self):
        rules = RuleSet(repetition_limit=3, consecutive_passes_for_draw=None)
        match = Match.new(rules=rules)
        for _ in range(4):
            match = match.play(Move.pass_move())
        self.assertEqual(match.position_repetition_count(), 3)
        self.assertEqual(match.status, GameStatus.DRAW_REPETITION)

    def test_bikjang_is_match_draw_when_enabled(self):
        board = [None] * 90
        board[4] = Piece(Side.CHO, PieceType.GENERAL)
        board[81 + 4] = Piece(Side.HAN, PieceType.GENERAL)
        state = GameState(tuple(board), Side.CHO)
        self.assertEqual(Match(state).status, GameStatus.DRAW_BIKJANG)

    def test_bikjang_can_be_disabled_by_policy(self):
        board = [None] * 90
        board[4] = Piece(Side.CHO, PieceType.GENERAL)
        board[81 + 4] = Piece(Side.HAN, PieceType.GENERAL)
        state = GameState(tuple(board), Side.CHO)
        match = Match(state=state, rules=RuleSet(bikjang_is_draw=False))
        self.assertEqual(match.status, GameStatus.PLAYING)

    def test_finished_match_rejects_more_moves(self):
        match = Match.new(rules=RuleSet(consecutive_passes_for_draw=2))
        match = match.play(Move.pass_move()).play(Move.pass_move())
        with self.assertRaises(ValueError):
            match.play(Move.pass_move())

    def test_undo_restores_previous_state_and_preserves_rules(self):
        rules = RuleSet(bikjang_is_draw=False, consecutive_passes_for_draw=None)
        match = Match.new(rules=rules)
        initial_state = match.state
        move = match.legal_moves()[0]
        played = match.play(move)
        undone = played.undo()

        self.assertEqual(undone.state, initial_state)
        self.assertEqual(undone.setup, match.setup)
        self.assertEqual(undone.rules, rules)
        self.assertEqual(undone.state.history, ())

    def test_undo_without_history_is_rejected(self):
        with self.assertRaises(ValueError):
            Match.new().undo()

    def test_undo_can_recover_a_finished_match(self):
        match = Match.new(rules=RuleSet(consecutive_passes_for_draw=2))
        match = match.play(Move.pass_move()).play(Move.pass_move())
        self.assertEqual(match.status, GameStatus.DRAW_CONSECUTIVE_PASS)

        undone = match.undo()
        self.assertEqual(undone.status, GameStatus.PLAYING)
        self.assertEqual(len(undone.state.history), 1)

    def test_rule_thresholds_are_validated(self):
        with self.assertRaises(ValueError):
            RuleSet(repetition_limit=1)
        with self.assertRaises(ValueError):
            RuleSet(consecutive_passes_for_draw=1)


if __name__ == "__main__":
    unittest.main()
