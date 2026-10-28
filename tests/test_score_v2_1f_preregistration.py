from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import rehearse_score_v2_1f_preregistration as rehearsal
from scripts import validate_score_v2_1f_preregistration as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FPreregistrationTests(unittest.TestCase):
    def test_protocol_is_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "preregistered_design_only")
        self.assertEqual(report["slot_count"], 5)
        self.assertTrue(report["exact_series_pinned"])
        self.assertTrue(report["h15_removed"])
        self.assertTrue(report["vintage_rules_frozen"])
        self.assertTrue(report["thresholds_frozen_before_results"])
        self.assertTrue(report["point_in_time_normalization"])
        self.assertFalse(report["live_vintage_preflight_authorized"])
        self.assertFalse(report["full_candidate_research_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_synthetic_rehearsal_preserves_point_in_time_rules(self) -> None:
        report = rehearsal.rehearse()
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["synthetic_only"])
        self.assertFalse(report["real_data_accessed"])
        self.assertEqual(report["slot_count"], 5)
        self.assertFalse(report["h15_present"])
        self.assertTrue(report["all_release_times_within_cutoff"])
        self.assertTrue(report["bls_initial_vintage_preserved_before_revision"])
        self.assertTrue(report["h8_original_vintage_preserved_before_correction"])
        self.assertTrue(report["current_week_excluded_from_own_normalization"])
        self.assertEqual(report["minimum_prior_complete_weeks"], 104)
        self.assertEqual(report["first_score_history_count"], 104)
        self.assertLess(report["first_score_history_end"], report["first_score_week"])
        self.assertAlmostEqual(report["absolute_weight_sum"], 1.0)
        self.assertFalse(report["live_vintage_preflight_authorized"])
        self.assertFalse(report["full_candidate_research_authorized"])
        self.assertFalse(report["production_authorized"])

    def test_live_preflight_requires_separate_owner_gate(self) -> None:
        protocol = json.loads(
            (ROOT / "governance/score-v2-1f-preregistration.json").read_text(encoding="utf-8")
        )
        preflight = protocol["execution_preconditions_before_any_live_vintage_preflight"]
        self.assertIn(
            "separate explicit owner authorization limited to live vintage feasibility only",
            preflight,
        )
        self.assertIn("no candidate Score computation", preflight)
        self.assertFalse(protocol["authorizations"]["live_vintage_preflight"])

    def test_full_research_requires_second_separate_owner_gate(self) -> None:
        protocol = json.loads(
            (ROOT / "governance/score-v2-1f-preregistration.json").read_text(encoding="utf-8")
        )
        full = protocol["additional_preconditions_before_full_candidate_research"]
        self.assertIn(
            "live BLS WPU0561 historical archive/vintage feasibility passes",
            full,
        )
        self.assertIn(
            "a second separate explicit owner authorization permits full v2.1F candidate research",
            full,
        )
        self.assertFalse(protocol["authorizations"]["real_data_research"])
        self.assertFalse(protocol["authorizations"]["candidate_score_computation"])

    def test_h15_and_rate_proxies_are_frozen_out(self) -> None:
        protocol = json.loads(
            (ROOT / "governance/score-v2-1f-preregistration.json").read_text(encoding="utf-8")
        )
        active = json.dumps(protocol["source_rules"]).lower()
        for forbidden in ("h15/", "riflgfcy", "fred", "alfred", "wayback"):
            self.assertNotIn(forbidden, active)
        self.assertFalse(protocol["hard_acceptance_gates"]["h15_or_rate_proxy_used"])

    def test_regime_bands_are_carried_forward_before_results(self) -> None:
        protocol = json.loads(
            (ROOT / "governance/score-v2-1f-preregistration.json").read_text(encoding="utf-8")
        )
        score = protocol["score"]
        self.assertEqual(
            score["regime_bands_status"],
            "frozen_for_first_v2_1f_candidate_research_only",
        )
        self.assertIn("not empirically re-fit", score["regime_band_derivation"])


if __name__ == "__main__":
    unittest.main()
