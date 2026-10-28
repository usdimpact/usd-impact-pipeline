#!/usr/bin/env python3
"""Validate consumed/fail-closed Score v2.1F Stage 1 preflight authorization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ACTIVE_RECEIPT = "governance/score-v2-1f-live-vintage-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-live-vintage-preflight-dispatch.json"
CONSUMPTION = "governance/score-v2-1f-live-vintage-preflight-consumption-2026-10-28.json"
EXPECTED_WINDOW = {"start": "2013-01-01", "end": "2026-10-23"}
APPROVAL_COMMENT = 6479715940
APPROVED_AT = "2026-10-28T20:20:28Z"
ACTIVATION_COMMIT = "48f6815199db7c030939629f49a75001d20ae566"
DISPATCH_COMMIT = "6ea7eb7390ad9949799867c6db38f20664cba6a3"
FAILED_RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40763350781"
BLOCKER = "https://github.com/usdimpact/usd-impact-pipeline/issues/228"

def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload

def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    template = _load(
        repo_root / "governance/score-v2-1f-live-vintage-preflight-authorization.template.json"
    )
    contract = _load(
        repo_root / "governance/score-v2-1f-live-vintage-preflight-execution-contract.json"
    )
    consumption = _load(repo_root / CONSUMPTION)
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")
    prereg = _load(repo_root / "governance/score-v2-1f-preregistration.json")

    if (repo_root / ACTIVE_RECEIPT).exists():
        raise RuntimeError("consumed Stage 1 authorization must not retain an active receipt")
    if (repo_root / DISPATCH).exists():
        raise RuntimeError("consumed Stage 1 authorization must not retain a dispatch marker")
    if hold.get("state") != "hold":
        raise RuntimeError("Score rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")

    if template.get("decision_status") != "hold":
        raise RuntimeError("HOLD template must remain unchanged")
    if template.get("data_window") != {"start": None, "end": None}:
        raise RuntimeError("HOLD template may not preselect a live data window")
    if template.get("approved_by") is not None or template.get("approved_at") is not None:
        raise RuntimeError("HOLD template may not contain approval evidence")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template authorizations must remain false")

    if consumption.get("state") != "consumed_fail_closed":
        raise RuntimeError("consumption record state changed")
    if consumption.get("owner_approval_comment_id") != APPROVAL_COMMENT:
        raise RuntimeError("owner approval evidence changed")
    if consumption.get("owner_approval_timestamp") != APPROVED_AT:
        raise RuntimeError("owner approval timestamp changed")
    if consumption.get("authorization_activation_merge_commit") != ACTIVATION_COMMIT:
        raise RuntimeError("activation merge evidence changed")
    if consumption.get("dispatch_merge_commit") != DISPATCH_COMMIT:
        raise RuntimeError("dispatch merge evidence changed")
    if consumption.get("authorized_data_window") != EXPECTED_WINDOW:
        raise RuntimeError("consumed authorization window changed")
    if consumption.get("preflight_run") != FAILED_RUN:
        raise RuntimeError("preflight run evidence changed")
    if consumption.get("blocker_issue") != BLOCKER:
        raise RuntimeError("blocker issue changed")
    if consumption.get("preflight_conclusion") != "failure":
        raise RuntimeError("preflight conclusion changed")

    failure = consumption.get("failure", {})
    if failure.get("official_host") != "www.bls.gov":
        raise RuntimeError("BLS blocker host changed")
    if failure.get("official_path") != "/bls/news-release/ppi.htm":
        raise RuntimeError("BLS blocker path changed")
    if failure.get("http_status") != 403:
        raise RuntimeError("BLS blocker HTTP status changed")
    if failure.get("federal_reserve_phase_completed_before_bls_request") is not True:
        raise RuntimeError("Federal Reserve pre-BLS phase evidence changed")

    result = consumption.get("research_result", {})
    for field in (
        "candidate_score_computed",
        "component_zscores_computed",
        "component_contributions_computed",
        "source_or_component_values_persisted",
        "source_or_component_values_posted_to_issue",
        "public_artifacts_modified",
        "research_ledgers_modified",
        "production_modified",
    ):
        if result.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    post = consumption.get("post_consumption_authorizations", {})
    if not isinstance(post, dict) or any(post.values()):
        raise RuntimeError("all post-consumption authorizations must be false")
    if consumption.get("new_owner_authorization_required_for_any_future_live_request") is not True:
        raise RuntimeError("future live work must require a new owner authorization")

    if contract.get("state") != "live_vintage_preflight_consumed_fail_closed":
        raise RuntimeError("execution contract is not consumed/fail-closed")
    if contract.get("blocker_issue") != BLOCKER:
        raise RuntimeError("contract blocker evidence changed")
    if contract.get("failed_preflight_run") != FAILED_RUN:
        raise RuntimeError("contract failed-run evidence changed")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected after consumption")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch marker must not be expected after consumption")
    if contract.get("authorized_data_window") != EXPECTED_WINDOW:
        raise RuntimeError("contract audit window changed")
    current = contract.get("current_state", {})
    if not isinstance(current, dict) or any(current.values()):
        raise RuntimeError("all execution authorizations must be false after consumption")

    return {
        "status": "passed",
        "state": "live_vintage_preflight_consumed_fail_closed",
        "active_authorization_receipt_present": False,
        "dispatch_marker_present": False,
        "data_window": EXPECTED_WINDOW,
        "preflight_conclusion": "failure",
        "blocker_http_status": 403,
        "federal_reserve_phase_completed_before_bls_request": True,
        "real_data_fetch_authorized": False,
        "live_vintage_preflight_authorized": False,
        "real_data_research_authorized": False,
        "candidate_score_computation_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
        "blocker_issue": BLOCKER,
        "failed_preflight_run": FAILED_RUN,
    }

def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
