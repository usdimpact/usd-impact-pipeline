#!/usr/bin/env python3
"""Validate design-only/HOLD WPU0561 column-semantics preflight packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RECEIPT = "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-dispatch.json"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/244"
EXPECTED_RESOURCES = [
    "/news.release/archives/ppi_05152013.htm",
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
        root / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-design.json"
    )
    template = _load(
        root
        / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-authorization.template.json"
    )
    contract = _load(
        root
        / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-execution-contract.json"
    )
    prior = _load(
        root
        / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-consumption-2026-10-28.json"
    )
    rights = _load(root / "governance/score-publication-rights-gate.json")
    prereg = _load(root / "governance/score-v2-1f-preregistration.json")
    workflow = (
        root / ".github/workflows/score-v2-1f-bls-wpu0561-column-semantics-preflight.yml"
    ).read_text(encoding="utf-8")

    for relative in (RECEIPT, DISPATCH):
        if (root / relative).exists():
            raise RuntimeError(f"design-only state must not retain {relative}")

    if prior.get("state") != "consumed_after_success":
        raise RuntimeError("row-presence consumption evidence changed")
    if prior.get("new_owner_authorization_required_for_any_future_live_request") is not True:
        raise RuntimeError("future live work must continue to require new authorization")

    if rights.get("state") != "hold":
        raise RuntimeError("Score publication rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")

    if design.get("state") != "design_only_hold":
        raise RuntimeError("column-semantics design must remain HOLD")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("column-semantics issue changed")
    if [item.get("path") for item in design.get("fixed_resources", [])] != EXPECTED_RESOURCES:
        raise RuntimeError("column-semantics fixed resources changed")
    if design.get("request_policy", {}).get("request_budget") != 2:
        raise RuntimeError("column-semantics request budget changed")
    if design.get("request_policy", {}).get("automatic_retries") != 0:
        raise RuntimeError("column-semantics retries must remain disabled")
    if design.get("identifier_policy", {}).get("ambiguous_cell_behavior") != (
        "discard_value_emit_ambiguity_only"
    ):
        raise RuntimeError("ambiguous-cell behavior changed")
    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("all design authorizations must remain false")

    if template.get("decision_status") != "hold":
        raise RuntimeError("column-semantics template must remain HOLD")
    if template.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("column-semantics template resources changed")
    if template.get("contact_user_agent") is not None:
        raise RuntimeError("HOLD template must not preselect contact identity")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template authorizations must remain false")

    if contract.get("state") != "design_only_hold":
        raise RuntimeError("column-semantics contract must remain HOLD")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch must not be expected")
    if contract.get("request_budget") != 2:
        raise RuntimeError("contract request budget changed")
    if any(contract.get("current_state", {}).values()):
        raise RuntimeError("all contract authorization flags must remain false")
    if contract.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if "if: ${{ false }}" not in workflow:
        raise RuntimeError("column-semantics workflow must remain inert")
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
