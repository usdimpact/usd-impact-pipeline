#!/usr/bin/env python3
"""Validate design-only Score v2.1B official-macro alternative."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED_SLOTS = [
    "USD",
    "ENERGY",
    "FIN_CONDITIONS",
    "FIN_STRESS",
    "LIQUIDITY",
    "REAL_YIELD",
    "UST_2Y",
    "UST_10Y",
]

EXPECTED_SERIES = {
    "USD": "DTWEXBGS",
    "ENERGY": "DCOILWTICO",
    "FIN_CONDITIONS": "NFCI",
    "FIN_STRESS": "STLFSI4",
    "LIQUIDITY": "WALCL",
    "REAL_YIELD": "DFII10",
    "UST_2Y": "DGS2",
    "UST_10Y": "DGS10",
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    design = _load(
        repo_root / "governance/score-v2-1b-official-macro-design.json"
    )
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")

    if design.get("state") != "design_only":
        raise RuntimeError("v2.1B must remain design-only")
    if design.get("candidate_class") != "official_macro_proxy_architecture":
        raise RuntimeError("unexpected v2.1B candidate class")
    if design.get("budget_constraint") != "zero_paid_market_data_budget":
        raise RuntimeError("zero-budget constraint missing")
    if hold.get("state") != "hold":
        raise RuntimeError("rights HOLD must remain active")

    authorizations = design.get("authorizations")
    if not isinstance(authorizations, dict) or any(authorizations.values()):
        raise RuntimeError("v2.1B design must not authorize execution or Production")
    if design.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    slots = design.get("proposed_slots")
    if not isinstance(slots, list) or len(slots) != 8:
        raise RuntimeError("v2.1B must define exactly eight slots")
    actual_slots = [item.get("slot") for item in slots]
    if actual_slots != EXPECTED_SLOTS:
        raise RuntimeError("v2.1B slot order mismatch")

    for item in slots:
        slot = item["slot"]
        if item.get("series") != EXPECTED_SERIES[slot]:
            raise RuntimeError(f"{slot} series changed")
        if item.get("rights_state") != "confirm_reuse_scope":
            raise RuntimeError(f"{slot} rights scope cannot be pre-approved")
        if abs(float(item.get("weight", 0))) != 0.125:
            raise RuntimeError(f"{slot} must retain explicit equal absolute weight")

    total_abs = sum(abs(float(item["weight"])) for item in slots)
    if abs(total_abs - 1.0) > 1e-12:
        raise RuntimeError("absolute weights must sum to 1.0")

    rules = design.get("structural_rules", {})
    if rules.get("missing_slot_policy") != "fail_closed_no_score":
        raise RuntimeError("missing slots must fail closed")
    if rules.get("no_dynamic_reweighting") is not True:
        raise RuntimeError("dynamic reweighting must remain forbidden")
    if rules.get("no_unapproved_proxy_autofill") is not True:
        raise RuntimeError("proxy autofill must remain forbidden")
    if rules.get("weekly_anchor") != "Friday":
        raise RuntimeError("weekly anchor must remain Friday")

    requirements = set(design.get("preregistration_requirements", []))
    required = {
        "exact transformation per slot",
        "point_in_time availability lag per source",
        "acceptance thresholds",
        "separate real_data_research_authorization",
    }
    if not required.issubset(requirements):
        raise RuntimeError("v2.1B preregistration requirements are incomplete")

    diagnostics = set(design.get("mandatory_research_diagnostics", []))
    if "pairwise_slot_correlation_matrix" not in diagnostics:
        raise RuntimeError("redundancy diagnostics missing")
    if "leave_one_slot_out_sensitivity" not in diagnostics:
        raise RuntimeError("slot sensitivity diagnostics missing")

    return {
        "status": "passed",
        "state": "design_only",
        "slot_count": len(slots),
        "complete_conceptual_candidate": True,
        "all_rights_pending_confirmation": True,
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
