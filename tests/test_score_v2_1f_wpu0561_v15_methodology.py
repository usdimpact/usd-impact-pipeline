"""Issue #258 v15 OFFLINE and fully synthetic methodology gate tests.

The real PDF and its URL are NOT opened, requested, parsed or inspected.
Only pre-existing committed governance and enumerated invented scenario names.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.score_v2_1f_wpu0561_v15_methodology_guard import (
    ROOT, DESIGN, V14, MANIFEST, V15_RECEIPT, V15_DISPATCH, V15_LIVE_WORKFLOW,
    _SYNTHETIC_SCENARIOS, classify_invented_case, validate_design_hold,
)
from scripts.score_v2_1f_wpu0561_pdf_v14_offline_diagnostics import (
    DESIGN as V14_DESIGN, LEDGER, CONTRACT, RIGHTS, WORKFLOW,
    V13_RECEIPT, V13_DISPATCH
)


class V15MethodologyHoldTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="wpu0561-v15-invented-only-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        files = (
            DESIGN, V14, MANIFEST,
            LEDGER, CONTRACT, RIGHTS, WORKFLOW,
            Path("scripts/score_v2_1f_wpu0561_pdf_v13_parser.py"),
        )
        for file in files:
            target = self.root / file
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / file, target)

    def change_json(self, path: Path, editor):
        target = self.root / path
        payload = json.loads(target.read_text(encoding="utf-8"))
        editor(payload)
        target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def assert_guard_rejects(self, reason):
        with self.assertRaisesRegex(RuntimeError, reason):
            validate_design_hold(self.root)

    def test_repository_hold_is_present(self):
        x = validate_design_hold(self.root)
        self.assertEqual(x["status"], "passed")
        self.assertEqual(x["stage"], "design_only_methodology_pending_choice")
        self.assertEqual(x["decision_options"], ["A", "B", "C"])
        self.assertFalse(x["owner_choice_made"])
        self.assertEqual(x["v13_request_budget"], 0)
        self.assertFalse(x["v13_actual_page_count_known"])
        self.assertFalse(x["original_release_vintage_proven"])
        self.assertFalse(x["index_level_feasibility_proven"])
        self.assertEqual(x["rights_155"], "hold")
        self.assertEqual(x["BLS_requests_performed_in_v15"], 0)
        self.assertFalse(x["Score_or_Production_changed"])

    def test_historical_v13_remains_consumed_and_v14_cannot_shift(self):
        d = json.loads((self.root / DESIGN).read_text())
        self.assertEqual(
            d["immutable_oneoff_claim"]["target"],
            "82adf0b250871887e82123ed56f641d09fa14ba0",
        )
        self.assertEqual(
            d["authoritative_evidence"]["v13_possible_branches"],
            ["count_lt_1", "count_gt_200"],
        )
        self.assertIsNone(d["authoritative_evidence"]["v13_actual_page_count"])
        self.assertFalse(d["authoritative_evidence"]["v9_original_fixed_pair_feasible"])

    def test_all_invented_cases_refuse_authorization(self):
        self.assertEqual(len(_SYNTHETIC_SCENARIOS), 11)
        for name in _SYNTHETIC_SCENARIOS:
            with self.subTest(name=name):
                out = classify_invented_case(name)
                self.assertIn(out["outcome"], {"hold", "reject", "halt"})
                self.assertEqual(out["scenario_kind"], "synthetic_name_only")
                for forbidden in (
                    "actual_pdf_page_count_observed",
                    "actual_pdf_content_accessed",
                    "first_release_pdf_proven",
                    "real_WPU0561_index_level_proven",
                    "economic_value_retained",
                    "numeric_identifier_retained",
                    "source_approved",
                    "rights_approved",
                    "new_owner_live_authorization",
                    "Score_calculated",
                    "Production_changed",
                ):
                    self.assertIs(out[forbidden], False)

    def test_not_accept_pdf_url_or_arbitrary_input(self):
        invalid = [
            "https://www.bls.gov/ppi/detailed-report/ppi-detailed-report-april-2026.pdf",
            "/tmp/detailed-report.pdf", "201", "index_level: 132.4", "", True, None,
            200, [], {}
        ]
        for item in invalid:
            with self.subTest(value=repr(item)):
                with self.assertRaises(ValueError):
                    classify_invented_case(item)

    def test_future_within_200_is_never_vintage_proof(self):
        d = classify_invented_case("future_within_existing_200")
        self.assertEqual(d["reason_code"], "future_count_only_not_source_proof")
        self.assertFalse(d["first_release_pdf_proven"])
        self.assertFalse(d["source_approved"])

    def test_future_all_private_structure_still_cannot_release(self):
        d = classify_invented_case("future_all_private_structure_but_rights_hold")
        self.assertEqual(d["reason_code"], "future_rights_still_hold")
        self.assertFalse(d["rights_approved"])
        self.assertFalse(d["Score_calculated"])
        self.assertFalse(d["Production_changed"])

    def test_no_current_BLS_HTTP_method_allowed(self):
        self.change_json(DESIGN, lambda d: d["fixed_resource_to_review_only"].update(
            methods_currently_allowed=["HEAD"]))
        self.assert_guard_rejects("source_or_network_boundary_broadened")

    def test_no_different_pdf_source(self):
        self.change_json(DESIGN, lambda d: d["fixed_resource_to_review_only"].update(
            url="https://example.org/other.pdf"))
        self.assert_guard_rejects("source_or_network_boundary_broadened")

    def test_no_future_method_preselected(self):
        self.change_json(DESIGN, lambda d: d["fixed_resource_to_review_only"].update(
            future_method="GET"))
        self.assert_guard_rejects("source_or_network_boundary_broadened")

    def test_no_live_receipt_reintroduced(self):
        (self.root / V15_RECEIPT).write_text("{}\n")
        self.assert_guard_rejects("v15_unapproved_live_artifact_detected")

    def test_no_live_dispatch_reintroduced(self):
        (self.root / V15_DISPATCH).write_text("{}\n")
        self.assert_guard_rejects("v15_unapproved_live_artifact_detected")

    def test_no_live_workflow_reintroduced(self):
        target = self.root / V15_LIVE_WORKFLOW
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("name: should not exist\n")
        self.assert_guard_rejects("v15_unapproved_live_artifact_detected")

    def test_no_BLS_GET_authorization(self):
        self.change_json(DESIGN, lambda d: d["permissions"].update(network_GET_BLS=True))
        self.assert_guard_rejects("v15_permission_not_design_only")

    def test_no_BLS_HEAD_authorization(self):
        self.change_json(DESIGN, lambda d: d["permissions"].update(network_HEAD_BLS=True))
        self.assert_guard_rejects("v15_permission_not_design_only")

    def test_no_BLS_RANGE_authorization(self):
        self.change_json(DESIGN, lambda d: d["permissions"].update(network_RANGE_BLS=True))
        self.assert_guard_rejects("v15_permission_not_design_only")

    def test_no_changed_page_bound(self):
        self.change_json(DESIGN, lambda d: d["permissions"].update(higher_page_limit=True))
        self.assert_guard_rejects("v15_permission_not_design_only")

    def test_no_numeric_identifier_authorization(self):
        self.change_json(DESIGN, lambda d: d["permissions"].update(identifier_value_read=True))
        self.assert_guard_rejects("v15_permission_not_design_only")

    def test_no_economic_observation_authorization(self):
        self.change_json(DESIGN, lambda d: d["permissions"].update(economic_observation_read=True))
        self.assert_guard_rejects("v15_permission_not_design_only")

    def test_no_scoring_authorization(self):
        self.change_json(DESIGN, lambda d: d["permissions"].update(Score_calculation=True))
        self.assert_guard_rejects("v15_permission_not_design_only")

    def test_no_production_authorization(self):
        self.change_json(DESIGN, lambda d: d["permissions"].update(production_change=True))
        self.assert_guard_rejects("v15_permission_not_design_only")

    def test_no_rewriting_original_fixed_resource_conclusion(self):
        self.change_json(DESIGN, lambda d: d["authoritative_evidence"].update(
            v9_original_fixed_pair_feasible=True))
        self.assert_guard_rejects("v9_fixed_resource_conclusion_rewritten")

    def test_no_invented_actual_pdf_page_count(self):
        self.change_json(DESIGN, lambda d: d["authoritative_evidence"].update(
            v13_actual_page_count=201))
        self.assert_guard_rejects("v13_page_count_speculation")

    def test_no_invented_original_release(self):
        self.change_json(DESIGN, lambda d: d["authoritative_evidence"].update(
            v13_original_PDF_edition_immutability_proven=True))
        self.assert_guard_rejects("v13_unobserved_schema_promoted")

    def test_no_invented_table9_index_level(self):
        self.change_json(DESIGN, lambda d: d["authoritative_evidence"].update(
            v13_actual_Table9_unadjusted_level_verified=True))
        self.assert_guard_rejects("v13_unobserved_schema_promoted")

    def test_owner_has_not_chosen_A_implicitly(self):
        self.change_json(DESIGN, lambda d: d["decisions"]["A"].update(owner_chosen_now=True))
        self.assert_guard_rejects("methodology_owner_choice_fabricated")

    def test_owner_has_not_chosen_B_implicitly(self):
        self.change_json(DESIGN, lambda d: d["decisions"]["B"].update(owner_chosen_now=True))
        self.assert_guard_rejects("methodology_owner_choice_fabricated")

    def test_owner_has_not_chosen_C_implicitly(self):
        self.change_json(DESIGN, lambda d: d["decisions"]["C"].update(owner_chosen_now=True))
        self.assert_guard_rejects("methodology_owner_choice_fabricated")

    def test_no_procedural_D2_activation(self):
        self.change_json(DESIGN, lambda d: d["proposed_diagnostic_layers"][2].update(
            status="approved_live"))
        self.assert_guard_rejects("methodology_gate_implicitly_activated")

    def test_no_rights_gate_approval(self):
        self.change_json(DESIGN, lambda d: d["proposed_diagnostic_layers"][5].update(
            status="released"))
        self.assert_guard_rejects("methodology_gate_implicitly_activated")

    def test_no_manifest_live_budget(self):
        self.change_json(MANIFEST, lambda d: d["v15"].update(request_budget=1))
        self.assert_guard_rejects("v15_manifest_contract_broken")

    def test_preserve_v13_claim_ref(self):
        self.change_json(DESIGN, lambda d: d["immutable_oneoff_claim"].update(
            target="a" * 40))
        self.assert_guard_rejects("v13_oneoff_claim_no_longer_preserved")

    def test_v14_offline_guard_remains_enforced(self):
        self.change_json(CONTRACT, lambda d: d.update(request_budget_remaining_now=1))
        self.assert_guard_rejects("v13_budget_reactivated")


if __name__ == "__main__":
    unittest.main()
