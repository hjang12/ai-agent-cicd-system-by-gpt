from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "run_ai_level_calibration.py"
SPEC = importlib.util.spec_from_file_location("run_ai_level_calibration", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class OffCiCalibrationRunnerTests(unittest.TestCase):
    def test_parse_seeds_rejects_duplicates(self) -> None:
        with self.assertRaisesRegex(ValueError, "unique"):
            runner._parse_seeds("20261002,20261002")

    def test_artifact_identity_includes_protocol_and_fixture_mode(self) -> None:
        path = runner._artifact_path(
            Path("/tmp/calibration"),
            "2-3",
            20261005,
            "classic",
            "tactical",
        )
        self.assertEqual(
            path.name,
            "ai-level-strength-2-3-seed-20261005-classic-v3-tactical.json",
        )
        self.assertNotEqual(
            path,
            Path("/tmp/calibration/ai-level-strength-2-3-seed-20261005-classic.json"),
        )

    def test_manifest_path_is_unique_to_protocol_and_run_identity(self) -> None:
        path = runner._manifest_path(
            Path("/tmp/calibration"),
            pairs=["2-3"],
            seeds=[20261006],
            setup="classic",
            fixture_mode="tactical",
            games=2,
            max_plies=96,
            source_revision="a" * 40,
        )
        self.assertEqual(
            path.name,
            "manifest-v3-pairs-2_3-seeds-20261006-setup-classic-fixture-tactical-g2-p96-src-aaaaaaaaaaaa.json",
        )
        self.assertNotEqual(path.name, "manifest.json")

    def test_aggregate_path_is_unique_to_run_identity(self) -> None:
        output_dir = Path("/tmp/calibration")
        common = {
            "pair": "2-3",
            "setup": "classic",
            "fixture_mode": "tactical",
            "games": 2,
            "max_plies": 96,
            "source_revision": "a" * 40,
        }
        first = runner._aggregate_path(
            output_dir, seeds=[20261006], **common
        )
        next_seed = runner._aggregate_path(
            output_dir, seeds=[20261007], **common
        )
        changed_game_count = runner._aggregate_path(
            output_dir, seeds=[20261006], **{**common, "games": 4}
        )
        changed_revision = runner._aggregate_path(
            output_dir,
            seeds=[20261006],
            **{**common, "source_revision": "b" * 40},
        )

        self.assertEqual(
            first.name,
            "aggregate-v3-pair-2_3-seeds-20261006-setup-classic-fixture-tactical-g2-p96-src-aaaaaaaaaaaa.json",
        )
        self.assertNotEqual(first, next_seed)
        self.assertNotEqual(first, changed_game_count)
        self.assertNotEqual(first, changed_revision)
        self.assertNotEqual(first.name, "aggregate-2-3-classic-v3-tactical.json")

    def test_existing_artifact_is_skipped_and_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            artifact = runner._artifact_path(project_root, "2-3", 20261002, "classic", "tactical")
            original = {
                "experiment": {
                    "pair": "2-3",
                    "seed": 20261002,
                    "setup": "classic",
                    "fixture": "tactical",
                    "calibration_protocol_version": "3",
                },
                "pairs": [],
            }
            artifact.write_text(
                json.dumps(original, ensure_ascii=False),
                encoding="utf-8",
            )

            with patch.object(runner, "_run") as run:
                runner._run_experiment(
                    project_root=project_root,
                    artifact=artifact,
                    pair="2-3",
                    seed=20261002,
                    setup="classic",
                    games=12,
                    max_plies=96,
                    fixture_mode="tactical",
                )
                self.assertEqual(
                    artifact.read_text(encoding="utf-8"),
                    json.dumps(original, ensure_ascii=False),
                )
                run.assert_not_called()

    def test_existing_artifact_identity_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = runner._artifact_path(Path(tmp), "2-3", 20261002, "classic", "tactical")
            artifact.write_text(
                json.dumps(
                    {
                        "experiment": {
                            "pair": "2-3",
                            "seed": 20261003,
                            "setup": "classic",
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                runner._run_experiment(
                    project_root=Path(tmp),
                    artifact=artifact,
                    pair="2-3",
                    seed=20261002,
                    setup="classic",
                    games=12,
                    max_plies=96,
                    fixture_mode="tactical",
                )


if __name__ == "__main__":
    unittest.main()
