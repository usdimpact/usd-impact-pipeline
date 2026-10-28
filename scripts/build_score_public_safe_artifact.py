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


def _canonical_history_bytes(history: list[dict[str, Any]]) -> bytes:
    return (
        json.dumps(history, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _numeric(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    return float(value)


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

    history = payload.get("history")
    if not isinstance(history, list) or not history:
        raise ValueError("public-safe payload must contain history")
    for index, row in enumerate(history):
        if set(row) != ALLOWED_HISTORY_KEYS:
            raise ValueError(
                f"history row {index} must contain only "
                f"{sorted(ALLOWED_HISTORY_KEYS)}"
            )


def write_outputs(
    payload: dict[str, Any],
    json_output: Path,
    csv_output: Path,
) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
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
