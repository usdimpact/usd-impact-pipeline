#!/usr/bin/env python3
"""Validate the review-only source-neutral Score replacement contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import usd_impact_score_v2 as score_v2

EXPECTED_YFINANCE_DRIVERS = {"DXY", "WTI", "SPX", "VIX", "BTC", "GOLD"}
EXPECTED_FRED_DRIVERS = {"UST_2Y", "UST_10Y"}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    contract = _load(repo_root / "governance/score-source-neutral-adapter-contract.json")
    gate = _load(repo_root / "governance/score-publication-rights-gate.json")
    migration = _load(repo_root / "governance/score-private-research-migration-contract.json")

    if contract.get("state") != "review_only":
        raise RuntimeError("source-neutral contract must remain review-only")
    for field in (
        "production_change_authorized",
        "real_provider_data_migration_authorized",
        "provider_purchase_or_contract_authorized",
        "live_fetch_switch_authorized",
    ):
        if contract.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if gate.get("state") != "hold" or gate.get("decision_receipt") is not None:
        raise RuntimeError("Score publication rights gate is not unresolved HOLD")
    if migration.get("real_provider_evidence_authorized") is not False:
        raise RuntimeError("real provider evidence is unexpectedly authorized")
    if migration.get("public_replacement_authorized") is not False:
        raise RuntimeError("public replacement is unexpectedly authorized")

    semantics = contract["score_semantics"]
    if semantics["start_date"] != score_v2.START_DATE:
        raise RuntimeError("source-neutral start date differs from production")
    if semantics["weekly_rule"] != score_v2.RESAMPLE_RULE:
        raise RuntimeError("source-neutral weekly rule differs from production")
    if float(semantics["zscore_clip"]) != float(score_v2.ZSCORE_CLIP):
        raise RuntimeError("source-neutral z-score clip differs from production")

    order = semantics["canonical_driver_order"]
    if order != list(score_v2.WEIGHTS):
        raise RuntimeError("canonical driver order differs from production")

    weights = {key: float(value) for key, value in semantics["weights"].items()}
    if weights != {key: float(value) for key, value in score_v2.WEIGHTS.items()}:
        raise RuntimeError("source-neutral weights differ from production")

    source_age_days = {
        key: int(value) for key, value in semantics["source_age_days"].items()
    }
    if source_age_days != {
        key: int(value) for key, value in score_v2.SOURCE_MAX_AGE_DAYS.items()
    }:
        raise RuntimeError("source-neutral freshness limits differ from production")

    current_sources = contract["current_sources"]
    if set(current_sources) != set(score_v2.TICKERS):
        raise RuntimeError("current source inventory differs from production drivers")

    yfinance_drivers = {
        driver
        for driver, item in current_sources.items()
        if item["provider_code"] == "yahoo"
    }
    fred_drivers = {
        driver
        for driver, item in current_sources.items()
        if item["provider_code"] == "fred"
    }
    if yfinance_drivers != EXPECTED_YFINANCE_DRIVERS:
        raise RuntimeError("unexpected yfinance driver set")
    if fred_drivers != EXPECTED_FRED_DRIVERS:
        raise RuntimeError("unexpected FRED driver set")

    for driver, (provider_code, series) in score_v2.TICKERS.items():
        item = current_sources[driver]
        if item["provider_code"] != provider_code:
            raise RuntimeError(f"{driver} provider code differs from production")
        if item["series"] != series:
            raise RuntimeError(f"{driver} series differs from production")

    adapter_output = contract["replacement_requirements"]["adapter_output"]
    if adapter_output["columns"] != list(score_v2.WEIGHTS):
        raise RuntimeError("adapter output columns differ from canonical driver order")
    if adapter_output["canonical_order_required"] is not True:
        raise RuntimeError("adapter must require canonical ordering")
    if adapter_output["extra_columns_forbidden"] is not True:
        raise RuntimeError("adapter must forbid extra columns")

    prohibited = set(contract["prohibited_shortcuts"])
    required_prohibitions = {
        "treat_yfinance_access_as_commercial_license",
        "change_instrument_or_price_semantics_to_fit_vendor",
        "change_score_weights_or_formula_during_source_migration",
        "mix_new_and_old_sources_without_explicit_parity_evidence",
    }
    if not required_prohibitions.issubset(prohibited):
        raise RuntimeError("source-neutral contract lacks required fail-closed prohibitions")

    return {
        "status": "passed",
        "review_only": True,
        "canonical_driver_count": len(order),
        "yfinance_driver_count": len(yfinance_drivers),
        "fred_driver_count": len(fred_drivers),
        "production_change_authorized": False,
        "real_provider_data_migration_authorized": False,
        "provider_purchase_or_contract_authorized": False,
        "live_fetch_switch_authorized": False,
        "score_formula_unchanged": True,
    }


def main() -> int:
    report = validate(Path(__file__).resolve().parents[1])
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
