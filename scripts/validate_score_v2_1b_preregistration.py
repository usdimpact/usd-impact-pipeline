#!/usr/bin/env python3
"""Validate the preregistered, design-only Score v2.1B research protocol."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED_TRANSFORMS = {
    "USD": "level",
    "ENERGY": "natural_log_level",
    "FIN_CONDITIONS": "level",
    "FIN_STRESS": "level",
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
    protocol = _load(repo_root / "governance/score-v2-1b-preregistration.json")
    design = _load(repo_root / "governance/score-v2-1b-official-macro-design.json")
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")

    if protocol.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1B protocol must remain preregistered design-only")
    if protocol.get("budget_constraint") != "zero_paid_market_data_budget":
        raise RuntimeError("zero-budget constraint missing")
    if hold.get("state") != "hold":
        raise RuntimeError("rights HOLD must remain active")

    auth = protocol.get("authorizations")
    if not isinstance(auth, dict) or any(auth.values()):
        raise RuntimeError("preregistration must not authorize execution or Production")
    if protocol.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    clock = protocol.get("evaluation_clock", {})
    if clock.get("timezone") != "America/New_York":
        raise RuntimeError("unexpected evaluation timezone")
    if clock.get("cutoff") != "Friday 23:59:59":
        raise RuntimeError("unexpected Friday cutoff")
    if clock.get("observation_date_is_not_release_date") is not True:
        raise RuntimeError("release-time distinction must remain explicit")

    source_rules = protocol.get("source_rules")
    if not isinstance(source_rules, list) or len(source_rules) != 8:
        raise RuntimeError("expected exactly eight source rules")
    actual_transforms = {item["slot"]: item["transform"] for item in source_rules}
    if actual_transforms != EXPECTED_TRANSFORMS:
        raise RuntimeError("preregistered transforms changed")
    for item in source_rules:
        if item.get("rights_state") != "confirm_reuse_scope":
            raise RuntimeError(f"{item['slot']} rights scope cannot be pre-approved")

    weekly = protocol.get("weekly_matrix", {})
    if weekly.get("required_prior_complete_weeks") != 104:
        raise RuntimeError("two-year prior-history requirement changed")
    if weekly.get("complete_case_history") is not True:
        raise RuntimeError("normalization history must remain complete-case")
    if weekly.get("missing_slot_policy") != "fail_closed_no_score":
        raise RuntimeError("missing slot policy must fail closed")
    if weekly.get("dynamic_reweighting") is not False:
        raise RuntimeError("dynamic reweighting must remain forbidden")
    if weekly.get("proxy_autofill") is not False:
        raise RuntimeError("proxy autofill must remain forbidden")

    norm = protocol.get("normalization", {})
    if norm.get("method") != "expanding_point_in_time_zscore":
        raise RuntimeError("candidate must use PIT expanding normalization")
    if norm.get("history_scope") != "strictly prior complete candidate weeks only":
        raise RuntimeError("current week must not enter normalization history")
    if norm.get("minimum_prior_complete_weeks") != 104:
        raise RuntimeError("normalization minimum history changed")
    if float(norm.get("clip")) != 3.5:
        raise RuntimeError("z-score clipping changed")
    if norm.get("current_week_excluded_from_own_normalization") is not True:
        raise RuntimeError("lookahead protection changed")
    if norm.get("full_sample_normalization_for_candidate") is not False:
        raise RuntimeError("full-sample normalization must remain disabled")

    score = protocol.get("score", {})
    if score.get("weights") != EXPECTED_WEIGHTS:
        raise RuntimeError("v2.1B preregistered weights changed")
    if abs(sum(abs(float(v)) for v in EXPECTED_WEIGHTS.values()) - 1.0) > 1e-12:
        raise RuntimeError("absolute weight sum is not 1.0")

    hard = protocol.get("hard_acceptance_gates", {})
    required_hard = {
        "zero_lookahead_violations": True,
        "availability_provenance_for_all_used_values": True,
        "transform_domain_errors": 0,
        "required_prior_complete_weeks": 104,
        "evaluated_week_complete_slot_coverage_min": 0.975,
        "each_slot_eligible_week_coverage_min": 0.98,
        "maximum_consecutive_missing_candidate_weeks": 2,
        "maximum_absolute_pairwise_spearman": 0.95,
        "maximum_variance_inflation_factor": 12.0,
        "maximum_first_principal_component_variance_share": 0.70,
        "historical_anchor_windows_minimum_with_sign_hit_rate_at_least_0_55": 4,
        "historical_anchor_window_minimum_allowed_sign_hit_rate": 0.35,
        "thresholds_fixed_before_results_visible": True,
    }
    for key, expected in required_hard.items():
        if hard.get(key) != expected:
            raise RuntimeError(f"hard gate changed: {key}")

    if len(protocol.get("historical_anchor_windows", [])) != 5:
        raise RuntimeError("historical anchor set changed")

    anti_tuning = protocol.get("anti_tuning_rules", [])
    required_phrases = (
        "No transform may change after candidate results are viewed",
        "No hard acceptance threshold may be relaxed after results are viewed",
        "No slot may be dropped or reweighted to rescue a failed candidate",
    )
    for phrase in required_phrases:
        if not any(str(item).startswith(phrase) for item in anti_tuning):
            raise RuntimeError(f"missing anti-tuning rule: {phrase}")

    if design.get("state") != "design_only":
        raise RuntimeError("parent v2.1B design boundary changed")

    return {
        "status": "passed",
        "state": "preregistered_design_only",
        "slot_count": len(source_rules),
        "transforms_frozen": True,
        "thresholds_frozen_before_results": True,
        "point_in_time_normalization": True,
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
