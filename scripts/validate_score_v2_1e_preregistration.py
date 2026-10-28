#!/usr/bin/env python3
"""Validate the preregistered, design-only Score v2.1E research protocol."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED_SERIES = {
    "USD": "H10/H10/JRXWTFB_N.B",
    "ENERGY": "WPU0561",
    "FIN_CONDITIONS": "H8/H8/B1001NCBA",
    "FIN_STRESS": "H41/H41/RESPPALDP_N.WW",
    "LIQUIDITY": "H41/H41/RESPPA_N.WW",
    "REAL_YIELD": "H15/H15/RIFLGFCY10_XII_N.B",
    "UST_2Y": "H15/H15/RIFLGFCY02_N.B",
    "UST_10Y": "H15/H15/RIFLGFCY10_N.B",
}

EXPECTED_TRANSFORMS = {
    "USD": "level",
    "ENERGY": "natural_log_level",
    "FIN_CONDITIONS": "negative_log_change_13_weeks",
    "FIN_STRESS": "log1p_level",
    "LIQUIDITY": "log_change_13_weeks",
    "REAL_YIELD": "level",
    "UST_2Y": "level",
    "UST_10Y": "level",
}

EXPECTED_WEIGHTS = {
    "USD": 0.125,
    "ENERGY": -0.125,
    "FIN_CONDITIONS": 0.125,
    "FIN_STRESS": 0.125,
    "LIQUIDITY": -0.125,
    "REAL_YIELD": 0.125,
    "UST_2Y": 0.125,
    "UST_10Y": 0.125,
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    protocol = _load(repo_root / "governance/score-v2-1e-preregistration.json")
    design = _load(repo_root / "governance/score-v2-1e-federal-bls-design.json")
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")

    if protocol.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1E protocol must remain preregistered design-only")
    if protocol.get("methodology_version") != "2.1E-design-candidate":
        raise RuntimeError("unexpected methodology version")
    if protocol.get("budget_constraint") != "zero_paid_market_data_budget":
        raise RuntimeError("zero-budget constraint missing")
    if hold.get("state") != "hold":
        raise RuntimeError("rights HOLD must remain active")

    auth = protocol.get("authorizations")
    if not isinstance(auth, dict) or any(auth.values()):
        raise RuntimeError("v2.1E preregistration must not authorize execution")
    if protocol.get("real_data_research_authorized") is not False:
        raise RuntimeError("real-data research must remain unauthorized")
    if protocol.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    clock = protocol.get("evaluation_clock", {})
    if clock.get("timezone") != "America/New_York":
        raise RuntimeError("unexpected evaluation timezone")
    if clock.get("cutoff") != "Friday 23:59:59":
        raise RuntimeError("unexpected Friday cutoff")
    if clock.get("observation_date_is_not_release_date") is not True:
        raise RuntimeError("observation/release distinction must remain explicit")
    if clock.get("release_date_is_not_vintage_identity") is not True:
        raise RuntimeError("release/vintage distinction must remain explicit")

    source_rules = protocol.get("source_rules")
    if not isinstance(source_rules, list) or len(source_rules) != 8:
        raise RuntimeError("expected exactly eight source rules")
    actual_series = {item["slot"]: item["exact_series_id"] for item in source_rules}
    actual_transforms = {item["slot"]: item["transform"] for item in source_rules}
    if actual_series != EXPECTED_SERIES:
        raise RuntimeError("v2.1E exact series inventory changed")
    if actual_transforms != EXPECTED_TRANSFORMS:
        raise RuntimeError("v2.1E preregistered transforms changed")

    energy = next(item for item in source_rules if item["slot"] == "ENERGY")
    if energy.get("max_observation_age_calendar_days") != 50:
        raise RuntimeError("BLS energy max-age boundary changed")
    if energy.get("vintage_fallback") != "fail_closed_no_candidate_week":
        raise RuntimeError("BLS missing-vintage behavior must fail closed")
    if "Current revised history is not an allowed substitute" not in energy.get(
        "historical_vintage_rule", ""
    ):
        raise RuntimeError("BLS latest-history fallback prohibition missing")

    bank = next(item for item in source_rules if item["slot"] == "FIN_CONDITIONS")
    if bank.get("vintage_fallback") != "fail_closed_no_candidate_week":
        raise RuntimeError("H.8 missing-vintage behavior must fail closed")
    if "Latest revised history is not an allowed substitute" not in bank.get(
        "historical_vintage_rule", ""
    ):
        raise RuntimeError("H.8 latest-history fallback prohibition missing")

    weekly = protocol.get("weekly_matrix", {})
    if weekly.get("required_prior_complete_weeks") != 104:
        raise RuntimeError("two-year prior-history requirement changed")
    if weekly.get("complete_case_history") is not True:
        raise RuntimeError("normalization history must remain complete-case")
    if weekly.get("missing_slot_policy") != "fail_closed_no_score":
        raise RuntimeError("missing slots must fail closed")
    if weekly.get("dynamic_reweighting") is not False:
        raise RuntimeError("dynamic reweighting must remain forbidden")
    if weekly.get("proxy_autofill") is not False:
        raise RuntimeError("proxy autofill must remain forbidden")
    if weekly.get("latest_revised_history_fallback") is not False:
        raise RuntimeError("latest revised history fallback must remain disabled")

    norm = protocol.get("normalization", {})
    if norm.get("method") != "expanding_point_in_time_zscore":
        raise RuntimeError("candidate must use expanding PIT normalization")
    if norm.get("history_scope") != "strictly prior complete candidate weeks only":
        raise RuntimeError("normalization history scope changed")
    if norm.get("minimum_prior_complete_weeks") != 104:
        raise RuntimeError("normalization minimum history changed")
    if norm.get("standard_deviation") != "sample ddof=1":
        raise RuntimeError("standard deviation convention changed")
    if float(norm.get("clip")) != 3.5:
        raise RuntimeError("z-score clip changed")
    if norm.get("current_week_excluded_from_own_normalization") is not True:
        raise RuntimeError("current week must remain excluded from normalization")
    if norm.get("full_sample_normalization_for_candidate") is not False:
        raise RuntimeError("full-sample normalization must remain disabled")

    score = protocol.get("score", {})
    if score.get("weights") != EXPECTED_WEIGHTS:
        raise RuntimeError("v2.1E preregistered weights changed")
    if abs(sum(abs(float(v)) for v in EXPECTED_WEIGHTS.values()) - 1.0) > 1e-12:
        raise RuntimeError("absolute weights must sum to 1.0")

    hard = protocol.get("hard_acceptance_gates", {})
    required_hard = {
        "source_scope_documented_for_all_slots": True,
        "zero_lookahead_violations": True,
        "exact_release_vintage_provenance_for_all_used_values": True,
        "current_revised_history_used_as_historical_vintage": False,
        "transform_domain_errors": 0,
        "required_prior_complete_weeks": 104,
        "evaluated_week_complete_slot_coverage_min": 0.975,
        "each_slot_eligible_week_coverage_min": 0.98,
        "maximum_consecutive_missing_candidate_weeks": 2,
        "maximum_absolute_pairwise_spearman": 0.95,
        "maximum_variance_inflation_factor": 12.0,
        "maximum_first_principal_component_variance_share": 0.70,
        "primary_credit_minimum_unique_transformed_values_per_104_weeks": 5,
        "primary_credit_maximum_single_value_share_per_104_weeks": 0.95,
        "historical_anchor_windows_minimum_with_sign_hit_rate_at_least_0_55": 4,
        "historical_anchor_window_minimum_allowed_sign_hit_rate": 0.35,
        "thresholds_fixed_before_results_visible": True,
    }
    for key, expected in required_hard.items():
        if hard.get(key) != expected:
            raise RuntimeError(f"hard gate changed: {key}")

    if len(protocol.get("historical_anchor_windows", [])) != 5:
        raise RuntimeError("historical anchor window set changed")

    anti_tuning = "\n".join(str(x) for x in protocol.get("anti_tuning_rules", []))
    for phrase in (
        "No transform may change after candidate results are viewed",
        "No hard acceptance threshold may be relaxed after results are viewed",
        "No slot may be dropped or reweighted to rescue a failed candidate",
        "No current revised BLS or H.8 history may substitute for the historical release vintage",
    ):
        if phrase not in anti_tuning:
            raise RuntimeError(f"missing anti-tuning rule: {phrase}")

    if design.get("state") != "design_only":
        raise RuntimeError("parent v2.1E design boundary changed")
    if design.get("real_data_research_authorized") is not False:
        raise RuntimeError("parent v2.1E design unexpectedly authorizes research")
    if design.get("production_authorized") is not False:
        raise RuntimeError("parent v2.1E design unexpectedly authorizes Production")

    return {
        "status": "passed",
        "state": "preregistered_design_only",
        "slot_count": len(source_rules),
        "exact_series_pinned": True,
        "vintage_rules_frozen": True,
        "thresholds_frozen_before_results": True,
        "point_in_time_normalization": True,
        "real_data_research_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
