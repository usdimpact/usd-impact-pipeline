#!/usr/bin/env python3
"""Validate active-but-not-dispatched Score v2.1F WPU0561 row-presence authorization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RECEIPT = "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-dispatch.json"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/236"
APPROVAL_COMMENT = 6481426895
APPROVED_AT = "2026-10-28T21:44:04Z"
EXPECTED_WINDOW = {"start": "2013-01-01", "end": "2026-10-23"}
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
        root / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-design.json"
    )
    template = _load(
        root
        / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-authorization.template.json"
    )
    receipt = _load(root / RECEIPT)
    contract = _load(
        root
        / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-execution-contract.json"
    )
    rights = _load(root / "governance/score-publication-rights-gate.json")
    prereg = _load(root / "governance/score-v2-1f-preregistration.json")
    workflow = (
        root / ".github/workflows/score-v2-1f-bls-wpu0561-row-presence-preflight.yml"
    ).read_text(encoding="utf-8")

    if (root / DISPATCH).exists():
        raise RuntimeError("dispatch must remain absent before separate review")

    if rights.get("state") != "hold":
        raise RuntimeError("Score publication rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")

    if design.get("version") != 2 or design.get("state") != "design_only_hold":
        raise RuntimeError("frozen row-presence design changed")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("row-presence owner-decision issue changed")
    if [item.get("path") for item in design.get("fixed_resources", [])] != EXPECTED_RESOURCES:
        raise RuntimeError("row-presence fixed resources changed")
    parser_policy = design.get("runtime_parser_policy", {})
    if parser_policy.get("html_parser") != "python_standard_library_html_parser_only":
        raise RuntimeError("HTML parser policy changed")
    if parser_policy.get("xlsx_parser") != "python_standard_library_zip_xml_only":
        raise RuntimeError("XLSX parser policy changed")
    if parser_policy.get("install_new_system_software") is not False:
        raise RuntimeError("new system software must remain forbidden")
    if parser_policy.get("install_new_python_dependency") is not False:
        raise RuntimeError("new Python dependencies must remain forbidden")

    if template.get("version") != 2 or template.get("decision_status") != "hold":
        raise RuntimeError("authorization template must remain v2 HOLD")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template authorizations must remain false")

    if receipt.get("version") != 2 or receipt.get("decision_status") != "approved":
        raise RuntimeError("active row-presence receipt is invalid")
    if receipt.get("issue") != ISSUE:
        raise RuntimeError("active row-presence receipt issue changed")
    if receipt.get("execution_scope") != "bls_wpu0561_row_presence_preflight_only":
        raise RuntimeError("active row-presence scope changed")
    if receipt.get("data_window") != EXPECTED_WINDOW:
        raise RuntimeError("active row-presence window changed")
    if receipt.get("request_budget") != 2:
        raise RuntimeError("active row-presence request budget changed")
    if receipt.get("allowed_host") != "www.bls.gov":
        raise RuntimeError("active row-presence host changed")
    if receipt.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("active row-presence resources changed")
    if receipt.get("approved_by") != "usdimpact owner via Issue #236 approval comment 6481426895":
        raise RuntimeError("active row-presence approval identity changed")
    if receipt.get("approved_at") != APPROVED_AT:
        raise RuntimeError("active row-presence approval timestamp changed")
    if "contact:" not in str(receipt.get("contact_user_agent", "")):
        raise RuntimeError("contactable project User-Agent missing")

    auth = receipt.get("authorizations", {})
    if auth.get("response_body_ephemeral_retrieval") is not True:
        raise RuntimeError("ephemeral response-body retrieval must be authorized")
    if auth.get("row_presence_preflight") is not True:
        raise RuntimeError("row-presence preflight must be authorized")
    for field in (
        "source_value_extraction",
        "real_data_research",
        "full_historical_reconstruction",
        "candidate_score_computation",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if contract.get("version") != 2:
        raise RuntimeError("row-presence contract version changed")
    if contract.get("state") != "row_presence_preflight_authorized_pending_dispatch":
        raise RuntimeError("execution contract must be active but pending dispatch")
    if contract.get("owner_approval_comment_id") != APPROVAL_COMMENT:
        raise RuntimeError("contract owner approval comment changed")
    if contract.get("owner_approval_timestamp") != APPROVED_AT:
        raise RuntimeError("contract owner approval timestamp changed")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("active receipt must be expected after activation")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch must remain absent before separate review")
    if contract.get("request_budget") != 2:
        raise RuntimeError("contract request budget changed")
    if contract.get("fixed_resources") != EXPECTED_RESOURCES:
        raise RuntimeError("contract resources changed")
    current = contract.get("current_state", {})
    if current.get("response_body_ephemeral_retrieval_authorized") is not True:
        raise RuntimeError("response-body retrieval contract flag must be true")
    if current.get("row_presence_preflight_authorized") is not True:
        raise RuntimeError("row-presence contract flag must be true")
    for field in (
        "source_value_extraction_authorized",
        "real_data_research_authorized",
        "full_historical_reconstruction_authorized",
        "candidate_score_computation_authorized",
        "research_ledger_mutation_authorized",
        "public_artifact_replacement_authorized",
        "production_authorized",
    ):
        if current.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if "if: ${{ false }}" not in workflow:
        raise RuntimeError("row-presence workflow must remain inert until dispatch")
    if "push:" in workflow:
        raise RuntimeError("row-presence workflow must not have push trigger before dispatch")

    return {
        "status": "passed",
        "state": "row_presence_preflight_authorized_pending_dispatch",
        "version": 2,
        "issue": ISSUE,
        "request_budget": 2,
        "fixed_resources": EXPECTED_RESOURCES,
        "standard_library_only": True,
        "active_receipt_present": True,
        "dispatch_present": False,
        "response_body_ephemeral_retrieval_authorized": True,
        "row_presence_preflight_authorized": True,
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
