from __future__ import annotations

import io
import json
import unittest
import zipfile
from unittest import mock

from scripts import run_score_v2_1f_bls_wpu0561_ambiguity_diagnostics_preflight as runner


class ScoreV21FWpu0561CandidateContextRunnerTests(unittest.TestCase):
    def test_dispatched_gate_validates_without_network(self) -> None:
        with mock.patch.object(
            runner,
            "_request_once",
            side_effect=AssertionError("network request occurred during gate validation"),
        ) as request:
            user_agent = runner._validate_authorization_and_dispatch()
            self.assertIn("support@usd-impact.com", user_agent)
            request.assert_not_called()

    def test_html_candidate_context_redacts_identifiers_and_economic_values(self) -> None:
        body = b"""
        <html><body><table>
          <tr><th>Producer Price Index detailed table 2026</th></tr>
          <tr><th>Product class</th><th>Series key</th><th>Reference period 2010=100</th></tr>
          <tr><td>Crude petroleum</td><td>WPU0561</td><td>252.4</td></tr>
        </table></body></html>
        """
        report = runner._inventory_html(body)
        encoded = json.dumps(report, sort_keys=True)
        self.assertEqual(report["candidate_count"], 1)
        self.assertIn("Crude petroleum", encoded)
        self.assertIn("Product class", encoded)
        self.assertIn("Series key", encoded)
        self.assertNotIn("WPU0561", encoded)
        self.assertNotIn("0561", encoded)
        self.assertNotIn("252.4", encoded)
        self.assertNotIn("2010", encoded)
        self.assertNotIn("100", encoded)

    def test_xlsx_candidate_context_redacts_identifiers_and_economic_values(self) -> None:
        shared = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="5" uniqueCount="5">
          <si><t>Producer Price Index detailed table 2026</t></si>
          <si><t>Product class</t></si>
          <si><t>Series key</t></si>
          <si><t>Reference period 2010=100</t></si>
          <si><t>Crude petroleum</t></si>
        </sst>
        """
        sheet = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
          <sheetData>
            <row r="1"><c r="A1" t="s"><v>0</v></c></row>
            <row r="2">
              <c r="A2" t="s"><v>1</v></c>
              <c r="B2" t="s"><v>2</v></c>
              <c r="C2" t="s"><v>3</v></c>
            </row>
            <row r="3">
              <c r="A3" t="s"><v>4</v></c>
              <c r="B3"><v>561</v></c>
              <c r="C3"><v>252.4</v></c>
            </row>
          </sheetData>
        </worksheet>
        """
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("xl/sharedStrings.xml", shared)
            archive.writestr("xl/worksheets/sheet1.xml", sheet)

        report = runner._inventory_xlsx(buf.getvalue())
        encoded = json.dumps(report, sort_keys=True)
        self.assertEqual(report["candidate_count"], 1)
        self.assertIn("Crude petroleum", encoded)
        self.assertIn("Product class", encoded)
        self.assertIn("Series key", encoded)
        self.assertNotIn("561", encoded)
        self.assertNotIn("252.4", encoded)
        self.assertNotIn("2010", encoded)
        self.assertNotIn("100", encoded)

    def test_context_bounds_are_enforced(self) -> None:
        self.assertEqual(runner.MAX_CANDIDATES_PER_RESOURCE, 32)
        self.assertEqual(runner.MAX_PRECEDING_ROWS, 8)
        self.assertEqual(runner.MAX_TEXT_CELLS_PER_CANDIDATE, 64)

    def test_request_budget_is_hard_capped_at_two(self) -> None:
        budget = runner.RequestBudget()
        budget.consume()
        budget.consume()
        with self.assertRaisesRegex(RuntimeError, "budget exceeded"):
            budget.consume()


if __name__ == "__main__":
    unittest.main()
