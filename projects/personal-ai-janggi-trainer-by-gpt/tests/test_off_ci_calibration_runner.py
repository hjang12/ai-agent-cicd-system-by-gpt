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

    def test_artifact_identity_contains_pair_seed_and_setup(self) -> None:
        path = runner._artifact_path(
            Path("/tmp/calibration"),
            "2-3",
            20261002,
            "classic",
        )
        self.assertEqual(
            path.name,
            "ai-level-strength-2-3-seed-20261002-classic.json",
        )

    def test_existing_artifact_is_skipped_and_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            artifact = project_root / "ai-level-strength-2-3-seed-20261002-classic.json"
            original = {
                "experiment": {
                    "pair": "2-3",
                    "seed": 20261002,
                    "setup": "classic",
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
                )
                self.assertEqual(
                    artifact.read_text(encoding="utf-8"),
                    json.dumps(original, ensure_ascii=False),
                )
                run.assert_not_called()

    def test_existing_artifact_identity_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "ai-level-strength-2-3-seed-20261002-classic.json"
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
                )


if __name__ == "__main__":
    unittest.main()
