#!/usr/bin/env python3
"""Validate the pending Score source-candidate evaluation template."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED_DRIVERS = ["DXY", "WTI", "SPX", "VIX", "BTC", "GOLD"]
RIGHTS_FIELDS = (
    "commercial_internal_use",
    "retention",
    "derived_internal_use",
    "public_aggregate_output",
    "public_component_output",
    "machine_readable_publication",
    "historical_archives",
)
PARITY_FIELDS = (
    "synthetic_adapter",
    "daily_history",
    "weekly_levels",
    "score_components",
    "aggregate_score",
    "regime",
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    template = _load(
        repo_root / "governance/score-source-candidate-evaluation.template.json"
    )
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")
    source_contract = _load(
        repo_root / "governance/score-source-neutral-adapter-contract.json"
    )

    if hold.get("state") != "hold" or hold.get("decision_receipt") is not None:
        raise RuntimeError("Score rights gate is not unresolved HOLD")
    if source_contract.get("state") != "review_only":
        raise RuntimeError("source-neutral contract is not review-only")
    if source_contract.get("live_fetch_switch_authorized") is not False:
        raise RuntimeError("live source switch is unexpectedly authorized")

    if template.get("state") != "review_only":
        raise RuntimeError("candidate template must remain review-only")
    if template.get("production_authorized") is not False:
        raise RuntimeError("candidate template must not authorize Production")

    evaluations = template.get("evaluations")
    if not isinstance(evaluations, list) or len(evaluations) != len(EXPECTED_DRIVERS):
        raise RuntimeError("candidate template must contain six evaluations")

    actual_drivers = [item.get("driver") for item in evaluations]
    if actual_drivers != EXPECTED_DRIVERS:
        raise RuntimeError("candidate evaluation driver order mismatch")

    for item in evaluations:
        driver = str(item["driver"])
        if item.get("state") != "pending":
            raise RuntimeError(f"{driver} candidate state must start pending")
        candidate = item.get("candidate")
        if not isinstance(candidate, dict):
            raise RuntimeError(f"{driver} candidate metadata missing")
        if any(candidate.get(field) is not None for field in (
            "provider", "product", "delivery_method", "commercial_contact_reference"
        )):
            raise RuntimeError(f"{driver} template must not preselect a provider")

        rights = item.get("rights")
        if not isinstance(rights, dict) or set(rights) != set(RIGHTS_FIELDS):
            raise RuntimeError(f"{driver} rights field set mismatch")
        if any(rights[field] != "pending" for field in RIGHTS_FIELDS):
            raise RuntimeError(f"{driver} rights must start pending")

        semantics = item.get("semantics")
        if not isinstance(semantics, dict):
            raise RuntimeError(f"{driver} semantics missing")
        if any(value is not None for value in semantics.values()):
            raise RuntimeError(f"{driver} semantics must start unset")

        parity = item.get("parity")
        if not isinstance(parity, dict) or set(parity) != set(PARITY_FIELDS):
            raise RuntimeError(f"{driver} parity field set mismatch")
        if any(parity[field] != "not_run" for field in PARITY_FIELDS):
            raise RuntimeError(f"{driver} parity must start not_run")

        decision = item.get("decision")
        if not isinstance(decision, dict) or decision.get("status") != "pending":
            raise RuntimeError(f"{driver} decision must start pending")
        if item.get("production_authorized") is not False:
            raise RuntimeError(f"{driver} must not authorize Production")

    return {
        "status": "passed",
        "review_only": True,
        "candidate_count": len(evaluations),
        "drivers": actual_drivers,
        "all_rights_pending": True,
        "all_parity_not_run": True,
        "provider_preselected": False,
        "live_fetch_switch_authorized": False,
        "production_authorized": False,
    }


def main() -> int:
    report = validate(Path(__file__).resolve().parents[1])
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
