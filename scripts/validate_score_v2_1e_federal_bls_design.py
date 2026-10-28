#!/usr/bin/env python3
"""Validate design-only Score v2.1E federal/BLS candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED = [
    ("USD", "H10/H10/JRXWTFB_N.B"),
    ("ENERGY", "WPU0561"),
    ("FIN_CONDITIONS", "H8/H8/B1001NCBA"),
    ("FIN_STRESS", "H41/H41/RESPPALDP_N.WW"),
    ("LIQUIDITY", "H41/H41/RESPPA_N.WW"),
    ("REAL_YIELD", "H15/H15/RIFLGFCY10_XII_N.B"),
    ("UST_2Y", "H15/H15/RIFLGFCY02_N.B"),
    ("UST_10Y", "H15/H15/RIFLGFCY10_N.B"),
]

def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return data

def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    design = _load(repo_root / "governance/score-v2-1e-federal-bls-design.json")
    receipts = _load(repo_root / "governance/score-v2-1e-exact-series-receipts.json")
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")

    if design.get("state") != "design_only":
        raise RuntimeError("v2.1E must remain design-only")
    if design.get("candidate_class") != "direct_federal_board_bls_release_architecture":
        raise RuntimeError("unexpected v2.1E candidate class")
    if design.get("budget_constraint") != "zero_paid_market_data_budget":
        raise RuntimeError("zero-budget constraint missing")
    if design.get("legal_conclusion") is not False:
        raise RuntimeError("v2.1E may not claim a legal conclusion")
    if design.get("no_source_approved") is not True:
        raise RuntimeError("v2.1E may not pre-approve sources")
    if hold.get("state") != "hold":
        raise RuntimeError("rights HOLD must remain active")

    auth = design.get("authorizations")
    if not isinstance(auth, dict) or any(auth.values()):
        raise RuntimeError("v2.1E design may not authorize execution")
    if design.get("real_data_research_authorized") is not False:
        raise RuntimeError("real-data research must remain unauthorized")
    if design.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    slots = design.get("proposed_slots")
    if not isinstance(slots, list) or len(slots) != 8:
        raise RuntimeError("v2.1E must define exactly eight slots")
    actual = [(item.get("slot"), item.get("exact_series_id")) for item in slots]
    if actual != EXPECTED:
        raise RuntimeError("v2.1E exact series inventory changed")
    for item in slots:
        if abs(float(item.get("weight", 0))) != 0.125:
            raise RuntimeError(f"{item['slot']} weight changed")
        if "approved" in str(item.get("rights_status", "")).lower():
            raise RuntimeError(f"{item['slot']} rights status appears approved")

    if sum(abs(float(item["weight"])) for item in slots) != 1.0:
        raise RuntimeError("absolute weights must sum to 1.0")

    energy = next(item for item in slots if item["slot"] == "ENERGY")
    if energy.get("source_family") != "U.S. Bureau of Labor Statistics":
        raise RuntimeError("v2.1E energy source must remain BLS")
    if energy.get("exact_series_id") != "WPU0561":
        raise RuntimeError("BLS crude petroleum series changed")
    if "four months" not in str(energy.get("revision_rule", "")).lower():
        raise RuntimeError("BLS revision handling is not explicit")

    serialized = json.dumps(design).lower()
    for forbidden in ("dcoilwtico", "rwtc", "refinitiv", "lseg"):
        if forbidden in serialized:
            raise RuntimeError(f"forbidden prior energy dependency remains: {forbidden}")

    rules = design.get("structural_rules", {})
    if rules.get("observation_date_is_not_release_date") is not True:
        raise RuntimeError("release-time discipline changed")
    if rules.get("point_in_time_release_provenance_required") is not True:
        raise RuntimeError("release provenance must remain mandatory")
    if rules.get("missing_slot_policy") != "fail_closed_no_score":
        raise RuntimeError("missing slot policy must remain fail closed")
    if rules.get("dynamic_reweighting") is not False:
        raise RuntimeError("dynamic reweighting must remain forbidden")
    if rules.get("proxy_autofill") is not False:
        raise RuntimeError("proxy autofill must remain forbidden")
    if rules.get("minimum_prior_complete_weeks") != 104:
        raise RuntimeError("minimum prior history changed")
    if float(rules.get("zscore_clip")) != 3.5:
        raise RuntimeError("z-score clip changed")

    if receipts.get("state") != "public_evidence_exact_series_receipts_only":
        raise RuntimeError("receipt packet state changed")
    if receipts.get("legal_conclusion") is not False:
        raise RuntimeError("receipt packet may not claim a legal conclusion")
    if receipts.get("no_source_approved") is not True:
        raise RuntimeError("receipt packet may not approve a source")
    if receipts.get("real_data_fetch_authorized") is not False:
        raise RuntimeError("receipt packet may not authorize real-data fetch")
    if receipts.get("real_data_research_authorized") is not False:
        raise RuntimeError("receipt packet may not authorize real-data research")
    if receipts.get("production_authorized") is not False:
        raise RuntimeError("receipt packet may not authorize Production")

    receipt_rows = receipts.get("series_receipts")
    if not isinstance(receipt_rows, list) or len(receipt_rows) != 8:
        raise RuntimeError("receipt packet must cover all eight slots")
    if [(row.get("slot"), row.get("exact_series_id")) for row in receipt_rows] != EXPECTED:
        raise RuntimeError("receipt exact-series inventory changed")

    blocker = receipts.get("blocker_removed", {})
    if blocker.get("prior_candidate") != "v2.1D":
        raise RuntimeError("prior blocked candidate reference changed")
    if blocker.get("replacement") != "BLS WPU0561":
        raise RuntimeError("v2.1E replacement is not pinned")
    if blocker.get("silent_substitution") is not False:
        raise RuntimeError("silent substitution must remain forbidden")

    return {
        "status":"passed",
        "state":"design_only",
        "slot_count":len(slots),
        "exact_series_pinned":True,
        "refinitiv_wti_dependency_removed":True,
        "real_data_research_authorized":False,
        "production_authorized":False,
        "rights_hold":True,
    }

def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
