#!/usr/bin/env python3
"""Validate activated-but-not-dispatched Issue #258 design-v8 header-band inventory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
V7_RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40897338145"
APPROVAL_COMMENT = 6500606721
APPROVED_AT = "2026-10-29T15:15:37Z"
EXPECTED_UA = "USD-Impact-Score-v2.1F-WPU0561-container-header-band/1.0 (contact: support@usd-impact.com)"
EXPECTED_RESOURCES = [
    "/news.release/archives/ppi_05152013.htm",
    "/ppi/detailed-report/ppi-detailed-report-april-2026.xlsx",
]
DESIGN = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json"
TEMPLATE = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json"
RECEIPT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
DISPATCH = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
CONTRACT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json"
CONSUMPTION = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-v7-header-gap-consumption-2026-10-29.json"
WORKFLOW = ROOT / ".github/workflows/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight.yml"


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
    consumption = _load(root / CONSUMPTION.relative_to(ROOT))
    rights = _load(root / "governance/score-publication-rights-gate.json")
    workflow = (root / WORKFLOW.relative_to(ROOT)).read_text(encoding="utf-8")

    if not receipt_path.exists():
        raise RuntimeError("active v8 receipt must exist after activation")
    if dispatch_path.exists():
        raise RuntimeError("dispatch must remain absent before separate review")
    receipt = _load(receipt_path)

    if rights.get("state") != "hold":
        raise RuntimeError("Issue #155 rights gate must remain HOLD")
    if template.get("decision_status") != "hold" or any(template.get("authorizations", {}).values()):
        raise RuntimeError("authorization template must remain HOLD")

    if consumption.get("state") != "consumed_after_completed_v7_header_gap_inventory":
        raise RuntimeError("v7 consumption evidence changed")
    if consumption.get("preflight_run") != V7_RUN:
        raise RuntimeError("v7 run evidence changed")
    prior = consumption.get("sanitized_result", {})
    if prior.get("request_attempt_count") != 2:
        raise RuntimeError("v7 request count changed")
    if prior.get("identifier_values_retained") is not False:
        raise RuntimeError("v7 identifier safeguard changed")
    if prior.get("economic_values_retained") is not False:
        raise RuntimeError("v7 economic safeguard changed")

    if design.get("version") != 8 or design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 v8 design changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("Issue #258 design issue changed")
    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("frozen v8 design authorization flags must remain false")

    policy = design.get("container_header_band_policy", {})
    if policy.get("state") != "design_only_not_live_authorized":
        raise RuntimeError("v8 header-band policy changed")
    if policy.get("candidate_row_as_selector") is not False:
        raise RuntimeError("candidate row must not be a selector")
    if policy.get("inspect_top_rows") != 32:
        raise RuntimeError("v8 top-row bound changed")
    if policy.get("maximum_persisted_text_cells_per_selected_container") != 128:
        raise RuntimeError("v8 cell bound changed")
    if policy.get("identifier_values") != "forbidden":
        raise RuntimeError("v8 identifier policy changed")
    if policy.get("economic_values") != "forbidden":
        raise RuntimeError("v8 economic policy changed")
    if policy.get("response_body_persistence") is not False:
        raise RuntimeError("v8 response-body persistence changed")

    if receipt.get("decision_status") != "approved":
        raise RuntimeError("active v8 receipt must be approved")
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
    if receipt.get("approved_by") != "usdimpact owner via Issue #258 approval comment 6500606721":
        raise RuntimeError("receipt approval identity changed")
    if receipt.get("approved_at") != APPROVED_AT:
        raise RuntimeError("receipt approval timestamp changed")

    auth = receipt.get("authorizations", {})
    if auth.get("response_body_ephemeral_retrieval") is not True:
        raise RuntimeError("ephemeral retrieval must be authorized")
    if auth.get("ambiguity_diagnostics_preflight") is not True:
        raise RuntimeError("header-band preflight must be authorized")
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

    if contract.get("version") != 18:
        raise RuntimeError("v8 activation contract version changed")
    if contract.get("state") != "ambiguity_diagnostics_v8_container_header_band_authorized_pending_dispatch":
        raise RuntimeError("contract must be active but pending dispatch")
    if contract.get("owner_approval_comment_id") != APPROVAL_COMMENT:
        raise RuntimeError("contract approval comment changed")
    if contract.get("owner_approval_timestamp") != APPROVED_AT:
        raise RuntimeError("contract approval timestamp changed")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("active receipt must be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch must remain absent")
    current = contract.get("current_state", {})
    if current.get("response_body_ephemeral_retrieval_authorized") is not True:
        raise RuntimeError("ephemeral retrieval must be active")
    if current.get("ambiguity_diagnostics_preflight_authorized") is not True:
        raise RuntimeError("header-band preflight must be active")
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
        "state": "ambiguity_diagnostics_v8_container_header_band_authorized_pending_dispatch",
        "design_version": 8,
        "request_budget": 2,
        "max_economic_observations_total": 0,
        "v8_header_band_top_rows": 32,
        "v8_header_band_max_cells": 128,
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
