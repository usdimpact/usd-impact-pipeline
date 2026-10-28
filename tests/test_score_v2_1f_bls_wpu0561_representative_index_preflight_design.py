from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1f_bls_wpu0561_representative_index_preflight as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FWpu0561RepresentativeIndexDesignTests(unittest.TestCase):
    def test_packet_is_design_only_and_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "design_only_hold")
        self.assertEqual(
            report["issue"],
            "https://github.com/usdimpact/usd-impact-pipeline/issues/252",
        )
        self.assertEqual(report["request_budget"], 2)
        self.assertEqual(report["max_observations_total"], 2)
        self.assertEqual(report["max_observations_per_resource"], 1)
        self.assertFalse(report["active_receipt_present"])
        self.assertFalse(report["dispatch_present"])
        self.assertFalse(report["response_body_ephemeral_retrieval_authorized"])
        self.assertFalse(report["representative_index_value_read_authorized"])
        self.assertFalse(report["representative_index_preflight_authorized"])
        self.assertFalse(report["candidate_score_computation_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_design_allows_only_original_release_index_level(self) -> None:
        design = json.loads(
            (
                ROOT
                / "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-design.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            design["field_semantics_policy"]["allowed"],
            ["original_release_index_level"],
        )
        self.assertTrue(
            design["field_semantics_policy"]["multiple_index_level_candidates_fail_closed"]
        )
        self.assertTrue(
            design["field_semantics_policy"]["ambiguous_revision_context_fails_closed"]
        )
        self.assertEqual(
            design["field_semantics_policy"]["release_context_policy"]["missing_or_conflicting_context"],
            "fail_closed_no_value",
        )
        self.assertEqual(design["future_live_budget"]["request_budget"], 2)
        self.assertEqual(
            design["future_live_budget"]["max_economic_observations_total"], 2
        )
        self.assertEqual(
            design["future_live_budget"]["max_economic_observations_per_resource"], 1
        )
        self.assertFalse(any(design["current_authorizations"].values()))


if __name__ == "__main__":
    unittest.main()
