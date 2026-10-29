#!/usr/bin/env python3
"""Validate Issue #258 design-v4 authorization pending separate dispatch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
APPROVAL_COMMENT = 6483993388
APPROVED_AT = "2026-10-29T00:03:08Z"
DESIGN = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json"
TEMPLATE = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json"
RECEIPT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
DISPATCH = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
CONTRACT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json"
WORKFLOW = ROOT / ".github/workflows/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight.yml"
PRIOR_CONSUMPTION = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-consumption-2026-10-29.json"
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
    receipt = _load(root / RECEIPT.relative_to(ROOT))
    contract = _load(root / CONTRACT.relative_to(ROOT))
    prior = _load(root / PRIOR_CONSUMPTION.relative_to(ROOT))
    rights = _load(root / "governance/score-publication-rights-gate.json")
    workflow = (root / WORKFLOW.relative_to(ROOT)).read_text(encoding="utf-8")

    if (root / DISPATCH.relative_to(ROOT)).exists():
        raise RuntimeError("dispatch must remain absent before separate review")
    if rights.get("state") != "hold":
        raise RuntimeError("Issue #155 rights gate must remain HOLD")
    if prior.get("state") != "consumed_after_completed_diagnostics":
        raise RuntimeError("prior Issue #258 consumption evidence changed")

    if design.get("version") != 4 or design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 design v4 changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("Issue #258 design issue changed")
    if [item.get("path") for item in design.get("fixed_resources", [])] != EXPECTED_RESOURCES:
        raise RuntimeError("fixed resources changed")
    if design.get("future_live_budget", {}).get("request_budget") != 2:
        raise RuntimeError("request budget changed")
    if design.get("future_live_budget", {}).get("max_economic_observations_total") != 0:
        raise RuntimeError("economic observation budget changed")
    header_compat = design.get("header_compatibility_policy", {})
    if header_compat.get("standalone_code_token_role") != "identifier":
        raise RuntimeError("standalone Code compatibility changed")
    if header_compat.get("mixed_index_code_role") != "ambiguous":
        raise RuntimeError("Index code must remain ambiguous")
    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("frozen design authorization flags must remain false")

    if template.get("decision_status") != "hold" or any(template.get("authorizations", {}).values()):
        raise RuntimeError("authorization template must remain HOLD")

    if receipt.get("decision_status") != "approved":
        raise RuntimeError("active receipt must be approved")
    if receipt.get("issue") != ISSUE:
        raise RuntimeError("receipt issue changed")
    if receipt.get("request_budget") != 2:
        raise RuntimeError("receipt request budget changed")
    if receipt.get("max_economic_observations_total") != 0:
        raise RuntimeError("receipt economic observation budget changed")
    if receipt.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("receipt resources changed")
    if receipt.get("approved_by") != "usdimpact owner via Issue #258 approval comment 6483993388":
        raise RuntimeError("approval evidence changed")
    if receipt.get("approved_at") != APPROVED_AT:
        raise RuntimeError("approval timestamp changed")
    auth = receipt.get("authorizations", {})
    for field in ("response_body_ephemeral_retrieval","ambiguity_diagnostics_preflight","numeric_identifier_field_read"):
        if auth.get(field) is not True:
            raise RuntimeError(f"{field} must be active")
    for field in ("economic_value_read","full_historical_reconstruction","candidate_score_computation","research_ledger_mutation","public_artifact_replacement","production"):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if contract.get("version") != 6:
        raise RuntimeError("activation contract version changed")
    if contract.get("state") != "ambiguity_diagnostics_v4_recheck_authorized_pending_dispatch":
        raise RuntimeError("contract must remain pending dispatch")
    if contract.get("owner_approval_comment_id") != APPROVAL_COMMENT:
        raise RuntimeError("contract approval comment changed")
    if contract.get("owner_approval_timestamp") != APPROVED_AT:
        raise RuntimeError("contract approval time changed")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("active receipt must be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch must not yet be expected")
    current = contract.get("current_state", {})
    for field in ("response_body_ephemeral_retrieval_authorized","ambiguity_diagnostics_preflight_authorized","numeric_identifier_field_read_authorized"):
        if current.get(field) is not True:
            raise RuntimeError(f"{field} must be true")
    for field in ("economic_value_read_authorized","full_historical_reconstruction_authorized","candidate_score_computation_authorized","research_ledger_mutation_authorized","public_artifact_replacement_authorized","production_authorized"):
        if current.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if ("if: $" + "{{ false }}") not in workflow:
        raise RuntimeError("activation workflow must remain inert")
    if "push:" in workflow:
        raise RuntimeError("activation workflow must not have a push trigger")

    return {
        "status": "passed",
        "state": "ambiguity_diagnostics_v4_recheck_authorized_pending_dispatch",
        "design_version": 4,
        "active_receipt_present": True,
        "dispatch_present": False,
        "live_request_authorized": False,
        "max_economic_observations_total": 0,
        "production_authorized": False,
        "rights_hold": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
