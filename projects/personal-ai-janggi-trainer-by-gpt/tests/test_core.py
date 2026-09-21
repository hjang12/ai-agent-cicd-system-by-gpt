import unittest

from janggi import GameRecord, GameState, Move, Piece, PieceType, Side, state_from_dict, state_to_dict


class JanggiCoreTests(unittest.TestCase):
    def test_initial_classic_setup_has_32_pieces(self):
        state = GameState.initial(starting_side=Side.CHO)
        self.assertEqual(sum(piece is not None for piece in state.board), 32)
        self.assertEqual(state.turn, Side.CHO)
        han_first = GameState.initial()
        self.assertEqual(han_first.turn, Side.HAN)
        self.assertEqual(state.piece_at((4, 0)), Piece(Side.CHO, PieceType.GENERAL))
        self.assertEqual(state.piece_at((3, 0)), Piece(Side.CHO, PieceType.GUARD))
        self.assertEqual(state.piece_at((4, 9)), Piece(Side.HAN, PieceType.GENERAL))

    def test_setup_variants_move_elephant_and_horse(self):
        classic = GameState.initial("classic", starting_side=Side.CHO)
        left = GameState.initial("left", starting_side=Side.CHO)
        right = GameState.initial("right", starting_side=Side.CHO)
        both = GameState.initial("both", starting_side=Side.CHO)
        self.assertEqual(classic.piece_at((1, 0)).kind, PieceType.ELEPHANT)
        self.assertEqual(left.piece_at((1, 0)).kind, PieceType.HORSE)
        self.assertEqual(right.piece_at((7, 0)).kind, PieceType.HORSE)
        self.assertEqual(both.piece_at((1, 0)).kind, PieceType.HORSE)
        self.assertEqual(both.piece_at((7, 0)).kind, PieceType.HORSE)

    def test_horse_blocking(self):
        board = [None] * 90
        board[0 * 9 + 4] = Piece(Side.CHO, PieceType.HORSE)
        board[0 * 9 + 5] = Piece(Side.CHO, PieceType.SOLDIER)
        state = GameState(tuple(board), Side.CHO)
        moves = state.pseudo_moves((4, 0))
        self.assertNotIn(Move((4, 0), (6, 1)), moves)
        self.assertIn(Move((4, 0), (2, 1)), moves)

    def test_elephant_blocking(self):
        board = [None] * 90
        board[0 * 9 + 4] = Piece(Side.CHO, PieceType.ELEPHANT)
        board[0 * 9 + 5] = Piece(Side.CHO, PieceType.SOLDIER)
        state = GameState(tuple(board), Side.CHO)
        self.assertNotIn(Move((4, 0), (7, 2)), state.pseudo_moves((4, 0)))

    def test_cannon_requires_one_non_cannon_screen(self):
        board = [None] * 90
        board[2 * 9 + 1] = Piece(Side.CHO, PieceType.CANNON)
        board[3 * 9 + 1] = Piece(Side.CHO, PieceType.SOLDIER)
        board[5 * 9 + 1] = Piece(Side.HAN, PieceType.SOLDIER)
        state = GameState(tuple(board), Side.CHO)
        moves = state.pseudo_moves((1, 2))
        self.assertIn(Move((1, 2), (1, 4)), moves)
        self.assertIn(Move((1, 2), (1, 5)), moves)
        self.assertNotIn(Move((1, 2), (1, 3)), moves)

    def test_cannon_cannot_capture_cannon(self):
        board = [None] * 90
        board[2 * 9 + 1] = Piece(Side.CHO, PieceType.CANNON)
        board[3 * 9 + 1] = Piece(Side.CHO, PieceType.SOLDIER)
        board[5 * 9 + 1] = Piece(Side.HAN, PieceType.CANNON)
        state = GameState(tuple(board), Side.CHO)
        self.assertNotIn(Move((1, 2), (1, 5)), state.pseudo_moves((1, 2)))

    def test_cannon_palace_diagonal_requires_center_screen(self):
        board = [None] * 90
        board[0 * 9 + 3] = Piece(Side.CHO, PieceType.CANNON)
        board[1 * 9 + 4] = Piece(Side.HAN, PieceType.SOLDIER)
        state = GameState(tuple(board), Side.CHO)
        moves = state.pseudo_moves((3, 0))
        self.assertIn(Move((3, 0), (5, 2)), moves)

    def test_general_and_guard_follow_palace_diagonals(self):
        general_board = [None] * 90
        general_board[1 * 9 + 4] = Piece(Side.CHO, PieceType.GENERAL)
        general_state = GameState(tuple(general_board), Side.CHO)
        general_moves = general_state.pseudo_moves((4, 1))
        self.assertIn(Move((4, 1), (3, 0)), general_moves)
        self.assertIn(Move((4, 1), (5, 2)), general_moves)

        guard_board = [None] * 90
        guard_board[0 * 9 + 3] = Piece(Side.CHO, PieceType.GUARD)
        guard_state = GameState(tuple(guard_board), Side.CHO)
        guard_moves = guard_state.pseudo_moves((3, 0))
        self.assertIn(Move((3, 0), (4, 1)), guard_moves)

    def test_soldier_can_step_forward_diagonally_inside_enemy_palace(self):
        board = [None] * 90
        board[7 * 9 + 3] = Piece(Side.CHO, PieceType.SOLDIER)
        state = GameState(tuple(board), Side.CHO)
        self.assertIn(Move((3, 7), (4, 8)), state.pseudo_moves((3, 7)))
        self.assertNotIn(Move((3, 7), (2, 8)), state.pseudo_moves((3, 7)))

    def test_soldier_cannot_move_backward_inside_enemy_palace(self):
        board = [None] * 90
        board[8 * 9 + 4] = Piece(Side.CHO, PieceType.SOLDIER)
        state = GameState(tuple(board), Side.CHO)
        self.assertNotIn(Move((4, 8), (3, 7)), state.pseudo_moves((4, 8)))

    def test_soldier_moves_forward_and_sideways(self):
        state = GameState.initial(starting_side=Side.CHO)
        moves = state.pseudo_moves((0, 3))
        self.assertIn(Move((0, 3), (0, 4)), moves)
        self.assertIn(Move((0, 3), (1, 3)), moves)
        self.assertNotIn(Move((0, 3), (0, 2)), moves)

    def test_apply_changes_turn_and_history(self):
        state = GameState.initial(starting_side=Side.CHO)
        move = Move((0, 3), (0, 4))
        next_state = state.apply(move)
        self.assertIsNone(next_state.piece_at((0, 3)))
        self.assertEqual(next_state.piece_at((0, 4)), Piece(Side.CHO, PieceType.SOLDIER))
        self.assertEqual(next_state.turn, Side.HAN)
        self.assertEqual(next_state.history, (move,))

    def test_pass_changes_turn_without_board_change(self):
        state = GameState.initial(starting_side=Side.CHO)
        next_state = state.apply(Move.pass_move())
        self.assertEqual(next_state.turn, Side.HAN)
        self.assertEqual(next_state.board, state.board)
        self.assertEqual(next_state.history[-1], Move.pass_move())

    def test_pass_is_rejected_while_in_check(self):
        board = [None] * 90
        board[0 * 9 + 4] = Piece(Side.CHO, PieceType.GENERAL)
        board[1 * 9 + 4] = Piece(Side.HAN, PieceType.CHARIOT)
        state = GameState(tuple(board), Side.CHO)
        self.assertTrue(state.is_in_check())
        with self.assertRaises(ValueError):
            state.apply(Move.pass_move())

    def test_illegal_self_check_is_rejected(self):
        board = [None] * 90
        board[0 * 9 + 4] = Piece(Side.CHO, PieceType.GENERAL)
        board[1 * 9 + 4] = Piece(Side.CHO, PieceType.SOLDIER)
        board[4 * 9 + 4] = Piece(Side.HAN, PieceType.CHARIOT)
        state = GameState(tuple(board), Side.CHO)
        move = Move((4, 1), (3, 1))
        self.assertIn(move, state.pseudo_moves((4, 1)))
        self.assertNotIn(move, state.legal_moves(include_pass=False))

    def test_bikjang_is_not_check(self):
        board = [None] * 90
        board[0 * 9 + 4] = Piece(Side.CHO, PieceType.GENERAL)
        board[9 * 9 + 4] = Piece(Side.HAN, PieceType.GENERAL)
        state = GameState(tuple(board), Side.CHO)
        self.assertTrue(state.is_bikjang())
        self.assertFalse(state.is_in_check(Side.CHO))
        self.assertFalse(state.is_in_check(Side.HAN))

    def test_position_key_changes_with_turn(self):
        state = GameState.initial(starting_side=Side.CHO)
        same_board_opposite_turn = GameState(state.board, Side.HAN)
        self.assertNotEqual(state.position_key(), same_board_opposite_turn.position_key())


class JanggiRecordTests(unittest.TestCase):
    def test_record_json_round_trip_and_replay(self):
        moves = (Move((0, 3), (0, 4)), Move((0, 6), (0, 5)), Move((2, 3), (2, 4)))
        record = GameRecord(setup="classic", moves=moves, result="CHO_WIN", source="self-play")
        restored = GameRecord.from_json(record.to_json())
        self.assertEqual(restored, record)
        self.assertEqual(restored.replay().history, moves)
        self.assertEqual(restored.replay().turn, Side.HAN)

    def test_pass_round_trip(self):
        record = GameRecord(moves=(Move.pass_move(),), source="manual")
        restored = GameRecord.from_dict(record.to_dict())
        self.assertEqual(restored.moves, (Move.pass_move(),))
        self.assertEqual(restored.replay().turn, Side.HAN)

    def test_state_json_round_trip(self):
        state = GameState.initial(starting_side=Side.CHO).apply(Move((0, 3), (0, 4)))
        restored = state_from_dict(state_to_dict(state))
        self.assertEqual(restored, state)

    def test_state_round_trip_preserves_setup_when_requested(self):
        state = GameState.initial("left", starting_side=Side.CHO)
        restored = state_from_dict(state_to_dict(state, setup="left"))
        self.assertEqual(restored, state)

    def test_state_history_integrity_is_validated_with_setup(self):
        state = GameState.initial(starting_side=Side.CHO).apply(Move((0, 3), (0, 4)))
        data = state_to_dict(state, setup="classic")
        data["board"][36] = "cho:chariot"
        with self.assertRaises(ValueError):
            state_from_dict(data)

    def test_state_setup_mismatch_is_rejected(self):
        data = state_to_dict(GameState.initial("left", starting_side=Side.CHO), setup="left")
        with self.assertRaises(ValueError):
            state_from_dict(data, setup="classic")

    def test_state_non_object_is_rejected(self):
        with self.assertRaises(ValueError):
            state_from_dict([])

    def test_invalid_record_object_is_rejected(self):
        with self.assertRaises(ValueError):
            GameRecord.from_dict([])

    def test_invalid_record_format_is_rejected(self):
        with self.assertRaises(ValueError):
            GameRecord.from_dict({"format": "unknown"})

    def test_invalid_move_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            GameRecord.from_dict({"format": "janggi-record-v1", "moves": [{"pass": False, "src": [0, 0]}]})


if __name__ == "__main__":
    unittest.main()
