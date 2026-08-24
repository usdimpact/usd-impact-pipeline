#!/usr/bin/env python3
"""Validate the supplemental source and calendar semantics contract."""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
from typing import Any

import usd_impact_score_v2 as score_v2


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "public/data/score_v2_data_semantics.json"
DEFAULT_SCHEMA = ROOT / "public/data/score_v2_data_semantics.schema.json"


def _load_object(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Missing or empty JSON file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a top-level JSON object: {path}")
    return payload


def validate_contract(
    contract_path: Path = DEFAULT_CONTRACT,
    schema_path: Path = DEFAULT_SCHEMA,
) -> dict[str, Any]:
    contract = _load_object(contract_path)
    schema = _load_object(schema_path)

    expected_top_level = {
        "$schema", "contract_version", "methodology_version", "status",
        "production_methodology_changed", "purpose", "retrieval", "alignment",
        "futures", "revision_policy", "vendor_resilience",
    }
    if set(contract) != expected_top_level:
        raise ValueError("Unexpected data-semantics contract fields")
    if set(schema.get("required", [])) != expected_top_level:
        raise ValueError("Schema required fields do not match the contract")
    if set(schema.get("properties", {})) != expected_top_level:
        raise ValueError("Schema properties do not match the contract")
    if schema.get("additionalProperties") is not False:
        raise ValueError("Data-semantics schema must be closed at the top level")
    if contract["contract_version"] != 1:
        raise ValueError("Unsupported data-semantics contract version")
    if contract["methodology_version"] != "usd_impact_score_v2":
        raise ValueError("Unexpected methodology version")
    if contract["production_methodology_changed"] is not False:
        raise ValueError("Supplemental contract must not claim a methodology change")

    yahoo = contract["retrieval"]["yahoo"]
    if yahoo["field"] != "Close" or yahoo["auto_adjust"] is not True:
        raise ValueError("Yahoo field semantics differ from the production contract")
    if yahoo["threads"] is not False:
        raise ValueError("Yahoo retrieval threading differs from production")
    fred = contract["retrieval"]["fred"]
    if fred["date_field"] != "observation_date":
        raise ValueError("FRED date semantics differ from production")

    alignment = contract["alignment"]
    if alignment["forward_fill_limit_observations"] != 3:
        raise ValueError("Forward-fill semantics differ from production")
    if alignment["weekly_rule"] != score_v2.RESAMPLE_RULE:
        raise ValueError("Weekly resampling rule differs from production")

    expected_futures = {"WTI": score_v2.TICKERS["WTI"][1], "GOLD": score_v2.TICKERS["GOLD"][1]}
    for driver, symbol in expected_futures.items():
        if contract["futures"][driver]["symbol"] != symbol:
            raise ValueError(f"{driver} futures symbol differs from production")

    # These source checks turn prose drift into a CI failure if the underlying
    # implementation later changes without a corresponding contract review.
    yahoo_source = inspect.getsource(score_v2.fetch_yahoo)
    fred_source = inspect.getsource(score_v2.fetch_fred)
    inputs_source = inspect.getsource(score_v2.fetch_all_inputs)
    weekly_source = inspect.getsource(score_v2.resample_weekly)
    invariants = {
        "Yahoo Close field": 'raw["Close"]' in yahoo_source and '["Close"]' in yahoo_source,
        "Yahoo auto_adjust": "auto_adjust=True" in yahoo_source,
        "Yahoo non-threaded": "threads=False" in yahoo_source,
        "FRED endpoint": "fredgraph.csv?id=" in fred_source,
        "FRED observation_date": 'parse_dates=["observation_date"]' in fred_source,
        "outer join": 'join(fred_df, how="outer")' in inputs_source,
        "three-observation fill": "ffill(limit=3)" in inputs_source,
        "Friday-ended last value": ".resample(RESAMPLE_RULE).last()" in weekly_source,
    }
    failed = [name for name, passed in invariants.items() if not passed]
    if failed:
        raise ValueError("Production implementation drift: " + ", ".join(failed))

    return {
        "contract_version": contract["contract_version"],
        "methodology_version": contract["methodology_version"],
        "implementation_invariants": len(invariants),
        "status": "verified",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate_contract(args.contract, args.schema)
    print(json.dumps(result, indent=2) if args.json else "Data semantics contract verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
