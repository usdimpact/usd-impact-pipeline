#!/usr/bin/env python3
"""Validate activated-but-not-dispatched Issue #258 ambiguity diagnostics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json"
TEMPLATE = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json"
RECEIPT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
DISPATCH = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
CONTRACT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json"
WORKFLOW = ROOT / ".github/workflows/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight.yml"
PREDECESSOR = ROOT / "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-consumption-2026-10-29.json"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
APPROVAL_COMMENT = 6483711604
APPROVED_AT = "2026-10-28T23:46:03Z"
EXPECTED_UA = "USD-Impact-Score-v2.1F-WPU0561-ambiguity-diagnostics/1.0 (contact: support@usd-impact.com)"
EXPECTED_RESOURCES = [
    "/news.release/archives/ppi_05152013.htm",
    "/ppi/detailed-report/ppi-detailed-report-april-2026.xlsx",
]


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path | None = None) -> dict[str, Any]:
    root = (repo_root or ROOT).resolve()
    design = _load(root / DESIGN.relative_to(ROOT))
    template = _load(root / TEMPLATE.relative_to(ROOT))
    receipt_path = root / RECEIPT.relative_to(ROOT)
    dispatch_path = root / DISPATCH.relative_to(ROOT)
    contract = _load(root / CONTRACT.relative_to(ROOT))
    predecessor = _load(root / PREDECESSOR.relative_to(ROOT))
    rights = _load(root / "governance/score-publication-rights-gate.json")
    prereg = _load(root / "governance/score-v2-1f-preregistration.json")
    workflow = (root / WORKFLOW.relative_to(ROOT)).read_text(encoding="utf-8")

    if not receipt_path.exists():
        raise RuntimeError("active Issue #258 receipt must exist after activation")
    if dispatch_path.exists():
        raise RuntimeError("dispatch must remain absent before separate review")
    receipt = _load(receipt_path)

    if predecessor.get("state") != "consumed_after_ambiguous_result":
        raise RuntimeError("Issue #252 consumption evidence changed")
    prior_result = predecessor.get("sanitized_result", {})
    if prior_result.get("request_count") != 2 or prior_result.get("observation_count") != 0:
        raise RuntimeError("Issue #252 sanitized evidence changed")
    if rights.get("state") != "hold":
        raise RuntimeError("Score publication rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")

    if design.get("version") != 3 or design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 frozen design changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("Issue #258 design issue changed")
    if [item.get("path") for item in design.get("fixed_resources", [])] != EXPECTED_RESOURCES:
        raise RuntimeError("Issue #258 fixed resources changed")
    if design.get("future_live_budget", {}).get("request_budget") != 2:
        raise RuntimeError("Issue #258 request budget changed")
    if design.get("future_live_budget", {}).get("max_economic_observations_total") != 0:
        raise RuntimeError("economic observation budget must remain zero")
    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("frozen design authorizations must remain false")
    execution = design.get("execution_environment_policy", {})
    if execution.get("preferred_environment") != "github_actions_protected_main_lifecycle":
        raise RuntimeError("protected GitHub Actions must remain preferred")
    if execution.get("activation_audit_write_required_before_live_request") is not True:
        raise RuntimeError("activation audit write requirement changed")
    if execution.get("dispatch_audit_write_required_before_live_request") is not True:
        raise RuntimeError("dispatch audit write requirement changed")
    if execution.get("direct_local_execution_under_standard_issue_258_authorization") is not False:
        raise RuntimeError("direct local fallback must remain forbidden")

    if template.get("decision_status") != "hold":
        raise RuntimeError("authorization template must remain HOLD")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("authorization template flags must remain false")

    if receipt.get("decision_status") != "approved":
        raise RuntimeError("active receipt must be approved")
    if receipt.get("issue") != ISSUE:
        raise RuntimeError("active receipt issue changed")
    if receipt.get("execution_scope") != "bls_wpu0561_ambiguity_diagnostics_preflight_only":
        raise RuntimeError("active receipt scope changed")
    if receipt.get("request_budget") != 2:
        raise RuntimeError("active receipt request budget changed")
    if receipt.get("max_economic_observations_total") != 0:
        raise RuntimeError("active receipt economic observation budget changed")
    if receipt.get("max_economic_observations_per_resource") != 0:
        raise RuntimeError("active receipt per-resource observation budget changed")
    if receipt.get("allowed_host") != "www.bls.gov":
        raise RuntimeError("active receipt host changed")
    if receipt.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("active receipt resources changed")
    if receipt.get("contact_user_agent") != EXPECTED_UA:
        raise RuntimeError("active receipt User-Agent changed")
    if receipt.get("approved_by") != "usdimpact owner via Issue #258 approval comment 6483711604":
        raise RuntimeError("active receipt approval identity changed")
    if receipt.get("approved_at") != APPROVED_AT:
        raise RuntimeError("active receipt approval timestamp changed")

    auth = receipt.get("authorizations", {})
    for field in (
        "response_body_ephemeral_retrieval",
        "ambiguity_diagnostics_preflight",
        "numeric_identifier_field_read",
    ):
        if auth.get(field) is not True:
            raise RuntimeError(f"{field} must be authorized")
    for field in (
        "economic_value_read",
        "full_historical_reconstruction",
        "candidate_score_computation",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if contract.get("version") != 3:
        raise RuntimeError("activation contract version changed")
    if contract.get("state") != "ambiguity_diagnostics_authorized_pending_dispatch":
        raise RuntimeError("contract must be active but pending dispatch")
    if contract.get("owner_approval_comment_id") != APPROVAL_COMMENT:
        raise RuntimeError("contract approval comment changed")
    if contract.get("owner_approval_timestamp") != APPROVED_AT:
        raise RuntimeError("contract approval timestamp changed")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("active receipt must be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch must remain absent")
    if contract.get("request_budget") != 2 or contract.get("max_economic_observations_total") != 0:
        raise RuntimeError("contract budgets changed")

    current = contract.get("current_state", {})
    for field in (
        "response_body_ephemeral_retrieval_authorized",
        "ambiguity_diagnostics_preflight_authorized",
        "numeric_identifier_field_read_authorized",
    ):
        if current.get(field) is not True:
            raise RuntimeError(f"{field} must be true after activation")
    for field in (
        "economic_value_read_authorized",
        "full_historical_reconstruction_authorized",
        "candidate_score_computation_authorized",
        "research_ledger_mutation_authorized",
        "public_artifact_replacement_authorized",
        "production_authorized",
    ):
        if current.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if ("if: $" + "{{ false }}") not in workflow:
        raise RuntimeError("activation workflow must remain inert")
    if "push:" in workflow:
        raise RuntimeError("activation workflow must not have a push trigger")

    return {
        "status": "passed",
        "state": "ambiguity_diagnostics_authorized_pending_dispatch",
        "issue": ISSUE,
        "request_budget": 2,
        "max_economic_observations_total": 0,
        "active_receipt_present": True,
        "dispatch_present": False,
        "live_request_authorized": False,
        "economic_value_read_authorized": False,
        "candidate_score_computation_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


def main() -> int:
    print(json.dumps(validate(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
