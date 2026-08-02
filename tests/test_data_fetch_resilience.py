import logging
import unittest
from datetime import date, datetime, timezone

import pandas as pd

from scripts.validate_weekly_release import latest_completed_friday
from usd_impact_score_v2 import compute_score, fetch_yahoo, resample_weekly


def yahoo_frame(tickers):
    index = pd.to_datetime(["2026-07-30", "2026-07-31"])
    columns = pd.MultiIndex.from_tuples((ticker, "Close") for ticker in tickers)
    values = [[100 + offset for offset in range(len(tickers))] for _ in index]
    return pd.DataFrame(values, index=index, columns=columns)


class YahooFetchResilienceTests(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger(self.id())
        self.logger.handlers.clear()
        self.logger.addHandler(logging.NullHandler())

    def test_retries_a_partial_batch_and_disables_threads(self):
        calls = []

        def download(tickers, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                return yahoo_frame(["DX-Y.NYB"])
            return yahoo_frame(tickers)

        result = fetch_yahoo(
            ["DX-Y.NYB", "CL=F"],
            "2015-01-01",
            self.logger,
            download_fn=download,
            retry_base_seconds=0,
        )

        self.assertEqual(list(result.columns), ["DX-Y.NYB", "CL=F"])
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(call["threads"] is False for call in calls))

    def test_reports_the_last_error_after_retry_budget_is_exhausted(self):
        calls = 0

        def download(_tickers, **_kwargs):
            nonlocal calls
            calls += 1
            raise RuntimeError("database is locked")

        with self.assertRaisesRegex(
            RuntimeError,
            "Yahoo fetch failed after 3 attempts: database is locked",
        ):
            fetch_yahoo(
                ["CL=F"],
                "2015-01-01",
                self.logger,
                download_fn=download,
                retry_base_seconds=0,
            )

        self.assertEqual(calls, 3)

    def test_score_rejects_an_empty_observation_frame(self):
        empty = pd.DataFrame(columns=["DXY"])
        with self.assertRaisesRegex(
            RuntimeError,
            "Score computation received no complete observations",
        ):
            compute_score(empty, {"DXY": 1.0}, self.logger)

    def test_weekend_observation_does_not_create_a_future_week(self):
        daily = pd.DataFrame(
            {"DXY": [100.0, 100.0], "BTC": [110.0, 111.0]},
            index=pd.to_datetime(["2026-07-31", "2026-08-01"]),
        )

        weekly = resample_weekly(daily, self.logger)

        self.assertEqual(list(weekly.index), [pd.Timestamp("2026-07-31")])

    def test_latest_completed_friday_never_moves_into_the_future(self):
        expectations = {
            datetime(2026, 7, 31, 22, tzinfo=timezone.utc): date(2026, 7, 31),
            datetime(2026, 8, 1, 3, tzinfo=timezone.utc): date(2026, 7, 31),
            datetime(2026, 8, 3, 9, tzinfo=timezone.utc): date(2026, 7, 31),
        }
        for generated_at, expected in expectations.items():
            with self.subTest(generated_at=generated_at):
                self.assertEqual(latest_completed_friday(generated_at), expected)


if __name__ == "__main__":
    unittest.main()
