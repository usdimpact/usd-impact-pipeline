#!/usr/bin/env python3
"""Validate consumed/fail-closed Issue #258 design-v7 header-gap state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40897338145"
ACTIVATION_COMMIT = "771bf87d381fda9f72adad5f5456331916195533"
DISPATCH_COMMIT = "549f0fe9019f884980a6aa6f5d7d849ca4bf137d"
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
    contract = _load(root / CONTRACT.relative_to(ROOT))
    consumption = _load(root / CONSUMPTION.relative_to(ROOT))
    rights = _load(root / "governance/score-publication-rights-gate.json")
    workflow = (root / WORKFLOW.relative_to(ROOT)).read_text(encoding="utf-8")

    for relative in (RECEIPT.relative_to(ROOT), DISPATCH.relative_to(ROOT)):
        if (root / relative).exists():
            raise RuntimeError(f"consumed v7 state must not retain {relative}")

    if rights.get("state") != "hold":
        raise RuntimeError("Issue #155 rights gate must remain HOLD")
    if template.get("decision_status") != "hold" or any(template.get("authorizations", {}).values()):
        raise RuntimeError("authorization template must remain HOLD")

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

    gap = design.get("candidate_local_header_gap_policy", {})
    if gap.get("maximum_preceding_rows") != 32:
        raise RuntimeError("v7 row bound changed")
    if gap.get("following_rows") != 0:
        raise RuntimeError("v7 following-row bound changed")
    if gap.get("maximum_persisted_text_cells_per_selected_candidate") != 128:
        raise RuntimeError("v7 cell bound changed")
    if gap.get("row_number_as_selector") is not False:
        raise RuntimeError("v7 row-number policy changed")
    if gap.get("identifier_values") != "forbidden":
        raise RuntimeError("v7 identifier-value policy changed")
    if gap.get("economic_values") != "forbidden":
        raise RuntimeError("v7 economic-value policy changed")

    if consumption.get("state") != "consumed_after_completed_v7_header_gap_inventory":
        raise RuntimeError("v7 consumption state changed")
    if consumption.get("design_version") != 7:
        raise RuntimeError("v7 consumption design version changed")
    if consumption.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("consumption issue changed")
    if consumption.get("owner_approval_comment_id") != 6500046079:
        raise RuntimeError("owner approval evidence changed")
    if consumption.get("authorization_activation_merge_commit") != ACTIVATION_COMMIT:
        raise RuntimeError("activation merge evidence changed")
    if consumption.get("dispatch_merge_commit") != DISPATCH_COMMIT:
        raise RuntimeError("dispatch merge evidence changed")
    if consumption.get("preflight_run") != RUN:
        raise RuntimeError("preflight run evidence changed")
    if consumption.get("preflight_workflow_conclusion") != "success":
        raise RuntimeError("workflow conclusion changed")
    if consumption.get("preflight_result_status") != "completed":
        raise RuntimeError("result status changed")
    if consumption.get("request_budget") != 2:
        raise RuntimeError("consumption request budget changed")
    if consumption.get("max_economic_observations_total") != 0:
        raise RuntimeError("consumption economic observation budget changed")

    result = consumption.get("sanitized_result", {})
    if result.get("request_attempt_count") != 2:
        raise RuntimeError("request attempt count changed")
    if result.get("identifier_values_retained") is not False:
        raise RuntimeError("identifier values must remain absent")
    if result.get("economic_values_retained") is not False:
        raise RuntimeError("economic values must remain absent")

    html = result.get("html", {})
    xlsx = result.get("xlsx", {})
    if html.get("transport_status") != "passed" or html.get("semantic_status") != "evaluated":
        raise RuntimeError("HTML transport/semantic evidence changed")
    if html.get("container") != "table 4" or html.get("candidate_row") != 226:
        raise RuntimeError("HTML selected candidate evidence changed")
    if html.get("window_start_row") != 194 or html.get("window_end_row") != 225:
        raise RuntimeError("HTML header-gap window changed")
    if html.get("nearest_recognized_header_row") is not None:
        raise RuntimeError("HTML nearest-header result changed")
    if html.get("recognized_header_role_rows") != []:
        raise RuntimeError("HTML recognized-header rows changed")
    if html.get("truncated") is not False:
        raise RuntimeError("HTML result must remain untruncated")

    if xlsx.get("transport_status") != "passed" or xlsx.get("semantic_status") != "evaluated":
        raise RuntimeError("XLSX transport/semantic evidence changed")
    if xlsx.get("container") != "xl/worksheets/sheet3.xml" or xlsx.get("candidate_row") != 289:
        raise RuntimeError("XLSX selected candidate evidence changed")
    if xlsx.get("window_start_row") != 257 or xlsx.get("window_end_row") != 288:
        raise RuntimeError("XLSX header-gap window changed")
    if xlsx.get("nearest_recognized_header_row") is not None:
        raise RuntimeError("XLSX nearest-header result changed")
    if xlsx.get("recognized_header_role_rows") != []:
        raise RuntimeError("XLSX recognized-header rows changed")
    if xlsx.get("truncated") is not False:
        raise RuntimeError("XLSX result must remain untruncated")

    for field in (
        "alternate_sources_used",
        "full_historical_reconstruction_performed",
        "candidate_score_computed",
        "component_zscores_computed",
        "component_contributions_computed",
        "research_ledger_modified",
        "public_artifacts_modified",
        "production_modified",
    ):
        if result.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if any(consumption.get("post_consumption_authorizations", {}).values()):
        raise RuntimeError("all post-consumption authorizations must be false")
    if consumption.get("new_owner_authorization_required_for_any_future_live_request") is not True:
        raise RuntimeError("future live BLS work must require new owner authorization")

    if contract.get("version") != 16:
        raise RuntimeError("consumed contract version changed")
    if contract.get("state") != "ambiguity_diagnostics_v7_header_gap_consumed_fail_closed":
        raise RuntimeError("contract must be consumed/fail-closed")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch marker must not be expected")
    if contract.get("completed_preflight_run") != RUN:
        raise RuntimeError("contract run evidence changed")
    if contract.get("completed_preflight_workflow_conclusion") != "success":
        raise RuntimeError("contract workflow conclusion changed")
    if contract.get("completed_preflight_result_status") != "completed":
        raise RuntimeError("contract result status changed")
    if any(contract.get("current_state", {}).values()):
        raise RuntimeError("all current authorization flags must be false")
    if contract.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if ("if: $" + "{{ false }}") not in workflow:
        raise RuntimeError("consumed workflow must remain inert")
    if "push:" in workflow:
        raise RuntimeError("consumed workflow must not retain a push trigger")

    return {
        "status": "passed",
        "state": "ambiguity_diagnostics_v7_header_gap_consumed_fail_closed",
        "design_version": 7,
        "preflight_run": RUN,
        "request_attempt_count": 2,
        "identifier_values_retained": False,
        "economic_values_retained": False,
        "html_candidate_row": 226,
        "html_nearest_header_row": None,
        "xlsx_candidate_row": 289,
        "xlsx_nearest_header_row": None,
        "active_receipt_present": False,
        "dispatch_present": False,
        "live_request_authorized": False,
        "identifier_value_read_authorized": False,
        "economic_value_read_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
