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
                <sheet name="Table 2" sheetId="1" r:id="rId1"/>
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
            "/ppi/detailed-report/ppi-detailed-report-april-2013.pdf"
        )
        preflight._validate_request_path(
            "/ppi/detailed-report/ppi-detailed-report-april-2026.xlsx"
        )
        with self.assertRaisesRegex(RuntimeError, "outside the two fixed"):
            preflight._validate_request_path(
                "/ppi/detailed-report/ppi-detailed-report-may-2013.pdf"
            )

    def test_structural_matcher_returns_identifiers_only(self) -> None:
        matches = preflight._matched_identifiers(
            "WPU0561 — Crude petroleum — 05-61"
        )
        self.assertEqual(
            matches,
            ["05-61", "Crude petroleum", "WPU0561"],
        )
        self.assertNotIn("123.45", matches)

    def test_xlsx_parser_ignores_numeric_cells_and_returns_location_only(self) -> None:
        matches = preflight._extract_xlsx_structural_matches(_synthetic_xlsx())
        self.assertEqual(
            matches,
            [
                {
                    "sheet": "Table 2",
                    "row": 27,
                    "matched_identifiers": ["Crude petroleum", "WPU0561"],
                }
            ],
        )
        serialized = repr(matches)
        self.assertNotIn("123.45", serialized)

    def test_missing_pdftotext_is_fail_closed(self) -> None:
        with mock.patch.object(preflight.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "before first network request"):
                preflight._validate_local_capabilities()


if __name__ == "__main__":
    unittest.main()
