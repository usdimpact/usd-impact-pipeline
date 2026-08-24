import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_methodology_contract import (
    DEFAULT_CONTRACT,
    DEFAULT_SCHEMA,
    expected_contract,
    validate_contract,
)


class MethodologyContractTests(unittest.TestCase):
    def test_public_contract_matches_production_constants_exactly(self):
        result = validate_contract()
        self.assertEqual(result["methodology_version"], "usd_impact_score_v2")
        self.assertEqual(result["contract_version"], 1)
        self.assertEqual(result["driver_count"], 8)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(len(result["contract_sha256"]), 64)

    def test_expected_contract_preserves_equal_absolute_weight_budget(self):
        contract = expected_contract()
        weights = [float(driver["weight"]) for driver in contract["drivers"]]
        self.assertAlmostEqual(sum(abs(weight) for weight in weights), 1.0, places=12)
        self.assertFalse(contract["predictive_claim"])
        self.assertEqual(contract["correlation_adjustment"], "none")
        self.assertFalse(contract["weights_rebalanced"])
        self.assertEqual(
            contract["reproduction_bundle"]["required_from_release"], "2026-08-28"
        )

    def test_tampered_public_weight_fails_closed(self):
        contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
        schema = DEFAULT_SCHEMA.read_text(encoding="utf-8")
        contract["drivers"][0]["weight"] = 0.126

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = root / "methodology.json"
            schema_path = root / "schema.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            schema_path.write_text(schema, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "differs from production constants"):
                validate_contract(contract_path, schema_path)

    def test_schema_is_closed_and_covers_every_top_level_contract_field(self):
        schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))
        contract = expected_contract()
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), set(contract))
        self.assertEqual(set(schema["properties"]), set(contract))


if __name__ == "__main__":
    unittest.main()
