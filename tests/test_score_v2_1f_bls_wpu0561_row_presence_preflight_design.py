from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1f_bls_wpu0561_row_presence_preflight as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FWpu0561RowPresenceConsumptionTests(unittest.TestCase):
    def test_authorization_is_consumed_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(
            report["state"],
            "row_presence_preflight_consumed_fail_closed",
        )
        self.assertEqual(report["preflight_conclusion"], "success")
        self.assertEqual(report["request_count"], 2)
        self.assertTrue(report["structurally_identifiable"])
        self.assertFalse(report["active_receipt_present"])
        self.assertFalse(report["dispatch_present"])
        self.assertFalse(report["response_body_ephemeral_retrieval_authorized"])
        self.assertFalse(report["row_presence_preflight_authorized"])
        self.assertFalse(report["source_value_extraction_authorized"])
        self.assertFalse(report["candidate_score_computation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_consumption_record_preserves_structural_pass_without_values(self) -> None:
        record = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-consumption-2026-10-28.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(record["owner_approval_comment_id"], 6481426895)
        self.assertEqual(record["preflight_conclusion"], "success")
        self.assertEqual(record["sanitized_result"]["request_count"], 2)
        self.assertTrue(record["sanitized_result"]["structurally_identifiable"])
        self.assertTrue(record["sanitized_result"]["html_2013_05_61_seen"])
        self.assertTrue(record["sanitized_result"]["xlsx_2026_crude_petroleum_seen"])
        self.assertFalse(record["sanitized_result"]["response_bodies_persisted"])
        self.assertFalse(record["sanitized_result"]["numeric_source_values_extracted"])
        self.assertFalse(record["sanitized_result"]["numeric_source_values_logged"])
        self.assertFalse(record["sanitized_result"]["numeric_source_values_persisted"])
        self.assertFalse(record["sanitized_result"]["wpu0561_numeric_value_extracted"])
        self.assertTrue(
            record["new_owner_authorization_required_for_any_future_live_request"]
        )

    def test_every_post_consumption_authorization_is_false(self) -> None:
        record = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-consumption-2026-10-28.json"
            ).read_text(encoding="utf-8")
        )
        self.assertFalse(any(record["post_consumption_authorizations"].values()))


if __name__ == "__main__":
    unittest.main()
