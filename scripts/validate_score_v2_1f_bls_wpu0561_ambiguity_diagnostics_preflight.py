#!/usr/bin/env python3
"""Validate dispatched Issue #258 design-v7 header-gap inventory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
V5_RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40794631448"
DESIGN = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json"
TEMPLATE = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json"
RECEIPT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
DISPATCH = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
CONTRACT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json"
CONSUMPTION = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-v5-candidate-context-consumption-2026-10-29.json"
WORKFLOW = ROOT / ".github/workflows/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight.yml"
APPROVAL_COMMENT = 6500046079
APPROVED_AT = "2026-10-29T14:53:20Z"
EXPECTED_UA = "USD-Impact-Score-v2.1F-WPU0561-header-gap/1.0 (contact: support@usd-impact.com)"
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
    consumption = _load(root / CONSUMPTION.relative_to(ROOT))
    rights = _load(root / "governance/score-publication-rights-gate.json")
    workflow = (root / WORKFLOW.relative_to(ROOT)).read_text(encoding="utf-8")

    if not receipt_path.exists():
        raise RuntimeError("active v7 receipt must exist while dispatched")
    if not dispatch_path.exists():
        raise RuntimeError("v7 dispatch marker must exist while dispatched")
    receipt = _load(receipt_path)
    dispatch = _load(dispatch_path)

    if rights.get("state") != "hold":
        raise RuntimeError("Issue #155 rights gate must remain HOLD")
    if template.get("decision_status") != "hold" or any(template.get("authorizations", {}).values()):
        raise RuntimeError("authorization template must remain HOLD")

    if consumption.get("state") != "consumed_after_completed_v5_candidate_context_inventory":
        raise RuntimeError("v5 consumption evidence changed")
    if consumption.get("preflight_run") != V5_RUN:
        raise RuntimeError("v5 run evidence changed")
    if consumption.get("sanitized_result", {}).get("economic_observation_count") != 0:
        raise RuntimeError("v5 economic observation evidence changed")
    if consumption.get("sanitized_result", {}).get("identifier_value_count") != 0:
        raise RuntimeError("v5 identifier evidence changed")

    if design.get("version") != 7 or design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 v7 design changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("Issue #258 design issue changed")
    if design.get("future_live_budget", {}).get("request_budget") != 2:
        raise RuntimeError("request budget changed")
    if design.get("future_live_budget", {}).get("max_economic_observations_total") != 0:
        raise RuntimeError("economic observation budget changed")
    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("frozen v7 design authorization flags must remain false")

    exact = design.get("exact_label_candidate_policy", {})
    discriminator = design.get("xlsx_context_discriminator_policy", {})
    gap = design.get("candidate_local_header_gap_policy", {})
    if exact.get("expected_html_narrowing") != "3 -> 1":
        raise RuntimeError("v6 HTML prerequisite changed")
    if exact.get("expected_xlsx_narrowing") != "29 -> 2":
        raise RuntimeError("v6 XLSX prerequisite changed")
    if exact.get("row_number_as_selector") is not False:
        raise RuntimeError("row numbers must not be selectors")
    if discriminator.get("expected_direct_commodity_survivors") != 1:
        raise RuntimeError("direct-commodity prerequisite changed")
    if discriminator.get("row_number_as_selector") is not False:
        raise RuntimeError("XLSX row numbers must not be selectors")
    if gap.get("state") != "design_only_not_live_authorized":
        raise RuntimeError("v7 header-gap design state changed")
    if gap.get("maximum_preceding_rows") != 32:
        raise RuntimeError("v7 row bound changed")
    if gap.get("following_rows") != 0:
        raise RuntimeError("v7 following-row bound changed")
    if gap.get("maximum_persisted_text_cells_per_selected_candidate") != 128:
        raise RuntimeError("v7 cell bound changed")
    if gap.get("row_number_as_selector") is not False:
        raise RuntimeError("v7 row numbers must remain coordinates only")
    if gap.get("identifier_values") != "forbidden":
        raise RuntimeError("identifier-value policy changed")
    if gap.get("economic_values") != "forbidden":
        raise RuntimeError("economic-value policy changed")

    if receipt.get("decision_status") != "approved":
        raise RuntimeError("active v7 receipt must be approved")
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
    if receipt.get("approved_by") != "usdimpact owner via Issue #258 approval comment 6500046079":
        raise RuntimeError("receipt approval identity changed")
    if receipt.get("approved_at") != APPROVED_AT:
        raise RuntimeError("receipt approval timestamp changed")

    auth = receipt.get("authorizations", {})
    if auth.get("response_body_ephemeral_retrieval") is not True:
        raise RuntimeError("ephemeral retrieval must be authorized")
    if auth.get("ambiguity_diagnostics_preflight") is not True:
        raise RuntimeError("header-gap preflight must be authorized")
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

    if dispatch.get("state") != "approved_dispatch":
        raise RuntimeError("dispatch state changed")
    if dispatch.get("phase") != "bls_wpu0561_candidate_local_header_gap_inventory_preflight":
        raise RuntimeError("dispatch phase changed")
    if dispatch.get("issue") != ISSUE:
        raise RuntimeError("dispatch issue changed")
    if dispatch.get("design_version") != 7:
        raise RuntimeError("dispatch design version changed")
    if dispatch.get("authorization_activation_merge_commit") != "771bf87d381fda9f72adad5f5456331916195533":
        raise RuntimeError("dispatch activation commit changed")
    if dispatch.get("request_budget") != 2 or dispatch.get("max_economic_observations_total") != 0:
        raise RuntimeError("dispatch budgets changed")
    if dispatch.get("maximum_preceding_rows") != 32:
        raise RuntimeError("dispatch row bound changed")
    if dispatch.get("following_rows") != 0:
        raise RuntimeError("dispatch following-row bound changed")
    if dispatch.get("maximum_persisted_text_cells_per_selected_candidate") != 128:
        raise RuntimeError("dispatch cell bound changed")
    if dispatch.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("dispatch resources changed")
    if dispatch.get("identifier_value_read_authorized") is not False:
        raise RuntimeError("identifier-value reads must remain forbidden")
    if dispatch.get("economic_value_read_authorized") is not False:
        raise RuntimeError("economic-value reads must remain forbidden")
    if dispatch.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if contract.get("version") != 15:
        raise RuntimeError("dispatch contract version changed")
    if contract.get("state") != "ambiguity_diagnostics_v7_header_gap_authorized":
        raise RuntimeError("contract must be dispatched-active")
    if contract.get("owner_approval_comment_id") != APPROVAL_COMMENT:
        raise RuntimeError("contract approval comment changed")
    if contract.get("owner_approval_timestamp") != APPROVED_AT:
        raise RuntimeError("contract approval timestamp changed")
    if contract.get("authorization_activation_merge_commit") != "771bf87d381fda9f72adad5f5456331916195533":
        raise RuntimeError("contract activation commit changed")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("active receipt must be expected")
    if contract.get("dispatch_marker_expected_now") is not True:
        raise RuntimeError("dispatch marker must be expected")
    if contract.get("request_budget") != 2 or contract.get("max_economic_observations_total") != 0:
        raise RuntimeError("contract budgets changed")

    current = contract.get("current_state", {})
    if current.get("response_body_ephemeral_retrieval_authorized") is not True:
        raise RuntimeError("ephemeral retrieval must be active")
    if current.get("ambiguity_diagnostics_preflight_authorized") is not True:
        raise RuntimeError("header-gap preflight must be active")
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

    if "score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json" not in workflow:
        raise RuntimeError("workflow must be path-gated to the dispatch marker")
    if ("if: $" + "{{ false }}") in workflow:
        raise RuntimeError("workflow must be active in dispatched state")
    if "workflow_dispatch:" in workflow:
        raise RuntimeError("dispatched workflow must not allow manual reruns")

    return {
        "status": "passed",
        "state": "ambiguity_diagnostics_v7_header_gap_authorized",
        "design_version": 7,
        "request_budget": 2,
        "max_economic_observations_total": 0,
        "max_preceding_rows": 32,
        "max_cells_per_selected_candidate": 128,
        "active_receipt_present": True,
        "dispatch_present": True,
        "live_request_authorized": True,
        "identifier_value_read_authorized": False,
        "economic_value_read_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
