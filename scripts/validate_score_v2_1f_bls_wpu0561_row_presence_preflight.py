#!/usr/bin/env python3
"""Validate the design-only/HOLD Score v2.1F WPU0561 row-presence packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RECEIPT = "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-dispatch.json"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/236"
EXPECTED_RESOURCES = [
    "/ppi/detailed-report/ppi-detailed-report-april-2013.pdf",
    "/ppi/detailed-report/ppi-detailed-report-april-2026.xlsx",
]


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
    contract = _load(
        root
        / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-execution-contract.json"
    )
    metadata_consumption = _load(
        root
        / "governance/score-v2-1f-bls-detailed-report-metadata-preflight-consumption-2026-10-28.json"
    )
    rights = _load(root / "governance/score-publication-rights-gate.json")
    prereg = _load(root / "governance/score-v2-1f-preregistration.json")
    workflow = (
        root / ".github/workflows/score-v2-1f-bls-wpu0561-row-presence-preflight.yml"
    ).read_text(encoding="utf-8")

    for relative in (RECEIPT, DISPATCH):
        if (root / relative).exists():
            raise RuntimeError(f"design-only state must not retain {relative}")

    if metadata_consumption.get("state") != "consumed_after_success":
        raise RuntimeError("metadata preflight success/consumption evidence changed")
    if metadata_consumption.get(
        "new_owner_authorization_required_for_any_future_live_request"
    ) is not True:
        raise RuntimeError("future live work must continue to require new authorization")

    if rights.get("state") != "hold":
        raise RuntimeError("Score publication rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")

    if design.get("state") != "design_only_hold":
        raise RuntimeError("row-presence design must remain HOLD")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("row-presence owner-decision issue changed")
    if design.get("research_window") != {"start": "2013-01-01", "end": "2026-10-23"}:
        raise RuntimeError("row-presence research window changed")
    if design.get("request_policy", {}).get("request_budget") != 2:
        raise RuntimeError("row-presence request budget must remain two")
    if design.get("request_policy", {}).get("concurrency") != 1:
        raise RuntimeError("row-presence requests must remain serialized")
    if design.get("request_policy", {}).get("automatic_retries") != 0:
        raise RuntimeError("row-presence retries must remain disabled")
    if [
        item.get("path") for item in design.get("fixed_resources", [])
    ] != EXPECTED_RESOURCES:
        raise RuntimeError("row-presence fixed resources changed")
    if design.get("runtime_capability_policy", {}).get(
        "missing_pdftotext_behavior"
    ) != "fail_before_first_network_request":
        raise RuntimeError("missing PDF capability must fail before network")
    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("all design-only authorizations must remain false")

    if template.get("decision_status") != "hold":
        raise RuntimeError("row-presence authorization template must remain HOLD")
    if template.get("issue") != ISSUE:
        raise RuntimeError("row-presence authorization issue changed")
    if template.get("data_window") != {"start": None, "end": None}:
        raise RuntimeError("HOLD template must not preselect a live window")
    if template.get("request_budget") != 2:
        raise RuntimeError("HOLD template request budget changed")
    if template.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("HOLD template fixed resources changed")
    if template.get("contact_user_agent") is not None:
        raise RuntimeError("HOLD template must not preselect contact identity")
    if template.get("approved_by") is not None or template.get("approved_at") is not None:
        raise RuntimeError("HOLD template may not contain approval evidence")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template authorizations must remain false")

    if contract.get("state") != "design_only_hold":
        raise RuntimeError("row-presence execution contract must remain HOLD")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch must not be expected")
    if contract.get("request_budget") != 2:
        raise RuntimeError("contract request budget changed")
    if any(contract.get("current_state", {}).values()):
        raise RuntimeError("all execution authorization flags must remain false")
    if contract.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if "if: ${{ false }}" not in workflow:
        raise RuntimeError("row-presence workflow must remain inert")
    if "push:" in workflow:
        raise RuntimeError("design-only workflow must not have a push trigger")

    return {
        "status": "passed",
        "state": "design_only_hold",
        "issue": ISSUE,
        "request_budget": 2,
        "fixed_resources": EXPECTED_RESOURCES,
        "active_receipt_present": False,
        "dispatch_present": False,
        "report_body_ephemeral_retrieval_authorized": False,
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
