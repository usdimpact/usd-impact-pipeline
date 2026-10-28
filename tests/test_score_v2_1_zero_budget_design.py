from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1_zero_budget_design as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21ZeroBudgetDesignTests(unittest.TestCase):
    def test_design_is_fail_closed_and_formula_isolated(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "design_only")
        self.assertEqual(report["driver_count"], 8)
        self.assertTrue(report["phase_1_formula_equal_to_v2"])
        self.assertFalse(report["complete_zero_budget_candidate_exists"])
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["methodology_activation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_blocked_drivers_have_no_preselected_proxy(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1-zero-budget-design.json")
            .read_text(encoding="utf-8")
        )
        by_driver = {item["driver"]: item for item in design["drivers"]}
        for driver in ("SPX", "VIX", "BTC", "GOLD"):
            self.assertIsNone(by_driver[driver]["zero_budget_candidate"])
            self.assertTrue(by_driver[driver]["silent_replacement_forbidden"])

    def test_phase_one_forbids_reweighting_and_proxy_autofill(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1-zero-budget-design.json")
            .read_text(encoding="utf-8")
        )
        protocol = design["research_protocol"]
        self.assertEqual(protocol["incomplete_driver_policy"], "fail_closed_no_score")
        self.assertTrue(protocol["no_reweighting_for_missing_driver"])
        self.assertTrue(protocol["no_proxy_autofill"])

    def test_thresholds_are_not_selected_before_preregistration(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1-zero-budget-design.json")
            .read_text(encoding="utf-8")
        )
        prereg = json.loads(
            (ROOT / "governance/score-v2-1-research-preregistration.template.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(
            design["research_protocol"]["acceptance_thresholds"]["status"],
            "not_set",
        )
        self.assertIsNone(prereg["fields"]["thresholds"])
        self.assertFalse(prereg["real_data_research_authorized"])

    def test_v2_history_is_immutable(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1-zero-budget-design.json")
            .read_text(encoding="utf-8")
        )
        versioning = design["versioning"]
        self.assertTrue(versioning["v2_history_rewrite_forbidden"])
        self.assertTrue(versioning["v2_1_must_be_new_methodology_version"])
        self.assertTrue(
            versioning["v2_and_v2_1_must_not_be_spliced_into_one_unversioned_series"]
        )


if __name__ == "__main__":
    unittest.main()
