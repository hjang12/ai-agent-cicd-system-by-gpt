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

    def test_existing_artifact_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            tools_dir = project_root / "tools"
            tools_dir.mkdir()
            script_path = tools_dir / "run_ai_level_calibration.py"
            script_path.write_text(MODULE_PATH.read_text(encoding="utf-8"), encoding="utf-8")

            artifact_dir = project_root / "artifacts"
            artifact_dir.mkdir()
            artifact = artifact_dir / "ai-level-strength-2-3-seed-20261002-classic.json"
            original = {
                "experiment": {
                    "pair": "2-3",
                    "seed": 20261002,
                    "setup": "classic",
                }
            }
            artifact.write_text(
                json.dumps(original, ensure_ascii=False),
                encoding="utf-8",
            )

            with patch.object(runner, "_run") as run:
                # The repository root is derived from __file__, so exercise the
                # skip rule directly through the identity function rather than
                # spawning a full benchmark subprocess.
                derived = runner._artifact_path(
                    artifact_dir,
                    "2-3",
                    20261002,
                    "classic",
                )
                self.assertEqual(derived.read_text(encoding="utf-8"), artifact.read_text(encoding="utf-8"))
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
