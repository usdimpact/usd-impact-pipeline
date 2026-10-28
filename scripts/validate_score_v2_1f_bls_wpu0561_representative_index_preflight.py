#!/usr/bin/env python3
"""Validate design-only/HOLD WPU0561 representative-index packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RECEIPT = "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-dispatch.json"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/252"
EXPECTED_RESOURCES = [
    "/news.release/archives/ppi_05152013.htm",
    "/ppi/detailed-report/ppi-detailed-report-april-2026.xlsx",
]

def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload

def validate(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    design = _load(root / "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-design.json")
    template = _load(root / "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-authorization.template.json")
    contract = _load(root / "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-execution-contract.json")
    predecessor = _load(root / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-consumption-2026-10-29.json")
    rights = _load(root / "governance/score-publication-rights-gate.json")
    prereg = _load(root / "governance/score-v2-1f-preregistration.json")
    workflow = (root / ".github/workflows/score-v2-1f-bls-wpu0561-representative-index-preflight.yml").read_text(encoding="utf-8")

    for relative in (RECEIPT, DISPATCH):
        if (root / relative).exists():
            raise RuntimeError(f"design-only state must not retain {relative}")

    if predecessor.get("state") != "consumed_after_success":
        raise RuntimeError("Issue #244 consumption evidence changed")
    if predecessor.get("sanitized_result", {}).get("wpu0561_mapping_proven") is not True:
        raise RuntimeError("Issue #244 WPU0561 mapping evidence changed")
    if predecessor.get("new_owner_authorization_required_for_any_future_live_request") is not True:
        raise RuntimeError("future live work must require a new owner authorization")

    if rights.get("state") != "hold":
        raise RuntimeError("Score publication rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")

    if design.get("state") != "design_only_hold":
        raise RuntimeError("representative-index design must remain HOLD")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("representative-index owner-decision issue changed")
    if design.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("representative-index fixed resources changed")
    budget = design.get("future_live_budget", {})
    if budget.get("request_budget") != 2:
        raise RuntimeError("request budget changed")
    if budget.get("max_economic_observations_total") != 2:
        raise RuntimeError("total observation cap changed")
    if budget.get("max_economic_observations_per_resource") != 1:
        raise RuntimeError("per-resource observation cap changed")
    policy = design.get("field_semantics_policy", {})
    if policy.get("allowed") != ["original_release_index_level"]:
        raise RuntimeError("allowed field semantics changed")
    if policy.get("multiple_index_level_candidates_fail_closed") is not True:
        raise RuntimeError("multiple-candidate fail-closed policy changed")
    if policy.get("ambiguous_revision_context_fails_closed") is not True:
        raise RuntimeError("revision ambiguity policy changed")
    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("all design authorizations must remain false")

    if template.get("decision_status") != "hold":
        raise RuntimeError("authorization template must remain HOLD")
    if template.get("request_budget") != 2:
        raise RuntimeError("template request budget changed")
    if template.get("max_observations_total") != 2:
        raise RuntimeError("template total observation cap changed")
    if template.get("max_observations_per_resource") != 1:
        raise RuntimeError("template per-resource observation cap changed")
    if template.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("template fixed resources changed")
    if template.get("contact_user_agent") is not None:
        raise RuntimeError("HOLD template must not preselect contact identity")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template authorizations must remain false")

    if contract.get("state") != "design_only_hold":
        raise RuntimeError("execution contract must remain HOLD")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch must not be expected")
    if contract.get("request_budget") != 2:
        raise RuntimeError("contract request budget changed")
    if contract.get("max_observations_total") != 2:
        raise RuntimeError("contract total observation cap changed")
    if contract.get("max_observations_per_resource") != 1:
        raise RuntimeError("contract per-resource observation cap changed")
    if any(contract.get("current_state", {}).values()):
        raise RuntimeError("all contract authorization flags must remain false")
    if contract.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if ("if: $" + "{{ false }}") not in workflow:
        raise RuntimeError("representative-index workflow must remain inert")
    if "push:" in workflow:
        raise RuntimeError("design-only workflow must not have a push trigger")

    return {
        "status": "passed",
        "state": "design_only_hold",
        "issue": ISSUE,
        "request_budget": 2,
        "max_observations_total": 2,
        "max_observations_per_resource": 1,
        "active_receipt_present": False,
        "dispatch_present": False,
        "response_body_ephemeral_retrieval_authorized": False,
        "representative_index_value_read_authorized": False,
        "representative_index_preflight_authorized": False,
        "candidate_score_computation_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }

def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
