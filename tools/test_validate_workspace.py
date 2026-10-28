from __future__ import annotations

import unittest

from validate_workspace import GAME_CI_DOC_EXCLUSIONS, validate_game_ci_doc_exclusions, validate_governance_version_values


class GovernanceVersionValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.version = "1.4.7"
        self.governance = "**Governance Version: 1.4.7**\n"
        self.changelog = "## [1.4.7] - 2026-10-22\n"
        self.current_status = "- Governance 1.4.7 is active on `main` following the approved merge.\n"

    def test_matching_canonical_version_passes(self) -> None:
        self.assertEqual(
            [],
            validate_governance_version_values(
                self.version,
                self.governance,
                self.changelog,
                self.current_status,
            ),
        )

    def test_governance_header_drift_fails(self) -> None:
        errors = validate_governance_version_values(
            self.version,
            "**Governance Version: 1.4.6**\n",
            self.changelog,
            self.current_status,
        )
        self.assertTrue(any("GOVERNANCE/GOVERNANCE.md version" in error for error in errors))

    def test_changelog_drift_fails(self) -> None:
        errors = validate_governance_version_values(
            self.version,
            self.governance,
            "## [1.4.6] - 2026-10-21\n",
            self.current_status,
        )
        self.assertTrue(any("CHANGELOG.md latest version" in error for error in errors))

    def test_current_status_drift_fails(self) -> None:
        errors = validate_governance_version_values(
            self.version,
            self.governance,
            self.changelog,
            "- Governance 1.4.6 is active on `main`.\n",
        )
        self.assertTrue(any("CURRENT_STATUS.md active version" in error for error in errors))

    def test_invalid_canonical_version_fails(self) -> None:
        errors = validate_governance_version_values(
            "latest",
            self.governance,
            self.changelog,
            self.current_status,
        )
        self.assertTrue(any("semantic version" in error for error in errors))


class GameCiPathFilterValidationTests(unittest.TestCase):
    def test_required_document_exclusions_pass(self) -> None:
        workflow = "\n".join(
            f"      - '!{path}'"
            for _event in ("pull_request", "push")
            for path in GAME_CI_DOC_EXCLUSIONS
        )
        self.assertEqual([], validate_game_ci_doc_exclusions(workflow))

    def test_missing_document_exclusion_fails(self) -> None:
        workflow = "\n".join(
            f"      - '!{path}'"
            for path in (
                "projects/soldier-gate-runner-by-gpt/AGENT_START.md",
                "projects/soldier-gate-runner-by-gpt/AGENTS.md",
                "projects/soldier-gate-runner-by-gpt/README.md",
            )
        )
        errors = validate_game_ci_doc_exclusions(workflow)
        self.assertTrue(any("docs/**" in error for error in errors))
        self.assertEqual(4, len(errors))


if __name__ == "__main__":
    unittest.main()
