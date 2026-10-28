from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1c_series_receipts as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21CSeriesReceiptsTests(unittest.TestCase):
    def test_receipts_are_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["slot_count"], 8)
        self.assertEqual(report["strong_candidate_count"], 6)
        self.assertEqual(report["conditional_blocked_count"], 2)
        self.assertFalse(report["exact_complete_eight_slot_candidate_rights_ready"])
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_composite_slots_remain_blocked(self) -> None:
        receipt = json.loads(
            (ROOT / "governance/score-v2-1c-series-receipts.json")
            .read_text(encoding="utf-8")
        )
        by_slot = {row["slot"]: row for row in receipt["series_receipts"]}
        self.assertTrue(
            by_slot["FIN_CONDITIONS"]["status"].startswith("conditional_blocked")
        )
        self.assertTrue(
            by_slot["FIN_STRESS"]["status"].startswith("conditional_blocked")
        )
        self.assertIn("Refinitiv", by_slot["FIN_STRESS"]["third_party_input_risk"])

    def test_direct_board_release_timing_is_explicit(self) -> None:
        receipt = json.loads(
            (ROOT / "governance/score-v2-1c-series-receipts.json")
            .read_text(encoding="utf-8")
        )
        by_slot = {row["slot"]: row for row in receipt["series_receipts"]}
        self.assertIn("Monday 16:15", by_slot["USD"]["release_schedule"])
        self.assertIn("Thursday", by_slot["LIQUIDITY"]["release_schedule"])
        self.assertIn("16:15", by_slot["UST_2Y"]["release_schedule"])

    def test_no_source_is_approved(self) -> None:
        receipt = json.loads(
            (ROOT / "governance/score-v2-1c-series-receipts.json")
            .read_text(encoding="utf-8")
        )
        self.assertTrue(receipt["no_source_approved"])
        self.assertFalse(receipt["legal_conclusion"])
        self.assertFalse(receipt["production_authorized"])


if __name__ == "__main__":
    unittest.main()
