#!/usr/bin/env python3
"""Validate Issue #258 v5 design-only candidate-context inventory state."""

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
    v4 = _load(root / V4_CONSUMPTION.relative_to(ROOT))
    rights = _load(root / "governance/score-publication-rights-gate.json")
    workflow = (root / WORKFLOW.relative_to(ROOT)).read_text(encoding="utf-8")

    for relative in (RECEIPT.relative_to(ROOT), DISPATCH.relative_to(ROOT)):
        if (root / relative).exists():
            raise RuntimeError(f"v5 design-only state must not retain {relative}")

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
        raise RuntimeError("all v5 design authorization flags must remain false")

    header_compat = design.get("header_compatibility_policy", {})
    if header_compat.get("standalone_code_token_role") != "identifier":
        raise RuntimeError("standalone Code compatibility changed")
    if header_compat.get("mixed_index_code_role") != "ambiguous":
        raise RuntimeError("Index code must remain ambiguous")
    if header_compat.get("live_verification_status") != "v4_recheck_completed_no_resolution":
        raise RuntimeError("v4 header compatibility result not preserved")

    inventory = design.get("candidate_context_inventory_policy", {})
    expected = {
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
    for key, value in expected.items():
        if inventory.get(key) != value:
            raise RuntimeError(f"candidate context policy changed: {key}")
    if "<num>" not in inventory.get("numeric_token_policy", ""):
        raise RuntimeError("numeric-token redaction changed")
    if "<alnum-redacted>" not in inventory.get("alphanumeric_numeric_token_policy", ""):
        raise RuntimeError("alphanumeric-token redaction changed")

    if contract.get("version") != 8:
        raise RuntimeError("consumed contract version changed")
    if contract.get("state") != "ambiguity_diagnostics_v4_recheck_consumed_fail_closed":
        raise RuntimeError("contract must remain consumed/fail-closed")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch marker must not be expected")
    if any(contract.get("current_state", {}).values()):
        raise RuntimeError("all contract authorization flags must remain false")
    if contract.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if ("if: $" + "{{ false }}") not in workflow:
        raise RuntimeError("workflow must remain inert")
    if "push:" in workflow:
        raise RuntimeError("v5 design-only workflow must not have a push trigger")

    return {
        "status": "passed",
        "state": "ambiguity_diagnostics_v5_design_only_hold",
        "design_version": 5,
        "prior_v4_recheck_consumed": True,
        "candidate_context_live_authorized": False,
        "max_economic_observations_total": 0,
        "active_receipt_present": False,
        "dispatch_present": False,
        "production_authorized": False,
        "rights_hold": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
