from __future__ import annotations
import unittest
from pathlib import Path
from scripts import validate_score_v2_1f_bls_wpu0561_column_semantics_preflight as validator

ROOT = Path(__file__).resolve().parents[1]

class ScoreV21FWpu0561ColumnSemanticsConsumptionTests(unittest.TestCase):
    def test_authorization_is_consumed_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "column_semantics_preflight_consumed_fail_closed")
        self.assertEqual(report["preflight_conclusion"], "success")
        self.assertEqual(report["request_count"], 2)
        self.assertTrue(report["wpu0561_mapping_proven"])
        self.assertEqual(report["normalized_identifier"], "0561")
        self.assertFalse(report["active_receipt_present"])
        self.assertFalse(report["dispatch_present"])
        self.assertFalse(report["response_body_ephemeral_retrieval_authorized"])
        self.assertFalse(report["column_semantics_preflight_authorized"])
        self.assertFalse(report["numeric_identifier_field_read_authorized"])
        self.assertFalse(report["economic_value_extraction_authorized"])
        self.assertFalse(report["candidate_score_computation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

if __name__ == "__main__":
    unittest.main()
