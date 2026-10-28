from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1e_federal_bls_design as validator

ROOT = Path(__file__).resolve().parents[1]

class ScoreV21EFederalBLSDesignTests(unittest.TestCase):
    def test_design_is_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "design_only")
        self.assertEqual(report["slot_count"], 8)
        self.assertTrue(report["exact_series_pinned"])
        self.assertTrue(report["refinitiv_wti_dependency_removed"])
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_energy_is_bls_wpu0561(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1e-federal-bls-design.json")
            .read_text(encoding="utf-8")
        )
        energy = next(item for item in design["proposed_slots"] if item["slot"] == "ENERGY")
        self.assertEqual(energy["source_family"], "U.S. Bureau of Labor Statistics")
        self.assertEqual(energy["exact_series_id"], "WPU0561")
        self.assertIn("four months", energy["revision_rule"].lower())

    def test_prior_wti_dependency_is_absent(self) -> None:
        text = (
            ROOT / "governance/score-v2-1e-federal-bls-design.json"
        ).read_text(encoding="utf-8").lower()
        for forbidden in ("dcoilwtico", "rwtc", "refinitiv", "lseg"):
            self.assertNotIn(forbidden, text)

    def test_exact_direct_identifiers_are_stable(self) -> None:
        receipts = json.loads(
            (ROOT / "governance/score-v2-1e-exact-series-receipts.json")
            .read_text(encoding="utf-8")
        )
        by_slot = {row["slot"]: row["exact_series_id"] for row in receipts["series_receipts"]}
        self.assertEqual(by_slot["USD"], "H10/H10/JRXWTFB_N.B")
        self.assertEqual(by_slot["FIN_CONDITIONS"], "H8/H8/B1001NCBA")
        self.assertEqual(by_slot["FIN_STRESS"], "H41/H41/RESPPALDP_N.WW")
        self.assertEqual(by_slot["LIQUIDITY"], "H41/H41/RESPPA_N.WW")
        self.assertEqual(by_slot["REAL_YIELD"], "H15/H15/RIFLGFCY10_XII_N.B")
        self.assertEqual(by_slot["UST_2Y"], "H15/H15/RIFLGFCY02_N.B")
        self.assertEqual(by_slot["UST_10Y"], "H15/H15/RIFLGFCY10_N.B")

if __name__ == "__main__":
    unittest.main()
