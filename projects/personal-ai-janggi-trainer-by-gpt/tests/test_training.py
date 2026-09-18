import unittest

from janggi import GameRecord, GameState, Move, RecordValidator, RuleSet, Side
from janggi.match import GameStatus
from janggi.training import Outcome, TrainingDataset, TrainingDatasetBuilder, TrainingExample, _outcome_for_cho, _outcome_for_side


class TrainingDatasetTests(unittest.TestCase):
    def setUp(self):
        self.builder = TrainingDatasetBuilder()
        self.draw_builder = TrainingDatasetBuilder(
            validator=RecordValidator(RuleSet(consecutive_passes_for_draw=2))
        )

    def test_completed_self_play_win_creates_no_samples_when_record_is_incomplete(self):
        record = GameRecord(
            moves=(Move((0, 3), (0, 4)),),
            result="han_win",
            source="self-play",
        )
        dataset = self.builder.build(record)
        self.assertEqual(len(dataset), 0)

    def test_completed_draw_uses_draw_value_for_both_sides(self):
        record = GameRecord(
            moves=(Move.pass_move(), Move.pass_move()),
            result="draw_consecutive_pass",
            source="self-play",
        )
        dataset = self.draw_builder.build(record)

        self.assertEqual(len(dataset), 2)
        self.assertTrue(all(example.outcome is Outcome.DRAW for example in dataset.examples))
        self.assertEqual(dataset.examples[0].side_to_move, Side.CHO)
        self.assertEqual(dataset.examples[1].side_to_move, Side.HAN)

    def test_outcome_conversion_covers_win_loss_and_draw(self):
        self.assertIs(_outcome_for_cho(GameStatus.CHO_WIN), Outcome.WIN)
        self.assertIs(_outcome_for_cho(GameStatus.HAN_WIN), Outcome.LOSS)
        self.assertIs(_outcome_for_cho(GameStatus.DRAW_BIKJANG), Outcome.DRAW)
        self.assertIs(_outcome_for_side(Outcome.WIN, Side.CHO), Outcome.WIN)
        self.assertIs(_outcome_for_side(Outcome.WIN, Side.HAN), Outcome.LOSS)
        self.assertIs(_outcome_for_side(Outcome.LOSS, Side.CHO), Outcome.LOSS)
        self.assertIs(_outcome_for_side(Outcome.LOSS, Side.HAN), Outcome.WIN)
        self.assertIs(_outcome_for_side(Outcome.DRAW, Side.CHO), Outcome.DRAW)
        self.assertIs(_outcome_for_side(Outcome.DRAW, Side.HAN), Outcome.DRAW)

    def test_incomplete_record_is_excluded(self):
        record = GameRecord(moves=(Move.pass_move(),), source="self-play")
        dataset = self.builder.build(record)
        self.assertEqual(len(dataset), 0)

    def test_personal_record_is_excluded_even_when_complete(self):
        record = GameRecord(
            moves=(Move.pass_move(), Move.pass_move()),
            result="draw_consecutive_pass",
            source="personal",
        )
        dataset = self.draw_builder.build(record)
        self.assertEqual(len(dataset), 0)

    def test_build_many_preserves_record_order(self):
        records = (
            GameRecord(
                moves=(Move.pass_move(), Move.pass_move()),
                result="draw_consecutive_pass",
                source="self-play",
            ),
            GameRecord(
                moves=(Move.pass_move(), Move.pass_move()),
                result="draw_consecutive_pass",
                source="self-play",
            ),
        )
        dataset = self.draw_builder.build_many(records)
        self.assertEqual(len(dataset), 4)
        self.assertEqual(dataset.examples[0].source, "self-play")
        self.assertEqual(dataset.examples[-1].source, "self-play")

    def test_variant_setup_is_preserved_in_training_examples(self):
        record = GameRecord(
            setup="left",
            moves=(Move.pass_move(), Move.pass_move()),
            result="draw_consecutive_pass",
            source="self-play",
        )
        dataset = self.draw_builder.build(record)

        self.assertEqual(len(dataset), 2)
        self.assertTrue(all(example.setup == "left" for example in dataset.examples))
        self.assertEqual(dataset.examples[0].state, GameState.initial("left"))

        restored = TrainingDataset.from_dict(dataset.to_dict())
        self.assertEqual(restored, dataset)
        self.assertTrue(all(example.setup == "left" for example in restored.examples))

    def test_training_example_rejects_illegal_action(self):
        with self.assertRaises(ValueError):
            TrainingExample(
                state=GameState.initial(),
                move=Move((0, 0), (8, 9)),
                outcome=Outcome.WIN,
                source="self-play",
            )

    def test_training_example_rejects_invalid_types(self):
        with self.assertRaises(ValueError):
            TrainingExample(
                state="not-a-state",  # type: ignore[arg-type]
                move=Move.pass_move(),
                outcome=Outcome.DRAW,
                source="self-play",
            )
        with self.assertRaises(ValueError):
            TrainingExample(
                state=GameState.initial(),
                move="not-a-move",  # type: ignore[arg-type]
                outcome=Outcome.DRAW,
                source="self-play",
            )
        with self.assertRaises(ValueError):
            TrainingExample(
                state=GameState.initial(),
                move=Move.pass_move(),
                outcome=0,  # type: ignore[arg-type]
                source="self-play",
            )

    def test_dataset_serialization_round_trip(self):
        record = GameRecord(
            moves=(Move.pass_move(), Move.pass_move()),
            result="draw_consecutive_pass",
            source="self-play",
        )
        dataset = self.draw_builder.build(record)
        payload = dataset.to_dict()
        restored = TrainingDataset.from_dict(payload)
        self.assertEqual(restored, dataset)
        self.assertEqual(TrainingDataset.from_json(dataset.to_json()), dataset)
        self.assertEqual(payload["format"], "janggi-training-v1")
        self.assertEqual(payload["examples"][0]["state"]["format"], "janggi-state-v1")
        self.assertEqual(payload["examples"][0]["state"]["setup"], "classic")
        self.assertEqual(payload["examples"][0]["setup"], "classic")
        self.assertEqual(payload["examples"][0]["outcome"], 0)
        self.assertTrue(payload["examples"][0]["move"]["pass"])

    def test_invalid_dataset_format_is_rejected(self):
        with self.assertRaises(ValueError):
            TrainingDataset.from_dict({"format": "other", "examples": []})


if __name__ == "__main__":
    unittest.main()
