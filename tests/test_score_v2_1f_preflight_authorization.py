from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1f_preflight_authorization as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FPreflightAuthorizationPacketTests(unittest.TestCase):
    def test_packet_is_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "authorization_packet_only")
        self.assertEqual(report["exact_series_count"], 5)
        self.assertFalse(report["active_authorization_receipt_present"])
        self.assertFalse(report["dispatch_marker_present"])
        self.assertFalse(report["live_vintage_preflight_authorized"])
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["candidate_score_computation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_template_keeps_every_authorization_false(self) -> None:
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

    def test_preflight_output_policy_forbids_values_and_score(self) -> None:
        template = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-live-vintage-preflight-authorization.template.json"
            ).read_text(encoding="utf-8")
        )
        output = template["output_policy"]
        self.assertFalse(output["source_values_in_logs"])
        self.assertFalse(output["component_values_in_logs"])
        self.assertFalse(output["candidate_score_output"])
        self.assertFalse(output["public_repo_source_values"])

    def test_active_receipt_and_dispatch_are_absent(self) -> None:
        self.assertFalse(
            (
                ROOT / "governance/score-v2-1f-live-vintage-preflight-authorization.json"
            ).exists()
        )
        self.assertFalse(
            (ROOT / "governance/score-v2-1f-live-vintage-preflight-dispatch.json").exists()
        )


if __name__ == "__main__":
    unittest.main()
