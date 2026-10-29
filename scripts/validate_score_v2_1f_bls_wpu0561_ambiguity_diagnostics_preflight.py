#!/usr/bin/env python3
"""Validate Issue #258 v9 structural-feasibility design-only HOLD."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
V8_RUN = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40901086765"
DESIGN = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json"
TEMPLATE = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json"
RECEIPT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
DISPATCH = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
CONTRACT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json"
CONSUMPTION = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-v8-container-header-band-consumption-2026-10-29.json"
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
            raise RuntimeError(f"v9 design-only state must not retain {relative}")

    if rights.get("state") != "hold":
        raise RuntimeError("Issue #155 rights gate must remain HOLD")
    if template.get("decision_status") != "hold" or any(template.get("authorizations", {}).values()):
        raise RuntimeError("authorization template must remain HOLD")

    if consumption.get("state") != "consumed_after_completed_v8_container_header_band_inventory":
        raise RuntimeError("v8 consumption state changed")
    if consumption.get("design_version") != 8:
        raise RuntimeError("v8 consumption design version changed")
    if consumption.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("consumption issue changed")
    if consumption.get("preflight_run") != V8_RUN:
        raise RuntimeError("v8 run evidence changed")
    if consumption.get("preflight_workflow_conclusion") != "success":
        raise RuntimeError("v8 workflow conclusion changed")
    if consumption.get("preflight_result_status") != "completed":
        raise RuntimeError("v8 result status changed")

    result = consumption.get("sanitized_result", {})
    if result.get("request_attempt_count") != 2:
        raise RuntimeError("v8 request attempt count changed")
    if result.get("identifier_values_retained") is not False:
        raise RuntimeError("identifier safeguard changed")
    if result.get("economic_values_retained") is not False:
        raise RuntimeError("economic safeguard changed")

    html = result.get("html", {})
    xlsx = result.get("xlsx", {})
    if html.get("container") != "table 4":
        raise RuntimeError("HTML container evidence changed")
    if "index_level" not in html.get("structural_roles", []):
        raise RuntimeError("HTML index-level evidence changed")
    if xlsx.get("container") != "xl/worksheets/sheet3.xml":
        raise RuntimeError("XLSX container evidence changed")
    if xlsx.get("index_level_column_observed_in_header_band") is not False:
        raise RuntimeError("XLSX index-level absence evidence changed")

    for field in (
        "alternate_sources_used",
        "full_historical_reconstruction_performed",
        "candidate_score_computed",
        "component_zscores_computed",
        "component_contributions_computed",
        "research_ledger_modified",
        "public_artifacts_modified",
        "production_modified",
    ):
        if result.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if any(consumption.get("post_consumption_authorizations", {}).values()):
        raise RuntimeError("all post-v8 authorizations must remain false")

    if design.get("version") != 9 or design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 v9 design changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("Issue #258 design issue changed")
    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("all v9 design authorization flags must remain false")

    evidence = design.get("known_consumed_evidence", {})
    expected = {
        "issue_258_v8_run": V8_RUN,
        "issue_258_v8_html_container": "table 4",
        "issue_258_v8_html_index_level_field_present": True,
        "issue_258_v8_html_identifier_field_present": True,
        "issue_258_v8_xlsx_container": "xl/worksheets/sheet3.xml",
        "issue_258_v8_xlsx_index_level_field_present": False,
        "issue_258_v8_xlsx_percent_change_fields_present": True,
        "issue_258_v8_identifier_values_retained": False,
        "issue_258_v8_economic_values_retained": False,
    }
    for key, value in expected.items():
        if evidence.get(key) != value:
            raise RuntimeError(f"v9 consumed evidence changed: {key}")

    policy = design.get("structural_feasibility_policy", {})
    if policy.get("state") != "design_only_hold":
        raise RuntimeError("v9 structural-feasibility policy must remain HOLD")

    html_policy = policy.get("html_2013", {})
    if html_policy.get("structural_status") != "index_level_schema_present":
        raise RuntimeError("2013 HTML structural status changed")
    if html_policy.get("identifier_header_present") is not True:
        raise RuntimeError("2013 HTML identifier-header evidence changed")
    if html_policy.get("index_level_header_present") is not True:
        raise RuntimeError("2013 HTML index-level evidence changed")
    if html_policy.get("representative_value_read_authorized") is not False:
        raise RuntimeError("2013 representative value read must remain unauthorized")

    xlsx_policy = policy.get("xlsx_2026", {})
    if xlsx_policy.get("structural_status") != "index_level_schema_absent_in_selected_container":
        raise RuntimeError("2026 XLSX structural status changed")
    if xlsx_policy.get("index_level_header_present") is not False:
        raise RuntimeError("2026 XLSX index-level field must remain absent")
    if xlsx_policy.get("percent_change_headers_present") is not True:
        raise RuntimeError("2026 XLSX percent-change evidence changed")
    if xlsx_policy.get("representative_value_read_authorized") is not False:
        raise RuntimeError("2026 representative value read must remain unauthorized")

    if "Do not broaden" not in policy.get("no_broadening_rule", ""):
        raise RuntimeError("v9 no-broadening rule changed")
    if "No alternate source" not in policy.get("alternate_source_rule", ""):
        raise RuntimeError("v9 alternate-source rule changed")
    if "not_feasible_for_two_resource_representative_index_level_pair" not in policy.get(
        "current_pairwise_feasibility", ""
    ):
        raise RuntimeError("v9 pairwise feasibility decision changed")
    if policy.get("html_only_feasibility") != "structurally_possible_but_not_authorized_for_value_read":
        raise RuntimeError("v9 HTML-only feasibility changed")
    if policy.get("xlsx_2026_feasibility") != "structurally_blocked_for_index_level_value_read":
        raise RuntimeError("v9 XLSX feasibility changed")
    if policy.get("score_candidate_status") != "hold":
        raise RuntimeError("Score candidate must remain HOLD")
    if policy.get("public_or_production_status") != "forbidden":
        raise RuntimeError("public/Production must remain forbidden")

    options = design.get("successor_options", {})
    if "fails closed" not in options.get("option_a", ""):
        raise RuntimeError("v9 option A changed")
    if "new methodology decision" not in options.get("option_b", ""):
        raise RuntimeError("v9 option B changed")
    if "search concept variants" not in options.get("forbidden_shortcut", ""):
        raise RuntimeError("v9 forbidden shortcut changed")

    if contract.get("version") != 21:
        raise RuntimeError("v9 contract version changed")
    if contract.get("state") != "ambiguity_diagnostics_v9_structural_feasibility_design_only_hold":
        raise RuntimeError("v9 contract must remain design-only HOLD")
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
        raise RuntimeError("v9 design-only workflow must not have a push trigger")

    return {
        "status": "passed",
        "state": "ambiguity_diagnostics_v9_structural_feasibility_design_only_hold",
        "design_version": 9,
        "v8_preflight_run": V8_RUN,
        "html_index_level_schema_present": True,
        "xlsx_selected_container_index_level_schema_present": False,
        "pairwise_representative_index_level_feasible": False,
        "live_request_authorized": False,
        "identifier_value_read_authorized": False,
        "economic_value_read_authorized": False,
        "candidate_score_computation_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
