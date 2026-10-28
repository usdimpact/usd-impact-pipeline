from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import rehearse_score_v2_1e_preregistration as rehearsal
from scripts import validate_score_v2_1e_preregistration as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21EPreregistrationTests(unittest.TestCase):
    def test_protocol_is_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "preregistered_design_only")
        self.assertEqual(report["slot_count"], 8)
        self.assertTrue(report["exact_series_pinned"])
        self.assertTrue(report["vintage_rules_frozen"])
        self.assertTrue(report["thresholds_frozen_before_results"])
        self.assertTrue(report["point_in_time_normalization"])
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_synthetic_rehearsal_preserves_historical_vintages(self) -> None:
        report = rehearsal.rehearse()
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["synthetic_only"])
        self.assertFalse(report["real_data_accessed"])
        self.assertTrue(report["all_release_times_within_cutoff"])
        self.assertTrue(report["bls_initial_vintage_preserved_before_revision"])
        self.assertTrue(report["h8_original_vintage_preserved_before_correction"])
        self.assertTrue(report["current_week_excluded_from_own_normalization"])
        self.assertEqual(report["minimum_prior_complete_weeks"], 104)
        self.assertEqual(report["first_score_history_count"], 104)
        self.assertLess(report["first_score_history_end"], report["first_score_week"])
        self.assertFalse(report["production_authorized"])

    def test_latest_revised_history_fallback_is_forbidden(self) -> None:
        protocol = json.loads(
            (ROOT / "governance/score-v2-1e-preregistration.json")
            .read_text(encoding="utf-8")
        )
        self.assertFalse(protocol["weekly_matrix"]["latest_revised_history_fallback"])
        by_slot = {item["slot"]: item for item in protocol["source_rules"]}
        self.assertEqual(
            by_slot["ENERGY"]["vintage_fallback"],
            "fail_closed_no_candidate_week",
        )
        self.assertEqual(
            by_slot["FIN_CONDITIONS"]["vintage_fallback"],
            "fail_closed_no_candidate_week",
        )

    def test_primary_credit_sparsity_gates_are_predeclared(self) -> None:
        protocol = json.loads(
            (ROOT / "governance/score-v2-1e-preregistration.json")
            .read_text(encoding="utf-8")
        )
        hard = protocol["hard_acceptance_gates"]
        review = protocol["review_gates"]
        self.assertEqual(
            hard["primary_credit_minimum_unique_transformed_values_per_104_weeks"], 5
        )
        self.assertEqual(
            hard["primary_credit_maximum_single_value_share_per_104_weeks"], 0.95
        )
        self.assertEqual(
            review["primary_credit_unique_transformed_values_per_104_weeks_review_below"],
            10,
        )
        self.assertEqual(
            review["primary_credit_single_value_share_review_above"],
            0.80,
        )


if __name__ == "__main__":
    unittest.main()
