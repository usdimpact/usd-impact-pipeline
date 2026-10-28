from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1e_research_authorization as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21EResearchAuthorizationTests(unittest.TestCase):
    def test_one_off_research_is_authorized_but_production_is_not(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "one_off_private_research_authorized")
        self.assertEqual(report["decision_status"], "approved")
        self.assertTrue(report["active_authorization_receipt_present"])
        self.assertEqual(report["exact_series_count"], 8)
        self.assertEqual(
            report["data_window"],
            {"start": "2013-01-01", "end": "2026-10-23"},
        )
        self.assertTrue(report["real_data_fetch_authorized"])
        self.assertTrue(report["real_data_research_authorized"])
        self.assertFalse(report["durable_private_storage_authorized"])
        self.assertFalse(report["public_artifact_replacement_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_active_receipt_has_exact_owner_approval(self) -> None:
        receipt = json.loads(
            (
                ROOT / "governance/score-v2-1e-real-data-research-authorization.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(receipt["decision_status"], "approved")
        self.assertEqual(
            receipt["approved_by"],
            "usdimpact owner via Issue #209 approval comment 6477834394",
        )
        self.assertEqual(receipt["approved_at"], "2026-10-28T18:55:48Z")
        self.assertEqual(
            receipt["data_window"],
            {"start": "2013-01-01", "end": "2026-10-23"},
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

    def test_non_research_actions_are_hard_forbidden(self) -> None:
        receipt = json.loads(
            (
                ROOT / "governance/score-v2-1e-real-data-research-authorization.json"
            ).read_text(encoding="utf-8")
        )
        auth = receipt["authorizations"]
        self.assertTrue(auth["real_data_fetch"])
        self.assertTrue(auth["real_data_research"])
        self.assertFalse(auth["production"])
        self.assertFalse(auth["public_artifact_replacement"])
        self.assertFalse(auth["research_ledger_mutation"])
        self.assertFalse(auth["paid_data"])
        self.assertFalse(auth["source_contract_acceptance"])

    def test_execution_contract_allows_only_official_direct_hosts(self) -> None:
        contract = json.loads(
            (
                ROOT / "governance/score-v2-1e-real-data-execution-contract.json"
            ).read_text(encoding="utf-8")
        )
        hosts = set(contract["network_policy"]["allowed_hosts"])
        self.assertIn("www.federalreserve.gov", hosts)
        self.assertIn("www.bls.gov", hosts)
        self.assertIn("data.bls.gov", hosts)
        self.assertFalse(contract["network_policy"]["credentials_required"])
        self.assertIn("Refinitiv", contract["network_policy"]["disallowed_source_families"])
        self.assertIn("Yahoo", contract["network_policy"]["disallowed_source_families"])


if __name__ == "__main__":
    unittest.main()
