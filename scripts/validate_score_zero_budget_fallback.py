#!/usr/bin/env python3
"""Validate zero-budget Score fallback planning remains fail-closed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED = ["DXY","WTI","SPX","VIX","BTC","GOLD","UST_2Y","UST_10Y"]


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    matrix = _load(repo_root / "governance/score-zero-budget-fallback-matrix.json")
    gate = _load(repo_root / "governance/score-publication-rights-gate.json")

    if gate.get("state") != "hold":
        raise RuntimeError("Score rights gate must remain HOLD")
    if matrix.get("state") != "review_only":
        raise RuntimeError("zero-budget matrix must remain review-only")
    if matrix.get("budget_constraint") != "zero_paid_market_data_budget":
        raise RuntimeError("zero-budget constraint missing")
    for field in (
        "production_authorized",
        "methodology_change_authorized",
        "real_data_rehearsal_authorized",
    ):
        if matrix.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    drivers = matrix.get("drivers")
    if not isinstance(drivers, list) or [d.get("driver") for d in drivers] != EXPECTED:
        raise RuntimeError("zero-budget driver inventory mismatch")

    proprietary = {"DXY","WTI","SPX","VIX","BTC","GOLD"}
    for item in drivers:
        driver = item["driver"]
        if driver in proprietary and item.get("disposition") == "retain_if_rights_confirmed":
            raise RuntimeError(f"{driver} cannot be treated as retained by default")

    conclusion = matrix.get("conclusion", {})
    if conclusion.get("exact_v2_zero_budget_path_confirmed") is not False:
        raise RuntimeError("exact v2 zero-budget path must remain unconfirmed")
    if conclusion.get("next_allowed_step") != (
        "wait_for_provider_rights_responses_or_prepare_methodology_change_options_only"
    ):
        raise RuntimeError("unexpected next-step authorization")

    return {
        "status":"passed",
        "review_only":True,
        "zero_budget":True,
        "driver_count":len(drivers),
        "exact_v2_zero_budget_path_confirmed":False,
        "methodology_change_authorized":False,
        "real_data_rehearsal_authorized":False,
        "production_authorized":False,
    }


def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
