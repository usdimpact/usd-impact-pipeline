#!/usr/bin/env python3
"""Validate the approved, fail-closed Score v2.1E one-off research authorization."""

from __future__ import annotations

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

    if receipt.get("decision_status") != "approved":
        raise RuntimeError("active receipt is not approved")
    if receipt.get("methodology_version") != "2.1E-design-candidate":
        raise RuntimeError("methodology version changed")
    if receipt.get("design_merge_commit") != DESIGN_COMMIT:
        raise RuntimeError("design merge pin changed")
    if receipt.get("preregistration_merge_commit") != PREREG_COMMIT:
        raise RuntimeError("preregistration merge pin changed")
    if receipt.get("execution_scope") != "one_off_private_research_only":
        raise RuntimeError("execution scope changed")
    if receipt.get("exact_series") != EXPECTED_SERIES:
        raise RuntimeError("exact-series inventory changed")
    if receipt.get("data_window") != EXPECTED_WINDOW:
        raise RuntimeError("approved data window changed")
    if receipt.get("approved_by") != APPROVED_BY:
        raise RuntimeError("approval identity/evidence changed")
    if receipt.get("approved_at") != APPROVED_AT:
        raise RuntimeError("approval timestamp changed")

    storage = receipt.get("storage_policy", {})
    if storage != {
        "source_values": "ephemeral_only",
        "raw_responses": "ephemeral_only",
        "temporary_workspace": "isolated_non_public",
        "durable_private_storage": False,
    }:
        raise RuntimeError("storage policy changed")

    output = receipt.get("output_policy", {})
    if output.get("public_repo_source_values") is not False:
        raise RuntimeError("public source values must remain forbidden")
    if output.get("public_repo_component_values") is not False:
        raise RuntimeError("public component values must remain forbidden")
    if output.get("allowed_persistent_outputs") != ALLOWED_OUTPUTS:
        raise RuntimeError("persistent output allowlist changed")

    auth = receipt.get("authorizations", {})
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

    if contract.get("state") != "one_off_private_research_authorized":
        raise RuntimeError("execution contract is not in one-off authorized state")
    if contract.get("active_authorization_receipt_path") != ACTIVE_RECEIPT:
        raise RuntimeError("active receipt path changed")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("active receipt must now be expected")
    if contract.get("authorized_data_window") != EXPECTED_WINDOW:
        raise RuntimeError("contract data window changed")

    current = contract.get("current_state", {})
    for field in ("real_data_fetch_authorized", "real_data_research_authorized", "active_receipt_present"):
        if current.get(field) is not True:
            raise RuntimeError(f"{field} must be true")
    for field in (
        "paid_data_authorized",
        "source_contract_acceptance_authorized",
        "durable_private_storage_authorized",
        "public_artifact_replacement_authorized",
        "research_ledger_mutation_authorized",
        "production_authorized",
    ):
        if current.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

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
        "state": "one_off_private_research_authorized",
        "decision_status": "approved",
        "active_authorization_receipt_present": True,
        "exact_series_count": len(EXPECTED_SERIES),
        "data_window": EXPECTED_WINDOW,
        "real_data_fetch_authorized": True,
        "real_data_research_authorized": True,
        "durable_private_storage_authorized": False,
        "public_artifact_replacement_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
