#!/usr/bin/env python3
"""Validate consumed/fail-closed Issue #258 design-v8 header-band state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40901086765"
ACTIVATION_COMMIT = "312a90e51ccbd91deff543af271bafc6d02247cb"
DISPATCH_COMMIT = "90601f583683d7fab457734a0bd0cfcec387f4f5"
DESIGN = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json"
TEMPLATE = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json"
RECEIPT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
DISPATCH = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
CONTRACT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json"
CONSUMPTION = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-v8-container-header-band-consumption-2026-10-29.json"
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
            raise RuntimeError(f"consumed v8 state must not retain {relative}")

    if rights.get("state") != "hold":
        raise RuntimeError("Issue #155 rights gate must remain HOLD")
    if template.get("decision_status") != "hold" or any(template.get("authorizations", {}).values()):
        raise RuntimeError("authorization template must remain HOLD")

    if design.get("version") != 8 or design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 v8 design changed")
    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("frozen v8 design authorization flags must remain false")

    if consumption.get("state") != "consumed_after_completed_v8_container_header_band_inventory":
        raise RuntimeError("v8 consumption state changed")
    if consumption.get("design_version") != 8:
        raise RuntimeError("v8 consumption design version changed")
    if consumption.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("consumption issue changed")
    if consumption.get("owner_approval_comment_id") != 6500606721:
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

    result = consumption.get("sanitized_result", {})
    if result.get("request_attempt_count") != 2:
        raise RuntimeError("request attempt count changed")
    if result.get("identifier_values_retained") is not False:
        raise RuntimeError("identifier safeguard changed")
    if result.get("economic_values_retained") is not False:
        raise RuntimeError("economic safeguard changed")
    html = result.get("html", {})
    xlsx = result.get("xlsx", {})
    if html.get("container") != "table 4":
        raise RuntimeError("HTML container evidence changed")
    if html.get("band_start_row") != 1 or html.get("band_end_row") != 32:
        raise RuntimeError("HTML band evidence changed")
    if html.get("recognized_header_role_rows") != [1]:
        raise RuntimeError("HTML recognized-role evidence changed")
    if "index_level" not in html.get("structural_roles", []):
        raise RuntimeError("HTML index-level evidence changed")
    if xlsx.get("container") != "xl/worksheets/sheet3.xml":
        raise RuntimeError("XLSX container evidence changed")
    if xlsx.get("band_start_row") != 1 or xlsx.get("band_end_row") != 32:
        raise RuntimeError("XLSX band evidence changed")
    if xlsx.get("recognized_header_role_rows") != [1, 4, 5]:
        raise RuntimeError("XLSX recognized-role evidence changed")
    if xlsx.get("index_level_column_observed_in_header_band") is not False:
        raise RuntimeError("XLSX index-level evidence changed")
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

    if contract.get("version") != 20:
        raise RuntimeError("consumed contract version changed")
    if contract.get("state") != "ambiguity_diagnostics_v8_container_header_band_consumed_fail_closed":
        raise RuntimeError("contract must be consumed/fail-closed")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch marker must not be expected")
    if contract.get("completed_preflight_run") != RUN:
        raise RuntimeError("contract run evidence changed")
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
        "state": "ambiguity_diagnostics_v8_container_header_band_consumed_fail_closed",
        "design_version": 8,
        "preflight_run": RUN,
        "request_attempt_count": 2,
        "identifier_values_retained": False,
        "economic_values_retained": False,
        "html_index_level_header_observed": True,
        "xlsx_index_level_header_observed": False,
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
