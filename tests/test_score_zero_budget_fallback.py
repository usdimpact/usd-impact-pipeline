from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from scripts import validate_score_zero_budget_fallback as validator

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class ScoreZeroBudgetFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = (
            read_json("governance/score-zero-budget-fallback-matrix.json"),
            read_json("governance/score-publication-rights-gate.json"),
            read_json("governance/score-spdji-provider-disposition-2026-10-30.json"),
            read_json("governance/independent-macro-context-fallback-draft-2026-10-30.json"),
        )

    def cloned(self) -> list[dict]:
        return [deepcopy(record) for record in self.snapshot]

    def assert_denied(self, records: list[dict]) -> None:
        with self.assertRaises(RuntimeError):
            validator.validate_snapshot(*records)

    def test_current_snapshot_passes_only_as_hold(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["review_only"])
        self.assertTrue(report["zero_budget"])
        self.assertEqual(report["driver_count"], 8)
        self.assertEqual(report["source_permissions_denied"], 56)
        self.assertEqual(report["external_authorities_denied"], 14)
        self.assertFalse(report["publication_authorized"])
        self.assertFalse(report["exact_v2_zero_budget_path_confirmed"])
        self.assertFalse(report["methodology_change_authorized"])
        self.assertFalse(report["real_data_rehearsal_authorized"])
        self.assertFalse(report["production_authorized"])

    def test_sp_paid_license_is_not_free_aggregate_approval(self) -> None:
        matrix, _, provider, _ = self.snapshot
        by_driver = {record["driver"]: record for record in matrix["drivers"]}
        self.assertEqual(by_driver["SPX"]["disposition"], "paid_license_required_no_budget")
        self.assertEqual(by_driver["VIX"]["disposition"], "rights_unresolved_not_zero_budget_safe")
        self.assertTrue(provider["provider_reply"]["paid_license_required_for_described_request"])
        self.assertFalse(provider["provider_reply"]["written_no_fee_aggregate_permission_received"])

    def test_fred_retention_and_legacy_gate_remain_hold(self) -> None:
        matrix, gate, _, _ = self.snapshot
        self.assertEqual(gate["state"], "hold")
        self.assertIsNone(gate["decision_receipt"])
        self.assertFalse(matrix["provider_evidence"]["fred_delivery"]["fred_content_retention_cleared"])
        for d in matrix["drivers"]:
            if d["driver"] in ("UST_2Y", "UST_10Y"):
                self.assertEqual(d["disposition"], "rights_and_retention_unresolved")

    def test_panel_distinct_from_score_and_zero_budget(self) -> None:
        matrix, _, _, panel = self.snapshot
        self.assertEqual(matrix["independent_alternative"]["license_budget_usd"], 0)
        self.assertTrue(matrix["independent_alternative"]["synthetic_only"])
        self.assertFalse(panel["legacy_score_replacement"])
        self.assertTrue(panel["methodology"]["no_composite_score"])
        self.assertEqual(len(panel["source_permissions"]), 4)
        self.assertEqual(len(panel["external_authorities"]), 14)

    def test_score_gate_allow_is_rejected(self) -> None:
        r = self.cloned()
        r[1]["state"] = "allow"
        self.assert_denied(r)

    def test_fake_score_approval_receipt_is_rejected(self) -> None:
        r = self.cloned()
        r[1]["decision_receipt"] = "https://github.com/usdimpact/usd-impact-pipeline/issues/155"
        self.assert_denied(r)

    def test_free_spx_or_aggregate_license_grant_is_rejected(self) -> None:
        r = self.cloned()
        r[0]["drivers"][2]["disposition"] = "rights_unresolved_not_zero_budget_safe"
        self.assert_denied(r)
        r = self.cloned()
        r[2]["provider_reply"]["written_no_fee_aggregate_permission_received"] = True
        self.assert_denied(r)

    def test_sp_provider_paid_requirement_cannot_be_mutated(self) -> None:
        r = self.cloned()
        r[2]["provider_reply"]["paid_license_required_for_described_request"] = False
        self.assert_denied(r)
        r = self.cloned()
        r[0]["provider_evidence"]["s_and_p"]["paid_license_executed"] = True
        self.assert_denied(r)

    def test_fred_delivery_auto_approval_rejected(self) -> None:
        r = self.cloned()
        r[0]["provider_evidence"]["fred_delivery"]["fred_content_retention_cleared"] = True
        self.assert_denied(r)
        r = self.cloned()
        r[0]["drivers"][6]["disposition"] = "retain_if_rights_confirmed"
        self.assert_denied(r)

    def test_semantic_source_equivalence_rejected(self) -> None:
        r = self.cloned()
        r[0]["drivers"][0]["exact_semantic_replacement"] = True
        self.assert_denied(r)

    def test_cannot_convert_panel_to_legacy_score_or_live_source(self) -> None:
        r = self.cloned()
        r[3]["legacy_score_replacement"] = True
        self.assert_denied(r)
        r = self.cloned()
        r[0]["independent_alternative"]["real_data_access_approved"] = True
        self.assert_denied(r)

    def test_any_of_56_panel_source_permissions_granted_or_missing_rejected(self) -> None:
        for source_id in self.snapshot[3]["source_permissions"]:
            for dimension in self.snapshot[3]["permission_dimensions"]:
                with self.subTest(source=source_id, permission=dimension):
                    r = self.cloned()
                    r[3]["source_permissions"][source_id]["rights"][dimension] = True
                    self.assert_denied(r)
                    r = self.cloned()
                    del r[3]["source_permissions"][source_id]["rights"][dimension]
                    self.assert_denied(r)

    def test_each_of_14_external_authorities_rejected(self) -> None:
        for authority in self.snapshot[3]["external_authorities"]:
            with self.subTest(authority=authority):
                r = self.cloned()
                r[3]["external_authorities"][authority] = True
                self.assert_denied(r)

    def test_panel_publication_or_private_release_receipt_rejected(self) -> None:
        r = self.cloned()
        r[3]["publication_control"]["public_release_authorized"] = True
        self.assert_denied(r)
        r = self.cloned()
        r[3]["publication_control"]["owner_release_receipt"] = "unreviewed"
        self.assert_denied(r)

    def test_stale_next_step_or_budget_increase_rejected(self) -> None:
        r = self.cloned()
        r[0]["conclusion"]["next_allowed_step"] = "wait_for_provider_rights_responses_or_prepare_methodology_change_options_only"
        self.assert_denied(r)
        r = self.cloned()
        r[2]["economics"]["authorized_additional_market_data_license_budget_usd"] = 1
        self.assert_denied(r)


if __name__ == "__main__":
    unittest.main()
