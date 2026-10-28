#!/usr/bin/env python3
"""Validate dispatched WPU0561 representative-index authorization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RECEIPT = "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-dispatch.json"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/252"
APPROVAL_COMMENT = 6482942968
APPROVED_AT = "2026-10-28T23:02:22Z"
ACTIVATION_COMMIT = "c41413ce08f3fad32cefe7ad307449eac0e65978"
EXPECTED_UA = "USD-Impact-Score-v2.1F-WPU0561-representative-index/1.0 (contact: support@usd-impact.com)"
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
    design = _load(root / "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-design.json")
    template = _load(root / "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-authorization.template.json")
    receipt = _load(root / RECEIPT)
    dispatch = _load(root / DISPATCH)
    contract = _load(root / "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-execution-contract.json")
    predecessor = _load(root / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-consumption-2026-10-29.json")
    rights = _load(root / "governance/score-publication-rights-gate.json")
    prereg = _load(root / "governance/score-v2-1f-preregistration.json")
    workflow = (root / ".github/workflows/score-v2-1f-bls-wpu0561-representative-index-preflight.yml").read_text(encoding="utf-8")

    if predecessor.get("state") != "consumed_after_success":
        raise RuntimeError("Issue #244 consumption evidence changed")
    if predecessor.get("sanitized_result", {}).get("wpu0561_mapping_proven") is not True:
        raise RuntimeError("Issue #244 WPU0561 mapping evidence changed")
    if rights.get("state") != "hold":
        raise RuntimeError("Score publication rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")

    if design.get("state") != "design_only_hold":
        raise RuntimeError("frozen representative-index design changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("representative-index owner-decision issue changed")
    if [item.get("path") for item in design.get("fixed_resources", [])] != EXPECTED_RESOURCES:
        raise RuntimeError("representative-index fixed resources changed")
    policy = design.get("field_semantics_policy", {})
    if policy.get("allowed") != ["original_release_index_level"]:
        raise RuntimeError("allowed field semantics changed")
    if policy.get("multiple_index_level_candidates_fail_closed") is not True:
        raise RuntimeError("multiple-candidate fail-closed policy changed")
    if policy.get("ambiguous_revision_context_fails_closed") is not True:
        raise RuntimeError("revision ambiguity policy changed")

    if template.get("decision_status") != "hold" or any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template changed")

    if receipt.get("decision_status") != "approved" or receipt.get("issue") != ISSUE:
        raise RuntimeError("active receipt is invalid")
    if receipt.get("execution_scope") != "bls_wpu0561_representative_index_preflight_only":
        raise RuntimeError("active receipt scope changed")
    if receipt.get("request_budget") != 2:
        raise RuntimeError("active receipt request budget changed")
    if receipt.get("max_observations_total") != 2 or receipt.get("max_observations_per_resource") != 1:
        raise RuntimeError("active receipt observation cap changed")
    if receipt.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("active receipt resources changed")
    if receipt.get("allowed_host") != "www.bls.gov":
        raise RuntimeError("active receipt host changed")
    if receipt.get("contact_user_agent") != EXPECTED_UA:
        raise RuntimeError("active receipt User-Agent changed")
    if receipt.get("approved_by") != "usdimpact owner via Issue #252 approval comment 6482942968":
        raise RuntimeError("active receipt approval identity changed")
    if receipt.get("approved_at") != APPROVED_AT:
        raise RuntimeError("active receipt approval timestamp changed")

    auth = receipt.get("authorizations", {})
    for field in (
        "response_body_ephemeral_retrieval",
        "representative_index_value_read",
        "representative_index_preflight",
    ):
        if auth.get(field) is not True:
            raise RuntimeError(f"{field} must be true")
    for field in (
        "full_historical_reconstruction",
        "candidate_score_computation",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if dispatch.get("state") != "approved_dispatch":
        raise RuntimeError("dispatch state changed")
    if dispatch.get("phase") != "bls_wpu0561_representative_index_preflight":
        raise RuntimeError("dispatch phase changed")
    if dispatch.get("issue") != ISSUE:
        raise RuntimeError("dispatch issue changed")
    if dispatch.get("authorization_activation_merge_commit") != ACTIVATION_COMMIT:
        raise RuntimeError("dispatch activation commit changed")
    if dispatch.get("request_budget") != 2:
        raise RuntimeError("dispatch request budget changed")
    if dispatch.get("max_observations_total") != 2 or dispatch.get("max_observations_per_resource") != 1:
        raise RuntimeError("dispatch observation cap changed")
    if dispatch.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("dispatch resources changed")
    for field in (
        "response_body_ephemeral_retrieval_authorized",
        "representative_index_value_read_authorized",
        "representative_index_preflight_authorized",
    ):
        if dispatch.get(field) is not True:
            raise RuntimeError(f"{field} must be true in dispatch")
    for field in (
        "full_historical_reconstruction_authorized",
        "candidate_score_computation_authorized",
        "research_ledger_mutation_authorized",
        "public_artifact_replacement_authorized",
        "production_authorized",
    ):
        if dispatch.get(field) is not False:
            raise RuntimeError(f"{field} must remain false in dispatch")

    if contract.get("state") != "representative_index_preflight_authorized":
        raise RuntimeError("execution contract must be dispatched-active")
    if contract.get("owner_approval_comment_id") != APPROVAL_COMMENT or contract.get("owner_approval_timestamp") != APPROVED_AT:
        raise RuntimeError("contract approval evidence changed")
    if contract.get("authorization_activation_merge_commit") != ACTIVATION_COMMIT:
        raise RuntimeError("contract activation commit changed")
    if contract.get("active_authorization_receipt_expected_now") is not True or contract.get("dispatch_marker_expected_now") is not True:
        raise RuntimeError("receipt/dispatch must both be expected")
    if contract.get("request_budget") != 2:
        raise RuntimeError("contract request budget changed")
    if contract.get("max_observations_total") != 2 or contract.get("max_observations_per_resource") != 1:
        raise RuntimeError("contract observation cap changed")
    if contract.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("contract resources changed")

    current = contract.get("current_state", {})
    for field in (
        "response_body_ephemeral_retrieval_authorized",
        "representative_index_value_read_authorized",
        "representative_index_preflight_authorized",
    ):
        if current.get(field) is not True:
            raise RuntimeError(f"{field} must be true while dispatched")
    for field in (
        "full_historical_reconstruction_authorized",
        "candidate_score_computation_authorized",
        "research_ledger_mutation_authorized",
        "public_artifact_replacement_authorized",
        "production_authorized",
    ):
        if current.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if "score-v2-1f-bls-wpu0561-representative-index-preflight-dispatch.json" not in workflow:
        raise RuntimeError("workflow is not path-gated to the dispatch marker")
    if ("if: $" + "{{ false }}") in workflow:
        raise RuntimeError("workflow must be active in dispatched state")

    return {
        "status": "passed",
        "state": "representative_index_preflight_authorized",
        "issue": ISSUE,
        "activation_merge_commit": ACTIVATION_COMMIT,
        "request_budget": 2,
        "max_observations_total": 2,
        "max_observations_per_resource": 1,
        "active_receipt_present": True,
        "dispatch_present": True,
        "response_body_ephemeral_retrieval_authorized": True,
        "representative_index_value_read_authorized": True,
        "representative_index_preflight_authorized": True,
        "candidate_score_computation_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }

def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
