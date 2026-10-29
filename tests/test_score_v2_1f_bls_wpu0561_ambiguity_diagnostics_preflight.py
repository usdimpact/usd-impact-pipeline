from __future__ import annotations

import unittest
from pathlib import Path

from scripts import score_v2_1f_wpu0561_ambiguity_diagnostics as diagnostic
from scripts import validate_score_v2_1f_bls_wpu0561_ambiguity_diagnostics_preflight as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FWpu0561AmbiguityDiagnosticsTests(unittest.TestCase):
    def test_v9_structural_feasibility_hold_is_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(
            report["state"],
            "ambiguity_diagnostics_v9_structural_feasibility_design_only_hold",
        )
        self.assertEqual(report["design_version"], 9)
        self.assertTrue(report["html_index_level_schema_present"])
        self.assertFalse(report["xlsx_selected_container_index_level_schema_present"])
        self.assertFalse(report["pairwise_representative_index_level_feasible"])
        self.assertFalse(report["live_request_authorized"])
        self.assertFalse(report["identifier_value_read_authorized"])
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

    def test_candidate_context_inventory_works_without_header_anchor(self) -> None:
        rows = [
            ["Producer Price Index detailed table"],
            ["Product class", "Series key", "Reference period 2010=100"],
            ["Crude petroleum", "WPU0561", "252.4"],
        ]
        inventory = diagnostic.candidate_context_inventory(rows)
        self.assertEqual(len(inventory), 1)
        self.assertEqual(inventory[0]["candidate_row"], 3)
        encoded = repr(inventory)
        self.assertIn("Product class", encoded)
        self.assertIn("Series key", encoded)
        self.assertIn("Reference period <num>=<num>", encoded)
        self.assertIn("Crude petroleum", encoded)
        self.assertNotIn("WPU0561", encoded)
        self.assertNotIn("252.4", encoded)

    def test_candidate_context_omits_numeric_and_identifier_only_cells(self) -> None:
        rows = [
            ["Header", "05-61", "123.45", "WPU0561"],
            ["Crude petroleum", "561", "3.2", "Dec2025"],
        ]
        inventory = diagnostic.candidate_context_inventory(rows)
        encoded = repr(inventory)
        self.assertIn("Header", encoded)
        self.assertIn("Crude petroleum", encoded)
        self.assertNotIn("05-61", encoded)
        self.assertNotIn("123.45", encoded)
        self.assertNotIn("WPU0561", encoded)
        self.assertNotIn("'561'", encoded)
        self.assertNotIn("3.2", encoded)
        self.assertNotIn("Dec2025", encoded)

    def test_candidate_context_window_is_bounded_to_eight_preceding_rows(self) -> None:
        rows = [[f"row {i} label"] for i in range(1, 12)]
        rows.append(["Crude petroleum"])
        inventory = diagnostic.candidate_context_inventory(rows)
        self.assertEqual(inventory[0]["candidate_row"], 12)
        self.assertEqual(inventory[0]["window_start_row"], 4)
        self.assertEqual(inventory[0]["window_end_row"], 12)
        cell_rows = [cell["row"] for cell in inventory[0]["cells"]]
        self.assertTrue(cell_rows)
        self.assertGreaterEqual(min(cell_rows), 4)
        self.assertNotIn(1, cell_rows)
        self.assertNotIn(2, cell_rows)
        self.assertNotIn(3, cell_rows)

    def test_candidate_context_fails_closed_above_32_candidates(self) -> None:
        rows = [["Crude petroleum"] for _ in range(33)]
        with self.assertRaisesRegex(RuntimeError, "exceeds 32"):
            diagnostic.candidate_context_inventory(rows)

    def test_v6_exact_label_filter_rejects_footnotes_and_concept_variants(self) -> None:
        accepted = (
            "Crude petroleum",
            "Crude petroleum(<num>)",
            "Crude petroleum ( <num> )",
        )
        rejected = (
            "Includes crude petroleum.",
            "Excludes crude petroleum.",
            "Crude petroleum (domestic production)",
            "Crude petroleum extraction",
            "Extraction of crude petroleum, including lease condensate",
            "Pipeline transportation of crude petroleum",
        )
        for value in accepted:
            self.assertTrue(diagnostic.is_exact_target_label(value), value)
        for value in rejected:
            self.assertFalse(diagnostic.is_exact_target_label(value), value)

    def test_v6_consumed_html_shape_narrows_three_to_one_by_label_only(self) -> None:
        rows = [
            ["Footnotes (<num>) Includes crude petroleum. (<num>) Excludes crude petroleum."],
            ["Crude petroleum"],
            ["Footnotes (<num>) Includes crude petroleum. (<num>) Excludes crude petroleum."],
        ]
        self.assertEqual(diagnostic.exact_target_rows(rows), (2,))

    def test_v6_xlsx_direct_commodity_context_is_distinct_from_stage_demand(self) -> None:
        direct_rows = [
            ["Raw milk"],
            ["Hay and hayseeds(<num>)"],
            ["Oilseeds"],
            ["Raw cane sugar and byproducts(<num>)"],
            ["Unprocessed nonfood materials"],
            ["Raw cotton(<num>)"],
            ["Coal(<num>)"],
            ["Natural gas(<num>)"],
            ["Crude petroleum(<num>)"],
        ]
        stage_rows = [
            ["Stage <num> intermediate demand"],
            ["Stage <num> intermediate demand goods"],
            ["Corn"],
            ["Oilseeds"],
            ["Prepared animal feeds"],
            ["Coal(<num>)"],
            ["Natural gas(<num>)"],
            ["Natural gas liquids(<num>)"],
            ["Crude petroleum(<num>)"],
        ]
        direct = diagnostic.classify_exact_target_context(direct_rows, 9)
        stage = diagnostic.classify_exact_target_context(stage_rows, 9)
        self.assertEqual(direct["context_status"], "commodity_unprocessed_nonfood_context")
        self.assertTrue(direct["unprocessed_nonfood_context"])
        self.assertFalse(direct["stage_intermediate_demand_context"])
        self.assertEqual(stage["context_status"], "stage_intermediate_demand_context")
        self.assertTrue(stage["stage_intermediate_demand_context"])
        self.assertFalse(stage["unprocessed_nonfood_context"])

    def test_v6_context_discriminator_fails_closed_on_mixed_or_unknown_context(self) -> None:
        mixed_rows = [
            ["Unprocessed nonfood materials"],
            ["Stage <num> intermediate demand goods"],
            ["Crude petroleum(<num>)"],
        ]
        unknown_rows = [
            ["Coal"],
            ["Natural gas"],
            ["Crude petroleum(<num>)"],
        ]
        mixed = diagnostic.classify_exact_target_context(mixed_rows, 3)
        unknown = diagnostic.classify_exact_target_context(unknown_rows, 3)
        self.assertEqual(mixed["context_status"], "ambiguous_mixed_context")
        self.assertEqual(unknown["context_status"], "exact_label_unclassified_context")

    def test_v6_context_discriminator_does_not_use_row_number_as_semantics(self) -> None:
        first = [
            ["Unprocessed nonfood materials"],
            ["Coal"],
            ["Natural gas"],
            ["Crude petroleum(<num>)"],
        ]
        shifted = [["Unrelated title"]] * 20 + first
        self.assertEqual(
            diagnostic.classify_exact_target_context(first, 4)["context_status"],
            diagnostic.classify_exact_target_context(shifted, 24)["context_status"],
        )

    def test_v7_header_gap_inventory_redacts_identifier_and_economic_values(self) -> None:
        rows = [
            ["Table title 2026"],
            ["Commodity", "Series code", "Index"],
            ["Unprocessed nonfood materials", "", ""],
            ["Coal", "9999", "250.1"],
            ["Natural gas", "8888", "175.2"],
            ["Crude petroleum(<num>)", "WPU0561", "252.4"],
        ]
        report = diagnostic.candidate_local_header_gap_inventory(rows, 6)
        encoded = repr(report)
        self.assertIn("Table title <num>", encoded)
        self.assertIn("Commodity", encoded)
        self.assertIn("Series code", encoded)
        self.assertIn("Index", encoded)
        self.assertIn("Unprocessed nonfood materials", encoded)
        self.assertNotIn("2026", encoded)
        self.assertNotIn("9999", encoded)
        self.assertNotIn("8888", encoded)
        self.assertNotIn("WPU0561", encoded)
        self.assertNotIn("250.1", encoded)
        self.assertNotIn("175.2", encoded)
        self.assertNotIn("252.4", encoded)

    def test_v7_header_gap_inventory_reports_nearest_recognized_header_distance(self) -> None:
        rows = [
            ["Intro"],
            ["Commodity", "Series code", "Index"],
            [""],
            ["Unprocessed nonfood materials"],
            ["Coal"],
            ["Natural gas"],
            ["Crude petroleum(<num>)"],
        ]
        report = diagnostic.candidate_local_header_gap_inventory(rows, 7)
        self.assertEqual(report["nearest_recognized_header_row"], 2)
        self.assertEqual(report["nearest_recognized_header_distance"], 5)
        self.assertIn(3, report["blank_separator_rows"])
        self.assertFalse(report["truncated"])

    def test_v7_header_gap_inventory_is_hard_bounded(self) -> None:
        rows = [[f"label {i}"] for i in range(1, 40)] + [["Crude petroleum(<num>)"]]
        report = diagnostic.candidate_local_header_gap_inventory(rows, 40)
        self.assertEqual(report["window_start_row"], 8)
        self.assertEqual(report["window_end_row"], 39)
        with self.assertRaisesRegex(ValueError, "must remain 32"):
            diagnostic.candidate_local_header_gap_inventory(
                rows,
                40,
                max_preceding_rows=31,
            )
        with self.assertRaisesRegex(ValueError, "must remain 128"):
            diagnostic.candidate_local_header_gap_inventory(
                rows,
                40,
                max_cells=127,
            )

    def test_v7_header_gap_inventory_requires_exact_target_candidate(self) -> None:
        rows = [
            ["Commodity", "Series code", "Index"],
            ["Crude petroleum (domestic production)"],
        ]
        with self.assertRaisesRegex(ValueError, "exact target label"):
            diagnostic.candidate_local_header_gap_inventory(rows, 2)

    def test_v8_header_band_inventory_is_top_bounded_and_structural(self) -> None:
        rows = [
            ["Producer Price Index detailed table 2026"],
            ["Commodity", "Series code", "Index"],
            [""],
            ["Section title"],
        ] + [[f"data label {i}"] for i in range(5, 40)]
        report = diagnostic.container_header_band_inventory(rows)
        self.assertEqual(report["band_start_row"], 1)
        self.assertEqual(report["band_end_row"], 32)
        self.assertEqual(report["first_nonempty_row"], 1)
        self.assertEqual(report["last_nonempty_row"], 32)
        self.assertIn(3, report["blank_rows"])
        recognized = report["recognized_header_role_rows"]
        self.assertTrue(any(row["row"] == 2 for row in recognized))
        self.assertFalse(report["truncated"])

    def test_v8_header_band_inventory_redacts_numeric_and_identifier_text(self) -> None:
        rows = [
            ["Report 2026"],
            ["Commodity", "Series code", "Index"],
            ["Crude petroleum", "WPU0561", "252.4"],
        ]
        report = diagnostic.container_header_band_inventory(rows)
        encoded = repr(report)
        self.assertIn("Report <num>", encoded)
        self.assertIn("Commodity", encoded)
        self.assertIn("Series code", encoded)
        self.assertIn("Index", encoded)
        self.assertIn("Crude petroleum", encoded)
        self.assertNotIn("2026", encoded)
        self.assertNotIn("WPU0561", encoded)
        self.assertNotIn("252.4", encoded)

    def test_v8_header_band_inventory_has_hard_bounds(self) -> None:
        rows = [["Header"]] * 40
        with self.assertRaisesRegex(ValueError, "max_rows must remain 32"):
            diagnostic.container_header_band_inventory(rows, max_rows=31)
        with self.assertRaisesRegex(ValueError, "max_cells must remain 128"):
            diagnostic.container_header_band_inventory(rows, max_cells=127)

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
