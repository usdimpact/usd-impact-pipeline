from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1f_bls_wpu0561_column_semantics_preflight as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FWpu0561ColumnSemanticsDesignTests(unittest.TestCase):
    def test_packet_is_design_only_and_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "design_only_hold")
        self.assertEqual(
            report["issue"],
            "https://github.com/usdimpact/usd-impact-pipeline/issues/244",
        )
        self.assertEqual(report["request_budget"], 2)
        self.assertFalse(report["active_receipt_present"])
        self.assertFalse(report["dispatch_present"])
        self.assertFalse(report["response_body_ephemeral_retrieval_authorized"])
        self.assertFalse(report["column_semantics_preflight_authorized"])
        self.assertFalse(report["numeric_identifier_field_read_authorized"])
        self.assertFalse(report["economic_value_extraction_authorized"])
        self.assertFalse(report["candidate_score_computation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_design_preserves_identifier_only_exception(self) -> None:
        design = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-design.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            design["identifier_policy"]["ambiguous_cell_behavior"],
            "discard_value_emit_ambiguity_only",
        )
        self.assertEqual(
            design["identifier_policy"]["conflicting_header_behavior"],
            "classify_ambiguous_never_identifier",
        )
        self.assertFalse(
            design["identifier_policy"]["row_wide_identifier_fallback"]
        )
        self.assertTrue(design["forbidden"]["economic_index_value_extraction"])
        self.assertTrue(design["forbidden"]["economic_percent_change_extraction"])
        self.assertTrue(design["forbidden"]["economic_value_logging"])
        self.assertTrue(design["forbidden"]["economic_value_persistence"])
        self.assertTrue(design["forbidden"]["candidate_score_computation"])
        self.assertTrue(design["forbidden"]["production_change"])


if __name__ == "__main__":
    unittest.main()
