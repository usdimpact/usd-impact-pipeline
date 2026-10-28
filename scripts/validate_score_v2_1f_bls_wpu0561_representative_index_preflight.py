#!/usr/bin/env python3
"""Validate consumed/fail-closed WPU0561 representative-index state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RECEIPT = "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-dispatch.json"
CONSUMPTION = "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-consumption-2026-10-29.json"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/252"
RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40785283066"
ACTIVATION_COMMIT = "c41413ce08f3fad32cefe7ad307449eac0e65978"
DISPATCH_COMMIT = "1f917706798f9d9b009a104f0543b84b51a8504c"

def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload

def validate(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    design = _load(root / "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-design.json")
    template = _load(root / "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-authorization.template.json")
    consumption = _load(root / CONSUMPTION)
    contract = _load(root / "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-execution-contract.json")
    predecessor = _load(root / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-consumption-2026-10-29.json")
    rights = _load(root / "governance/score-publication-rights-gate.json")
    prereg = _load(root / "governance/score-v2-1f-preregistration.json")
    workflow = (root / ".github/workflows/score-v2-1f-bls-wpu0561-representative-index-preflight.yml").read_text(encoding="utf-8")

    for relative in (RECEIPT, DISPATCH):
        if (root / relative).exists():
            raise RuntimeError(f"consumed state must not retain {relative}")

    if predecessor.get("state") != "consumed_after_success":
        raise RuntimeError("Issue #244 consumption evidence changed")
    if predecessor.get("sanitized_result", {}).get("wpu0561_mapping_proven") is not True:
        raise RuntimeError("Issue #244 WPU0561 mapping evidence changed")
    if rights.get("state") != "hold":
        raise RuntimeError("Score publication rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")

    if design.get("state") != "design_only_hold":
        raise RuntimeError("frozen representative-index design changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("representative-index issue changed")
    policy = design.get("field_semantics_policy", {})
    if policy.get("allowed") != ["original_release_index_level"]:
        raise RuntimeError("allowed field semantics changed")
    if policy.get("multiple_index_level_candidates_fail_closed") is not True:
        raise RuntimeError("multiple-candidate fail-closed policy changed")
    if policy.get("ambiguous_revision_context_fails_closed") is not True:
        raise RuntimeError("revision ambiguity policy changed")

    if template.get("decision_status") != "hold" or any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template changed")

    if consumption.get("state") != "consumed_after_ambiguous_result":
        raise RuntimeError("consumption state changed")
    if consumption.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("consumption issue changed")
    if consumption.get("owner_approval_comment_id") != 6482942968:
        raise RuntimeError("owner approval evidence changed")
    if consumption.get("authorization_activation_merge_commit") != ACTIVATION_COMMIT:
        raise RuntimeError("activation merge evidence changed")
    if consumption.get("dispatch_merge_commit") != DISPATCH_COMMIT:
        raise RuntimeError("dispatch merge evidence changed")
    if consumption.get("preflight_run") != RUN:
        raise RuntimeError("preflight run evidence changed")
    if consumption.get("preflight_workflow_conclusion") != "success":
        raise RuntimeError("workflow conclusion changed")
    if consumption.get("preflight_result_status") != "ambiguous":
        raise RuntimeError("result status changed")
    if consumption.get("request_budget") != 2:
        raise RuntimeError("request budget changed")
    if consumption.get("max_observations_total") != 2:
        raise RuntimeError("observation budget changed")
    if consumption.get("max_observations_per_resource") != 1:
        raise RuntimeError("per-resource observation budget changed")
    if consumption.get("new_owner_authorization_required_for_any_future_live_request") is not True:
        raise RuntimeError("future live work must require new owner authorization")

    result = consumption.get("sanitized_result", {})
    if result.get("request_count") != 2:
        raise RuntimeError("sanitized request count changed")
    if result.get("observation_count") != 0:
        raise RuntimeError("ambiguous run must retain zero observations")
    for field in (
        "html_observation_retained",
        "xlsx_observation_retained",
        "percent_change_fields_retained",
        "unrelated_numeric_values_retained",
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

    if contract.get("state") != "representative_index_preflight_consumed_fail_closed":
        raise RuntimeError("execution contract is not consumed/fail-closed")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch must not be expected")
    if contract.get("completed_preflight_run") != RUN:
        raise RuntimeError("contract run evidence changed")
    if contract.get("completed_preflight_workflow_conclusion") != "success":
        raise RuntimeError("contract workflow conclusion changed")
    if contract.get("completed_preflight_result_status") != "ambiguous":
        raise RuntimeError("contract result status changed")
    if any(contract.get("current_state", {}).values()):
        raise RuntimeError("all contract authorization flags must be false")
    if contract.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if ("if: $" + "{{ false }}") not in workflow:
        raise RuntimeError("consumed workflow must remain inert")
    if "push:" in workflow:
        raise RuntimeError("consumed workflow must not retain a push trigger")

    return {
        "status": "passed",
        "state": "representative_index_preflight_consumed_fail_closed",
        "issue": ISSUE,
        "preflight_run": RUN,
        "preflight_workflow_conclusion": "success",
        "preflight_result_status": "ambiguous",
        "request_count": 2,
        "observation_count": 0,
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
