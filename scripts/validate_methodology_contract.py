#!/usr/bin/env python3
"""Fail closed when the public Score v2 methodology contract drifts from code.

This validator intentionally uses only production constants and standard-library
JSON handling. The public JSON Schema is provided for third-party tooling; CI
uses exact semantic comparison so no additional schema dependency can silently
change the validation behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

import usd_impact_score_v2 as score_v2


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "public/data/score_v2_methodology.json"
DEFAULT_SCHEMA = ROOT / "public/data/score_v2_methodology.schema.json"
CONTRACT_VERSION = 1
REPRO_REQUIRED_FROM = "2026-08-28"
REPRO_BUNDLE_VERSION = 1
REPRO_TOLERANCE = 1e-9


def _regime_bands() -> list[dict[str, Any]]:
    return [
        {
            "low": None if not np.isfinite(low) else float(low),
            "high": None if not np.isfinite(high) else float(high),
            "label": label,
        }
        for low, high, label in score_v2.REGIME_BANDS
    ]


def expected_contract() -> dict[str, Any]:
    drivers = []
    for name, (provider_code, series) in score_v2.TICKERS.items():
        drivers.append(
            {
                "name": name,
                "provider_code": provider_code,
                "provider": score_v2.SOURCE_PROVIDER_LABELS[provider_code],
                "series": series,
                "source_url": score_v2.SOURCE_URLS[name],
                "max_age_days": int(score_v2.SOURCE_MAX_AGE_DAYS[name]),
                "weight": float(score_v2.WEIGHTS[name]),
            }
        )

    return {
        "$schema": "./score_v2_methodology.schema.json",
        "contract_version": CONTRACT_VERSION,
        "methodology_version": "usd_impact_score_v2",
        "status": "production",
        "purpose": "descriptive weekly U.S. dollar regime indicator",
        "predictive_claim": False,
        "production_start_date": score_v2.START_DATE,
        "frequency": {
            "resample_rule": score_v2.RESAMPLE_RULE,
            "weekly_observation": "last available observation in the Friday-ended week",
        },
        "normalization": {
            "input_type": "weekly levels",
            "sample": "full available complete weekly sample",
            "mean": "arithmetic mean",
            "standard_deviation": "sample standard deviation",
            "ddof": 1,
            "zscore_clip": float(score_v2.ZSCORE_CLIP),
        },
        "missing_data": {
            "daily_alignment": "outer join across providers",
            "forward_fill_limit_observations": 3,
            "weekly_complete_case_required": True,
            "latest_week_complete_required": True,
        },
        "correlation_adjustment": "none",
        "weights_rebalanced": False,
        "drivers": drivers,
        "regime_bands": _regime_bands(),
        "source_provenance_version": int(score_v2.SOURCE_PROVENANCE_VERSION),
        "reproduction_bundle": {
            "bundle_version": REPRO_BUNDLE_VERSION,
            "required_from_release": REPRO_REQUIRED_FROM,
            "absolute_tolerance": REPRO_TOLERANCE,
        },
        "scope_boundaries": {
            "predictive_backtest": False,
            "canonical_2008_result": False,
            "historical_full_sample_series_is_point_in_time": False,
        },
    }


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Missing or empty JSON file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected top-level JSON object: {path}")
    return payload


def validate_schema_document(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError("Methodology schema must use JSON Schema draft 2020-12")
    if schema.get("$id") != (
        "https://usd-impact-pipeline.pages.dev/data/score_v2_methodology.schema.json"
    ):
        raise ValueError("Unexpected methodology schema $id")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        raise ValueError("Methodology schema must be a closed top-level object")

    expected_keys = set(expected_contract())
    required = schema.get("required")
    properties = schema.get("properties")
    if set(required or []) != expected_keys:
        raise ValueError("Methodology schema required fields do not match the contract")
    if set((properties or {}).keys()) != expected_keys:
        raise ValueError("Methodology schema properties do not match the contract")


def validate_contract(
    contract_path: Path = DEFAULT_CONTRACT,
    schema_path: Path = DEFAULT_SCHEMA,
) -> dict[str, Any]:
    contract = _load_json(contract_path)
    schema = _load_json(schema_path)
    validate_schema_document(schema)

    expected = expected_contract()
    if contract != expected:
        expected_text = json.dumps(expected, indent=2, ensure_ascii=False, sort_keys=True)
        actual_text = json.dumps(contract, indent=2, ensure_ascii=False, sort_keys=True)
        raise ValueError(
            "Public Score v2 methodology contract differs from production constants.\n"
            f"EXPECTED:\n{expected_text}\nACTUAL:\n{actual_text}"
        )

    contract_sha256 = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    return {
        "methodology_version": contract["methodology_version"],
        "contract_version": contract["contract_version"],
        "contract_sha256": contract_sha256,
        "driver_count": len(contract["drivers"]),
        "status": "verified",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--json", action="store_true", help="Print the verification result as JSON")
    args = parser.parse_args()

    result = validate_contract(args.contract, args.schema)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            "Score v2 methodology contract verified: "
            f"{result['driver_count']} drivers, SHA-256 {result['contract_sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
