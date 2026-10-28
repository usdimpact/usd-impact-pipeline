from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal

from scripts.score_source_adapter import AdapterSpec, normalize_daily_frame
from scripts import rehearse_score_source_adapter_parity as rehearsal
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


ALPHA = AdapterSpec(
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

BETA = AdapterSpec(
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


class ScoreSourceAdapterParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = _NullLogger()
        self.alpha_raw = pd.read_csv(FIXTURES / "provider_alpha.csv")
        self.beta_raw = pd.read_csv(FIXTURES / "provider_beta.csv")

    def test_provider_shaped_fixtures_normalize_exactly(self) -> None:
        alpha = normalize_daily_frame(self.alpha_raw, ALPHA)
        beta = normalize_daily_frame(self.beta_raw, BETA)
        assert_frame_equal(alpha, beta, check_exact=False, rtol=0, atol=1e-12)
        self.assertEqual(list(alpha.columns), list(WEIGHTS))

    def test_normalized_fixtures_produce_identical_score_path(self) -> None:
        alpha = normalize_daily_frame(self.alpha_raw, ALPHA).ffill(limit=3)
        beta = normalize_daily_frame(self.beta_raw, BETA).ffill(limit=3)

        alpha_weekly = resample_weekly(
            alpha, self.logger, completed_friday=pd.Timestamp("2026-08-28")
        ).dropna()
        beta_weekly = resample_weekly(
            beta, self.logger, completed_friday=pd.Timestamp("2026-08-28")
        ).dropna()
        assert_frame_equal(alpha_weekly, beta_weekly, check_exact=False, rtol=0, atol=1e-12)

        alpha_z = compute_zscores(alpha_weekly, ZSCORE_CLIP, self.logger)
        beta_z = compute_zscores(beta_weekly, ZSCORE_CLIP, self.logger)
        assert_frame_equal(alpha_z, beta_z, check_exact=False, rtol=0, atol=1e-12)

        alpha_score = compute_score(alpha_z, WEIGHTS, self.logger)
        beta_score = compute_score(beta_z, WEIGHTS, self.logger)
        assert_series_equal(alpha_score, beta_score, check_exact=False, rtol=0, atol=1e-12)

        alpha_regime = alpha_score.apply(label_regime)
        beta_regime = beta_score.apply(label_regime)
        assert_series_equal(alpha_regime, beta_regime, check_exact=True)

    def test_rehearsal_report_is_fail_closed_and_equal(self) -> None:
        report = rehearsal.rehearse()
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["review_only"])
        self.assertFalse(report["network_access_performed"])
        self.assertFalse(report["real_provider_data_used"])
        self.assertFalse(report["live_fetch_switch_performed"])
        self.assertFalse(report["provider_purchase_or_contract_performed"])
        self.assertFalse(report["production_change_authorized"])
        self.assertTrue(report["canonical_daily_frame_equal"])
        self.assertTrue(report["weekly_inputs_equal"])
        self.assertTrue(report["zscores_equal"])
        self.assertTrue(report["score_equal"])
        self.assertTrue(report["regime_equal"])
        self.assertEqual(report["canonical_driver_count"], 8)
        self.assertEqual(len(report["canonical_daily_sha256"]), 64)
        self.assertEqual(report["latest_week"], "2026-08-28")


    def test_adapter_rejects_incomplete_canonical_mapping(self) -> None:
        broken = AdapterSpec(
            provider_id="broken",
            date_column="date",
            column_map={"dollar_idx": "DXY"},
        )
        with self.assertRaisesRegex(RuntimeError, "exactly the canonical drivers"):
            normalize_daily_frame(self.alpha_raw, broken)

    def test_adapter_rejects_duplicate_dates(self) -> None:
        duplicated = pd.concat(
            [self.alpha_raw, self.alpha_raw.iloc[[0]]],
            ignore_index=True,
        )
        with self.assertRaisesRegex(RuntimeError, "dates must be unique"):
            normalize_daily_frame(duplicated, ALPHA)

    def test_adapter_rejects_extra_noncanonical_multiplier(self) -> None:
        broken = AdapterSpec(
            provider_id="broken-multiplier",
            date_column="date",
            column_map=ALPHA.column_map,
            value_multiplier={"NOT_A_DRIVER": 1.0},
        )
        with self.assertRaisesRegex(RuntimeError, "non-canonical drivers"):
            normalize_daily_frame(self.alpha_raw, broken)


if __name__ == "__main__":
    unittest.main()
