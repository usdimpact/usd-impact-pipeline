#!/usr/bin/env python3
"""Validate the fail-closed Score v2.1E real-data research authorization packet."""

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

DESIGN_COMMIT = "65e71695a3d99ed6a5584548652a61dc0e66006f"
PREREG_COMMIT = "b93ab1b4514e828561e74963b1a830421a104e29"
ACTIVE_RECEIPT = "governance/score-v2-1e-real-data-research-authorization.json"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    schema = _load(
        repo_root
        / "governance/score-v2-1e-real-data-research-authorization.schema.json"
    )
    template = _load(
        repo_root
        / "governance/score-v2-1e-real-data-research-authorization.template.json"
    )
    contract = _load(
        repo_root / "governance/score-v2-1e-real-data-execution-contract.json"
    )
    prereg = _load(repo_root / "governance/score-v2-1e-preregistration.json")
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")

    if hold.get("state") != "hold":
        raise RuntimeError("Score rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1E preregistration boundary changed")
    if prereg.get("real_data_research_authorized") is not False:
        raise RuntimeError("v2.1E preregistration unexpectedly authorizes research")
    if prereg.get("production_authorized") is not False:
        raise RuntimeError("v2.1E preregistration unexpectedly authorizes Production")

    active_path = repo_root / ACTIVE_RECEIPT
    if active_path.exists():
        raise RuntimeError(
            "active v2.1E research authorization receipt must not exist in HOLD packet"
        )

    if template.get("decision_status") != "hold":
        raise RuntimeError("authorization template must remain HOLD")
    if template.get("methodology_version") != "2.1E-design-candidate":
        raise RuntimeError("authorization methodology version changed")
    if template.get("design_merge_commit") != DESIGN_COMMIT:
        raise RuntimeError("design merge commit pin changed")
    if template.get("preregistration_merge_commit") != PREREG_COMMIT:
        raise RuntimeError("preregistration merge commit pin changed")
    if template.get("execution_scope") != "one_off_private_research_only":
        raise RuntimeError("execution scope changed")
    if template.get("exact_series") != EXPECTED_SERIES:
        raise RuntimeError("authorization exact-series inventory changed")
    if template.get("data_window") != {"start": None, "end": None}:
        raise RuntimeError("HOLD template must not preselect a data window")
    if template.get("approved_by") is not None or template.get("approved_at") is not None:
        raise RuntimeError("HOLD template must not contain approval identity/time")

    auth = template.get("authorizations")
    if not isinstance(auth, dict) or any(auth.values()):
        raise RuntimeError("HOLD authorization template must keep every flag false")

    storage = template.get("storage_policy", {})
    if storage.get("source_values") != "ephemeral_only":
        raise RuntimeError("source values must remain ephemeral-only")
    if storage.get("raw_responses") != "ephemeral_only":
        raise RuntimeError("raw responses must remain ephemeral-only")
    if storage.get("temporary_workspace") != "isolated_non_public":
        raise RuntimeError("temporary workspace must remain isolated/non-public")
    if storage.get("durable_private_storage") is not False:
        raise RuntimeError("durable private storage must remain unauthorized")

    output = template.get("output_policy", {})
    if output.get("public_repo_source_values") is not False:
        raise RuntimeError("public repository source values must remain forbidden")
    if output.get("public_repo_component_values") is not False:
        raise RuntimeError("public repository component values must remain forbidden")

    if contract.get("state") != "authorization_packet_only":
        raise RuntimeError("execution contract must remain authorization-packet-only")
    if contract.get("active_authorization_receipt_path") != ACTIVE_RECEIPT:
        raise RuntimeError("active receipt path changed")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active authorization receipt must not be expected now")

    current = contract.get("current_state", {})
    if any(
        current.get(key) is not False
        for key in (
            "real_data_fetch_authorized",
            "real_data_research_authorized",
            "active_receipt_present",
            "production_authorized",
        )
    ):
        raise RuntimeError("execution contract current state must remain fully unauthorized")

    network = contract.get("network_policy", {})
    if network.get("credentials_required") is not False:
        raise RuntimeError("credentials must not be required")
    allowed_hosts = set(network.get("allowed_hosts", []))
    if not {"www.federalreserve.gov", "www.bls.gov", "data.bls.gov"}.issubset(
        allowed_hosts
    ):
        raise RuntimeError("official Board/BLS host allowlist is incomplete")

    schema_props = schema.get("properties", {})
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

    if schema_props.get("design_merge_commit", {}).get("const") != DESIGN_COMMIT:
        raise RuntimeError("schema design commit pin changed")
    if (
        schema_props.get("preregistration_merge_commit", {}).get("const")
        != PREREG_COMMIT
    ):
        raise RuntimeError("schema preregistration commit pin changed")

    return {
        "status": "passed",
        "state": "authorization_packet_only",
        "decision_status": "hold",
        "active_authorization_receipt_present": False,
        "exact_series_count": len(EXPECTED_SERIES),
        "real_data_fetch_authorized": False,
        "real_data_research_authorized": False,
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
