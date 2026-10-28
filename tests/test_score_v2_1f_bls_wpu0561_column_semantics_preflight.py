from __future__ import annotations

import io
import unittest
import zipfile
from unittest import mock

from scripts import run_score_v2_1f_bls_wpu0561_column_semantics_preflight as preflight


def _synthetic_html() -> bytes:
    return b"""
    <html><body>
      <table>
        <tr><th>Commodity</th><th>Commodity code</th><th>Index</th></tr>
        <tr><td>Crude petroleum</td><td>05-61</td><td>252.4</td></tr>
      </table>
    </body></html>
    """


def _synthetic_html_unproven_05_61() -> bytes:
    return b"""
    <html><body>
      <table>
        <tr><th>Commodity</th><th>Index</th></tr>
        <tr><td>Crude petroleum</td><td>05-61</td></tr>
      </table>
    </body></html>
    """


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
                 count="4" uniqueCount="4">
              <si><t>Commodity</t></si>
              <si><t>Commodity code</t></si>
              <si><t>Index</t></si>
              <si><t>Crude petroleum</t></si>
            </sst>""",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
            <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
              <sheetData>
                <row r="1">
                  <c r="A1" t="s"><v>0</v></c>
                  <c r="B1" t="s"><v>1</v></c>
                  <c r="C1" t="s"><v>2</v></c>
                </row>
                <row r="2">
                  <c r="A2" t="s"><v>3</v></c>
                  <c r="B2"><v>561</v></c>
                  <c r="C2"><v>123.45</v></c>
                </row>
              </sheetData>
            </worksheet>""",
        )
    return output.getvalue()


def _synthetic_ambiguous_xlsx() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "xl/workbook.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
            <workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
                      xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
              <sheets>
                <sheet name="Ambiguous" sheetId="1" r:id="rId1"/>
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
                 count="3" uniqueCount="3">
              <si><t>Commodity</t></si>
              <si><t>Index code</t></si>
              <si><t>Crude petroleum</t></si>
            </sst>""",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
            <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
              <sheetData>
                <row r="1">
                  <c r="A1" t="s"><v>0</v></c>
                  <c r="B1" t="s"><v>1</v></c>
                </row>
                <row r="2">
                  <c r="A2" t="s"><v>2</v></c>
                  <c r="B2"><v>561</v></c>
                </row>
              </sheetData>
            </worksheet>""",
        )
    return output.getvalue()


class ScoreV21FWpu0561ColumnSemanticsRunnerTests(unittest.TestCase):
    def test_consumed_state_refuses_before_network(self) -> None:
        with mock.patch.object(
            preflight,
            "_request_once",
            side_effect=AssertionError("network request occurred after consumption"),
        ) as request:
            with self.assertRaisesRegex(RuntimeError, "authorization is not active"):
                preflight.run_preflight()
            request.assert_not_called()

    def test_html_semantics_maps_05_61_without_economic_value(self) -> None:
        reports = preflight._extract_html_semantics(_synthetic_html())
        self.assertEqual(reports[0]["identifier_columns"], [2])
        self.assertEqual(reports[0]["description_columns"], [1])
        self.assertEqual(reports[0]["economic_columns"], [3])
        self.assertEqual(reports[0]["matches"][0]["identifiers"], ["0561"])
        self.assertEqual(
            reports[0]["matches"][0]["mapping_status"],
            "mapped_to_0561",
        )
        self.assertNotIn("252.4", repr(reports))

    def test_xlsx_numeric_identifier_exception_excludes_index_value(self) -> None:
        reports = preflight._extract_xlsx_semantics(_synthetic_xlsx())
        report = reports[0]
        self.assertEqual(report["identifier_columns"], [2])
        self.assertEqual(report["description_columns"], [1])
        self.assertEqual(report["economic_columns"], [3])
        match = report["matches"][0]
        self.assertEqual(match["identifiers"], ["0561"])
        self.assertEqual(match["mapping_status"], "mapped_to_0561")
        self.assertEqual(
            match["identifier_fields"],
            [
                {
                    "column": 2,
                    "cell_type": "numeric",
                    "normalized_identifier": "0561",
                }
            ],
        )
        self.assertNotIn("123.45", repr(reports))

    def test_html_05_61_without_proven_identifier_header_does_not_map(self) -> None:
        reports = preflight._extract_html_semantics(_synthetic_html_unproven_05_61())
        report = reports[0]
        self.assertEqual(report["identifier_columns"], [])
        self.assertEqual(report["economic_columns"], [2])
        self.assertEqual(report["matches"][0]["identifiers"], [])
        self.assertEqual(
            report["matches"][0]["mapping_status"],
            "description_only",
        )

    def test_index_code_header_is_ambiguous_and_numeric_561_is_not_retained(self) -> None:
        reports = preflight._extract_xlsx_semantics(_synthetic_ambiguous_xlsx())
        report = reports[0]
        self.assertEqual(report["identifier_columns"], [])
        self.assertEqual(report["ambiguous_columns"], [2])
        match = report["matches"][0]
        self.assertEqual(match["identifiers"], [])
        self.assertEqual(match["identifier_fields"], [])
        self.assertEqual(match["mapping_status"], "description_only")
        self.assertNotIn("561", repr(match))

    def test_request_budget_is_hard_capped_at_two(self) -> None:
        budget = preflight.RequestBudget()
        budget.consume()
        budget.consume()
        with self.assertRaisesRegex(RuntimeError, "budget exceeded"):
            budget.consume()


if __name__ == "__main__":
    unittest.main()
