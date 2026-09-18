import unittest

from janggi import EvaluationGame, EvaluationSummary, FirstLegalEngine, GameStatus, HeadToHeadTournament


class TournamentTests(unittest.TestCase):
    def test_run_rejects_invalid_game_count(self):
        tournament = HeadToHeadTournament(
            FirstLegalEngine(),
            FirstLegalEngine(),
            first_model_id="first",
            second_model_id="second",
            max_plies=1,
        )
        with self.assertRaises(ValueError):
            tournament.run(0)

    def test_run_preserves_game_count_and_balances_colors(self):
        tournament = HeadToHeadTournament(
            FirstLegalEngine(),
            FirstLegalEngine(),
            first_model_id="first",
            second_model_id="second",
            max_plies=1,
        )

        summary = tournament.run(4, alternate_colors=True)

        self.assertEqual(summary.first_model_id, "first")
        self.assertEqual(summary.second_model_id, "second")
        self.assertEqual(len(summary.games), 4)
        self.assertEqual(summary.unfinished, 4)
        self.assertEqual(summary.completed, 0)
        self.assertEqual(summary.first_wins + summary.second_wins + summary.draws, 0)
        self.assertEqual(summary.first_score + summary.second_score, 0.0)

    def test_unfinished_games_are_not_counted_as_draws(self):
        unfinished = EvaluationGame(
            first_model_id="first",
            second_model_id="second",
            moves=(),
            status=GameStatus.PLAYING,
        )
        summary = EvaluationSummary("first", "second", (unfinished,))

        self.assertEqual(summary.unfinished, 1)
        self.assertEqual(summary.completed, 0)
        self.assertEqual(summary.draws, 0)
        self.assertEqual(summary.first_score + summary.second_score, 0.0)


if __name__ == "__main__":
    unittest.main()
