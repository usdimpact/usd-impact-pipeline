from __future__ import annotations

import unittest
from pathlib import Path

from scripts import validate_score_v2_1f_bls_wpu0561_row_presence_preflight as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FWpu0561RowPresenceActivationTests(unittest.TestCase):
    def test_packet_is_active_but_pending_dispatch(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "row_presence_preflight_authorized_pending_dispatch")
        self.assertEqual(report["request_budget"], 2)
        self.assertTrue(report["active_receipt_present"])
        self.assertFalse(report["dispatch_present"])
        self.assertTrue(report["row_presence_preflight_authorized"])
        self.assertFalse(report["source_value_extraction_authorized"])
        self.assertFalse(report["candidate_score_computation_authorized"])
        self.assertFalse(report["production_authorized"])


if __name__ == "__main__":
    unittest.main()
