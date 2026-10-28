#!/usr/bin/env python3
"""Validate preregistered, design-only Score v2.1F protocol."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DESIGN_COMMIT = "e14aec35142b9536b5b889d0fae4eab9a94faf88"
EXPECTED_SERIES = {
    "USD": "H10/H10/JRXWTFB_N.B",
    "ENERGY": "WPU0561",
    "FIN_CONDITIONS": "H8/H8/B1001NCBA",
    "FIN_STRESS": "H41/H41/RESPPALDP_N.WW",
    "LIQUIDITY": "H41/H41/RESPPA_N.WW",
}
EXPECTED_TRANSFORMS = {
    "USD": "level",
    "ENERGY": "natural_log_level",
    "FIN_CONDITIONS": "negative_log_change_13_weeks",
    "FIN_STRESS": "log1p_level",
    "LIQUIDITY": "log_change_13_weeks",
}
EXPECTED_WEIGHTS = {
    "USD": 0.2,
    "ENERGY": -0.2,
    "FIN_CONDITIONS": 0.2,
    "FIN_STRESS": 0.2,
    "LIQUIDITY": -0.2,
}
EXPECTED_BANDS = [
    {"low": 1, "high": None, "label": "Strong dollar regime"},
    {"low": 0.3, "high": 1, "label": "Firm dollar regime"},
    {"low": -0.3, "high": 0.3, "label": "Neutral / transitional"},
    {"low": -1, "high": -0.3, "label": "Soft dollar regime"},
    {"low": None, "high": -1, "label": "Weak dollar regime"},
]

def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload

def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    protocol = _load(repo_root / "governance/score-v2-1f-preregistration.json")
    design = _load(repo_root / "governance/score-v2-1f-five-slot-design.json")
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")
    consumption = _load(
        repo_root / "governance/score-v2-1e-real-data-research-consumption-2026-10-28.json"
    )

    if protocol.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F protocol must remain preregistered design-only")
    if protocol.get("methodology_version") != "2.1F-design-candidate":
        raise RuntimeError("unexpected v2.1F methodology version")
    if protocol.get("design_merge_commit") != DESIGN_COMMIT:
        raise RuntimeError("v2.1F design merge pin changed")
    if protocol.get("budget_constraint") != "zero_paid_market_data_budget":
        raise RuntimeError("zero-budget constraint missing")
    if hold.get("state") != "hold":
        raise RuntimeError("rights HOLD must remain active")
    if consumption.get("state") != "consumed_fail_closed":
        raise RuntimeError("v2.1E consumption evidence changed")
    if (repo_root / "governance/score-v2-1e-real-data-research-authorization.json").exists():
        raise RuntimeError("consumed v2.1E authorization must remain absent")

    auth = protocol.get("authorizations")
    if not isinstance(auth, dict) or any(auth.values()):
        raise RuntimeError("v2.1F preregistration must not authorize execution")
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
    if not isinstance(source_rules, list) or len(source_rules) != 5:
        raise RuntimeError("expected exactly five v2.1F source rules")
    actual_series = {item["slot"]: item["exact_series_id"] for item in source_rules}
    actual_transforms = {item["slot"]: item["transform"] for item in source_rules}
    if actual_series != EXPECTED_SERIES:
        raise RuntimeError("v2.1F exact series inventory changed")
    if actual_transforms != EXPECTED_TRANSFORMS:
        raise RuntimeError("v2.1F transforms changed")

    serialized = json.dumps(source_rules).lower()
    for forbidden in ("h15/", "riflgfcy", "fred", "alfred", "wayback"):
        if forbidden in serialized:
            raise RuntimeError(f"forbidden rate/proxy dependency active: {forbidden}")

    energy = next(item for item in source_rules if item["slot"] == "ENERGY")
    if energy.get("max_release_age_calendar_days") != 45:
        raise RuntimeError("BLS energy release-age boundary changed")
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
    expected_weekly = {
        "target_start": "2015-01-02",
        "history_seed_start": "2013-01-01",
        "required_prior_complete_weeks": 104,
        "complete_case_history": True,
        "missing_slot_policy": "fail_closed_no_score",
        "dynamic_reweighting": False,
        "proxy_autofill": False,
        "latest_revised_history_fallback": False,
    }
    if weekly != expected_weekly:
        raise RuntimeError("v2.1F weekly matrix changed")

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
        raise RuntimeError("v2.1F preregistered weights changed")
    if score.get("regime_bands") != EXPECTED_BANDS:
        raise RuntimeError("v2.1F preregistered regime bands changed")
    if score.get("regime_bands_status") != "frozen_for_first_v2_1f_candidate_research_only":
        raise RuntimeError("regime-band freeze state changed")
    if abs(sum(abs(float(v)) for v in EXPECTED_WEIGHTS.values()) - 1.0) > 1e-12:
        raise RuntimeError("absolute weights must sum to 1.0")

    preflight = protocol.get("execution_preconditions_before_any_live_vintage_preflight", [])
    if "separate explicit owner authorization limited to live vintage feasibility only" not in preflight:
        raise RuntimeError("live-preflight owner gate missing")
    if "no candidate Score computation" not in preflight:
        raise RuntimeError("live preflight must forbid candidate Score computation")

    full = protocol.get("additional_preconditions_before_full_candidate_research", [])
    for required in (
        "live BLS WPU0561 historical archive/vintage feasibility passes",
        "retained H.10, H.8 and H.4.1 archive paths are revalidated for the authorized window",
        "a second separate explicit owner authorization permits full v2.1F candidate research",
    ):
        if required not in full:
            raise RuntimeError(f"missing full-research precondition: {required}")

    hard = protocol.get("hard_acceptance_gates", {})
    required_hard = {
        "source_scope_documented_for_all_slots": True,
        "zero_lookahead_violations": True,
        "exact_release_vintage_provenance_for_all_used_values": True,
        "current_revised_history_used_as_historical_vintage": False,
        "h15_or_rate_proxy_used": False,
        "transform_domain_errors": 0,
        "required_prior_complete_weeks": 104,
        "evaluated_week_complete_slot_coverage_min": 0.975,
        "each_slot_eligible_week_coverage_min": 0.98,
        "maximum_consecutive_missing_candidate_weeks": 2,
        "maximum_absolute_pairwise_spearman": 0.95,
        "maximum_variance_inflation_factor": 12,
        "maximum_first_principal_component_variance_share": 0.7,
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

    anti = "\n".join(str(x) for x in protocol.get("anti_tuning_rules", []))
    for phrase in (
        "No transform may change after any v2.1F real-data result is viewed",
        "No hard acceptance threshold may be relaxed after results are viewed",
        "No slot may be dropped, added, proxied or reweighted to rescue a failed candidate",
        "No H.15, FRED, ALFRED, Treasury-current-history, Wayback or other rate proxy",
        "No regime band may be re-fit from v2.1F candidate results",
    ):
        if phrase not in anti:
            raise RuntimeError(f"missing anti-tuning rule: {phrase}")

    if protocol.get("next_step_if_design_checks_pass") != (
        "separate_owner_authorization_for_v2_1f_live_vintage_feasibility_preflight_only"
    ):
        raise RuntimeError("unexpected next step")

    if design.get("state") != "design_only":
        raise RuntimeError("parent v2.1F design boundary changed")
    if design.get("methodology_version") != "2.1F-design-candidate":
        raise RuntimeError("parent v2.1F design version changed")
    if design.get("real_data_research_authorized") is not False:
        raise RuntimeError("parent design unexpectedly authorizes research")
    if design.get("production_authorized") is not False:
        raise RuntimeError("parent design unexpectedly authorizes Production")

    return {
        "status": "passed",
        "state": "preregistered_design_only",
        "slot_count": len(source_rules),
        "exact_series_pinned": True,
        "h15_removed": True,
        "vintage_rules_frozen": True,
        "thresholds_frozen_before_results": True,
        "point_in_time_normalization": True,
        "live_vintage_preflight_authorized": False,
        "full_candidate_research_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }

def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
