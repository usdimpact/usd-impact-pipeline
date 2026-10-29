#!/usr/bin/env python3
"""Issue #155: reconcile source transport and owner coverage, no live access.

Static review only. Reads committed governance JSON and the legacy rights
decision template, never provider observations, public Score data, email,
credentials, private storage or network endpoints. FAIL CLOSED when coverage or
existing independent publication HOLD is weakened.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = Path("governance/score-rights-seven-provider-coverage-2026-10-29.json")
QUEUE = Path("governance/score-provider-rights-followup-queue-2026-10-29.json")
LEGACY = Path("governance/score-rights-decision-receipt.template.json")
GATE = Path("governance/score-publication-rights-gate.json")
SURFACE = Path("governance/score-public-rights-surface.json")
PRIVATE = Path("governance/score-private-research-migration-contract.json")
INVENTORY = Path("governance/score-current-tree-exposure-inventory-2026-10-29.json")
PHASE_A = Path("governance/score-zero-license-phase-a-feasibility-2026-10-29.json")
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/155"
LEGACY_SHA = "833e8e3498188286c9eb5954d2f9280e53d3ee83"

EXPECTED = {
    "fred_dgs2_dgs10": ("FRED / government-series delivery", "federal_data_transport", True),
    "yahoo_delivery": ("Yahoo Finance / yfinance delivery path", "commercial_transport", True),
    "sp_dji_sp500": ("S&P Dow Jones Indices / S&P 500", "index_owner", True),
    "cboe_vix": ("Cboe Global Indices / VIX", "index_owner", True),
    "cme_wti_gold": ("CME Group / WTI and Gold futures", "market_data_owner", True),
    "ice_usdx": ("ICE U.S. Dollar Index / DXY", "index_owner", False),
    "treasury_h15_direct": ("U.S. Treasury / Federal Reserve H.15 direct published outputs",
                            "direct_source_and_republisher", False),
}
LEGACY_FAMILIES = {
    "Yahoo Finance / yfinance delivery path", "S&P Dow Jones Indices",
    "Cboe Global Indices", "CME Group", "FRED",
}
RIGHTS_FIELDS = {
    "commercial_internal_retrieval", "transient_computation",
    "private_evidence_retention", "public_aggregate_distribution",
    "public_component_distribution", "historical_archive_treatment",
    "source_naming_attribution", "automated_access_and_delivery",
}
CLASSES = set("ABCDEF")
EXPECTED_PERMISSIONS = {
    "live_source_GET_or_HEAD", "source_switch", "provider_mail_outreach",
    "paid_license_purchase", "real_provider_evidence_retention",
    "source_derived_aggregate_publication", "component_derived_publication",
    "public_aggregate_schema_activation", "public_archive_delete_or_rewrite",
    "Git_history_rewrite", "CDN_or_Pages_purge",
    "member_page_or_website_change", "public_artifact_replacement",
    "research_ledger_mutation", "production_deployment",
    "rights_gate_state_change",
}


def require(test: bool, reason: str) -> None:
    if test is not True:
        raise RuntimeError(reason)


def load(root: Path, relative: Path) -> dict[str, Any]:
    obj = json.loads((root / relative).read_text(encoding="utf-8"))
    require(isinstance(obj, dict), "rights_document_not_a_json_object")
    return obj


def git_blob_sha(content: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\x00" + content
    ).hexdigest()


def validate(root: Path | None = None) -> dict[str, Any]:
    root = (root or ROOT).resolve()
    coverage = load(root, COVERAGE)
    queue = load(root, QUEUE)
    template = load(root, LEGACY)
    gate = load(root, GATE)
    surface = load(root, SURFACE)
    private = load(root, PRIVATE)
    inventory = load(root, INVENTORY)
    phase_a = load(root, PHASE_A)

    require(coverage.get("schema_version") == "score-seven-provider-coverage-v1"
            and coverage.get("date_recorded") == "2026-10-29"
            and coverage.get("state") == "DESIGN_ONLY_COVERAGE_GAP_HOLD"
            and coverage.get("controlling_issue") == ISSUE
            and coverage.get("result") == "INCOMPLETE_RIGHTS_DISPOSITIONS_HOLD",
            "coverage_status_not_hold")

    legacy = coverage.get("legacy_receipt", {})
    require(legacy.get("path") == str(LEGACY)
            and legacy.get("frozen_git_blob_sha") == LEGACY_SHA
            and git_blob_sha((root / LEGACY).read_bytes()) == LEGACY_SHA
            and legacy.get("historical_state") == "hold"
            and legacy.get("historical_provider_rows") == 5
            and legacy.get("coverage_complete") is False
            and legacy.get("missing_decision_relationships") ==
            ["ice_usdx", "treasury_h15_direct"]
            and legacy.get("do_not_silently_promote_to_approval") is True
            and legacy.get("historical_template_must_not_be_overwritten") is True,
            "legacy_five_provider_gap_not_preserved")
    require(template.get("decision_status") == "hold"
            and template.get("approved_public_schema") is None
            and template.get("decision_authority") is None
            and template.get("production_authorized") is False
            and template.get("decided_at_utc") is None,
            "legacy_template_wrongly_approved")
    legacy_entries = template.get("provider_dispositions", [])
    require(isinstance(legacy_entries, list)
            and len(legacy_entries) == 5
            and {p.get("provider_family") for p in legacy_entries} == LEGACY_FAMILIES
            and all(p.get("status") == "pending" and p.get("reference") is None
                    for p in legacy_entries),
            "legacy_receipt_not_five_pending_rows")

    require(queue.get("state") == "RIGHTS_HOLD_RESEARCH_ONLY"
            and queue.get("snapshot_date") == "2026-10-29"
            and queue.get("contact_policy", {}).get("no_duplicate_outreach") is True
            and queue.get("contact_policy", {}).get("no_new_paid_service") is True
            and queue.get("contact_policy", {}).get("no_automatic_sending") is True
            and all(v is False for v in queue.get("authorizations", {}).values()),
            "source_provider_followup_queue_not_hold")
    qproviders = queue.get("providers", [])
    require(isinstance(qproviders, list) and
            len(qproviders) == len(EXPECTED) and
            {x.get("id") for x in qproviders} == set(EXPECTED),
            "source_queue_must_cover_seven_relationships")

    providers = coverage.get("providers", [])
    require(coverage.get("provider_count") == 7
            and isinstance(providers, list) and
            len(providers) == 7 and
            {x.get("id") for x in providers} == set(EXPECTED),
            "seven_provider_coverage_incomplete")
    require(coverage.get("field_rights_dimensions") == sorted(RIGHTS_FIELDS)
            or set(coverage.get("field_rights_dimensions", [])) == RIGHTS_FIELDS
            and len(coverage.get("field_rights_dimensions", [])) == len(RIGHTS_FIELDS),
            "field_rights_dimensions_incomplete")
    for p in providers:
        name = p["id"]
        display, relationship, historical = EXPECTED[name]
        require(p.get("display_name") == display
                and p.get("relationship") == relationship
                and p.get("present_in_legacy_five_provider_receipt") is historical
                and p.get("source_queue_id") == name
                and p.get("specific_signed_rights_disposition_received") is False
                and p.get("evidence_review_owner_status") ==
                "pending_counsel_or_provider_confirmation",
                "missing_or_claimed_provider_permission_" + name)
        require(set(p.get("fields", {})) == RIGHTS_FIELDS
                and all(p["fields"][field] == "unapproved" for field in RIGHTS_FIELDS),
                "field_rights_not_unapproved_" + name)
        expected_status = (
            "conditional_transient_processing_only_not_a_general_release"
            if name == "fred_dgs2_dgs10" else "pending_written_permission"
        )
        require(p.get("current_status") == expected_status,
                "provider_status_wrong_" + name)
    for item in qproviders:
        grants = item.get("grants", {})
        require(grants.get("retention") == "unapproved"
                and grants.get("public_aggregate_distribution") == "unapproved"
                and grants.get("public_component_distribution") == "unapproved",
                "provider_queue_contains_unreviewed_grant")

    require(gate.get("state") == "hold"
            and gate.get("decision_receipt") is None
            and gate.get("approved_by") is None,
            "binding_publication_rights_gate_not_hold")
    require(surface.get("state") == "hold"
            and surface.get("production_change_authorized") is False
            and set(surface.get("classes", {})) == CLASSES,
            "public_rights_surface_no_longer_on_hold")
    require(private.get("state") == "review_only"
            and private.get("real_provider_evidence_authorized") is False
            and private.get("public_replacement_authorized") is False
            and private.get("production_change_authorized") is False,
            "private_provider_data_or_public_replacement_approved")

    pub = coverage.get("public_surface", {})
    require(set(pub.get("classes", [])) == CLASSES
            and len(pub.get("classes", [])) == 6
            and set(pub.get("class_status", {})) == CLASSES
            and all(pub["class_status"][c] == "pending_authority_review" for c in CLASSES)
            and pub.get("public_aggregate_schema_approved") is False
            and pub.get("private_real_provider_evidence_retention_approved") is False
            and pub.get("historical_git_pages_cdn_and_external_copies_disposition_approved") is False
            and pub.get("content_files_or_provider_values_read_for_this_register") is False,
            "public_classes_and_archive_treatment_not_pending")
    require(pub.get("current_tree_inventory") == str(INVENTORY)
            and pub.get("historical_metadata_inventory_classC_files") ==
            inventory.get("current_tree_total_class_c_files") == 54
            and pub.get("historical_metadata_inventory_dated_dirs") ==
            inventory.get("dated_archive", {}).get("directory_count") == 27
            and inventory.get("authorization", {}).get("public_redaction") is False
            and inventory.get("authorization", {}).get("production_release") is False,
            "historical_metadata_preservation_not_approved")

    zero = coverage.get("zero_paid_license_alternatives", {})
    require(zero.get("reference") == str(PHASE_A)
            and zero.get("all_eight_driver_equivalent_rights_safe_replacement_proven") is False
            and zero.get("four_signal_alternative_is_new_model_only") is True
            and zero.get("source_parity_verified") is False
            and zero.get("new_model_adopted") is False
            and phase_a.get("state") == "RESEARCH_ONLY_HOLD"
            and phase_a.get("decision", {}).get(
                "identified_complete_eight_driver_license_safe_pipeline") is False
            and all(v is False for v in phase_a.get("authorizations", {}).values()),
            "zero_paid_license_research_promoted_to_live")

    communications = coverage.get("communications", {})
    require(communications.get("affirmative_new_publication_permission_found") is False
            and communications.get("outreach_email_sent_by_this_work") is False
            and communications.get("subscription_or_purchase_authorized") is False
            and communications.get("avoid_duplicate_outreach") is True
            and communications.get("personal_contact_details_persisted") is False,
            "provider_outreach_or_rights_claim_unauthorized")
    readiness = coverage.get("release_readiness", {})
    require(readiness.get("seven_provider_coverage_completed_in_inventory") is True
            and all(value is False for key, value in readiness.items()
                    if key != "seven_provider_coverage_completed_in_inventory"),
            "release_readiness_incorrectly_claimed")
    permissions = coverage.get("authorizations", {})
    require(set(permissions) == EXPECTED_PERMISSIONS
            and all(permissions[x] is False for x in EXPECTED_PERMISSIONS),
            "rights_authorization_or_field_set_changed")

    return {
        "status": "passed", "controlling_issue": ISSUE,
        "rights_gate": "hold", "registered_relationships": len(providers),
        "legacy_template_rows": 5, "legacy_missing": ["ice_usdx", "treasury_h15_direct"],
        "written_provider_dispositions_complete": False,
        "public_field_classes_pending": 6,
        "historical_classC_path_inventory": 54,
        "zero_license_equivalent_ready": False,
        "public_aggregate_approved": False,
        "real_provider_retention_approved": False,
        "provider_outreach_performed": False,
        "Production_changed": False,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
