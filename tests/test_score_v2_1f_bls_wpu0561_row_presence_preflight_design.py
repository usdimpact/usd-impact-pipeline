from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1f_bls_wpu0561_row_presence_preflight as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FWpu0561RowPresenceDesignTests(unittest.TestCase):
    def test_packet_is_v2_design_only_and_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "design_only_hold")
        self.assertEqual(report["version"], 2)
        self.assertEqual(
            report["issue"],
            "https://github.com/usdimpact/usd-impact-pipeline/issues/236",
        )
        self.assertEqual(report["request_budget"], 2)
        self.assertEqual(
            report["fixed_resources"],
            [
                "/news.release/archives/ppi_05152013.htm",
                "/ppi/detailed-report/ppi-detailed-report-april-2026.xlsx",
            ],
        )
        self.assertTrue(report["standard_library_only"])
        self.assertFalse(report["active_receipt_present"])
        self.assertFalse(report["dispatch_present"])
        self.assertFalse(report["response_body_ephemeral_retrieval_authorized"])
        self.assertFalse(report["row_presence_preflight_authorized"])
        self.assertFalse(report["source_value_extraction_authorized"])
        self.assertFalse(report["candidate_score_computation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_design_supersedes_pdf_dependency_and_preserves_value_boundary(self) -> None:
        design = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-design.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(design["version"], 2)
        self.assertEqual(design["supersedes"]["version"], 1)
        self.assertFalse(
            design["runtime_parser_policy"]["install_new_system_software"]
        )
        self.assertFalse(
            design["runtime_parser_policy"]["install_new_python_dependency"]
        )
        self.assertFalse(design["runtime_parser_policy"]["external_parser_process"])
        self.assertEqual(
            design["runtime_parser_policy"]["html_parser"],
            "python_standard_library_html_parser_only",
        )
        self.assertEqual(
            design["runtime_parser_policy"]["xlsx_parser"],
            "python_standard_library_zip_xml_only",
        )
        self.assertTrue(design["forbidden"]["response_body_persistence"])
        self.assertTrue(design["forbidden"]["numeric_source_value_logging"])
        self.assertTrue(design["forbidden"]["numeric_source_value_persistence"])
        self.assertTrue(design["forbidden"]["wpu0561_value_extraction"])
        self.assertTrue(design["forbidden"]["full_historical_reconstruction"])
        self.assertTrue(design["forbidden"]["candidate_score_computation"])
        self.assertTrue(design["forbidden"]["production_change"])


if __name__ == "__main__":
    unittest.main()
