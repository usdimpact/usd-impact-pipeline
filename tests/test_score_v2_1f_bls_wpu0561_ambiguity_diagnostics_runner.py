from __future__ import annotations

import io
import json
import unittest
import zipfile
from unittest import mock

from scripts import run_score_v2_1f_bls_wpu0561_ambiguity_diagnostics_preflight as runner


class ScoreV21FWpu0561HeaderGapRunnerTests(unittest.TestCase):
    def test_consumed_state_refuses_before_network(self) -> None:
        with mock.patch.object(
            runner,
            "_request_once",
            side_effect=AssertionError("network request occurred after consumption"),
        ) as request:
            with self.assertRaisesRegex(RuntimeError, "authorization is not active"):
                runner.run_preflight()
            request.assert_not_called()

    def test_v7_selects_one_html_and_direct_xlsx_candidate(self) -> None:
        html = [
            ("table 1", [["Includes crude petroleum."]]),
            (
                "table 2",
                [
                    ["Commodity", "Series code", "Index"],
                    [""],
                    ["Unprocessed nonfood materials"],
                    ["Coal"],
                    ["Natural gas"],
                    ["Crude petroleum"],
                ],
            ),
        ]
        xlsx = [
            (
                "xl/worksheets/sheet3.xml",
                [
                    ["Commodity", "Series code", "Index"],
                    [""],
                    ["Unprocessed nonfood materials"],
                    ["Raw cotton(<num>)"],
                    ["Coal(<num>)"],
                    ["Natural gas(<num>)"],
                    ["Crude petroleum(<num>)"],
                    ["Stage <num> intermediate demand"],
                    ["Stage <num> intermediate demand goods"],
                    ["Corn"],
                    ["Coal(<num>)"],
                    ["Natural gas(<num>)"],
                    ["Crude petroleum(<num>)"],
                ],
            )
        ]
        html_selected, xlsx_selected = runner._select_v7_candidates(html, xlsx)
        self.assertEqual(html_selected[0], "table 2")
        self.assertEqual(html_selected[1], 6)
        self.assertEqual(xlsx_selected[0], "xl/worksheets/sheet3.xml")
        self.assertEqual(xlsx_selected[1], 7)

    def test_v7_prerequisites_fail_closed_when_xlsx_shape_differs(self) -> None:
        html = [("table 1", [["Crude petroleum"]])]
        xlsx = [
            (
                "sheet",
                [
                    ["Unprocessed nonfood materials"],
                    ["Crude petroleum(<num>)"],
                ],
            )
        ]
        with self.assertRaisesRegex(runner.SemanticStop, "xlsx_exact_label"):
            runner._select_v7_candidates(html, xlsx)

    def test_header_gap_result_contains_only_sanitized_structural_text(self) -> None:
        rows = [
            ["Table title <num>"],
            ["Commodity", "Series code", "Index"],
            [""],
            ["Unprocessed nonfood materials"],
            ["Coal"],
            ["Natural gas"],
            ["Crude petroleum(<num>)"],
        ]
        report = runner._header_gap_result(
            runner.XLSX_PATH,
            ("sheet3.xml", 7, rows),
        )
        encoded = json.dumps(report, sort_keys=True)
        self.assertEqual(report["candidate_row"], 7)
        self.assertEqual(report["nearest_recognized_header_row"], 2)
        self.assertEqual(report["nearest_recognized_header_distance"], 5)
        self.assertIn("Commodity", encoded)
        self.assertIn("Series code", encoded)
        self.assertIn("Index", encoded)
        self.assertIn("Unprocessed nonfood materials", encoded)
        self.assertNotIn("WPU0561", encoded)
        self.assertNotIn("252.4", encoded)

    def test_xlsx_parser_ignores_numeric_cells_and_redacts_shared_strings(self) -> None:
        shared = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="7" uniqueCount="7">
          <si><t>Commodity</t></si>
          <si><t>Series code</t></si>
          <si><t>Index</t></si>
          <si><t>Unprocessed nonfood materials</t></si>
          <si><t>Crude petroleum</t></si>
          <si><t>Stage 4 intermediate demand</t></si>
          <si><t>Crude petroleum</t></si>
        </sst>
        """
        sheet = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
          <sheetData>
            <row r="1">
              <c r="A1" t="s"><v>0</v></c>
              <c r="B1" t="s"><v>1</v></c>
              <c r="C1" t="s"><v>2</v></c>
            </row>
            <row r="2"><c r="A2" t="s"><v>3</v></c></row>
            <row r="3">
              <c r="A3" t="s"><v>4</v></c>
              <c r="B3"><v>561</v></c>
              <c r="C3"><v>252.4</v></c>
            </row>
            <row r="4"><c r="A4" t="s"><v>5</v></c></row>
            <row r="5">
              <c r="A5" t="s"><v>6</v></c>
              <c r="B5"><v>561</v></c>
              <c r="C5"><v>252.4</v></c>
            </row>
          </sheetData>
        </worksheet>
        """
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("xl/sharedStrings.xml", shared)
            archive.writestr("xl/worksheets/sheet1.xml", sheet)

        containers = runner._parse_xlsx_containers(buf.getvalue())
        encoded = json.dumps(containers, sort_keys=True)
        self.assertIn("Crude petroleum", encoded)
        self.assertIn("Stage <num> intermediate demand", encoded)
        self.assertNotIn('"561"', encoded)
        self.assertNotIn("252.4", encoded)

    def test_header_gap_bounds_and_request_budget_are_hard_capped(self) -> None:
        self.assertEqual(runner.MAX_HEADER_GAP_ROWS, 32)
        self.assertEqual(runner.MAX_HEADER_GAP_CELLS, 128)
        budget = runner.RequestBudget()
        budget.consume()
        budget.consume()
        with self.assertRaisesRegex(RuntimeError, "budget exceeded"):
            budget.consume()


if __name__ == "__main__":
    unittest.main()
