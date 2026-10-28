from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FWpu0561ValueFieldDesignTests(unittest.TestCase):
    def test_design_is_hold_and_live_work_is_false(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1f-bls-wpu0561-value-field-preflight-design.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(design["state"], "design_only_hold")
        self.assertEqual(
            design["owner_decision_issue"],
            "https://github.com/usdimpact/usd-impact-pipeline/issues/245",
        )
        self.assertEqual(design["future_live_budget"]["requests"], 2)
        self.assertEqual(
            design["future_live_budget"]["max_numeric_observations_extracted"], 2
        )
        self.assertEqual(
            design["allowed_field_semantics"],
            ["index_level_original_release"],
        )
        self.assertIn(
            "monthly_percent_change",
            design["explicitly_rejected_semantics"],
        )
        self.assertTrue(design["forbidden_now"]["live_bls_request"])
        self.assertTrue(design["forbidden_now"]["numeric_value_extraction"])
        self.assertTrue(design["forbidden_now"]["full_historical_reconstruction"])
        self.assertFalse(any(design["current_authorizations"].values()))

    def test_contract_and_workflow_are_inert(self) -> None:
        contract = json.loads(
            (ROOT / "governance/score-v2-1f-bls-wpu0561-value-field-preflight-execution-contract.json")
            .read_text(encoding="utf-8")
        )
        workflow = (
            ROOT / ".github/workflows/score-v2-1f-bls-wpu0561-value-field-preflight.yml"
        ).read_text(encoding="utf-8")
        self.assertEqual(contract["state"], "design_only_hold")
        self.assertFalse(any(contract["current_state"].values()))
        self.assertFalse(contract["production_authorized"])
        self.assertIn("if: ${{ false }}", workflow)


if __name__ == "__main__":
    unittest.main()
