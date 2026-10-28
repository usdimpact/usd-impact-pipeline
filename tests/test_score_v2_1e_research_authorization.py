from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1e_research_authorization as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21EResearchAuthorizationTests(unittest.TestCase):
    def test_one_off_authorization_is_consumed_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "one_off_private_research_consumed_fail_closed")
        self.assertFalse(report["active_authorization_receipt_present"])
        self.assertEqual(report["data_window"], {"start": "2013-01-01", "end": "2026-10-23"})
        self.assertFalse(report["real_data_fetch_authorized"])
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["candidate_score_computed"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_active_receipt_is_absent(self) -> None:
        self.assertFalse(
            (ROOT / "governance/score-v2-1e-real-data-research-authorization.json").exists()
        )

    def test_owner_approval_is_preserved_as_consumed_audit_evidence(self) -> None:
        record = json.loads(
            (ROOT / "governance/score-v2-1e-real-data-research-consumption-2026-10-28.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(record["owner_approval_comment_id"], 6477834394)
        self.assertEqual(record["owner_approval_timestamp"], "2026-10-28T18:55:48Z")
        self.assertEqual(
            record["failed_run"],
            "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40755916179",
        )
        self.assertEqual(
            record["blocker_issue"],
            "https://github.com/usdimpact/usd-impact-pipeline/issues/218",
        )
        self.assertTrue(record["new_owner_authorization_required_for_any_future_real_data_run"])

    def test_every_post_consumption_authorization_is_false(self) -> None:
        record = json.loads(
            (ROOT / "governance/score-v2-1e-real-data-research-consumption-2026-10-28.json")
            .read_text(encoding="utf-8")
        )
        self.assertFalse(any(record["post_consumption_authorizations"].values()))
        self.assertFalse(record["research_result"]["candidate_score_computed"])
        self.assertFalse(record["research_result"]["source_or_component_values_persisted"])

    def test_template_remains_hold(self) -> None:
        template = json.loads(
            (ROOT / "governance/score-v2-1e-real-data-research-authorization.template.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(template["decision_status"], "hold")
        self.assertIsNone(template["approved_by"])
        self.assertIsNone(template["approved_at"])
        self.assertEqual(template["data_window"], {"start": None, "end": None})
        self.assertFalse(any(template["authorizations"].values()))


if __name__ == "__main__":
    unittest.main()
