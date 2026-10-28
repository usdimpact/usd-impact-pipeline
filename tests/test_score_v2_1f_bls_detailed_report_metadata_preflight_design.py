from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1f_bls_detailed_report_metadata_preflight as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FBlsDetailedReportMetadataPreflightConsumptionTests(unittest.TestCase):
    def test_authorization_is_consumed_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "metadata_preflight_consumed_fail_closed")
        self.assertEqual(report["preflight_conclusion"], "success")
        self.assertEqual(report["request_count"], 4)
        self.assertTrue(report["report_resource_2013_present"])
        self.assertTrue(report["report_resource_2026_present"])
        self.assertTrue(report["october_2025_not_available_label_seen"])
        self.assertTrue(report["february_2016_correction_label_seen"])
        self.assertFalse(report["active_receipt_present"])
        self.assertFalse(report["dispatch_present"])
        self.assertFalse(report["network_metadata_fetch_authorized"])
        self.assertFalse(report["bls_metadata_preflight_authorized"])
        self.assertFalse(report["candidate_score_computation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_consumption_record_preserves_success_evidence(self) -> None:
        record = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-bls-detailed-report-metadata-preflight-consumption-2026-10-28.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(record["owner_approval_comment_id"], 6480432536)
        self.assertEqual(
            record["authorization_activation_merge_commit"],
            "59cd5e6b1cd47f3d04eec6588697d252ff93cff2",
        )
        self.assertEqual(
            record["dispatch_merge_commit"],
            "8348c276ecc12053501f444d9a55e1c6572612f5",
        )
        self.assertEqual(
            record["preflight_run"],
            "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40768295606",
        )
        self.assertEqual(record["preflight_conclusion"], "success")
        self.assertEqual(record["sanitized_result"]["request_count"], 4)
        self.assertFalse(record["sanitized_result"]["report_bodies_downloaded"])
        self.assertFalse(record["sanitized_result"]["source_values_retrieved"])
        self.assertFalse(record["sanitized_result"]["candidate_score_computed"])
        self.assertTrue(
            record["new_owner_authorization_required_for_any_future_live_request"]
        )

    def test_every_post_consumption_authorization_is_false(self) -> None:
        record = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-bls-detailed-report-metadata-preflight-consumption-2026-10-28.json"
            ).read_text(encoding="utf-8")
        )
        self.assertFalse(any(record["post_consumption_authorizations"].values()))

    def test_active_receipt_and_dispatch_are_absent(self) -> None:
        self.assertFalse(
            (
                ROOT
                / "governance/score-v2-1f-bls-detailed-report-metadata-preflight-authorization.json"
            ).exists()
        )
        self.assertFalse(
            (
                ROOT
                / "governance/score-v2-1f-bls-detailed-report-metadata-preflight-dispatch.json"
            ).exists()
        )


if __name__ == "__main__":
    unittest.main()
