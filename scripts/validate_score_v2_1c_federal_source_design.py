#!/usr/bin/env python3
"""Validate the design-only, public-evidence Score v2.1C candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED = [
    ("USD", "DTWEXBGS"),
    ("ENERGY", "DCOILWTICO"),
    ("FIN_CONDITIONS", "FCI_G_BASELINE_MONTHLY"),
    ("FIN_STRESS", "OFR_FSI"),
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
    design = _load(repo_root / "governance/score-v2-1c-federal-source-design.json")
    rights = _load(repo_root / "governance/score-v2-1c-public-rights-evidence.json")
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")

    if design.get("state") != "design_only":
        raise RuntimeError("v2.1C must remain design-only")
    if design.get("candidate_class") != "rights_minimized_federal_source_architecture":
        raise RuntimeError("unexpected candidate class")
    if design.get("budget_constraint") != "zero_paid_market_data_budget":
        raise RuntimeError("zero-budget constraint missing")
    if design.get("legal_conclusion") is not False or rights.get("legal_conclusion") is not False:
        raise RuntimeError("public evidence packet must not claim a legal conclusion")
    if hold.get("state") != "hold":
        raise RuntimeError("rights HOLD must remain active")

    auth = design.get("authorizations")
    if not isinstance(auth, dict) or any(auth.values()):
        raise RuntimeError("v2.1C design must not authorize execution")
    if design.get("real_data_research_authorized") is not False:
        raise RuntimeError("real-data research must remain unauthorized")
    if design.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    slots = design.get("proposed_slots")
    if not isinstance(slots, list) or len(slots) != 8:
        raise RuntimeError("v2.1C must define eight slots")
    actual = [(item.get("slot"), item.get("canonical_id")) for item in slots]
    if actual != EXPECTED:
        raise RuntimeError("v2.1C slot/source inventory changed")

    for item in slots:
        status = str(item.get("rights_status", ""))
        if "required" not in status and "candidate" not in status:
            raise RuntimeError(f"{item['slot']} rights status is unexpectedly final")
        if item.get("weight") is None or abs(float(item["weight"])) != 0.125:
            raise RuntimeError(f"{item['slot']} weight changed")

    if abs(sum(abs(float(item["weight"])) for item in slots) - 1.0) > 1e-12:
        raise RuntimeError("absolute weights must sum to 1.0")

    if rights.get("state") != "public_evidence_only":
        raise RuntimeError("rights packet must remain public-evidence-only")
    if rights.get("no_source_approved") is not True:
        raise RuntimeError("no source may be pre-approved")
    if rights.get("production_authorized") is not False:
        raise RuntimeError("rights packet must not authorize Production")
    rows = rights.get("rows")
    if not isinstance(rows, list) or len(rows) != 8:
        raise RuntimeError("rights matrix must cover all eight series")
    for row in rows:
        unresolved = row.get("unresolved")
        if not isinstance(unresolved, list) or not unresolved:
            raise RuntimeError(f"{row.get('series')} must retain unresolved checks")

    deprioritized = {item.get("series") for item in rights.get("rejected_or_deprioritized", [])}
    if deprioritized != {"NFCI", "STLFSI4"}:
        raise RuntimeError("rights-minimized exclusions changed")

    timing = design.get("timing_constraints", {})
    if timing.get("observation_date_is_not_release_date") is not True:
        raise RuntimeError("release-time discipline must remain explicit")
    if timing.get("FCI_G_max_age_calendar_days") != 45:
        raise RuntimeError("FCI-G stale-age boundary changed")
    if timing.get("mixed_frequency_fail_closed") is not True:
        raise RuntimeError("mixed-frequency candidate must fail closed")

    return {
        "status": "passed",
        "state": "design_only",
        "slot_count": len(slots),
        "no_source_approved": True,
        "legal_conclusion": False,
        "real_data_research_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
