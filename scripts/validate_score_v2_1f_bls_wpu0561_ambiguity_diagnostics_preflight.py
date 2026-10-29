#!/usr/bin/env python3
"""Validate consumed/fail-closed Issue #258 design-v5 candidate-context state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40794631448"
ACTIVATION_COMMIT = "a4fce774c7df612b83ed8be120da944a360ce016"
DISPATCH_COMMIT = "a12d009d1b081b65ddb86ea27118b1fa743045d0"
DESIGN = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json"
TEMPLATE = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json"
RECEIPT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
DISPATCH = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
CONTRACT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json"
CONSUMPTION = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-v5-candidate-context-consumption-2026-10-29.json"
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
            raise RuntimeError(f"consumed v5 state must not retain {relative}")

    if rights.get("state") != "hold":
        raise RuntimeError("Issue #155 rights gate must remain HOLD")
    if template.get("decision_status") != "hold" or any(template.get("authorizations", {}).values()):
        raise RuntimeError("authorization template must remain HOLD")

    if design.get("version") != 5 or design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 v5 design changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("Issue #258 design issue changed")
    if design.get("future_live_budget", {}).get("request_budget") != 2:
        raise RuntimeError("request budget changed")
    if design.get("future_live_budget", {}).get("max_economic_observations_total") != 0:
        raise RuntimeError("economic observation budget changed")
    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("frozen design authorization flags must remain false")

    inventory = design.get("candidate_context_inventory_policy", {})
    expected_inventory = {
        "maximum_candidates_per_resource": 32,
        "preceding_rows_per_candidate": 8,
        "following_rows_per_candidate": 0,
        "maximum_persisted_text_cells_per_candidate": 64,
        "identifier_values": "forbidden; this diagnostic does not read or persist identifier values",
        "economic_values": "forbidden",
        "response_body_persistence": False,
    }
    for key, value in expected_inventory.items():
        if inventory.get(key) != value:
            raise RuntimeError(f"candidate context policy changed: {key}")

    if consumption.get("state") != "consumed_after_completed_v5_candidate_context_inventory":
        raise RuntimeError("v5 consumption state changed")
    if consumption.get("design_version") != 5:
        raise RuntimeError("v5 consumption design version changed")
    if consumption.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("consumption issue changed")
    if consumption.get("owner_approval_comment_id") != 6484353947:
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
    if result.get("economic_observation_count") != 0:
        raise RuntimeError("economic observation count must remain zero")
    if result.get("identifier_value_count") != 0:
        raise RuntimeError("identifier value count must remain zero")
    html = result.get("html", {})
    xlsx = result.get("xlsx", {})
    if html.get("transport_status") != "passed" or html.get("semantic_status") != "evaluated":
        raise RuntimeError("HTML transport/semantic evidence changed")
    if html.get("candidate_count") != 3:
        raise RuntimeError("HTML candidate count changed")
    if xlsx.get("transport_status") != "passed" or xlsx.get("semantic_status") != "evaluated":
        raise RuntimeError("XLSX transport/semantic evidence changed")
    if xlsx.get("candidate_count") != 29:
        raise RuntimeError("XLSX candidate count changed")

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

    if contract.get("version") != 11:
        raise RuntimeError("consumed contract version changed")
    if contract.get("state") != "ambiguity_diagnostics_v5_candidate_context_consumed_fail_closed":
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
        "state": "ambiguity_diagnostics_v5_candidate_context_consumed_fail_closed",
        "design_version": 5,
        "preflight_run": RUN,
        "request_attempt_count": 2,
        "economic_observation_count": 0,
        "identifier_value_count": 0,
        "html_candidate_count": 3,
        "xlsx_candidate_count": 29,
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
