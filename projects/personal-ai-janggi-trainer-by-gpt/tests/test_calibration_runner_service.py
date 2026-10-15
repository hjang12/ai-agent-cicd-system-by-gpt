from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.calibration_runner_service import CalibrationRunner


class CalibrationRunnerServiceTests(unittest.TestCase):
    def test_completion_artifacts_are_scoped_to_the_matching_v3_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output_dir = Path(temp)
            raw_name = "ai-level-strength-2-3-seed-20261006-classic-v3-tactical.json"
            aggregate_name = "aggregate-2-3-classic-v3-tactical.json"
            manifest_name = (
                "manifest-v3-pairs-2_3-seeds-20261006-setup-classic-"
                "fixture-tactical-g2-p96-src-535598c4445f.json"
            )
            old_name = "ai-level-strength-2-3-seed-20261005-classic-v2-tactical.json"
            for name in (raw_name, aggregate_name, old_name):
                (output_dir / name).write_text("{}", encoding="utf-8")

            manifest = {
                "pairs": ["2-3"],
                "seeds": [20261006],
                "setup": "classic",
                "fixture": "tactical",
                "games_per_experiment": 2,
                "max_plies": 96,
                "calibration_protocol_version": "3",
                "source_revision": "535598c4445f5fbeab2f",
                "artifacts": [str(output_dir / raw_name)],
                "aggregate_reports": {"2-3:tactical": str(output_dir / aggregate_name)},
            }
            (output_dir / manifest_name).write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )

            runner = CalibrationRunner(
                {
                    "pair": "2-3",
                    "seeds": "20261006",
                    "setup": "classic",
                    "fixture": "tactical",
                    "source_revision": "535598c4445f5fbeab2f",
                    "games": 2,
                    "max_plies": 96,
                    "output_dir": output_dir,
                }
            )

            self.assertEqual(
                runner._request_artifact_names(),
                sorted([manifest_name, raw_name, aggregate_name]),
            )
            # API browsing still exposes retained historical artifacts.
            self.assertEqual(
                runner._artifact_names(),
                sorted([manifest_name, raw_name, aggregate_name, old_name]),
            )

    def test_v3_manifest_matching_rejects_wrong_source_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output_dir = Path(temp)
            manifest_name = (
                "manifest-v3-pairs-2_3-seeds-20261006-setup-classic-"
                "fixture-tactical-g2-p96-src-wrongrevision.json"
            )
            (output_dir / manifest_name).write_text(
                json.dumps(
                    {
                        "pairs": ["2-3"],
                        "seeds": [20261006],
                        "setup": "classic",
                        "fixture": "tactical",
                        "games_per_experiment": 2,
                        "max_plies": 96,
                        "calibration_protocol_version": "3",
                        "source_revision": "different-source-revision",
                        "artifacts": [],
                        "aggregate_reports": {},
                    }
                ),
                encoding="utf-8",
            )
            runner = CalibrationRunner(
                {
                    "pair": "2-3",
                    "seeds": "20261006",
                    "setup": "classic",
                    "fixture": "tactical",
                    "source_revision": "expected-source-revision",
                    "games": 2,
                    "max_plies": 96,
                    "output_dir": output_dir,
                }
            )
            self.assertEqual(runner._request_artifact_names(), [])


if __name__ == "__main__":
    unittest.main()
