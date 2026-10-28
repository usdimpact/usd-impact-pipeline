#!/usr/bin/env python3
"""Validate dispatched WPU0561 column-semantics authorization."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any

RECEIPT = "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-dispatch.json"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/244"
APPROVAL_COMMENT = 6482193778
APPROVED_AT = "2026-10-28T22:23:21Z"
ACTIVATION_COMMIT = "474770a01b5493537731697f804e88b4e849d41d"
EXPECTED_UA = "USD-Impact-Score-v2.1F-WPU0561-column-semantics/1.0 (contact: support@usd-impact.com)"
EXPECTED_RESOURCES = [
    "/news.release/archives/ppi_05152013.htm",
    "/ppi/detailed-report/ppi-detailed-report-april-2026.xlsx",
]

def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload

def validate(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    design = _load(root / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-design.json")
    template = _load(root / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-authorization.template.json")
    receipt = _load(root / RECEIPT)
    dispatch = _load(root / DISPATCH)
    contract = _load(root / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-execution-contract.json")
    prior = _load(root / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-consumption-2026-10-28.json")
    rights = _load(root / "governance/score-publication-rights-gate.json")
    prereg = _load(root / "governance/score-v2-1f-preregistration.json")
    workflow = (root / ".github/workflows/score-v2-1f-bls-wpu0561-column-semantics-preflight.yml").read_text(encoding="utf-8")

    if prior.get("state") != "consumed_after_success":
        raise RuntimeError("row-presence consumption evidence changed")
    if rights.get("state") != "hold":
        raise RuntimeError("Score publication rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")

    if design.get("state") != "design_only_hold":
        raise RuntimeError("frozen column-semantics design changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("column-semantics issue changed")
    if [item.get("path") for item in design.get("fixed_resources", [])] != EXPECTED_RESOURCES:
        raise RuntimeError("column-semantics fixed resources changed")
    if design.get("identifier_policy", {}).get("conflicting_header_behavior") != "classify_ambiguous_never_identifier":
        raise RuntimeError("conflicting-header fail-closed policy changed")
    if design.get("identifier_policy", {}).get("row_wide_identifier_fallback") is not False:
        raise RuntimeError("row-wide identifier fallback must remain disabled")

    if template.get("decision_status") != "hold" or any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template changed")

    if receipt.get("decision_status") != "approved" or receipt.get("issue") != ISSUE:
        raise RuntimeError("active receipt is invalid")
    if receipt.get("execution_scope") != "bls_wpu0561_column_semantics_preflight_only":
        raise RuntimeError("active receipt scope changed")
    if receipt.get("request_budget") != 2 or receipt.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("active receipt request boundary changed")
    if receipt.get("contact_user_agent") != EXPECTED_UA:
        raise RuntimeError("active receipt User-Agent changed")
    if receipt.get("approved_by") != "usdimpact owner via Issue #244 approval comment 6482193778":
        raise RuntimeError("active receipt approval identity changed")
    if receipt.get("approved_at") != APPROVED_AT:
        raise RuntimeError("active receipt approval timestamp changed")
    auth = receipt.get("authorizations", {})
    for field in ("response_body_ephemeral_retrieval","column_semantics_preflight","numeric_identifier_field_read"):
        if auth.get(field) is not True:
            raise RuntimeError(f"{field} must be true")
    for field in ("economic_value_extraction","real_data_research","full_historical_reconstruction","candidate_score_computation","research_ledger_mutation","public_artifact_replacement","production"):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if dispatch.get("state") != "approved_dispatch":
        raise RuntimeError("dispatch state changed")
    if dispatch.get("phase") != "bls_wpu0561_column_semantics_preflight":
        raise RuntimeError("dispatch phase changed")
    if dispatch.get("issue") != ISSUE:
        raise RuntimeError("dispatch issue changed")
    if dispatch.get("authorization_activation_merge_commit") != ACTIVATION_COMMIT:
        raise RuntimeError("dispatch activation commit changed")
    if dispatch.get("request_budget") != 2 or dispatch.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("dispatch request boundary changed")
    for field in ("response_body_ephemeral_retrieval_authorized","column_semantics_preflight_authorized","numeric_identifier_field_read_authorized"):
        if dispatch.get(field) is not True:
            raise RuntimeError(f"{field} must be true in dispatch")
    for field in ("economic_value_extraction_authorized","real_data_research_authorized","full_historical_reconstruction_authorized","candidate_score_computation_authorized","research_ledger_mutation_authorized","public_artifact_replacement_authorized","production_authorized"):
        if dispatch.get(field) is not False:
            raise RuntimeError(f"{field} must remain false in dispatch")

    if contract.get("state") != "column_semantics_preflight_authorized":
        raise RuntimeError("execution contract must be dispatched-active")
    if contract.get("owner_approval_comment_id") != APPROVAL_COMMENT or contract.get("owner_approval_timestamp") != APPROVED_AT:
        raise RuntimeError("contract approval evidence changed")
    if contract.get("authorization_activation_merge_commit") != ACTIVATION_COMMIT:
        raise RuntimeError("contract activation commit changed")
    if contract.get("active_authorization_receipt_expected_now") is not True or contract.get("dispatch_marker_expected_now") is not True:
        raise RuntimeError("receipt/dispatch must both be expected")
    if contract.get("request_budget") != 2 or contract.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("contract request boundary changed")
    current = contract.get("current_state", {})
    for field in ("response_body_ephemeral_retrieval_authorized","column_semantics_preflight_authorized","numeric_identifier_field_read_authorized"):
        if current.get(field) is not True:
            raise RuntimeError(f"{field} must be true while dispatched")
    for field in ("economic_value_extraction_authorized","real_data_research_authorized","full_historical_reconstruction_authorized","candidate_score_computation_authorized","research_ledger_mutation_authorized","public_artifact_replacement_authorized","production_authorized"):
        if current.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if "score-v2-1f-bls-wpu0561-column-semantics-preflight-dispatch.json" not in workflow:
        raise RuntimeError("workflow is not path-gated to the dispatch marker")
    if ("if: $" + "{{ false }}") in workflow:
        raise RuntimeError("workflow must be active in dispatched state")

    return {
        "status": "passed",
        "state": "column_semantics_preflight_authorized",
        "issue": ISSUE,
        "activation_merge_commit": ACTIVATION_COMMIT,
        "request_budget": 2,
        "active_receipt_present": True,
        "dispatch_present": True,
        "response_body_ephemeral_retrieval_authorized": True,
        "column_semantics_preflight_authorized": True,
        "numeric_identifier_field_read_authorized": True,
        "economic_value_extraction_authorized": False,
        "candidate_score_computation_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }

def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
