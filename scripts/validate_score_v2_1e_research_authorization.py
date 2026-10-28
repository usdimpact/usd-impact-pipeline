#!/usr/bin/env python3
"""Validate the consumed, fail-closed Score v2.1E research authorization lifecycle."""

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
ARCHIVED_RECEIPT = "governance/archive/score-v2-1e-real-data-research-authorization-2026-10-28.json"
OUTCOME = "governance/score-v2-1e-real-data-research-outcome-2026-10-28.json"
APPROVED_BY = "usdimpact owner via Issue #209 approval comment 6477834394"
APPROVED_AT = "2026-10-28T18:55:48Z"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    template = _load(repo_root / "governance/score-v2-1e-real-data-research-authorization.template.json")
    archived = _load(repo_root / ARCHIVED_RECEIPT)
    outcome = _load(repo_root / OUTCOME)
    contract = _load(repo_root / "governance/score-v2-1e-real-data-execution-contract.json")
    prereg = _load(repo_root / "governance/score-v2-1e-preregistration.json")
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")
    active_path = repo_root / ACTIVE_RECEIPT

    if hold.get("state") != "hold":
        raise RuntimeError("Score rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1E preregistration boundary changed")
    if prereg.get("production_authorized") is not False:
        raise RuntimeError("preregistration may not authorize Production")

    if active_path.exists():
        raise RuntimeError("consumed v2.1E authorization must not remain active")

    if template.get("decision_status") != "hold":
        raise RuntimeError("HOLD template must remain unchanged")
    if template.get("approved_by") is not None or template.get("approved_at") is not None:
        raise RuntimeError("HOLD template may not contain approval identity/time")
    if template.get("data_window") != {"start": None, "end": None}:
        raise RuntimeError("HOLD template may not preselect a data window")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("HOLD template authorizations must remain false")

    if archived.get("decision_status") != "approved":
        raise RuntimeError("archived owner approval changed")
    if archived.get("methodology_version") != "2.1E-design-candidate":
        raise RuntimeError("archived methodology version changed")
    if archived.get("design_merge_commit") != DESIGN_COMMIT:
        raise RuntimeError("archived design merge pin changed")
    if archived.get("preregistration_merge_commit") != PREREG_COMMIT:
        raise RuntimeError("archived preregistration merge pin changed")
    if archived.get("execution_scope") != "one_off_private_research_only":
        raise RuntimeError("archived execution scope changed")
    if archived.get("exact_series") != EXPECTED_SERIES:
        raise RuntimeError("archived exact-series inventory changed")
    if archived.get("data_window") != EXPECTED_WINDOW:
        raise RuntimeError("archived approved data window changed")
    if archived.get("approved_by") != APPROVED_BY or archived.get("approved_at") != APPROVED_AT:
        raise RuntimeError("archived approval evidence changed")

    if outcome.get("state") != "blocked_fail_closed":
        raise RuntimeError("v2.1E outcome must remain blocked/fail-closed")
    blocker = outcome.get("hard_blocker", {})
    if blocker.get("slot_family") != "H15":
        raise RuntimeError("expected H15 historical-vintage blocker")
    if blocker.get("preregistered_stop_condition_triggered") != "a required release timestamp/vintage cannot be established":
        raise RuntimeError("expected preregistered stop condition is not recorded")
    if blocker.get("current_revised_history_substitution_allowed") is not False:
        raise RuntimeError("current revised history substitution must remain forbidden")

    result = outcome.get("execution_result", {})
    for field in (
        "full_candidate_score_computed",
        "methodology_activated",
        "public_artifacts_modified",
        "research_ledgers_modified",
        "production_modified",
        "raw_source_values_persisted",
        "component_values_persisted",
    ):
        if result.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    consumed = outcome.get("authorization_consumption", {})
    if consumed.get("one_off_authorization_consumed") is not True:
        raise RuntimeError("one-off authorization must remain consumed")
    if consumed.get("active_authorization_receipt_should_exist") is not False:
        raise RuntimeError("active authorization receipt must remain absent")
    if consumed.get("further_real_data_fetch_authorized") is not False:
        raise RuntimeError("further real-data fetch must remain unauthorized")
    if consumed.get("further_real_data_research_authorized") is not False:
        raise RuntimeError("further real-data research must remain unauthorized")

    if contract.get("state") != "blocked_fail_closed_authorization_consumed":
        raise RuntimeError("execution contract must remain blocked/fail-closed")
    if contract.get("archived_authorization_receipt_path") != ARCHIVED_RECEIPT:
        raise RuntimeError("archived receipt path changed")
    if contract.get("active_authorization_receipt_path") != ACTIVE_RECEIPT:
        raise RuntimeError("reserved active receipt path changed")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected after consumption")
    if contract.get("research_outcome_path") != OUTCOME:
        raise RuntimeError("research outcome path changed")
    if contract.get("authorized_data_window") != EXPECTED_WINDOW:
        raise RuntimeError("historical approved window record changed")

    current = contract.get("current_state", {})
    if current.get("one_off_authorization_consumed") is not True:
        raise RuntimeError("contract must record consumed authorization")
    for field in (
        "real_data_fetch_authorized",
        "real_data_research_authorized",
        "active_receipt_present",
        "paid_data_authorized",
        "source_contract_acceptance_authorized",
        "durable_private_storage_authorized",
        "public_artifact_replacement_authorized",
        "research_ledger_mutation_authorized",
        "production_authorized",
    ):
        if current.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    stop = contract.get("stop_condition_triggered", {})
    if stop.get("source_family") != "H15":
        raise RuntimeError("contract must bind the H15 blocker")
    if stop.get("condition") != "a required release timestamp/vintage cannot be established":
        raise RuntimeError("contract stop condition changed")

    return {
        "status": "passed",
        "state": "blocked_fail_closed_authorization_consumed",
        "decision_status": "consumed_after_blocker",
        "active_authorization_receipt_present": False,
        "archived_owner_approval_present": True,
        "exact_series_count": len(EXPECTED_SERIES),
        "data_window": EXPECTED_WINDOW,
        "hard_blocker": "H15_historical_release_vintage_unavailable",
        "real_data_fetch_authorized": False,
        "real_data_research_authorized": False,
        "full_candidate_score_computed": False,
        "public_artifact_replacement_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
