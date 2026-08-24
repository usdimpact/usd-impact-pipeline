#!/usr/bin/env python3
"""Point-in-time normalization study for USD Impact Score v2.

Research-only. This script does not change the production score. It compares
production-style full-sample normalization with expanding-window normalization
that uses only observations strictly prior to each evaluated week.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import usd_impact_score_v2 as score_v2

DEFAULT_MIN_HISTORY = 52


def expanding_point_in_time_score(
    weekly: pd.DataFrame,
    *,
    min_history: int = DEFAULT_MIN_HISTORY,
) -> pd.DataFrame:
    drivers = list(score_v2.WEIGHTS)
    data = weekly[drivers].dropna().copy()
    rows: list[dict[str, Any]] = []

    for idx in range(min_history, len(data)):
        history = data.iloc[:idx]
        current = data.iloc[idx]
        date = data.index[idx]
        mu = history.mean()
        sd = history.std()
        if (sd == 0).any() or sd.isna().any():
            continue
        z_raw = (current - mu) / sd
        z = z_raw.clip(lower=-score_v2.ZSCORE_CLIP, upper=score_v2.ZSCORE_CLIP)
        score = float(sum(float(z[k]) * w for k, w in score_v2.WEIGHTS.items()))
        row: dict[str, Any] = {
            "date": date,
            "score_pit": score,
            "regime_pit": score_v2.label_regime(score),
            "history_start": history.index[0],
            "history_end": history.index[-1],
            "history_count": len(history),
        }
        for driver in drivers:
            row[f"{driver}_z_pit"] = float(z[driver])
        rows.append(row)

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).set_index("date")


def full_sample_score(weekly: pd.DataFrame) -> pd.DataFrame:
    drivers = list(score_v2.WEIGHTS)
    data = weekly[drivers].dropna().copy()
    mu = data.mean()
    sd = data.std()
    z = ((data - mu) / sd).clip(
        lower=-score_v2.ZSCORE_CLIP, upper=score_v2.ZSCORE_CLIP
    )
    score = sum(z[k] * w for k, w in score_v2.WEIGHTS.items())
    result = pd.DataFrame({"score_full_sample": score})
    result["regime_full_sample"] = score.apply(score_v2.label_regime)
    return result


def compare_scores(weekly: pd.DataFrame, *, min_history: int = DEFAULT_MIN_HISTORY) -> pd.DataFrame:
    pit = expanding_point_in_time_score(weekly, min_history=min_history)
    if pit.empty:
        return pit
    full = full_sample_score(weekly)
    joined = pit.join(full, how="left")
    joined["score_difference"] = joined["score_pit"] - joined["score_full_sample"]
    joined["regime_agreement"] = (
        joined["regime_pit"] == joined["regime_full_sample"]
    )
    return joined


def anchor_window_summary(comparison: pd.DataFrame) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for start, end, expected_sign, name in score_v2.BACKTEST_REGIMES:
        window = comparison.loc[start:end]
        if window.empty:
            continue
        pit_hits = int((np.sign(window["score_pit"]) == expected_sign).sum())
        full_hits = int((np.sign(window["score_full_sample"]) == expected_sign).sum())
        summaries.append({
            "name": name,
            "start": start,
            "end": end,
            "expected_sign": expected_sign,
            "weeks": int(len(window)),
            "pit_sign_hit_rate": pit_hits / len(window),
            "full_sample_sign_hit_rate": full_hits / len(window),
            "pit_mean_score": float(window["score_pit"].mean()),
            "full_sample_mean_score": float(window["score_full_sample"].mean()),
            "regime_label_agreement_rate": float(window["regime_agreement"].mean()),
        })
    return summaries


def build_report(weekly: pd.DataFrame, *, min_history: int = DEFAULT_MIN_HISTORY) -> dict[str, Any]:
    comparison = compare_scores(weekly, min_history=min_history)
    if comparison.empty:
        raise RuntimeError("Insufficient complete weekly history for point-in-time study")

    abs_diff = comparison["score_difference"].abs()
    return {
        "study": "usd_impact_score_v2_point_in_time_normalization",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "production_methodology_changed": False,
        "predictive_claim": False,
        "purpose": (
            "Robustness comparison only. PIT normalization for week t uses only "
            "complete weekly observations strictly before t."
        ),
        "min_prior_weeks": min_history,
        "first_evaluated_week": comparison.index[0].date().isoformat(),
        "last_evaluated_week": comparison.index[-1].date().isoformat(),
        "evaluated_weeks": int(len(comparison)),
        "summary": {
            "mean_absolute_score_difference": float(abs_diff.mean()),
            "max_absolute_score_difference": float(abs_diff.max()),
            "regime_label_agreement_rate": float(comparison["regime_agreement"].mean()),
        },
        "anchor_windows": anchor_window_summary(comparison),
        "weeks": [
            {
                "date": idx.date().isoformat(),
                "score_pit": float(row["score_pit"]),
                "regime_pit": row["regime_pit"],
                "score_full_sample": float(row["score_full_sample"]),
                "regime_full_sample": row["regime_full_sample"],
                "score_difference": float(row["score_difference"]),
                "regime_agreement": bool(row["regime_agreement"]),
                "history_start": row["history_start"].date().isoformat(),
                "history_end": row["history_end"].date().isoformat(),
                "history_count": int(row["history_count"]),
            }
            for idx, row in comparison.iterrows()
        ],
    }


def _load_weekly_levels(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["date"]).set_index("date")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weekly-levels", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-history", type=int, default=DEFAULT_MIN_HISTORY)
    args = parser.parse_args()

    weekly = _load_weekly_levels(args.weekly_levels)
    report = build_report(weekly, min_history=args.min_history)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"Point-in-time study: {report['evaluated_weeks']} weeks; "
        f"regime agreement {report['summary']['regime_label_agreement_rate']:.1%}; "
        f"mean |score diff| {report['summary']['mean_absolute_score_difference']:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
