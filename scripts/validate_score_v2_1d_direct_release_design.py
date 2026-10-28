#!/usr/bin/env python3
"""Validate design-only Score v2.1D direct-release architecture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED = [
    ("USD", "DTWEXBGS"),
    ("ENERGY", "DCOILWTICO"),
    ("FIN_CONDITIONS", "BOARD_H8_BANK_CREDIT_ALL"),
    ("FIN_STRESS", "BOARD_H41_PRIMARY_CREDIT"),
    ("LIQUIDITY", "WALCL"),
    ("REAL_YIELD", "DFII10"),
    ("UST_2Y", "DGS2"),
    ("UST_10Y", "DGS10"),
]


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    design = _load(repo_root / "governance/score-v2-1d-direct-release-design.json")
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")

    if design.get("state") != "design_only":
        raise RuntimeError("v2.1D must remain design-only")
    if design.get("candidate_class") != "direct_board_eia_release_architecture":
        raise RuntimeError("unexpected v2.1D candidate class")
    if design.get("budget_constraint") != "zero_paid_market_data_budget":
        raise RuntimeError("zero-budget constraint missing")
    if design.get("legal_conclusion") is not False:
        raise RuntimeError("design must not claim a legal conclusion")
    if design.get("no_source_approved") is not True:
        raise RuntimeError("design must not approve sources")
    if hold.get("state") != "hold":
        raise RuntimeError("rights HOLD must remain active")

    auth = design.get("authorizations")
    if not isinstance(auth, dict) or any(auth.values()):
        raise RuntimeError("v2.1D must not authorize execution")
    if design.get("real_data_research_authorized") is not False:
        raise RuntimeError("real-data research must remain unauthorized")
    if design.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    slots = design.get("proposed_slots")
    if not isinstance(slots, list) or len(slots) != 8:
        raise RuntimeError("v2.1D must define exactly eight slots")
    actual = [(item.get("slot"), item.get("source_key")) for item in slots]
    if actual != EXPECTED:
        raise RuntimeError("v2.1D slot/source inventory changed")

    for item in slots:
        if abs(float(item.get("weight", 0))) != 0.125:
            raise RuntimeError(f"{item.get('slot')} weight changed")
        if "approved" in str(item.get("rights_status", "")).lower():
            raise RuntimeError(f"{item.get('slot')} cannot be marked approved")

    if abs(sum(abs(float(item["weight"])) for item in slots) - 1.0) > 1e-12:
        raise RuntimeError("absolute weights must sum to 1.0")

    by_slot = {item["slot"]: item for item in slots}
    if by_slot["FIN_CONDITIONS"]["transform"] != "negative_log_change_13_weeks":
        raise RuntimeError("bank-credit transform changed")
    if by_slot["FIN_STRESS"]["transform"] != "log1p_level":
        raise RuntimeError("primary-credit stress transform changed")

    rules = design.get("structural_rules", {})
    if rules.get("observation_date_is_not_release_date") is not True:
        raise RuntimeError("release-time discipline missing")
    if rules.get("point_in_time_release_provenance_required") is not True:
        raise RuntimeError("release provenance must remain mandatory")
    if rules.get("minimum_prior_complete_weeks") != 104:
        raise RuntimeError("minimum history changed")
    if rules.get("normalization") != "expanding_point_in_time_zscore":
        raise RuntimeError("normalization boundary changed")
    if rules.get("missing_slot_policy") != "fail_closed_no_score":
        raise RuntimeError("missing slots must fail closed")
    if rules.get("dynamic_reweighting") is not False:
        raise RuntimeError("dynamic reweighting must remain forbidden")

    advantage = design.get("direct_release_advantage", {})
    if advantage.get("composite_private_input_slots") != 0:
        raise RuntimeError("v2.1D must not depend on composite private-input slots")
    if advantage.get("direct_board_slots") != 7 or advantage.get("direct_eia_slots") != 1:
        raise RuntimeError("direct source-family count changed")

    prereg = set(design.get("preregistration_requirements", []))
    required = {
        "exact H.8 Board series/item mapping",
        "exact H.4.1 Primary Credit series/item mapping",
        "release-vintage archive strategy",
        "primary-credit sparse-distribution diagnostics",
        "acceptance thresholds fixed before results",
        "separate real_data_research_authorization",
    }
    if not required.issubset(prereg):
        raise RuntimeError("v2.1D preregistration requirements incomplete")

    return {
        "status": "passed",
        "state": "design_only",
        "slot_count": len(slots),
        "composite_private_input_slots": 0,
        "direct_board_slots": 7,
        "direct_eia_slots": 1,
        "real_data_research_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
