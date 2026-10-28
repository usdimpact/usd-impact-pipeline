#!/usr/bin/env python3
"""Validate consumed/fail-closed state for the Score v2.1E one-off research authorization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ACTIVE_RECEIPT = "governance/score-v2-1e-real-data-research-authorization.json"
CONSUMPTION = "governance/score-v2-1e-real-data-research-consumption-2026-10-28.json"
EXPECTED_WINDOW = {"start": "2013-01-01", "end": "2026-10-23"}
APPROVAL_COMMENT = 6477834394
APPROVED_AT = "2026-10-28T18:55:48Z"
FAILED_RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40755916179"
BLOCKER_ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/218"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    contract = _load(repo_root / "governance/score-v2-1e-real-data-execution-contract.json")
    consumption = _load(repo_root / CONSUMPTION)
    template = _load(repo_root / "governance/score-v2-1e-real-data-research-authorization.template.json")
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")

    if (repo_root / ACTIVE_RECEIPT).exists():
        raise RuntimeError("consumed one-off authorization must not retain an active receipt")
    if hold.get("state") != "hold":
        raise RuntimeError("Score rights gate must remain HOLD")
    if template.get("decision_status") != "hold":
        raise RuntimeError("HOLD template must remain unchanged")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template authorizations must remain false")

    if consumption.get("state") != "consumed_fail_closed":
        raise RuntimeError("consumption record state changed")
    if consumption.get("owner_approval_comment_id") != APPROVAL_COMMENT:
        raise RuntimeError("owner approval evidence changed")
    if consumption.get("owner_approval_timestamp") != APPROVED_AT:
        raise RuntimeError("owner approval timestamp changed")
    if consumption.get("authorized_data_window") != EXPECTED_WINDOW:
        raise RuntimeError("consumed authorization window changed")
    if consumption.get("failed_run") != FAILED_RUN:
        raise RuntimeError("failed preflight run changed")
    if consumption.get("blocker_issue") != BLOCKER_ISSUE:
        raise RuntimeError("blocker issue changed")
    result = consumption.get("research_result", {})
    for field in (
        "candidate_score_computed",
        "source_or_component_values_persisted",
        "public_artifacts_modified",
        "research_ledgers_modified",
        "production_modified",
    ):
        if result.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")
    post = consumption.get("post_consumption_authorizations", {})
    if not isinstance(post, dict) or any(post.values()):
        raise RuntimeError("all post-consumption authorizations must be false")
    if consumption.get("new_owner_authorization_required_for_any_future_real_data_run") is not True:
        raise RuntimeError("future real-data work must require a new owner authorization")

    if contract.get("state") != "one_off_private_research_consumed_fail_closed":
        raise RuntimeError("execution contract is not consumed/fail-closed")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected after consumption")
    if contract.get("authorized_data_window") != EXPECTED_WINDOW:
        raise RuntimeError("contract audit window changed")
    if contract.get("failed_preflight_run") != FAILED_RUN:
        raise RuntimeError("contract failed-run evidence changed")
    if contract.get("blocker_issue") != BLOCKER_ISSUE:
        raise RuntimeError("contract blocker evidence changed")
    current = contract.get("current_state", {})
    if not isinstance(current, dict) or any(current.values()):
        raise RuntimeError("all execution authorizations must be false after consumption")

    return {
        "status": "passed",
        "state": "one_off_private_research_consumed_fail_closed",
        "active_authorization_receipt_present": False,
        "data_window": EXPECTED_WINDOW,
        "real_data_fetch_authorized": False,
        "real_data_research_authorized": False,
        "candidate_score_computed": False,
        "production_authorized": False,
        "rights_hold": True,
        "blocker_issue": BLOCKER_ISSUE,
        "failed_preflight_run": FAILED_RUN,
    }


def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
