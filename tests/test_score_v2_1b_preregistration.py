from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import rehearse_score_v2_1b_preregistration as rehearsal
from scripts import validate_score_v2_1b_preregistration as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21BPreregistrationTests(unittest.TestCase):
    def test_protocol_is_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "preregistered_design_only")
        self.assertEqual(report["slot_count"], 8)
        self.assertTrue(report["transforms_frozen"])
        self.assertTrue(report["thresholds_frozen_before_results"])
        self.assertTrue(report["point_in_time_normalization"])
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["methodology_activation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_synthetic_rehearsal_excludes_future_releases(self) -> None:
        report = rehearsal.rehearse()
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["synthetic_only"])
        self.assertFalse(report["real_data_accessed"])
        self.assertTrue(report["future_released_nfci_excluded"])
        self.assertTrue(report["all_release_times_within_cutoff"])
        self.assertTrue(report["current_week_excluded_from_own_normalization"])
        self.assertEqual(report["minimum_prior_complete_weeks"], 104)
        self.assertEqual(report["first_score_history_count"], 104)
        self.assertLess(report["first_score_history_end"], report["first_score_week"])
        self.assertFalse(report["production_authorized"])

    def test_walcl_transform_is_frozen_to_13_week_log_change(self) -> None:
        protocol = json.loads(
            (ROOT / "governance/score-v2-1b-preregistration.json")
            .read_text(encoding="utf-8")
        )
        by_slot = {item["slot"]: item for item in protocol["source_rules"]}
        self.assertEqual(by_slot["LIQUIDITY"]["transform"], "log_change_13_weeks")

    def test_no_post_result_threshold_relaxation(self) -> None:
        protocol = json.loads(
            (ROOT / "governance/score-v2-1b-preregistration.json")
            .read_text(encoding="utf-8")
        )
        self.assertTrue(
            protocol["hard_acceptance_gates"]["thresholds_fixed_before_results_visible"]
        )
        rules = "\n".join(protocol["anti_tuning_rules"])
        self.assertIn(
            "No hard acceptance threshold may be relaxed after results are viewed",
            rules,
        )


if __name__ == "__main__":
    unittest.main()
