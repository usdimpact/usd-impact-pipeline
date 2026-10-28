#!/usr/bin/env python3
"""Validate consumed/fail-closed Issue #258 ambiguity diagnostics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json"
TEMPLATE = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json"
RECEIPT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
DISPATCH = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
CONTRACT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json"
CONSUMPTION = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-consumption-2026-10-29.json"
WORKFLOW = ROOT / ".github/workflows/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight.yml"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40790532286"
ACTIVATION_COMMIT = "f67d925e5bc35575f822ae6e22566b0155fbf00f"
DISPATCH_COMMIT = "7046d9d69c65739ca43c4e6effec7fbee3c0b35f"


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
    prereg = _load(root / "governance/score-v2-1f-preregistration.json")
    workflow = (root / WORKFLOW.relative_to(ROOT)).read_text(encoding="utf-8")

    for relative in (RECEIPT.relative_to(ROOT), DISPATCH.relative_to(ROOT)):
        if (root / relative).exists():
            raise RuntimeError(f"consumed state must not retain {relative}")

    if rights.get("state") != "hold":
        raise RuntimeError("Score publication rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")

    if design.get("version") != 4 or design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 frozen design changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("Issue #258 design issue changed")
    if design.get("future_live_budget", {}).get("max_economic_observations_total") != 0:
        raise RuntimeError("economic observation budget must remain zero")
    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("frozen design authorizations must remain false")
    header_compat = design.get("header_compatibility_policy", {})
    if header_compat.get("standalone_code_token_role") != "identifier":
        raise RuntimeError("standalone Code header role changed")
    if header_compat.get("mixed_index_code_role") != "ambiguous":
        raise RuntimeError("Index code must remain ambiguous")
    if header_compat.get("substring_only_matches_for_code") != "forbidden; Code must appear as a standalone word token":
        raise RuntimeError("bare Code recognition became too permissive")
    if header_compat.get("live_verification_status") != "not_yet_authorized":
        raise RuntimeError("header compatibility must remain unverified without new owner authorization")

    if template.get("decision_status") != "hold":
        raise RuntimeError("authorization template must remain HOLD")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("authorization template flags must remain false")

    if consumption.get("state") != "consumed_after_completed_diagnostics":
        raise RuntimeError("Issue #258 consumption state changed")
    if consumption.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("Issue #258 consumption issue changed")
    if consumption.get("owner_approval_comment_id") != 6483711604:
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
        raise RuntimeError("diagnostic result status changed")
    if consumption.get("request_budget") != 2:
        raise RuntimeError("request budget changed")
    if consumption.get("max_economic_observations_total") != 0:
        raise RuntimeError("economic observation budget changed")

    result = consumption.get("sanitized_result", {})
    if result.get("request_attempt_count") != 2:
        raise RuntimeError("request attempt count changed")
    if result.get("economic_observation_count") != 0:
        raise RuntimeError("economic observation count must remain zero")
    for resource in ("html", "xlsx"):
        payload = result.get(resource, {})
        if payload.get("transport_status") != "passed":
            raise RuntimeError(f"{resource} transport evidence changed")
        if payload.get("semantic_status") != "evaluated":
            raise RuntimeError(f"{resource} semantic evidence changed")
        if payload.get("reason_summary") != {"no_local_header_anchor": 1}:
            raise RuntimeError(f"{resource} reason summary changed")
        if payload.get("candidate_bearing_or_proven_blocks") != 0:
            raise RuntimeError(f"{resource} candidate-bearing block count changed")

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

    if contract.get("version") != 5:
        raise RuntimeError("consumed contract version changed")
    if contract.get("state") != "ambiguity_diagnostics_consumed_fail_closed":
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
        "state": "ambiguity_diagnostics_consumed_fail_closed",
        "issue": ISSUE,
        "preflight_run": RUN,
        "request_attempt_count": 2,
        "economic_observation_count": 0,
        "html_reason": "no_local_header_anchor",
        "xlsx_reason": "no_local_header_anchor",
        "active_receipt_present": False,
        "dispatch_present": False,
        "live_request_authorized": False,
        "economic_value_read_authorized": False,
        "candidate_score_computation_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


def main() -> int:
    print(json.dumps(validate(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
