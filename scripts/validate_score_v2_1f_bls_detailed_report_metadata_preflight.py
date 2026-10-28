#!/usr/bin/env python3
"""Validate the design-only/HOLD Score v2.1F BLS metadata preflight packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

NEW_RECEIPT = "governance/score-v2-1f-bls-detailed-report-metadata-preflight-authorization.json"
NEW_DISPATCH = "governance/score-v2-1f-bls-detailed-report-metadata-preflight-dispatch.json"
OLD_RECEIPT = "governance/score-v2-1f-live-vintage-preflight-authorization.json"
OLD_DISPATCH = "governance/score-v2-1f-live-vintage-preflight-dispatch.json"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/230"
BLOCKER = "https://github.com/usdimpact/usd-impact-pipeline/issues/228"


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

    for relative in (NEW_RECEIPT, NEW_DISPATCH, OLD_RECEIPT, OLD_DISPATCH):
        if (root / relative).exists():
            raise RuntimeError(f"no active receipt/dispatch may exist in design-only state: {relative}")

    if rights.get("state") != "hold":
        raise RuntimeError("Score publication rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")
    if prior.get("new_owner_authorization_required_for_any_future_live_request") is not True:
        raise RuntimeError("prior Stage 1 consumption must continue to require new authorization")

    if design.get("state") != "design_only_hold":
        raise RuntimeError("BLS metadata design must remain HOLD")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("BLS metadata owner-decision issue changed")
    if design.get("blocker_issue") != BLOCKER:
        raise RuntimeError("BLS metadata blocker issue changed")
    if design.get("research_window") != {"start": "2013-01-01", "end": "2026-10-23"}:
        raise RuntimeError("BLS metadata research window changed")
    proposed = design.get("proposed_preflight", {})
    if proposed.get("request_budget") != 4:
        raise RuntimeError("BLS metadata request budget must remain four")
    if proposed.get("concurrency") != 1 or proposed.get("automatic_retries") != 0:
        raise RuntimeError("BLS metadata concurrency/retry policy changed")
    if proposed.get("allowed_hosts") != ["www.bls.gov"]:
        raise RuntimeError("BLS metadata allowed-host set changed")
    if design.get("current_authorizations", {}) and any(
        design["current_authorizations"].values()
    ):
        raise RuntimeError("all design-only authorizations must remain false")

    if template.get("decision_status") != "hold":
        raise RuntimeError("BLS metadata authorization template must remain HOLD")
    if template.get("issue") != ISSUE:
        raise RuntimeError("BLS metadata template issue changed")
    if template.get("data_window") != {"start": None, "end": None}:
        raise RuntimeError("HOLD template must not preselect a live window")
    if template.get("contact_user_agent") is not None:
        raise RuntimeError("HOLD template must not preselect contact identity")
    if template.get("approved_by") is not None or template.get("approved_at") is not None:
        raise RuntimeError("HOLD template may not contain approval evidence")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template authorizations must remain false")

    if contract.get("state") != "design_only_hold":
        raise RuntimeError("BLS metadata execution contract must remain HOLD")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch must not be expected")
    if contract.get("request_budget") != 4:
        raise RuntimeError("contract request budget changed")
    if any(contract.get("current_state", {}).values()):
        raise RuntimeError("all execution-contract authorization flags must remain false")
    if contract.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if "if: ${{ false }}" not in workflow:
        raise RuntimeError("BLS metadata workflow must remain inert in design-only state")

    return {
        "status": "passed",
        "state": "design_only_hold",
        "issue": ISSUE,
        "blocker_issue": BLOCKER,
        "request_budget": 4,
        "allowed_host": "www.bls.gov",
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
