#!/usr/bin/env python3
"""Issue #258 v14 OFFLINE forensic guard for consumed BLS PDF preflight.

Reads local committed JSON/YAML source files only. No HTTP, BLS, PDF, pypdf,
OCR, provider APIs, environment secrets, or runtime authorization. The
synthetic count classifier never represents a real PDF observation.

Historical v13 execution is deliberately immutable in this module.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DESIGN = Path("governance/score-v2-1f-wpu0561-v14-pagecount-forensic-design.json")
LEDGER = Path("governance/score-v2-1f-wpu0561-pdf-v13-consumption-2026-10-29.json")
CONTRACT = Path("governance/score-v2-1f-wpu0561-pdf-v13-execution-contract.json")
RIGHTS = Path("governance/score-publication-rights-gate.json")
WORKFLOW = Path(".github/workflows/score-v2-1f-wpu0561-pdf-v13-oneoff.yml")
V13_RECEIPT = Path("governance/score-v2-1f-wpu0561-pdf-v13-live-authorization.json")
V13_DISPATCH = Path("governance/score-v2-1f-wpu0561-pdf-v13-dispatch.json")
V8_RECEIPT = Path("governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json")
V8_DISPATCH = Path("governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json")
PAGE_LIMIT_V13 = 200
V13_CLAIM = "refs/tags/score-v2-1f-wpu0561-pdf-v13-oneoff-2026-10-29"
V13_DISPATCH_SHA = "82adf0b250871887e82123ed56f641d09fa14ba0"


def _read(root: Path, path: Path) -> dict[str, Any]:
    data = json.loads((root / path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("governance_json_not_object")
    return data


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def synthetic_count_case(fake_page_count: int) -> dict[str, Any]:
    """Mirror v13 two-sided page test for INVENTED counts only.

    Never pass a real PDF's page count to this function. A synthetic compatible
    count does NOT establish eligible report schema, source vintage or rights.
    """
    if type(fake_page_count) is not int:
        raise ValueError("synthetic_count_must_be_plain_integer")
    if fake_page_count < 1:
        branch = "synthetic_below_minimum"
    elif fake_page_count > PAGE_LIMIT_V13:
        branch = "synthetic_over_existing_limit"
    else:
        branch = "synthetic_within_existing_limit"
    return {
        "case_kind": "invented_scalar_only",
        "branch": branch,
        "v13_failure_code": "invalid_page_count" if branch != "synthetic_within_existing_limit" else None,
        "source_pdf_fetched": False,
        "source_data_read": False,
        "economic_values_retained": False,
        "identifier_values_retained": False,
        "score_calculated": False,
        "production_changed": False,
        "real_pdf_branch_proven": False,
        "permission_to_change_page_limit": False,
        "permission_to_request_pdf": False,
    }


def v13_evidence_interpretation() -> dict[str, Any]:
    """Interpret only the retained, deliberately ambiguous v13 status."""
    return {
        "observed_code": "invalid_page_count",
        "possible_v13_branches": ["page_count_below_one", "page_count_above_existing_200_limit"],
        "exact_branch_identified": False,
        "actual_pdf_page_count_known": False,
        "table9_observed": False,
        "pdf_source_adopted": False,
        "original_release_vintage_proven": False,
        "no_new_source_request_authorized": True,
    }


def validate_consumed_state(root: Path | None = None) -> dict[str, Any]:
    root = (root or ROOT).resolve()
    design = _read(root, DESIGN)
    ledger = _read(root, LEDGER)
    contract = _read(root, CONTRACT)
    rights = _read(root, RIGHTS)
    wf = (root / WORKFLOW).read_text(encoding="utf-8")

    _require(design.get("version") == 14 and design.get("state") == "owner_approved_design_only_hold",
             "v14_no_longer_design_only")
    _require(design.get("exact_root_cause_evidence", {}).get("max_pages_at_v13") == PAGE_LIMIT_V13,
             "v14_page_ceiling_changed")
    _require(design.get("exact_root_cause_evidence", {}).get("actual_pdf_page_count") is None,
             "v14_fabricated_actual_page_count")
    _require(design.get("exact_root_cause_evidence", {}).get("exact_branch_identified") is False,
             "v14_improper_branch_attribution")
    _require(design.get("baseline", {}).get("v13_claim_sha") == V13_DISPATCH_SHA,
             "v14_claim_commit_changed")
    _require(design.get("v14_only_actions", {}).get("BLS_pdf_GET") is False,
             "v14_download_authorization_changed")
    for key in (
        "BLS_pdf_HEAD", "BLS_page_scan", "third_party_pdf_or_mirror_fetch",
        "source_fallback", "page_cap_increase", "numeric_identifier_read",
        "economic_value_read", "score_reconstruction", "score_calculation",
        "rights_release", "research_ledger_change", "public_artifact_write",
        "production_change",
    ):
        _require(design.get("v14_only_actions", {}).get(key) is False,
                 "v14_execution_gate_broadened")
    _require(
        design.get("authorization") == {
            "v14_design_only": True,
            "new_BLS_request": False,
            "page_bound_relaxation": False,
            "economic_fields": False,
            "publication": False,
            "production": False,
        },
        "v14_authorization_not_inert",
    )

    _require(ledger.get("state") == "consumed_after_one_off_pdf_structural_preflight_fail_closed",
             "v13_consumption_state_changed")
    _require(ledger.get("status") == "fail_closed" and ledger.get("reason_codes") == ["invalid_page_count"],
             "v13_consumption_reason_changed")
    _require(ledger.get("pdf_actual_page_count") is None,
             "v13_page_count_not_publicly_known")
    _require(ledger.get("page_count_policy_bound") == PAGE_LIMIT_V13,
             "v13_historical_limit_changed")
    _require(ledger.get("consumed_claim_ref") == V13_CLAIM,
             "v13_claim_ref_changed")
    _require(ledger.get("consumed_claim_commit") == V13_DISPATCH_SHA,
             "v13_claim_sha_changed")
    _require(ledger.get("authorization_consumed_even_on_failure") is True and
             ledger.get("rerun_forbidden") is True,
             "v13_consumption_no_longer_enforced")
    _require(ledger.get("economic_values_retained") is False and
             ledger.get("identifier_values_retained") is False,
             "v13_source_value_retention_flag_changed")
    _require(ledger.get("source_field_feasibility_proven") is False and
             ledger.get("historical_original_release_vintage_verified") is False,
             "v13_not_proof_of_original_edition")

    _require(contract.get("version") == 13 and
             contract.get("state") == "consumed_after_failed_structural_preflight_invalid_page_count",
             "v13_execution_contract_reactivated")
    _require(contract.get("request_budget_remaining_now") == 0,
             "v13_budget_reactivated")
    live = contract.get("authorization_state", {})
    for key in ("current_live_BLS_GET", "receipt_created", "dispatch_marker_created",
                "execution_workflow_enabled", "identifier_read", "economic_value_read",
                "score_or_reconstruction", "research_ledger_change", "public_write", "production_change"):
        _require(live.get(key) is False, "v13_execution_permission_reactivated")
    _require(live.get("claim_written") is True, "v13_claim_unaccounted")
    _require(not (root / V13_RECEIPT).exists() and not (root / V13_DISPATCH).exists() and
             not (root / V8_RECEIPT).exists() and not (root / V8_DISPATCH).exists(),
             "old_consumed_authorization_or_dispatch_reappeared")
    _require("  push:" not in wf and "if: $" + "{{ false }}" in wf and
             "consume-before-http:" not in wf,
             "v13_workflow_not_inert")
    _require(rights.get("state") == "hold" and rights.get("decision_receipt") is None,
             "independent_rights_gate_no_longer_hold")

    return {
        "status": "passed",
        "stage": "v14_offline_forensic_only",
        "v13_claim_consumed": True,
        "v13_request_budget_remaining": 0,
        "v13_workflow_inert": True,
        "v13_pdf_exact_pages_known": False,
        "v13_failure_code": "invalid_page_count",
        "v13_possible_branches": v13_evidence_interpretation()["possible_v13_branches"],
        "original_release_vintage_proven": False,
        "source_values_retained": 0,
        "rights_issue_155": "hold",
        "new_PDF_request_made": False,
        "live_request_authorized": False,
        "page_limit_changed": False,
        "score_or_production_modified": False,
    }


if __name__ == "__main__":
    print(json.dumps({
        "guard": validate_consumed_state(),
        "forensic_interpretation": v13_evidence_interpretation(),
        "invented_boundary_cases": [
            synthetic_count_case(n) for n in (0, 1, PAGE_LIMIT_V13, PAGE_LIMIT_V13 + 1)
        ],
    }, sort_keys=True, indent=2))
