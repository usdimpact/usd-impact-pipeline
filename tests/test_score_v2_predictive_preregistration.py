from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "research/score_v2_predictive_preregistration.json"
SCHEMA_PATH = ROOT / "research/score_v2_predictive_preregistration.schema.json"
DOC_PATH = ROOT / "docs/score-v2-predictive-preregistration.md"


class ScoreV2PredictivePreregistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.doc = DOC_PATH.read_text(encoding="utf-8")

    def test_closed_top_level_contract_matches_schema(self) -> None:
        required = set(self.schema["required"])
        self.assertEqual(set(self.protocol), required)
        self.assertEqual(set(self.schema["properties"]), required)
        self.assertIs(self.schema["additionalProperties"], False)

    def test_registered_before_untouched_holdout_without_current_claim(self) -> None:
        self.assertEqual(self.protocol["registered_date"], "2026-08-25")
        boundary = self.protocol["knowledge_boundary"]
        self.assertEqual(boundary["latest_observation_seen_at_registration"], "2026-08-21")
        self.assertEqual(boundary["first_untouched_prediction_origin"], "2026-08-28")
        self.assertEqual(boundary["required_resolved_predictions"], 52)
        self.assertIs(
            boundary["all_data_through_latest_observation_are_retrospective_design_information"],
            True,
        )
        self.assertIs(boundary["score_v2_and_prediction_rule_were_selected_before_untouched_holdout"], True)
        self.assertIs(boundary["pre_holdout_results_are_untouched_test_evidence"], False)
        self.assertIs(boundary["post_holdout_rule_change_allowed"], False)
        self.assertIs(self.protocol["current_predictive_claim_authorized"], False)
        self.assertIs(self.protocol["production_change"], False)

    def test_target_rule_has_no_abstention_or_posthoc_threshold(self) -> None:
        predictor = self.protocol["predictor"]
        target = self.protocol["target"]
        integrity = self.protocol["sample_integrity"]
        self.assertEqual(
            predictor["prediction_rule"],
            "predict DXY up when score >= 0; predict DXY down when score < 0",
        )
        self.assertIs(predictor["abstention_allowed"], False)
        self.assertIs(predictor["threshold_optimization_allowed"], False)
        self.assertEqual(
            target["horizon"],
            "one completed Friday to the immediately following completed Friday",
        )
        self.assertIs(target["later_provider_recalculation_allowed"], False)
        self.assertIs(integrity["missed_origin_may_be_backfilled_after_outcome"], False)
        self.assertIs(integrity["driver_or_regime_based_exclusions_allowed"], False)

    def test_confirmatory_rule_is_frozen_and_requires_benchmark_lift(self) -> None:
        endpoint = self.protocol["primary_endpoint"]
        rule = self.protocol["meaningful_predictive_evidence_rule"]
        self.assertEqual(endpoint["significance_threshold"], 0.05)
        self.assertIn("all 51 non-zero circular shifts", endpoint["circular_shift_rule"])
        conditions = " ".join(rule["conditions"])
        self.assertIn("accuracy is at least 0.60", conditions)
        self.assertIn("better of always-up and one-week DXY momentum", conditions)
        self.assertIn("at least 0.05", conditions)

    def test_interim_reporting_cannot_peek_or_select(self) -> None:
        reporting = self.protocol["reporting_policy"]
        self.assertEqual(
            reporting["integrity_checkpoints_after_resolved_predictions"],
            [13, 26, 39],
        )
        self.assertIs(reporting["interim_performance_values_may_be_published"], False)
        self.assertIs(reporting["interim_accept_or_reject_decision_allowed"], False)
        self.assertIs(reporting["automatic_site_predictive_claim_allowed"], False)

    def test_human_document_preserves_claim_boundary(self) -> None:
        for phrase in (
            "Current status: preregistered, not started, no predictive claim authorized",
            "That earlier information is design evidence, not part of the untouched predictive test.",
            "No abstentions",
            "52 consecutive resolved predictions",
            "It would not establish causal power, trading profitability",
        ):
            self.assertIn(phrase, self.doc)


if __name__ == "__main__":
    unittest.main()
