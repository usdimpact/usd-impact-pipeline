import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_JSON = ROOT / "research/score_v3_preregistration.json"
PROTOCOL_MD = ROOT / "research/score_v3_preregistration.md"


class ScoreV3PreregistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL_JSON.read_text(encoding="utf-8"))
        cls.markdown = PROTOCOL_MD.read_text(encoding="utf-8")

    def test_protocol_is_research_only_and_non_predictive(self):
        self.assertFalse(self.protocol["production_change"])
        self.assertFalse(self.protocol["production_methodology_affected"])
        self.assertFalse(self.protocol["predictive_claim"])
        self.assertFalse(self.protocol["trading_strategy_claim"])
        self.assertEqual(self.protocol["baseline_methodology"], "usd_impact_score_v2")
        self.assertEqual(self.protocol["research_status"], "preregistered_not_started")

    def test_knowledge_boundary_is_explicit_and_future_holdout_is_untouched(self):
        boundary = self.protocol["knowledge_boundary"]
        self.assertEqual(
            boundary["latest_observation_already_seen_at_registration"], "2026-08-21"
        )
        self.assertTrue(
            boundary["all_data_through_registration_cutoff_are_retrospective_design_information"]
        )
        self.assertEqual(boundary["prospective_untouched_holdout_start"], "2026-08-28")
        self.assertEqual(boundary["minimum_prospective_completed_weeks_before_selection"], 52)
        self.assertFalse(boundary["interim_reporting_may_change_candidate_formulas"])
        self.assertFalse(boundary["interim_reporting_may_select_a_winner"])

    def test_candidate_set_is_fixed_and_all_candidates_exclude_future_data(self):
        candidates = self.protocol["candidates"]
        self.assertEqual(
            [candidate["candidate_id"] for candidate in candidates],
            ["V3_E52", "V3_R260", "V3_MAD260", "V3_GRP_MAD260"],
        )
        for candidate in candidates:
            self.assertFalse(candidate["uses_future_data"])
            self.assertFalse(candidate["estimated_parameters_from_target"])
            weights = candidate["weights"].copy()
            weights.pop("type")
            self.assertAlmostEqual(
                sum(abs(float(weight)) for weight in weights.values()), 1.0, places=12
            )

    def test_primary_thresholds_are_fixed_and_not_optimizable(self):
        self.assertFalse(self.protocol["common_rules"]["regime_thresholds_may_be_optimized"])
        bands = self.protocol["fixed_regime_thresholds_for_primary_comparison"]
        self.assertEqual(len(bands), 5)
        self.assertEqual(bands[0]["low"], 1.0)
        self.assertIsNone(bands[0]["high"])
        self.assertIsNone(bands[-1]["low"])
        self.assertEqual(bands[-1]["high"], -1.0)
        self.assertFalse(self.protocol["threshold_sensitivity_only"]["may_select_new_thresholds"])

    def test_selection_rule_permits_no_change_outcome(self):
        rule = self.protocol["selection_rule_after_52_weeks"]
        self.assertTrue(rule["no_composite_optimized_score"])
        self.assertIn("Keep v2 in production", rule["no_eligible_candidate_result"])
        self.assertIn("10%", rule["step_2"])
        self.assertIn("V3_E52", rule["step_5"])
        self.assertIn("V3_GRP_MAD260", rule["step_5"])

    def test_prospective_evaluation_uses_as_published_weekly_artifacts(self):
        contract = self.protocol["data_contract"]
        self.assertIn("immutable as-published weekly input/reproduction artifacts", contract["prospective_holdout_source"])
        self.assertIn("freeze and hash", contract["historical_snapshot_requirement"])

    def test_predictive_study_requires_separate_preregistration(self):
        requirement = self.protocol["separate_predictive_study_requirement"]
        for term in ("target", "forecast horizon", "loss/score metric", "untouched test period"):
            self.assertIn(term, requirement)

    def test_markdown_contains_non_negotiable_boundaries(self):
        required_phrases = (
            "Production change authorized by this document: **No**",
            "First prospective untouched week: August 28, 2026",
            "52 completed prospective weeks",
            "keep v2 in production",
            "not be described as an untouched out-of-sample test",
            "does **not** automatically become production Score v3",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.markdown)


if __name__ == "__main__":
    unittest.main()
