from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1d_direct_release_design as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21DDirectReleaseDesignTests(unittest.TestCase):
    def test_design_is_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "design_only")
        self.assertEqual(report["slot_count"], 8)
        self.assertEqual(report["composite_private_input_slots"], 0)
        self.assertEqual(report["direct_board_slots"], 7)
        self.assertEqual(report["direct_eia_slots"], 1)
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_direct_replacements_are_frozen(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1d-direct-release-design.json")
            .read_text(encoding="utf-8")
        )
        by_slot = {item["slot"]: item for item in design["proposed_slots"]}
        self.assertEqual(
            by_slot["FIN_CONDITIONS"]["source_key"],
            "BOARD_H8_BANK_CREDIT_ALL",
        )
        self.assertEqual(
            by_slot["FIN_CONDITIONS"]["transform"],
            "negative_log_change_13_weeks",
        )
        self.assertEqual(
            by_slot["FIN_STRESS"]["source_key"],
            "BOARD_H41_PRIMARY_CREDIT",
        )
        self.assertEqual(by_slot["FIN_STRESS"]["transform"], "log1p_level")

    def test_release_provenance_remains_mandatory(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1d-direct-release-design.json")
            .read_text(encoding="utf-8")
        )
        rules = design["structural_rules"]
        self.assertTrue(rules["observation_date_is_not_release_date"])
        self.assertTrue(rules["point_in_time_release_provenance_required"])
        self.assertEqual(rules["missing_slot_policy"], "fail_closed_no_score")

    def test_no_source_is_approved(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1d-direct-release-design.json")
            .read_text(encoding="utf-8")
        )
        self.assertTrue(design["no_source_approved"])
        self.assertFalse(design["legal_conclusion"])
        self.assertFalse(design["production_authorized"])


if __name__ == "__main__":
    unittest.main()
