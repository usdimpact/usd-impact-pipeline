from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1f_bls_detailed_report_metadata_preflight as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FBlsDetailedReportMetadataPreflightDispatchTests(unittest.TestCase):
    def test_packet_is_dispatched_but_narrow(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "metadata_preflight_authorized")
        self.assertEqual(
            report["activation_merge_commit"],
            "59cd5e6b1cd47f3d04eec6588697d252ff93cff2",
        )
        self.assertEqual(report["request_budget"], 4)
        self.assertEqual(report["allowed_host"], "www.bls.gov")
        self.assertTrue(report["active_receipt_present"])
        self.assertTrue(report["dispatch_present"])
        self.assertTrue(report["network_metadata_fetch_authorized"])
        self.assertTrue(report["bls_metadata_preflight_authorized"])
        self.assertFalse(report["candidate_score_computation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_dispatch_is_pinned_to_activation_and_forbids_broader_work(self) -> None:
        dispatch = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-bls-detailed-report-metadata-preflight-dispatch.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(dispatch["state"], "approved_dispatch")
        self.assertEqual(
            dispatch["authorization_activation_merge_commit"],
            "59cd5e6b1cd47f3d04eec6588697d252ff93cff2",
        )
        self.assertEqual(dispatch["request_budget"], 4)
        self.assertEqual(dispatch["allowed_host"], "www.bls.gov")
        self.assertFalse(dispatch["report_body_download_authorized"])
        self.assertFalse(dispatch["source_value_retrieval_authorized"])
        self.assertFalse(dispatch["real_data_research_authorized"])
        self.assertFalse(dispatch["candidate_score_computation_authorized"])
        self.assertFalse(dispatch["production_authorized"])

    def test_receipt_preserves_exact_owner_approval(self) -> None:
        receipt = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-bls-detailed-report-metadata-preflight-authorization.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            receipt["approved_by"],
            "usdimpact owner via Issue #230 approval comment 6480432536",
        )
        self.assertEqual(receipt["approved_at"], "2026-10-28T20:53:16Z")
        self.assertEqual(receipt["request_budget"], 4)
        self.assertIn("support@usd-impact.com", receipt["contact_user_agent"])


if __name__ == "__main__":
    unittest.main()
