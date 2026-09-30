import json
import tempfile
import unittest
from pathlib import Path

from tools.evaluate_ai_level_evidence import aggregate_evidence


def _write_fixture(path: Path, *, pair: str, seed: int, outcomes: list[int | None]) -> None:
    lower, higher = pair.split("-")
    games = []
    for index, outcome in enumerate(outcomes, start=1):
        if outcome is None:
            games.append(
                {
                    "game": index,
                    "status": "playing",
                    "outcome_for_lower": None,
                    "plies": 48,
                }
            )
        else:
            games.append(
                {
                    "game": index,
                    "status": "cho_win"
                    if outcome == 1
                    else ("han_win" if outcome == -1 else "draw_bikjang"),
                    "outcome_for_lower": outcome,
                    "plies": 24,
                }
            )
    payload = {
        "experiment": {
            "pair": pair,
            "seed": seed,
            "setup": "classic",
        },
        "pairs": [
            {
                "lower_level": lower,
                "higher_level": higher,
                "game_results": games,
                "games": len(outcomes),
                "completed": sum(value is not None for value in outcomes),
                "unfinished": sum(value is None for value in outcomes),
                "lower_wins": sum(value == 1 for value in outcomes),
                "higher_wins": sum(value == -1 for value in outcomes),
                "draws": sum(value == 0 for value in outcomes),
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class AiLevelEvidenceTests(unittest.TestCase):
    def test_aggregate_rejects_duplicate_experiment_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first.json"
            second = Path(temp) / "second.json"
            _write_fixture(first, pair="1-2", seed=1, outcomes=[-1, -1, 0, None])
            _write_fixture(second, pair="1-2", seed=1, outcomes=[-1, -1, 0, None])
            with self.assertRaises(ValueError):
                aggregate_evidence((first, second))

    def test_aggregate_marks_small_sample_insufficient(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sample.json"
            _write_fixture(path, pair="1-2", seed=1, outcomes=[-1, -1, 0, None])
            result = aggregate_evidence((path,), min_completed=4, min_unique_seeds=1)
            report = result["pairs"][0]
            self.assertEqual(report["status"], "INSUFFICIENT")

    def test_aggregate_reports_higher_scored_pair(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = []
            for seed in (1, 2):
                path = Path(temp) / f"{seed}.json"
                _write_fixture(
                    path,
                    pair="1-2",
                    seed=seed,
                    outcomes=[-1, -1, -1, 1, None],
                )
                paths.append(path)
            result = aggregate_evidence(
                paths,
                min_completed=6,
                min_unique_seeds=2,
                max_unfinished_rate=0.5,
            )
            report = result["pairs"][0]
            self.assertEqual(report["status"], "HIGHER_SCORED")
            self.assertFalse(result["candidate_monotonic_higher_levels"])


if __name__ == "__main__":
    unittest.main()
