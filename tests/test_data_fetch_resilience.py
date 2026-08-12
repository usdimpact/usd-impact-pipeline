import logging
import unittest
from copy import deepcopy
from datetime import date, datetime, timezone

import pandas as pd

from scripts.validate_weekly_release import (
    SOURCE_CONTRACT,
    latest_completed_friday,
    validate_source_provenance as validate_release_source_provenance,
)
from usd_impact_score_v2 import (
    SOURCE_MAX_AGE_DAYS,
    SOURCE_PROVENANCE_VERSION,
    SOURCE_PROVIDER_LABELS,
    SOURCE_URLS,
    TICKERS,
    build_source_provenance,
    compute_score,
    fetch_yahoo,
    resample_weekly,
    validate_source_freshness,
)


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

    def test_source_provenance_records_raw_dates_before_forward_fill(self):
        index = pd.to_datetime(["2026-08-06", "2026-08-07"])
        raw = pd.DataFrame(100.0, index=index, columns=list(TICKERS))
        raw.loc[pd.Timestamp("2026-08-07"), ["UST_2Y", "UST_10Y"]] = float("nan")

        provenance = build_source_provenance(raw, date(2026, 8, 7))

        self.assertEqual(provenance["DXY"]["observation_date"], "2026-08-07")
        self.assertEqual(provenance["DXY"]["age_days"], 0)
        self.assertEqual(provenance["UST_2Y"]["observation_date"], "2026-08-06")
        self.assertEqual(provenance["UST_2Y"]["age_days"], 1)
        self.assertEqual(provenance["UST_2Y"]["status"], "fresh")

        # The operational check accepts the normal one-day FRED lag.
        validate_source_freshness(provenance, date(2026, 8, 7), self.logger)

    def test_source_freshness_rejects_a_stale_driver(self):
        index = pd.to_datetime(["2026-08-03", "2026-08-07"])
        raw = pd.DataFrame(100.0, index=index, columns=list(TICKERS))
        raw.loc[pd.Timestamp("2026-08-07"), "DXY"] = float("nan")

        provenance = build_source_provenance(raw, date(2026, 8, 7))

        self.assertEqual(provenance["DXY"]["status"], "stale")
        with self.assertRaisesRegex(
            RuntimeError,
            r"DXY observation 2026-08-03 is stale by 4 days \(limit 3\)",
        ):
            validate_source_freshness(provenance, date(2026, 8, 7), self.logger)

    def test_source_freshness_rejects_future_dated_provenance(self):
        raw = pd.DataFrame(
            100.0,
            index=pd.to_datetime(["2026-08-07"]),
            columns=list(TICKERS),
        )
        provenance = build_source_provenance(raw, date(2026, 8, 7))
        provenance["BTC"].update({
            "observation_date": "2026-08-08",
            "age_days": -1,
        })

        with self.assertRaisesRegex(RuntimeError, "BTC observation 2026-08-08 is after"):
            validate_source_freshness(provenance, date(2026, 8, 7), self.logger)

    def test_release_requires_provenance_from_august_14(self):
        with self.assertRaisesRegex(
            ValueError,
            "Source provenance is required for releases from 2026-08-14",
        ):
            validate_release_source_provenance({}, {}, "2026-08-14")

    def test_release_requires_live_retrieval_from_august_14(self):
        raw = pd.DataFrame(
            100.0,
            index=pd.to_datetime(["2026-08-14"]),
            columns=list(TICKERS),
        )
        provenance = build_source_provenance(raw, date(2026, 8, 14))
        metadata = {
            "source_provenance_version": SOURCE_PROVENANCE_VERSION,
            "source_provenance": provenance,
        }
        bridge = deepcopy(metadata)

        validate_release_source_provenance(metadata, bridge, "2026-08-14")

        metadata["source_provenance"]["DXY"]["retrieval_mode"] = "cache"
        bridge = deepcopy(metadata)
        with self.assertRaisesRegex(
            ValueError,
            "Source provenance DXY.retrieval_mode must be live",
        ):
            validate_release_source_provenance(metadata, bridge, "2026-08-14")

    def test_generator_and_independent_validator_source_contracts_match(self):
        generated_contract = {
            driver: {
                "provider": SOURCE_PROVIDER_LABELS[provider_code],
                "provider_code": provider_code,
                "series": series,
                "source_url": SOURCE_URLS[driver],
                "max_age_days": SOURCE_MAX_AGE_DAYS[driver],
            }
            for driver, (provider_code, series) in TICKERS.items()
        }
        self.assertEqual(generated_contract, SOURCE_CONTRACT)


if __name__ == "__main__":
    unittest.main()
