#!/usr/bin/env python3
"""Research-only robustness battery for USD Impact Score v2.

This module does not alter the production score. It evaluates specification
sensitivity using the same eight production drivers and fixed transmission
signs, while keeping all outputs explicitly descriptive and non-predictive.

Published research outputs are current-vintage recalculations. They are not
as-published historical vintages and must not be represented as such.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

import usd_impact_score_v2 as score_v2
from scripts.point_in_time_validation import build_report as build_pit_report

DEFAULT_CORRELATION_WINDOW = 52
DEFAULT_ROLLING_WINDOWS = (104, 156, 260)
DEFAULT_MIN_HISTORY = 52


class _QuietLogger:
    def debug(self, *_args, **_kwargs):
        pass

    def info(self, *_args, **_kwargs):
        pass

    def warning(self, *_args, **_kwargs):
        pass

    def error(self, *_args, **_kwargs):
        pass


def _complete_weekly(weekly: pd.DataFrame) -> pd.DataFrame:
    drivers = list(score_v2.WEIGHTS)
    missing = [driver for driver in drivers if driver not in weekly.columns]
    if missing:
        raise RuntimeError(f"Weekly levels missing required drivers: {missing}")
    data = weekly[drivers].dropna().copy()
    if data.empty:
        raise RuntimeError("No complete weekly observations available")
    return data


def _full_sample_components(weekly: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    data = _complete_weekly(weekly)
    mu = data.mean()
    sd = data.std()
    if (sd == 0).any() or sd.isna().any():
        raise RuntimeError("Invalid full-sample standard deviation")
    z = ((data - mu) / sd).clip(
        lower=-score_v2.ZSCORE_CLIP,
        upper=score_v2.ZSCORE_CLIP,
    )
    score = sum(z[k] * w for k, w in score_v2.WEIGHTS.items())
    score.name = "score"
    return z, score


def leave_one_driver_out(weekly: pd.DataFrame) -> list[dict[str, Any]]:
    """Measure score sensitivity to removing one driver at a time.

    Remaining signed weights are rescaled proportionally so their absolute
    magnitudes sum to 1.0. This is a diagnostic only, not an alternative model.
    """
    z, baseline = _full_sample_components(weekly)
    baseline_regime = baseline.apply(score_v2.label_regime)
    results: list[dict[str, Any]] = []

    for omitted in score_v2.WEIGHTS:
        remaining = {k: v for k, v in score_v2.WEIGHTS.items() if k != omitted}
        abs_sum = sum(abs(v) for v in remaining.values())
        normalized = {k: v / abs_sum for k, v in remaining.items()}
        alt = sum(z[k] * w for k, w in normalized.items())
        alt_regime = alt.apply(score_v2.label_regime)
        results.append({
            "omitted_driver": omitted,
            "remaining_absolute_weight_sum": float(sum(abs(v) for v in normalized.values())),
            "latest_score": float(alt.iloc[-1]),
            "latest_score_difference": float(alt.iloc[-1] - baseline.iloc[-1]),
            "mean_absolute_score_difference": float((alt - baseline).abs().mean()),
            "max_absolute_score_difference": float((alt - baseline).abs().max()),
            "sign_agreement_rate": float((np.sign(alt) == np.sign(baseline)).mean()),
            "regime_label_agreement_rate": float((alt_regime == baseline_regime).mean()),
            "latest_regime": alt_regime.iloc[-1],
        })
    return results


def _rolling_prior_score(data: pd.DataFrame, window: int) -> pd.Series:
    rows: list[tuple[pd.Timestamp, float]] = []
    for idx in range(window, len(data)):
        history = data.iloc[idx - window:idx]
        current = data.iloc[idx]
        mu = history.mean()
        sd = history.std()
        if (sd == 0).any() or sd.isna().any():
            continue
        z = ((current - mu) / sd).clip(
            lower=-score_v2.ZSCORE_CLIP,
            upper=score_v2.ZSCORE_CLIP,
        )
        score = float(sum(float(z[k]) * w for k, w in score_v2.WEIGHTS.items()))
        rows.append((data.index[idx], score))
    if not rows:
        return pd.Series(dtype=float, name=f"rolling_{window}")
    series = pd.Series({date: score for date, score in rows}, name=f"rolling_{window}")
    series.index = pd.DatetimeIndex(series.index)
    return series.sort_index()


def rolling_window_sensitivity(
    weekly: pd.DataFrame,
    *,
    windows: Iterable[int] = DEFAULT_ROLLING_WINDOWS,
) -> list[dict[str, Any]]:
    data = _complete_weekly(weekly)
    _, baseline = _full_sample_components(data)
    results: list[dict[str, Any]] = []

    for window in windows:
        if window < 2:
            raise ValueError("Rolling normalization windows must be at least 2 weeks")
        alt = _rolling_prior_score(data, int(window))
        if alt.empty:
            continue
        aligned = baseline.loc[alt.index]
        alt_regime = alt.apply(score_v2.label_regime)
        baseline_regime = aligned.apply(score_v2.label_regime)
        results.append({
            "prior_window_weeks": int(window),
            "evaluated_weeks": int(len(alt)),
            "first_evaluated_week": alt.index[0].date().isoformat(),
            "last_evaluated_week": alt.index[-1].date().isoformat(),
            "latest_score": float(alt.iloc[-1]),
            "latest_full_sample_score": float(aligned.iloc[-1]),
            "mean_absolute_score_difference_vs_full_sample": float((alt - aligned).abs().mean()),
            "max_absolute_score_difference_vs_full_sample": float((alt - aligned).abs().max()),
            "sign_agreement_rate_vs_full_sample": float((np.sign(alt) == np.sign(aligned)).mean()),
            "regime_label_agreement_rate_vs_full_sample": float((alt_regime == baseline_regime).mean()),
        })
    return results


def correlation_concentration(
    weekly: pd.DataFrame,
    *,
    window: int = DEFAULT_CORRELATION_WINDOW,
) -> dict[str, Any]:
    """Describe correlation concentration among production input levels.

    This intentionally measures the level series consumed by v2, not returns.
    Level correlations can reflect common trends and must not be interpreted as
    stable structural correlations.
    """
    data = _complete_weekly(weekly)
    if window < 3:
        raise ValueError("Correlation window must be at least 3 weeks")
    sample = data.tail(min(window, len(data)))
    corr = sample.corr()
    pairs: list[dict[str, Any]] = []
    names = list(corr.columns)
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            value = float(corr.loc[left, right])
            if not np.isfinite(value):
                continue
            pairs.append({"left": left, "right": right, "correlation": value})
    pairs.sort(key=lambda item: abs(item["correlation"]), reverse=True)
    absolute = [abs(item["correlation"]) for item in pairs]
    return {
        "diagnostic": "Pearson correlation of production weekly level inputs",
        "caution": "Level correlations may reflect common trends and are not return correlations.",
        "window_weeks": int(len(sample)),
        "window_start": sample.index[0].date().isoformat(),
        "window_end": sample.index[-1].date().isoformat(),
        "mean_absolute_pair_correlation": float(np.mean(absolute)) if absolute else None,
        "max_absolute_pair_correlation": float(max(absolute)) if absolute else None,
        "pairs_at_or_above_abs_0_70": int(sum(value >= 0.70 for value in absolute)),
        "top_pairs": pairs[:10],
    }


def _label_with_thresholds(score: float, neutral: float, strong: float) -> str:
    if score >= strong:
        return "Strong dollar regime"
    if score >= neutral:
        return "Firm dollar regime"
    if score > -neutral:
        return "Neutral / transitional"
    if score > -strong:
        return "Soft dollar regime"
    return "Weak dollar regime"


def threshold_sensitivity(weekly: pd.DataFrame) -> list[dict[str, Any]]:
    _, score = _full_sample_components(weekly)
    production = score.apply(score_v2.label_regime)
    variants = [
        ("narrower", 0.20, 0.80),
        ("production", 0.30, 1.00),
        ("wider", 0.40, 1.20),
    ]
    results: list[dict[str, Any]] = []
    for name, neutral, strong in variants:
        labels = score.apply(lambda value: _label_with_thresholds(float(value), neutral, strong))
        results.append({
            "variant": name,
            "neutral_boundary": neutral,
            "strong_boundary": strong,
            "latest_regime": labels.iloc[-1],
            "label_agreement_rate_vs_production": float((labels == production).mean()),
        })
    return results


def subperiod_stability(weekly: pd.DataFrame) -> list[dict[str, Any]]:
    _, score = _full_sample_components(weekly)
    latest = score.index[-1].date().isoformat()
    periods = [
        ("2015-2018", "2015-01-01", "2018-12-31"),
        ("2019-2021", "2019-01-01", "2021-12-31"),
        ("2022-latest", "2022-01-01", latest),
    ]
    results: list[dict[str, Any]] = []
    for name, start, end in periods:
        window = score.loc[start:end]
        if window.empty:
            continue
        regimes = window.apply(score_v2.label_regime)
        results.append({
            "period": name,
            "start": start,
            "end": end,
            "weeks": int(len(window)),
            "mean_score": float(window.mean()),
            "score_std": float(window.std()),
            "min_score": float(window.min()),
            "max_score": float(window.max()),
            "positive_score_share": float((window > 0).mean()),
            "negative_score_share": float((window < 0).mean()),
            "neutral_regime_share": float((regimes == "Neutral / transitional").mean()),
        })
    return results


def build_robustness_report(
    weekly: pd.DataFrame,
    *,
    min_history: int = DEFAULT_MIN_HISTORY,
    rolling_windows: Iterable[int] = DEFAULT_ROLLING_WINDOWS,
    correlation_window: int = DEFAULT_CORRELATION_WINDOW,
    source_provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = _complete_weekly(weekly)
    _, production_score = _full_sample_components(data)
    pit = build_pit_report(data, min_history=min_history)
    return {
        "study": "usd_impact_score_v2_robustness_battery",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "production_methodology_changed": False,
        "predictive_claim": False,
        "as_published_vintage": False,
        "purpose": (
            "Descriptive robustness diagnostics for the production v2 specification. "
            "Results are current-vintage recalculations and do not change the production score."
        ),
        "data": {
            "production_start_date": score_v2.START_DATE,
            "first_complete_week": data.index[0].date().isoformat(),
            "latest_complete_week": data.index[-1].date().isoformat(),
            "complete_weeks": int(len(data)),
            "latest_production_recalculated_score": float(production_score.iloc[-1]),
            "latest_production_recalculated_regime": score_v2.label_regime(float(production_score.iloc[-1])),
            "source_provenance": source_provenance,
        },
        "point_in_time_normalization": {
            "min_prior_weeks": pit["min_prior_weeks"],
            "first_evaluated_week": pit["first_evaluated_week"],
            "last_evaluated_week": pit["last_evaluated_week"],
            "evaluated_weeks": pit["evaluated_weeks"],
            "summary": pit["summary"],
            "anchor_windows": pit["anchor_windows"],
        },
        "leave_one_driver_out": leave_one_driver_out(data),
        "rolling_normalization": rolling_window_sensitivity(data, windows=rolling_windows),
        "correlation_concentration": correlation_concentration(data, window=correlation_window),
        "regime_threshold_sensitivity": threshold_sensitivity(data),
        "subperiod_stability": subperiod_stability(data),
        "limitations": [
            "The production score is descriptive, not predictive.",
            "Current-vintage source histories can differ from historical as-published vintages.",
            "Leave-one-out and rolling-window variants are diagnostics, not alternative production models.",
            "Correlation diagnostics use the weekly input levels consumed by v2 and may reflect common trends.",
            "2008 is outside canonical v2 because the production specification begins in 2015 and includes Bitcoin.",
        ],
    }


def load_live_weekly() -> tuple[pd.DataFrame, dict[str, Any]]:
    logger = _QuietLogger()
    now = datetime.now(timezone.utc)
    score_week = score_v2.latest_completed_friday(now)
    daily = score_v2.fetch_all_inputs(score_v2.START_DATE, logger, as_of=now)
    provenance = daily.attrs.get("source_provenance")
    if not isinstance(provenance, dict):
        raise RuntimeError("Live input fetch did not return source provenance")
    score_v2.validate_source_freshness(provenance, score_week, logger)
    weekly = score_v2.resample_weekly(daily, logger, completed_friday=score_week)
    data = _complete_weekly(weekly)
    if data.index[-1].date() != score_week:
        raise RuntimeError(
            f"Latest complete week {data.index[-1].date()} does not match expected {score_week}"
        )
    return data, provenance


def _load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["date"]).set_index("date")


def main() -> int:
    parser = argparse.ArgumentParser(description="USD Impact Score v2 robustness research")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--live", action="store_true")
    source.add_argument("--weekly-levels", type=Path)
    parser.add_argument("--robustness-output", type=Path, required=True)
    parser.add_argument("--pit-output", type=Path, required=True)
    parser.add_argument("--min-history", type=int, default=DEFAULT_MIN_HISTORY)
    args = parser.parse_args()

    if args.live:
        weekly, provenance = load_live_weekly()
    else:
        weekly = _load_csv(args.weekly_levels)
        provenance = None

    robust = build_robustness_report(
        weekly,
        min_history=args.min_history,
        source_provenance=provenance,
    )
    pit = build_pit_report(_complete_weekly(weekly), min_history=args.min_history)
    pit["source_provenance"] = provenance
    pit["as_published_vintage"] = False
    pit["limitations"] = [
        "This is a current-vintage point-in-time normalization study, not a predictive backtest.",
        "The production v2 score remains unchanged.",
        "Historical upstream data may differ from values available at the original publication date.",
    ]

    for path, payload in (
        (args.robustness_output, robust),
        (args.pit_output, pit),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        "Score v2 robustness research generated for "
        f"{robust['data']['latest_complete_week']}; "
        f"PIT regime agreement {pit['summary']['regime_label_agreement_rate']:.1%}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
