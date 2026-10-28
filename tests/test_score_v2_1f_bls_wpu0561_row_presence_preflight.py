from __future__ import annotations

import io
import unittest
import zipfile
from unittest import mock

from scripts import run_score_v2_1f_bls_wpu0561_row_presence_preflight as preflight


def _synthetic_xlsx() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "xl/workbook.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
            <workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
                      xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
              <sheets>
                <sheet name="Table 6" sheetId="1" r:id="rId1"/>
              </sheets>
            </workbook>""",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
            <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
              <Relationship Id="rId1"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
                Target="worksheets/sheet1.xml"/>
            </Relationships>""",
        )
        archive.writestr(
            "xl/sharedStrings.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
            <sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
                 count="2" uniqueCount="2">
              <si><t>WPU0561</t></si>
              <si><t>Crude petroleum</t></si>
            </sst>""",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
            <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
              <sheetData>
                <row r="27">
                  <c r="A27" t="s"><v>0</v></c>
                  <c r="B27" t="s"><v>1</v></c>
                  <c r="C27"><v>123.45</v></c>
                </row>
              </sheetData>
            </worksheet>""",
        )
    return output.getvalue()


def _synthetic_html() -> bytes:
    return b"""
    <html><body>
      <table>
        <tr><th>Grouping</th><th>Commodity code</th><th>Index</th></tr>
        <tr><td>Natural gas</td><td>05-31</td><td>999.1</td></tr>
        <tr><td>Crude petroleum</td><td>05-61</td><td>252.4</td></tr>
      </table>
    </body></html>
    """


class ScoreV21FWpu0561RowPresenceRunnerTests(unittest.TestCase):
    def test_design_only_state_refuses_before_network(self) -> None:
        with mock.patch.object(
            preflight,
            "_request_once",
            side_effect=AssertionError("network request occurred in HOLD state"),
        ) as request:
            with self.assertRaisesRegex(RuntimeError, "authorization is not active"):
                preflight.run_preflight()
            request.assert_not_called()

    def test_request_budget_is_hard_capped_at_two(self) -> None:
        budget = preflight.RequestBudget()
        budget.consume()
        budget.consume()
        self.assertEqual(budget.count, 2)
        with self.assertRaisesRegex(RuntimeError, "budget exceeded"):
            budget.consume()

    def test_only_two_fixed_resources_are_allowed(self) -> None:
        preflight._validate_request_path(
            "/news.release/archives/ppi_05152013.htm"
        )
        preflight._validate_request_path(
            "/ppi/detailed-report/ppi-detailed-report-april-2026.xlsx"
        )
        with self.assertRaisesRegex(RuntimeError, "outside the two fixed"):
            preflight._validate_request_path(
                "/ppi/detailed-report/ppi-detailed-report-april-2013.pdf"
            )

    def test_html_parser_returns_table_row_and_tokens_only(self) -> None:
        matches = preflight._extract_html_structural_matches(_synthetic_html())
        self.assertEqual(
            matches,
            [
                {
                    "table": 1,
                    "row": 3,
                    "matched_identifiers": ["05-61", "Crude petroleum"],
                }
            ],
        )
        serialized = repr(matches)
        self.assertNotIn("252.4", serialized)
        self.assertNotIn("999.1", serialized)

    def test_xlsx_parser_ignores_numeric_cells_and_returns_location_only(self) -> None:
        matches = preflight._extract_xlsx_structural_matches(_synthetic_xlsx())
        self.assertEqual(
            matches,
            [
                {
                    "sheet": "Table 6",
                    "row": 27,
                    "matched_identifiers": ["Crude petroleum", "WPU0561"],
                }
            ],
        )
        serialized = repr(matches)
        self.assertNotIn("123.45", serialized)

    def test_structural_matcher_returns_identifiers_only(self) -> None:
        matches = preflight._matched_identifiers(
            "WPU0561 — Crude petroleum — 05-61"
        )
        self.assertEqual(
            matches,
            ["05-61", "Crude petroleum", "WPU0561"],
        )
        self.assertNotIn("123.45", matches)


if __name__ == "__main__":
    unittest.main()
