from __future__ import annotations

import unittest
from unittest import mock

from scripts import run_score_v2_1f_bls_detailed_report_metadata_preflight as preflight


class ScoreV21FBlsDetailedReportMetadataPreflightTests(unittest.TestCase):
    def test_consumed_state_refuses_before_network(self) -> None:
        with mock.patch.object(
            preflight,
            "_request_once",
            side_effect=AssertionError("network request occurred after consumption"),
        ) as request:
            with self.assertRaisesRegex(RuntimeError, "authorization is not active"):
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


if __name__ == "__main__":
    unittest.main()
