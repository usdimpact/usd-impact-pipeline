#!/usr/bin/env python3
"""Validate fail-closed Score v2.1F live-vintage preflight authorization packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DESIGN_COMMIT = "e14aec35142b9536b5b889d0fae4eab9a94faf88"
PREREG_COMMIT = "bcf473e2bbcb36fa1080a3a56f77a3796d74ccaa"
ACTIVE_RECEIPT = "governance/score-v2-1f-live-vintage-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-live-vintage-preflight-dispatch.json"
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
    schema = _load(
        repo_root / "governance/score-v2-1f-live-vintage-preflight-authorization.schema.json"
    )
    template = _load(
        repo_root / "governance/score-v2-1f-live-vintage-preflight-authorization.template.json"
    )
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

    if (repo_root / ACTIVE_RECEIPT).exists():
        raise RuntimeError("active v2.1F preflight authorization receipt must remain absent")
    if (repo_root / DISPATCH).exists():
        raise RuntimeError("v2.1F preflight dispatch marker must remain absent")

    if template.get("decision_status") != "hold":
        raise RuntimeError("preflight authorization template must remain HOLD")
    if template.get("methodology_version") != "2.1F-design-candidate":
        raise RuntimeError("template methodology version changed")
    if template.get("issue") != "https://github.com/usdimpact/usd-impact-pipeline/issues/224":
        raise RuntimeError("template owner decision issue changed")
    if template.get("design_merge_commit") != DESIGN_COMMIT:
        raise RuntimeError("template design pin changed")
    if template.get("preregistration_merge_commit") != PREREG_COMMIT:
        raise RuntimeError("template preregistration pin changed")
    if template.get("exact_series") != EXPECTED_SERIES:
        raise RuntimeError("template exact-series inventory changed")
    if template.get("data_window") != {"start": None, "end": None}:
        raise RuntimeError("HOLD template may not preselect a live data window")
    if template.get("approved_by") is not None or template.get("approved_at") is not None:
        raise RuntimeError("HOLD template may not contain approval evidence")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template authorizations must remain false")

    output = template.get("output_policy", {})
    for field in (
        "source_values_in_logs",
        "component_values_in_logs",
        "candidate_score_output",
        "public_repo_source_values",
    ):
        if output.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if contract.get("state") != "authorization_packet_only":
        raise RuntimeError("preflight execution contract must remain packet-only")
    if contract.get("design_merge_commit") != DESIGN_COMMIT:
        raise RuntimeError("contract design pin changed")
    if contract.get("preregistration_merge_commit") != PREREG_COMMIT:
        raise RuntimeError("contract preregistration pin changed")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected before owner approval")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch marker must not be expected before activation")
    if contract.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")
    current = contract.get("current_state", {})
    if not isinstance(current, dict) or any(current.values()):
        raise RuntimeError("all current preflight execution authorizations must be false")

    network = contract.get("network_policy", {})
    required_hosts = {"www.federalreserve.gov", "www.bls.gov", "data.bls.gov"}
    if not required_hosts.issubset(set(network.get("allowed_hosts", []))):
        raise RuntimeError("official Board/BLS host allowlist is incomplete")
    if network.get("credentials_required") is not False:
        raise RuntimeError("credentials must remain unnecessary")

    schema_props = schema.get("properties", {})
    if schema_props.get("design_merge_commit", {}).get("const") != DESIGN_COMMIT:
        raise RuntimeError("schema design pin changed")
    if schema_props.get("preregistration_merge_commit", {}).get("const") != PREREG_COMMIT:
        raise RuntimeError("schema preregistration pin changed")
    auth_schema = schema_props.get("authorizations", {}).get("properties", {})
    for field in (
        "real_data_research",
        "candidate_score_computation",
        "paid_data",
        "source_contract_acceptance",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth_schema.get(field, {}).get("const") is not False:
            raise RuntimeError(f"schema must hard-code {field}=false")

    if prereg.get("next_step_if_design_checks_pass") != (
        "separate_owner_authorization_for_v2_1f_live_vintage_feasibility_preflight_only"
    ):
        raise RuntimeError("preregistration next step changed")

    return {
        "status": "passed",
        "state": "authorization_packet_only",
        "exact_series_count": len(EXPECTED_SERIES),
        "active_authorization_receipt_present": False,
        "dispatch_marker_present": False,
        "live_vintage_preflight_authorized": False,
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
