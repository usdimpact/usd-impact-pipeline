#!/usr/bin/env python3
"""Validate Issue #258 v6 design-only exact-label/context state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
V5_RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40794631448"
DESIGN = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json"
TEMPLATE = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json"
RECEIPT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
DISPATCH = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
CONTRACT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json"
CONSUMPTION = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-v5-candidate-context-consumption-2026-10-29.json"
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
            raise RuntimeError(f"v6 design-only state must not retain {relative}")

    if rights.get("state") != "hold":
        raise RuntimeError("Issue #155 rights gate must remain HOLD")
    if template.get("decision_status") != "hold" or any(template.get("authorizations", {}).values()):
        raise RuntimeError("authorization template must remain HOLD")

    if consumption.get("state") != "consumed_after_completed_v5_candidate_context_inventory":
        raise RuntimeError("v5 consumption state changed")
    if consumption.get("design_version") != 5:
        raise RuntimeError("v5 consumption design version changed")
    if consumption.get("preflight_run") != V5_RUN:
        raise RuntimeError("v5 run evidence changed")
    if consumption.get("preflight_workflow_conclusion") != "success":
        raise RuntimeError("v5 workflow conclusion changed")
    result = consumption.get("sanitized_result", {})
    if result.get("request_attempt_count") != 2:
        raise RuntimeError("v5 request attempt count changed")
    if result.get("economic_observation_count") != 0:
        raise RuntimeError("v5 economic observation count changed")
    if result.get("identifier_value_count") != 0:
        raise RuntimeError("v5 identifier value count changed")
    if result.get("html", {}).get("candidate_count") != 3:
        raise RuntimeError("v5 HTML candidate count changed")
    if result.get("xlsx", {}).get("candidate_count") != 29:
        raise RuntimeError("v5 XLSX candidate count changed")
    if any(consumption.get("post_consumption_authorizations", {}).values()):
        raise RuntimeError("all post-v5 authorizations must remain false")
    if consumption.get("new_owner_authorization_required_for_any_future_live_request") is not True:
        raise RuntimeError("future live BLS work must require new owner authorization")

    if design.get("version") != 6 or design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 v6 design changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("Issue #258 design issue changed")
    if design.get("future_live_budget", {}).get("request_budget") != 2:
        raise RuntimeError("future request budget changed")
    if design.get("future_live_budget", {}).get("max_economic_observations_total") != 0:
        raise RuntimeError("future economic observation budget changed")
    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("all v6 design authorization flags must remain false")

    evidence = design.get("known_consumed_evidence", {})
    expected_evidence = {
        "issue_258_v5_run": V5_RUN,
        "issue_258_v5_html_candidate_count": 3,
        "issue_258_v5_xlsx_candidate_count": 29,
        "issue_258_v5_identifier_value_count": 0,
        "issue_258_v5_economic_observation_count": 0,
        "v5_exact_label_html_survivors": 1,
        "v5_exact_label_xlsx_survivors": 2,
        "v5_html_exact_label_coordinate": "table 4 row 226",
    }
    for key, value in expected_evidence.items():
        if evidence.get(key) != value:
            raise RuntimeError(f"v6 consumed evidence changed: {key}")
    if evidence.get("v5_xlsx_exact_label_coordinates") != [
        "xl/worksheets/sheet3.xml row 289",
        "xl/worksheets/sheet3.xml row 527",
    ]:
        raise RuntimeError("v6 XLSX exact-label coordinates changed")

    exact = design.get("exact_label_candidate_policy", {})
    if exact.get("state") != "design_only_not_live_authorized":
        raise RuntimeError("exact-label policy must remain design-only")
    if exact.get("regex") != r"^Crude\s+petroleum(?:\s*\(\s*<num>\s*\))?$":
        raise RuntimeError("exact-label regex changed")
    if exact.get("row_number_as_selector") is not False:
        raise RuntimeError("row numbers must not be selectors")
    if exact.get("expected_html_narrowing") != "3 -> 1":
        raise RuntimeError("HTML narrowing evidence changed")
    if exact.get("expected_xlsx_narrowing") != "29 -> 2":
        raise RuntimeError("XLSX narrowing evidence changed")
    if exact.get("identity_proven_by_this_rule") is not False:
        raise RuntimeError("exact-label rule must not prove identity")

    discriminator = design.get("xlsx_context_discriminator_policy", {})
    if discriminator.get("state") != "design_only_not_live_authorized":
        raise RuntimeError("XLSX context discriminator must remain design-only")
    if discriminator.get("lookback_rows") != 8:
        raise RuntimeError("XLSX context lookback changed")
    if discriminator.get("direct_commodity_marker") != "Unprocessed nonfood materials":
        raise RuntimeError("direct commodity marker changed")
    if discriminator.get("stage_demand_marker") != "Stage <num> intermediate demand":
        raise RuntimeError("stage-demand marker changed")
    if discriminator.get("expected_direct_commodity_survivors") != 1:
        raise RuntimeError("expected direct commodity survivor count changed")
    if discriminator.get("row_number_as_selector") is not False:
        raise RuntimeError("row numbers must not be selectors")
    if discriminator.get("identifier_read_required") is not False:
        raise RuntimeError("v6 design must not require identifier reads")
    if discriminator.get("economic_value_read_required") is not False:
        raise RuntimeError("v6 design must not require economic-value reads")
    if discriminator.get("identity_proven_by_this_rule") is not False:
        raise RuntimeError("v6 context discriminator must not prove identity")
    if discriminator.get("live_verification_status") != "not_authorized":
        raise RuntimeError("v6 live verification must remain unauthorized")

    if contract.get("version") != 12:
        raise RuntimeError("v6 contract version changed")
    if contract.get("state") != "ambiguity_diagnostics_v6_exact_label_context_design_only_hold":
        raise RuntimeError("v6 contract must remain design-only HOLD")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch marker must not be expected")
    if any(contract.get("current_state", {}).values()):
        raise RuntimeError("all contract authorization flags must remain false")
    if contract.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if ("if: $" + "{{ false }}") not in workflow:
        raise RuntimeError("workflow must remain inert")
    if "push:" in workflow:
        raise RuntimeError("v6 design-only workflow must not have a push trigger")

    return {
        "status": "passed",
        "state": "ambiguity_diagnostics_v6_exact_label_context_design_only_hold",
        "design_version": 6,
        "v5_preflight_run": V5_RUN,
        "v5_html_candidates": 3,
        "v5_xlsx_candidates": 29,
        "v6_html_exact_label_survivors": 1,
        "v6_xlsx_exact_label_survivors": 2,
        "v6_xlsx_direct_commodity_survivors": 1,
        "v6_xlsx_stage_demand_survivors": 1,
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
