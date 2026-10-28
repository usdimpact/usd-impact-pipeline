#!/usr/bin/env python3
"""Validate the design-only Score v2.1 zero-budget methodology packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import usd_impact_score_v2 as score_v2

EXPECTED_DRIVER_ORDER = ["DXY","WTI","SPX","VIX","BTC","GOLD","UST_2Y","UST_10Y"]
BLOCKED_OR_UNRESOLVED = {"SPX","VIX","BTC","GOLD"}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def _bands_from_v2() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for low, high, label in score_v2.REGIME_BANDS:
        result.append({
            "low": None if low == float("-inf") else float(low),
            "high": None if high == float("inf") else float(high),
            "label": label,
        })
    return result


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    design = _load(repo_root / "governance/score-v2-1-zero-budget-design.json")
    prereg = _load(
        repo_root / "governance/score-v2-1-research-preregistration.template.json"
    )
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")
    zero = _load(repo_root / "governance/score-zero-budget-fallback-matrix.json")

    if design.get("state") != "design_only":
        raise RuntimeError("v2.1 packet must remain design-only")
    if design.get("budget_constraint") != "zero_paid_market_data_budget":
        raise RuntimeError("v2.1 packet must retain the zero-budget constraint")
    if hold.get("state") != "hold" or hold.get("decision_receipt") is not None:
        raise RuntimeError("rights gate must remain unresolved HOLD")
    if zero.get("methodology_change_authorized") is not False:
        raise RuntimeError("zero-budget matrix unexpectedly authorizes methodology change")

    authorizations = design.get("authorizations")
    expected_auth = {
        "real_data_access": False,
        "real_data_backtest": False,
        "methodology_activation": False,
        "public_artifact_replacement": False,
        "research_ledger_mutation": False,
        "production": False,
    }
    if authorizations != expected_auth:
        raise RuntimeError("v2.1 design authorization boundary changed")

    invariants = design["phase_1_invariants"]
    if invariants["start_date_target"] != score_v2.START_DATE:
        raise RuntimeError("v2.1 design start-date target differs from v2")
    if invariants["weekly_rule"] != score_v2.RESAMPLE_RULE:
        raise RuntimeError("v2.1 phase-1 weekly rule differs from v2")
    if float(invariants["zscore_clip"]) != float(score_v2.ZSCORE_CLIP):
        raise RuntimeError("v2.1 phase-1 z-score clip differs from v2")
    if invariants["canonical_driver_order"] != list(score_v2.WEIGHTS):
        raise RuntimeError("v2.1 phase-1 driver order differs from v2")
    if invariants["weights"] != {
        key: float(value) for key, value in score_v2.WEIGHTS.items()
    }:
        raise RuntimeError("v2.1 phase-1 weights differ from v2")
    if invariants["regime_bands"] != _bands_from_v2():
        raise RuntimeError("v2.1 phase-1 regime bands differ from v2")

    drivers = design.get("drivers")
    if not isinstance(drivers, list) or [d.get("driver") for d in drivers] != EXPECTED_DRIVER_ORDER:
        raise RuntimeError("v2.1 driver inventory mismatch")

    by_driver = {item["driver"]: item for item in drivers}
    if by_driver["DXY"]["design_status"] != "candidate_methodology_substitution":
        raise RuntimeError("DXY must remain an explicit methodology substitution")
    if by_driver["WTI"]["design_status"] != "candidate_methodology_substitution":
        raise RuntimeError("WTI must remain an explicit methodology substitution")

    for driver in BLOCKED_OR_UNRESOLVED:
        if by_driver[driver].get("zero_budget_candidate") is not None:
            raise RuntimeError(f"{driver} must not have a preselected zero-budget candidate")
        if by_driver[driver].get("silent_replacement_forbidden") is not True:
            raise RuntimeError(f"{driver} must forbid silent replacement")

    protocol = design["research_protocol"]
    if protocol.get("status") != "not_authorized":
        raise RuntimeError("real-data research must remain unauthorized")
    if protocol.get("candidate_freeze_required_before_data") is not True:
        raise RuntimeError("candidate definitions must freeze before data")
    if protocol.get("acceptance_thresholds", {}).get("status") != "not_set":
        raise RuntimeError("acceptance thresholds must remain unset in design-only packet")
    if protocol.get("incomplete_driver_policy") != "fail_closed_no_score":
        raise RuntimeError("incomplete driver policy must fail closed")
    if protocol.get("no_reweighting_for_missing_driver") is not True:
        raise RuntimeError("missing drivers must not trigger reweighting")
    if protocol.get("no_proxy_autofill") is not True:
        raise RuntimeError("unapproved proxies must not autofill")

    versioning = design["versioning"]
    if versioning.get("v2_history_rewrite_forbidden") is not True:
        raise RuntimeError("v2 history rewrite must remain forbidden")
    if versioning.get("v2_and_v2_1_must_not_be_spliced_into_one_unversioned_series") is not True:
        raise RuntimeError("v2/v2.1 unversioned splice must remain forbidden")

    if prereg.get("state") != "template_only":
        raise RuntimeError("v2.1 preregistration must remain template-only")
    if prereg.get("real_data_research_authorized") is not False:
        raise RuntimeError("preregistration template must not authorize real-data research")
    if prereg.get("production_authorized") is not False:
        raise RuntimeError("preregistration template must not authorize Production")
    fields = prereg.get("fields", {})
    if fields.get("thresholds") is not None:
        raise RuntimeError("preregistration template must not preselect thresholds")
    if any(fields.get(key) is not None for key in (
        "preregistration_id",
        "approved_by",
        "approved_at",
        "data_cutoff",
        "evaluation_window_start",
        "evaluation_window_end",
        "candidate_definition_commit",
        "missing_history_policy",
        "revision_policy",
        "calendar_policy",
        "timezone_policy",
    )):
        raise RuntimeError("preregistration template contains premature research decisions")

    return {
        "status": "passed",
        "state": "design_only",
        "driver_count": len(drivers),
        "phase_1_formula_equal_to_v2": True,
        "complete_zero_budget_candidate_exists": False,
        "real_data_research_authorized": False,
        "methodology_activation_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
