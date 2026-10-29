"""Offline fail-closed checks for the provider-rights inquiry queue.

This file does not read market data, personal correspondence or provider
secrets; it does not contact providers or request a production release.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "governance/score-provider-rights-followup-queue-2026-10-29.json"
RIGHTS = ROOT / "governance/score-publication-rights-gate.json"
PRIVATE = ROOT / "governance/score-private-research-migration-contract.json"


class ProviderRightsFollowupQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.queue = json.loads(QUEUE.read_text(encoding="utf-8"))

    def test_overall_rights_hold_and_no_automatic_outreach(self) -> None:
        self.assertEqual(self.queue["state"], "RIGHTS_HOLD_RESEARCH_ONLY")
        self.assertEqual(self.queue["snapshot_date"], "2026-10-29")
        self.assertTrue(self.queue["contact_policy"]["no_duplicate_outreach"])
        self.assertTrue(self.queue["contact_policy"]["no_new_paid_service"])
        self.assertTrue(self.queue["contact_policy"]["sensitive_provider_personal_details_public"] is False)
        self.assertTrue(self.queue["contact_policy"]["no_automatic_sending"])
        self.assertTrue(self.queue["authorizations"])
        for key, allowed in self.queue["authorizations"].items():
            with self.subTest(authorization=key):
                self.assertIs(allowed, False)

    def test_all_source_owners_and_transports_are_explicit(self) -> None:
        providers = self.queue["providers"]
        ids = [provider["id"] for provider in providers]
        self.assertEqual(
            set(ids),
            {
                "fred_dgs2_dgs10",
                "yahoo_delivery",
                "sp_dji_sp500",
                "cboe_vix",
                "cme_wti_gold",
                "ice_usdx",
                "treasury_h15_direct",
            },
        )
        self.assertEqual(len(ids), len(set(ids)))
        for provider in providers:
            with self.subTest(provider=provider["id"]):
                self.assertIn(provider["rights_state"], {"pending", "conditional_transient_processing_only"})
                self.assertTrue(provider["unresolved"])
                self.assertTrue(provider["next_action"])
                self.assertTrue(provider["public_reference"].startswith("https://"))
                self.assertEqual(provider["grants"]["retention"], "unapproved")
                self.assertEqual(provider["grants"]["public_aggregate_distribution"], "unapproved")
                self.assertEqual(provider["grants"]["public_component_distribution"], "unapproved")
                self.assertEqual(provider["grants"]["machine_learning_training"], "unapproved")

    def test_fred_reply_does_not_grant_storage_or_redistribution(self) -> None:
        p = {provider["id"]: provider for provider in self.queue["providers"]}
        self.assertEqual(p["fred_dgs2_dgs10"]["rights_state"], "conditional_transient_processing_only")
        self.assertEqual(
            p["fred_dgs2_dgs10"]["grants"]["commercial_transient_use"],
            "conditional_public_domain_series_with_citation_and_disposal",
        )
        self.assertEqual(p["fred_dgs2_dgs10"]["grants"]["retention"], "unapproved")
        for name, value in p.items():
            if name != "fred_dgs2_dgs10":
                self.assertEqual(value["grants"]["commercial_transient_use"], "unverified")

    def test_no_provider_queue_entry_can_change_binding_release_gates(self) -> None:
        binding = json.loads(RIGHTS.read_text(encoding="utf-8"))
        private = json.loads(PRIVATE.read_text(encoding="utf-8"))
        self.assertEqual(binding["state"], "hold")
        self.assertIsNone(binding["decision_receipt"])
        self.assertIsNone(binding["approved_by"])
        self.assertFalse(private["real_provider_evidence_authorized"])
        self.assertFalse(private["public_replacement_authorized"])
        self.assertFalse(private["production_change_authorized"])

    def test_packet_does_not_embed_private_provider_correspondence(self) -> None:
        text = QUEUE.read_text(encoding="utf-8")
        self.assertNotIn("@", text)
        self.assertNotIn("Bearer ", text)
        self.assertNotIn("api_key", text)
        self.assertNotIn("token=", text)
        self.assertNotIn("approved_public_schema", self.queue["authorizations"])


if __name__ == "__main__":
    unittest.main()
