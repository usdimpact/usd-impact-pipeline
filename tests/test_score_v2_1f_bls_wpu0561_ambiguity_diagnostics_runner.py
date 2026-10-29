from __future__ import annotations

import io
import json
import unittest
import zipfile
from unittest import mock

from scripts import run_score_v2_1f_bls_wpu0561_ambiguity_diagnostics_preflight as runner


class ScoreV21FWpu0561AmbiguityDiagnosticsRunnerTests(unittest.TestCase):
    def test_activation_state_refuses_before_network_without_dispatch(self) -> None:
        with mock.patch.object(
            runner,
            "_request_once",
            side_effect=AssertionError("network request occurred before dispatch"),
        ) as request:
            with self.assertRaisesRegex(RuntimeError, "dispatch is not active"):
                runner.run_preflight()
            request.assert_not_called()

    def test_html_diagnostics_never_emit_economic_values(self) -> None:
        body = b"""
        <html><body><table>
          <tr><th>Commodity</th><th>Commodity code</th><th>Index</th><th>Percent change</th></tr>
          <tr><td>Crude petroleum</td><td>05-61</td><td>252.4</td><td>3.2</td></tr>
        </table></body></html>
        """
        report = runner._diagnose_html(body)
        encoded = json.dumps(report, sort_keys=True)
        self.assertNotIn("252.4", encoded)
        self.assertNotIn("3.2", encoded)
        self.assertIn("0561", encoded)
        self.assertEqual(report["semantic_status"], "evaluated")
        self.assertIn("candidate_block_unique", report["reason_summary"])

    def test_xlsx_diagnostics_never_emit_economic_values(self) -> None:
        shared = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="6" uniqueCount="6">
          <si><t>Preliminary</t></si>
          <si><t>Commodity</t></si>
          <si><t>Commodity code</t></si>
          <si><t>Index</t></si>
          <si><t>Percent change</t></si>
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
              <c r="D2" t="s"><v>4</v></c>
            </row>
            <row r="3">
              <c r="A3" t="s"><v>5</v></c>
              <c r="B3"><v>561</v></c>
              <c r="C3"><v>252.4</v></c>
              <c r="D3"><v>3.2</v></c>
            </row>
          </sheetData>
        </worksheet>
        """
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("xl/sharedStrings.xml", shared)
            archive.writestr("xl/worksheets/sheet1.xml", sheet)

        report = runner._diagnose_xlsx(buf.getvalue())
        encoded = json.dumps(report, sort_keys=True)
        self.assertNotIn("252.4", encoded)
        self.assertNotIn("3.2", encoded)
        self.assertIn("0561", encoded)
        self.assertEqual(report["semantic_status"], "evaluated")
        self.assertIn("candidate_block_unique", report["reason_summary"])

    def test_request_budget_is_hard_capped_at_two(self) -> None:
        budget = runner.RequestBudget()
        budget.consume()
        budget.consume()
        with self.assertRaisesRegex(RuntimeError, "budget exceeded"):
            budget.consume()


if __name__ == "__main__":
    unittest.main()
