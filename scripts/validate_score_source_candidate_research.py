#!/usr/bin/env python3
"""Validate public-evidence-only Score source candidate research."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED_DRIVERS = ["DXY", "SPX", "VIX", "WTI", "GOLD", "BTC"]


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    research = _load(
        repo_root / "governance/score-source-candidate-public-research.json"
    )
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")
    template = _load(
        repo_root / "governance/score-source-candidate-evaluation.template.json"
    )

    if hold.get("state") != "hold" or hold.get("decision_receipt") is not None:
        raise RuntimeError("Score rights gate is not unresolved HOLD")
    if research.get("state") != "public_evidence_only":
        raise RuntimeError("candidate research must remain public-evidence-only")
    for field in (
        "production_authorized",
        "provider_purchase_or_contract_authorized",
        "real_data_rehearsal_authorized",
    ):
        if research.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    candidates = research.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != len(EXPECTED_DRIVERS):
        raise RuntimeError("candidate research must contain six shortlisted drivers")

    actual = [item.get("driver") for item in candidates]
    if actual != EXPECTED_DRIVERS:
        raise RuntimeError("candidate research driver order mismatch")

    for item in candidates:
        if item.get("rights_status") != "license_required_or_confirmation_pending":
            raise RuntimeError(f"{item.get('driver')} rights status is not fail-closed")
        if not item.get("unresolved"):
            raise RuntimeError(f"{item.get('driver')} must retain unresolved conditions")
        evidence = item.get("public_evidence")
        if not isinstance(evidence, dict) or not evidence.get("official_url"):
            raise RuntimeError(f"{item.get('driver')} lacks official public evidence")

    recommendation = research.get("recommendation")
    if not isinstance(recommendation, dict):
        raise RuntimeError("candidate research recommendation missing")
    if recommendation.get("no_vendor_selected") is not True:
        raise RuntimeError("candidate research must not select a vendor")

    if template.get("production_authorized") is not False:
        raise RuntimeError("candidate evaluation template unexpectedly authorizes Production")
    if any(
        evaluation["decision"]["status"] != "pending"
        for evaluation in template["evaluations"]
    ):
        raise RuntimeError("candidate evaluation template no longer starts pending")

    return {
        "status": "passed",
        "public_evidence_only": True,
        "candidate_count": len(candidates),
        "drivers": actual,
        "vendor_selected": False,
        "real_data_rehearsal_authorized": False,
        "provider_purchase_or_contract_authorized": False,
        "production_authorized": False,
    }


def main() -> int:
    report = validate(Path(__file__).resolve().parents[1])
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
