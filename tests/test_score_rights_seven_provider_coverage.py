"""Issue #155 — provider rights coverage and HOLD checks, local files only.

Copies review/governance JSON into a disposable temp folder and mutates
invented decision states. No licensed data, Gmail, BLS, Yahoo, Supabase,
Cloudflare or other remote requests are performed.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_score_rights_seven_provider_coverage import (
    ROOT, COVERAGE, QUEUE, LEGACY, GATE, SURFACE, PRIVATE, INVENTORY, PHASE_A,
    EXPECTED, RIGHTS_FIELDS, validate,
)

FILES = [COVERAGE, QUEUE, LEGACY, GATE, SURFACE, PRIVATE, INVENTORY, PHASE_A]


class SevenSourceCoverageHoldTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="score-rights-coverage-synthetic-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for relative in FILES:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def edit(self, relative, update):
        p = self.root / relative
        j = json.loads(p.read_text(encoding="utf-8"))
        update(j)
        p.write_text(json.dumps(j, indent=2) + "\n", encoding="utf-8")

    def refused(self, reason):
        with self.assertRaisesRegex(RuntimeError, reason):
            validate(self.root)

    def test_current_seven_relationship_review_passes_but_not_rights(self):
        result = validate(self.root)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["registered_relationships"], 7)
        self.assertEqual(result["legacy_template_rows"], 5)
        self.assertEqual(result["legacy_missing"], ["ice_usdx", "treasury_h15_direct"])
        self.assertFalse(result["written_provider_dispositions_complete"])
        self.assertEqual(result["rights_gate"], "hold")
        self.assertEqual(result["public_field_classes_pending"], 6)
        self.assertEqual(result["historical_classC_path_inventory"], 54)
        for key in ("public_aggregate_approved", "real_provider_retention_approved",
                    "provider_outreach_performed", "Production_changed",
                    "zero_license_equivalent_ready"):
            self.assertIs(result[key], False)

    def test_seven_provider_roles_exactly_match_queue(self):
        c = json.loads((self.root / COVERAGE).read_text(encoding="utf-8"))
        p = {z["id"]: z for z in c["providers"]}
        self.assertEqual(set(p), set(EXPECTED))
        self.assertFalse(p["ice_usdx"]["present_in_legacy_five_provider_receipt"])
        self.assertFalse(p["treasury_h15_direct"]["present_in_legacy_five_provider_receipt"])
        self.assertEqual(set(p["fred_dgs2_dgs10"]["fields"]), RIGHTS_FIELDS)
        self.assertEqual(
            p["fred_dgs2_dgs10"]["current_status"],
            "conditional_transient_processing_only_not_a_general_release",
        )

    def test_legacy_receipt_persistently_five_and_unapproved(self):
        old = json.loads((self.root / LEGACY).read_text(encoding="utf-8"))
        self.assertEqual(len(old["provider_dispositions"]), 5)
        self.assertTrue(all(x["status"] == "pending" for x in old["provider_dispositions"]))
        self.assertEqual(old["decision_status"], "hold")
        self.assertIsNone(old["approved_public_schema"])

    def test_missing_ICE_relationship_is_a_hard_failure(self):
        self.edit(COVERAGE, lambda d: d["providers"].__setitem__(
            slice(None), [p for p in d["providers"] if p["id"] != "ice_usdx"]))
        self.refused("seven_provider_coverage_incomplete")

    def test_missing_direct_treasury_relation_is_a_hard_failure(self):
        self.edit(COVERAGE, lambda d: d["providers"].__setitem__(
            slice(None), [p for p in d["providers"] if p["id"] != "treasury_h15_direct"]))
        self.refused("seven_provider_coverage_incomplete")

    def test_duplicate_provider_is_a_hard_failure(self):
        def mutate(d):
            d["providers"][6] = dict(d["providers"][5])
        self.edit(COVERAGE, mutate)
        self.refused("seven_provider_coverage_incomplete")

    def test_wrong_ICE_role_is_a_hard_failure(self):
        def mutate(d):
            next(x for x in d["providers"] if x["id"] == "ice_usdx")["relationship"] = "free"
        self.edit(COVERAGE, mutate)
        self.refused("missing_or_claimed_provider_permission_ice_usdx")

    def test_wrong_FRED_transient_scope_is_a_hard_failure(self):
        def mutate(d):
            next(x for x in d["providers"] if x["id"] == "fred_dgs2_dgs10")["current_status"] = "fully_licensed"
        self.edit(COVERAGE, mutate)
        self.refused("provider_status_wrong_fred_dgs2_dgs10")

    def test_fred_conditional_does_not_approve_aggregate_history(self):
        def mutate(d):
            next(x for x in d["providers"] if x["id"] == "fred_dgs2_dgs10")[
                "fields"]["public_aggregate_distribution"] = "approved"
        self.edit(COVERAGE, mutate)
        self.refused("field_rights_not_unapproved_fred_dgs2_dgs10")

    def test_provider_evidence_cannot_be_fabricated(self):
        def mutate(d):
            next(x for x in d["providers"] if x["id"] == "sp_dji_sp500")[
                "specific_signed_rights_disposition_received"] = True
        self.edit(COVERAGE, mutate)
        self.refused("missing_or_claimed_provider_permission_sp_dji_sp500")

    def test_legacy_template_cannot_silently_approve_five_only(self):
        self.edit(LEGACY, lambda d: d.update(decision_status="approved_aggregate_only"))
        self.refused("legacy_five_provider_gap_not_preserved")

    def test_legacy_template_cannot_expand_without_new_review(self):
        self.edit(LEGACY, lambda d: d["provider_dispositions"].append({
            "provider_family": "ICE", "scope": "USDX", "status": "approved", "reference": None,
        }))
        self.refused("legacy_five_provider_gap_not_preserved")

    def test_legacy_gap_cannot_be_marked_complete(self):
        self.edit(COVERAGE, lambda d: d["legacy_receipt"].update(coverage_complete=True))
        self.refused("legacy_five_provider_gap_not_preserved")

    def test_legacy_gap_missing_provider_list_is_immutable(self):
        self.edit(COVERAGE, lambda d: d["legacy_receipt"].update(
            missing_decision_relationships=[]))
        self.refused("legacy_five_provider_gap_not_preserved")

    def test_provider_queue_must_keep_seven(self):
        self.edit(QUEUE, lambda d: d["providers"].pop())
        self.refused("source_queue_must_cover_seven_relationships")

    def test_provider_queue_retention_not_granted(self):
        self.edit(QUEUE, lambda d: d["providers"][0]["grants"].update(retention="approved"))
        self.refused("provider_queue_contains_unreviewed_grant")

    def test_rhs_gate_cannot_be_allowed(self):
        self.edit(GATE, lambda d: d.update(state="allow"))
        self.refused("binding_publication_rights_gate_not_hold")

    def test_rights_decision_comment_does_not_become_receipt(self):
        self.edit(GATE, lambda d: d.update(decision_receipt="https://github.com/placeholder"))
        self.refused("binding_publication_rights_gate_not_hold")

    def test_real_provider_evidence_not_authorized(self):
        self.edit(PRIVATE, lambda d: d.update(real_provider_evidence_authorized=True))
        self.refused("private_provider_data_or_public_replacement_approved")

    def test_private_public_replacement_not_authorized(self):
        self.edit(PRIVATE, lambda d: d.update(public_replacement_authorized=True))
        self.refused("private_provider_data_or_public_replacement_approved")

    def test_six_public_classes_not_silently_cleared(self):
        self.edit(COVERAGE, lambda d: d["public_surface"]["class_status"].update(C="approved"))
        self.refused("public_classes_and_archive_treatment_not_pending")

    def test_candidate_aggregate_schema_not_approved_by_transformer(self):
        self.edit(COVERAGE, lambda d: d["public_surface"].update(
            public_aggregate_schema_approved=True))
        self.refused("public_classes_and_archive_treatment_not_pending")

    def test_historical_archive_cannot_be_purged_by_rights_register(self):
        self.edit(COVERAGE, lambda d: d["public_surface"].update(
            historical_git_pages_cdn_and_external_copies_disposition_approved=True))
        self.refused("public_classes_and_archive_treatment_not_pending")

    def test_archived_metadata_count_cannot_be_mislabeled_as_zero(self):
        self.edit(COVERAGE, lambda d: d["public_surface"].update(
            historical_metadata_inventory_classC_files=0))
        self.refused("historical_metadata_preservation_not_approved")

    def test_phaseA_research_not_like_for_like_license(self):
        self.edit(PHASE_A, lambda d: d["decision"].update(
            identified_complete_eight_driver_license_safe_pipeline=True))
        self.refused("zero_paid_license_research_promoted_to_live")

    def test_outreach_is_not_authorized(self):
        self.edit(COVERAGE, lambda d: d["authorizations"].update(provider_mail_outreach=True))
        self.refused("rights_authorization_or_field_set_changed")

    def test_provider_contact_not_falsely_said_sent(self):
        self.edit(COVERAGE, lambda d: d["communications"].update(
            outreach_email_sent_by_this_work=True))
        self.refused("provider_outreach_or_rights_claim_unauthorized")

    def test_provider_purchase_not_authorized(self):
        self.edit(COVERAGE, lambda d: d["authorizations"].update(
            paid_license_purchase=True))
        self.refused("rights_authorization_or_field_set_changed")

    def test_public_score_publication_not_authorized(self):
        self.edit(COVERAGE, lambda d: d["authorizations"].update(
            source_derived_aggregate_publication=True))
        self.refused("rights_authorization_or_field_set_changed")

    def test_production_not_authorized(self):
        self.edit(COVERAGE, lambda d: d["authorizations"].update(
            production_deployment=True))
        self.refused("rights_authorization_or_field_set_changed")

    def test_permission_field_cannot_be_dropped(self):
        self.edit(COVERAGE, lambda d: d["authorizations"].pop("production_deployment"))
        self.refused("rights_authorization_or_field_set_changed")

    def test_rights_dimensions_cannot_omit_historical_archive(self):
        self.edit(COVERAGE, lambda d: d["field_rights_dimensions"].remove(
            "historical_archive_treatment"))
        self.refused("field_rights_dimensions_incomplete")

    def test_no_public_decision_authority_can_be_invented(self):
        self.edit(COVERAGE, lambda d: d["release_readiness"].update(
            seven_provider_written_decisions_completed=True))
        self.refused("release_readiness_incorrectly_claimed")


if __name__ == "__main__":
    unittest.main()
