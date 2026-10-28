from __future__ import annotations

import unittest

from scripts import run_score_v2_1f_bls_wpu0561_representative_index_preflight as preflight


class ScoreV21FWpu0561RepresentativeIndexRunnerTests(unittest.TestCase):
    def test_dispatched_authorization_gate_validates_without_network(self) -> None:
        user_agent = preflight._validate_authorization_and_dispatch()
        self.assertIn("support@usd-impact.com", user_agent)

    def test_single_index_level_candidate_is_allowed(self) -> None:
        rows = [
            ["Commodity", "Commodity code", "Index", "Percent change"],
            ["Crude petroleum", "05-61", "252.4", "3.2"],
        ]
        report = preflight._classify_rows(
            rows,
            container="table 1",
            source_context="archived_original_release",
        )
        self.assertEqual(report["identifier_columns"], [2])
        self.assertEqual(report["index_level_columns"], [3])
        self.assertEqual(report["percent_change_columns"], [4])
        self.assertIsNone(report["ambiguity"])
        self.assertEqual(
            report["observation"],
            {
                "container": "table 1",
                "row": 2,
                "column": 3,
                "normalized_identifier": "0561",
                "semantic": "original_release_index_level",
                "revision_context": "archived_release_path",
                "value": "252.4",
            },
        )

    def test_multiple_index_level_columns_fail_closed(self) -> None:
        rows = [
            ["Commodity", "Commodity code", "Index", "Index value"],
            ["Crude petroleum", "05-61", "252.4", "252.5"],
        ]
        report = preflight._classify_rows(
            rows,
            container="table 1",
            source_context="archived_original_release",
        )
        self.assertIsNone(report["observation"])
        self.assertEqual(report["ambiguity"], "index_level_column_count_not_one")

    def test_percent_change_is_never_index_level(self) -> None:
        rows = [
            ["Commodity", "Commodity code", "Percent change"],
            ["Crude petroleum", "05-61", "3.2"],
        ]
        report = preflight._classify_rows(
            rows,
            container="table 1",
            source_context="archived_original_release",
        )
        self.assertEqual(report["index_level_columns"], [])
        self.assertEqual(report["percent_change_columns"], [3])
        self.assertIsNone(report["observation"])

    def test_unproven_identifier_does_not_release_value(self) -> None:
        rows = [
            ["Commodity", "Index"],
            ["Crude petroleum", "252.4"],
        ]
        report = preflight._classify_rows(
            rows,
            container="table 1",
            source_context="archived_original_release",
        )
        self.assertEqual(report["mapped_row_count"], 0)
        self.assertIsNone(report["observation"])

    def test_detailed_report_without_revision_context_fails_closed(self) -> None:
        rows = [
            ["Commodity", "Commodity code", "Index"],
            ["Crude petroleum", "05-61", "252.4"],
        ]
        report = preflight._classify_rows(
            rows,
            container="sheet Table 6",
            source_context="detailed_report",
        )
        self.assertIsNone(report["observation"])
        self.assertEqual(report["revision_context_status"], "missing")
        self.assertEqual(report["ambiguity"], "ambiguous_revision_context")

    def test_detailed_report_single_preliminary_context_allows_candidate(self) -> None:
        rows = [
            ["Preliminary"],
            ["Commodity", "Commodity code", "Index"],
            ["Crude petroleum", "05-61", "252.4"],
        ]
        report = preflight._classify_rows(
            rows,
            container="sheet Table 6",
            source_context="detailed_report",
        )
        self.assertEqual(report["revision_context_status"], "preliminary")
        self.assertIsNotNone(report["observation"])
        self.assertEqual(report["observation"]["revision_context"], "preliminary")

    def test_conflicting_revision_context_fails_closed(self) -> None:
        rows = [
            ["Preliminary", "Revised"],
            ["Commodity", "Commodity code", "Index"],
            ["Crude petroleum", "05-61", "252.4"],
        ]
        report = preflight._classify_rows(
            rows,
            container="sheet Table 6",
            source_context="detailed_report",
        )
        self.assertIsNone(report["observation"])
        self.assertEqual(report["revision_context_status"], "conflicting")
        self.assertEqual(report["ambiguity"], "ambiguous_revision_context")

    def test_request_budget_is_hard_capped_at_two(self) -> None:
        budget = preflight.RequestBudget()
        budget.consume()
        budget.consume()
        with self.assertRaisesRegex(RuntimeError, "budget exceeded"):
            budget.consume()


if __name__ == "__main__":
    unittest.main()
