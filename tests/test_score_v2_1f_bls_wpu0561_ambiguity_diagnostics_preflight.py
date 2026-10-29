from __future__ import annotations

import unittest
from pathlib import Path

from scripts import score_v2_1f_wpu0561_ambiguity_diagnostics as diagnostic
from scripts import validate_score_v2_1f_bls_wpu0561_ambiguity_diagnostics_preflight as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FWpu0561AmbiguityDiagnosticsTests(unittest.TestCase):
    def test_v4_activation_is_authorized_but_not_dispatched(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "ambiguity_diagnostics_v4_recheck_authorized_pending_dispatch")
        self.assertEqual(report["design_version"], 4)
        self.assertTrue(report["active_receipt_present"])
        self.assertFalse(report["dispatch_present"])
        self.assertFalse(report["live_request_authorized"])
        self.assertEqual(report["max_economic_observations_total"], 0)
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
        self.assertEqual(blocks[0].identity_status, "proven")
        self.assertEqual(blocks[0].field_status, "unique")
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
        self.assertEqual(blocks[0].release_context_status, "preliminary")
        self.assertEqual(blocks[0].reason_code, "candidate_block_unique")
        self.assertEqual(blocks[1].revision_context_labels, ("revised",))

    def test_multiple_candidate_rows_do_not_erase_identity(self) -> None:
        rows = [
            ["Commodity", "Commodity code", "Index"],
            ["Crude petroleum", "05-61", "<economic-value-not-read>"],
            ["Crude petroleum", "0561", "<economic-value-not-read>"],
        ]
        blocks = diagnostic.diagnose_local_blocks(rows, source_context="archived_original_release")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].identity_status, "proven")
        self.assertEqual(blocks[0].block_status, "multiple")
        self.assertIn("mapped_row_count_multiple", blocks[0].reason_codes)
        self.assertEqual(blocks[0].mapped_candidate_rows, (2, 3))

    def test_field_ambiguity_does_not_erase_identity(self) -> None:
        rows = [
            ["Commodity", "Commodity code", "Index", "Index value"],
            ["Crude petroleum", "05-61", "<economic-value-not-read>", "<economic-value-not-read>"],
        ]
        blocks = diagnostic.diagnose_local_blocks(rows, source_context="archived_original_release")
        self.assertEqual(blocks[0].identity_status, "proven")
        self.assertEqual(blocks[0].block_status, "unique")
        self.assertEqual(blocks[0].field_status, "multiple")
        self.assertIn("index_level_column_count_multiple", blocks[0].reason_codes)

    def test_multiple_unique_blocks_are_reported_without_collapsing_identity(self) -> None:
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
        self.assertTrue(all(block.identity_status == "proven" for block in blocks))

    def test_multirow_header_stack_resolves_leaf_roles(self) -> None:
        rows = [
            ["Commodity", "Index group", "Index group"],
            ["", "Commodity code", "Index"],
            ["Crude petroleum", "05 61", "<economic-value-not-read>"],
        ]
        blocks = diagnostic.diagnose_local_blocks(rows, source_context="archived_original_release")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].header_start_row, 1)
        self.assertEqual(blocks[0].header_end_row, 2)
        self.assertEqual(blocks[0].roles[1], "description")
        self.assertEqual(blocks[0].roles[2], "identifier")
        self.assertEqual(blocks[0].roles[3], "index_level")
        self.assertEqual(blocks[0].identity_status, "proven")

    def test_parent_group_label_does_not_override_explicit_child_identifier(self) -> None:
        rows = [
            ["Commodity", "Index information", "Index information"],
            ["", "Commodity code", "Index"],
            ["Crude petroleum", "WPU0561", "<economic-value-not-read>"],
        ]
        blocks = diagnostic.diagnose_local_blocks(rows, source_context="archived_original_release")
        self.assertEqual(blocks[0].roles[2], "identifier")
        self.assertEqual(blocks[0].identity_status, "proven")

    def test_standalone_code_header_restores_predecessor_compatibility(self) -> None:
        rows = [
            ["Commodity", "Code", "Index"],
            ["Crude petroleum", "05-61", "<economic-value-not-read>"],
        ]
        blocks = diagnostic.diagnose_local_blocks(rows, source_context="archived_original_release")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].roles[2], "identifier")
        self.assertEqual(blocks[0].identity_status, "proven")
        self.assertEqual(blocks[0].field_status, "unique")

    def test_index_code_remains_ambiguous(self) -> None:
        self.assertEqual(diagnostic.header_role("Index code"), "ambiguous")
        rows = [
            ["Commodity", "Index code", "Index"],
            ["Crude petroleum", "05-61", "<economic-value-not-read>"],
        ]
        self.assertEqual(
            diagnostic.resource_reason_summary(
                diagnostic.diagnose_local_blocks(rows, source_context="archived_original_release")
            ),
            {"no_local_header_anchor": 1},
        )

    def test_code_substring_is_not_treated_as_identifier(self) -> None:
        self.assertIsNone(diagnostic.header_role("Barcode"))
        self.assertIsNone(diagnostic.header_role("Decode"))

    def test_identifier_normalization_is_conservative_but_handles_structural_variants(self) -> None:
        for value in ("05-61", "05 61", "0561", "561", "WPU0561", "05–61"):
            self.assertEqual(diagnostic.normalize_identifier(value), "0561")
        self.assertIsNone(diagnostic.normalize_identifier("0561.0"))
        self.assertIsNone(diagnostic.normalize_identifier("foo0561"))

    def test_transport_failure_is_not_content_ambiguity(self) -> None:
        report = diagnostic.not_evaluated_transport("transport_dns_failure")
        self.assertEqual(report.transport_status, "failed")
        self.assertEqual(report.semantic_status, "not_evaluated")
        self.assertEqual(report.reason_code, "transport_dns_failure")

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
