from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1c_federal_source_design as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21CFederalSourceDesignTests(unittest.TestCase):
    def test_design_is_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "design_only")
        self.assertEqual(report["slot_count"], 8)
        self.assertTrue(report["no_source_approved"])
        self.assertFalse(report["legal_conclusion"])
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_nfc_and_stlfsi_are_deprioritized_only_in_v21c(self) -> None:
        rights = json.loads(
            (ROOT / "governance/score-v2-1c-public-rights-evidence.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(
            {item["series"] for item in rights["rejected_or_deprioritized"]},
            {"NFCI", "STLFSI4"},
        )

    def test_all_rights_rows_retain_unresolved_checks(self) -> None:
        rights = json.loads(
            (ROOT / "governance/score-v2-1c-public-rights-evidence.json")
            .read_text(encoding="utf-8")
        )
        for row in rights["rows"]:
            self.assertTrue(row["unresolved"])

    def test_fci_g_monthly_staleness_is_explicit(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1c-federal-source-design.json")
            .read_text(encoding="utf-8")
        )
        timing = design["timing_constraints"]
        self.assertEqual(timing["FCI_G_max_age_calendar_days"], 45)
        self.assertTrue(timing["mixed_frequency_fail_closed"])


if __name__ == "__main__":
    unittest.main()
