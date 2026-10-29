#!/usr/bin/env python3
"""Issue #258: v16 owner-approved Option A historical WPU0561 method closure.

Strictly local, read-only, no network/PDF/Score execution. Preserves the
historical v15 file that recorded NO choice at its earlier publication date.
Fails closed if the consumed v13 boundary or v15 historical decisions drift.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.score_v2_1f_wpu0561_v15_methodology_guard import (
    ROOT, DESIGN as V15_DESIGN, MANIFEST, validate_design_hold,
)

V16 = Path("governance/score-v2-1f-wpu0561-v16-owner-option-a-decision.json")
V16_RECEIPT = Path("governance/score-v2-1f-wpu0561-v16-live-authorization.json")
V16_DISPATCH = Path("governance/score-v2-1f-wpu0561-v16-dispatch.json")
V16_WORKFLOW = Path(".github/workflows/score-v2-1f-wpu0561-v16-live.yml")
V15_ORIGINAL_GIT_BLOB = "4181d3d59ef931523508a3fe4efc1a790b72f115"
V13_CLAIM = "refs/tags/score-v2-1f-wpu0561-pdf-v13-oneoff-2026-10-29"
V13_CLAIM_TARGET = "82adf0b250871887e82123ed56f641d09fa14ba0"

def require(test: bool, code: str) -> None:
    if test is not True:
        raise RuntimeError(code)

def read_json(root: Path, path: Path) -> dict[str, Any]:
    obj = json.loads((root / path).read_text(encoding="utf-8"))
    require(isinstance(obj, dict), "decision_json_not_object")
    return obj

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()

def validate_owner_option_a(root: Path | None = None) -> dict[str, Any]:
    """Inspect only pinned git-checkout files. Never request a source."""
    root = (root or ROOT).resolve()
    former = validate_design_hold(root)
    require(former["status"] == "passed" and former["owner_choice_made"] is False
            and former["v13_request_budget"] == 0,
            "historical_design_hold_changed")
    old_path = root / V15_DESIGN
    require(git_blob_sha(old_path.read_bytes()) == V15_ORIGINAL_GIT_BLOB,
            "historical_v15_choice_record_rewritten")
    decision = read_json(root, V16)
    require(decision.get("version") == 16
            and decision.get("recorded_date") == "2026-10-29"
            and decision.get("state") == "owner_approved_option_A_fixed_resource_methodology_closed"
            and decision.get("decision_class") ==
            "methodological_stop_decision_only_not_executable_release",
            "owner_option_a_decision_not_valid")
    att = decision.get("owner_attestation", {})
    require(att.get("option") == "A" and
            att.get("effective_date") == "2026-10-29" and
            att.get("historical_v15_unselected_record_is_not_rewritten") is True and
            att.get("no_prior_approval_backdated") is True and
            att.get("new_BLS_or_publication_approval_inferred") is False,
            "option_a_not_separately_attested")
    require(decision.get("frozen_prior_decision_commit") ==
            "381db57df68db8624cc3b03e83ac5a1febd06611",
            "v15_provenance_replaced")

    outcome = decision.get("option_A", {})
    require(outcome.get("chosen") is True and
            outcome.get("new_historical_WPU0561_pair_admissible") is False and
            outcome.get("original_fixed_pair_feasible") is False and
            outcome.get("Crude_petroleum_identifier_0561_proof_preserved") is True and
            outcome.get("requires_another_BLS_request") is False and
            outcome.get("scope") ==
            "WPU0561 historical-vintage representative pair for the specifically preregistered 2013 HTML / 2026 XLSX resources, NOT the availability of WPU0561 generally or the broader public Score drivers.",
            "option_a_scope_or_infeasibility_broadened")
    for key in (
        "authorizes_removing_live_score_driver", "authorizes_new_score_formula",
        "authorizes_source_substitution", "authorizes_publishing_WPU0561_observation",
    ):
        require(outcome.get(key) is False, "option_a_scope_incorrectly_expanded")
    require(outcome.get("decision_does_not_revoke_future_independent_research") is True,
            "future_independent_research_incorrectly_revoked")

    evidence = decision.get("unchanged_evidence", {})
    require(evidence.get("v9_2013_HTML_structurally_supports_unadjusted_index_role") is True and
            evidence.get("v9_2026_selected_XLSX_container") == "xl/worksheets/sheet3.xml" and
            evidence.get("v9_2026_selected_XLSX_index_level_header_present") is False and
            evidence.get("v9_2026_selected_XLSX_percent_change_header_present") is True and
            evidence.get("normalized_identifier") == "0561",
            "v9_original_fixed_resource_proof_changed")
    require(evidence.get("v13_sanitized_reason") == "invalid_page_count" and
            evidence.get("v13_actual_PDF_page_count") is None and
            evidence.get("v13_possible_conditions") ==
            ["page_count_less_than_one", "page_count_greater_than_200"] and
            evidence.get("v13_original_release_PDF_vintage_proven") is False and
            evidence.get("v13_Table9_WPU0561_index_level_proven") is False and
            evidence.get("v13_economic_values_retained") == 0 and
            evidence.get("v13_identifier_values_retained") == 0,
            "v13_non_economic_result_promoted")
    require(evidence.get("v13_claim_ref") == V13_CLAIM and
            evidence.get("v13_claim_target") == V13_CLAIM_TARGET and
            all(evidence.get("v15_decision_" + c + "_owner_chosen_then") is False
                for c in ("A", "B", "C")),
            "historical_v15_or_v13_provenance_modified")

    b = decision.get("path_B_future_only", {})
    require(b.get("status") == "not_approved" and
            b.get("requires_new_owner_methodology_and_one_off_authorization") is True and
            b.get("requires_new_source_boundary_preregistration") is True and
            b.get("requires_new_one_use_claim_and_cleanup") is True and
            b.get("does_not_inherit_v8_or_v13_consumed_receipt") is True and
            b.get("no_current_live_request_permission") is True and
            decision.get("path_C_not_selected") is True,
            "new_source_research_not_independently_gated")

    disposition = decision.get("research_disposition", {})
    require(disposition.get("issue_155") ==
            "independent_rights_and_redistribution_review_remains_OPEN_HOLD" and
            disposition.get("no_automatic_public_rights_clearance") is True and
            disposition.get("no_methodology_change_in_existing_score_formula") is True and
            disposition.get("no_BLS_PDF_pagecount_resolution_claim") is True,
            "rights_or_scope_wrongly_released")
    runtime = decision.get("runtime_boundary", {})
    require(isinstance(runtime, dict) and runtime and
            runtime.get("request_budget_remaining") == 0 and
            all(value is True for key, value in runtime.items()
                if key != "request_budget_remaining"),
            "runtime_data_or_production_boundary_undermined")
    permissions = decision.get("permissions", {})
    require(isinstance(permissions, dict) and permissions and
            all(value is False for value in permissions.values()),
            "new_live_authorization_inserted")
    require(not (root / V16_RECEIPT).exists() and
            not (root / V16_DISPATCH).exists() and
            not (root / V16_WORKFLOW).exists(),
            "v16_live_receipt_dispatch_or_workflow_present")

    manifest = read_json(root, MANIFEST)
    record = manifest.get("v16", {})
    require(record.get("state") == "owner_option_A_fixed_resource_closed_no_runtime_change" and
            record.get("chosen_option") == "A" and
            record.get("v15_immutable_unselected") is True and
            record.get("zero_new_BLS_requests") is True and
            record.get("request_budget_remaining") == 0 and
            record.get("issue_155_rights_hold") is True and
            record.get("score_changed") is False and
            record.get("production_changed") is False and
            record.get("consumed_claim") == V13_CLAIM,
            "recovery_manifest_not_option_a_only")
    require(all(v is False for v in manifest.get("authorizations", {}).values()),
            "older_recovery_permissions_broadened")

    return {
        "status": "passed",
        "decision": "A",
        "decision_date": "2026-10-29",
        "scope": "original_fixed_2013_HTML_2026_XLSX_historical_pair_only",
        "fixed_pair_index_level_feasible": False,
        "commodity_identifier_0561_preserved": True,
        "v15_original_choice_record_unchanged": True,
        "v13_claim_consumed": True,
        "requests_remaining": 0,
        "new_BLS_requests": 0,
        "original_release_pdf_evidence_proven": False,
        "rights_155": "hold",
        "historical_score_observation_created": False,
        "production_changed": False,
        "future_B_requires_separate_authorization": True,
    }

if __name__ == "__main__":
    print(json.dumps(validate_owner_option_a(), sort_keys=True, indent=2))
