#!/usr/bin/env python3
"""Validate activated-but-not-dispatched Issue #258 design-v5 candidate-context inventory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
V4_RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40792259680"
DESIGN = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json"
TEMPLATE = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json"
RECEIPT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
DISPATCH = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
CONTRACT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json"
V4_CONSUMPTION = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-v4-recheck-consumption-2026-10-29.json"
WORKFLOW = ROOT / ".github/workflows/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight.yml"
APPROVAL_COMMENT = 6484353947
APPROVED_AT = "2026-10-29T00:24:35Z"
EXPECTED_UA = "USD-Impact-Score-v2.1F-WPU0561-candidate-context/1.0 (contact: support@usd-impact.com)"
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
    v4 = _load(root / V4_CONSUMPTION.relative_to(ROOT))
    rights = _load(root / "governance/score-publication-rights-gate.json")
    workflow = (root / WORKFLOW.relative_to(ROOT)).read_text(encoding="utf-8")

    if not receipt_path.exists():
        raise RuntimeError("active v5 receipt must exist after activation")
    if dispatch_path.exists():
        raise RuntimeError("dispatch must remain absent before separate review")
    receipt = _load(receipt_path)

    if rights.get("state") != "hold":
        raise RuntimeError("Issue #155 rights gate must remain HOLD")
    if template.get("decision_status") != "hold" or any(template.get("authorizations", {}).values()):
        raise RuntimeError("authorization template must remain HOLD")

    if v4.get("state") != "consumed_after_completed_v4_recheck":
        raise RuntimeError("v4 recheck consumption evidence changed")
    if v4.get("preflight_run") != V4_RUN:
        raise RuntimeError("v4 run evidence changed")
    v4_result = v4.get("sanitized_result", {})
    if v4_result.get("standalone_code_compatibility_resolved_anchor_failure") is not False:
        raise RuntimeError("v4 live outcome changed")
    for resource in ("html", "xlsx"):
        if v4_result.get(resource, {}).get("reason_summary") != {"no_local_header_anchor": 1}:
            raise RuntimeError(f"v4 {resource} reason changed")

    if design.get("version") != 5 or design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 v5 design changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("Issue #258 design issue changed")
    if design.get("future_live_budget", {}).get("request_budget") != 2:
        raise RuntimeError("request budget changed")
    if design.get("future_live_budget", {}).get("max_economic_observations_total") != 0:
        raise RuntimeError("economic observation budget changed")
    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("frozen v5 design authorization flags must remain false")

    inventory = design.get("candidate_context_inventory_policy", {})
    expected_inventory = {
        "state": "design_only_not_authorized",
        "maximum_candidates_per_resource": 32,
        "preceding_rows_per_candidate": 8,
        "following_rows_per_candidate": 0,
        "maximum_persisted_text_cells_per_candidate": 64,
        "identifier_values": "forbidden; this diagnostic does not read or persist identifier values",
        "economic_values": "forbidden",
        "response_body_persistence": False,
        "live_verification_status": "not_yet_authorized",
    }
    for key, value in expected_inventory.items():
        if inventory.get(key) != value:
            raise RuntimeError(f"candidate context policy changed: {key}")
    if "<num>" not in inventory.get("numeric_token_policy", ""):
        raise RuntimeError("numeric-token redaction changed")
    if "<alnum-redacted>" not in inventory.get("alphanumeric_numeric_token_policy", ""):
        raise RuntimeError("alphanumeric-token redaction changed")

    if receipt.get("decision_status") != "approved":
        raise RuntimeError("active v5 receipt must be approved")
    if receipt.get("issue") != ISSUE:
        raise RuntimeError("receipt issue changed")
    if receipt.get("execution_scope") != "bls_wpu0561_ambiguity_diagnostics_preflight_only":
        raise RuntimeError("receipt scope changed")
    if receipt.get("request_budget") != 2:
        raise RuntimeError("receipt request budget changed")
    if receipt.get("max_economic_observations_total") != 0:
        raise RuntimeError("receipt economic observation budget changed")
    if receipt.get("max_economic_observations_per_resource") != 0:
        raise RuntimeError("receipt per-resource observation budget changed")
    if receipt.get("allowed_host") != "www.bls.gov":
        raise RuntimeError("receipt host changed")
    if receipt.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("receipt resources changed")
    if receipt.get("contact_user_agent") != EXPECTED_UA:
        raise RuntimeError("receipt User-Agent changed")
    if receipt.get("approved_by") != "usdimpact owner via Issue #258 approval comment 6484353947":
        raise RuntimeError("receipt approval identity changed")
    if receipt.get("approved_at") != APPROVED_AT:
        raise RuntimeError("receipt approval timestamp changed")

    auth = receipt.get("authorizations", {})
    if auth.get("response_body_ephemeral_retrieval") is not True:
        raise RuntimeError("ephemeral retrieval must be authorized")
    if auth.get("ambiguity_diagnostics_preflight") is not True:
        raise RuntimeError("candidate-context preflight must be authorized")
    for field in (
        "numeric_identifier_field_read",
        "economic_value_read",
        "full_historical_reconstruction",
        "candidate_score_computation",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if contract.get("version") != 9:
        raise RuntimeError("activation contract version changed")
    if contract.get("state") != "ambiguity_diagnostics_v5_candidate_context_authorized_pending_dispatch":
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
    if current.get("response_body_ephemeral_retrieval_authorized") is not True:
        raise RuntimeError("ephemeral retrieval must be active")
    if current.get("ambiguity_diagnostics_preflight_authorized") is not True:
        raise RuntimeError("candidate-context preflight must be active")
    for field in (
        "numeric_identifier_field_read_authorized",
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
        "state": "ambiguity_diagnostics_v5_candidate_context_authorized_pending_dispatch",
        "design_version": 5,
        "request_budget": 2,
        "max_economic_observations_total": 0,
        "max_candidates_per_resource": 32,
        "preceding_rows_per_candidate": 8,
        "max_cells_per_candidate": 64,
        "active_receipt_present": True,
        "dispatch_present": False,
        "live_request_authorized": False,
        "identifier_value_read_authorized": False,
        "economic_value_read_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
