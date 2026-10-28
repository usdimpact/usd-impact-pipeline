#!/usr/bin/env python3
"""Validate dispatched Score v2.1F BLS metadata preflight authorization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RECEIPT = "governance/score-v2-1f-bls-detailed-report-metadata-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-bls-detailed-report-metadata-preflight-dispatch.json"
OLD_RECEIPT = "governance/score-v2-1f-live-vintage-preflight-authorization.json"
OLD_DISPATCH = "governance/score-v2-1f-live-vintage-preflight-dispatch.json"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/230"
BLOCKER = "https://github.com/usdimpact/usd-impact-pipeline/issues/228"
APPROVAL_COMMENT = 6480432536
APPROVED_AT = "2026-10-28T20:53:16Z"
ACTIVATION_COMMIT = "59cd5e6b1cd47f3d04eec6588697d252ff93cff2"
EXPECTED_WINDOW = {"start": "2013-01-01", "end": "2026-10-23"}
EXPECTED_UA = "USD-Impact-Score-v2.1F-BLS-metadata-preflight/1.0 (contact: support@usd-impact.com)"


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
    receipt = _load(root / RECEIPT)
    dispatch = _load(root / DISPATCH)
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

    for relative in (OLD_RECEIPT, OLD_DISPATCH):
        if (root / relative).exists():
            raise RuntimeError(f"prior consumed Stage 1 state reactivated: {relative}")

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

    if receipt.get("decision_status") != "approved":
        raise RuntimeError("active BLS metadata receipt is not approved")
    if receipt.get("issue") != ISSUE or receipt.get("blocker_issue") != BLOCKER:
        raise RuntimeError("active BLS metadata receipt issue binding changed")
    if receipt.get("execution_scope") != "bls_detailed_report_metadata_preflight_only":
        raise RuntimeError("active BLS metadata receipt scope changed")
    if receipt.get("data_window") != EXPECTED_WINDOW:
        raise RuntimeError("active BLS metadata receipt window changed")
    if receipt.get("request_budget") != 4:
        raise RuntimeError("active BLS metadata request budget changed")
    if receipt.get("allowed_host") != "www.bls.gov":
        raise RuntimeError("active BLS metadata host changed")
    if receipt.get("contact_user_agent") != EXPECTED_UA:
        raise RuntimeError("contactable project User-Agent changed")
    if receipt.get("approved_by") != (
        "usdimpact owner via Issue #230 approval comment 6480432536"
    ):
        raise RuntimeError("active BLS metadata approval identity changed")
    if receipt.get("approved_at") != APPROVED_AT:
        raise RuntimeError("active BLS metadata approval timestamp changed")

    auth = receipt.get("authorizations", {})
    if auth.get("network_metadata_fetch") is not True:
        raise RuntimeError("network metadata fetch must be authorized")
    if auth.get("bls_metadata_preflight") is not True:
        raise RuntimeError("BLS metadata preflight must be authorized")
    for field in (
        "report_body_download",
        "source_value_retrieval",
        "real_data_research",
        "candidate_score_computation",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if dispatch.get("state") != "approved_dispatch":
        raise RuntimeError("dispatch marker state changed")
    if dispatch.get("phase") != "bls_detailed_report_metadata_preflight":
        raise RuntimeError("dispatch phase changed")
    if dispatch.get("issue") != ISSUE or dispatch.get("blocker_issue") != BLOCKER:
        raise RuntimeError("dispatch issue binding changed")
    if dispatch.get("authorization_activation_merge_commit") != ACTIVATION_COMMIT:
        raise RuntimeError("dispatch activation commit changed")
    if dispatch.get("data_window") != EXPECTED_WINDOW:
        raise RuntimeError("dispatch window changed")
    if dispatch.get("request_budget") != 4:
        raise RuntimeError("dispatch request budget changed")
    if dispatch.get("allowed_host") != "www.bls.gov":
        raise RuntimeError("dispatch host changed")
    for field in (
        "report_body_download_authorized",
        "source_value_retrieval_authorized",
        "real_data_research_authorized",
        "candidate_score_computation_authorized",
        "research_ledger_mutation_authorized",
        "public_artifact_replacement_authorized",
        "production_authorized",
    ):
        if dispatch.get(field) is not False:
            raise RuntimeError(f"{field} must remain false in dispatch")

    if contract.get("state") != "metadata_preflight_authorized":
        raise RuntimeError("execution contract must be dispatched-active")
    if contract.get("owner_approval_comment_id") != APPROVAL_COMMENT:
        raise RuntimeError("contract owner approval comment changed")
    if contract.get("owner_approval_timestamp") != APPROVED_AT:
        raise RuntimeError("contract owner approval timestamp changed")
    if contract.get("authorization_activation_merge_commit") != ACTIVATION_COMMIT:
        raise RuntimeError("contract activation commit changed")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("active receipt must be expected")
    if contract.get("dispatch_marker_expected_now") is not True:
        raise RuntimeError("dispatch must be expected")
    if contract.get("request_budget") != 4:
        raise RuntimeError("contract request budget changed")
    if contract.get("contact_user_agent") != EXPECTED_UA:
        raise RuntimeError("contract User-Agent changed")

    current = contract.get("current_state", {})
    for field in (
        "network_metadata_fetch_authorized",
        "bls_metadata_preflight_authorized",
    ):
        if current.get(field) is not True:
            raise RuntimeError(f"{field} must be true while dispatched")
    for field in (
        "report_body_download_authorized",
        "source_value_retrieval_authorized",
        "real_data_research_authorized",
        "candidate_score_computation_authorized",
        "research_ledger_mutation_authorized",
        "public_artifact_replacement_authorized",
        "production_authorized",
    ):
        if current.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if "score-v2-1f-bls-detailed-report-metadata-preflight-dispatch.json" not in workflow:
        raise RuntimeError("workflow is not path-gated to the dispatch marker")
    if "if: ${{ false }}" in workflow:
        raise RuntimeError("workflow must be active in the dispatched state")

    return {
        "status": "passed",
        "state": "metadata_preflight_authorized",
        "issue": ISSUE,
        "blocker_issue": BLOCKER,
        "activation_merge_commit": ACTIVATION_COMMIT,
        "request_budget": 4,
        "allowed_host": "www.bls.gov",
        "active_receipt_present": True,
        "dispatch_present": True,
        "network_metadata_fetch_authorized": True,
        "bls_metadata_preflight_authorized": True,
        "candidate_score_computation_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
