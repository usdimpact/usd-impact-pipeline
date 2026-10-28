#!/usr/bin/env python3
"""Validate the Issue #258 ambiguity-diagnostics design-only HOLD state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DESIGN = "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json"
TEMPLATE = "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json"
CONTRACT = "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json"
ACTIVE_RECEIPT = "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
PREDECESSOR = "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-consumption-2026-10-29.json"
WORKFLOW = ".github/workflows/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight.yml"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
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
    design = _load(root / DESIGN)
    template = _load(root / TEMPLATE)
    contract = _load(root / CONTRACT)
    predecessor = _load(root / PREDECESSOR)
    rights = _load(root / "governance/score-publication-rights-gate.json")
    prereg = _load(root / "governance/score-v2-1f-preregistration.json")
    workflow = (root / WORKFLOW).read_text(encoding="utf-8")

    for relative in (ACTIVE_RECEIPT, DISPATCH):
        if (root / relative).exists():
            raise RuntimeError(f"design-only HOLD must not contain {relative}")

    if predecessor.get("state") != "consumed_after_ambiguous_result":
        raise RuntimeError("Issue #252 consumption evidence changed")
    result = predecessor.get("sanitized_result", {})
    if result.get("request_count") != 2 or result.get("observation_count") != 0:
        raise RuntimeError("Issue #252 sanitized result changed")

    if rights.get("state") != "hold":
        raise RuntimeError("Score publication rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")

    if design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 design must remain HOLD")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("Issue #258 owner-decision URL changed")
    if [item.get("path") for item in design.get("fixed_resources", [])] != EXPECTED_RESOURCES:
        raise RuntimeError("Issue #258 fixed resources changed")
    budget = design.get("future_live_budget", {})
    if budget.get("request_budget") != 2:
        raise RuntimeError("Issue #258 request budget changed")
    if budget.get("max_economic_observations_total") != 0:
        raise RuntimeError("Issue #258 must allow zero economic observations")
    if budget.get("max_economic_observations_per_resource") != 0:
        raise RuntimeError("Issue #258 per-resource economic observation cap must be zero")

    policy = design.get("diagnostic_policy", {})
    if policy.get("economic_value_read") is not False:
        raise RuntimeError("economic value read must remain forbidden")
    if policy.get("local_block_required") is not True:
        raise RuntimeError("local candidate block scoping must be required")
    if policy.get("whole_sheet_or_whole_table_role_accumulation_forbidden") is not True:
        raise RuntimeError("whole-container role accumulation must remain forbidden")
    if policy.get("whole_sheet_revision_context_accumulation_forbidden") is not True:
        raise RuntimeError("whole-sheet revision context accumulation must remain forbidden")

    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("all Issue #258 design authorizations must remain false")
    if template.get("decision_status") != "hold":
        raise RuntimeError("authorization template must remain HOLD")
    if template.get("max_economic_observations_total") != 0:
        raise RuntimeError("authorization template economic observation cap must be zero")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("authorization template flags must remain false")

    if contract.get("state") != "ambiguity_diagnostics_design_only_hold":
        raise RuntimeError("execution contract must remain design-only HOLD")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch must not be expected")
    if contract.get("max_economic_observations_total") != 0:
        raise RuntimeError("contract economic observation cap must be zero")
    if any(contract.get("current_state", {}).values()):
        raise RuntimeError("contract authorization flags must all remain false")
    if contract.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if ("if: $" + "{{ false }}") not in workflow:
        raise RuntimeError("Issue #258 workflow must remain inert")
    if "push:" in workflow:
        raise RuntimeError("Issue #258 HOLD workflow must not have a push trigger")

    return {
        "status": "passed",
        "state": "ambiguity_diagnostics_design_only_hold",
        "issue": ISSUE,
        "request_budget": 2,
        "max_economic_observations_total": 0,
        "active_receipt_present": False,
        "dispatch_present": False,
        "live_request_authorized": False,
        "economic_value_read_authorized": False,
        "candidate_score_computation_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
