"""Offline regression on the published FRED terms clause crosswalk and rights HOLD.

This test does not contact FRED, Gmail, market-data providers or production.
It reads only documentation, policy and governance text in this repository.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CROSSWALK = ROOT / "governance/fred-terms-clause-crosswalk-2026-10-29.json"
RIGHTS = ROOT / "governance/score-publication-rights-gate.json"
SOURCE_POLICY = ROOT / "docs/source-retention-policy.md"
AUDIT = ROOT / "docs/issue-282-fred-retention-inventory-2026-10-29.md"


class FredTermsClauseCrosswalkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(CROSSWALK.read_text(encoding="utf-8"))

    def test_current_public_services_vs_api_clauses_not_inverted(self) -> None:
        self.assertEqual(self.data["verified_on"], "2026-10-29")
        self.assertEqual(
            self.data["public_primary_source"],
            "https://fred.stlouisfed.org/legal/terms/",
        )
        services = self.data["sections"]["fred_services"]
        self.assertIn("AI/ML", services["p"])
        self.assertIn("storage", services["q"])
        self.assertIn("deriv", services["r"])
        api = self.data["sections"]["fred_api"]
        self.assertIn("AI/ML", api["k"])
        self.assertIn("storage", api["l"])

    def test_authoritative_policy_and_audit_match_current_clause_labels(self) -> None:
        policy = SOURCE_POLICY.read_text(encoding="utf-8")
        audit = AUDIT.read_text(encoding="utf-8")
        for name, content in (("policy", policy), ("audit", audit)):
            with self.subTest(document=name):
                self.assertIn("Services (p)", content)
                self.assertIn("Services (q)", content)
                self.assertIn("Services (r)", content)
                self.assertIn("API (k)", content)
                self.assertIn("API (l)", content)
        self.assertNotIn("Services storage/cache/archive in clause (p)", policy)
        self.assertNotIn("General Services prohibition (p) for storage", audit)

    def test_private_provider_mail_was_not_copied_into_public_register(self) -> None:
        evidence = self.data["email_evidence"]
        self.assertEqual(evidence["attachments_in_retrieved_provider_messages"], 0)
        self.assertEqual(evidence["provider_inbound_messages_scoped"]["fred"], 1)
        self.assertEqual(evidence["provider_inbound_messages_scoped"]["sp_dji"], 2)
        self.assertEqual(evidence["provider_inbound_messages_scoped"]["cboe"], 2)
        self.assertNotIn("@", CROSSWALK.read_text(encoding="utf-8"))

    def test_no_rights_grants_or_production_decision(self) -> None:
        for key, permitted in self.data["authorizations"].items():
            with self.subTest(control=key):
                self.assertIs(permitted, False)
        rights = json.loads(RIGHTS.read_text(encoding="utf-8"))
        self.assertEqual(rights["state"], "hold")
        self.assertIsNone(rights["decision_receipt"])
        self.assertIsNone(rights["approved_by"])


if __name__ == "__main__":
    unittest.main()
