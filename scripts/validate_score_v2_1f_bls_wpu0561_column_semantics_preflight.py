#!/usr/bin/env python3
"""Validate consumed/fail-closed WPU0561 column-semantics state."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any

RECEIPT = "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-dispatch.json"
CONSUMPTION = "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-consumption-2026-10-29.json"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/244"
RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40780574921"
ACTIVATION_COMMIT = "474770a01b5493537731697f804e88b4e849d41d"
DISPATCH_COMMIT = "d42d0adae56a66061f6e4a24dd1096f04af94441"

def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload

def validate(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    design = _load(root / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-design.json")
    template = _load(root / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-authorization.template.json")
    consumption = _load(root / CONSUMPTION)
    contract = _load(root / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-execution-contract.json")
    prior = _load(root / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-consumption-2026-10-28.json")
    rights = _load(root / "governance/score-publication-rights-gate.json")
    prereg = _load(root / "governance/score-v2-1f-preregistration.json")
    workflow = (root / ".github/workflows/score-v2-1f-bls-wpu0561-column-semantics-preflight.yml").read_text(encoding="utf-8")

    for relative in (RECEIPT, DISPATCH):
        if (root / relative).exists():
            raise RuntimeError(f"consumed state must not retain {relative}")

    if prior.get("state") != "consumed_after_success":
        raise RuntimeError("row-presence consumption evidence changed")
    if rights.get("state") != "hold":
        raise RuntimeError("Score publication rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")

    if design.get("state") != "design_only_hold":
        raise RuntimeError("frozen column-semantics design changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("column-semantics issue changed")
    if design.get("identifier_policy", {}).get("conflicting_header_behavior") != "classify_ambiguous_never_identifier":
        raise RuntimeError("conflicting-header policy changed")
    if design.get("identifier_policy", {}).get("row_wide_identifier_fallback") is not False:
        raise RuntimeError("row-wide identifier fallback must remain disabled")

    if template.get("decision_status") != "hold" or any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template changed")

    if consumption.get("state") != "consumed_after_success":
        raise RuntimeError("consumption state changed")
    if consumption.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("consumption issue changed")
    if consumption.get("owner_approval_comment_id") != 6482193778:
        raise RuntimeError("owner approval evidence changed")
    if consumption.get("authorization_activation_merge_commit") != ACTIVATION_COMMIT:
        raise RuntimeError("activation merge evidence changed")
    if consumption.get("dispatch_merge_commit") != DISPATCH_COMMIT:
        raise RuntimeError("dispatch merge evidence changed")
    if consumption.get("preflight_run") != RUN or consumption.get("preflight_conclusion") != "success":
        raise RuntimeError("preflight run evidence changed")
    if consumption.get("request_budget") != 2:
        raise RuntimeError("request budget changed")
    if consumption.get("new_owner_authorization_required_for_any_future_live_request") is not True:
        raise RuntimeError("future live work must require new owner authorization")

    result = consumption.get("sanitized_result", {})
    if result.get("request_count") != 2:
        raise RuntimeError("sanitized request count changed")
    if result.get("wpu0561_mapping_proven") is not True:
        raise RuntimeError("WPU0561 mapping evidence changed")
    if result.get("normalized_identifier") != "0561":
        raise RuntimeError("normalized identifier changed")
    if result.get("html_crude_petroleum_match_count") != 3:
        raise RuntimeError("HTML match count changed")
    if result.get("xlsx_crude_petroleum_match_count") != 29:
        raise RuntimeError("XLSX match count changed")
    for field in (
        "economic_values_extracted","economic_values_logged","economic_values_persisted",
        "full_historical_reconstruction_performed","candidate_score_computed",
        "component_zscores_computed","component_contributions_computed",
        "alternate_sources_used","research_ledger_modified","public_artifacts_modified",
        "production_modified",
    ):
        if result.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")
    if any(consumption.get("post_consumption_authorizations", {}).values()):
        raise RuntimeError("all post-consumption authorizations must be false")

    if contract.get("state") != "column_semantics_preflight_consumed_fail_closed":
        raise RuntimeError("execution contract is not consumed/fail-closed")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch must not be expected")
    if contract.get("completed_preflight_run") != RUN or contract.get("completed_preflight_conclusion") != "success":
        raise RuntimeError("contract run evidence changed")
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
        "state": "column_semantics_preflight_consumed_fail_closed",
        "issue": ISSUE,
        "preflight_run": RUN,
        "preflight_conclusion": "success",
        "request_count": 2,
        "wpu0561_mapping_proven": True,
        "normalized_identifier": "0561",
        "active_receipt_present": False,
        "dispatch_present": False,
        "response_body_ephemeral_retrieval_authorized": False,
        "column_semantics_preflight_authorized": False,
        "numeric_identifier_field_read_authorized": False,
        "economic_value_extraction_authorized": False,
        "candidate_score_computation_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }

def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
