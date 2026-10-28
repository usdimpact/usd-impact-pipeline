from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1f_bls_wpu0561_row_presence_preflight as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FWpu0561RowPresenceDesignTests(unittest.TestCase):
    def test_packet_is_design_only_and_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "design_only_hold")
        self.assertEqual(
            report["issue"],
            "https://github.com/usdimpact/usd-impact-pipeline/issues/236",
        )
        self.assertEqual(report["request_budget"], 2)
        self.assertEqual(
            report["fixed_resources"],
            [
                "/ppi/detailed-report/ppi-detailed-report-april-2013.pdf",
                "/ppi/detailed-report/ppi-detailed-report-april-2026.xlsx",
            ],
        )
        self.assertFalse(report["active_receipt_present"])
        self.assertFalse(report["dispatch_present"])
        self.assertFalse(report["report_body_ephemeral_retrieval_authorized"])
        self.assertFalse(report["row_presence_preflight_authorized"])
        self.assertFalse(report["source_value_extraction_authorized"])
        self.assertFalse(report["candidate_score_computation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_design_preserves_value_boundary(self) -> None:
        design = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-design.json"
            ).read_text(encoding="utf-8")
        )
        self.assertTrue(design["forbidden"]["report_body_persistence"])
        self.assertTrue(design["forbidden"]["numeric_source_value_logging"])
        self.assertTrue(design["forbidden"]["numeric_source_value_persistence"])
        self.assertTrue(design["forbidden"]["wpu0561_value_extraction"])
        self.assertTrue(design["forbidden"]["full_historical_reconstruction"])
        self.assertTrue(design["forbidden"]["candidate_score_computation"])
        self.assertTrue(design["forbidden"]["production_change"])
        self.assertEqual(
            design["runtime_capability_policy"]["missing_pdftotext_behavior"],
            "fail_before_first_network_request",
        )


if __name__ == "__main__":
    unittest.main()
