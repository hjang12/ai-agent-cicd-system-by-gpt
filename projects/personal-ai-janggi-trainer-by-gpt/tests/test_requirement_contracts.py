import json
import tempfile
import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import validate_requirement_contracts as validator


class RequirementContractValidationTests(unittest.TestCase):
    def test_active_contract_registry_is_valid(self):
        errors = validator.validate_registry(
            PROJECT_ROOT,
            PROJECT_ROOT / "docs" / "requirement_contracts.json",
            PROJECT_ROOT / "docs" / "REQUIREMENT_CONTRACTS.md",
        )
        self.assertEqual([], errors)

    def test_duplicate_contract_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            registry = {
                "schema_version": 1,
                "contracts": [
                    {
                        "id": "DUP-1",
                        "status": "ACTIVE",
                        "title": "One",
                        "requirement": "One",
                        "source": "test",
                        "protected_paths": [],
                        "regression_tests": [],
                        "change_policy": "INTENTIONAL_CHANGE_REQUIRES_REPORT",
                    },
                    {
                        "id": "DUP-1",
                        "status": "ACTIVE",
                        "title": "Two",
                        "requirement": "Two",
                        "source": "test",
                        "protected_paths": [],
                        "regression_tests": [],
                        "change_policy": "INTENTIONAL_CHANGE_REQUIRES_REPORT",
                    },
                ],
            }
            registry_path = root / "docs" / "requirement_contracts.json"
            doc_path = root / "docs" / "REQUIREMENT_CONTRACTS.md"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            doc_path.write_text("# DUP-1\nOne\nTwo", encoding="utf-8")

            errors = validator.validate_registry(root, registry_path, doc_path)
            self.assertTrue(any("duplicate contract id" in error for error in errors))

    def test_contract_test_symbol_must_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "tests").mkdir()
            test_path = root / "tests" / "test_example.py"
            test_path.write_text("def test_existing():\n    pass\n", encoding="utf-8")
            registry = {
                "schema_version": 1,
                "contracts": [
                    {
                        "id": "REG-1",
                        "status": "ACTIVE",
                        "title": "Existing",
                        "requirement": "Existing",
                        "source": "test",
                        "protected_paths": ["tests/test_example.py"],
                        "regression_tests": [
                            {"file": "tests/test_example.py", "symbol": "test_missing"}
                        ],
                        "change_policy": "INTENTIONAL_CHANGE_REQUIRES_REPORT",
                    }
                ],
            }
            registry_path = root / "docs" / "requirement_contracts.json"
            doc_path = root / "docs" / "REQUIREMENT_CONTRACTS.md"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            doc_path.write_text("# REG-1\nExisting", encoding="utf-8")

            errors = validator.validate_registry(root, registry_path, doc_path)
            self.assertTrue(any("regression test symbol not found" in error for error in errors))

    def test_change_declaration_parser_accepts_contract_id(self):
        text = "CONTRACT-CHANGE: UX-001\nreason: intentional product change"
        self.assertEqual({"UX-001"}, validator.declared_contract_ids(text))


if __name__ == "__main__":
    unittest.main()
