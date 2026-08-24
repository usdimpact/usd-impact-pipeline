#!/usr/bin/env python3
"""Research-only implementation of the four preregistered Score v3 candidates.

The engine reads candidate formulas, weights, clipping, thresholds and holdout
rules from research/score_v3_preregistration.json. It does not change or replace
production Score v2 and contains no predictive/trading objective.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

LOCKED_PREREGISTRATION_SHA = "bf49152fa6005edd20b770db287924d56cfa7499"
PROTOCOL_PATH = Path("research/score_v3_preregistration.json")
EXPECTED_CANDIDATE_IDS = (
    "V3_E52",
    "V3_R260",
    "V3_MAD260",
    "V3_GRP_MAD260",
)
EXPECTED_DRIVERS = (
    "DXY",
    "WTI",
    "SPX",
    "VIX",
    "BTC",
    "GOLD",
    "UST_2Y",
    "UST_10Y",
)


def load_protocol(path: Path = PROTOCOL_PATH) -> dict[str, Any]:
    protocol = json.loads(path.read_text(encoding="utf-8"))
    ids = tuple(candidate.get("candidate_id") for candidate in protocol.get("candidates", []))
    if protocol.get("protocol_version") != 1:
        raise RuntimeError("Unsupported Score v3 protocol version")
    if protocol.get("production_change") is not False:
        raise RuntimeError("Score v3 research protocol unexpectedly authorizes production change")
    if protocol.get("predictive_claim") is not False:
        raise RuntimeError("Score v3 research protocol unexpectedly contains a predictive claim")
    if ids != EXPECTED_CANDIDATE_IDS:
        raise RuntimeError(
            "Candidate set differs from locked protocol implementation contract; "
            "a versioned protocol/code change is required"
        )
    boundary = protocol.get("knowledge_boundary", {})
    if boundary.get("prospective_untouched_holdout_start") != "2026-08-28":
        raise RuntimeError("Unexpected Score v3 prospective holdout start")
    rules = protocol.get("common_rules", {})
    if rules.get("zscore_clip") != 3.5:
        raise RuntimeError("Unexpected Score v3 z-score clip")
    if rules.get("normalization_moments_for_week_t_must_exclude_week_t") is not True:
        raise RuntimeError("Protocol no longer requires prior-only normalization")
    if rules.get("normalization_moments_for_week_t_must_exclude_future_weeks") is not True:
        raise RuntimeError("Protocol no longer excludes future normalization data")
    return protocol


def _candidate(protocol: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    if candidate_id not in EXPECTED_CANDIDATE_IDS:
        raise KeyError(f"Unknown/unauthorized candidate: {candidate_id}")
    for candidate in protocol["candidates"]:
        if candidate["candidate_id"] == candidate_id:
            return candidate
    raise RuntimeError(f"Candidate {candidate_id} missing from protocol")


def candidate_weights(protocol: dict[str, Any], candidate_id: str) -> dict[str, float]:
    raw = _candidate(protocol, candidate_id)["weights"]
    weights = {driver: float(raw[driver]) for driver in EXPECTED_DRIVERS}
    if set(raw) - {"type", *EXPECTED_DRIVERS}:
        raise RuntimeError(f"Candidate {candidate_id} contains unexpected weight fields")
    if not math.isclose(sum(abs(value) for value in weights.values()), 1.0, rel_tol=0, abs_tol=1e-12):
        raise RuntimeError(f"Candidate {candidate_id} absolute weight budget is not 1.0")
    return weights


def regime_label(score: float, protocol: dict[str, Any]) -> str:
    matches: list[str] = []
    for band in protocol["fixed_regime_thresholds_for_primary_comparison"]:
        low = band["low"]
        high = band["high"]
        low_ok = low is None or score >= float(low)
        high_ok = high is None or score < float(high)
        if low_ok and high_ok:
            matches.append(str(band["label"]))
    if len(matches) != 1:
        raise RuntimeError(f"Regime thresholds produced {len(matches)} matches for score {score}")
    return matches[0]


def _history_for_week(
    data: pd.DataFrame,
    current_pos: int,
    candidate: dict[str, Any],
    protocol: dict[str, Any],
) -> pd.DataFrame:
    normalization = candidate["normalization"]
    history = data.iloc[:current_pos]
    normalization_type = normalization["type"]

    if normalization_type == "expanding_prior_only_mean_std":
        minimum = int(normalization.get("minimum_weeks", protocol["common_rules"]["minimum_prior_complete_weeks"]))
        if len(history) < minimum:
            raise ValueError(f"insufficient_history:{len(history)}<{minimum}")
        return history

    if normalization_type in {
        "rolling_prior_only_mean_std",
        "rolling_prior_only_median_mad",
    }:
        window = int(normalization["history_weeks"])
        if len(history) < window:
            raise ValueError(f"insufficient_history:{len(history)}<{window}")
        return history.iloc[-window:]

    raise RuntimeError(f"Unsupported normalization type: {normalization_type}")


def _normalize(
    current: pd.Series,
    history: pd.DataFrame,
    normalization: dict[str, Any],
    clip: float,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    normalization_type = normalization["type"]
    if normalization_type in {
        "expanding_prior_only_mean_std",
        "rolling_prior_only_mean_std",
    }:
        center = history.mean()
        scale = history.std(ddof=1)
    elif normalization_type == "rolling_prior_only_median_mad":
        center = history.median()
        mad = (history - center).abs().median()
        scale = mad * 1.4826
    else:
        raise RuntimeError(f"Unsupported normalization type: {normalization_type}")

    invalid = scale.isna() | ~np.isfinite(scale) | (scale <= 0)
    if invalid.any():
        drivers = list(scale.index[invalid])
        raise RuntimeError(f"zero_or_invalid_scale:{','.join(drivers)}")

    z_raw = (current - center) / scale
    if z_raw.isna().any() or not np.isfinite(z_raw.to_numpy(dtype=float)).all():
        raise RuntimeError("candidate normalization produced a non-finite z-score")
    z = z_raw.clip(lower=-clip, upper=clip)
    return z_raw, z, scale


def compute_candidate_week(
    weekly_levels: pd.DataFrame,
    week: pd.Timestamp | str,
    candidate_id: str,
    *,
    protocol: dict[str, Any] | None = None,
) -> dict[str, Any]:
    protocol = protocol or load_protocol()
    candidate = _candidate(protocol, candidate_id)
    clip = float(protocol["common_rules"]["zscore_clip"])

    missing = [driver for driver in EXPECTED_DRIVERS if driver not in weekly_levels.columns]
    if missing:
        raise RuntimeError(f"Weekly levels missing required drivers: {missing}")

    data = weekly_levels[list(EXPECTED_DRIVERS)].dropna().sort_index().copy()
    if not data.index.is_unique:
        raise RuntimeError("Weekly levels index must be unique")
    target = pd.Timestamp(week).normalize()
    positions = np.flatnonzero(data.index.normalize() == target)
    if len(positions) != 1:
        raise KeyError(f"Expected exactly one complete row for week {target.date()}")
    pos = int(positions[0])
    current = data.iloc[pos]
    history = _history_for_week(data, pos, candidate, protocol)

    if not (history.index < data.index[pos]).all():
        raise RuntimeError("Candidate history includes week t or future data")

    z_raw, z, scale = _normalize(current, history, candidate["normalization"], clip)
    weights = candidate_weights(protocol, candidate_id)
    contributions = {driver: float(z[driver]) * weights[driver] for driver in EXPECTED_DRIVERS}
    score = float(sum(contributions.values()))
    if not math.isfinite(score):
        raise RuntimeError("Candidate score is not finite")

    return {
        "candidate_id": candidate_id,
        "week": data.index[pos].date().isoformat(),
        "score": score,
        "regime": regime_label(score, protocol),
        "history_start": history.index[0].date().isoformat(),
        "history_end": history.index[-1].date().isoformat(),
        "history_count": int(len(history)),
        "normalization_type": candidate["normalization"]["type"],
        "clip": clip,
        "levels": {driver: float(current[driver]) for driver in EXPECTED_DRIVERS},
        "scale": {driver: float(scale[driver]) for driver in EXPECTED_DRIVERS},
        "z_unclipped": {driver: float(z_raw[driver]) for driver in EXPECTED_DRIVERS},
        "z_clipped": {driver: float(z[driver]) for driver in EXPECTED_DRIVERS},
        "weights": weights,
        "contributions": contributions,
    }


def compute_candidate_series(
    weekly_levels: pd.DataFrame,
    candidate_id: str,
    *,
    protocol: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    protocol = protocol or load_protocol()
    data = weekly_levels[list(EXPECTED_DRIVERS)].dropna().sort_index()
    rows: list[dict[str, Any]] = []
    for week in data.index:
        try:
            rows.append(compute_candidate_week(data, week, candidate_id, protocol=protocol))
        except ValueError as error:
            if str(error).startswith("insufficient_history:"):
                continue
            raise
    return rows


def structural_readiness_report(weekly_levels: pd.DataFrame) -> dict[str, Any]:
    protocol = load_protocol()
    candidates = []
    for candidate_id in EXPECTED_CANDIDATE_IDS:
        rows = compute_candidate_series(weekly_levels, candidate_id, protocol=protocol)
        if not rows:
            raise RuntimeError(f"Candidate {candidate_id} produced no retrospective structural rows")
        candidates.append({
            "candidate_id": candidate_id,
            "rows": len(rows),
            "first_week": rows[0]["week"],
            "last_week": rows[-1]["week"],
            "all_scores_finite": all(math.isfinite(float(row["score"])) for row in rows),
            "absolute_weight_budget": sum(abs(value) for value in rows[-1]["weights"].values()),
        })
    return {
        "report_type": "score_v3_structural_readiness",
        "research_only": True,
        "predictive_claim": False,
        "candidate_selection_performed": False,
        "locked_preregistration_commit_sha": LOCKED_PREREGISTRATION_SHA,
        "retrospective_data_status": "current_vintage_not_untouched",
        "candidates": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weekly-levels", type=Path, required=True)
    parser.add_argument("--readiness-output", type=Path)
    args = parser.parse_args()

    weekly = pd.read_csv(args.weekly_levels, parse_dates=["date"]).set_index("date")
    report = structural_readiness_report(weekly)
    if args.readiness_output:
        args.readiness_output.parent.mkdir(parents=True, exist_ok=True)
        args.readiness_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
