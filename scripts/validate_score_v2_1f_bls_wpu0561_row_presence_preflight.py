#!/usr/bin/env python3
"""Validate consumed/fail-closed Score v2.1F WPU0561 row-presence state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RECEIPT = "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-dispatch.json"
CONSUMPTION = (
    "governance/"
    "score-v2-1f-bls-wpu0561-row-presence-preflight-consumption-2026-10-28.json"
)
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/236"
RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40775867627"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    design = _load(
        root / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-design.json"
    )
    template = _load(
        root
        / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-authorization.template.json"
    )
    consumption = _load(root / CONSUMPTION)
    contract = _load(
        root
        / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-execution-contract.json"
    )
    rights = _load(root / "governance/score-publication-rights-gate.json")
    prereg = _load(root / "governance/score-v2-1f-preregistration.json")
    workflow = (
        root / ".github/workflows/score-v2-1f-bls-wpu0561-row-presence-preflight.yml"
    ).read_text(encoding="utf-8")

    for relative in (RECEIPT, DISPATCH):
        if (root / relative).exists():
            raise RuntimeError(f"consumed state must not retain {relative}")

    if rights.get("state") != "hold":
        raise RuntimeError("Score publication rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")

    if design.get("version") != 2 or design.get("state") != "design_only_hold":
        raise RuntimeError("frozen row-presence design changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("row-presence owner-decision issue changed")

    if template.get("version") != 2 or template.get("decision_status") != "hold":
        raise RuntimeError("authorization template must remain v2 HOLD")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template authorizations must remain false")

    if consumption.get("state") != "consumed_after_success":
        raise RuntimeError("row-presence consumption state changed")
    if consumption.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("consumption issue changed")
    if consumption.get("owner_approval_comment_id") != 6481426895:
        raise RuntimeError("owner approval evidence changed")
    if consumption.get("authorization_activation_merge_commit") != (
        "2fa7232ced1f578b6d11bf1d58c464753b9dfdeb"
    ):
        raise RuntimeError("activation merge evidence changed")
    if consumption.get("dispatch_merge_commit") != (
        "d8d317f7b298dff4ea339f3e866276b43150196d"
    ):
        raise RuntimeError("dispatch merge evidence changed")
    if consumption.get("preflight_run") != RUN:
        raise RuntimeError("preflight run evidence changed")
    if consumption.get("preflight_conclusion") != "success":
        raise RuntimeError("row-presence conclusion changed")
    if consumption.get("request_budget") != 2:
        raise RuntimeError("row-presence request budget changed")
    if consumption.get(
        "new_owner_authorization_required_for_any_future_live_request"
    ) is not True:
        raise RuntimeError("future live work must require a new owner authorization")

    result = consumption.get("sanitized_result", {})
    for field in (
        "structurally_identifiable",
        "html_2013_crude_petroleum_seen",
        "html_2013_05_61_seen",
        "xlsx_2026_crude_petroleum_seen",
    ):
        if result.get(field) is not True:
            raise RuntimeError(f"{field} pass evidence changed")
    if result.get("request_count") != 2:
        raise RuntimeError("sanitized request count changed")
    for field in (
        "response_bodies_persisted",
        "numeric_source_values_extracted",
        "numeric_source_values_logged",
        "numeric_source_values_persisted",
        "wpu0561_numeric_value_extracted",
        "full_historical_reconstruction_performed",
        "candidate_score_computed",
        "component_zscores_computed",
        "component_contributions_computed",
        "alternate_sources_used",
        "research_ledger_modified",
        "public_artifacts_modified",
        "production_modified",
    ):
        if result.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    post = consumption.get("post_consumption_authorizations", {})
    if not isinstance(post, dict) or any(post.values()):
        raise RuntimeError("all post-consumption authorizations must be false")

    if contract.get("state") != "row_presence_preflight_consumed_fail_closed":
        raise RuntimeError("execution contract is not consumed/fail-closed")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch must not be expected")
    if contract.get("completed_preflight_run") != RUN:
        raise RuntimeError("contract preflight run evidence changed")
    if contract.get("completed_preflight_conclusion") != "success":
        raise RuntimeError("contract preflight conclusion changed")
    if any(contract.get("current_state", {}).values()):
        raise RuntimeError("all contract authorization flags must be false")
    if contract.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if "if: ${{ false }}" not in workflow:
        raise RuntimeError("consumed row-presence workflow must remain inert")
    if "push:" in workflow:
        raise RuntimeError("consumed row-presence workflow must not retain a push trigger")

    return {
        "status": "passed",
        "state": "row_presence_preflight_consumed_fail_closed",
        "issue": ISSUE,
        "preflight_run": RUN,
        "preflight_conclusion": "success",
        "request_count": 2,
        "structurally_identifiable": True,
        "active_receipt_present": False,
        "dispatch_present": False,
        "response_body_ephemeral_retrieval_authorized": False,
        "row_presence_preflight_authorized": False,
        "source_value_extraction_authorized": False,
        "candidate_score_computation_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
