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
            preflight._validate_url("https://www.bls.gov/bls/news-release/ppi.htm"),
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

    def test_html_parser_suppresses_script_and_style_variants(self) -> None:
        payload = b"<div>visible<script>alert(1)</script ><style>x</style ></div>"
        text = preflight._html_text(payload)
        self.assertIn("visible", text)
        self.assertNotIn("alert", text)

    def test_fed_fixed_samples_span_authorized_window(self) -> None:
        for family, cfg in preflight.FED_FAMILIES.items():
            samples = tuple(cfg["sample_dates"])
            self.assertEqual(len(samples), 3, family)
            self.assertLessEqual(preflight.START, samples[0], family)
            self.assertLess(samples[0], samples[1], family)
            self.assertLess(samples[1], samples[2], family)
            self.assertLessEqual(samples[2], preflight.END, family)
            self.assertTrue(cfg["landing_tokens"], family)
            self.assertTrue(cfg["tokens"], family)

    def test_bls_release_date_extraction_respects_authorized_window(self) -> None:
        payload = b"""
        <a href="/news.release/archives/ppi_12142012.htm">old</a>
        <a href="/news.release/archives/ppi_10292013.htm">in</a>
        <a href="/news.release/archives/ppi_10152026.htm">in</a>
        <a href="/news.release/archives/ppi_11122026.htm">future</a>
        """
        self.assertEqual(
            preflight.extract_bls_release_dates(payload),
            [date(2013, 10, 29), date(2026, 10, 15)],
        )

    def test_bls_crude_petroleum_parser_accepts_historical_code_forms(self) -> None:
        self.assertTrue(preflight._bls_crude_petroleum_parseable("Crude petroleum 05-61 267.3"))
        self.assertTrue(preflight._bls_crude_petroleum_parseable("Crude petroleum 05 61 12.1"))
        self.assertTrue(preflight._bls_crude_petroleum_parseable("0561 Crude petroleum"))
        self.assertFalse(preflight._bls_crude_petroleum_parseable("Crude petroleum only"))
        self.assertFalse(preflight._bls_crude_petroleum_parseable("05-61 unrelated"))

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
