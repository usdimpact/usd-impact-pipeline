#!/usr/bin/env python3
"""Validate design-only Score v2.1F five-slot federal/BLS successor."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED = [
    ("USD", "H10/H10/JRXWTFB_N.B", "level", 0.2),
    ("ENERGY", "WPU0561", "natural_log_level", -0.2),
    ("FIN_CONDITIONS", "H8/H8/B1001NCBA", "negative_log_change_13_weeks", 0.2),
    ("FIN_STRESS", "H41/H41/RESPPALDP_N.WW", "log1p_level", 0.2),
    ("LIQUIDITY", "H41/H41/RESPPA_N.WW", "log_change_13_weeks", -0.2),
]
REMOVED = {
    "REAL_YIELD": "H15/H15/RIFLGFCY10_XII_N.B",
    "UST_2Y": "H15/H15/RIFLGFCY02_N.B",
    "UST_10Y": "H15/H15/RIFLGFCY10_N.B",
}

def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return data

def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    design = _load(repo_root / "governance/score-v2-1f-five-slot-design.json")
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")
    consumption = _load(
        repo_root / "governance/score-v2-1e-real-data-research-consumption-2026-10-28.json"
    )
    active_v21e = repo_root / "governance/score-v2-1e-real-data-research-authorization.json"

    if design.get("state") != "design_only":
        raise RuntimeError("v2.1F must remain design-only")
    if design.get("methodology_version") != "2.1F-design-candidate":
        raise RuntimeError("unexpected v2.1F methodology version")
    if design.get("candidate_class") != "five_slot_archived_federal_board_bls_release_architecture":
        raise RuntimeError("unexpected v2.1F candidate class")
    if design.get("budget_constraint") != "zero_paid_market_data_budget":
        raise RuntimeError("zero-budget constraint missing")
    if design.get("legal_conclusion") is not False:
        raise RuntimeError("v2.1F may not claim a legal conclusion")
    if design.get("no_source_approved") is not True:
        raise RuntimeError("v2.1F may not pre-approve sources")
    if hold.get("state") != "hold":
        raise RuntimeError("rights HOLD must remain active")

    auth = design.get("authorizations")
    if not isinstance(auth, dict) or any(auth.values()):
        raise RuntimeError("v2.1F design may not authorize execution")
    if design.get("real_data_research_authorized") is not False:
        raise RuntimeError("v2.1F real-data research must remain unauthorized")
    if design.get("production_authorized") is not False:
        raise RuntimeError("v2.1F Production must remain unauthorized")

    predecessor = design.get("predecessor", {})
    if predecessor.get("methodology_version") != "2.1E-design-candidate":
        raise RuntimeError("v2.1F predecessor changed")
    if predecessor.get("candidate_score_computed") is not False:
        raise RuntimeError("v2.1E may not be represented as scored")
    if predecessor.get("source_or_component_values_persisted") is not False:
        raise RuntimeError("v2.1E persisted-value boundary changed")
    if predecessor.get("authorization_inherited") is not False:
        raise RuntimeError("v2.1F may not inherit v2.1E authorization")
    if consumption.get("state") != "consumed_fail_closed":
        raise RuntimeError("v2.1E authorization consumption evidence changed")
    if active_v21e.exists():
        raise RuntimeError("consumed v2.1E active receipt must remain absent")

    slots = design.get("proposed_slots")
    if not isinstance(slots, list) or len(slots) != 5:
        raise RuntimeError("v2.1F must define exactly five slots")
    actual = [
        (
            item.get("slot"),
            item.get("exact_series_id"),
            item.get("transform"),
            float(item.get("weight")),
        )
        for item in slots
    ]
    if actual != EXPECTED:
        raise RuntimeError("v2.1F slot inventory, transforms, or weights changed")
    if abs(sum(abs(float(item["weight"])) for item in slots) - 1.0) > 1e-12:
        raise RuntimeError("absolute weights must sum to 1.0")

    principle = design.get("design_principle", {})
    if principle.get("h15_slots_removed") is not True:
        raise RuntimeError("H.15 slots must remain removed")
    if principle.get("silent_proxy_substitution") is not False:
        raise RuntimeError("silent proxy substitution must remain forbidden")
    if principle.get("result_driven_tuning") is not False:
        raise RuntimeError("result-driven tuning must remain false")

    removed_rows = design.get("removed_v2_1e_slots")
    if not isinstance(removed_rows, list) or len(removed_rows) != 3:
        raise RuntimeError("exactly three v2.1E H.15 slots must be recorded as removed")
    actual_removed = {row.get("slot"): row.get("series_id") for row in removed_rows}
    if actual_removed != REMOVED:
        raise RuntimeError("removed H.15 inventory changed")

    serialized = json.dumps(slots).lower()
    for forbidden in ("h15/", "riflgfcy", "fred", "alfred", "yfinance", "refinitiv", "lseg"):
        if forbidden in serialized:
            raise RuntimeError(f"forbidden successor dependency is active: {forbidden}")

    energy = next(item for item in slots if item["slot"] == "ENERGY")
    if energy.get("live_archive_feasibility") != "pending_separate_authorized_preflight":
        raise RuntimeError("BLS live feasibility must remain pending")
    if "four months" not in str(energy.get("revision_rule", "")).lower():
        raise RuntimeError("BLS revision handling must remain explicit")
    if "current revised history is not an allowed historical-vintage substitute" not in str(
        energy.get("historical_vintage_rule", "")
    ).lower():
        raise RuntimeError("BLS current-history fallback prohibition missing")

    for slot in ("USD", "FIN_CONDITIONS", "FIN_STRESS", "LIQUIDITY"):
        row = next(item for item in slots if item["slot"] == slot)
        if row.get("live_archive_feasibility") != (
            "sampled_historical_archive_paths_verified_before_v2_1e_h15_failure"
        ):
            raise RuntimeError(f"{slot} archive evidence status changed")

    rules = design.get("structural_rules", {})
    expected_rules = {
        "weekly_anchor": "completed Friday",
        "cutoff_timezone": "America/New_York",
        "cutoff_time": "23:59:59",
        "observation_date_is_not_release_date": True,
        "release_date_is_not_vintage_identity": True,
        "point_in_time_release_provenance_required": True,
        "minimum_prior_complete_weeks": 104,
        "normalization": "expanding_point_in_time_zscore",
        "zscore_clip": 3.5,
        "missing_slot_policy": "fail_closed_no_score",
        "complete_case_history": True,
        "dynamic_reweighting": False,
        "proxy_autofill": False,
        "latest_revised_history_fallback": False,
        "target_start": "2015-01-02",
        "history_seed_start": "2013-01-01",
    }
    for key, expected in expected_rules.items():
        if rules.get(key) != expected:
            raise RuntimeError(f"structural rule changed: {key}")

    scale = design.get("candidate_scale", {})
    if scale.get("absolute_weights_sum_to_one") is not True:
        raise RuntimeError("candidate scale normalization must remain explicit")
    if scale.get("regime_bands_frozen_here") is not False:
        raise RuntimeError("regime bands must not be frozen before preregistration")

    if design.get("next_allowed_step") != (
        "prepare_v2_1f_preregistration_and_synthetic_release_timing_rehearsal_only"
    ):
        raise RuntimeError("unexpected next allowed step")

    return {
        "status": "passed",
        "state": "design_only",
        "slot_count": len(slots),
        "h15_slots_removed": True,
        "absolute_weights_sum": sum(abs(float(item["weight"])) for item in slots),
        "result_driven_tuning": False,
        "real_data_research_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }

def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
