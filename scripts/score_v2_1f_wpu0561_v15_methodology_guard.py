#!/usr/bin/env python3
"""Issue #258 v15 DESIGN-ONLY source/page/provenance decision guard.

This module accepts ONLY enumerated invented scenario names. It does not fetch,
open, read or parse PDFs; no network, subprocess, provider access or credentials.
It validates the existing consumed-v13 state through the previously merged v14
guard and checks the v15 methodology choice has NOT been silently approved.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.score_v2_1f_wpu0561_pdf_v14_offline_diagnostics import (
    ROOT, validate_consumed_state, V13_CLAIM, V13_DISPATCH_SHA,
)

DESIGN = Path("governance/score-v2-1f-wpu0561-v15-methodology-decision.json")
V14 = Path("governance/score-v2-1f-wpu0561-v14-pagecount-forensic-design.json")
MANIFEST = Path("governance/score-v2-1f-wpu0561-v10-recovery-manifest.json")
V15_RECEIPT = Path("governance/score-v2-1f-wpu0561-v15-live-authorization.json")
V15_DISPATCH = Path("governance/score-v2-1f-wpu0561-v15-dispatch.json")
V15_LIVE_WORKFLOW = Path(".github/workflows/score-v2-1f-wpu0561-v15-live.yml")
OFFICIAL_PDF = "https://www.bls.gov/ppi/detailed-report/ppi-detailed-report-april-2026.pdf"

# These are invented model scenarios, NOT PDF observations, not source
# identifiers, and never permission for an actual network operation.
_SYNTHETIC_SCENARIOS: dict[str, tuple[str, str]] = {
    "v13_retained_ambiguous": ("v13_no_usable_page_decision", "hold"),
    "future_below_minimum": ("future_invalid_page_tree", "reject"),
    "future_above_existing_200": ("future_page_limit_reached", "halt"),
    "future_within_existing_200": ("future_count_only_not_source_proof", "hold"),
    "future_pdf_reader_failure": ("future_parser_failure", "halt"),
    "future_unverified_edition": ("future_original_release_not_proven", "hold"),
    "future_ambiguous_table_continuation": ("future_table9_scope_ambiguous", "halt"),
    "future_wrong_domestic_variant": ("future_not_exact_WPU0561", "reject"),
    "future_percent_change_not_index": ("future_unadjusted_level_missing", "reject"),
    "future_exact_schema_but_unproven_basis": ("future_bases_not_comparable", "hold"),
    "future_all_private_structure_but_rights_hold": ("future_rights_still_hold", "hold"),
}


def classify_invented_case(name: str) -> dict[str, Any]:
    """Fixed invented names only; cannot accept PDF bytes, URLs or values."""
    if type(name) is not str or name not in _SYNTHETIC_SCENARIOS:
        raise ValueError("only_enumerated_invented_scenario_names")
    reason, gate = _SYNTHETIC_SCENARIOS[name]
    return {
        "scenario_kind": "synthetic_name_only",
        "scenario": name,
        "outcome": gate,
        "reason_code": reason,
        "actual_pdf_page_count_observed": False,
        "actual_pdf_content_accessed": False,
        "first_release_pdf_proven": False,
        "real_WPU0561_index_level_proven": False,
        "economic_value_retained": False,
        "numeric_identifier_retained": False,
        "source_approved": False,
        "rights_approved": False,
        "new_owner_live_authorization": False,
        "Score_calculated": False,
        "Production_changed": False,
    }


def _read_json(root: Path, relative: Path) -> dict[str, Any]:
    result = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise RuntimeError("methodology_json_not_an_object")
    return result


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def validate_design_hold(root: Path | None = None) -> dict[str, Any]:
    """Read ONLY already committed governance files; fail closed on drift."""
    root = (root or ROOT).resolve()
    previous = validate_consumed_state(root)
    _require(previous["v13_claim_consumed"] is True and
             previous["v13_request_budget_remaining"] == 0 and
             previous["v13_workflow_inert"] is True,
             "v13_consumed_baseline_lost")

    plan = _read_json(root, DESIGN)
    v14 = _read_json(root, V14)
    manifest = _read_json(root, MANIFEST)
    _require(plan.get("version") == 15 and
             plan.get("state") == "design_only_owner_methodology_choice_pending" and
             plan.get("release_state") == "HOLD",
             "v15_design_hold_broken")
    _require(plan.get("prior_approved_forensic_commit") ==
             "2e028a553132c94db64ed9ba88927957374c2b1f" and
             v14.get("state") == "owner_approved_design_only_hold",
             "v14_provenance_or_hold_changed")
    claim = plan.get("immutable_oneoff_claim", {})
    _require(claim.get("ref") == V13_CLAIM and
             claim.get("target") == V13_DISPATCH_SHA and
             claim.get("must_never_be_deleted_or_reused") is True,
             "v13_oneoff_claim_no_longer_preserved")

    evidence = plan.get("authoritative_evidence", {})
    _require(evidence.get("v9_exact_fixed_2026_xlsx_index_level_available") is False and
             evidence.get("v9_original_fixed_pair_feasible") is False,
             "v9_fixed_resource_conclusion_rewritten")
    _require(evidence.get("v13_observed_reason") == "invalid_page_count" and
             evidence.get("v13_actual_page_count") is None and
             evidence.get("v13_possible_branches") == ["count_lt_1", "count_gt_200"],
             "v13_page_count_speculation")
    _require(evidence.get("v13_original_PDF_edition_immutability_proven") is False and
             evidence.get("v13_actual_Table9_unadjusted_level_verified") is False and
             evidence.get("v13_WPU0561_row_concept_verified") is False and
             evidence.get("v13_economic_or_identifier_values_retained") == 0,
             "v13_unobserved_schema_promoted")
    _require(evidence.get("original_v13_parser_git_blob_sha") ==
             "8a70409b0b5928e99de04930714dfc25774631ae",
             "v13_parser_not_pinned")

    source = plan.get("fixed_resource_to_review_only", {})
    _require(source.get("url") == OFFICIAL_PDF and
             source.get("methods_currently_allowed") == [] and
             source.get("future_method") == "not_selected" and
             source.get("source_candidate_not_adopted") is True and
             source.get("no_alternate_resource_or_alias") is True,
             "source_or_network_boundary_broadened")
    permission = plan.get("permissions")
    _require(isinstance(permission, dict) and permission and
             all(value is False for value in permission.values()),
             "v15_permission_not_design_only")
    _require(not (root / V15_RECEIPT).exists() and
             not (root / V15_DISPATCH).exists() and
             not (root / V15_LIVE_WORKFLOW).exists(),
             "v15_unapproved_live_artifact_detected")

    layers = plan.get("proposed_diagnostic_layers", [])
    _require(isinstance(layers, list) and
             [x.get("id") for x in layers if isinstance(x, dict)] ==
             ["D0", "D1", "D2", "D3", "D4", "D5", "D6"] and
             len(layers) == 7,
             "diagnostic_layers_changed")
    _require(layers[0].get("status") == "done_from_repository_no_network" and
             layers[2].get("status") == "not_authorized" and
             layers[5].get("status") == "independent_issue_155_hold" and
             layers[6].get("status") == "not_authorized",
             "methodology_gate_implicitly_activated")
    options = plan.get("decisions", {})
    _require(set(options) == {"A", "B", "C"} and
             all(isinstance(item, dict) and item.get("owner_chosen_now") is False
                 for item in options.values()) and
             options["B"].get("future_live_authorization_required") is True,
             "methodology_owner_choice_fabricated")
    _require(plan.get("recommended_next_choice") ==
             "A_as_safe_default_with_B_retained_as_separately_scoped_research_option",
             "recommendation_not_nonbinding")

    v15_record = manifest.get("v15", {})
    _require(v15_record.get("state") == "design_only_methodology_pending_choice" and
             v15_record.get("no_network_requests") is True and
             v15_record.get("request_budget") == 0 and
             v15_record.get("rights_155_hold") is True and
             v15_record.get("Score_or_Production_changes") is False and
             v15_record.get("consumed_v13_claim_ref") == V13_CLAIM,
             "v15_manifest_contract_broken")
    _require(all(x is False for x in manifest.get("authorizations", {}).values()),
             "older_recovery_authorization_changed")

    return {
        "status": "passed",
        "version": 15,
        "stage": "design_only_methodology_pending_choice",
        "decision_options": ["A", "B", "C"],
        "owner_choice_made": False,
        "v13_claim_preserved": True,
        "v13_request_budget": 0,
        "v13_actual_page_count_known": False,
        "original_release_vintage_proven": False,
        "index_level_feasibility_proven": False,
        "rights_155": "hold",
        "BLS_requests_performed_in_v15": 0,
        "economic_values_read_in_v15": 0,
        "Score_or_Production_changed": False,
    }


if __name__ == "__main__":
    print(json.dumps({
        "guard": validate_design_hold(),
        "invented_outcomes": [
            classify_invented_case(case)
            for case in sorted(_SYNTHETIC_SCENARIOS)
        ],
    }, sort_keys=True, indent=2))
