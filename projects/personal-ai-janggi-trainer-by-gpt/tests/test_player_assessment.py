import unittest

from janggi import OpponentProfile, Outcome, PlayerGameAssessment, PlayerSkillAssessment, Side


class PlayerSkillAssessmentTests(unittest.TestCase):
    def test_unrated_game_preserves_result_without_creating_numeric_rating(self):
        assessment = PlayerSkillAssessment("player-1")
        game = assessment.record_game(
            game_id="game-1",
            player_side=Side.CHO,
            opponent=OpponentProfile(
                model_id="baseline-search",
                model_version=None,
                ai_level="1",
                rating=None,
            ),
            outcome=Outcome.WIN,
            result_status="cho_win",
            move_count=20,
        )

        self.assertIsInstance(game, PlayerGameAssessment)
        self.assertFalse(game.rating_eligible)
        self.assertEqual(game.rating_delta, 0)
        snapshot = assessment.snapshot()
        self.assertIsNone(snapshot["rating"])
        self.assertEqual(snapshot["rating_status"], "unrated")
        self.assertEqual(snapshot["games"], 1)
        self.assertEqual(snapshot["wins"], 1)
        self.assertEqual(snapshot["unrated_games"], 1)

    def test_rated_game_updates_player_rating(self):
        assessment = PlayerSkillAssessment("player-1")
        game = assessment.record_game(
            game_id="game-1",
            player_side=Side.CHO,
            opponent=OpponentProfile(model_id="calibrated-model", rating=1000),
            outcome=Outcome.WIN,
            result_status="cho_win",
            move_count=20,
        )

        self.assertTrue(game.rating_eligible)
        self.assertEqual(game.rating_before, 1000)
        self.assertGreater(game.rating_after, game.rating_before)
        self.assertGreater(game.rating_delta, 0)
        snapshot = assessment.snapshot()
        self.assertEqual(snapshot["rating"], game.rating_after)
        self.assertEqual(snapshot["rating_status"], "provisional")
        self.assertEqual(snapshot["rated_games"], 1)

    def test_player_perspective_is_used_for_han(self):
        assessment = PlayerSkillAssessment("player-1")
        game = assessment.record_game(
            game_id="game-1",
            player_side=Side.HAN,
            opponent=OpponentProfile(model_id="calibrated-model", rating=1000),
            outcome=Outcome.WIN,
            result_status="han_win",
            move_count=10,
        )
        self.assertEqual(game.outcome, Outcome.WIN)
        self.assertGreater(game.rating_delta, 0)

    def test_duplicate_game_id_is_rejected(self):
        assessment = PlayerSkillAssessment("player-1")
        args = dict(
            game_id="game-1",
            player_side=Side.CHO,
            opponent=OpponentProfile(model_id="calibrated-model", rating=1000),
            outcome=Outcome.DRAW,
            result_status="draw_repetition",
            move_count=10,
        )
        assessment.record_game(**args)
        with self.assertRaises(ValueError):
            assessment.record_game(**args)

    def test_terminal_result_mapping(self):
        from janggi.player_assessment import outcome_from_result

        self.assertEqual(outcome_from_result(Side.CHO, "cho_win"), Outcome.WIN)
        self.assertEqual(outcome_from_result(Side.HAN, "cho_win"), Outcome.LOSS)
        self.assertEqual(outcome_from_result(Side.HAN, "han_win"), Outcome.WIN)
        self.assertEqual(outcome_from_result(Side.CHO, "draw_stalemate"), Outcome.DRAW)
        with self.assertRaises(ValueError):
            outcome_from_result(Side.CHO, "playing")

    def test_provisional_becomes_established_at_configured_threshold(self):
        assessment = PlayerSkillAssessment("player-1", established_rated_games=2)
        for index in range(2):
            assessment.record_game(
                game_id=f"game-{index}",
                player_side=Side.CHO,
                opponent=OpponentProfile(model_id="calibrated-model", rating=1000),
                outcome=Outcome.DRAW,
                result_status="draw_repetition",
                move_count=8,
            )
        self.assertEqual(assessment.snapshot()["rating_status"], "established")
        self.assertEqual(len(assessment.snapshot()["rating_history"]), 3)


if __name__ == "__main__":
    unittest.main()
