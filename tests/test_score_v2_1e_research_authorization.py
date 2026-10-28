from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1e_research_authorization as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21EResearchAuthorizationTests(unittest.TestCase):
    def test_packet_is_hold_and_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "authorization_packet_only")
        self.assertEqual(report["decision_status"], "hold")
        self.assertFalse(report["active_authorization_receipt_present"])
        self.assertEqual(report["exact_series_count"], 8)
        self.assertFalse(report["real_data_fetch_authorized"])
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["durable_private_storage_authorized"])
        self.assertFalse(report["public_artifact_replacement_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_active_receipt_does_not_exist(self) -> None:
        self.assertFalse(
            (ROOT / "governance/score-v2-1e-real-data-research-authorization.json")
            .exists()
        )

    def test_template_has_no_approval_or_data_window(self) -> None:
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

    def test_production_is_impossible_even_in_future_research_schema(self) -> None:
        schema = json.loads(
            (
                ROOT
                / "governance/score-v2-1e-real-data-research-authorization.schema.json"
            ).read_text(encoding="utf-8")
        )
        auth_props = schema["properties"]["authorizations"]["properties"]
        self.assertFalse(auth_props["production"]["const"])
        self.assertFalse(auth_props["public_artifact_replacement"]["const"])
        self.assertFalse(auth_props["research_ledger_mutation"]["const"])
        self.assertFalse(auth_props["paid_data"]["const"])
        self.assertFalse(auth_props["source_contract_acceptance"]["const"])

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
