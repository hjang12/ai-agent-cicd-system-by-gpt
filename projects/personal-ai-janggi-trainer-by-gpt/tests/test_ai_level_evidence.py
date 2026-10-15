import json
import tempfile
import unittest
from pathlib import Path

from tools.evaluate_ai_level_evidence import aggregate_evidence


def _write_fixture(
    path: Path,
    *,
    pair: str,
    seed: int,
    outcomes: list[int | None],
    config_fingerprint: str | None = None,
    engine_version: str | None = None,
    protocol_version: str | None = None,
    fixture_mode: str = "initial",
) -> None:
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
            "fixture": fixture_mode,
            "ai_level_config_fingerprint": config_fingerprint,
            "engine_version": engine_version,
            "calibration_protocol_version": protocol_version,
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

    def test_same_seed_can_have_distinct_fixture_mode_experiments(self):
        with tempfile.TemporaryDirectory() as temp:
            initial = Path(temp) / "initial.json"
            tactical = Path(temp) / "tactical.json"
            common = {
                "config_fingerprint": "same",
                "engine_version": "7",
                "protocol_version": "2",
            }
            _write_fixture(initial, pair="2-3", seed=20261005, outcomes=[-1, -1], fixture_mode="initial", **common)
            _write_fixture(tactical, pair="2-3", seed=20261005, outcomes=[-1, 0], fixture_mode="tactical", **common)
            result = aggregate_evidence((initial, tactical), min_completed=4, min_unique_seeds=1)["pairs"][1]
            self.assertEqual(result["experiments"], 2)
            self.assertEqual(result["fixture_modes"], ["initial", "tactical"])

    def test_aggregate_rejects_incompatible_config_fingerprints(self):
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first.json"
            second = Path(temp) / "second.json"
            _write_fixture(first, pair="1-2", seed=1, outcomes=[-1, -1, 0], config_fingerprint="aaa")
            _write_fixture(second, pair="1-2", seed=2, outcomes=[-1, -1, 0], config_fingerprint="bbb")
            with self.assertRaisesRegex(ValueError, "configuration fingerprints"):
                aggregate_evidence((first, second), min_completed=6, min_unique_seeds=2)

    def test_aggregate_rejects_mixed_legacy_and_provenance_artifacts(self):
        with tempfile.TemporaryDirectory() as temp:
            legacy = Path(temp) / "legacy.json"
            current = Path(temp) / "current.json"
            _write_fixture(legacy, pair="1-2", seed=1, outcomes=[-1, -1, 0])
            _write_fixture(current, pair="1-2", seed=2, outcomes=[-1, -1, 0], config_fingerprint="same", engine_version="7")
            with self.assertRaisesRegex(ValueError, "mixed legacy"):
                aggregate_evidence((legacy, current), min_completed=6, min_unique_seeds=2)

    def test_aggregate_rejects_incompatible_source_revisions(self):
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first.json"
            second = Path(temp) / "second.json"
            _write_fixture(
                first,
                pair="1-2",
                seed=1,
                outcomes=[-1, -1, 0],
                config_fingerprint="same",
                engine_version="7",
                protocol_version="1",
            )
            _write_fixture(
                second,
                pair="1-2",
                seed=2,
                outcomes=[-1, -1, 0],
                config_fingerprint="same",
                engine_version="7",
                protocol_version="1",
            )
            first_payload = json.loads(first.read_text(encoding="utf-8"))
            second_payload = json.loads(second.read_text(encoding="utf-8"))
            first_payload["experiment"]["source_revision"] = "abc"
            second_payload["experiment"]["source_revision"] = "def"
            first.write_text(json.dumps(first_payload), encoding="utf-8")
            second.write_text(json.dumps(second_payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source revisions"):
                aggregate_evidence((first, second), min_completed=6, min_unique_seeds=2)

    def test_aggregate_rejects_incompatible_protocol_versions(self):
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first.json"
            second = Path(temp) / "second.json"
            _write_fixture(first, pair="1-2", seed=1, outcomes=[-1, -1, 0], config_fingerprint="same", engine_version="7", protocol_version="1")
            _write_fixture(second, pair="1-2", seed=2, outcomes=[-1, -1, 0], config_fingerprint="same", engine_version="7", protocol_version="2")
            with self.assertRaisesRegex(ValueError, "calibration protocol versions"):
                aggregate_evidence((first, second), min_completed=6, min_unique_seeds=2)

    def test_aggregate_reports_provenance_context(self):
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first.json"
            second = Path(temp) / "second.json"
            for seed, path in ((1, first), (2, second)):
                _write_fixture(path, pair="1-2", seed=seed, outcomes=[-1, -1, 0], config_fingerprint="same", engine_version="7", protocol_version="1")
            result = aggregate_evidence((first, second), min_completed=6, min_unique_seeds=2)
            report = result["pairs"][0]
            self.assertEqual(report["ai_level_config_fingerprints"], ["same"])
            self.assertEqual(report["engine_versions"], ["7"])
            self.assertEqual(report["calibration_protocol_versions"], ["1"])

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
