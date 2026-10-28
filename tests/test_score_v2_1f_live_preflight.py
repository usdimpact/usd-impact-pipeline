from __future__ import annotations

import unittest
from datetime import date
from unittest import mock

from scripts import run_score_v2_1f_live_preflight as preflight


class ScoreV21FLivePreflightTests(unittest.TestCase):
    def test_exact_source_families_exclude_h15(self) -> None:
        self.assertEqual(set(preflight.FED_FAMILIES), {"H10", "H8", "H41"})
        self.assertNotIn("H15", preflight.FED_FAMILIES)
        self.assertEqual(len(preflight.EXPECTED_SERIES), 5)
        self.assertFalse(any("H15/" in value for value in preflight.EXPECTED_SERIES))

    def test_url_allowlist_rejects_unapproved_hosts_and_credentials(self) -> None:
        self.assertEqual(
            preflight._validate_url("https://www.federalreserve.gov/releases/h10/"),
            "www.federalreserve.gov",
        )
        self.assertEqual(
            preflight._validate_url("https://www.bls.gov/bls/news-release/ppi.htm"),
            "www.bls.gov",
        )
        with self.assertRaisesRegex(RuntimeError, "outside authorization allowlist"):
            preflight._validate_url("https://fred.stlouisfed.org/series/DGS10")
        with self.assertRaisesRegex(RuntimeError, "credentials"):
            preflight._validate_url("https://user:pass@www.bls.gov/test")

    def test_bls_release_date_extraction_respects_authorized_window(self) -> None:
        payload = b"""
        ppi_12312012.htm
        ppi_10292013.htm
        ppi_02192020.htm
        ppi_10152026.htm
        ppi_10302026.htm
        """
        self.assertEqual(
            preflight.extract_bls_release_dates(payload),
            [date(2013, 10, 29), date(2020, 2, 19), date(2026, 10, 15)],
        )

    def test_bls_crude_petroleum_presence_parser_is_value_agnostic(self) -> None:
        self.assertTrue(
            preflight._bls_crude_petroleum_parseable(
                "Table 2. 05-61 Crude petroleum [redacted source values]"
            )
        )
        self.assertTrue(
            preflight._bls_crude_petroleum_parseable(
                "0561 Crude petroleum no value retained"
            )
        )
        self.assertFalse(preflight._bls_crude_petroleum_parseable("Finished gasoline 0571"))

    def test_consumed_state_refuses_before_any_network_call(self) -> None:
        with mock.patch.object(
            preflight,
            "_get_fixed",
            side_effect=AssertionError("network request after Stage 1 consumption"),
        ) as request:
            with self.assertRaisesRegex(RuntimeError, "authorization is not active"):
                preflight.run_preflight()
            request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
