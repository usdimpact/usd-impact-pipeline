"""Issue #258 v16 owner-option-A methodological closure: OFFLINE only.

No BLS GET/HEAD/Range, no PDFs, no source response, no Score/Production write.
A v15 unselected decision remains historically true; v16 records the NEW
dated owner choice without backdating or granting runtime/publication rights.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.score_v2_1f_wpu0561_v16_option_a_guard import (
    ROOT, V16, V15_DESIGN, MANIFEST, V16_RECEIPT, V16_DISPATCH,
    V16_WORKFLOW, validate_owner_option_a,
)
from scripts.score_v2_1f_wpu0561_pdf_v14_offline_diagnostics import (
    DESIGN as V14_DESIGN, LEDGER, CONTRACT, RIGHTS, WORKFLOW,
    V13_RECEIPT, V13_DISPATCH,
)


class OwnerOptionAClosureTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="wpu0561-v16-owner-choice-offline-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        for relative in (
            V16, V15_DESIGN, V14_DESIGN, MANIFEST,
            LEDGER, CONTRACT, RIGHTS, WORKFLOW,
            Path("scripts/score_v2_1f_wpu0561_pdf_v13_parser.py"),
        ):
            dest = self.root / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, dest)

    def update(self, path, editor):
        file = self.root / path
        data = json.loads(file.read_text(encoding="utf-8"))
        editor(data)
        file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def assert_closed(self, reason):
        with self.assertRaisesRegex(RuntimeError, reason):
            validate_owner_option_a(self.root)

    def test_owner_approved_A_no_new_runtime_source(self):
        r = validate_owner_option_a(self.root)
        self.assertEqual(r["status"], "passed")
        self.assertEqual(r["decision"], "A")
        self.assertEqual(r["requests_remaining"], 0)
        self.assertEqual(r["new_BLS_requests"], 0)
        self.assertFalse(r["fixed_pair_index_level_feasible"])
        self.assertTrue(r["commodity_identifier_0561_preserved"])
        self.assertTrue(r["v15_original_choice_record_unchanged"])
        self.assertFalse(r["original_release_pdf_evidence_proven"])
        self.assertFalse(r["historical_score_observation_created"])
        self.assertFalse(r["production_changed"])
        self.assertEqual(r["rights_155"], "hold")

    def test_v15_at_historical_point_remains_unselected(self):
        data = json.loads((self.root / V15_DESIGN).read_text())
        self.assertEqual(data["version"], 15)
        self.assertTrue(all(not d["owner_chosen_now"] for d in data["decisions"].values()))
        self.assertTrue(validate_owner_option_a(self.root)["v15_original_choice_record_unchanged"])

    def test_old_v15_historical_file_tamper_rejected(self):
        self.update(V15_DESIGN, lambda d: d.update(silent_revision="new owner choice"))
        self.assert_closed("historical_v15_choice_record_rewritten")

    def test_v16_wrong_record_date_rejected(self):
        self.update(V16, lambda d: d.update(recorded_date="2026-10-28"))
        self.assert_closed("owner_option_a_decision_not_valid")

    def test_v16_wrong_decision_state_rejected(self):
        self.update(V16, lambda d: d.update(state="active_source_authorization"))
        self.assert_closed("owner_option_a_decision_not_valid")

    def test_choice_A_cannot_be_replaced_with_B(self):
        self.update(V16, lambda d: d["owner_attestation"].update(option="B"))
        self.assert_closed("option_a_not_separately_attested")

    def test_choice_A_cannot_be_backdated(self):
        self.update(V16, lambda d: d["owner_attestation"].update(no_prior_approval_backdated=False))
        self.assert_closed("option_a_not_separately_attested")

    def test_choice_A_does_not_imply_new_BLS_approval(self):
        self.update(V16, lambda d: d["owner_attestation"].update(new_BLS_or_publication_approval_inferred=True))
        self.assert_closed("option_a_not_separately_attested")

    def test_reject_future_live_approval_implication(self):
        self.update(V16, lambda d: d["path_B_future_only"].update(status="approved"))
        self.assert_closed("new_source_research_not_independently_gated")

    def test_future_B_cannot_reuse_v13_authorization(self):
        self.update(V16, lambda d: d["path_B_future_only"].update(does_not_inherit_v8_or_v13_consumed_receipt=False))
        self.assert_closed("new_source_research_not_independently_gated")

    def test_future_B_requires_new_authorization(self):
        self.update(V16, lambda d: d["path_B_future_only"].update(requires_new_owner_methodology_and_one_off_authorization=False))
        self.assert_closed("new_source_research_not_independently_gated")

    def test_choice_C_not_selected(self):
        self.update(V16, lambda d: d.update(path_C_not_selected=False))
        self.assert_closed("new_source_research_not_independently_gated")

    def test_option_A_must_be_chosen(self):
        self.update(V16, lambda d: d["option_A"].update(chosen=False))
        self.assert_closed("option_a_scope_or_infeasibility_broadened")

    def test_eligible_historical_pair_cannot_be_fabricated(self):
        self.update(V16, lambda d: d["option_A"].update(new_historical_WPU0561_pair_admissible=True))
        self.assert_closed("option_a_scope_or_infeasibility_broadened")

    def test_scope_must_not_be_all_BLS_or_live_Score(self):
        self.update(V16, lambda d: d["option_A"].update(scope="No WPU0561 anywhere"))
        self.assert_closed("option_a_scope_or_infeasibility_broadened")

    def test_identifier_proof_cannot_be_lost(self):
        self.update(V16, lambda d: d["option_A"].update(Crude_petroleum_identifier_0561_proof_preserved=False))
        self.assert_closed("option_a_scope_or_infeasibility_broadened")

    def test_no_live_score_driver_removal(self):
        self.update(V16, lambda d: d["option_A"].update(authorizes_removing_live_score_driver=True))
        self.assert_closed("option_a_scope_incorrectly_expanded")

    def test_no_score_formula_change(self):
        self.update(V16, lambda d: d["option_A"].update(authorizes_new_score_formula=True))
        self.assert_closed("option_a_scope_incorrectly_expanded")

    def test_no_source_substitution(self):
        self.update(V16, lambda d: d["option_A"].update(authorizes_source_substitution=True))
        self.assert_closed("option_a_scope_incorrectly_expanded")

    def test_no_WPU0561_publication(self):
        self.update(V16, lambda d: d["option_A"].update(authorizes_publishing_WPU0561_observation=True))
        self.assert_closed("option_a_scope_incorrectly_expanded")

    def test_2026_index_level_header_not_invented(self):
        self.update(V16, lambda d: d["unchanged_evidence"].update(
            v9_2026_selected_XLSX_index_level_header_present=True))
        self.assert_closed("v9_original_fixed_resource_proof_changed")

    def test_selected_2026_sheet_not_substituted(self):
        self.update(V16, lambda d: d["unchanged_evidence"].update(
            v9_2026_selected_XLSX_container="xl/worksheets/sheet1.xml"))
        self.assert_closed("v9_original_fixed_resource_proof_changed")

    def test_2013_role_unchanged(self):
        self.update(V16, lambda d: d["unchanged_evidence"].update(
            v9_2013_HTML_structurally_supports_unadjusted_index_role=False))
        self.assert_closed("v9_original_fixed_resource_proof_changed")

    def test_2026_percent_change_header_preserved(self):
        self.update(V16, lambda d: d["unchanged_evidence"].update(
            v9_2026_selected_XLSX_percent_change_header_present=False))
        self.assert_closed("v9_original_fixed_resource_proof_changed")

    def test_unknown_pdf_page_count_not_guessed(self):
        self.update(V16, lambda d: d["unchanged_evidence"].update(v13_actual_PDF_page_count=201))
        self.assert_closed("v13_non_economic_result_promoted")

    def test_pdf_first_edition_not_claimed(self):
        self.update(V16, lambda d: d["unchanged_evidence"].update(
            v13_original_release_PDF_vintage_proven=True))
        self.assert_closed("v13_non_economic_result_promoted")

    def test_pdf_index_level_not_claimed(self):
        self.update(V16, lambda d: d["unchanged_evidence"].update(
            v13_Table9_WPU0561_index_level_proven=True))
        self.assert_closed("v13_non_economic_result_promoted")

    def test_consumed_claim_is_not_repointed(self):
        self.update(V16, lambda d: d["unchanged_evidence"].update(v13_claim_target="b" * 40))
        self.assert_closed("historical_v15_or_v13_provenance_modified")

    def test_rights_issue_155_not_released(self):
        self.update(V16, lambda d: d["research_disposition"].update(
            no_automatic_public_rights_clearance=False))
        self.assert_closed("rights_or_scope_wrongly_released")

    def test_public_score_unchanged(self):
        self.update(V16, lambda d: d["runtime_boundary"].update(
            existing_public_score_artifacts_untouched=False))
        self.assert_closed("runtime_data_or_production_boundary_undermined")

    def test_omitted_BLS_GET_permission_cannot_silently_default_true(self):
        self.update(V16, lambda d: d["permissions"].pop("BLS_GET"))
        self.assert_closed("new_live_authorization_inserted")

    def test_unrecognized_runtime_status_field_is_not_silently_allowed(self):
        self.update(V16, lambda d: d["runtime_boundary"].update(
            unreviewed_external_provider_write=True))
        self.assert_closed("runtime_data_or_production_boundary_undermined")

    def test_no_BLS_GET(self):
        self.update(V16, lambda d: d["permissions"].update(BLS_GET=True))
        self.assert_closed("new_live_authorization_inserted")

    def test_no_BLS_HEAD(self):
        self.update(V16, lambda d: d["permissions"].update(BLS_HEAD=True))
        self.assert_closed("new_live_authorization_inserted")

    def test_no_economic_value_read(self):
        self.update(V16, lambda d: d["permissions"].update(economic_value_read=True))
        self.assert_closed("new_live_authorization_inserted")

    def test_no_historical_reconstruction(self):
        self.update(V16, lambda d: d["permissions"].update(historical_reconstruction=True))
        self.assert_closed("new_live_authorization_inserted")

    def test_no_public_artifact_writes(self):
        self.update(V16, lambda d: d["permissions"].update(public_artifact_write=True))
        self.assert_closed("new_live_authorization_inserted")

    def test_no_production_writes(self):
        self.update(V16, lambda d: d["permissions"].update(production_change=True))
        self.assert_closed("new_live_authorization_inserted")

    def test_no_v16_live_receipt(self):
        f = self.root / V16_RECEIPT
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("{}", encoding="utf-8")
        self.assert_closed("v16_live_receipt_dispatch_or_workflow_present")

    def test_no_v16_live_dispatch(self):
        f = self.root / V16_DISPATCH
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("{}", encoding="utf-8")
        self.assert_closed("v16_live_receipt_dispatch_or_workflow_present")

    def test_no_v16_live_workflow(self):
        f = self.root / V16_WORKFLOW
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("name: forbidden\n", encoding="utf-8")
        self.assert_closed("v16_live_receipt_dispatch_or_workflow_present")

    def test_no_new_request_budget_in_recovery_manifest(self):
        self.update(MANIFEST, lambda d: d["v16"].update(request_budget_remaining=1))
        self.assert_closed("recovery_manifest_not_option_a_only")

    def test_manifest_rights_hold_cannot_be_cleared(self):
        self.update(MANIFEST, lambda d: d["v16"].update(rights_issue_155_hold=False))
        self.assert_closed("recovery_manifest_not_option_a_only")

    def test_manifest_does_not_change_to_B(self):
        self.update(MANIFEST, lambda d: d["v16"].update(chosen_option="B"))
        self.assert_closed("recovery_manifest_not_option_a_only")

    def test_v13_consumption_cannot_be_reactivated(self):
        self.update(CONTRACT, lambda d: d.update(request_budget_remaining_now=1))
        self.assert_closed("v13_budget_reactivated")


if __name__ == "__main__":
    unittest.main()
