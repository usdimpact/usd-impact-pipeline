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
    backtest_results.json      — (with --backtest) honest hit rate per regime
    usd_impact_score_v2.log    — run log with data quality notes

Run modes:
    python usd_impact_score_v2.py             # default weekly run
    python usd_impact_score_v2.py --backtest  # compute honest hit rate
    python usd_impact_score_v2.py --test      # use cached data if present

Dependencies (pip install):
    pandas numpy yfinance pandas-datareader matplotlib pyarrow

Author: USD Impact project
License: proprietary, all rights reserved
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

START_DATE = "2015-01-01"
ZSCORE_CLIP = 3.5
RESAMPLE_RULE = "W-FRI"

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

# Historical regime windows used by --backtest to produce an honest hit rate.
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

def fetch_yahoo(tickers: list[str], start: str, logger: logging.Logger) -> pd.DataFrame:
    """Fetch daily close prices from Yahoo Finance for a list of tickers."""
    import yfinance as yf

    logger.info(f"Fetching Yahoo: {tickers}")
    raw = yf.download(
        tickers,
        start=start,
        progress=False,
        auto_adjust=True,
        group_by="ticker" if len(tickers) > 1 else None,
    )

    if raw.empty:
        raise RuntimeError(f"Yahoo returned no data for {tickers}")

    if len(tickers) == 1:
        df = pd.DataFrame({tickers[0]: raw["Close"]})
    else:
        df = pd.DataFrame({
            t: raw[t]["Close"]
            for t in tickers
            if t in raw.columns.get_level_values(0)
        })

    missing = [t for t in tickers if t not in df.columns]
    if missing:
        raise RuntimeError(f"Yahoo missing tickers: {missing}")

    logger.info(f"Yahoo: {len(df)} daily rows")
    return df


def fetch_fred(series: list[str], start: str, logger: logging.Logger) -> pd.DataFrame:
    """Fetch daily series from FRED using pandas_datareader."""
    from pandas_datareader import data as pdr

    logger.info(f"Fetching FRED: {series}")
    df = pdr.DataReader(series, "fred", start=start)
    if df.empty:
        raise RuntimeError(f"FRED returned no data for {series}")
    logger.info(f"FRED: {len(df)} daily rows")
    return df


def fetch_all_inputs(start: str, logger: logging.Logger) -> pd.DataFrame:
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

    # Forward fill up to 3 days for holiday misalignment
    df = df.ffill(limit=3)

    logger.info(
        f"Combined daily frame: {len(df)} rows, "
        f"{df.index.min().date()} → {df.index.max().date()}"
    )
    return df


# ============================================================
# PROCESSING
# ============================================================

def resample_weekly(daily_df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    weekly = daily_df.resample(RESAMPLE_RULE).last().dropna(how="all")
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


def export_json(df: pd.DataFrame, path: Path, logger: logging.Logger) -> None:
    payload = {
        "metadata": {
            "pipeline": "usd_impact_score_v2",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "start_date": START_DATE,
            "resample": RESAMPLE_RULE,
            "zscore_clip": ZSCORE_CLIP,
            "weights": WEIGHTS,
            "n_weeks": len(df),
            "latest_date": str(df.index[-1].date()),
            "latest_score": float(df["score"].iloc[-1]),
            "latest_regime": df["regime"].iloc[-1],
        },
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
        footer = (
            "This is an educational tool. It is not investment advice nor a "
            "recommendation to buy or sell. See USD Impact — Read the Dollar First."
        )

    chart_png = build_chart_png(score, chart_title)
    chart_b64 = base64.b64encode(chart_png).decode("ascii")
    chart_data_uri = f"data:image/png;base64,{chart_b64}"

    change_sign = "+" if wk_change >= 0 else ""
    score_color = "#1B3A5F" if latest_score >= 0 else "#B8860B"

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
                        help="Run backtest and report honest hit rate")
    parser.add_argument("--test", action="store_true",
                        help="Use cached data if present (for development)")
    parser.add_argument("--web", action="store_true",
                        help="Write output in Cloudflare Pages layout "
                             "(public/en/, public/es/, public/data/)")
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

    logger.info("=" * 60)
    logger.info("USD Impact Score v2 — pipeline run")
    logger.info(f"Started at {datetime.now(timezone.utc).isoformat()}")
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
            daily = fetch_all_inputs(args.start_date, logger)
            # Skip cache write in --web mode: CI runs want fresh data and
            # we don't want the cache file sitting inside the public dir.
            if not args.web:
                try:
                    daily.to_parquet(cache_path)
                    logger.debug(f"Cached daily data to {cache_path}")
                except Exception as e:
                    logger.debug(f"Cache write skipped: {e}")

        weekly = resample_weekly(daily, logger)

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
        export_json(out_df, json_path, logger)

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
