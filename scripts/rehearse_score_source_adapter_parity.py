#!/usr/bin/env python3
"""Synthetic parity rehearsal for the provider-neutral Score source adapter."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal

from scripts.score_source_adapter import AdapterSpec, normalize_daily_frame
from usd_impact_score_v2 import (
    WEIGHTS,
    ZSCORE_CLIP,
    compute_score,
    compute_zscores,
    label_regime,
    resample_weekly,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "score_source_adapter"


class _NullLogger:
    def info(self, *args, **kwargs) -> None:
        pass

    def debug(self, *args, **kwargs) -> None:
        pass

    def warning(self, *args, **kwargs) -> None:
        pass


def _specs() -> tuple[AdapterSpec, AdapterSpec]:
    alpha = AdapterSpec(
        provider_id="synthetic-alpha",
        date_column="date",
        column_map={
            "dollar_idx": "DXY",
            "crude_front": "WTI",
            "sp500": "SPX",
            "vix_idx": "VIX",
            "btc_usd": "BTC",
            "gold_front": "GOLD",
            "ust2_pct": "UST_2Y",
            "ust10_pct": "UST_10Y",
        },
    )
    beta = AdapterSpec(
        provider_id="synthetic-beta",
        date_column="timestamp",
        column_map={
            "usd_index_level": "DXY",
            "wti_continuous": "WTI",
            "spx_index": "SPX",
            "vix_close": "VIX",
            "bitcoin_reference": "BTC",
            "gold_continuous": "GOLD",
            "ust2_bps": "UST_2Y",
            "ust10_bps": "UST_10Y",
        },
        value_multiplier={"UST_2Y": 0.01, "UST_10Y": 0.01},
    )
    return alpha, beta


def _canonical_bytes(frame: pd.DataFrame) -> bytes:
    out = frame.copy()
    out.index = pd.to_datetime(out.index)
    return out.to_csv(
        index=True,
        index_label="date",
        float_format="%.12f",
        lineterminator="\n",
    ).encode("utf-8")


def rehearse() -> dict[str, Any]:
    alpha_spec, beta_spec = _specs()
    alpha_raw = pd.read_csv(FIXTURES / "provider_alpha.csv")
    beta_raw = pd.read_csv(FIXTURES / "provider_beta.csv")

    alpha = normalize_daily_frame(alpha_raw, alpha_spec)
    beta = normalize_daily_frame(beta_raw, beta_spec)
    assert_frame_equal(alpha, beta, check_exact=False, rtol=0, atol=1e-12)

    alpha_sha = hashlib.sha256(_canonical_bytes(alpha)).hexdigest()
    beta_sha = hashlib.sha256(_canonical_bytes(beta)).hexdigest()
    if alpha_sha != beta_sha:
        raise RuntimeError("canonical daily-frame fingerprints differ")

    logger = _NullLogger()
    alpha_weekly = resample_weekly(
        alpha.ffill(limit=3), logger, completed_friday=pd.Timestamp("2026-08-28")
    ).dropna()
    beta_weekly = resample_weekly(
        beta.ffill(limit=3), logger, completed_friday=pd.Timestamp("2026-08-28")
    ).dropna()
    assert_frame_equal(alpha_weekly, beta_weekly, check_exact=False, rtol=0, atol=1e-12)

    alpha_z = compute_zscores(alpha_weekly, ZSCORE_CLIP, logger)
    beta_z = compute_zscores(beta_weekly, ZSCORE_CLIP, logger)
    assert_frame_equal(alpha_z, beta_z, check_exact=False, rtol=0, atol=1e-12)

    alpha_score = compute_score(alpha_z, WEIGHTS, logger)
    beta_score = compute_score(beta_z, WEIGHTS, logger)
    assert_series_equal(alpha_score, beta_score, check_exact=False, rtol=0, atol=1e-12)

    alpha_regime = alpha_score.apply(label_regime)
    beta_regime = beta_score.apply(label_regime)
    assert_series_equal(alpha_regime, beta_regime, check_exact=True)

    return {
        "schema_version": "score-source-adapter-synthetic-parity-v1",
        "status": "passed",
        "review_only": True,
        "network_access_performed": False,
        "real_provider_data_used": False,
        "live_fetch_switch_performed": False,
        "provider_purchase_or_contract_performed": False,
        "production_change_authorized": False,
        "canonical_daily_frame_equal": True,
        "canonical_daily_sha256": alpha_sha,
        "weekly_inputs_equal": True,
        "zscores_equal": True,
        "score_equal": True,
        "regime_equal": True,
        "canonical_driver_count": len(WEIGHTS),
        "daily_row_count": len(alpha),
        "weekly_row_count": len(alpha_weekly),
        "latest_week": alpha_weekly.index[-1].date().isoformat(),
        "latest_score": float(alpha_score.iloc[-1]),
        "latest_regime": str(alpha_regime.iloc[-1]),
        "unit_normalization_proven": {
            "UST_2Y": "basis_points_to_percent",
            "UST_10Y": "basis_points_to_percent",
        },
    }


def main() -> int:
    print(json.dumps(rehearse(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
