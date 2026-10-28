#!/usr/bin/env python3
"""Validate v2.1C series-specific public-evidence receipts remain fail-closed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED = {
    "USD": "DTWEXBGS",
    "ENERGY": "DCOILWTICO",
    "FIN_CONDITIONS": "FCI_G_BASELINE_MONTHLY",
    "FIN_STRESS": "OFR_FSI",
    "LIQUIDITY": "WALCL",
    "REAL_YIELD": "DFII10",
    "UST_2Y": "DGS2",
    "UST_10Y": "DGS10",
}

BLOCKED = {"FIN_CONDITIONS", "FIN_STRESS"}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    receipt = _load(repo_root / "governance/score-v2-1c-series-receipts.json")
    design = _load(repo_root / "governance/score-v2-1c-federal-source-design.json")
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")

    if receipt.get("state") != "public_evidence_series_receipts_only":
        raise RuntimeError("series receipt state changed")
    if receipt.get("legal_conclusion") is not False:
        raise RuntimeError("receipt must not claim legal conclusion")
    if receipt.get("no_source_approved") is not True:
        raise RuntimeError("receipt must not approve sources")
    for field in (
        "real_data_fetch_authorized",
        "real_data_research_authorized",
        "production_authorized",
    ):
        if receipt.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")
    if hold.get("state") != "hold":
        raise RuntimeError("rights HOLD must remain active")
    if design.get("state") != "design_only":
        raise RuntimeError("parent v2.1C design must remain design-only")

    rows = receipt.get("series_receipts")
    if not isinstance(rows, list) or len(rows) != 8:
        raise RuntimeError("receipt must cover exactly eight slots")
    actual = {row.get("slot"): row.get("canonical_id") for row in rows}
    if actual != EXPECTED:
        raise RuntimeError("slot/source receipt inventory changed")

    for row in rows:
        for required in (
            "official_source_page",
            "official_delivery_page",
            "release_schedule",
            "point_in_time_rule",
            "attribution",
            "rights_basis",
            "third_party_input_risk",
            "revision_vintage_risk",
            "status",
        ):
            if not row.get(required):
                raise RuntimeError(f"{row.get('slot')} missing {required}")
        if "approved" in str(row.get("status", "")).lower():
            raise RuntimeError(f"{row.get('slot')} status must not claim approval")

    blocked = {
        row["slot"]
        for row in rows
        if str(row["status"]).startswith("conditional_blocked")
    }
    if blocked != BLOCKED:
        raise RuntimeError("conditional blocked slot set changed")

    summary = receipt.get("summary", {})
    if summary.get("strong_candidate_count") != 6:
        raise RuntimeError("strong candidate count changed")
    if summary.get("conditional_blocked_count") != 2:
        raise RuntimeError("blocked candidate count changed")
    if summary.get("blocked_slots") != ["FIN_CONDITIONS", "FIN_STRESS"]:
        raise RuntimeError("blocked slot ordering changed")
    if summary.get("exact_complete_eight_slot_candidate_rights_ready") is not False:
        raise RuntimeError("receipt must not claim complete rights readiness")
    if summary.get("source_approval_authorized") is not False:
        raise RuntimeError("receipt must not authorize source approval")

    ofr = next(row for row in rows if row["slot"] == "FIN_STRESS")
    if "Refinitiv" not in ofr["third_party_input_risk"]:
        raise RuntimeError("OFR FSI private-input risk must remain explicit")

    fcig = next(row for row in rows if row["slot"] == "FIN_CONDITIONS")
    if "private" not in fcig["third_party_input_risk"].lower():
        raise RuntimeError("FCI-G private-input risk must remain explicit")

    return {
        "status": "passed",
        "state": "public_evidence_series_receipts_only",
        "slot_count": len(rows),
        "strong_candidate_count": 6,
        "conditional_blocked_count": 2,
        "exact_complete_eight_slot_candidate_rights_ready": False,
        "real_data_research_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
