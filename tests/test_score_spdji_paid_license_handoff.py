"""Offline governance tests for S&P's scoped paid-license response.

Never reads Gmail, real Score observations, provider terms or secrets. This
test asserts only the conservatively recorded *negative* disposition; it is
not evidence that a paid license was executed or that other sources are clear.
"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS_FILE = ROOT / "governance/score-spdji-provider-disposition-2026-10-30.json"
OLDER_QUEUE = ROOT / "governance/score-provider-rights-followup-queue-2026-10-29.json"
OLDER_COVERAGE = ROOT / "governance/score-rights-seven-provider-coverage-2026-10-29.json"
CURRENT_POLICY = ROOT / "governance/score-publication-rights-gate.json"
REVIEW_PACKET = ROOT / "governance/score-v2-public-schema-retention-review-2026-10-30.json"
DOC = ROOT / "docs/score-provider-rights-followup-packet-2026-10-29.md"

EXPECTED_GATES = {
    "existing_score_publication", "aggregate_score_publication",
    "score_source_switch", "original_engine_or_weight_change",
    "provider_fetch_or_data_copy", "new_paid_license_contract",
    "market_data_purchase", "historical_artifact_delete_or_purge",
    "historical_retention_or_private_storage",
    "independent_macro_context_panel_release",
    "website_or_cloudflare_deployment", "rights_gate_allow",
}
EXPECTED_PUBLIC_FIELDS = {
    "week_ending_date", "non_reconstructible_aggregate_score",
    "regime_label", "aggregate_score_history",
}


def fail_if_disposition_is_upgraded(status: dict) -> None:
    """Prevent an accidental grant, budget change or no-cost conclusion."""
    if status.get("schema_version") != "score-spdji-provider-disposition-review-v1":
        raise ValueError("unsupported provider response record")
    if status.get("review_state") != "PROVIDER_PAID_LICENSE_REQUIRED_NO_BUDGET_HOLD":
        raise ValueError("paid-license response must remain on HOLD")
    if status.get("source_relationship_id") != "sp_dji_sp500":
        raise ValueError("unexpected source relationship")
    if status.get("source_evidence_location") != "existing_private_correspondence_only":
        raise ValueError("private evidence cannot be embedded in public Git")
    if status.get("private_correspondence_copied_to_repository") is not False:
        raise ValueError("private correspondence cannot be copied")
    if status.get("sender_name_case_number_or_private_contact_included") is not False:
        raise ValueError("private sender details are disallowed")
    response = status.get("provider_reply", {})
    required = {
        "paid_license_required_for_described_request": True,
        "separate_internal_vs_public_license_exemptions_expressly_resolved": False,
        "written_no_fee_aggregate_permission_received": False,
        "paid_license_executed": False,
        "separately_scoped_component_rights_approved": False,
        "historic_artifact_remediation_direction_received": False,
    }
    if response.get("categorization") != "PAID_LICENSE_REQUIRED_FOR_DESCRIBED_USE_CASE":
        raise ValueError("provider answer misclassified")
    for name, expected in required.items():
        if response.get(name) is not expected:
            raise ValueError("provider reply permission/status drift: " + name)
    economics = status.get("economics", {})
    expected_economics = {
        "authorized_additional_market_data_license_budget_usd": 0,
        "paid_license_purchase_authorized": False,
        "original_eight_driver_score_zero_budget_release_viable": False,
        "separately_licensed_future_path_may_be_reviewed_by_owner": True,
        "independent_four_signal_panel_is_not_legacy_score": True,
    }
    if economics != expected_economics:
        raise ValueError("budget/no-cost Score boundary drift")
    gates = status.get("authorizations", {})
    if set(gates) != EXPECTED_GATES or any(v is not False for v in gates.values()):
        raise ValueError("a provider reply cannot grant operation or release")


class SpdjiPaidLicenseResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = json.loads(STATUS_FILE.read_text(encoding="utf-8"))

    def test_scoped_no_fee_path_blocked_without_claiming_unanswered_details(self) -> None:
        fail_if_disposition_is_upgraded(self.record)
        self.assertEqual(self.record["recorded_date"], "2026-10-30")
        self.assertEqual(self.record["provider_reply_date_utc"], "2026-10-29")
        self.assertEqual(self.record["provider_family"], "S&P Dow Jones Indices / S&P 500")
        scope = self.record["original_request_scope"]
        self.assertIn("S&P 500", scope["index_use"])
        self.assertIs(scope["commercial_internal_calculation_inquiry"], True)
        self.assertIs(scope["requested_no_fee_possibility"], True)
        self.assertEqual(set(scope["proposed_public_output"]), EXPECTED_PUBLIC_FIELDS)
        self.assertEqual(len(scope["proposed_public_output"]), 4)
        self.assertIn("component_z_scores", scope["proposed_excluded_public_fields"])
        self.assertIn("normalization_moments", scope["proposed_excluded_public_fields"])
        self.assertIs(
            self.record["provider_reply"]["separate_internal_vs_public_license_exemptions_expressly_resolved"],
            False,
        )

    def test_mutations_cannot_turn_paid_response_into_approval(self) -> None:
        for key in EXPECTED_GATES:
            with self.subTest(gate=key):
                altered = copy.deepcopy(self.record)
                altered["authorizations"][key] = True
                with self.assertRaisesRegex(ValueError, "cannot grant"):
                    fail_if_disposition_is_upgraded(altered)
        cases = [
            ("provider_reply", "written_no_fee_aggregate_permission_received", True),
            ("provider_reply", "paid_license_executed", True),
            ("provider_reply", "paid_license_required_for_described_request", False),
            ("provider_reply", "separate_internal_vs_public_license_exemptions_expressly_resolved", True),
            ("economics", "authorized_additional_market_data_license_budget_usd", 300),
            ("economics", "original_eight_driver_score_zero_budget_release_viable", True),
        ]
        for section, key, value in cases:
            with self.subTest(field=key):
                altered = copy.deepcopy(self.record)
                altered[section][key] = value
                with self.assertRaises(ValueError):
                    fail_if_disposition_is_upgraded(altered)

    def test_earlier_snapshots_remain_historical_not_current_licenses(self) -> None:
        old_queue = json.loads(OLDER_QUEUE.read_text(encoding="utf-8"))
        old_coverage = json.loads(OLDER_COVERAGE.read_text(encoding="utf-8"))
        self.assertEqual(old_queue["snapshot_date"], "2026-10-29")
        self.assertEqual(old_queue["state"], "RIGHTS_HOLD_RESEARCH_ONLY")
        self.assertIs(old_queue["contact_policy"]["no_new_paid_service"], True)
        old_sp = next(p for p in old_queue["providers"] if p["id"] == "sp_dji_sp500")
        self.assertEqual(old_sp["latest_contact"], "sales_referral_2026-10-28_no_license")
        self.assertEqual(old_sp["rights_state"], "pending")
        self.assertEqual(old_sp["grants"]["public_aggregate_distribution"], "unapproved")
        sp_coverage = next(p for p in old_coverage["providers"] if p["id"] == "sp_dji_sp500")
        self.assertEqual(sp_coverage["current_status"], "pending_written_permission")
        self.assertIs(sp_coverage["specific_signed_rights_disposition_received"], False)
        self.assertEqual(
            set(self.record["linked_prior_status_snapshots"]),
            {
                "governance/score-provider-rights-followup-queue-2026-10-29.json",
                "governance/score-rights-seven-provider-coverage-2026-10-29.json",
                "governance/score-v2-successor-rights-readiness-2026-10-29.json",
            },
        )

    def test_all_canonical_publication_rights_and_retention_gates_remain_closed(self) -> None:
        rights = json.loads(CURRENT_POLICY.read_text(encoding="utf-8"))
        review = json.loads(REVIEW_PACKET.read_text(encoding="utf-8"))
        self.assertEqual(rights["state"], "hold")
        self.assertIsNone(rights["decision_receipt"])
        self.assertIsNone(rights["approved_by"])
        self.assertEqual(review["decision_state"], "DRAFT_SYNTHETIC_ONLY_RIGHTS_HOLD")
        self.assertTrue(review["authorization_gates"])
        self.assertTrue(all(v is False for v in review["authorization_gates"].values()))
        self.assertTrue(all(q["state"] == "PENDING" and q["receipt"] is None
                            for q in review["open_decision_questions"]))

    def test_public_evidence_does_not_copy_mail_or_sensitive_correspondence(self) -> None:
        text = STATUS_FILE.read_text(encoding="utf-8")
        document = DOC.read_text(encoding="utf-8")
        self.assertNotIn("@", text)
        self.assertNotIn("mailto:", text)
        self.assertNotIn("mail.google.com", text)
        self.assertNotIn("Case Number:", text)
        self.assertNotIn("Phone:", text)
        self.assertNotIn("Bearer ", text)
        self.assertNotIn("https://mail.", document)
        self.assertIn("2026-10-30 provider-response addendum", document)
        self.assertIn("requires a **paid license**", document)
        self.assertIn("NOT cleared for a no-cost release", document)


if __name__ == "__main__":
    unittest.main()
