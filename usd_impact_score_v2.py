#!/usr/bin/env python3
"""
USD Impact Score v2 — weekly cross-asset dollar regime pipeline.

Computes a single weekly score from eight cross-asset inputs, resampled to
Friday close, z-scored against full sample history, clipped at ±3.5, and
weighted by the transmission logic documented in the USD Impact book
(Chapter 10 — Reading Regimes).

Inputs (fetched live each run):
    DXY     — ICE U.S. Dollar Index       (Yahoo: DX-Y.NYB)
    WTI     — WTI crude continuous front  (Yahoo: CL=F)
    SPX     — S&P 500 index               (Yahoo: ^GSPC)
    VIX     — Cboe volatility index       (Yahoo: ^VIX)
    BTC     — Bitcoin USD spot            (Yahoo: BTC-USD)
    GOLD    — Gold continuous front       (Yahoo: GC=F)
    UST_2Y  — U.S. 2Y Treasury yield      (FRED: DGS2)
    UST_10Y — U.S. 10Y Treasury yield     (FRED: DGS10)

Weights (magnitude 0.125, sign = transmission direction):
    DXY +, WTI −, SPX −, VIX +, BTC −, GOLD −, UST_2Y +, UST_10Y +

Outputs (written to ./output/):
    usd_impact_score_v2.csv    — weekly z-scored components + score + regime
    usd_impact_score_v2.json   — same data as JSON for programmatic use
    _graphic.html              — English dashboard (latest + 11-year chart)
    _graphic_es.html           — Spanish dashboard
    backtest_results.json      — (with --backtest) descriptive hit rate per regime
    usd_impact_score_v2.log    — run log with data quality notes

Run modes:
    python usd_impact_score_v2.py             # default weekly run
    python usd_impact_score_v2.py --backtest  # descriptive regime-window analysis
    python usd_impact_score_v2.py --test      # use cached data if present

Dependencies (pip install):
    pandas numpy yfinance pandas-datareader matplotlib pyarrow

Author: USD Impact project
License: proprietary, all rights reserved
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

START_DATE = "2015-01-01"
ZSCORE_CLIP = 3.5
RESAMPLE_RULE = "W-FRI"
YAHOO_FETCH_ATTEMPTS = 3
YAHOO_RETRY_BASE_SECONDS = 2

# Ticker map: canonical name -> (source, ticker)
TICKERS = {
    "DXY":     ("yahoo", "DX-Y.NYB"),
    "WTI":     ("yahoo", "CL=F"),
    "SPX":     ("yahoo", "^GSPC"),
    "VIX":     ("yahoo", "^VIX"),
    "BTC":     ("yahoo", "BTC-USD"),
    "GOLD":    ("yahoo", "GC=F"),
    "UST_2Y":  ("fred",  "DGS2"),
    "UST_10Y": ("fred",  "DGS10"),
}

# Operational source contract. These fields describe where each input was
# retrieved and how old its last raw observation may be at publication time.
# They do not affect the score calculation, weights, or data transformations.
SOURCE_URLS = {
    "DXY": "https://finance.yahoo.com/quote/DX-Y.NYB/history",
    "WTI": "https://finance.yahoo.com/quote/CL%3DF/history",
    "SPX": "https://finance.yahoo.com/quote/%5EGSPC/history",
    "VIX": "https://finance.yahoo.com/quote/%5EVIX/history",
    "BTC": "https://finance.yahoo.com/quote/BTC-USD/history",
    "GOLD": "https://finance.yahoo.com/quote/GC%3DF/history",
    "UST_2Y": "https://fred.stlouisfed.org/series/DGS2",
    "UST_10Y": "https://fred.stlouisfed.org/series/DGS10",
}

SOURCE_PROVIDER_LABELS = {
    "yahoo": "Yahoo Finance via yfinance",
    "fred": "Federal Reserve Bank of St. Louis (FRED)",
}

# Calendar-day limits intentionally allow normal market holidays and the
# publication lag sometimes seen in the daily Treasury constant-maturity
# series, while rejecting a driver that has stopped updating for a full week.
SOURCE_MAX_AGE_DAYS = {
    "DXY": 3,
    "WTI": 3,
    "SPX": 3,
    "VIX": 3,
    "BTC": 2,
    "GOLD": 3,
    "UST_2Y": 4,
    "UST_10Y": 4,
}

SOURCE_PROVENANCE_VERSION = 1
PROVIDER_DAILY_FINGERPRINT_VERSION = 1
PROVIDER_DAILY_FINGERPRINT_SCOPE = (
    "complete provider-derived daily input matrix on or before the completed "
    "score Friday, after selected-field extraction and canonical driver "
    "renaming, before calendar forward fill"
)
PROVIDER_DAILY_FINGERPRINT_CANONICALIZATION = (
    "UTF-8 CSV; date plus production driver order; YYYY-MM-DD dates; missing "
    "values empty; finite floats formatted with 17 significant digits; LF line endings"
)

# Sign = expected direction of move under a stronger dollar regime.
# Magnitude 0.125 means equal-weight across eight inputs (sum of |w| = 1.0).
WEIGHTS = {
    "DXY":     +0.125,
    "WTI":     -0.125,
    "SPX":     -0.125,
    "VIX":     +0.125,
    "BTC":     -0.125,
    "GOLD":    -0.125,
    "UST_2Y":  +0.125,
    "UST_10Y": +0.125,
}

# Regime bands used for dashboard labels
REGIME_BANDS = [
    (+1.0, float("inf"),  "Strong dollar regime"),
    (+0.3, +1.0,          "Firm dollar regime"),
    (-0.3, +0.3,          "Neutral / transitional"),
    (-1.0, -0.3,          "Soft dollar regime"),
    (-float("inf"), -1.0, "Weak dollar regime"),
]

# Historical regime windows used by --backtest for descriptive analysis.
# Each entry: (start, end, expected_sign, name).
# expected_sign: +1 for "framework should read this as positive regime", −1 for negative.
BACKTEST_REGIMES = [
    ("2015-07-01", "2016-02-01",  +1, "2015-16 oil/EM stress"),
    ("2018-06-01", "2018-12-31",  +1, "2018 Fed tightening"),
    ("2020-03-01", "2020-03-23",  +1, "2020 COVID funding stress (phase 1)"),
    ("2020-04-01", "2021-10-01",  -1, "2020-21 post-Fed liquidity (phase 2)"),
    ("2022-02-01", "2023-03-01",  +1, "2022 tightening cycle"),
]


# ============================================================
# LOGGING
# ============================================================

def setup_logging(output_dir: Path, verbose: bool = True) -> logging.Logger:
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "usd_impact_score_v2.log"

    logger = logging.getLogger("usd_impact")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    return logger


# ============================================================
# DATA FETCH
# ============================================================

def fetch_yahoo(
    tickers: list[str],
    start: str,
    logger: logging.Logger,
    *,
    download_fn=None,
    attempts: int = YAHOO_FETCH_ATTEMPTS,
    retry_base_seconds: float = YAHOO_RETRY_BASE_SECONDS,
) -> pd.DataFrame:
    """Fetch daily close prices from Yahoo Finance for a list of tickers."""
    if attempts < 1:
        raise ValueError("Yahoo fetch attempts must be at least 1")

    if download_fn is None:
        import yfinance as yf
        download_fn = yf.download

    logger.info(f"Fetching Yahoo: {tickers}")
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            # yfinance defaults to threaded downloads. Its shared SQLite cache
            # can lock when ticker workers initialize concurrently, leaving one
            # asset entirely empty. Serializing the batch avoids that race.
            raw = download_fn(
                tickers,
                start=start,
                progress=False,
                auto_adjust=True,
                group_by="ticker" if len(tickers) > 1 else None,
                threads=False,
            )

            if raw.empty:
                raise RuntimeError(f"Yahoo returned no data for {tickers}")

            if len(tickers) == 1:
                close = raw["Close"]
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]
                df = pd.DataFrame({tickers[0]: close})
            else:
                df = pd.DataFrame({
                    ticker: raw[ticker]["Close"]
                    for ticker in tickers
                    if ticker in raw.columns.get_level_values(0)
                })

            missing = [ticker for ticker in tickers if ticker not in df.columns]
            if missing:
                raise RuntimeError(f"Yahoo missing tickers: {missing}")

            logger.info(f"Yahoo: {len(df)} daily rows")
            return df
        except Exception as error:
            last_error = error
            if attempt == attempts:
                break
            delay = retry_base_seconds * attempt
            logger.warning(
                f"Yahoo fetch attempt {attempt}/{attempts} failed: {error}. "
                f"Retrying in {delay:g} seconds."
            )
            if delay > 0:
                time.sleep(delay)

    raise RuntimeError(
        f"Yahoo fetch failed after {attempts} attempts: {last_error}"
    ) from last_error


def fetch_fred(series: list[str], start: str, logger: logging.Logger) -> pd.DataFrame:
    """Fetch daily series from FRED using the public CSV download endpoint.

    FRED exposes every series at a stable, no-auth URL:
        https://fred.stlouisfed.org/graph/fredgraph.csv?id=SERIES_ID
    This avoids the pandas_datareader dependency (which is unmaintained and
    breaks against pandas 3.x) and uses plain pandas.read_csv instead.
    """
    logger.info(f"Fetching FRED: {series}")
    frames = []
    for s in series:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}"
        try:
            one = pd.read_csv(url, parse_dates=["observation_date"])
        except Exception as e:
            raise RuntimeError(f"FRED fetch failed for {s}: {e}")
        one = one.rename(columns={"observation_date": "DATE"})
        one = one.set_index("DATE")
        # FRED marks missing observations as "." — convert to NaN
        one[s] = pd.to_numeric(one[s], errors="coerce")
        frames.append(one)

    df = pd.concat(frames, axis=1, sort=True)
    # Filter to start date
    df = df[df.index >= pd.Timestamp(start)]
    if df.empty:
        raise RuntimeError(f"FRED returned no data for {series} after {start}")
    logger.info(f"FRED: {len(df)} daily rows")
    return df


def latest_completed_friday(value: datetime | date | pd.Timestamp) -> date:
    """Return the most recent Friday that has completed in UTC."""
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        current_date = value.astimezone(timezone.utc).date()
    else:
        current_date = value
    return current_date - timedelta(days=(current_date.weekday() - 4) % 7)


def build_source_provenance(
    raw_df: pd.DataFrame,
    score_week: date | pd.Timestamp,
    *,
    retrieval_mode: str = "live",
) -> dict[str, dict[str, object]]:
    """Describe the last raw observation available for every score driver.

    The input must be the joined frame before holiday forward filling. This
    ensures the reported observation date identifies the original provider
    row rather than a value copied forward for calendar alignment.
    """
    canonical = set(TICKERS)
    for label, mapping in (
        ("source URLs", SOURCE_URLS),
        ("source age limits", SOURCE_MAX_AGE_DAYS),
    ):
        if set(mapping) != canonical:
            raise RuntimeError(f"Configured {label} do not match canonical drivers")

    score_date = pd.Timestamp(score_week).date()
    provenance: dict[str, dict[str, object]] = {}
    for driver, (provider_code, series) in TICKERS.items():
        observation_date: date | None = None
        if driver in raw_df.columns:
            valid = raw_df[driver].dropna()
            eligible_dates = [
                pd.Timestamp(index).date()
                for index in valid.index
                if pd.Timestamp(index).date() <= score_date
            ]
            if eligible_dates:
                observation_date = max(eligible_dates)

        max_age_days = SOURCE_MAX_AGE_DAYS[driver]
        if observation_date is None:
            age_days: int | None = None
            status = "missing"
        else:
            age_days = (score_date - observation_date).days
            status = "fresh" if age_days <= max_age_days else "stale"

        provenance[driver] = {
            "driver": driver,
            "provider": SOURCE_PROVIDER_LABELS[provider_code],
            "provider_code": provider_code,
            "series": series,
            "source_url": SOURCE_URLS[driver],
            "observation_date": (
                observation_date.isoformat() if observation_date else None
            ),
            "score_week": score_date.isoformat(),
            "age_days": age_days,
            "max_age_days": max_age_days,
            "status": status,
            "retrieval_mode": retrieval_mode,
        }
    return provenance


def _canonical_provider_daily_bytes(
    raw_df: pd.DataFrame,
    drivers: list[str],
) -> bytes:
    lines = [",".join(("date", *drivers))]
    for index, row in raw_df[drivers].iterrows():
        date_text = pd.Timestamp(index).date().isoformat()
        values = []
        for driver in drivers:
            value = row[driver]
            if pd.isna(value):
                values.append("")
                continue
            numeric = float(value)
            if not np.isfinite(numeric):
                raise RuntimeError(
                    f"Non-finite provider-derived daily input for {driver} {date_text}"
                )
            values.append(format(numeric, ".17g"))
        lines.append(",".join((date_text, *values)))
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_provider_derived_daily_fingerprint(
    raw_df: pd.DataFrame,
    score_week: date | pd.Timestamp,
    *,
    retrieval_run_started_at: datetime,
    retrieval_mode: str = "live",
) -> dict[str, object]:
    """Bind a release to its provider-derived daily histories without values.

    This hashes parsed, selected daily series rather than original HTTP response
    bytes. It deliberately retains neither transport payloads nor source values.
    """
    drivers = list(WEIGHTS)
    missing = [driver for driver in drivers if driver not in raw_df.columns]
    if missing:
        raise RuntimeError(
            f"Provider-derived daily fingerprint is missing drivers: {missing}"
        )

    score_date = pd.Timestamp(score_week).date()
    frame = raw_df[drivers].copy()
    frame.index = pd.to_datetime(frame.index)
    frame = frame[
        [pd.Timestamp(index).date() <= score_date for index in frame.index]
    ].sort_index()
    if frame.empty or frame.index.has_duplicates:
        raise RuntimeError(
            "Provider-derived daily fingerprint needs non-empty, unique dates"
        )
    if not frame.index.is_monotonic_increasing:
        raise RuntimeError("Provider-derived daily fingerprint dates must be ordered")

    driver_fingerprints: dict[str, dict[str, object]] = {}
    for driver, (provider_code, series) in TICKERS.items():
        observed = frame[[driver]].dropna()
        if observed.empty:
            raise RuntimeError(
                f"Provider-derived daily fingerprint has no observations for {driver}"
            )
        driver_fingerprints[driver] = {
            "sha256": hashlib.sha256(
                _canonical_provider_daily_bytes(observed, [driver])
            ).hexdigest(),
            "provider_code": provider_code,
            "series": series,
            "observation_start": observed.index[0].date().isoformat(),
            "observation_end": observed.index[-1].date().isoformat(),
            "observation_count": len(observed),
        }

    if retrieval_run_started_at.tzinfo is None:
        retrieval_run_started_at = retrieval_run_started_at.replace(
            tzinfo=timezone.utc
        )
    started_at_utc = retrieval_run_started_at.astimezone(timezone.utc)
    return {
        "version": PROVIDER_DAILY_FINGERPRINT_VERSION,
        "scope": PROVIDER_DAILY_FINGERPRINT_SCOPE,
        "canonicalization": PROVIDER_DAILY_FINGERPRINT_CANONICALIZATION,
        "score_week": score_date.isoformat(),
        "retrieval_run_started_at_utc": started_at_utc.isoformat(),
        "retrieval_mode": retrieval_mode,
        "matrix_sha256": hashlib.sha256(
            _canonical_provider_daily_bytes(frame, drivers)
        ).hexdigest(),
        "drivers": driver_fingerprints,
        "original_transport_bytes_hashed": False,
        "raw_provider_payloads_archived": False,
        "provider_derived_values_published": False,
        "purpose": (
            "Detect later changes in the exact provider-derived daily histories "
            "eligible for this release without retaining or redistributing values."
        ),
    }


def validate_source_freshness(
    provenance: dict[str, dict[str, object]],
    score_week: date | pd.Timestamp,
    logger: logging.Logger,
) -> None:
    """Fail closed when any canonical driver is missing, future, or stale."""
    expected = set(TICKERS)
    if set(provenance) != expected:
        missing = sorted(expected - set(provenance))
        unexpected = sorted(set(provenance) - expected)
        raise RuntimeError(
            "Source provenance driver mismatch: "
            f"missing={missing}, unexpected={unexpected}"
        )

    score_date = pd.Timestamp(score_week).date()
    failures = []
    for driver in TICKERS:
        item = provenance[driver]
        observation_raw = item.get("observation_date")
        if not observation_raw:
            failures.append(f"{driver} has no observation on or before {score_date}")
            continue

        observation_date = date.fromisoformat(str(observation_raw))
        age_days = (score_date - observation_date).days
        max_age_days = SOURCE_MAX_AGE_DAYS[driver]
        if age_days < 0:
            failures.append(
                f"{driver} observation {observation_date} is after score week {score_date}"
            )
            continue
        if age_days > max_age_days:
            failures.append(
                f"{driver} observation {observation_date} is stale by {age_days} days "
                f"(limit {max_age_days})"
            )
            continue

        if item.get("score_week") != score_date.isoformat():
            failures.append(f"{driver} provenance score_week does not match {score_date}")
            continue
        if item.get("age_days") != age_days:
            failures.append(f"{driver} provenance age_days is inconsistent")
            continue
        if item.get("max_age_days") != max_age_days:
            failures.append(f"{driver} provenance max_age_days is inconsistent")
            continue
        if item.get("status") != "fresh":
            failures.append(f"{driver} provenance status is not fresh")
            continue

        logger.info(
            f"Source freshness {driver}: {observation_date} "
            f"({age_days} calendar days old; limit {max_age_days})"
        )

    if failures:
        raise RuntimeError("Source freshness validation failed: " + "; ".join(failures))


def fetch_all_inputs(
    start: str,
    logger: logging.Logger,
    *,
    as_of: datetime | None = None,
) -> pd.DataFrame:
    """Fetch every configured input, returning a daily DataFrame aligned on date."""
    yahoo_names = [k for k, (src, _) in TICKERS.items() if src == "yahoo"]
    fred_names  = [k for k, (src, _) in TICKERS.items() if src == "fred"]

    yahoo_tickers = [TICKERS[k][1] for k in yahoo_names]
    fred_tickers  = [TICKERS[k][1] for k in fred_names]

    yahoo_df = fetch_yahoo(yahoo_tickers, start, logger)
    fred_df  = fetch_fred(fred_tickers, start, logger)

    # Rename columns to canonical names
    yahoo_df.columns = yahoo_names
    fred_df.columns = fred_names

    df = yahoo_df.join(fred_df, how="outer").sort_index()

    missing_pct = df.isna().mean() * 100
    for col, pct in missing_pct.items():
        if pct > 5:
            logger.warning(f"{col}: {pct:.1f}% missing after join")
        else:
            logger.debug(f"{col}: {pct:.1f}% missing")

    reference_time = as_of or datetime.now(timezone.utc)
    score_week = latest_completed_friday(reference_time)
    provenance = build_source_provenance(df, score_week)
    provider_daily_fingerprint = build_provider_derived_daily_fingerprint(
        df,
        score_week,
        retrieval_run_started_at=reference_time,
    )

    # Forward fill up to 3 observations for holiday-calendar alignment. Source
    # provenance above is captured first so copied values retain their true
    # provider observation date in the release metadata.
    df = df.ffill(limit=3)
    df.attrs["source_provenance_version"] = SOURCE_PROVENANCE_VERSION
    df.attrs["source_provenance"] = provenance
    df.attrs["provider_derived_daily_history_fingerprint"] = (
        provider_daily_fingerprint
    )
    df.attrs["expected_score_week"] = score_week.isoformat()

    logger.info(
        f"Combined daily frame: {len(df)} rows, "
        f"{df.index.min().date()} → {df.index.max().date()}"
    )
    return df


# ============================================================
# PROCESSING
# ============================================================

def resample_weekly(
    daily_df: pd.DataFrame,
    logger: logging.Logger,
    *,
    completed_friday: date | pd.Timestamp | None = None,
) -> pd.DataFrame:
    weekly = daily_df.resample(RESAMPLE_RULE).last().dropna(how="all")
    if completed_friday is None:
        latest_observation = daily_df.index.max().normalize()
        cutoff = latest_observation - pd.Timedelta(
            days=(latest_observation.weekday() - 4) % 7
        )
    else:
        cutoff = pd.Timestamp(completed_friday).normalize()
    weekly = weekly.loc[weekly.index <= cutoff]
    logger.info(
        f"Weekly resampled: {len(weekly)} weeks, "
        f"{weekly.index.min().date()} → {weekly.index.max().date()}"
    )
    return weekly


def compute_zscores(weekly_df: pd.DataFrame, clip: float,
                    logger: logging.Logger) -> pd.DataFrame:
    """Full-sample z-score, clipped at ±clip."""
    mu = weekly_df.mean()
    sd = weekly_df.std()
    z = (weekly_df - mu) / sd
    z_clipped = z.clip(lower=-clip, upper=clip)

    for col in z_clipped.columns:
        n_clipped = (z[col].abs() > clip).sum()
        logger.debug(
            f"{col}: μ={mu[col]:.3f}, σ={sd[col]:.3f}, "
            f"clipped {n_clipped} weeks"
        )

    return z_clipped


def compute_score(z_df: pd.DataFrame, weights: dict[str, float],
                  logger: logging.Logger) -> pd.Series:
    if z_df.empty:
        raise RuntimeError("Score computation received no complete observations")

    missing = [k for k in weights if k not in z_df.columns]
    if missing:
        raise RuntimeError(f"Score computation missing columns: {missing}")

    score = sum(z_df[k] * w for k, w in weights.items())
    score.name = "score"
    logger.info(
        f"Score computed: {len(score)} weeks, "
        f"range [{score.min():.3f}, {score.max():.3f}], "
        f"latest {score.iloc[-1]:+.3f} on {score.index[-1].date()}"
    )
    return score


def label_regime(score_value: float) -> str:
    for low, high, label in REGIME_BANDS:
        if low <= score_value < high:
            return label
    return "Unknown"


# ============================================================
# BACKTEST
# ============================================================

@dataclass
class RegimeResult:
    name: str
    expected_sign: int
    weeks: int
    hits: int
    hit_rate: float
    mean_score: float


def backtest(score: pd.Series, logger: logging.Logger) -> tuple[list[RegimeResult], float]:
    """Compute hit rate across the five anchor regimes.

    A 'hit' is a week where sign(score) matches expected_sign.
    """
    results: list[RegimeResult] = []
    total_weeks = 0
    total_hits = 0

    logger.info("=" * 60)
    logger.info("BACKTEST: hit rate across five anchor regimes")
    logger.info("=" * 60)

    for start, end, expected_sign, name in BACKTEST_REGIMES:
        window = score.loc[start:end]
        if len(window) == 0:
            logger.warning(f"Regime '{name}' has no data in range {start} to {end}")
            continue

        hits = int((np.sign(window) == expected_sign).sum())
        weeks = len(window)
        hit_rate = hits / weeks if weeks > 0 else 0.0
        mean_s = float(window.mean())

        results.append(RegimeResult(
            name=name,
            expected_sign=expected_sign,
            weeks=weeks,
            hits=hits,
            hit_rate=hit_rate,
            mean_score=mean_s,
        ))

        total_weeks += weeks
        total_hits += hits

        sign_char = "+" if expected_sign > 0 else "−"
        logger.info(
            f"  {name:42s} {sign_char} {hits:3d}/{weeks:3d} = {hit_rate:6.1%}  "
            f"mean={mean_s:+.3f}"
        )

    aggregate = total_hits / total_weeks if total_weeks > 0 else 0.0
    logger.info("-" * 60)
    logger.info(
        f"  AGGREGATE                                   "
        f"{total_hits:3d}/{total_weeks:3d} = {aggregate:6.1%}"
    )
    logger.info("=" * 60)

    return results, aggregate


# ============================================================
# OUTPUT: CSV + JSON
# ============================================================

def build_output_frame(z_df: pd.DataFrame, score: pd.Series) -> pd.DataFrame:
    out = z_df.copy()
    out["score"] = score
    out["regime"] = score.apply(label_regime)
    return out


def export_csv(df: pd.DataFrame, path: Path, logger: logging.Logger) -> None:
    df.to_csv(path, index_label="date", float_format="%.6f")
    logger.info(f"Wrote {path.name} ({path.stat().st_size:,} bytes)")


def write_weekly_levels_snapshot(
    weekly_clean: pd.DataFrame,
    path: Path,
    logger: logging.Logger,
    *,
    public_root: Path | None = None,
) -> None:
    """Write the exact weekly input matrix for a same-run evidence handoff.

    The snapshot is deliberately operational and non-public. The reproduction
    bundle consumes it in the same runner, publishes only cryptographic
    fingerprints and calculation evidence, and does not redistribute the full
    provider-derived history.
    """
    resolved_path = path.resolve()
    if public_root is not None:
        resolved_public_root = public_root.resolve()
        if resolved_path == resolved_public_root or resolved_path.is_relative_to(
            resolved_public_root
        ):
            raise RuntimeError(
                "Weekly input snapshot must remain outside the public output tree"
            )

    drivers = list(WEIGHTS)
    missing = [driver for driver in drivers if driver not in weekly_clean.columns]
    if missing:
        raise RuntimeError(f"Weekly input snapshot is missing drivers: {missing}")
    snapshot = weekly_clean[drivers].dropna().sort_index()
    if snapshot.empty or snapshot.index.has_duplicates:
        raise RuntimeError("Weekly input snapshot must be non-empty with unique weeks")
    if not snapshot.index.is_monotonic_increasing:
        raise RuntimeError("Weekly input snapshot must be ordered by week")
    if not np.isfinite(snapshot.to_numpy(dtype=float)).all():
        raise RuntimeError("Weekly input snapshot contains a non-finite value")

    path.parent.mkdir(parents=True, exist_ok=True)
    snapshot.to_csv(
        path,
        index_label="date",
        date_format="%Y-%m-%d",
        float_format="%.17g",
        lineterminator="\n",
    )
    logger.info(
        f"Wrote non-public same-run weekly input snapshot: {path} "
        f"({len(snapshot)} weeks)"
    )


def write_provider_evidence_receipt(
    receipt: dict[str, object],
    path: Path,
    logger: logging.Logger,
    *,
    public_root: Path | None = None,
) -> None:
    """Write a non-public same-run handoff containing hashes, never values."""
    resolved_path = path.resolve()
    if public_root is not None:
        resolved_public_root = public_root.resolve()
        if resolved_path == resolved_public_root or resolved_path.is_relative_to(
            resolved_public_root
        ):
            raise RuntimeError(
                "Provider evidence receipt must remain outside the public output tree"
            )
    if receipt.get("raw_provider_payloads_archived") is not False:
        raise RuntimeError("Provider evidence receipt must not claim raw archival")
    if receipt.get("provider_derived_values_published") is not False:
        raise RuntimeError("Provider evidence receipt must not contain published values")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    logger.info(
        "Wrote non-public same-run provider evidence receipt with hashes only: "
        f"{path}"
    )


def export_json(
    df: pd.DataFrame,
    path: Path,
    logger: logging.Logger,
    *,
    generated_at: datetime | None = None,
    source_provenance: dict[str, dict[str, object]] | None = None,
) -> None:
    generated_at = generated_at or datetime.now(timezone.utc)
    metadata = {
        "pipeline": "usd_impact_score_v2",
        "generated_at_utc": generated_at.isoformat(),
        "start_date": START_DATE,
        "resample": RESAMPLE_RULE,
        "zscore_clip": ZSCORE_CLIP,
        "weights": WEIGHTS,
        "n_weeks": len(df),
        "latest_date": str(df.index[-1].date()),
        "latest_score": float(df["score"].iloc[-1]),
        "latest_regime": df["regime"].iloc[-1],
    }
    if source_provenance is not None:
        metadata["source_provenance_version"] = SOURCE_PROVENANCE_VERSION
        metadata["source_provenance"] = source_provenance

    payload = {
        "metadata": metadata,
        "weeks": [
            {
                "date": str(idx.date()),
                **{
                    k: float(v) if pd.notna(v) else None
                    for k, v in row.items() if k != "regime"
                },
                "regime": row["regime"],
            }
            for idx, row in df.iterrows()
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    logger.info(f"Wrote {path.name} ({path.stat().st_size:,} bytes)")


# ============================================================
# OUTPUT: HTML DASHBOARDS
# ============================================================

def build_chart_png(score: pd.Series, title: str) -> bytes:
    """Render the eleven-year score chart as PNG bytes."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    NAVY = "#1B3A5F"
    GOLD = "#B8860B"
    MUTE = "#6B7280"

    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Georgia", "DejaVu Serif", "serif"],
        "axes.edgecolor": MUTE,
        "axes.labelcolor": "#333333",
        "xtick.color": MUTE,
        "ytick.color": MUTE,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })

    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(score.index, score.values, color=NAVY, linewidth=1.2)
    ax.axhline(0, color=MUTE, linewidth=0.6, alpha=0.5)

    # Regime shading
    ax.fill_between(
        score.index, 0.3, score.values,
        where=(score.values >= 0.3), color=NAVY, alpha=0.10, linewidth=0,
    )
    ax.fill_between(
        score.index, score.values, -0.3,
        where=(score.values <= -0.3), color=GOLD, alpha=0.10, linewidth=0,
    )

    ax.set_title(title, color=NAVY, loc="left", fontsize=12, fontweight="bold", pad=10)
    ax.set_ylabel("Score (z-standardized)", fontsize=9)
    ax.set_ylim(-4, 4)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.yaxis.grid(True, color=MUTE, alpha=0.15)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def build_behavior_diagnostics_png(score: pd.Series, *, lang: str = "en") -> bytes:
    """Render score-distribution and regime-duration transparency charts."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    navy = "#1B3A5F"
    gold = "#B8860B"
    mute = "#6B7280"
    labels = score.apply(label_regime)
    runs: dict[str, list[int]] = {
        regime: [] for _low, _high, regime in REGIME_BANDS
    }
    current = labels.iloc[0]
    length = 1
    for label in labels.iloc[1:]:
        if label == current:
            length += 1
            continue
        runs[current].append(length)
        current = label
        length = 1
    runs[current].append(length)

    regime_order = [regime for _low, _high, regime in REGIME_BANDS]
    median_duration = [
        float(np.median(runs[regime])) if runs[regime] else 0.0
        for regime in regime_order
    ]
    maximum_duration = [
        float(max(runs[regime])) if runs[regime] else 0.0
        for regime in regime_order
    ]

    if lang == "es":
        distribution_title = "Distribución del score"
        duration_title = "Duración consecutiva por régimen"
        score_label = "Score recalculado"
        weeks_label = "Semanas"
        median_label = "Mediana"
        maximum_label = "Máximo"
        short_labels = ["Muy fuerte", "Firme", "Neutral", "Débil", "Muy débil"]
    else:
        distribution_title = "Score distribution"
        duration_title = "Consecutive regime duration"
        score_label = "Recalculated score"
        weeks_label = "Weeks"
        median_label = "Median"
        maximum_label = "Maximum"
        short_labels = ["Strong", "Firm", "Neutral", "Soft", "Weak"]

    fig, axes = plt.subplots(1, 2, figsize=(8, 3.2))
    axes[0].hist(score.values, bins=24, color=navy, alpha=0.78, edgecolor="white")
    for threshold in (-1.0, -0.3, 0.3, 1.0):
        axes[0].axvline(threshold, color=gold, linewidth=0.8, alpha=0.75)
    axes[0].axvline(float(score.iloc[-1]), color="#9B1C31", linewidth=1.3)
    axes[0].set_title(distribution_title, color=navy, loc="left", fontsize=10, fontweight="bold")
    axes[0].set_xlabel(score_label, fontsize=8)
    axes[0].set_ylabel(weeks_label, fontsize=8)

    positions = np.arange(len(regime_order))
    width = 0.38
    axes[1].bar(positions - width / 2, median_duration, width, label=median_label, color=navy)
    axes[1].bar(positions + width / 2, maximum_duration, width, label=maximum_label, color=gold)
    axes[1].set_title(duration_title, color=navy, loc="left", fontsize=10, fontweight="bold")
    axes[1].set_ylabel(weeks_label, fontsize=8)
    axes[1].set_xticks(positions, short_labels, rotation=25, ha="right", fontsize=7)
    axes[1].legend(frameon=False, fontsize=7)

    for axis in axes:
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(colors=mute, labelsize=7)
        axis.yaxis.grid(True, color=mute, alpha=0.12)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def load_commentary(lang: str = "en") -> str:
    """Load the latest weekly commentary from the commentary/ directory.

    Looks for (in order):
      1. commentary/latest_{lang}.md  (language-specific latest)
      2. commentary/latest.md         (fallback, typically English)
      3. Empty string + graceful message if neither exists

    Returns an HTML-ready string. Markdown is converted to basic HTML
    (paragraphs, headings, horizontal rules, bold, italic) without
    requiring an external markdown library.
    """
    candidates = [
        Path(f"commentary/latest_{lang}.md"),
        Path("commentary/latest.md"),
    ]
    source = None
    for p in candidates:
        if p.exists():
            source = p.read_text(encoding="utf-8")
            break

    if not source:
        return ""

    # Minimal markdown → HTML conversion
    # Split into blocks by double newlines, classify each
    html_blocks = []
    blocks = source.split("\n\n")
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Horizontal rule
        if block == "---":
            html_blocks.append("<hr/>")
            continue
        # Heading
        if block.startswith("# "):
            html_blocks.append(f"<h2 class='commentary-title'>{block[2:].strip()}</h2>")
            continue
        if block.startswith("## "):
            html_blocks.append(f"<h3 class='commentary-h3'>{block[3:].strip()}</h3>")
            continue
        # Italicized footer (entire block wrapped in *)
        if block.startswith("*") and block.endswith("*") and block.count("*") == 2:
            inner = block[1:-1].strip()
            html_blocks.append(f"<p class='commentary-footer'><em>{inner}</em></p>")
            continue
        # Default: paragraph. Convert inline **bold** and *italic*
        import re as _re
        text = _re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', block)
        text = _re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', text)
        html_blocks.append(f"<p>{text}</p>")

    return "\n".join(html_blocks)


def build_graphic_payload(df: pd.DataFrame, score: pd.Series, lang: str = "en") -> str:
    """Build a self-contained HTML dashboard string in English or Spanish."""
    latest_date = df.index[-1].date()
    latest_score = float(score.iloc[-1])
    latest_regime = df["regime"].iloc[-1]
    wk_change = float(score.iloc[-1] - score.iloc[-2]) if len(score) >= 2 else 0.0

    if lang == "es":
        title = "USD Impact Score"
        subtitle = "Registro semanal, régimen transversal del dólar"
        lbl_latest = "Última lectura"
        lbl_regime = "Régimen"
        lbl_change = "Cambio semanal"
        lbl_as_of = "Datos al"
        chart_title = "USD Impact Score — Registro de once años"
        diagnostics_title = "Diagnósticos de comportamiento de la serie recalculada"
        diagnostics_note = (
            "Distribución y duración de regímenes usando la historia recalculada actual; "
            "son descriptivas y pueden cambiar con revisiones o nuevas observaciones."
        )
        footer = (
            "Esta es una herramienta educativa. No constituye asesoramiento "
            "financiero ni recomendación de compra o venta. Ver USD Impact — "
            "Lee primero el dólar."
        )
        regime_map = {
            "Strong dollar regime":   "Régimen fuerte",
            "Firm dollar regime":     "Régimen firme",
            "Neutral / transitional": "Neutral / transicional",
            "Soft dollar regime":     "Régimen débil",
            "Weak dollar regime":     "Régimen muy débil",
        }
        latest_regime = regime_map.get(latest_regime, latest_regime)
    else:
        title = "USD Impact Score"
        subtitle = "Weekly cross-asset dollar regime reading"
        lbl_latest = "Latest reading"
        lbl_regime = "Regime"
        lbl_change = "Week-over-week change"
        lbl_as_of = "Data as of"
        chart_title = "USD Impact Score — Eleven-Year Record"
        diagnostics_title = "Current-vintage behavior diagnostics"
        diagnostics_note = (
            "Score distribution and regime duration use today's recalculated history; "
            "they are descriptive and can change after revisions or new observations."
        )
        footer = (
            "This is an educational tool. It is not investment advice nor a "
            "recommendation to buy or sell. See USD Impact — Read the Dollar First."
        )

    chart_png = build_chart_png(score, chart_title)
    chart_b64 = base64.b64encode(chart_png).decode("ascii")
    chart_data_uri = f"data:image/png;base64,{chart_b64}"
    diagnostics_png = build_behavior_diagnostics_png(score, lang=lang)
    diagnostics_b64 = base64.b64encode(diagnostics_png).decode("ascii")
    diagnostics_data_uri = f"data:image/png;base64,{diagnostics_b64}"

    change_sign = "+" if wk_change >= 0 else ""
    score_color = "#1B3A5F" if latest_score >= 0 else "#B8860B"

    # Load commentary. If no commentary exists, render an empty div that
    # does not appear on screen (so the layout degrades gracefully).
    commentary_html = load_commentary(lang)
    if commentary_html:
        commentary_section = f'<div class="commentary">{commentary_html}</div>'
    elif lang == "es":
        commentary_section = (
            '<div class="commentary commentary-fallback">'
            '<p><em>Comentario semanal disponible solo en inglés esta semana. '
            'Desplácese hacia arriba para ver el registro del régimen.</em></p>'
            '</div>'
        )
    else:
        commentary_section = ""

    html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<style>
  body {{
    font-family: Georgia, 'DejaVu Serif', serif;
    color: #222;
    background: #fff;
    max-width: 820px;
    margin: 2rem auto;
    padding: 0 1.5rem;
    line-height: 1.5;
  }}
  h1 {{ color: #1B3A5F; font-size: 1.8rem; margin: 0 0 0.25rem; }}
  .subtitle {{ color: #6B7280; font-style: italic; margin-bottom: 1.5rem; }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
    padding: 1rem;
    border: 1px solid #D0C2A2;
    background: #F7F3EA;
    border-radius: 4px;
  }}
  .metric .label {{
    font-size: 0.8rem; color: #6B7280;
    text-transform: uppercase; letter-spacing: 0.5px;
  }}
  .metric .value {{
    font-size: 1.6rem; font-weight: bold;
    color: #1B3A5F; margin-top: 0.25rem;
  }}
  .score-value {{ color: {score_color} !important; }}
  .chart {{ margin: 1.5rem 0; }}
  .chart img {{ width: 100%; height: auto; }}
  .diagnostics {{
    margin: 1.5rem 0 2rem;
    padding: 1rem;
    border: 1px solid #D0C2A2;
    background: #FDFCF9;
  }}
  .diagnostics h2 {{ color: #1B3A5F; font-size: 1.05rem; margin: 0 0 0.4rem; }}
  .diagnostics p {{ color: #6B7280; font-size: 0.82rem; margin: 0 0 0.75rem; }}
  .diagnostics img {{ width: 100%; height: auto; }}
  .commentary {{
    margin: 2rem 0;
    padding: 1.5rem 1.75rem;
    background: #FDFCF9;
    border: 1px solid #D0C2A2;
    border-left: 4px solid #1B3A5F;
    border-radius: 2px;
  }}
  .commentary .commentary-title {{
    color: #1B3A5F;
    font-size: 1.35rem;
    font-weight: bold;
    margin: 0 0 0.75rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #D0C2A2;
  }}
  .commentary .commentary-h3 {{
    color: #1B3A5F;
    font-size: 1.05rem;
    font-weight: bold;
    margin: 1.25rem 0 0.5rem 0;
  }}
  .commentary p {{
    margin: 0.6rem 0;
    line-height: 1.65;
    color: #333;
  }}
  .commentary hr {{
    border: 0;
    border-top: 1px solid #D0C2A2;
    margin: 1.25rem 0 0.75rem 0;
  }}
  .commentary .commentary-footer {{
    font-size: 0.85rem;
    color: #6B7280;
    font-style: italic;
  }}
  .commentary-fallback {{
    text-align: center;
    color: #6B7280;
  }}
  .footer {{
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #D0C2A2;
    font-size: 0.8rem;
    color: #6B7280;
    font-style: italic;
  }}
</style>
</head>
<body>
  <h1>{title}</h1>
  <div class="subtitle">{subtitle}</div>

  <div class="grid">
    <div class="metric">
      <div class="label">{lbl_latest}</div>
      <div class="value score-value">{latest_score:+.2f}</div>
    </div>
    <div class="metric">
      <div class="label">{lbl_regime}</div>
      <div class="value" style="font-size:1.1rem;">{latest_regime}</div>
    </div>
    <div class="metric">
      <div class="label">{lbl_change}</div>
      <div class="value" style="font-size:1.1rem;">{change_sign}{wk_change:.2f}</div>
    </div>
    <div class="metric">
      <div class="label">{lbl_as_of}</div>
      <div class="value" style="font-size:1.1rem;">{latest_date}</div>
    </div>
  </div>

  <div class="chart">
    <img src="{chart_data_uri}" alt="{chart_title}"/>
  </div>

  <section class="diagnostics">
    <h2>{diagnostics_title}</h2>
    <p>{diagnostics_note}</p>
    <img src="{diagnostics_data_uri}" alt="{diagnostics_title}"/>
  </section>

  {commentary_section}

  <div class="footer">{footer}</div>
</body>
</html>
"""
    return html


def export_html(payload: str, path: Path, logger: logging.Logger) -> None:
    path.write_text(payload, encoding="utf-8")
    logger.info(f"Wrote {path.name} ({path.stat().st_size:,} bytes)")


def build_language_gateway() -> str:
    """Build the root index.html that auto-redirects based on browser language.

    Renders a minimal branded page with two language buttons. JS auto-redirects
    to /en/ or /es/ based on browser locale; no-JS users see the buttons.
    """
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>USD Impact Score</title>
<style>
  body {
    font-family: Georgia, 'DejaVu Serif', serif;
    color: #222;
    background: #fff;
    max-width: 640px;
    margin: 6rem auto;
    padding: 0 2rem;
    text-align: center;
    line-height: 1.5;
  }
  h1 { color: #1B3A5F; font-size: 2.2rem; margin: 0 0 0.5rem; }
  .subtitle {
    color: #6B7280; font-style: italic;
    margin-bottom: 3rem; font-size: 1.05rem;
  }
  .buttons { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
  .btn {
    display: inline-block;
    padding: 1rem 2rem;
    border: 1px solid #1B3A5F;
    color: #1B3A5F;
    text-decoration: none;
    font-family: inherit;
    font-size: 1rem;
    background: #F7F3EA;
    transition: background 0.15s;
  }
  .btn:hover { background: #D0C2A2; }
  .footer {
    margin-top: 4rem;
    padding-top: 1rem;
    border-top: 1px solid #D0C2A2;
    font-size: 0.75rem;
    color: #6B7280;
    font-style: italic;
  }
</style>
</head>
<body>
  <h1>USD Impact Score</h1>
  <div class="subtitle">Weekly cross-asset dollar regime reading — Lectura semanal del régimen del dólar</div>
  <div class="buttons">
    <a href="./en/" class="btn">Read in English →</a>
    <a href="./es/" class="btn">Leer en español →</a>
  </div>
  <div class="footer">
    USD Impact — Read the Dollar First. Educational. Not investment advice.
  </div>
  <script>
    (function() {
      var lang = (navigator.language || 'en').toLowerCase();
      if (lang.indexOf('es') === 0) {
        window.location.replace('./es/');
      } else {
        window.location.replace('./en/');
      }
    })();
  </script>
</body>
</html>
"""


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(description="USD Impact Score v2 pipeline")
    parser.add_argument("--output-dir", type=Path, default=Path("./output"),
                        help="Output directory (default: ./output)")
    parser.add_argument("--start-date", type=str, default=START_DATE,
                        help=f"Start date (default: {START_DATE})")
    parser.add_argument("--backtest", action="store_true",
                        help="Run descriptive historical regime hit-rate analysis")
    parser.add_argument("--test", action="store_true",
                        help="Use cached data if present (for development)")
    parser.add_argument("--web", action="store_true",
                        help="Write output in Cloudflare Pages layout "
                             "(public/en/, public/es/, public/data/)")
    parser.add_argument(
        "--weekly-levels-output",
        type=Path,
        help=(
            "Optional non-public same-run weekly input snapshot for the "
            "reproduction-bundle step"
        ),
    )
    parser.add_argument(
        "--provider-evidence-output",
        type=Path,
        help=(
            "Optional non-public same-run provider-derived daily fingerprint "
            "receipt for the reproduction-bundle step"
        ),
    )
    args = parser.parse_args()

    output_dir: Path = args.output_dir
    # In --web mode, logs and cache live outside the public dir so they
    # don't get served by Cloudflare Pages.
    if args.web:
        log_dir = Path("./logs")
        cache_path = Path("./.pipeline_cache/_daily_cache.parquet")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        log_dir = output_dir
        cache_path = output_dir / "_daily_cache.parquet"

    logger = setup_logging(log_dir)
    run_started_at = datetime.now(timezone.utc)
    expected_score_week = latest_completed_friday(run_started_at)

    logger.info("=" * 60)
    logger.info("USD Impact Score v2 — pipeline run")
    logger.info(f"Started at {run_started_at.isoformat()}")
    logger.info(f"Expected score week: {expected_score_week}")
    logger.info(f"Start date: {args.start_date}")
    logger.info(f"Output dir: {output_dir.resolve()}")
    logger.info(f"Log dir:    {log_dir.resolve()}")
    logger.info(f"Web mode:   {args.web}")
    logger.info("=" * 60)

    try:
        if args.test and cache_path.exists():
            logger.info(f"Using cached daily data from {cache_path}")
            daily = pd.read_parquet(cache_path)
        else:
            daily = fetch_all_inputs(
                args.start_date,
                logger,
                as_of=run_started_at,
            )
            # Skip cache write in --web mode: CI runs want fresh data and
            # we don't want the cache file sitting inside the public dir.
            if not args.web:
                try:
                    daily.to_parquet(cache_path)
                    logger.debug(f"Cached daily data to {cache_path}")
                except Exception as e:
                    logger.debug(f"Cache write skipped: {e}")

        source_provenance = daily.attrs.get("source_provenance")
        if not isinstance(source_provenance, dict):
            retrieval_mode = "cache" if args.test else "live"
            source_provenance = build_source_provenance(
                daily,
                expected_score_week,
                retrieval_mode=retrieval_mode,
            )
        validate_source_freshness(
            source_provenance,
            expected_score_week,
            logger,
        )

        if args.provider_evidence_output is not None:
            provider_evidence = daily.attrs.get(
                "provider_derived_daily_history_fingerprint"
            )
            if not isinstance(provider_evidence, dict):
                raise RuntimeError(
                    "Provider evidence output requires a same-run live fingerprint"
                )
            write_provider_evidence_receipt(
                provider_evidence,
                args.provider_evidence_output,
                logger,
                public_root=output_dir if args.web else None,
            )

        weekly = resample_weekly(
            daily,
            logger,
            completed_friday=expected_score_week,
        )

        required = list(WEIGHTS.keys())
        missing = [c for c in required if c not in weekly.columns]
        if missing:
            logger.error(f"Weekly frame missing required columns: {missing}")
            return 2

        weekly_clean = weekly[required].dropna()
        logger.info(
            f"Clean weekly frame: {len(weekly_clean)} weeks "
            f"(dropped {len(weekly) - len(weekly_clean)} weeks with missing data)"
        )
        if weekly_clean.empty:
            logger.error(
                "No complete weekly observations remain after required-input filtering"
            )
            return 2
        if weekly_clean.index[-1].date() != expected_score_week:
            raise RuntimeError(
                f"Latest complete score week {weekly_clean.index[-1].date()} does not "
                f"match expected completed Friday {expected_score_week}"
            )

        if args.weekly_levels_output is not None:
            write_weekly_levels_snapshot(
                weekly_clean,
                args.weekly_levels_output,
                logger,
                public_root=output_dir if args.web else None,
            )

        z = compute_zscores(weekly_clean, ZSCORE_CLIP, logger)
        score = compute_score(z, WEIGHTS, logger)
        out_df = build_output_frame(z, score)

        if args.web:
            # Cloudflare Pages layout: public/en/, public/es/, public/data/
            data_dir = output_dir / "data"
            en_dir   = output_dir / "en"
            es_dir   = output_dir / "es"
            data_dir.mkdir(parents=True, exist_ok=True)
            en_dir.mkdir(parents=True, exist_ok=True)
            es_dir.mkdir(parents=True, exist_ok=True)

            csv_path      = data_dir / "usd_impact_score_v2.csv"
            json_path     = data_dir / "usd_impact_score_v2.json"
            html_en       = en_dir / "index.html"
            html_es       = es_dir / "index.html"
            backtest_path = data_dir / "backtest_results.json"
            gateway_path  = output_dir / "index.html"

            # Write language gateway at the root
            gateway_path.write_text(build_language_gateway(), encoding="utf-8")
            logger.info(f"Wrote {gateway_path.name} (language gateway)")
        else:
            # Flat layout (default, local use)
            csv_path      = output_dir / "usd_impact_score_v2.csv"
            json_path     = output_dir / "usd_impact_score_v2.json"
            html_en       = output_dir / "_graphic.html"
            html_es       = output_dir / "_graphic_es.html"
            backtest_path = output_dir / "backtest_results.json"

        export_csv(out_df, csv_path, logger)
        export_json(
            out_df,
            json_path,
            logger,
            generated_at=run_started_at,
            source_provenance=source_provenance,
        )

        en_payload = build_graphic_payload(out_df, score, lang="en")
        es_payload = build_graphic_payload(out_df, score, lang="es")
        export_html(en_payload, html_en, logger)
        export_html(es_payload, html_es, logger)

        if args.backtest:
            results, aggregate = backtest(score, logger)
            backtest_path.write_text(json.dumps({
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "aggregate_hit_rate": aggregate,
                "regimes": [
                    {
                        "name": r.name,
                        "expected_sign": r.expected_sign,
                        "weeks": r.weeks,
                        "hits": r.hits,
                        "hit_rate": r.hit_rate,
                        "mean_score": r.mean_score,
                    } for r in results
                ],
            }, indent=2))
            logger.info(f"Wrote {backtest_path.name}")

        logger.info("=" * 60)
        logger.info(f"LATEST SCORE: {score.iloc[-1]:+.3f}")
        logger.info(f"LATEST REGIME: {out_df['regime'].iloc[-1]}")
        logger.info(f"AS OF: {score.index[-1].date()}")
        logger.info("Pipeline run complete.")
        logger.info("=" * 60)
        return 0

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
