#!/usr/bin/env python3
"""Validate dispatched Issue #258 design-v4 ambiguity recheck."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
APPROVAL_COMMENT = 6483993388
APPROVED_AT = "2026-10-29T00:03:08Z"
ACTIVATION_COMMIT = "b312fa34e6c579294a21d2deadfc1154ef117e27"
DESIGN = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json"
TEMPLATE = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json"
RECEIPT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
DISPATCH = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
CONTRACT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json"
WORKFLOW = ROOT / ".github/workflows/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight.yml"
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
    dispatch = _load(root / DISPATCH.relative_to(ROOT))
    contract = _load(root / CONTRACT.relative_to(ROOT))
    rights = _load(root / "governance/score-publication-rights-gate.json")
    workflow = (root / WORKFLOW.relative_to(ROOT)).read_text(encoding="utf-8")

    if rights.get("state") != "hold":
        raise RuntimeError("Issue #155 rights gate must remain HOLD")
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
        raise RuntimeError("receipt must be approved")
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
        raise RuntimeError("approval time changed")
    auth = receipt.get("authorizations", {})
    for field in ("response_body_ephemeral_retrieval","ambiguity_diagnostics_preflight","numeric_identifier_field_read"):
        if auth.get(field) is not True:
            raise RuntimeError(f"{field} must be true")
    for field in ("economic_value_read","full_historical_reconstruction","candidate_score_computation","research_ledger_mutation","public_artifact_replacement","production"):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if dispatch.get("state") != "approved_dispatch":
        raise RuntimeError("dispatch state changed")
    if dispatch.get("phase") != "bls_wpu0561_ambiguity_diagnostics_preflight":
        raise RuntimeError("dispatch phase changed")
    if dispatch.get("design_version") != 4:
        raise RuntimeError("dispatch design version changed")
    if dispatch.get("authorization_activation_merge_commit") != ACTIVATION_COMMIT:
        raise RuntimeError("dispatch activation commit changed")
    if dispatch.get("request_budget") != 2:
        raise RuntimeError("dispatch request budget changed")
    if dispatch.get("max_economic_observations_total") != 0:
        raise RuntimeError("dispatch economic observation budget changed")
    if dispatch.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("dispatch resources changed")
    if dispatch.get("production_authorized") is not False:
        raise RuntimeError("dispatch Production authorization changed")

    if contract.get("version") != 7:
        raise RuntimeError("dispatch contract version changed")
    if contract.get("state") != "ambiguity_diagnostics_v4_recheck_authorized":
        raise RuntimeError("contract must be dispatched-active")
    if contract.get("owner_approval_comment_id") != APPROVAL_COMMENT:
        raise RuntimeError("contract approval comment changed")
    if contract.get("owner_approval_timestamp") != APPROVED_AT:
        raise RuntimeError("contract approval time changed")
    if contract.get("authorization_activation_merge_commit") != ACTIVATION_COMMIT:
        raise RuntimeError("contract activation commit changed")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("active receipt must be expected")
    if contract.get("dispatch_marker_expected_now") is not True:
        raise RuntimeError("dispatch marker must be expected")
    current = contract.get("current_state", {})
    for field in ("response_body_ephemeral_retrieval_authorized","ambiguity_diagnostics_preflight_authorized","numeric_identifier_field_read_authorized"):
        if current.get(field) is not True:
            raise RuntimeError(f"{field} must be true")
    for field in ("economic_value_read_authorized","full_historical_reconstruction_authorized","candidate_score_computation_authorized","research_ledger_mutation_authorized","public_artifact_replacement_authorized","production_authorized"):
        if current.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if "score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json" not in workflow:
        raise RuntimeError("workflow must be path-gated to dispatch")
    if ("if: $" + "{{ false }}") in workflow:
        raise RuntimeError("workflow must be active in dispatched state")
    if "workflow_dispatch:" in workflow:
        raise RuntimeError("dispatched workflow must not allow manual reruns")

    return {
        "status": "passed",
        "state": "ambiguity_diagnostics_v4_recheck_authorized",
        "design_version": 4,
        "activation_merge_commit": ACTIVATION_COMMIT,
        "active_receipt_present": True,
        "dispatch_present": True,
        "live_request_authorized": True,
        "max_economic_observations_total": 0,
        "production_authorized": False,
        "rights_hold": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
