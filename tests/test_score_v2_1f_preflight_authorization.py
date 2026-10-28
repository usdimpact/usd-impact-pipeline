from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1f_preflight_authorization as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FPreflightAuthorizationTests(unittest.TestCase):
    def test_preflight_is_dispatched_but_full_research_is_not(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "live_vintage_preflight_authorized")
        self.assertEqual(report["decision_status"], "approved")
        self.assertEqual(report["exact_series_count"], 5)
        self.assertEqual(
            report["data_window"],
            {"start": "2013-01-01", "end": "2026-10-23"},
        )
        self.assertEqual(
            report["activation_merge_commit"],
            "48f6815199db7c030939629f49a75001d20ae566",
        )
        self.assertTrue(report["active_authorization_receipt_present"])
        self.assertTrue(report["dispatch_marker_present"])
        self.assertTrue(report["real_data_fetch_authorized"])
        self.assertTrue(report["live_vintage_preflight_authorized"])
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["candidate_score_computation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_dispatch_is_pinned_to_activation_merge_and_narrow_scope(self) -> None:
        dispatch = json.loads(
            (
                ROOT / "governance/score-v2-1f-live-vintage-preflight-dispatch.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(dispatch["state"], "dispatch_once")
        self.assertEqual(
            dispatch["authorization_activation_merge_commit"],
            "48f6815199db7c030939629f49a75001d20ae566",
        )
        self.assertEqual(
            dispatch["data_window"],
            {"start": "2013-01-01", "end": "2026-10-23"},
        )
        self.assertFalse(dispatch["candidate_score_computation_authorized"])
        self.assertFalse(dispatch["full_candidate_research_authorized"])
        self.assertFalse(dispatch["production_authorized"])

    def test_active_receipt_has_exact_owner_approval(self) -> None:
        receipt = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-live-vintage-preflight-authorization.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(receipt["decision_status"], "approved")
        self.assertEqual(
            receipt["approved_by"],
            "usdimpact owner via Issue #224 approval comment 6479715940",
        )
        self.assertEqual(receipt["approved_at"], "2026-10-28T20:20:28Z")

    def test_full_research_scoring_and_production_remain_forbidden(self) -> None:
        receipt = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-live-vintage-preflight-authorization.json"
            ).read_text(encoding="utf-8")
        )
        auth = receipt["authorizations"]
        self.assertTrue(auth["real_data_fetch"])
        self.assertTrue(auth["live_vintage_preflight"])
        self.assertFalse(auth["real_data_research"])
        self.assertFalse(auth["candidate_score_computation"])
        self.assertFalse(auth["public_artifact_replacement"])
        self.assertFalse(auth["research_ledger_mutation"])
        self.assertFalse(auth["production"])


if __name__ == "__main__":
    unittest.main()
