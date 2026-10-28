#!/usr/bin/env python3
"""Validate the approved, fail-closed Score v2.1E one-off research authorization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_SERIES = [
    "H10/H10/JRXWTFB_N.B",
    "WPU0561",
    "H8/H8/B1001NCBA",
    "H41/H41/RESPPALDP_N.WW",
    "H41/H41/RESPPA_N.WW",
    "H15/H15/RIFLGFCY10_XII_N.B",
    "H15/H15/RIFLGFCY02_N.B",
    "H15/H15/RIFLGFCY10_N.B",
]
EXPECTED_WINDOW = {"start": "2013-01-01", "end": "2026-10-23"}
DESIGN_COMMIT = "65e71695a3d99ed6a5584548652a61dc0e66006f"
PREREG_COMMIT = "b93ab1b4514e828561e74963b1a830421a104e29"
ACTIVE_RECEIPT = "governance/score-v2-1e-real-data-research-authorization.json"
HISTORICAL_RECEIPT = "governance/score-v2-1e-real-data-research-authorization-historical-approved-2026-10-28.json"
CLOSEOUT = "governance/score-v2-1e-preflight-closeout-2026-10-28.json"
APPROVED_BY = "usdimpact owner via Issue #209 approval comment 6477834394"
APPROVED_AT = "2026-10-28T18:55:48Z"
ALLOWED_OUTPUTS = [
    "aggregate_diagnostics",
    "pass_fail_gate_results",
    "non_value_bearing_hashes",
    "release_vintage_identifiers",
    "coverage_statistics",
    "correlation_and_redundancy_statistics",
]


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    schema = _load(repo_root / "governance/score-v2-1e-real-data-research-authorization.schema.json")
    template = _load(repo_root / "governance/score-v2-1e-real-data-research-authorization.template.json")
    receipt = _load(repo_root / ACTIVE_RECEIPT)
    historical_receipt = _load(repo_root / HISTORICAL_RECEIPT)
    closeout = _load(repo_root / CLOSEOUT)
    contract = _load(repo_root / "governance/score-v2-1e-real-data-execution-contract.json")
    prereg = _load(repo_root / "governance/score-v2-1e-preregistration.json")
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")

    if hold.get("state") != "hold":
        raise RuntimeError("Score rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1E preregistration boundary changed")
    if prereg.get("production_authorized") is not False:
        raise RuntimeError("preregistration may not authorize Production")

    if template.get("decision_status") != "hold":
        raise RuntimeError("HOLD template must remain unchanged")
    if template.get("approved_by") is not None or template.get("approved_at") is not None:
        raise RuntimeError("HOLD template may not contain approval identity/time")
    if template.get("data_window") != {"start": None, "end": None}:
        raise RuntimeError("HOLD template may not preselect a data window")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template authorizations must remain false")

    expected_inactive_receipt = dict(template)
    expected_inactive_receipt["notes"] = "One-off authorization consumed after official H.15 historical-vintage preflight failed closed under pipeline Issue #218; no further data fetch authorized. Original approved receipt preserved in governance/score-v2-1e-real-data-research-authorization-historical-approved-2026-10-28.json."
    if receipt != expected_inactive_receipt:
        raise RuntimeError("active authorization receipt must remain HOLD and consumed")

    if historical_receipt.get("decision_status") != "approved":
        raise RuntimeError("active receipt is not approved")
    if historical_receipt.get("methodology_version") != "2.1E-design-candidate":
        raise RuntimeError("methodology version changed")
    if historical_receipt.get("design_merge_commit") != DESIGN_COMMIT:
        raise RuntimeError("design merge pin changed")
    if historical_receipt.get("preregistration_merge_commit") != PREREG_COMMIT:
        raise RuntimeError("preregistration merge pin changed")
    if historical_receipt.get("execution_scope") != "one_off_private_research_only":
        raise RuntimeError("execution scope changed")
    if historical_receipt.get("exact_series") != EXPECTED_SERIES:
        raise RuntimeError("exact-series inventory changed")
    if historical_receipt.get("data_window") != EXPECTED_WINDOW:
        raise RuntimeError("approved data window changed")
    if historical_receipt.get("approved_by") != APPROVED_BY:
        raise RuntimeError("approval identity/evidence changed")
    if historical_receipt.get("approved_at") != APPROVED_AT:
        raise RuntimeError("approval timestamp changed")

    storage = historical_receipt.get("storage_policy", {})
    if storage != {
        "source_values": "ephemeral_only",
        "raw_responses": "ephemeral_only",
        "temporary_workspace": "isolated_non_public",
        "durable_private_storage": False,
    }:
        raise RuntimeError("storage policy changed")

    output = historical_receipt.get("output_policy", {})
    if output.get("public_repo_source_values") is not False:
        raise RuntimeError("public source values must remain forbidden")
    if output.get("public_repo_component_values") is not False:
        raise RuntimeError("public component values must remain forbidden")
    if output.get("allowed_persistent_outputs") != ALLOWED_OUTPUTS:
        raise RuntimeError("persistent output allowlist changed")

    auth = historical_receipt.get("authorizations", {})
    if auth.get("real_data_fetch") is not True or auth.get("real_data_research") is not True:
        raise RuntimeError("approved research flags are not active")
    for field in (
        "paid_data",
        "source_contract_acceptance",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if contract.get("state") != "one_off_private_research_blocked":
        raise RuntimeError("v2.1E is permanently blocked under Issue #218")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt is not permitted after closeout")
    if contract.get("active_authorization_receipt_path") is not None:
        raise RuntimeError("active receipt path must be null")
    if contract.get("historical_authorization_receipt_path") != HISTORICAL_RECEIPT:
        raise RuntimeError("archival evidence path changed")
    if contract.get("preflight_closeout_path") != CLOSEOUT:
        raise RuntimeError("historical-vintage stop marker path changed")
    if contract.get("authorized_data_window") != EXPECTED_WINDOW:
        raise RuntimeError("historical approval window changed")

    current = contract.get("current_state", {})
    for field in (
        "real_data_fetch_authorized", "real_data_research_authorized",
        "active_receipt_present", "paid_data_authorized",
        "source_contract_acceptance_authorized",
        "durable_private_storage_authorized",
        "public_artifact_replacement_authorized",
        "research_ledger_mutation_authorized", "production_authorized",
    ):
        if current.get(field) is not False:
            raise RuntimeError(f"blocked contract cannot authorize {field}")

    expected_closeout =     {
        "version": 1,
        "state": "failed_closed_consumed",
        "phase": "historical_vintage_feasibility_preflight",
        "methodology_version": "2.1E-design-candidate",
        "owner_decision_issue": "https://github.com/usdimpact/usd-impact-pipeline/issues/209",
        "owner_approval_comment_id": 6477834394,
        "historical_receipt_path": "governance/score-v2-1e-real-data-research-authorization-historical-approved-2026-10-28.json",
        "historical_approval_time_utc": "2026-10-28T18:55:48Z",
        "historical_approval_original_blob_sha": "40283d6c846c994b71e3d1a8007f1844215a655e",
        "execution_issue": "https://github.com/usdimpact/usd-impact-pipeline/issues/211",
        "blocking_issue": "https://github.com/usdimpact/usd-impact-pipeline/issues/218",
        "failed_workflow_run": "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40755916179",
        "blocked_source_family": "H15",
        "blocked_release_date": "2020-01-06",
        "failed_official_archive_path": "/releases/h15/20200106/default.htm",
        "failed_http_status": 404,
        "fed_sample_families_reached": [
            "H10",
            "H8",
            "H41"
        ],
        "full_candidate_score_computed": False,
        "source_or_component_values_persisted": False,
        "public_artifacts_modified": False,
        "research_ledgers_modified": False,
        "production_authorized": False,
        "one_off_research_authorized_now": False,
        "retry_under_original_approval_authorized": False,
        "revised_current_history_substitute_authorized": False,
        "alternative_sources_under_original_approval_authorized": False,
        "drop_or_reweight_h15_authorized": False,
        "future_design_requires_new_version_preregistration_and_owner_review": True,
        "public_redistribution_rights_hold": "https://github.com/usdimpact/usd-impact-pipeline/issues/155"
    }
    if closeout != expected_closeout:
        raise RuntimeError("fail-closed historical-vintage stop evidence changed")

    network = contract.get("network_policy", {})
    if network.get("credentials_required") is not False:
        raise RuntimeError("credentials must not be required")
    allowed_hosts = set(network.get("allowed_hosts", []))
    required_hosts = {"www.federalreserve.gov", "www.bls.gov", "data.bls.gov"}
    if not required_hosts.issubset(allowed_hosts):
        raise RuntimeError("official Board/BLS host allowlist is incomplete")

    schema_props = schema.get("properties", {})
    if schema_props.get("design_merge_commit", {}).get("const") != DESIGN_COMMIT:
        raise RuntimeError("schema design pin changed")
    if schema_props.get("preregistration_merge_commit", {}).get("const") != PREREG_COMMIT:
        raise RuntimeError("schema preregistration pin changed")
    auth_schema = schema_props.get("authorizations", {}).get("properties", {})
    for field in (
        "paid_data",
        "source_contract_acceptance",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth_schema.get(field, {}).get("const") is not False:
            raise RuntimeError(f"schema must hard-code {field}=false")

    return {
        "status": "passed",
        "state": "one_off_private_research_blocked",
        "historical_owner_decision": "approved",
        "decision_status": "hold_consumed",
        "historical_authorization_receipt_present": True,
        "active_authorization_receipt_present": False,
        "exact_series_count": len(EXPECTED_SERIES),
        "data_window": EXPECTED_WINDOW,
        "real_data_fetch_authorized": False,
        "real_data_research_authorized": False,
        "durable_private_storage_authorized": False,
        "public_artifact_replacement_authorized": False,
        "production_authorized": False,
        "candidate_score_computed": False,
        "historical_vintage_preflight": "blocked",
        "blocking_issue": "https://github.com/usdimpact/usd-impact-pipeline/issues/218",
        "rights_hold": True,
    }



def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-active", action="store_true")
    args = parser.parse_args()
    report = validate(Path(__file__).resolve().parents[1])
    if args.require_active:
        raise RuntimeError(
            "one-off v2.1E research is consumed/blocked by H.15 vintage Issue #218"
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
