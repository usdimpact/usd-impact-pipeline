"""Design-only v14 BLS PDF page-count forensic regression tests.

No BLS HTTP requests, no real PDF input, no provider data and no production
file writes. Unit tests use invented page counts and local governance copies.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from scripts.score_v2_1f_wpu0561_pdf_v14_offline_diagnostics import (
    ROOT, DESIGN, LEDGER, CONTRACT, RIGHTS, WORKFLOW,
    V13_RECEIPT, V13_DISPATCH, V13_CLAIM, PAGE_LIMIT_V13,
    synthetic_count_case, v13_evidence_interpretation,
    validate_consumed_state
)


class V14BoundaryAndGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="score-v14-offline-only-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for relative in (DESIGN, LEDGER, CONTRACT, RIGHTS, WORKFLOW,
                         Path("scripts/score_v2_1f_wpu0561_pdf_v13_parser.py")):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)

    def mutate_json(self, relative: Path, editor) -> None:
        path = self.root / relative
        doc = json.loads(path.read_text(encoding="utf-8"))
        editor(doc)
        path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    def test_existing_consumption_verified_without_live_access(self) -> None:
        out = validate_consumed_state(self.root)
        self.assertEqual(out["status"], "passed")
        self.assertEqual(out["v13_request_budget_remaining"], 0)
        self.assertFalse(out["v13_pdf_exact_pages_known"])
        self.assertFalse(out["live_request_authorized"])
        self.assertFalse(out["new_PDF_request_made"])
        self.assertFalse(out["page_limit_changed"])
        self.assertEqual(out["rights_issue_155"], "hold")

    def test_real_result_is_deliberately_ambiguous(self) -> None:
        out = v13_evidence_interpretation()
        self.assertEqual(out["observed_code"], "invalid_page_count")
        self.assertEqual(len(out["possible_v13_branches"]), 2)
        self.assertFalse(out["exact_branch_identified"])
        self.assertFalse(out["actual_pdf_page_count_known"])
        self.assertFalse(out["table9_observed"])

    def test_zero_synthetic_count_reports_existing_code(self) -> None:
        out = synthetic_count_case(0)
        self.assertEqual(out["branch"], "synthetic_below_minimum")
        self.assertEqual(out["v13_failure_code"], "invalid_page_count")
        self.assertFalse(out["real_pdf_branch_proven"])

    def test_negative_synthetic_count_is_lower_bound(self) -> None:
        self.assertEqual(synthetic_count_case(-1)["branch"], "synthetic_below_minimum")

    def test_existing_lower_accepted_boundary(self) -> None:
        out = synthetic_count_case(1)
        self.assertEqual(out["branch"], "synthetic_within_existing_limit")
        self.assertIsNone(out["v13_failure_code"])

    def test_existing_upper_accepted_boundary(self) -> None:
        out = synthetic_count_case(PAGE_LIMIT_V13)
        self.assertEqual(out["branch"], "synthetic_within_existing_limit")
        self.assertIsNone(out["v13_failure_code"])

    def test_just_above_upper_limit_uses_same_historical_code(self) -> None:
        out = synthetic_count_case(PAGE_LIMIT_V13 + 1)
        self.assertEqual(out["branch"], "synthetic_over_existing_limit")
        self.assertEqual(out["v13_failure_code"], "invalid_page_count")

    def test_huge_invented_count_remains_synthetic_and_holds(self) -> None:
        out = synthetic_count_case(10**8)
        self.assertEqual(out["branch"], "synthetic_over_existing_limit")
        self.assertFalse(out["permission_to_change_page_limit"])
        self.assertFalse(out["permission_to_request_pdf"])

    def test_type_ambiguity_rejected(self) -> None:
        for bad in (None, True, 200.0, "201", [], {"value": 201}):
            with self.subTest(case=type(bad).__name__):
                with self.assertRaises(ValueError):
                    synthetic_count_case(bad)

    def test_existing_page_ceiling_cannot_change(self) -> None:
        self.mutate_json(DESIGN, lambda d: d["exact_root_cause_evidence"].update(max_pages_at_v13=201))
        with self.assertRaisesRegex(RuntimeError, "v14_page_ceiling_changed"):
            validate_consumed_state(self.root)

    def test_cannot_claim_to_know_actual_page_count(self) -> None:
        self.mutate_json(DESIGN, lambda d: d["exact_root_cause_evidence"].update(actual_pdf_page_count=201))
        with self.assertRaisesRegex(RuntimeError, "v14_fabricated_actual_page_count"):
            validate_consumed_state(self.root)

    def test_cannot_claim_real_failure_branch_proven(self) -> None:
        self.mutate_json(DESIGN, lambda d: d["exact_root_cause_evidence"].update(exact_branch_identified=True))
        with self.assertRaisesRegex(RuntimeError, "v14_improper_branch_attribution"):
            validate_consumed_state(self.root)

    def test_original_v13_parser_cannot_be_silently_rewritten(self) -> None:
        path = self.root / "scripts/score_v2_1f_wpu0561_pdf_v13_parser.py"
        path.write_text(path.read_text(encoding="utf-8") + "\n# synthetic tamper\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "v13_original_parser_changed"):
            validate_consumed_state(self.root)

    def test_cannot_enable_pdf_get(self) -> None:
        self.mutate_json(DESIGN, lambda d: d["v14_only_actions"].update(BLS_pdf_GET=True))
        with self.assertRaisesRegex(RuntimeError, "v14_download_authorization_changed"):
            validate_consumed_state(self.root)

    def test_cannot_enable_new_page_limit(self) -> None:
        self.mutate_json(DESIGN, lambda d: d["v14_only_actions"].update(page_cap_increase=True))
        with self.assertRaisesRegex(RuntimeError, "v14_execution_gate_broadened"):
            validate_consumed_state(self.root)

    def test_cannot_reactivate_consumed_budget(self) -> None:
        self.mutate_json(CONTRACT, lambda d: d.update(request_budget_remaining_now=1))
        with self.assertRaisesRegex(RuntimeError, "v13_budget_reactivated"):
            validate_consumed_state(self.root)

    def test_cannot_reenable_workflow(self) -> None:
        file = self.root / WORKFLOW
        file.write_text(file.read_text(encoding="utf-8").replace(
            "if: $" + "{{ false }}", "if: $" + "{{ true }}"
        ), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "v13_workflow_not_inert"):
            validate_consumed_state(self.root)

    def test_cannot_restore_consumed_receipt(self) -> None:
        file = self.root / V13_RECEIPT
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "old_consumed_authorization_or_dispatch_reappeared"):
            validate_consumed_state(self.root)

    def test_cannot_restore_consumed_dispatch(self) -> None:
        file = self.root / V13_DISPATCH
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "old_consumed_authorization_or_dispatch_reappeared"):
            validate_consumed_state(self.root)

    def test_cannot_change_consumed_reason_to_a_page_count_guess(self) -> None:
        self.mutate_json(LEDGER, lambda d: d.update(reason_codes=["over_200_pages"]))
        with self.assertRaisesRegex(RuntimeError, "v13_consumption_reason_changed"):
            validate_consumed_state(self.root)

    def test_cannot_backfill_unobserved_page_count(self) -> None:
        self.mutate_json(LEDGER, lambda d: d.update(pdf_actual_page_count=201))
        with self.assertRaisesRegex(RuntimeError, "v13_page_count_not_publicly_known"):
            validate_consumed_state(self.root)

    def test_cannot_treat_v13_as_original_release_proof(self) -> None:
        self.mutate_json(LEDGER, lambda d: d.update(historical_original_release_vintage_verified=True))
        with self.assertRaisesRegex(RuntimeError, "v13_not_proof_of_original_edition"):
            validate_consumed_state(self.root)

    def test_cannot_claim_rights_approval(self) -> None:
        self.mutate_json(RIGHTS, lambda d: d.update(state="approved"))
        with self.assertRaisesRegex(RuntimeError, "independent_rights_gate_no_longer_hold"):
            validate_consumed_state(self.root)

    def test_cannot_retarget_claim_to_a_new_dispatch(self) -> None:
        self.mutate_json(LEDGER, lambda d: d.update(consumed_claim_commit="a" * 40))
        with self.assertRaisesRegex(RuntimeError, "v13_claim_sha_changed"):
            validate_consumed_state(self.root)

    def test_synthetic_results_never_emit_real_economic_data(self) -> None:
        for n in (0, 1, 199, 200, 201, 250):
            result = synthetic_count_case(n)
            self.assertFalse(result["economic_values_retained"])
            self.assertFalse(result["identifier_values_retained"])
            self.assertFalse(result["source_data_read"])
            self.assertFalse(result["source_pdf_fetched"])
            self.assertFalse(result["score_calculated"])
            self.assertFalse(result["production_changed"])


HAS_PYPDF = importlib.util.find_spec("pypdf") is not None

if HAS_PYPDF:
    from scripts import score_v2_1f_wpu0561_pdf_v13_parser as v13_parser


class SyntheticPages:
    def __init__(self, count: int):
        self.count = count
        self.iterated = False

    def __len__(self) -> int:
        return self.count

    def __iter__(self):
        self.iterated = True
        # Blank fake pages; this creates NO real PDF or source values.
        return iter([SyntheticBlankPage()] * self.count)


class SyntheticBlankPage:
    def get_contents(self):
        return None


class SyntheticTextStream:
    def get_data(self):
        return b"BT (invented synthetic table text) Tj ET"


class SyntheticTextPage:
    def __init__(self, content: str):
        self.content = content

    def get_contents(self):
        return SyntheticTextStream()

    def extract_text(self, extraction_mode="plain"):
        return self.content


class SyntheticTextReader:
    def __init__(self, contents):
        self.pages = [SyntheticTextPage(x) for x in contents]
        self.is_encrypted = False


class SyntheticReader:
    def __init__(self, count: int):
        self.pages = SyntheticPages(count)
        self.is_encrypted = False


@unittest.skipUnless(HAS_PYPDF, "Exact pinned pypdf is installed only in isolated synthetic CI")
class OriginalV13ParserBoundaryTests(unittest.TestCase):
    FAKE_PDF_BYTES = b"%PDF-1.7\nINVENTED PAGE COUNT FIXTURE ONLY\n%%EOF\n"

    def check_injected_count(self, n: int):
        fake = SyntheticReader(n)
        with mock.patch.object(v13_parser, "PdfReader", return_value=fake):
            out = v13_parser.inspect_bytes(self.FAKE_PDF_BYTES)
        self.assertFalse(out["vintage_proven"])
        self.assertFalse(out["economic_values_retained"])
        self.assertFalse(out["identifier_values_retained"])
        return fake, out

    def test_zero_pages_produces_exact_v13_reason_without_scanning(self):
        reader, out = self.check_injected_count(0)
        self.assertEqual(out["reason_codes"], ["invalid_page_count"])
        self.assertEqual(out["page_count_band"], "unknown")
        self.assertFalse(reader.pages.iterated)

    def test_201_pages_produces_identical_v13_reason_without_scanning(self):
        reader, out = self.check_injected_count(201)
        self.assertEqual(out["reason_codes"], ["invalid_page_count"])
        self.assertEqual(out["page_count_band"], "unknown")
        self.assertFalse(reader.pages.iterated)

    def test_one_page_uses_normal_schema_holds_not_page_count_failure(self):
        reader, out = self.check_injected_count(1)
        self.assertTrue(reader.pages.iterated)
        self.assertNotIn("invalid_page_count", out["reason_codes"])
        self.assertEqual(out["page_count_band"], "1_to_50")
        self.assertIn("missing_table9_title", out["reason_codes"])

    def test_200_pages_also_uses_schema_hold_with_no_limit_increase(self):
        reader, out = self.check_injected_count(200)
        self.assertTrue(reader.pages.iterated)
        self.assertNotIn("invalid_page_count", out["reason_codes"])
        self.assertEqual(out["page_count_band"], "51_to_200")
        self.assertIn("missing_table9_title", out["reason_codes"])

    def test_repeated_table9_heading_is_flagged_ambiguous_on_fake_continuation(self):
        page_one = (
            "Table 9. Producer price indexes for commodity and service groupings and individual items\n"
            "Commodity code\nUnadjusted index\nUnprocessed nonfood materials\n"
            "Crude petroleum\n"
        )
        page_two = (
            "Table 9. Producer price indexes for commodity and service groupings and individual items\n"
            "Commodity code\nUnadjusted index\nOther synthetic item\n"
        )
        with mock.patch.object(v13_parser, "PdfReader", return_value=SyntheticTextReader(
            [page_one, page_two]
        )):
            out = v13_parser.inspect_bytes(self.FAKE_PDF_BYTES)
        self.assertIn("ambiguous_repeated_title", out["reason_codes"])
        self.assertFalse(out["vintage_proven"])
        self.assertFalse(out["economic_values_retained"])
        # This establishes a possible false ambiguity on continuation titles
        # in an invented fixture; it does not establish actual Table 9 contents.

    def test_lexical_crude_petroleum_prefix_is_not_semantic_identity(self):
        invented = (
            "Table 9. Producer price indexes for commodity and service groupings and individual items\n"
            "Commodity code\nUnadjusted index\nUnprocessed nonfood materials\n"
            "Crude petroleum derived products\n"
        )
        with mock.patch.object(v13_parser, "PdfReader", return_value=SyntheticTextReader([invented])):
            out = v13_parser.inspect_bytes(self.FAKE_PDF_BYTES)
        self.assertTrue(out["target_label_seen"])
        self.assertFalse(out["vintage_proven"])
        self.assertFalse(out["economic_values_retained"])
        # A mere lexical match is insufficient. This is design evidence for
        # stricter future row identity, NOT a reason to reinterpret the old run.

    def test_reader_exception_is_different_failure_code(self):
        with mock.patch.object(v13_parser, "PdfReader", side_effect=RuntimeError("private bytes")):
            out = v13_parser.inspect_bytes(self.FAKE_PDF_BYTES)
        self.assertEqual(out["reason_codes"], ["pdf_load_failed"])
        self.assertNotIn("private bytes", json.dumps(out))


if __name__ == "__main__":
    unittest.main()
