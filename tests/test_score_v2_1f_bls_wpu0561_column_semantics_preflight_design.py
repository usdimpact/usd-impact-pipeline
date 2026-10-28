from __future__ import annotations
import unittest
from pathlib import Path
from scripts import validate_score_v2_1f_bls_wpu0561_column_semantics_preflight as validator

ROOT = Path(__file__).resolve().parents[1]

class ScoreV21FWpu0561ColumnSemanticsDispatchTests(unittest.TestCase):
    def test_packet_is_dispatched_but_narrow(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "column_semantics_preflight_authorized")
        self.assertEqual(report["activation_merge_commit"], "474770a01b5493537731697f804e88b4e849d41d")
        self.assertEqual(report["request_budget"], 2)
        self.assertTrue(report["active_receipt_present"])
        self.assertTrue(report["dispatch_present"])
        self.assertTrue(report["response_body_ephemeral_retrieval_authorized"])
        self.assertTrue(report["column_semantics_preflight_authorized"])
        self.assertTrue(report["numeric_identifier_field_read_authorized"])
        self.assertFalse(report["economic_value_extraction_authorized"])
        self.assertFalse(report["candidate_score_computation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

if __name__ == "__main__":
    unittest.main()
