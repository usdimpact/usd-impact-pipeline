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


def sign_sensitivity(weekly: pd.DataFrame) -> list[dict[str, Any]]:
    """Flip each transmission sign while holding every other choice fixed.

    This deliberately adversarial diagnostic asks how much the published score
    depends on each directional assumption. It is not an alternative model and
    does not select signs from the observed results.
    """
    z, baseline = _full_sample_components(weekly)
    baseline_regime = baseline.apply(score_v2.label_regime)
    results: list[dict[str, Any]] = []

    for flipped in score_v2.WEIGHTS:
        weights = dict(score_v2.WEIGHTS)
        weights[flipped] = -weights[flipped]
        alt = sum(z[k] * w for k, w in weights.items())
        alt_regime = alt.apply(score_v2.label_regime)
        results.append({
            "flipped_driver": flipped,
            "production_weight": float(score_v2.WEIGHTS[flipped]),
            "diagnostic_weight": float(weights[flipped]),
            "latest_score": float(alt.iloc[-1]),
            "latest_score_difference": float(alt.iloc[-1] - baseline.iloc[-1]),
            "mean_absolute_score_difference": float((alt - baseline).abs().mean()),
            "max_absolute_score_difference": float((alt - baseline).abs().max()),
            "sign_agreement_rate": float((np.sign(alt) == np.sign(baseline)).mean()),
            "regime_label_agreement_rate": float((alt_regime == baseline_regime).mean()),
            "latest_regime": alt_regime.iloc[-1],
        })
    return results


def score_distribution(weekly: pd.DataFrame) -> dict[str, Any]:
    """Summarize the practical distribution of the recalculated v2 score."""
    _, score = _full_sample_components(weekly)
    regimes = score.apply(score_v2.label_regime)
    quantiles = score.quantile([0.05, 0.25, 0.50, 0.75, 0.95])
    regime_order = [label for _low, _high, label in score_v2.REGIME_BANDS]
    regime_counts = regimes.value_counts()

    return {
        "diagnostic": "Distribution of the current-vintage recalculated production score",
        "caution": (
            "Full-sample normalization makes this a current-vintage descriptive "
            "distribution, not an immutable as-published history or forecast."
        ),
        "observations": int(len(score)),
        "mean": float(score.mean()),
        "sample_standard_deviation": float(score.std()),
        "minimum": float(score.min()),
        "maximum": float(score.max()),
        "quantiles": {
            "p05": float(quantiles.loc[0.05]),
            "p25": float(quantiles.loc[0.25]),
            "p50": float(quantiles.loc[0.50]),
            "p75": float(quantiles.loc[0.75]),
            "p95": float(quantiles.loc[0.95]),
        },
        "regimes": [
            {
                "regime": regime,
                "weeks": int(regime_counts.get(regime, 0)),
                "share": float((regimes == regime).mean()),
            }
            for regime in regime_order
        ],
    }


def regime_duration(weekly: pd.DataFrame) -> dict[str, Any]:
    """Measure consecutive time spent in each production regime."""
    _, score = _full_sample_components(weekly)
    labels = score.apply(score_v2.label_regime)
    runs: list[dict[str, Any]] = []
    start_pos = 0
    current = labels.iloc[0]

    for idx in range(1, len(labels)):
        label = labels.iloc[idx]
        if label == current:
            continue
        runs.append({
            "regime": current,
            "start": labels.index[start_pos].date().isoformat(),
            "end": labels.index[idx - 1].date().isoformat(),
            "weeks": int(idx - start_pos),
        })
        start_pos = idx
        current = label

    runs.append({
        "regime": current,
        "start": labels.index[start_pos].date().isoformat(),
        "end": labels.index[-1].date().isoformat(),
        "weeks": int(len(labels) - start_pos),
    })

    regime_order = [label for _low, _high, label in score_v2.REGIME_BANDS]
    summaries = []
    for regime in regime_order:
        durations = [run["weeks"] for run in runs if run["regime"] == regime]
        summaries.append({
            "regime": regime,
            "runs": int(len(durations)),
            "total_weeks": int(sum(durations)),
            "mean_weeks": float(np.mean(durations)) if durations else None,
            "median_weeks": float(np.median(durations)) if durations else None,
            "maximum_weeks": int(max(durations)) if durations else None,
        })

    return {
        "diagnostic": "Consecutive duration of current-vintage production regime labels",
        "caution": (
            "Historical labels may change when full-sample normalization or upstream "
            "source history is recalculated."
        ),
        "observations": int(len(labels)),
        "run_count": int(len(runs)),
        "current_run": runs[-1],
        "by_regime": summaries,
        "runs": runs,
    }


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


def _correlation_pairs(corr: pd.DataFrame) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    names = list(corr.columns)
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            value = float(corr.loc[left, right])
            if not np.isfinite(value):
                continue
            pairs.append({"left": left, "right": right, "correlation": value})
    pairs.sort(key=lambda item: abs(item["correlation"]), reverse=True)
    return pairs


def _correlation_summary(corr: pd.DataFrame) -> dict[str, Any]:
    pairs = _correlation_pairs(corr)
    absolute = [abs(item["correlation"]) for item in pairs]
    top = pairs[0] if pairs else None
    return {
        "mean_absolute_pair_correlation": float(np.mean(absolute)) if absolute else None,
        "max_absolute_pair_correlation": float(max(absolute)) if absolute else None,
        "pairs_at_or_above_abs_0_70": int(sum(value >= 0.70 for value in absolute)),
        "top_pair": top,
        "top_pairs": pairs[:10],
    }


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
    summary = _correlation_summary(sample.corr())
    return {
        "diagnostic": "Pearson correlation of production weekly level inputs",
        "caution": "Level correlations may reflect common trends and are not return correlations.",
        "window_weeks": int(len(sample)),
        "window_start": sample.index[0].date().isoformat(),
        "window_end": sample.index[-1].date().isoformat(),
        **summary,
    }


def rolling_component_correlations(
    weekly: pd.DataFrame,
    *,
    window: int = DEFAULT_CORRELATION_WINDOW,
) -> dict[str, Any]:
    """Publish a current-vintage rolling history of component correlations.

    Correlations are calculated on the clipped production component z-scores
    from the current full-sample recalculation. Because those z-scores are
    current-vintage, this is a robustness diagnostic rather than an immutable
    as-published correlation history.
    """
    if window < 3:
        raise ValueError("Correlation window must be at least 3 weeks")
    z, _ = _full_sample_components(weekly)
    if len(z) < window:
        raise RuntimeError(
            f"Need at least {window} complete weeks for rolling component correlations"
        )

    history: list[dict[str, Any]] = []
    for idx in range(window - 1, len(z)):
        sample = z.iloc[idx - window + 1:idx + 1]
        summary = _correlation_summary(sample.corr())
        history.append({
            "date": z.index[idx].date().isoformat(),
            "window_start": sample.index[0].date().isoformat(),
            "window_end": sample.index[-1].date().isoformat(),
            "mean_absolute_pair_correlation": summary["mean_absolute_pair_correlation"],
            "max_absolute_pair_correlation": summary["max_absolute_pair_correlation"],
            "pairs_at_or_above_abs_0_70": summary["pairs_at_or_above_abs_0_70"],
            "top_pair": summary["top_pair"],
        })

    return {
        "diagnostic": "Rolling Pearson correlation of clipped production component z-scores",
        "caution": (
            "Current-vintage component correlations are descriptive and can change "
            "when the full-sample normalization history is recalculated."
        ),
        "window_weeks": int(window),
        "observations": int(len(history)),
        "first_date": history[0]["date"],
        "latest_date": history[-1]["date"],
        "latest": history[-1],
        "history": history,
    }


def contribution_concentration(
    weekly: pd.DataFrame,
    *,
    window: int = DEFAULT_CORRELATION_WINDOW,
) -> dict[str, Any]:
    """Quantify concentration of score contributions with correlation overlap.

    For each week, absolute contribution shares p_i are calculated from
    |weight_i * clipped_z_i|. Ordinary concentration is HHI = sum(p_i^2), with
    effective component count 1/HHI. A deliberately transparent heuristic then
    replaces the identity matrix with the element-wise absolute rolling
    component-correlation matrix: C_abs = p' |R| p. Its reciprocal is the
    effective correlated component count. Because |R| adds non-negative overlap,
    the correlated count cannot exceed the ordinary effective count.

    This is an audit diagnostic, not a covariance risk model or portfolio metric.
    """
    if window < 3:
        raise ValueError("Correlation window must be at least 3 weeks")
    z, score = _full_sample_components(weekly)
    if len(z) < window:
        raise RuntimeError(
            f"Need at least {window} complete weeks for contribution concentration"
        )

    drivers = list(score_v2.WEIGHTS)
    contributions = pd.DataFrame(
        {driver: z[driver] * float(score_v2.WEIGHTS[driver]) for driver in drivers},
        index=z.index,
    )
    history: list[dict[str, Any]] = []

    for idx in range(window - 1, len(z)):
        sample = z.iloc[idx - window + 1:idx + 1]
        corr_abs = np.abs(sample.corr().to_numpy(dtype=float))
        corr_abs = np.nan_to_num(corr_abs, nan=0.0, posinf=1.0, neginf=1.0)
        np.fill_diagonal(corr_abs, 1.0)

        current = contributions.iloc[idx].to_numpy(dtype=float)
        gross = float(np.abs(current).sum())
        if gross <= 0:
            continue
        shares = np.abs(current) / gross
        hhi = float(shares @ shares)
        corr_index = float(shares @ corr_abs @ shares)
        if hhi <= 0 or corr_index <= 0:
            continue

        effective_uncorrelated = float(1.0 / hhi)
        effective_correlated = float(1.0 / corr_index)
        # Floating-point noise can put the correlated count a few ulps above.
        effective_correlated = min(effective_correlated, effective_uncorrelated)
        dominant_idx = int(np.argmax(shares))
        net_score = float(score.iloc[idx])
        history.append({
            "date": z.index[idx].date().isoformat(),
            "window_start": sample.index[0].date().isoformat(),
            "window_end": sample.index[-1].date().isoformat(),
            "gross_absolute_contribution": gross,
            "net_score": net_score,
            "net_to_gross_ratio": float(abs(net_score) / gross),
            "dominant_driver": drivers[dominant_idx],
            "dominant_absolute_contribution_share": float(shares[dominant_idx]),
            "ordinary_contribution_hhi": hhi,
            "effective_uncorrelated_component_count": effective_uncorrelated,
            "absolute_correlation_adjusted_concentration_index": corr_index,
            "effective_correlated_component_count": effective_correlated,
            "correlation_overlap_multiplier": float(corr_index / hhi),
        })

    if not history:
        raise RuntimeError("No valid contribution-concentration observations")

    return {
        "diagnostic": "Absolute contribution concentration adjusted by absolute component correlations",
        "method": (
            "p_i = |weight_i * clipped_z_i| / sum_j |weight_j * clipped_z_j|; "
            "HHI = p'p; correlated concentration = p'|R|p; effective counts are reciprocals."
        ),
        "caution": (
            "Heuristic transparency diagnostic only. It is not a covariance risk model, "
            "portfolio diversification measure, forecast, or alternative score methodology."
        ),
        "window_weeks": int(window),
        "observations": int(len(history)),
        "first_date": history[0]["date"],
        "latest_date": history[-1]["date"],
        "latest": history[-1],
        "history": history,
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
        "sign_sensitivity": sign_sensitivity(data),
        "rolling_normalization": rolling_window_sensitivity(data, windows=rolling_windows),
        "correlation_concentration": correlation_concentration(data, window=correlation_window),
        "rolling_component_correlations": rolling_component_correlations(
            data, window=correlation_window
        ),
        "contribution_concentration": contribution_concentration(
            data, window=correlation_window
        ),
        "regime_threshold_sensitivity": threshold_sensitivity(data),
        "score_distribution": score_distribution(data),
        "regime_duration": regime_duration(data),
        "subperiod_stability": subperiod_stability(data),
        "limitations": [
            "The production score is descriptive, not predictive.",
            "Current-vintage source histories can differ from historical as-published vintages.",
            "Leave-one-out and rolling-window variants are diagnostics, not alternative production models.",
            "Sign flips are adversarial assumption checks, not data-selected alternative weights.",
            "Correlation diagnostics use current-vintage weekly levels or component z-scores and may reflect common trends.",
            "The correlation-adjusted contribution concentration is a transparent heuristic, not a covariance risk model.",
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
