from __future__ import annotations

import unittest
from pathlib import Path

from scripts import score_v2_1f_wpu0561_ambiguity_diagnostics as diagnostic
from scripts import validate_score_v2_1f_bls_wpu0561_ambiguity_diagnostics_preflight as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FWpu0561AmbiguityDiagnosticsTests(unittest.TestCase):
    def test_design_packet_is_hold_zero_value(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "ambiguity_diagnostics_design_only_hold")
        self.assertEqual(report["request_budget"], 2)
        self.assertEqual(report["max_economic_observations_total"], 0)
        self.assertFalse(report["active_receipt_present"])
        self.assertFalse(report["dispatch_present"])
        self.assertFalse(report["live_request_authorized"])
        self.assertFalse(report["economic_value_read_authorized"])
        self.assertFalse(report["candidate_score_computation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_local_blocks_prevent_unrelated_column_role_poisoning(self) -> None:
        rows = [
            ["Preliminary"],
            ["Commodity", "Commodity code", "Index"],
            ["Crude petroleum", "05-61", "<economic-value-not-read>"],
            [""],
            ["Description", "Item code", "Percent change"],
            ["Other item", "9999", "<economic-value-not-read>"],
        ]
        blocks = diagnostic.diagnose_local_blocks(rows, source_context="detailed_report")
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].reason_code, "candidate_block_unique")
        self.assertEqual(blocks[0].revision_context_labels, ("preliminary",))
        self.assertEqual(blocks[0].mapped_candidate_rows, (3,))
        self.assertEqual(blocks[1].reason_code, "mapped_row_count_zero")

    def test_revision_context_is_local_not_whole_sheet(self) -> None:
        rows = [
            ["Preliminary"],
            ["Commodity", "Commodity code", "Index"],
            ["Crude petroleum", "0561", "<economic-value-not-read>"],
            [""],
            ["Revised"],
            ["Description", "Item code", "Index"],
            ["Other item", "9999", "<economic-value-not-read>"],
        ]
        blocks = diagnostic.diagnose_local_blocks(rows, source_context="detailed_report")
        self.assertEqual(blocks[0].revision_context_labels, ("preliminary",))
        self.assertEqual(blocks[0].reason_code, "candidate_block_unique")
        self.assertEqual(blocks[1].revision_context_labels, ("revised",))

    def test_multiple_candidate_rows_remain_fail_closed(self) -> None:
        rows = [
            ["Commodity", "Commodity code", "Index"],
            ["Crude petroleum", "05-61", "<economic-value-not-read>"],
            ["Crude petroleum", "0561", "<economic-value-not-read>"],
        ]
        blocks = diagnostic.diagnose_local_blocks(rows, source_context="archived_original_release")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].reason_code, "mapped_row_count_multiple")
        self.assertEqual(blocks[0].mapped_candidate_rows, (2, 3))

    def test_multiple_unique_blocks_are_reported_without_collapsing_reason(self) -> None:
        rows = [
            ["Commodity", "Commodity code", "Index"],
            ["Crude petroleum", "05-61", "<economic-value-not-read>"],
            [""],
            ["Commodity", "Commodity code", "Index"],
            ["Crude petroleum", "0561", "<economic-value-not-read>"],
        ]
        blocks = diagnostic.diagnose_local_blocks(rows, source_context="archived_original_release")
        summary = diagnostic.resource_reason_summary(blocks)
        self.assertEqual(summary["candidate_block_unique"], 2)
        self.assertEqual(summary["multiple_candidate_blocks"], 1)

    def test_no_anchor_has_explicit_reason(self) -> None:
        rows = [["Crude petroleum", "05-61", "<economic-value-not-read>"]]
        self.assertEqual(
            diagnostic.resource_reason_summary(
                diagnostic.diagnose_local_blocks(rows, source_context="archived_original_release")
            ),
            {"no_local_header_anchor": 1},
        )


if __name__ == "__main__":
    unittest.main()
