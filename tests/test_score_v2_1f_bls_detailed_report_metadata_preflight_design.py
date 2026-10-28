from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1f_bls_detailed_report_metadata_preflight as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FBlsDetailedReportMetadataPreflightActivationTests(unittest.TestCase):
    def test_packet_is_authorized_but_pending_dispatch(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(
            report["state"],
            "metadata_preflight_authorized_pending_dispatch",
        )
        self.assertEqual(
            report["issue"],
            "https://github.com/usdimpact/usd-impact-pipeline/issues/230",
        )
        self.assertEqual(report["request_budget"], 4)
        self.assertEqual(report["allowed_host"], "www.bls.gov")
        self.assertTrue(report["active_receipt_present"])
        self.assertFalse(report["dispatch_present"])
        self.assertTrue(report["network_metadata_fetch_authorized"])
        self.assertTrue(report["bls_metadata_preflight_authorized"])
        self.assertFalse(report["candidate_score_computation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_receipt_preserves_exact_owner_approval_and_narrow_scope(self) -> None:
        receipt = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-bls-detailed-report-metadata-preflight-authorization.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(receipt["decision_status"], "approved")
        self.assertEqual(
            receipt["data_window"],
            {"start": "2013-01-01", "end": "2026-10-23"},
        )
        self.assertEqual(receipt["request_budget"], 4)
        self.assertEqual(receipt["allowed_host"], "www.bls.gov")
        self.assertEqual(
            receipt["approved_by"],
            "usdimpact owner via Issue #230 approval comment 6480432536",
        )
        self.assertEqual(receipt["approved_at"], "2026-10-28T20:53:16Z")
        self.assertIn("support@usd-impact.com", receipt["contact_user_agent"])
        self.assertTrue(receipt["authorizations"]["network_metadata_fetch"])
        self.assertTrue(receipt["authorizations"]["bls_metadata_preflight"])
        self.assertFalse(receipt["authorizations"]["report_body_download"])
        self.assertFalse(receipt["authorizations"]["source_value_retrieval"])
        self.assertFalse(receipt["authorizations"]["candidate_score_computation"])
        self.assertFalse(receipt["authorizations"]["production"])

    def test_design_evidence_remains_frozen(self) -> None:
        design = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-bls-detailed-report-metadata-preflight-design.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            design["research_findings"]["preferred_official_route"],
            "/ppi/detailed-report/",
        )
        self.assertIn(
            "February 2016",
            design["research_findings"]["known_correction_metadata"],
        )
        self.assertIn(
            "October 2025",
            design["research_findings"]["known_gap_metadata"],
        )
        self.assertTrue(design["forbidden"]["pdf_or_xlsx_body_download"])
        self.assertTrue(design["forbidden"]["wpu0561_value_retrieval"])
        self.assertTrue(design["forbidden"]["candidate_score_computation"])
        self.assertTrue(design["forbidden"]["production_change"])


if __name__ == "__main__":
    unittest.main()
