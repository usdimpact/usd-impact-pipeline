from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1b_official_macro_design as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21BOfficialMacroDesignTests(unittest.TestCase):
    def test_design_is_complete_but_non_executable(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "design_only")
        self.assertEqual(report["slot_count"], 8)
        self.assertTrue(report["complete_conceptual_candidate"])
        self.assertTrue(report["all_rights_pending_confirmation"])
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["methodology_activation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_all_slots_require_rights_confirmation(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1b-official-macro-design.json")
            .read_text(encoding="utf-8")
        )
        for item in design["proposed_slots"]:
            self.assertEqual(item["rights_state"], "confirm_reuse_scope")

    def test_no_missing_slot_reweighting(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1b-official-macro-design.json")
            .read_text(encoding="utf-8")
        )
        rules = design["structural_rules"]
        self.assertEqual(rules["missing_slot_policy"], "fail_closed_no_score")
        self.assertTrue(rules["no_dynamic_reweighting"])
        self.assertTrue(rules["no_unapproved_proxy_autofill"])

    def test_redundancy_and_sensitivity_are_mandatory(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1b-official-macro-design.json")
            .read_text(encoding="utf-8")
        )
        diagnostics = set(design["mandatory_research_diagnostics"])
        self.assertIn("pairwise_slot_correlation_matrix", diagnostics)
        self.assertIn("leave_one_slot_out_sensitivity", diagnostics)


if __name__ == "__main__":
    unittest.main()
