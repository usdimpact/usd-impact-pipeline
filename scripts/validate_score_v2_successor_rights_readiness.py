#!/usr/bin/env python3
"""Verify the Issue #155 successor rights decision packet remains non-activatable.

This is an OFFLINE readiness/coverage validator, deliberately NOT a release
authorizer. Only repository source code AST and governance JSON are read; no
market observations, public Score bodies, provider calls, private storage,
provider email content, credentials, or network access is used.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKET = Path("governance/score-v2-successor-rights-readiness-2026-10-29.json")
GATE = Path("governance/score-publication-rights-gate.json")
QUEUE = Path("governance/score-provider-rights-followup-queue-2026-10-29.json")
PREVIOUS = Path("governance/score-rights-seven-provider-coverage-2026-10-29.json")
INVENTORY = Path("governance/score-current-tree-exposure-inventory-2026-10-29.json")
PHASE_A = Path("governance/score-zero-license-phase-a-feasibility-2026-10-29.json")
FOUR_SOURCE = Path("governance/score-four-source-exact-series-rights-matrix-2026-10-29.json")
SCORE = Path("usd_impact_score_v2.py")
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/155"

INPUTS = {
    "DXY": ("yahoo", "DX-Y.NYB", ("yahoo_delivery", "ice_usdx"), +0.125),
    "WTI": ("yahoo", "CL=F", ("yahoo_delivery", "cme_wti_gold"), -0.125),
    "SPX": ("yahoo", "^GSPC", ("yahoo_delivery", "sp_dji_sp500"), -0.125),
    "VIX": ("yahoo", "^VIX", ("yahoo_delivery", "cboe_vix"), +0.125),
    "BTC": ("yahoo", "BTC-USD", ("yahoo_delivery", "btc_usd_historical_price_origin"), -0.125),
    "GOLD": ("yahoo", "GC=F", ("yahoo_delivery", "cme_wti_gold"), -0.125),
    "UST_2Y": ("fred", "DGS2", ("fred_dgs2_dgs10", "treasury_h15_direct"), +0.125),
    "UST_10Y": ("fred", "DGS10", ("fred_dgs2_dgs10", "treasury_h15_direct"), +0.125),
}

KNOWN_QUEUE_IDS = {
    "fred_dgs2_dgs10", "yahoo_delivery", "sp_dji_sp500",
    "cboe_vix", "cme_wti_gold", "ice_usdx", "treasury_h15_direct",
}
RELATIONSHIPS = {
    "fred_dgs2_dgs10": ("FRED DGS2/DGS10 delivery", "published_series_transport"),
    "yahoo_delivery": ("Yahoo Finance/yfinance historical delivery", "delivery_transport"),
    "sp_dji_sp500": ("S&P Dow Jones Indices S&P 500", "index_owner"),
    "cboe_vix": ("Cboe VIX", "index_owner"),
    "cme_wti_gold": ("CME WTI and gold futures", "futures_owner"),
    "ice_usdx": ("ICE USDX", "index_owner"),
    "treasury_h15_direct": (
        "U.S. Treasury/Board H.15 yield-source lineage",
        "underlying_source_and_republisher",
    ),
    "btc_usd_historical_price_origin": (
        "Yahoo BTC-USD historical OHLC underlying source", "unverified_data_origin",
    ),
}
PERMISSIONS = {
    "commercial_internal_ingestion", "commercial_non_display_transformation",
    "transient_processing", "provider_content_retention", "observations_archival",
    "logs_and_cache_retention", "backup_and_disaster_recovery_retention",
    "revision_vintage_receipt_retention", "public_aggregate_distribution",
    "public_component_distribution", "public_history_distribution",
    "ai_ml_processing", "downstream_redistribution", "live_source_retrieval",
    "source_attribution_and_trademark", "automated_delivery",
}
ARCHIVAL_SURFACES = {
    "current_public_git_tree", "historical_git_commits_and_clones",
    "cloudflare_pages_production_deployments",
    "cloudflare_pages_preview_deployments",
    "cloudflare_cdn_and_edge_caches",
    "github_actions_logs_artifacts_and_caches",
    "off_platform_backups_and_external_copies",
}
CONSUMERS = {
    "weekly_score_generation", "score_v2_predictive_ingestion",
    "score_v3_shadow_ingestion", "research_validation_and_vintage",
    "independent_reproduction_and_attestation",
    "website_methodology_public_links", "member_dashboard_and_archive_routes",
}
EXTERNAL_GATES = {
    "complete_source_and_transport_authorities",
    "rights_for_aggregate_publication",
    "rights_for_components_and_research_publication",
    "rights_for_commercial_internal_use",
    "rights_for_retention_or_required_disposal",
    "lawful_historical_archive_disposition",
    "approved_public_artifact_schema",
    "approved_private_real_evidence_boundary",
    "research_and_site_consumer_migration",
    "verified_nonproduction_preview",
    "exact_head_release_ci",
    "separate_owner_production_receipt",
}
AUTHORIZATIONS = {
    "provider_get_or_head", "new_provider_outreach",
    "new_licenses_or_purchases", "live_or_historical_real_data_fetch",
    "commercial_public_derived_release", "public_component_or_history_release",
    "source_formula_or_weight_change", "site_member_or_research_consumer_change",
    "real_provider_evidence_storage", "historical_archive_rewrite_or_purge",
    "cloudflare_pages_or_cdn_change", "production_or_publication_activation",
    "legacy_v1_policy_change",
}
PRIMARY_LINKS = {
    "https://coinmarketcap.com/academy/article/how-yahoo-finance-powers-its-crypto-data-with-coinmarketcap-api",
    "https://help.yahoo.com/kb/SLN2310.html",
    "https://coinmarketcap.com/terms/",
    "https://coinmarketcap.com/api/pricing/",
    "https://pro.coinmarketcap.com/user-agreement-commercial/",
}


def require(ok: bool, message: str) -> None:
    if ok is not True:
        raise RuntimeError(message)


def load(root: Path, path: Path) -> dict[str, Any]:
    value = json.loads((root / path).read_text(encoding="utf-8"))
    require(isinstance(value, dict), "document_not_object_" + path.name)
    return value


def literal(root: Path, variable: str) -> Any:
    # Parse frozen source constants, NEVER import its provider-fetching module.
    module = ast.parse((root / SCORE).read_text(encoding="utf-8"))
    found = [
        node.value for node in module.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
        and target.id == variable
    ]
    require(len(found) == 1, "source_constant_not_unique_" + variable)
    return ast.literal_eval(found[0])


def assert_false_mapping(mapping: Any, names: set[str], reason: str) -> None:
    require(isinstance(mapping, dict) and set(mapping) == names
            and all(mapping[key] is False for key in names), reason)


def assert_named_rows(rows: Any, names: set[str], key: str, reason: str) -> dict[str, Any]:
    require(isinstance(rows, list) and len(rows) == len(names)
            and all(isinstance(x, dict) for x in rows)
            and {x.get(key) for x in rows} == names, reason)
    return {x[key]: x for x in rows}


def validate(root: Path | None = None) -> dict[str, Any]:
    root = (root or ROOT).resolve()
    packet = load(root, PACKET)
    gate = load(root, GATE)
    queue = load(root, QUEUE)
    previous = load(root, PREVIOUS)
    inventory = load(root, INVENTORY)
    phase_a = load(root, PHASE_A)
    four = load(root, FOUR_SOURCE)

    require(packet.get("schema_version") == "score-v2-rights-successor-readiness-draft-v0"
            and packet.get("recorded_date") == "2026-10-29"
            and packet.get("state") == "DRAFT_ONLY_HOLD_NO_RUNTIME"
            and packet.get("controlling_issue") == ISSUE
            and packet.get("active_policy_path") == str(GATE)
            and packet.get("active_policy_expected_state") == "hold"
            and packet.get("active_legacy_v1_policy_version") == 1
            and packet.get("future_positive_release_contract_exists") is False
            and packet.get("new_live_release_mechanism_enabled") is False,
            "successor_is_not_inactive_draft")

    require(gate.get("version") == 1 and gate.get("state") == "hold"
            and gate.get("decision_receipt") is None
            and gate.get("approved_by") is None,
            "binding_score_publication_gate_not_hold")
    gate_source = (root / "scripts/score_publication_rights_gate.py").read_text(
        encoding="utf-8"
    )
    require("v1-allow-not-an-authorized-rights-release-contract" in gate_source,
            "legacy_v1_interlock_missing")

    original = literal(root, "TICKERS")
    weights = literal(root, "WEIGHTS")
    require(set(original) == set(INPUTS) == set(weights)
            and all(original[k] == (INPUTS[k][0], INPUTS[k][1])
                    and weights[k] == INPUTS[k][3] for k in INPUTS),
            "active_eight_driver_source_or_weights_changed")
    rows = assert_named_rows(
        packet.get("active_inputs"), set(INPUTS), "driver",
        "active_source_coverage_missing_or_duplicate",
    )
    require(packet.get("input_count") == 8
            and packet.get("frozen_model_source_path") == str(SCORE),
            "score_source_contract_not_frozen")
    for driver, (transport, ticker, ids, _) in INPUTS.items():
        item = rows[driver]
        require(item.get("transport") == transport
                and item.get("ticker") == ticker
                and item.get("source_relationship_ids") == list(ids)
                and item.get("original_model_preserved") is True
                and item.get("live_source_change_authorized") is False,
                "source_relationship_missing_" + driver)

    qrows = assert_named_rows(
        queue.get("providers"), KNOWN_QUEUE_IDS, "id",
        "existing_seven_source_queue_drifted",
    )
    require(queue.get("state") == "RIGHTS_HOLD_RESEARCH_ONLY"
            and queue.get("contact_policy", {}).get("no_automatic_sending") is True
            and queue.get("contact_policy", {}).get("no_duplicate_outreach") is True,
            "provider_queue_authorization_drift")
    require(previous.get("state") == "DESIGN_ONLY_COVERAGE_GAP_HOLD"
            and previous.get("provider_count") == 7
            and {x["id"] for x in previous.get("providers", [])} == KNOWN_QUEUE_IDS,
            "historical_seven_provider_packet_drift")

    providers = assert_named_rows(
        packet.get("relationships"), set(RELATIONSHIPS), "id",
        "successor_eight_relationship_coverage_not_complete",
    )
    require(packet.get("relationship_count") == 8
            and set(packet.get("permission_dimensions", [])) == PERMISSIONS
            and len(packet.get("permission_dimensions", [])) == len(PERMISSIONS),
            "successor_permissions_schema_incomplete")
    for ident, (label, role) in RELATIONSHIPS.items():
        item = providers[ident]
        expected_status = (
            "limited_public_domain_tagged_transient_conditional_not_release"
            if ident == "fred_dgs2_dgs10" else "unresolved"
        )
        require(item.get("display_label") == label
                and item.get("role") == role
                and item.get("matched_to_earlier_seven_queue") is (ident in KNOWN_QUEUE_IDS)
                and item.get("owner_identity_proved_for_exact_historical_values") is False
                and item.get("binding_executed_license_or_counsel_disposition_found") is False
                and item.get("effective_written_rights_reference") is None
                and item.get("status") == expected_status,
                "provider_identity_or_rights_unverified_" + ident)
        assert_false_mapping(item.get("rights"), PERMISSIONS,
                             "source_field_rights_not_denied_" + ident)
        if ident in qrows:
            grants = qrows[ident].get("grants", {})
            require(all(grants.get(p) == "unapproved" for p in (
                "retention", "public_aggregate_distribution",
                "public_component_distribution",
            )), "prior_provider_queue_contains_new_approval_" + ident)

    btc = packet.get("btc_provenance_caveat", {})
    require(btc.get("driver") == "BTC" and btc.get("ticker") == "BTC-USD"
            and btc.get("relationship_id") == "btc_usd_historical_price_origin"
            and btc.get("historical_OHLC_underlying_owner_identified") is False
            and btc.get("exact_historical_close_calculation_and_data_lineage_verified") is False
            and btc.get("coinmarketcap_yahoo_partnership_official_public_evidence") is True
            and btc.get("partnership_is_not_legacy_OHLC_ownership_or_usd_impact_license") is True
            and btc.get("free_or_paid_CMC_API_is_not_approval_for_yahoo_delivered_historical_OHLC") is True
            and btc.get("rights_decision_pending") is True
            and set(btc.get("public_evidence_links", [])) == PRIMARY_LINKS
            and len(btc.get("public_evidence_links", [])) == len(PRIMARY_LINKS),
            "historical_BTC_price_owner_must_stay_unresolved")

    classes = assert_named_rows(
        packet.get("publication_classes"), set("ABCDEF"), "id",
        "public_artifact_classes_missing",
    )
    for k, v in classes.items():
        require(v.get("rights_decision") == "pending"
                and v.get("historical_archive_treatment") == "pending"
                and v.get("aggregate_safe_transform_not_legal_clearance") is True,
                "public_artifact_class_approval_not_proven_" + k)

    history = packet.get("historical_snapshot", {})
    require(history.get("source") == str(INVENTORY)
            and history.get("current_tree_class_C_file_count") ==
            inventory.get("current_tree_total_class_c_files") == 54
            and history.get("dated_archive_directory_count") ==
            inventory.get("dated_archive", {}).get("directory_count") == 27
            and history.get("deletion_or_history_rewrite_authorized") is False
            and history.get("real_provider_copy_to_private_storage_authorized") is False
            and inventory.get("authorization", {}).get("production_release") is False,
            "legacy_artifact_footprint_or_history_purge_authorized")
    for k, v in assert_named_rows(history.get("preservation_surfaces"),
                                  ARCHIVAL_SURFACES, "id", "preservation_surface_missing").items():
        require(v.get("rights_review_complete") is False
                and v.get("disposition") == "not_approved"
                and v.get("remediation_authorized") is False,
                "historic_preservation_not_approved_" + k)

    for k, v in assert_named_rows(packet.get("consumer_migration"), CONSUMERS,
                                  "id", "research_or_member_consumer_missing").items():
        require(v.get("compatibility_approved") is False
                and v.get("cutover_authorized") is False,
                "consumer_migration_not_approved_" + k)

    followup = packet.get("S_and_P_vendor_followup", {})
    require(followup.get("existing_case_status") ==
            "provider_offered_week_of_2026_11_02_discussion"
            and followup.get("commercial_or_derived_publication_license_granted") is False
            and followup.get("user_availability_confirmed") is False
            and followup.get("outbound_reply_sent_by_this_work") is False
            and followup.get("meeting_invitation_or_booking_created") is False
            and followup.get("no_duplicate_case") is True
            and followup.get("personal_correspondence_or_contact_details_included") is False,
            "provider_meeting_not_a_rights_license")

    research = packet.get("related_research", {})
    require(research.get("phase_A") == str(PHASE_A)
            and research.get("four_source_study") == str(FOUR_SOURCE)
            and research.get("like_for_like_eight_source_zero_cost_parity_cleared") is False
            and research.get("four_source_study_is_distinct_model_only") is True
            and research.get("automated_source_substitution_approved") is False
            and research.get("current_617_week_history_may_be_spliced") is False
            and phase_a.get("state") == "RESEARCH_ONLY_HOLD"
            and phase_a.get("decision", {}).get(
                "identified_complete_eight_driver_license_safe_pipeline") is False
            and four.get("product_boundary", {}).get(
                "legacy_eight_driver_score", {}).get("changes_authorized") is False,
            "separate_four_source_study_was_promoted_into_legacy_score")

    assert_false_mapping(packet.get("external_authority_gates"), EXTERNAL_GATES,
                         "external_rights_or_production_gates_not_all_denied")
    assert_false_mapping(packet.get("authorizations"), AUTHORIZATIONS,
                         "successor_packet_contains_unauthorized_actions")
    decision = packet.get("decision", {})
    require(decision.get("status") == "HOLD_NO_RELEASE"
            and decision.get("authority") is None
            and decision.get("decision_at") is None
            and decision.get("counsel_or_provider_rights_receipt") is None
            and decision.get("owner_production_release_receipt") is None
            and decision.get("approved_public_schema") is None
            and decision.get("approved_historical_treatment") is None
            and decision.get("proposed_future_policy_protocol") ==
            "separate_explicitly_reviewed_v2_contract_not_implemented_here",
            "future_release_improperly_approved")

    return {
        "result": "PASS_DRAFT_ONLY_HOLD",
        "active_driver_count": 8,
        "rights_relationship_count": len(providers),
        "prior_queue_relationships": len(qrows),
        "unresolved_BTC_source": True,
        "permission_checks_denied": len(providers) * len(PERMISSIONS),
        "publication_classes_pending": len(classes),
        "preservation_surfaces_pending": len(ARCHIVAL_SURFACES),
        "consumer_migrations_pending": len(CONSUMERS),
        "external_release_authorizations": 0,
        "score_legacy_release_allowed": False,
        "real_provider_retention_allowed": False,
        "production_changed": False,
    }


def main() -> int:
    print(json.dumps(validate(), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
