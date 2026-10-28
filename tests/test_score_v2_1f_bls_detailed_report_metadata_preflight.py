from __future__ import annotations

import unittest
from unittest import mock

from scripts import run_score_v2_1f_bls_detailed_report_metadata_preflight as preflight


class ScoreV21FBlsDetailedReportMetadataPreflightTests(unittest.TestCase):
    def test_activated_but_undispatched_state_refuses_before_network(self) -> None:
        with mock.patch.object(
            preflight,
            "_request_once",
            side_effect=AssertionError("network request occurred before dispatch"),
        ) as request:
            with self.assertRaisesRegex(RuntimeError, "dispatch is not active"):
                preflight.run_preflight()
            request.assert_not_called()

    def test_request_budget_is_hard_capped_at_four(self) -> None:
        budget = preflight.RequestBudget()
        for _ in range(4):
            budget.consume()
        self.assertEqual(budget.count, 4)
        with self.assertRaisesRegex(RuntimeError, "budget exceeded"):
            budget.consume()

    def test_only_fixed_gets_and_report_heads_are_allowed(self) -> None:
        preflight._validate_request_path("GET", "/robots.txt")
        preflight._validate_request_path("GET", "/ppi/detailed-report/")
        preflight._validate_request_path(
            "HEAD",
            "/ppi/detailed-report/ppi-detailed-report-january-2013.pdf",
        )
        preflight._validate_request_path(
            "HEAD",
            "/ppi/detailed-report/ppi-detailed-report-january-2026.xlsx",
        )
        with self.assertRaisesRegex(RuntimeError, "outside the fixed"):
            preflight._validate_request_path(
                "GET",
                "/ppi/detailed-report/ppi-detailed-report-january-2013.pdf",
            )
        with self.assertRaisesRegex(RuntimeError, "outside the fixed"):
            preflight._validate_request_path("POST", "/ppi/detailed-report/")

    def test_archive_parser_extracts_metadata_not_values(self) -> None:
        payload = b"""
        <html><body>
          <h4>2026 Producer Price Index Detailed Reports</h4>
          <a href="/ppi/detailed-report/ppi-detailed-report-january-2026.pdf">PDF</a>
          <a href="/ppi/detailed-report/ppi-detailed-report-january-2026.xlsx">XLSX</a>
          <p>October 2025: Not Available</p>
          <p><a href="/ppi/detailed-report/ppi-detailed-report-february-2016.pdf">February 2016</a> CORRECTED</p>
          <h4>2013 Producer Price Index Detailed Reports</h4>
          <a href="/ppi/detailed-report/ppi-detailed-report-january-2013.pdf">January 2013</a>
        </body></html>
        """
        result = preflight._parse_archive_index(payload)
        self.assertTrue(result["has_2013"])
        self.assertTrue(result["has_2026"])
        self.assertTrue(result["expected_unavailable_2025_10_seen"])
        self.assertIn("February 2016", result["corrected_labels"])
        self.assertTrue(str(result["selected_2013_path"]).endswith(".pdf"))
        self.assertTrue(str(result["selected_2026_path"]).endswith(".xlsx"))
        self.assertNotIn("value", result)

    def test_off_domain_archive_resource_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "approved BLS host"):
            preflight._path_from_href(
                "https://example.com/ppi/detailed-report/report-2013.pdf"
            )

    def test_contactable_user_agent_is_required(self) -> None:
        valid = (
            "USD-Impact-Score-v2.1F-BLS-metadata-preflight/1.0 "
            "(contact: support@usd-impact.com)"
        )
        self.assertEqual(preflight._validate_contact_user_agent(valid), valid)
        with self.assertRaisesRegex(RuntimeError, "User-Agent"):
            preflight._validate_contact_user_agent("python-http-client")


if __name__ == "__main__":
    unittest.main()
