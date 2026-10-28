#!/usr/bin/env python3
"""Validate active-but-not-dispatched WPU0561 representative-index authorization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RECEIPT = "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-dispatch.json"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/252"
APPROVAL_COMMENT = 6482942968
APPROVED_AT = "2026-10-28T23:02:22Z"
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
    contract = _load(root / "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-execution-contract.json")
    predecessor = _load(root / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-consumption-2026-10-29.json")
    rights = _load(root / "governance/score-publication-rights-gate.json")
    prereg = _load(root / "governance/score-v2-1f-preregistration.json")
    workflow = (root / ".github/workflows/score-v2-1f-bls-wpu0561-representative-index-preflight.yml").read_text(encoding="utf-8")

    if (root / DISPATCH).exists():
        raise RuntimeError("dispatch must remain absent before separate review")

    if predecessor.get("state") != "consumed_after_success":
        raise RuntimeError("Issue #244 consumption evidence changed")
    if predecessor.get("sanitized_result", {}).get("wpu0561_mapping_proven") is not True:
        raise RuntimeError("Issue #244 WPU0561 mapping evidence changed")
    if predecessor.get("new_owner_authorization_required_for_any_future_live_request") is not True:
        raise RuntimeError("future live work must require a new owner authorization")

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

    if template.get("decision_status") != "hold":
        raise RuntimeError("authorization template must remain HOLD")
    if template.get("contact_user_agent") is not None:
        raise RuntimeError("HOLD template must not preselect contact identity")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template authorizations must remain false")

    if receipt.get("decision_status") != "approved":
        raise RuntimeError("active representative-index receipt is not approved")
    if receipt.get("issue") != ISSUE:
        raise RuntimeError("active receipt issue changed")
    if receipt.get("execution_scope") != "bls_wpu0561_representative_index_preflight_only":
        raise RuntimeError("active receipt scope changed")
    if receipt.get("request_budget") != 2:
        raise RuntimeError("active receipt request budget changed")
    if receipt.get("max_observations_total") != 2:
        raise RuntimeError("active receipt total observation cap changed")
    if receipt.get("max_observations_per_resource") != 1:
        raise RuntimeError("active receipt per-resource observation cap changed")
    if receipt.get("allowed_host") != "www.bls.gov":
        raise RuntimeError("active receipt host changed")
    if receipt.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("active receipt resources changed")
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
            raise RuntimeError(f"{field} must be authorized")
    for field in (
        "full_historical_reconstruction",
        "candidate_score_computation",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if contract.get("state") != "representative_index_preflight_authorized_pending_dispatch":
        raise RuntimeError("execution contract must be active but pending dispatch")
    if contract.get("owner_approval_comment_id") != APPROVAL_COMMENT:
        raise RuntimeError("contract approval comment changed")
    if contract.get("owner_approval_timestamp") != APPROVED_AT:
        raise RuntimeError("contract approval timestamp changed")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("active receipt must be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch must remain absent")
    if contract.get("request_budget") != 2:
        raise RuntimeError("contract request budget changed")
    if contract.get("max_observations_total") != 2:
        raise RuntimeError("contract total observation cap changed")
    if contract.get("max_observations_per_resource") != 1:
        raise RuntimeError("contract per-resource observation cap changed")
    if contract.get("contact_user_agent") != EXPECTED_UA:
        raise RuntimeError("contract User-Agent changed")
    if contract.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("contract resources changed")

    current = contract.get("current_state", {})
    for field in (
        "response_body_ephemeral_retrieval_authorized",
        "representative_index_value_read_authorized",
        "representative_index_preflight_authorized",
    ):
        if current.get(field) is not True:
            raise RuntimeError(f"{field} must be true after activation")
    for field in (
        "full_historical_reconstruction_authorized",
        "candidate_score_computation_authorized",
        "research_ledger_mutation_authorized",
        "public_artifact_replacement_authorized",
        "production_authorized",
    ):
        if current.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if ("if: $" + "{{ false }}") not in workflow:
        raise RuntimeError("workflow must remain inert until dispatch")
    if "push:" in workflow:
        raise RuntimeError("activation-only workflow must not have a push trigger")

    return {
        "status": "passed",
        "state": "representative_index_preflight_authorized_pending_dispatch",
        "issue": ISSUE,
        "request_budget": 2,
        "max_observations_total": 2,
        "max_observations_per_resource": 1,
        "active_receipt_present": True,
        "dispatch_present": False,
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
