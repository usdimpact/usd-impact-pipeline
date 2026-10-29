#!/usr/bin/env python3
"""Build an aggregate-only Score v2 public artifact.

Review-only prototype. This script is intentionally not wired into the production
weekly workflow. It demonstrates that the public Score/regime product can be
derived from the existing release JSON without redistributing per-driver
provider-derived levels, z-scores, contributions, normalization moments, or
source provenance.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "score-public-v2-safe-1"

FORBIDDEN_KEYS = {
    "source_provenance",
    "source_provenance_version",
    "provider",
    "provider_code",
    "series",
    "source_url",
    "observation_date",
    "weekly_level",
    "z",
    "z_unclipped",
    "z_clipped",
    "contribution",
    "normalization",
    "mean",
    "sample_std_ddof_1",
}

ALLOWED_HISTORY_KEYS = {"date", "score", "regime"}
EXPECTED_WEIGHTS = {
    "DXY": 0.125,
    "WTI": -0.125,
    "SPX": -0.125,
    "VIX": 0.125,
    "BTC": -0.125,
    "GOLD": -0.125,
    "UST_2Y": 0.125,
    "UST_10Y": 0.125,
}
ROOT_KEYS = {"schema_version", "metadata", "latest", "history", "release_evidence"}
METADATA_KEYS = {"pipeline", "generated_at_utc", "n_weeks", "weights"}
LATEST_KEYS = {
    "week_ending", "score", "regime",
    "week_over_week_change", "four_week_change",
}
EVIDENCE_KEYS = {"aggregate_history_sha256"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _strict_keys(value: Any, expected: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{label} must contain exactly: {sorted(expected)}")


def _friday(value: Any, label: str) -> date:
    if not isinstance(value, str) or not DATE_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must be a YYYY-MM-DD Friday")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid calendar date") from exc
    if parsed.weekday() != 4:
        raise ValueError(f"{label} must be a Friday")
    return parsed


def _valid_utc_timestamp(value: Any) -> None:
    if value is None:
        return  # Synthetic private-research receipts can omit generation time.
    if not isinstance(value, str):
        raise ValueError("generated_at_utc must be an ISO UTC timestamp or null")
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("generated_at_utc must be an ISO UTC timestamp") from exc
    if stamp.tzinfo is None or stamp.utcoffset() != timedelta(0):
        raise ValueError("generated_at_utc must include a UTC offset")


def _expected_regime(score: float) -> str:
    # Frozen production Score v2 thresholds, used only to validate synthetic
    # and reviewed aggregate payloads. The Score engine is not modified.
    if score >= 1.0:
        return "Strong dollar regime"
    if score >= 0.3:
        return "Firm dollar regime"
    if score >= -0.3:
        return "Neutral / transitional"
    if score >= -1.0:
        return "Soft dollar regime"
    return "Weak dollar regime"


def _canonical_history_bytes(history: list[dict[str, Any]]) -> bytes:
    return (
        json.dumps(history, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _numeric(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def build_public_safe_payload(source: dict[str, Any]) -> dict[str, Any]:
    metadata = source.get("metadata")
    weeks = source.get("weeks")
    if not isinstance(metadata, dict):
        raise ValueError("score source is missing metadata")
    if not isinstance(weeks, list) or not weeks:
        raise ValueError("score source is missing weekly history")

    history: list[dict[str, Any]] = []
    for index, row in enumerate(weeks):
        if not isinstance(row, dict):
            raise ValueError(f"week {index} must be an object")
        date = row.get("date")
        regime = row.get("regime")
        if not isinstance(date, str) or not date:
            raise ValueError(f"week {index} has no date")
        if not isinstance(regime, str) or not regime:
            raise ValueError(f"week {index} has no regime")
        score = _numeric(row.get("score"), f"week {index} score")
        history.append({"date": date, "score": score, "regime": regime})

    latest = history[-1]
    previous_score = history[-2]["score"] if len(history) >= 2 else latest["score"]
    four_week_anchor = history[-5]["score"] if len(history) >= 5 else history[0]["score"]

    weights = metadata.get("weights")
    if not isinstance(weights, dict) or not weights:
        raise ValueError("score source is missing methodology weights")
    safe_weights: dict[str, float] = {}
    for name, value in weights.items():
        if not isinstance(name, str) or not name:
            raise ValueError("weight names must be non-empty strings")
        safe_weights[name] = _numeric(value, f"weight {name}")

    public_payload = {
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "pipeline": str(metadata.get("pipeline") or "usd_impact_score_v2"),
            "generated_at_utc": metadata.get("generated_at_utc"),
            "n_weeks": len(history),
            "weights": safe_weights,
        },
        "latest": {
            "week_ending": latest["date"],
            "score": latest["score"],
            "regime": latest["regime"],
            "week_over_week_change": latest["score"] - previous_score,
            "four_week_change": latest["score"] - four_week_anchor,
        },
        "history": history,
        "release_evidence": {
            "aggregate_history_sha256": hashlib.sha256(
                _canonical_history_bytes(history)
            ).hexdigest()
        },
    }
    assert_public_safe(public_payload)
    return public_payload


def assert_public_safe(payload: Any) -> None:
    """Closed, numeric-safe contract for the *inactive* aggregate prototype.

    Schema narrowing and passing this check are NOT a commercial license or
    permission to redistribute even aggregate provider-derived Score data.
    """
    _strict_keys(payload, ROOT_KEYS, "aggregate payload")

    def walk(value: Any, path: str = "$") -> None:
        if isinstance(value, dict):
            forbidden = FORBIDDEN_KEYS.intersection(value)
            if forbidden:
                raise ValueError(
                    f"public-safe payload contains forbidden keys at {path}: "
                    + ", ".join(sorted(forbidden))
                )
            for key, child in value.items():
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(payload)
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported aggregate-safe schema version")

    metadata = payload["metadata"]
    _strict_keys(metadata, METADATA_KEYS, "aggregate metadata")
    if metadata["pipeline"] != "usd_impact_score_v2":
        raise ValueError("metadata pipeline must be the frozen v2 identifier")
    _valid_utc_timestamp(metadata["generated_at_utc"])
    _strict_keys(metadata["weights"], set(EXPECTED_WEIGHTS), "methodology weights")
    for name, expected in EXPECTED_WEIGHTS.items():
        if _numeric(metadata["weights"][name], f"weight {name}") != expected:
            raise ValueError(f"weight {name} differs from frozen methodology")

    history = payload["history"]
    if not isinstance(history, list) or not history:
        raise ValueError("public-safe payload must contain history")
    n = metadata["n_weeks"]
    if isinstance(n, bool) or not isinstance(n, int) or n != len(history):
        raise ValueError("metadata week count does not match history")

    previous_date: date | None = None
    for index, row in enumerate(history):
        _strict_keys(row, ALLOWED_HISTORY_KEYS, f"history row {index}")
        week = _friday(row["date"], f"history row {index} date")
        if previous_date is not None and week <= previous_date:
            raise ValueError("aggregate history must be strictly chronological")
        previous_date = week
        score = _numeric(row["score"], f"history row {index} score")
        if row["regime"] != _expected_regime(score):
            raise ValueError(f"history row {index} has an inconsistent regime")

    latest = payload["latest"]
    _strict_keys(latest, LATEST_KEYS, "latest")
    _friday(latest["week_ending"], "latest week ending")
    if latest["week_ending"] != history[-1]["date"]:
        raise ValueError("latest date must match final history row")
    if _numeric(latest["score"], "latest score") != history[-1]["score"]:
        raise ValueError("latest score must match final history row")
    if latest["regime"] != history[-1]["regime"]:
        raise ValueError("latest regime must match final history row")
    prior = history[-2]["score"] if len(history) >= 2 else history[-1]["score"]
    anchor = history[-5]["score"] if len(history) >= 5 else history[0]["score"]
    if _numeric(latest["week_over_week_change"], "weekly change") != (
        latest["score"] - prior
    ):
        raise ValueError("weekly aggregate change does not match history")
    if _numeric(latest["four_week_change"], "four-week change") != (
        latest["score"] - anchor
    ):
        raise ValueError("four-week aggregate change does not match history")

    evidence = payload["release_evidence"]
    _strict_keys(evidence, EVIDENCE_KEYS, "release evidence")
    expected_hash = hashlib.sha256(_canonical_history_bytes(history)).hexdigest()
    if evidence["aggregate_history_sha256"] != expected_hash:
        raise ValueError("aggregate history SHA256 does not match payload")


def write_outputs(
    payload: dict[str, Any],
    json_output: Path,
    csv_output: Path,
) -> None:
    assert_public_safe(payload)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    with csv_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "score", "regime"])
        writer.writeheader()
        writer.writerows(payload["history"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--score-json", required=True, type=Path)
    parser.add_argument("--json-output", required=True, type=Path)
    parser.add_argument("--csv-output", required=True, type=Path)
    args = parser.parse_args()

    source = json.loads(args.score_json.read_text(encoding="utf-8"))
    payload = build_public_safe_payload(source)
    write_outputs(payload, args.json_output, args.csv_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
