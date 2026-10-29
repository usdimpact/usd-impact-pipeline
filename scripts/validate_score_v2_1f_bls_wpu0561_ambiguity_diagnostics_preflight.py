#!/usr/bin/env python3
"""Validate Issue #258 v8 design-only container header-band state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
V7_RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40897338145"
DESIGN = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json"
TEMPLATE = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json"
RECEIPT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
DISPATCH = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
CONTRACT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json"
CONSUMPTION = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-v7-header-gap-consumption-2026-10-29.json"
WORKFLOW = ROOT / ".github/workflows/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight.yml"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path | None = None) -> dict[str, Any]:
    root = (repo_root or ROOT).resolve()
    design = _load(root / DESIGN.relative_to(ROOT))
    template = _load(root / TEMPLATE.relative_to(ROOT))
    contract = _load(root / CONTRACT.relative_to(ROOT))
    consumption = _load(root / CONSUMPTION.relative_to(ROOT))
    rights = _load(root / "governance/score-publication-rights-gate.json")
    workflow = (root / WORKFLOW.relative_to(ROOT)).read_text(encoding="utf-8")

    for relative in (RECEIPT.relative_to(ROOT), DISPATCH.relative_to(ROOT)):
        if (root / relative).exists():
            raise RuntimeError(f"v8 design-only state must not retain {relative}")

    if rights.get("state") != "hold":
        raise RuntimeError("Issue #155 rights gate must remain HOLD")
    if template.get("decision_status") != "hold" or any(template.get("authorizations", {}).values()):
        raise RuntimeError("authorization template must remain HOLD")

    if consumption.get("state") != "consumed_after_completed_v7_header_gap_inventory":
        raise RuntimeError("v7 consumption evidence changed")
    if consumption.get("preflight_run") != V7_RUN:
        raise RuntimeError("v7 run evidence changed")
    result = consumption.get("sanitized_result", {})
    if result.get("request_attempt_count") != 2:
        raise RuntimeError("v7 request count changed")
    if result.get("identifier_values_retained") is not False:
        raise RuntimeError("v7 identifier safeguard changed")
    if result.get("economic_values_retained") is not False:
        raise RuntimeError("v7 economic safeguard changed")
    if result.get("html", {}).get("nearest_recognized_header_row") is not None:
        raise RuntimeError("v7 HTML header-gap result changed")
    if result.get("xlsx", {}).get("nearest_recognized_header_row") is not None:
        raise RuntimeError("v7 XLSX header-gap result changed")
    if any(consumption.get("post_consumption_authorizations", {}).values()):
        raise RuntimeError("all post-v7 authorizations must remain false")
    if consumption.get("new_owner_authorization_required_for_any_future_live_request") is not True:
        raise RuntimeError("future live work must require new owner authorization")

    if design.get("version") != 8 or design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 v8 design changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("Issue #258 design issue changed")
    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("all v8 design authorization flags must remain false")

    evidence = design.get("known_consumed_evidence", {})
    if evidence.get("issue_258_v7_run") != V7_RUN:
        raise RuntimeError("v7 run evidence missing from v8 design")
    if evidence.get("issue_258_v7_html_nearest_recognized_header_row") is not None:
        raise RuntimeError("v8 HTML predecessor evidence changed")
    if evidence.get("issue_258_v7_xlsx_nearest_recognized_header_row") is not None:
        raise RuntimeError("v8 XLSX predecessor evidence changed")

    policy = design.get("container_header_band_policy", {})
    if policy.get("state") != "design_only_not_live_authorized":
        raise RuntimeError("v8 header-band policy must remain design-only")
    if policy.get("candidate_row_as_selector") is not False:
        raise RuntimeError("candidate row must not be a selector")
    if policy.get("inspect_top_rows") != 32:
        raise RuntimeError("v8 top-row bound changed")
    if policy.get("maximum_persisted_text_cells_per_selected_container") != 128:
        raise RuntimeError("v8 cell bound changed")
    if policy.get("identifier_values") != "forbidden":
        raise RuntimeError("v8 identifier-value policy changed")
    if policy.get("economic_values") != "forbidden":
        raise RuntimeError("v8 economic-value policy changed")
    if policy.get("response_body_persistence") is not False:
        raise RuntimeError("v8 response-body persistence changed")
    if policy.get("identity_proven_by_this_rule") is not False:
        raise RuntimeError("v8 header band must not prove identity")
    if policy.get("live_verification_status") != "not_authorized":
        raise RuntimeError("v8 live verification must remain unauthorized")

    if contract.get("version") != 17:
        raise RuntimeError("v8 contract version changed")
    if contract.get("state") != "ambiguity_diagnostics_v8_container_header_band_design_only_hold":
        raise RuntimeError("v8 contract must remain design-only HOLD")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch must not be expected")
    if any(contract.get("current_state", {}).values()):
        raise RuntimeError("all contract authorization flags must remain false")
    if contract.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if ("if: $" + "{{ false }}") not in workflow:
        raise RuntimeError("workflow must remain inert")
    if "push:" in workflow:
        raise RuntimeError("v8 design-only workflow must not have a push trigger")

    return {
        "status": "passed",
        "state": "ambiguity_diagnostics_v8_container_header_band_design_only_hold",
        "design_version": 8,
        "v7_preflight_run": V7_RUN,
        "v7_html_nearest_header_row": None,
        "v7_xlsx_nearest_header_row": None,
        "v8_header_band_top_rows": 32,
        "v8_header_band_max_cells": 128,
        "active_receipt_present": False,
        "dispatch_present": False,
        "live_request_authorized": False,
        "identifier_value_read_authorized": False,
        "economic_value_read_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
