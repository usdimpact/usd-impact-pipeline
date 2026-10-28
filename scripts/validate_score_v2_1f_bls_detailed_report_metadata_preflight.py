#!/usr/bin/env python3
"""Validate consumed/fail-closed Score v2.1F BLS metadata preflight state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RECEIPT = "governance/score-v2-1f-bls-detailed-report-metadata-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-bls-detailed-report-metadata-preflight-dispatch.json"
CONSUMPTION = (
    "governance/"
    "score-v2-1f-bls-detailed-report-metadata-preflight-consumption-2026-10-28.json"
)
OLD_RECEIPT = "governance/score-v2-1f-live-vintage-preflight-authorization.json"
OLD_DISPATCH = "governance/score-v2-1f-live-vintage-preflight-dispatch.json"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/230"
BLOCKER = "https://github.com/usdimpact/usd-impact-pipeline/issues/228"
RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40768295606"
ACTIVATION_COMMIT = "59cd5e6b1cd47f3d04eec6588697d252ff93cff2"
DISPATCH_COMMIT = "8348c276ecc12053501f444d9a55e1c6572612f5"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    design = _load(
        root / "governance/score-v2-1f-bls-detailed-report-metadata-preflight-design.json"
    )
    template = _load(
        root
        / "governance/score-v2-1f-bls-detailed-report-metadata-preflight-authorization.template.json"
    )
    consumption = _load(root / CONSUMPTION)
    contract = _load(
        root
        / "governance/score-v2-1f-bls-detailed-report-metadata-preflight-execution-contract.json"
    )
    prior = _load(
        root / "governance/score-v2-1f-live-vintage-preflight-consumption-2026-10-28.json"
    )
    rights = _load(root / "governance/score-publication-rights-gate.json")
    prereg = _load(root / "governance/score-v2-1f-preregistration.json")
    workflow = (
        root / ".github/workflows/score-v2-1f-bls-detailed-report-metadata-preflight.yml"
    ).read_text(encoding="utf-8")

    for relative in (RECEIPT, DISPATCH, OLD_RECEIPT, OLD_DISPATCH):
        if (root / relative).exists():
            raise RuntimeError(f"consumed authorization state must not retain {relative}")

    if rights.get("state") != "hold":
        raise RuntimeError("Score publication rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")
    if prior.get("new_owner_authorization_required_for_any_future_live_request") is not True:
        raise RuntimeError("prior Stage 1 consumption evidence changed")

    if design.get("state") != "design_only_hold":
        raise RuntimeError("frozen BLS metadata design artifact changed")
    if design.get("owner_decision_issue") != ISSUE or design.get("blocker_issue") != BLOCKER:
        raise RuntimeError("BLS metadata design issue binding changed")

    if template.get("decision_status") != "hold":
        raise RuntimeError("authorization template must remain HOLD")
    if template.get("data_window") != {"start": None, "end": None}:
        raise RuntimeError("HOLD template may not preselect a live window")
    if template.get("contact_user_agent") is not None:
        raise RuntimeError("HOLD template may not preselect contact identity")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template authorizations must remain false")

    if consumption.get("state") != "consumed_after_success":
        raise RuntimeError("metadata preflight consumption state changed")
    if consumption.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("consumption owner decision issue changed")
    if consumption.get("blocker_issue") != BLOCKER:
        raise RuntimeError("consumption blocker issue changed")
    if consumption.get("owner_approval_comment_id") != 6480432536:
        raise RuntimeError("owner approval evidence changed")
    if consumption.get("authorization_activation_merge_commit") != ACTIVATION_COMMIT:
        raise RuntimeError("activation merge evidence changed")
    if consumption.get("dispatch_merge_commit") != DISPATCH_COMMIT:
        raise RuntimeError("dispatch merge evidence changed")
    if consumption.get("preflight_run") != RUN:
        raise RuntimeError("preflight run evidence changed")
    if consumption.get("preflight_conclusion") != "success":
        raise RuntimeError("metadata preflight conclusion changed")
    if consumption.get("request_budget") != 4:
        raise RuntimeError("metadata preflight request budget changed")
    if consumption.get("new_owner_authorization_required_for_any_future_live_request") is not True:
        raise RuntimeError("future live work must require a new owner authorization")

    result = consumption.get("sanitized_result", {})
    expected_true = (
        "report_resource_2013_present",
        "report_resource_2026_present",
        "october_2025_not_available_label_seen",
        "february_2016_correction_label_seen",
    )
    for field in expected_true:
        if result.get(field) is not True:
            raise RuntimeError(f"{field} pass evidence changed")
    if result.get("request_count") != 4:
        raise RuntimeError("sanitized request count changed")
    for field in (
        "report_bodies_downloaded",
        "source_values_retrieved",
        "candidate_score_computed",
        "component_zscores_computed",
        "component_contributions_computed",
        "alternate_sources_used",
        "public_artifacts_modified",
        "research_ledgers_modified",
        "production_modified",
    ):
        if result.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    post = consumption.get("post_consumption_authorizations", {})
    if not isinstance(post, dict) or any(post.values()):
        raise RuntimeError("all post-consumption authorizations must be false")

    if contract.get("state") != "metadata_preflight_consumed_fail_closed":
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
        raise RuntimeError("all contract authorization flags must be false after consumption")
    if contract.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if "if: ${{ false }}" not in workflow:
        raise RuntimeError("consumed BLS metadata workflow must remain inert")
    if "push:" in workflow:
        raise RuntimeError("consumed BLS metadata workflow must not retain a push trigger")

    return {
        "status": "passed",
        "state": "metadata_preflight_consumed_fail_closed",
        "issue": ISSUE,
        "blocker_issue": BLOCKER,
        "preflight_run": RUN,
        "preflight_conclusion": "success",
        "request_count": 4,
        "report_resource_2013_present": True,
        "report_resource_2026_present": True,
        "october_2025_not_available_label_seen": True,
        "february_2016_correction_label_seen": True,
        "active_receipt_present": False,
        "dispatch_present": False,
        "network_metadata_fetch_authorized": False,
        "bls_metadata_preflight_authorized": False,
        "candidate_score_computation_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
