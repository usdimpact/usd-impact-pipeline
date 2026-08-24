import unittest
from pathlib import Path

import pandas as pd

from scripts.point_in_time_validation import (
    build_report,
    compare_scores,
    expanding_point_in_time_score,
)


class PointInTimeValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.weekly = pd.read_csv(
            Path("tests/fixtures/weekly_levels.csv"), parse_dates=["date"]
        ).set_index("date")

    def test_future_observations_do_not_change_prior_pit_scores(self):
        min_history = 5
        base = self.weekly.iloc[:-2].copy()
        extended = self.weekly.copy()

        pit_base = expanding_point_in_time_score(base, min_history=min_history)
        pit_extended = expanding_point_in_time_score(extended, min_history=min_history)
        overlap = pit_base.index.intersection(pit_extended.index)

        self.assertGreater(len(overlap), 0)
        pd.testing.assert_series_equal(
            pit_base.loc[overlap, "score_pit"],
            pit_extended.loc[overlap, "score_pit"],
            check_names=True,
            atol=1e-12,
            rtol=0,
        )

    def test_history_endpoint_is_strictly_before_evaluated_week(self):
        comparison = compare_scores(self.weekly, min_history=5)
        self.assertFalse(comparison.empty)
        for date, row in comparison.iterrows():
            self.assertLess(row["history_end"], date)
            self.assertEqual(row["history_count"], self.weekly.index.get_loc(date))

    def test_report_is_explicitly_non_predictive(self):
        report = build_report(self.weekly, min_history=5)
        self.assertFalse(report["production_methodology_changed"])
        self.assertFalse(report["predictive_claim"])
        self.assertGreater(report["evaluated_weeks"], 0)
        self.assertIn("regime_label_agreement_rate", report["summary"])


if __name__ == "__main__":
    unittest.main()
