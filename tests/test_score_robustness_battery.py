import unittest
from pathlib import Path

import pandas as pd

import usd_impact_score_v2 as score_v2
from scripts.score_robustness_battery import (
    build_robustness_report,
    correlation_concentration,
    leave_one_driver_out,
    rolling_window_sensitivity,
    threshold_sensitivity,
)


class ScoreRobustnessBatteryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.weekly = pd.read_csv(
            Path("tests/fixtures/weekly_levels.csv"), parse_dates=["date"]
        ).set_index("date")

    def test_report_is_non_predictive_and_methodology_preserving(self):
        report = build_robustness_report(
            self.weekly,
            min_history=5,
            rolling_windows=(5, 7),
            correlation_window=5,
        )
        self.assertFalse(report["production_methodology_changed"])
        self.assertFalse(report["predictive_claim"])
        self.assertFalse(report["as_published_vintage"])
        self.assertEqual(
            report["data"]["latest_complete_week"],
            self.weekly.index[-1].date().isoformat(),
        )
        self.assertIn("point_in_time_normalization", report)
        self.assertIn("leave_one_driver_out", report)
        self.assertIn("rolling_normalization", report)
        self.assertIn("correlation_concentration", report)
        self.assertIn("regime_threshold_sensitivity", report)
        self.assertIn("subperiod_stability", report)

    def test_leave_one_out_covers_every_driver_and_normalizes_weights(self):
        results = leave_one_driver_out(self.weekly)
        self.assertEqual(
            {row["omitted_driver"] for row in results}, set(score_v2.WEIGHTS)
        )
        for row in results:
            self.assertAlmostEqual(row["remaining_absolute_weight_sum"], 1.0, places=12)
            self.assertGreaterEqual(row["regime_label_agreement_rate"], 0.0)
            self.assertLessEqual(row["regime_label_agreement_rate"], 1.0)

    def test_production_threshold_variant_matches_production_labels(self):
        variants = threshold_sensitivity(self.weekly)
        production = next(row for row in variants if row["variant"] == "production")
        self.assertAlmostEqual(
            production["label_agreement_rate_vs_production"], 1.0, places=12
        )

    def test_rolling_windows_only_use_available_prior_history(self):
        results = rolling_window_sensitivity(self.weekly, windows=(5, 7))
        self.assertEqual({row["prior_window_weeks"] for row in results}, {5, 7})
        for row in results:
            self.assertGreater(row["evaluated_weeks"], 0)
            self.assertLess(row["first_evaluated_week"], row["last_evaluated_week"])

    def test_correlation_diagnostic_has_unique_pairs(self):
        result = correlation_concentration(self.weekly, window=5)
        self.assertEqual(result["window_weeks"], 5)
        pairs = result["top_pairs"]
        seen = set()
        for pair in pairs:
            key = tuple(sorted((pair["left"], pair["right"])))
            self.assertNotIn(key, seen)
            seen.add(key)
            self.assertGreaterEqual(pair["correlation"], -1.0)
            self.assertLessEqual(pair["correlation"], 1.0)


if __name__ == "__main__":
    unittest.main()
