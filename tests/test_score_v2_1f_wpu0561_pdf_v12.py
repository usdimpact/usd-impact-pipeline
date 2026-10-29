"""Offline-only pypdf PDF-fixture tests. No public PDF, economic data or BLS HTTP."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

try:
    import pypdf
except ModuleNotFoundError as exc:
    if exc.name != "pypdf":
        raise
    # The main Score runtime does not install the fixture-only package.
    # Parser tests run fully in the hash-pinned isolated CI job instead.
    pypdf = None

if pypdf is not None:
    from scripts.score_v2_1f_wpu0561_pdf_v12_synthetic import (
        CASES, run_synthetic_case
    )
else:
    CASES = frozenset()

    def run_synthetic_case(case: str) -> dict:
        raise RuntimeError("pypdf fixture parser is available only in the isolated job")


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "governance/score-v2-1f-bls-wpu0561-pdf-parser-security-v12-design.json"
LOCK = ROOT / "governance/score-v2-1f-wpu0561-pdf-v12-parser.lock"
PIN = "33e4fb41ca352810eb4e9838aa0d82d6888a5f8bf682f43e99cce5faa666255c"
BLS = "https://www.bls.gov/ppi/detailed-report/ppi-detailed-report-april-2026.pdf"


class V12ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = json.loads(DESIGN.read_text(encoding="utf-8"))

    @unittest.skipUnless(pypdf is not None, "fixture-only parser is absent from production dependency lock")
    def test_locked_parser_version_and_hash(self) -> None:
        self.assertEqual(pypdf.__version__, "6.21.4")
        self.assertIn("pypdf==6.21.4 --hash=sha256:" + PIN, LOCK.read_text(encoding="utf-8"))

    def test_scope_is_design_only(self) -> None:
        self.assertEqual(self.spec["version"], 12)
        self.assertEqual(self.spec["status"], "owner_approved_design_only_live_hold")
        self.assertEqual(self.spec["owner_approval"]["scope"],
                         "precise_april_2026_BLS_PDF_source_boundary_and_parser_security_contract_design_only")
        self.assertTrue(self.spec["owner_approval"]["synthetic_fixture_parser_implementation_allowed"])
        self.assertFalse(self.spec["owner_approval"]["pdf_binary_network_request_allowed"])
        self.assertFalse(self.spec["owner_approval"]["live_pdf_parser_access_allowed"])

    def test_source_pinned_but_never_retrieved(self) -> None:
        s = self.spec["source_boundary"]
        self.assertEqual(s["pdf_url"], BLS)
        self.assertEqual(s["expected_hostname"], "www.bls.gov")
        self.assertEqual(s["requests_authorized_now"], 0)
        self.assertEqual(s["future_max_requests_if_separately_authorized"], 1)
        for name in ("pdf_content_has_been_fetched", "pdf_response_header_verified",
                     "pdf_immutable_vintage_proven", "pdf_table9_schema_proven",
                     "pdf_exact_target_row_proven", "source_eligible_for_values"):
            self.assertIs(s[name], False)
        self.assertIsNone(s["pdf_hash_sha256"])

    def test_only_synthetic_parser_selected(self) -> None:
        spec = self.spec["parser_candidate"]
        self.assertTrue(spec["parser_selected_for_fixture_only"])
        self.assertFalse(spec["parser_approved_for_live_pdf"])
        self.assertTrue(spec["cannot_modify_main_requirements_lock"])
        self.assertEqual(spec["version"], "6.21.4")
        self.assertEqual(spec["wheel_sha256"], PIN)

    def test_networkless_sandbox_contract(self) -> None:
        sb = self.spec["isolated_fixture_runtime"]
        self.assertEqual(sb["network"], "none")
        self.assertTrue(sb["read_only_rootfs"])
        self.assertTrue(sb["drop_all_capabilities"])
        self.assertTrue(sb["no_new_privileges"])
        self.assertEqual(sb["run_as_uid"], "65534:65534")
        self.assertTrue(sb["only_synthetic_generated_in_process"])
        self.assertFalse(sb["github_token_in_container"])
        self.assertFalse(sb["real_BLS_bytes_in_container"])

    def test_future_real_pdf_gate_stays_closed(self) -> None:
        sec = self.spec["provisional_real_pdf_security_gates"]
        self.assertEqual(sec["status"], "not_authorized")
        self.assertFalse(sec["pdf_raw_stream_transient_access_approved"])
        self.assertFalse(sec["pdf_semantic_numeric_access_approved"])
        self.assertFalse(sec["future_execution_job_created"])
        self.assertTrue(sec["separate_network_broker_design_required"])
        self.assertEqual(sec["max_raw_value_retention"], 0)

    def test_all_execution_flags_remain_false(self) -> None:
        auth = self.spec["current_execution_permissions"]
        self.assertTrue(auth)
        self.assertTrue(all(value is False for value in auth.values()))

    def test_rights_and_prior_methodology_not_changed(self) -> None:
        refs = self.spec["references"]
        self.assertTrue(refs["authoritative_existing_v9_design"])
        self.assertEqual(refs["authoritative_main_commit"],
                         "0c420f495e6196d34d195d441edf7b707da4f35a")
        self.assertIn("/issues/155", refs["rights_hold_issue"])


@unittest.skipUnless(pypdf is not None, "synthetic parser is tested in isolated no-network CI")
class V12SyntheticPDFTests(unittest.TestCase):
    def test_enumerated_fixture_cases_are_static(self) -> None:
        self.assertEqual(len(CASES), 16)

    def test_nominal_is_compatible_but_never_approved(self) -> None:
        result = run_synthetic_case("nominal")
        self.assertEqual(result["status"], "synthetic_format_compatible_not_live")
        self.assertEqual(result["reason_codes"], [])
        self.assertEqual(result["network_requests"], 0)
        self.assertFalse(result["source_approved"])

    def test_percent_change_is_not_index_level(self) -> None:
        self.assert_reject("percent_only", "unadjusted_index_header_missing_or_not_unique")

    def test_wrong_month_rejected(self) -> None:
        self.assert_reject("wrong_month", "april_month_missing_or_not_unique")

    def test_wrong_table_rejected(self) -> None:
        self.assert_reject("wrong_table", "table9_missing_or_not_unique")

    def test_duplicate_table_rejected(self) -> None:
        self.assert_reject("two_tables", "table9_missing_or_not_unique")

    def test_stage_demand_context_rejected(self) -> None:
        self.assert_reject("wrong_context", "direct_commodity_context_missing")

    def test_domestic_production_variant_rejected(self) -> None:
        self.assert_reject("domestic_variant", "exact_target_missing_or_not_unique")

    def test_duplicate_crude_petroleum_rejected(self) -> None:
        self.assert_reject("duplicate_target", "exact_target_missing_or_not_unique")

    def test_missing_crude_petroleum_rejected(self) -> None:
        self.assert_reject("no_target", "exact_target_missing_or_not_unique")

    def test_ambiguous_header_rejected(self) -> None:
        self.assert_reject("duplicate_header", "unadjusted_index_header_missing_or_not_unique")

    def test_wrong_synthetic_marker_rejected(self) -> None:
        self.assert_reject("wrong_marker", "wrong_fixture_marker")

    def test_numeric_token_rejected_without_returning_value(self) -> None:
        r = self.assert_reject("numeric_text", "numeric_economic_token_in_fixture")
        self.assertNotIn("123.45", json.dumps(r))

    def test_more_than_one_page_rejected(self) -> None:
        self.assert_reject("too_many_pages", "unexpected_page_count")

    def test_oversized_synthetic_text_rejected(self) -> None:
        self.assert_reject("text_overflow", "synthetic_text_oversized")

    def test_invalid_magic_rejected(self) -> None:
        self.assert_reject("invalid_magic", "invalid_pdf_magic")

    def test_unknown_extra_text_rejected(self) -> None:
        self.assert_reject("unknown_extra", "unexpected_fixture_text")

    def test_cannot_supply_file_path_or_url_as_case(self) -> None:
        for case in (BLS, "/tmp/bls.pdf", "live", ""):
            with self.assertRaises(ValueError):
                run_synthetic_case(case)

    def test_all_fixture_reports_have_zero_live_output(self) -> None:
        for case in CASES:
            out = run_synthetic_case(case)
            self.assertEqual(out["network_requests"], 0)
            self.assertFalse(out["live_pdf_fetched"])
            self.assertFalse(out["actual_bls_pdf_parsed"])
            self.assertFalse(out["economic_value_retained"])
            self.assertFalse(out["numeric_identifier_value_retained"])
            self.assertFalse(out["source_approved"])
            self.assertFalse(out["production_changed"])

    def assert_reject(self, case: str, expected: str) -> dict:
        out = run_synthetic_case(case)
        self.assertEqual(out["status"], "hold", msg=out)
        self.assertIn(expected, out["reason_codes"], msg=out)
        self.assertEqual(out["network_requests"], 0)
        return out


if __name__ == "__main__":
    unittest.main()
