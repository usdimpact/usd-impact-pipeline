from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1e_research_authorization as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21EResearchAuthorizationTests(unittest.TestCase):
    def test_blocked_authorization_is_consumed_and_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "blocked_fail_closed_authorization_consumed")
        self.assertEqual(report["decision_status"], "consumed_after_blocker")
        self.assertFalse(report["active_authorization_receipt_present"])
        self.assertTrue(report["archived_owner_approval_present"])
        self.assertEqual(report["exact_series_count"], 8)
        self.assertEqual(
            report["data_window"],
            {"start": "2013-01-01", "end": "2026-10-23"},
        )
        self.assertEqual(
            report["hard_blocker"],
            "H15_historical_release_vintage_unavailable",
        )
        self.assertFalse(report["real_data_fetch_authorized"])
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["full_candidate_score_computed"])
        self.assertFalse(report["public_artifact_replacement_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_active_receipt_is_absent_and_owner_approval_is_archived(self) -> None:
        self.assertFalse(
            (ROOT / "governance/score-v2-1e-real-data-research-authorization.json")
            .exists()
        )
        archived = json.loads(
            (
                ROOT
                / "governance/archive/score-v2-1e-real-data-research-authorization-2026-10-28.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(archived["decision_status"], "approved")
        self.assertEqual(
            archived["approved_by"],
            "usdimpact owner via Issue #209 approval comment 6477834394",
        )
        self.assertEqual(archived["approved_at"], "2026-10-28T18:55:48Z")

    def test_outcome_records_h15_fail_closed_blocker(self) -> None:
        outcome = json.loads(
            (
                ROOT
                / "governance/score-v2-1e-real-data-research-outcome-2026-10-28.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(outcome["state"], "blocked_fail_closed")
        self.assertEqual(outcome["hard_blocker"]["slot_family"], "H15")
        self.assertFalse(
            outcome["hard_blocker"]["current_revised_history_substitution_allowed"]
        )
        self.assertTrue(
            outcome["authorization_consumption"]["one_off_authorization_consumed"]
        )
        self.assertFalse(
            outcome["authorization_consumption"]["further_real_data_fetch_authorized"]
        )
        self.assertFalse(
            outcome["authorization_consumption"]["further_real_data_research_authorized"]
        )

    def test_template_remains_hold(self) -> None:
        template = json.loads(
            (
                ROOT
                / "governance/score-v2-1e-real-data-research-authorization.template.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(template["decision_status"], "hold")
        self.assertIsNone(template["approved_by"])
        self.assertIsNone(template["approved_at"])
        self.assertEqual(template["data_window"], {"start": None, "end": None})
        self.assertFalse(any(template["authorizations"].values()))

    def test_execution_contract_is_fully_deactivated(self) -> None:
        contract = json.loads(
            (
                ROOT / "governance/score-v2-1e-real-data-execution-contract.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            contract["state"],
            "blocked_fail_closed_authorization_consumed",
        )
        self.assertFalse(contract["active_authorization_receipt_expected_now"])
        current = contract["current_state"]
        self.assertTrue(current["one_off_authorization_consumed"])
        self.assertFalse(current["real_data_fetch_authorized"])
        self.assertFalse(current["real_data_research_authorized"])
        self.assertFalse(current["production_authorized"])
        self.assertFalse(current["public_artifact_replacement_authorized"])


if __name__ == "__main__":
    unittest.main()
