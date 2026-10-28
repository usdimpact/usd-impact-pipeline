from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1f_preflight_authorization as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FPreflightAuthorizationTests(unittest.TestCase):
    def test_stage1_authorization_is_consumed_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(
            report["state"],
            "live_vintage_preflight_consumed_fail_closed",
        )
        self.assertFalse(report["active_authorization_receipt_present"])
        self.assertFalse(report["dispatch_marker_present"])
        self.assertEqual(
            report["data_window"],
            {"start": "2013-01-01", "end": "2026-10-23"},
        )
        self.assertEqual(report["preflight_conclusion"], "failure")
        self.assertEqual(report["blocker_http_status"], 403)
        self.assertTrue(report["federal_reserve_phase_completed_before_bls_request"])
        self.assertFalse(report["real_data_fetch_authorized"])
        self.assertFalse(report["live_vintage_preflight_authorized"])
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["candidate_score_computation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_consumption_record_preserves_owner_and_run_evidence(self) -> None:
        record = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-live-vintage-preflight-consumption-2026-10-28.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(record["owner_approval_comment_id"], 6479715940)
        self.assertEqual(record["owner_approval_timestamp"], "2026-10-28T20:20:28Z")
        self.assertEqual(
            record["authorization_activation_merge_commit"],
            "48f6815199db7c030939629f49a75001d20ae566",
        )
        self.assertEqual(
            record["dispatch_merge_commit"],
            "6ea7eb7390ad9949799867c6db38f20664cba6a3",
        )
        self.assertEqual(
            record["preflight_run"],
            "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40763350781",
        )
        self.assertEqual(
            record["blocker_issue"],
            "https://github.com/usdimpact/usd-impact-pipeline/issues/228",
        )
        self.assertEqual(record["failure"]["http_status"], 403)
        self.assertTrue(
            record["new_owner_authorization_required_for_any_future_live_request"]
        )

    def test_every_post_consumption_authorization_is_false(self) -> None:
        record = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-live-vintage-preflight-consumption-2026-10-28.json"
            ).read_text(encoding="utf-8")
        )
        self.assertFalse(any(record["post_consumption_authorizations"].values()))
        self.assertFalse(record["research_result"]["candidate_score_computed"])
        self.assertFalse(record["research_result"]["component_zscores_computed"])
        self.assertFalse(record["research_result"]["source_or_component_values_persisted"])

    def test_active_receipt_and_dispatch_are_absent(self) -> None:
        self.assertFalse(
            (ROOT / "governance/score-v2-1f-live-vintage-preflight-authorization.json").exists()
        )
        self.assertFalse(
            (ROOT / "governance/score-v2-1f-live-vintage-preflight-dispatch.json").exists()
        )

    def test_template_remains_hold(self) -> None:
        template = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-live-vintage-preflight-authorization.template.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(template["decision_status"], "hold")
        self.assertEqual(template["data_window"], {"start": None, "end": None})
        self.assertIsNone(template["approved_by"])
        self.assertIsNone(template["approved_at"])
        self.assertFalse(any(template["authorizations"].values()))


if __name__ == "__main__":
    unittest.main()
