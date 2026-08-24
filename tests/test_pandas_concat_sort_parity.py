from __future__ import annotations

import unittest
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal

import usd_impact_score_v2 as score_v2


ROOT = Path(__file__).resolve().parents[1]


class _NullLogger:
    def debug(self, *_args, **_kwargs):
        pass

    def info(self, *_args, **_kwargs):
        pass

    def warning(self, *_args, **_kwargs):
        pass

    def error(self, *_args, **_kwargs):
        pass


class PandasConcatSortParityTests(unittest.TestCase):
    def _frames(self) -> tuple[list[pd.DataFrame], pd.DataFrame]:
        dates = pd.date_range("2026-01-01", periods=120, freq="D")
        # Deliberately use opposite DatetimeIndex order across FRED fixtures so
        # pandas' deprecated implicit sort behavior is exercised explicitly.
        fred_2y = pd.DataFrame(
            {"UST_2Y": 4.0 + np.linspace(0.0, 0.6, len(dates))},
            index=dates[::-1],
        )
        fred_10y = pd.DataFrame(
            {"UST_10Y": 4.4 + np.linspace(0.0, -0.4, len(dates))},
            index=dates,
        )
        yahoo = pd.DataFrame(
            {
                "DXY": 98 + np.linspace(0, 4, len(dates)),
                "WTI": 70 + np.sin(np.arange(len(dates)) / 8) * 4,
                "SPX": 6000 + np.linspace(0, 300, len(dates)),
                "VIX": 18 + np.cos(np.arange(len(dates)) / 7) * 3,
                "BTC": 90000 + np.linspace(0, 12000, len(dates)),
                "GOLD": 2600 + np.linspace(0, 180, len(dates)),
            },
            index=dates,
        )
        return [fred_2y, fred_10y], yahoo

    def test_explicit_sort_true_matches_current_pandas_concat_behavior(self) -> None:
        frames, _ = self._frames()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            legacy = pd.concat(frames, axis=1)
        explicit = pd.concat(frames, axis=1, sort=True)
        assert_frame_equal(legacy, explicit, check_exact=True)
        self.assertTrue(explicit.index.is_monotonic_increasing)

    def test_daily_weekly_and_score_outputs_are_identical(self) -> None:
        frames, yahoo = self._frames()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            legacy_fred = pd.concat(frames, axis=1)
        explicit_fred = pd.concat(frames, axis=1, sort=True)

        legacy_daily = yahoo.join(legacy_fred, how="outer").sort_index().ffill(limit=3)
        explicit_daily = yahoo.join(explicit_fred, how="outer").sort_index().ffill(limit=3)
        assert_frame_equal(legacy_daily, explicit_daily, check_exact=True)

        logger = _NullLogger()
        cutoff = pd.Timestamp("2026-04-24")
        legacy_weekly = score_v2.resample_weekly(legacy_daily, logger, completed_friday=cutoff)
        explicit_weekly = score_v2.resample_weekly(explicit_daily, logger, completed_friday=cutoff)
        assert_frame_equal(legacy_weekly, explicit_weekly, check_exact=True)

        required = list(score_v2.WEIGHTS)
        legacy_clean = legacy_weekly[required].dropna()
        explicit_clean = explicit_weekly[required].dropna()
        legacy_z = score_v2.compute_zscores(legacy_clean, score_v2.ZSCORE_CLIP, logger)
        explicit_z = score_v2.compute_zscores(explicit_clean, score_v2.ZSCORE_CLIP, logger)
        assert_frame_equal(legacy_z, explicit_z, check_exact=True)

        legacy_score = score_v2.compute_score(legacy_z, score_v2.WEIGHTS, logger)
        explicit_score = score_v2.compute_score(explicit_z, score_v2.WEIGHTS, logger)
        assert_series_equal(legacy_score, explicit_score, check_exact=True)

    def test_production_source_makes_sort_behavior_explicit(self) -> None:
        source = (ROOT / "usd_impact_score_v2.py").read_text(encoding="utf-8")
        self.assertIn("pd.concat(frames, axis=1, sort=True)", source)
        self.assertNotIn("pd.concat(frames, axis=1)\n", source)


if __name__ == "__main__":
    unittest.main()
