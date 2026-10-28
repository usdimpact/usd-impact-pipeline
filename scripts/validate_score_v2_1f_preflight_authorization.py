#!/usr/bin/env python3
"""Validate dispatched Score v2.1F live-vintage preflight authorization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DESIGN_COMMIT = "e14aec35142b9536b5b889d0fae4eab9a94faf88"
PREREG_COMMIT = "bcf473e2bbcb36fa1080a3a56f77a3796d74ccaa"
ACTIVATION_COMMIT = "48f6815199db7c030939629f49a75001d20ae566"
ACTIVE_RECEIPT = "governance/score-v2-1f-live-vintage-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-live-vintage-preflight-dispatch.json"
APPROVAL_COMMENT = 6479715940
APPROVED_AT = "2026-10-28T20:20:28Z"
APPROVED_BY = "usdimpact owner via Issue #224 approval comment 6479715940"
EXPECTED_WINDOW = {"start": "2013-01-01", "end": "2026-10-23"}
EXPECTED_SERIES = [
    "H10/H10/JRXWTFB_N.B",
    "WPU0561",
    "H8/H8/B1001NCBA",
    "H41/H41/RESPPALDP_N.WW",
    "H41/H41/RESPPA_N.WW",
]

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
    receipt = _load(repo_root / ACTIVE_RECEIPT)
    dispatch = _load(repo_root / DISPATCH)
    contract = _load(
        repo_root / "governance/score-v2-1f-live-vintage-preflight-execution-contract.json"
    )
    prereg = _load(repo_root / "governance/score-v2-1f-preregistration.json")
    design = _load(repo_root / "governance/score-v2-1f-five-slot-design.json")
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")

    if hold.get("state") != "hold":
        raise RuntimeError("Score rights gate must remain HOLD")
    if design.get("state") != "design_only":
        raise RuntimeError("v2.1F design state changed")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")
    if prereg.get("design_merge_commit") != DESIGN_COMMIT:
        raise RuntimeError("v2.1F design pin changed")

    if template.get("decision_status") != "hold":
        raise RuntimeError("HOLD template must remain unchanged")
    if template.get("data_window") != {"start": None, "end": None}:
        raise RuntimeError("HOLD template may not preselect a live data window")
    if template.get("approved_by") is not None or template.get("approved_at") is not None:
        raise RuntimeError("HOLD template may not contain approval evidence")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template authorizations must remain false")

    if receipt.get("decision_status") != "approved":
        raise RuntimeError("active preflight receipt is not approved")
    if receipt.get("methodology_version") != "2.1F-design-candidate":
        raise RuntimeError("receipt methodology version changed")
    if receipt.get("issue") != "https://github.com/usdimpact/usd-impact-pipeline/issues/224":
        raise RuntimeError("receipt owner decision issue changed")
    if receipt.get("design_merge_commit") != DESIGN_COMMIT:
        raise RuntimeError("receipt design pin changed")
    if receipt.get("preregistration_merge_commit") != PREREG_COMMIT:
        raise RuntimeError("receipt preregistration pin changed")
    if receipt.get("execution_scope") != "live_historical_vintage_feasibility_preflight_only":
        raise RuntimeError("receipt execution scope changed")
    if receipt.get("exact_series") != EXPECTED_SERIES:
        raise RuntimeError("receipt exact-series inventory changed")
    if receipt.get("data_window") != EXPECTED_WINDOW:
        raise RuntimeError("receipt data window changed")
    if receipt.get("approved_by") != APPROVED_BY:
        raise RuntimeError("receipt approval identity/evidence changed")
    if receipt.get("approved_at") != APPROVED_AT:
        raise RuntimeError("receipt approval timestamp changed")

    auth = receipt.get("authorizations", {})
    if auth.get("real_data_fetch") is not True:
        raise RuntimeError("preflight receipt must authorize real-data fetch")
    if auth.get("live_vintage_preflight") is not True:
        raise RuntimeError("preflight receipt must authorize live vintage preflight")
    for field in (
        "real_data_research",
        "candidate_score_computation",
        "paid_data",
        "source_contract_acceptance",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if dispatch.get("version") != 1 or dispatch.get("state") != "dispatch_once":
        raise RuntimeError("dispatch marker state changed")
    if dispatch.get("phase") != "live_historical_vintage_feasibility_preflight":
        raise RuntimeError("dispatch phase changed")
    if dispatch.get("issue") != "https://github.com/usdimpact/usd-impact-pipeline/issues/224":
        raise RuntimeError("dispatch issue changed")
    if dispatch.get("authorization_activation_merge_commit") != ACTIVATION_COMMIT:
        raise RuntimeError("dispatch activation pin changed")
    if dispatch.get("exact_series") != EXPECTED_SERIES:
        raise RuntimeError("dispatch exact-series inventory changed")
    if dispatch.get("data_window") != EXPECTED_WINDOW:
        raise RuntimeError("dispatch data window changed")
    for field in (
        "candidate_score_computation_authorized",
        "full_candidate_research_authorized",
        "public_artifact_replacement_authorized",
        "research_ledger_mutation_authorized",
        "production_authorized",
    ):
        if dispatch.get(field) is not False:
            raise RuntimeError(f"{field} must remain false in dispatch")

    if contract.get("state") != "live_vintage_preflight_authorized":
        raise RuntimeError("execution contract must be dispatched-active")
    if contract.get("owner_approval_comment_id") != APPROVAL_COMMENT:
        raise RuntimeError("contract owner approval comment changed")
    if contract.get("owner_approval_timestamp") != APPROVED_AT:
        raise RuntimeError("contract owner approval timestamp changed")
    if contract.get("authorization_activation_merge_commit") != ACTIVATION_COMMIT:
        raise RuntimeError("contract activation merge pin changed")
    if contract.get("design_merge_commit") != DESIGN_COMMIT:
        raise RuntimeError("contract design pin changed")
    if contract.get("preregistration_merge_commit") != PREREG_COMMIT:
        raise RuntimeError("contract preregistration pin changed")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("active receipt must be expected")
    if contract.get("dispatch_marker_expected_now") is not True:
        raise RuntimeError("dispatch marker must be expected")
    if contract.get("authorized_data_window") != EXPECTED_WINDOW:
        raise RuntimeError("contract data window changed")
    if contract.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    current = contract.get("current_state", {})
    for field in (
        "real_data_fetch_authorized",
        "live_vintage_preflight_authorized",
        "active_receipt_present",
        "dispatch_marker_present",
    ):
        if current.get(field) is not True:
            raise RuntimeError(f"{field} must be true during dispatched preflight")
    for field in (
        "real_data_research_authorized",
        "candidate_score_computation_authorized",
        "paid_data_authorized",
        "source_contract_acceptance_authorized",
        "durable_private_storage_authorized",
        "public_artifact_replacement_authorized",
        "research_ledger_mutation_authorized",
        "production_authorized",
    ):
        if current.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    return {
        "status": "passed",
        "state": "live_vintage_preflight_authorized",
        "decision_status": "approved",
        "exact_series_count": len(EXPECTED_SERIES),
        "data_window": EXPECTED_WINDOW,
        "activation_merge_commit": ACTIVATION_COMMIT,
        "active_authorization_receipt_present": True,
        "dispatch_marker_present": True,
        "real_data_fetch_authorized": True,
        "live_vintage_preflight_authorized": True,
        "real_data_research_authorized": False,
        "candidate_score_computation_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }

def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
