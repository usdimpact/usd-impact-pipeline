"""Offline synthetic tests for one BLS PDF source-boundary proposal (never real data)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.validate_score_v2_1f_wpu0561_pdf_v11 import (
    DESIGN, ROOT, classify_synthetic_layout, synthetic_example, validate_design,
)


class V11DesignContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="score-pdf-v11-design-only-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        dest = self.root / DESIGN
        dest.parent.mkdir(parents=True)
        dest.write_bytes((ROOT / DESIGN).read_bytes())

    def mutate(self, operation) -> None:
        path = self.root / DESIGN
        doc = json.loads(path.read_text(encoding="utf-8"))
        operation(doc)
        path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    def test_unmodified_v11_inert_contract_passes(self) -> None:
        result = validate_design(self.root)
        self.assertEqual(result["state"], "draft_pre_registration_hold")
        self.assertFalse(result["pdf_fetched"])
        self.assertFalse(result["economic_read_authorized"])

    def test_cannot_enable_pdf_download(self) -> None:
        self.mutate(lambda d: d["current_execution_authorization"].update(pdf_download=True))
        with self.assertRaisesRegex(RuntimeError, "execution authorization"):
            validate_design(self.root)

    def test_cannot_mark_source_eligible(self) -> None:
        self.mutate(lambda d: d["source_candidate"].update(eligible_for_adoption=True))
        with self.assertRaisesRegex(RuntimeError, "unauthorized PDF"):
            validate_design(self.root)

    def test_cannot_mark_revision_proven(self) -> None:
        self.mutate(lambda d: d["source_candidate"].update(first_publication_pdf_vintage_proven=True))
        with self.assertRaisesRegex(RuntimeError, "unauthorized PDF"):
            validate_design(self.root)

    def test_cannot_adopt_domestic_production_variant(self) -> None:
        self.mutate(lambda d: d["source_candidate"].update(domestic_production_alias_approved=True))
        with self.assertRaisesRegex(RuntimeError, "unauthorized PDF"):
            validate_design(self.root)

    def test_cannot_increase_one_get_budget(self) -> None:
        self.mutate(lambda d: d["preflight_plan_if_separately_approved"].update(potential_max_requests=2))
        with self.assertRaisesRegex(RuntimeError, "one-request GET"):
            validate_design(self.root)

    def test_cannot_change_pdf_host(self) -> None:
        self.mutate(lambda d: d["source_candidate"].update(canonical_hostname="example.com"))
        with self.assertRaisesRegex(RuntimeError, "host/protocol"):
            validate_design(self.root)

    def test_cannot_add_parser_until_review(self) -> None:
        self.mutate(lambda d: d["preflight_plan_if_separately_approved"].update(parser_dependency_lock="pdf-lib@latest"))
        with self.assertRaisesRegex(RuntimeError, "parser not yet reviewed"):
            validate_design(self.root)

    def test_cannot_activate_consumed_receipt(self) -> None:
        self.mutate(lambda d: d["preflight_plan_if_separately_approved"].update(request_execution_receipt_exists=True))
        with self.assertRaisesRegex(RuntimeError, "unsafe preflight activation"):
            validate_design(self.root)

    def test_cannot_supersede_v9_contract(self) -> None:
        self.mutate(lambda d: d.update(authoritative_methodology_design_version=11))
        with self.assertRaisesRegex(RuntimeError, "authoritative v9"):
            validate_design(self.root)

    def test_cannot_set_economic_persistence_to_one(self) -> None:
        self.mutate(lambda d: d["preflight_plan_if_separately_approved"].update(max_retained_economic_cells=1))
        with self.assertRaisesRegex(RuntimeError, "numeric persistence"):
            validate_design(self.root)


class V11SyntheticLayoutTests(unittest.TestCase):
    def assert_hold(self, **updates) -> list[str]:
        sample = synthetic_example()
        sample.update(updates)
        result = classify_synthetic_layout(sample)
        self.assertEqual(result["status"], "hold", msg=result)
        self.assertFalse(result["live_approval"])
        self.assertFalse(result["source_adopted"])
        self.assertFalse(result["economic_value_read"])
        return result["reasons"]

    def test_nominal_synthetic_only_never_grants_live_access(self) -> None:
        result = classify_synthetic_layout(synthetic_example())
        self.assertEqual(result["status"], "synthetic_layout_compatible_not_authorized")
        self.assertEqual(result["reasons"], [])
        self.assertFalse(result["live_approval"])
        self.assertFalse(result["source_adopted"])

    def test_source_substitution_fails(self) -> None:
        self.assertIn("source_mismatch", self.assert_hold(source_url="https://fred.stlouisfed.org/series/WPU0561"))

    def test_wrong_edition_fails(self) -> None:
        self.assertIn("edition_unverified", self.assert_hold(document_vintage_status="unknown"))

    def test_wrong_month_fails(self) -> None:
        self.assertIn("target_month_mismatch", self.assert_hold(reference_month="2026-05"))

    def test_missing_index_role_fails(self) -> None:
        self.assertIn("missing_ambiguous_or_unsupported_governing_header", self.assert_hold(
            governing_header_roles=["commodity_identity", "percent_change"],
        ))

    def test_duplicate_index_role_fails(self) -> None:
        self.assertIn("missing_ambiguous_or_unsupported_governing_header", self.assert_hold(
            governing_header_roles=["commodity_identity", "unadjusted_index_level", "unadjusted_index_level"],
        ))

    def test_multiple_matching_rows_fail(self) -> None:
        self.assertIn("candidate_count_not_unique", self.assert_hold(direct_commodity_candidate_count=2))

    def test_footnote_and_stage_context_fail(self) -> None:
        self.assertIn("not_direct_commodity", self.assert_hold(concept_scope="stage_intermediate_demand"))

    def test_domestic_production_label_requires_owner_decision(self) -> None:
        self.assertIn("concept_label_not_exact", self.assert_hold(concept_label="Crude Petroleum (Domestic Production)"))

    def test_extraction_label_requires_owner_decision(self) -> None:
        self.assertIn("concept_label_not_exact", self.assert_hold(concept_label="Crude petroleum extraction"))

    def test_wrong_table_title_fails(self) -> None:
        self.assertIn("wrong_table_title", self.assert_hold(table_title="Table 1. Percent changes"))

    def test_multiple_table_titles_fail(self) -> None:
        self.assertIn("table_title_ambiguous", self.assert_hold(table_title_count=2))

    def test_no_unique_month_column_fails(self) -> None:
        self.assertIn("observation_column_not_unique", self.assert_hold(target_period_columns=2))

    def test_adjusted_column_fails(self) -> None:
        self.assertIn("not_unadjusted", self.assert_hold(target_adjustment="seasonally_adjusted"))

    def test_basis_unverified_fails(self) -> None:
        self.assertIn("index_basis_not_proven", self.assert_hold(index_basis_status="unknown"))

    def test_revision_unknown_fails(self) -> None:
        self.assertIn("revision_ambiguous", self.assert_hold(revision_status="unknown"))

    def test_claimed_pdf_extraction_fails(self) -> None:
        self.assertIn("not_metadata_only", self.assert_hold(pdf_extracted=True))

    def test_numeric_identifier_fails(self) -> None:
        self.assertIn("numeric_identifier_read_or_unproven", self.assert_hold(identifier_proof="0561"))

    def test_unrequested_economic_field_fails(self) -> None:
        sample = synthetic_example()
        sample["index_level_value"] = 123.45
        result = classify_synthetic_layout(sample)
        self.assertEqual(result["status"], "hold")
        self.assertIn("unexpected_or_missing_fields", result["reasons"])

    def test_non_synthetic_input_fails(self) -> None:
        self.assertIn("non_synthetic_input", self.assert_hold(fixture_kind="live_pdf"))

    def test_non_object_fails(self) -> None:
        result = classify_synthetic_layout("PDF bytes")
        self.assertEqual(result["status"], "hold")
        self.assertIn("not_a_synthetic_metadata_object", result["reasons"])

    def test_boolean_candidate_count_is_not_accepted(self) -> None:
        self.assertIn("candidate_count_not_unique", self.assert_hold(direct_commodity_candidate_count=True))

    def test_synthetic_result_never_includes_values(self) -> None:
        sample = synthetic_example()
        result = classify_synthetic_layout(copy.deepcopy(sample))
        self.assertNotIn("index", result)
        self.assertNotIn("value", result)
        self.assertFalse(result["numeric_identifier_read"])


if __name__ == "__main__":
    unittest.main()
