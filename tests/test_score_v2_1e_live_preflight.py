from __future__ import annotations

import unittest
from datetime import date

from scripts import run_score_v2_1e_live_preflight as preflight


class ScoreV21ELivePreflightTests(unittest.TestCase):
    def test_source_url_allowlist_is_fail_closed(self) -> None:
        self.assertEqual(
            preflight._validate_url("https://www.federalreserve.gov/releases/h8/"),
            "www.federalreserve.gov",
        )
        self.assertEqual(
            preflight._validate_url("https://www.bls.gov/ppi/detailed-report/"),
            "www.bls.gov",
        )
        with self.assertRaises(RuntimeError):
            preflight._validate_url("http://www.bls.gov/ppi/")
        with self.assertRaises(RuntimeError):
            preflight._validate_url("https://example.com/data")
        with self.assertRaises(RuntimeError):
            preflight._validate_url("https://download.bls.gov/pub/time.series/wp/")

    def test_live_source_paths_reject_noncanonical_input(self) -> None:
        preflight._validate_path("/releases/h8/")
        with self.assertRaises(RuntimeError):
            preflight._validate_path("releases/h8/")
        with self.assertRaises(RuntimeError):
            preflight._validate_path("/releases/../h8/")
        with self.assertRaises(RuntimeError):
            preflight._validate_path("/https://example.com/")

    def test_fed_release_date_extraction_respects_authorized_window(self) -> None:
        payload = b"""
        <a href="/releases/h8/20121228/">old</a>
        <a href="/releases/h8/20130104/">in</a>
        <a href="/releases/h8/20261023/default.htm">in</a>
        <a href="/releases/h8/20261030/">future</a>
        """
        self.assertEqual(
            preflight.extract_fed_release_dates(payload, "h8"),
            [date(2013, 1, 4), date(2026, 10, 23)],
        )

    def test_bls_report_path_extraction_reconstructs_canonical_paths(self) -> None:
        payload = b"""
        <a href="/ppi/detailed-report/ppi-detailed-report-december-2012.pdf">old</a>
        <a href="/ppi/detailed-report/ppi-detailed-report-january-2013.pdf">in</a>
        <a href="https://evil.invalid/ppi-detailed-report-september-2026.pdf">identifier only</a>
        """
        rows = preflight.[(d, None) for d in preflight.extract_bls_report_identifiers(payload)]
        self.assertEqual(rows[0][0], date(2013, 1, 1))
        self.assertEqual(rows[-1][0], date(2026, 9, 1))
        self.assertEqual(len(rows), 2)

    def test_wpu0561_parser_requires_series_and_description(self) -> None:
        text = """
        0560 Crude energy materials 120.0 121.0 122.0
        0561 Crude petroleum 165.6 202.9 182.5 74.8 -10.1
        """
        self.assertTrue(preflight._bls_wpu0561_parseable(text))
        self.assertFalse(preflight._bls_wpu0561_parseable("0561 unrelated label 1 2 3"))
        self.assertFalse(preflight._bls_wpu0561_parseable("Crude petroleum 1 2 3"))

    def test_family_label_matching_is_presence_only(self) -> None:
        self.assertTrue(
            preflight._matches_family(
                "Bank credit — All commercial banks",
                (("bank credit",), ("commercial banks",)),
            )
        )
        self.assertFalse(
            preflight._matches_family(
                "Bank credit only",
                (("bank credit",), ("commercial banks",)),
            )
        )


if __name__ == "__main__":
    unittest.main()
