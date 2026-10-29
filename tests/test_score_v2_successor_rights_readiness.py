"""Issue #155 successor readiness: synthetic mutation tests, absolutely no provider access."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_score_v2_successor_rights_readiness import (
    ROOT, PACKET, GATE, QUEUE, PREVIOUS, INVENTORY, PHASE_A,
    FOUR_SOURCE, SCORE, PERMISSIONS, RELATIONSHIPS, INPUTS, validate,
)

FILES = [
    PACKET, GATE, QUEUE, PREVIOUS, INVENTORY, PHASE_A, FOUR_SOURCE,
    SCORE, Path("scripts/score_publication_rights_gate.py"),
]


class ScoreV2SuccessorDraftHoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="score-rights-successor-2099-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in FILES:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)

    def edit(self, path: Path, callback) -> None:
        f = self.root / path
        d = json.loads(f.read_text(encoding="utf-8"))
        callback(d)
        f.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")

    def denied(self, reason: str) -> None:
        with self.assertRaisesRegex(RuntimeError, reason):
            validate(self.root)

    def item(self, d: dict, id: str) -> dict:
        return next(x for x in d["relationships"] if x["id"] == id)

    def test_current_packet_passes_but_never_authorizes_release(self) -> None:
        report = validate(self.root)
        self.assertEqual(report["result"], "PASS_DRAFT_ONLY_HOLD")
        self.assertEqual(report["active_driver_count"], 8)
        self.assertEqual(report["rights_relationship_count"], 8)
        self.assertEqual(report["prior_queue_relationships"], 7)
        self.assertTrue(report["unresolved_BTC_source"])
        self.assertEqual(report["permission_checks_denied"], 128)
        self.assertEqual(report["publication_classes_pending"], 6)
        self.assertEqual(report["preservation_surfaces_pending"], 7)
        self.assertEqual(report["consumer_migrations_pending"], 7)
        self.assertEqual(report["external_release_authorizations"], 0)
        self.assertFalse(report["score_legacy_release_allowed"])
        self.assertFalse(report["real_provider_retention_allowed"])
        self.assertFalse(report["production_changed"])

    def test_frozen_source_not_imported(self) -> None:
        script = (ROOT / "scripts/validate_score_v2_successor_rights_readiness.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("ast.parse(", script)
        self.assertNotIn("import yfinance", script)
        self.assertNotIn("from usd_impact_score_v2 import", script)
        self.assertNotIn("requests.get(", script)
        self.assertNotIn("urllib.request", script)

    def test_btc_exact_origin_is_not_claimed(self) -> None:
        raw = json.loads((self.root / PACKET).read_text(encoding="utf-8"))
        row = self.item(raw, "btc_usd_historical_price_origin")
        self.assertFalse(row["owner_identity_proved_for_exact_historical_values"])
        self.assertEqual(row["role"], "unverified_data_origin")
        self.assertFalse(raw["btc_provenance_caveat"]["historical_OHLC_underlying_owner_identified"])
        self.assertTrue(
            raw["btc_provenance_caveat"][
                "free_or_paid_CMC_API_is_not_approval_for_yahoo_delivered_historical_OHLC"
            ]
        )

    def test_no_arbitrary_provider_permission_allowed(self) -> None:
        for ident in RELATIONSHIPS:
            with self.subTest(relationship=ident):
                obj = json.loads((self.root / PACKET).read_text(encoding="utf-8"))
                self.item(obj, ident)["rights"]["public_aggregate_distribution"] = True
                f = self.root / PACKET
                f.write_text(json.dumps(obj), encoding="utf-8")
                self.denied("source_field_rights_not_denied_")
                shutil.copyfile(ROOT / PACKET, f)

    def test_no_arbitrary_permission_dimension_allowed(self) -> None:
        self.edit(PACKET, lambda d: self.item(d, "cme_wti_gold")[
            "rights"].update(provider_content_retention=True))
        self.denied("source_field_rights_not_denied_cme_wti_gold")

    def test_missing_rights_dimension_is_a_failure(self) -> None:
        self.edit(PACKET, lambda d: self.item(d, "fred_dgs2_dgs10")[
            "rights"].pop("source_attribution_and_trademark"))
        self.denied("source_field_rights_not_denied_fred_dgs2_dgs10")

    def test_unapproved_extra_permission_dimension_is_a_failure(self) -> None:
        self.edit(PACKET, lambda d: d["permission_dimensions"].append("silent_exemption"))
        self.denied("successor_permissions_schema_incomplete")

    def test_missing_BTC_underlying_source_is_a_failure(self) -> None:
        self.edit(PACKET, lambda d: d["relationships"].__setitem__(
            slice(None), [x for x in d["relationships"]
                          if x["id"] != "btc_usd_historical_price_origin"]))
        self.denied("successor_eight_relationship_coverage_not_complete")

    def test_missing_existing_Yahoo_transport_is_a_failure(self) -> None:
        self.edit(PACKET, lambda d: d["relationships"].__setitem__(
            slice(None), [x for x in d["relationships"] if x["id"] != "yahoo_delivery"]))
        self.denied("successor_eight_relationship_coverage_not_complete")

    def test_duplicate_BTC_source_does_not_fill_missing_ICE(self) -> None:
        def tweak(d):
            d["relationships"][-1] = dict(d["relationships"][3])
        self.edit(PACKET, tweak)
        self.denied("successor_eight_relationship_coverage_not_complete")

    def test_BTC_must_reference_owner_and_delivery(self) -> None:
        def tweak(d):
            next(x for x in d["active_inputs"] if x["driver"] == "BTC")[
                "source_relationship_ids"] = ["yahoo_delivery"]
        self.edit(PACKET, tweak)
        self.denied("source_relationship_missing_BTC")

    def test_treasury_upstream_and_FRED_transport_both_recorded(self) -> None:
        def tweak(d):
            next(x for x in d["active_inputs"] if x["driver"] == "UST_2Y")[
                "source_relationship_ids"] = ["fred_dgs2_dgs10"]
        self.edit(PACKET, tweak)
        self.denied("source_relationship_missing_UST_2Y")

    def test_wrong_legacy_WTI_future_contract_cannot_be_substituted(self) -> None:
        def tweak(d):
            next(x for x in d["active_inputs"] if x["driver"] == "WTI")[
                "ticker"] = "EIA_WCESTUS1"
        self.edit(PACKET, tweak)
        self.denied("source_relationship_missing_WTI")

    def test_frozen_code_ticker_drift_is_a_failure(self) -> None:
        path = self.root / SCORE
        s = path.read_text(encoding="utf-8")
        before = '"BTC":     ("yahoo", "BTC-USD"),'
        self.assertIn(before, s)
        path.write_text(s.replace(before, '"BTC":     ("yahoo", "OTHER"),'),
                        encoding="utf-8")
        self.denied("active_eight_driver_source_or_weights_changed")

    def test_CMC_partnership_not_historical_OHLC_license(self) -> None:
        self.edit(PACKET, lambda d: d["btc_provenance_caveat"].update(
            historical_OHLC_underlying_owner_identified=True))
        self.denied("historical_BTC_price_owner_must_stay_unresolved")

    def test_CMC_commercial_API_not_permission_for_Yahoo_history(self) -> None:
        self.edit(PACKET, lambda d: d["btc_provenance_caveat"].update(
            free_or_paid_CMC_API_is_not_approval_for_yahoo_delivered_historical_OHLC=False))
        self.denied("historical_BTC_price_owner_must_stay_unresolved")

    def test_missing_primary_rights_reference_is_a_failure(self) -> None:
        self.edit(PACKET, lambda d: d["btc_provenance_caveat"][
            "public_evidence_links"].pop())
        self.denied("historical_BTC_price_owner_must_stay_unresolved")

    def test_cannot_fabricate_written_license(self) -> None:
        self.edit(PACKET, lambda d: self.item(d, "sp_dji_sp500").update(
            binding_executed_license_or_counsel_disposition_found=True))
        self.denied("provider_identity_or_rights_unverified_sp_dji_sp500")

    def test_FRED_conditional_does_not_approve_storage(self) -> None:
        self.edit(PACKET, lambda d: self.item(d, "fred_dgs2_dgs10")[
            "rights"].update(provider_content_retention=True))
        self.denied("source_field_rights_not_denied_fred_dgs2_dgs10")

    def test_source_queue_license_approval_cannot_be_inferred(self) -> None:
        self.edit(QUEUE, lambda d: d["providers"][0]["grants"].update(
            public_aggregate_distribution="approved"))
        self.denied("prior_provider_queue_contains_new_approval_")

    def test_old_v1_gate_cannot_be_flipped(self) -> None:
        self.edit(GATE, lambda d: d.update(state="allow"))
        self.denied("binding_score_publication_gate_not_hold")

    def test_future_v2_runtime_claim_must_not_be_set(self) -> None:
        self.edit(PACKET, lambda d: d.update(
            new_live_release_mechanism_enabled=True))
        self.denied("successor_is_not_inactive_draft")

    def test_release_receipt_cannot_be_fabricated(self) -> None:
        self.edit(PACKET, lambda d: d["decision"].update(
            owner_production_release_receipt="https://github.com/example"))
        self.denied("future_release_improperly_approved")

    def test_production_release_authorization_remains_false(self) -> None:
        self.edit(PACKET, lambda d: d["authorizations"].update(
            production_or_publication_activation=True))
        self.denied("successor_packet_contains_unauthorized_actions")

    def test_no_provider_new_contact_without_owner(self) -> None:
        self.edit(PACKET, lambda d: d["authorizations"].update(
            new_provider_outreach=True))
        self.denied("successor_packet_contains_unauthorized_actions")

    def test_missing_action_field_does_not_default_to_approval(self) -> None:
        self.edit(PACKET, lambda d: d["authorizations"].pop(
            "live_or_historical_real_data_fetch"))
        self.denied("successor_packet_contains_unauthorized_actions")

    def test_new_action_field_not_permitted(self) -> None:
        self.edit(PACKET, lambda d: d["authorizations"].update(
            unreviewed_provider_data_access=False))
        self.denied("successor_packet_contains_unauthorized_actions")

    def test_historical_Git_cleanup_is_not_approved(self) -> None:
        self.edit(PACKET, lambda d: d["historical_snapshot"].update(
            deletion_or_history_rewrite_authorized=True))
        self.denied("legacy_artifact_footprint_or_history_purge_authorized")

    def test_historical_CDN_rollback_unreviewed(self) -> None:
        self.edit(PACKET, lambda d: d["historical_snapshot"][
            "preservation_surfaces"][4].update(remediation_authorized=True))
        self.denied("historic_preservation_not_approved_")

    def test_class_C_public_rights_unreviewed(self) -> None:
        self.edit(PACKET, lambda d: d["publication_classes"][2].update(
            rights_decision="approved"))
        self.denied("public_artifact_class_approval_not_proven_C")

    def test_class_F_historical_treatment_unreviewed(self) -> None:
        self.edit(PACKET, lambda d: d["publication_classes"][-1].update(
            historical_archive_treatment="approved"))
        self.denied("public_artifact_class_approval_not_proven_F")

    def test_research_consumer_not_migrated(self) -> None:
        self.edit(PACKET, lambda d: d["consumer_migration"][3].update(
            cutover_authorized=True))
        self.denied("consumer_migration_not_approved_")

    def test_S_and_P_meeting_not_equivalent_to_license(self) -> None:
        self.edit(PACKET, lambda d: d["S_and_P_vendor_followup"].update(
            commercial_or_derived_publication_license_granted=True))
        self.denied("provider_meeting_not_a_rights_license")

    def test_S_and_P_reply_cannot_be_falsely_sent(self) -> None:
        self.edit(PACKET, lambda d: d["S_and_P_vendor_followup"].update(
            outbound_reply_sent_by_this_work=True))
        self.denied("provider_meeting_not_a_rights_license")

    def test_zero_license_study_does_not_authorize_original_score(self) -> None:
        self.edit(PACKET, lambda d: d["related_research"].update(
            like_for_like_eight_source_zero_cost_parity_cleared=True))
        self.denied("separate_four_source_study_was_promoted_into_legacy_score")

    def test_cannot_infer_from_study_citation_reference(self) -> None:
        self.edit(PACKET, lambda d: d["related_research"].update(
            automated_source_substitution_approved=True))
        self.denied("separate_four_source_study_was_promoted_into_legacy_score")

    def test_external_counsel_release_gate_unapproved(self) -> None:
        self.edit(PACKET, lambda d: d["external_authority_gates"].update(
            complete_source_and_transport_authorities=True))
        self.denied("external_rights_or_production_gates_not_all_denied")

    def test_unreviewed_public_schema_is_not_release_approved(self) -> None:
        self.edit(PACKET, lambda d: d["decision"].update(
            approved_public_schema="aggregate-prototype"))
        self.denied("future_release_improperly_approved")


if __name__ == "__main__":
    unittest.main()
