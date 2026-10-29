"""Issue #258 v13 one-off preflight safety tests: NO BLS network traffic.

Transport is fully mocked; PDF parser uses v12 in-memory invented fixtures in
isolated pypdf CI only. Main Score dependency suite runs stdlib cases and skips
optional parser fixtures without importing pypdf.
"""

from __future__ import annotations

from email.message import Message
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

from scripts import score_v2_1f_wpu0561_pdf_v13_transport as transport


class V13ScopedApprovalContractTests(unittest.TestCase):
    """Owner approval does not by itself activate a network request."""

    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        gov = root / "governance"
        self.approval = json.loads(
            (gov / "score-v2-1f-wpu0561-pdf-v13-owner-decision.json").read_text()
        )
        self.contract = json.loads(
            (gov / "score-v2-1f-wpu0561-pdf-v13-execution-contract.json").read_text()
        )

    def test_approval_one_resource_and_no_values(self) -> None:
        self.assertEqual(self.approval["version"], 13)
        self.assertEqual(
            self.approval["exact_resource"]["allowed_url"], transport.PDF_URL
        )
        self.assertEqual(self.approval["exact_resource"]["maximum_attempts"], 1)
        auth = self.approval["approval"]
        self.assertTrue(auth["transient_raw_PDF_bytes_for_only_that_structural_preflight"])
        self.assertTrue(auth["transient_decoded_page_text_exposure_in_bounded_parser"])
        self.assertFalse(auth["numeric_identifier_value_read"])
        self.assertFalse(auth["economic_observation_read"])
        self.assertFalse(auth["public_artifact_change"])
        self.assertFalse(auth["production_change"])

    def test_contract_binds_single_request_and_claim(self) -> None:
        self.assertEqual(self.contract["version"], 13)
        self.assertEqual(self.contract["one_off_network"]["target"], transport.PDF_URL)
        self.assertEqual(self.contract["one_off_network"]["max_request_attempts"], 1)
        self.assertTrue(self.contract["separation_of_duties"]["claim_must_succeed_before_http"])
        self.assertTrue(self.contract["separation_of_duties"]["claim_must_succeed_before_http"])
        self.assertTrue(self.contract["separation_of_duties"]["protected_main_dispatch_marker_commit_required"])

    def test_initial_pending_workflow_does_not_activate(self) -> None:
        # The exact stage is a governance record, independent of code presence.
        state = self.contract["state"]
        self.assertIn(state, (
            "review_only_no_dispatch_or_live_receipt",
            "owner_activation_pending_dispatch",
            "approved_one_off_active",
        ))
        auth = self.contract["authorization_state"]
        receipt = transport.RECEIPT.is_file()
        dispatch = transport.DISPATCH.is_file()
        if state == "review_only_no_dispatch_or_live_receipt":
            self.assertFalse(auth["current_live_BLS_GET"])
            self.assertFalse(auth["receipt_created"])
            self.assertFalse(auth["dispatch_marker_created"])
            self.assertFalse(receipt)
            self.assertFalse(dispatch)
        elif state == "owner_activation_pending_dispatch":
            self.assertTrue(receipt)
            self.assertFalse(dispatch)
            self.assertTrue(auth["receipt_created"])
            self.assertFalse(auth["current_live_BLS_GET"])
            self.assertFalse(auth["dispatch_marker_created"])
        else:
            self.assertTrue(receipt)
            self.assertTrue(dispatch)
            self.assertTrue(auth["current_live_BLS_GET"])
            self.assertTrue(auth["receipt_created"])
            self.assertTrue(auth["dispatch_marker_created"])
        for field in (
            "identifier_read", "economic_value_read", "score_or_reconstruction",
            "research_ledger_change", "public_write", "production_change",
        ):
            self.assertFalse(auth[field])

    def test_old_v8_receipt_never_reactivated(self) -> None:
        p = Path(__file__).resolve().parents[1] / "governance"
        self.assertFalse(
            (p / "score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json").exists()
        )
        self.assertFalse(
            (p / "score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json").exists()
        )


class FakeResponse:
    def __init__(self, body: bytes | None = None, *,
                 url: str = transport.PDF_URL,
                 code: int = 200,
                 mime: str = "application/pdf",
                 length: str | None = None) -> None:
        self.body = body if body is not None else b"%PDF-1.7\nfake-synthetic\n%%EOF\n"
        self.url = url
        self.code = code
        self.mime = mime
        self.length = length
        self.read_calls = 0

    def geturl(self) -> str:
        return self.url

    def getcode(self) -> int:
        return self.code

    def info(self) -> Message:
        headers = Message()
        headers["Content-Type"] = self.mime
        if self.length is not None:
            headers["Content-Length"] = self.length
        return headers

    def read(self, cap: int) -> bytes:
        self.read_calls += 1
        return self.body[:cap]

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_: object) -> None:
        return None


class FakeOpener:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.count = 0
        self.requested_url = ""
        self.timeout = None

    def open(self, request, timeout: int = 0):
        self.count += 1
        self.requested_url = request.full_url
        self.timeout = timeout
        return self.response


class TransportUnitTests(unittest.TestCase):
    def test_single_exact_pdf_get_mock(self) -> None:
        o = FakeOpener(FakeResponse())
        budget = [0]
        out = transport.fetch_exactly_once(opener=o, budget=budget)
        self.assertEqual(o.count, 1)
        self.assertEqual(budget, [1])
        self.assertEqual(o.requested_url, transport.PDF_URL)
        self.assertEqual(o.timeout, 20)
        self.assertTrue(out.startswith(b"%PDF-"))

    def test_no_second_attempt_after_success(self) -> None:
        o = FakeOpener(FakeResponse())
        budget = [0]
        transport.fetch_exactly_once(opener=o, budget=budget)
        with self.assertRaisesRegex(transport.GlobalStop, "request_budget_exhausted"):
            transport.fetch_exactly_once(opener=o, budget=budget)
        self.assertEqual(o.count, 1)

    def test_redirect_rejected(self) -> None:
        o = FakeOpener(FakeResponse(url="https://other.example.com/final.pdf"))
        with self.assertRaisesRegex(transport.GlobalStop, "url_or_redirect_mismatch"):
            transport.fetch_exactly_once(opener=o, budget=[0])
        self.assertEqual(o.count, 1)

    def test_wrong_content_type_rejected(self) -> None:
        o = FakeOpener(FakeResponse(mime="text/html"))
        with self.assertRaisesRegex(transport.GlobalStop, "wrong_content_type"):
            transport.fetch_exactly_once(opener=o, budget=[0])

    def test_http_status_rejected(self) -> None:
        o = FakeOpener(FakeResponse(code=429))
        with self.assertRaisesRegex(transport.GlobalStop, "non_200_response"):
            transport.fetch_exactly_once(opener=o, budget=[0])

    def test_large_declared_size_rejected(self) -> None:
        o = FakeOpener(FakeResponse(length=str(transport.MAX_BYTES + 1)))
        with self.assertRaisesRegex(transport.GlobalStop, "declared_pdf_size_over_bound"):
            transport.fetch_exactly_once(opener=o, budget=[0])

    def test_large_binary_size_rejected(self) -> None:
        o = FakeOpener(FakeResponse(body=b"%PDF-" + b"x" * transport.MAX_BYTES))
        with self.assertRaisesRegex(transport.GlobalStop, "pdf_response_over_bound"):
            transport.fetch_exactly_once(opener=o, budget=[0])

    def test_truncated_binary_rejected(self) -> None:
        o = FakeOpener(FakeResponse(body=b"%PDF-1.7\nno_eof"))
        with self.assertRaisesRegex(transport.GlobalStop, "truncated_pdf_no_eof"):
            transport.fetch_exactly_once(opener=o, budget=[0])

    def test_challenge_without_pdf_magic_rejected(self) -> None:
        o = FakeOpener(FakeResponse(body=b"<html>Captcha</html>"))
        with self.assertRaisesRegex(transport.GlobalStop, "wrong_magic_or_challenge"):
            transport.fetch_exactly_once(opener=o, budget=[0])

    def test_network_failure_consumes_budget(self) -> None:
        o = mock.Mock()
        o.open.side_effect = OSError("simulated network failure")
        budget = [0]
        with self.assertRaisesRegex(transport.GlobalStop, "transport_failure_no_retry"):
            transport.fetch_exactly_once(opener=o, budget=budget)
        self.assertEqual(budget, [1])
        self.assertEqual(o.open.call_count, 1)

    def test_no_receipt_blocks_all_live_processing(self) -> None:
        with self.assertRaises(transport.GlobalStop):
            transport.validate_live_gate({})

    def test_default_cli_path_does_not_fetch(self) -> None:
        with mock.patch.object(transport, "validate_live_gate") as a:
            with mock.patch.object(transport, "fetch_exactly_once") as b:
                with mock.patch("sys.argv", ["preflight-v13"]):
                    with mock.patch("builtins.print"):
                        code = transport.main()
        self.assertEqual(code, 2)
        a.assert_not_called()
        b.assert_not_called()

    def test_sandbox_configuration_forces_no_network(self) -> None:
        # Local paths are invented to check argument composition, no process
        # or container launched from this test.
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / "checkout").mkdir()
            (root / "pypdf-v13-oneoff").mkdir()
            env = {"GITHUB_WORKSPACE": str(root / "checkout"), "RUNNER_TEMP": str(root)}
            cmd = transport.configured_sandbox_command(env)
        self.assertIn("--network", cmd)
        self.assertEqual(cmd[cmd.index("--network") + 1], "none")
        self.assertIn("--read-only", cmd)
        self.assertIn("--cap-drop", cmd)
        self.assertIn("no-new-privileges", cmd)
        self.assertIn("--user", cmd)
        self.assertIn("65534:65534", cmd)
        self.assertNotIn("--privileged", cmd)
        self.assertTrue(cmd[-1].endswith("_pdf_v13_parser"))

    def test_sanitizer_never_returns_exception_text(self) -> None:
        r = transport.safe_failure("sensitive 123.45 notes", 1)
        self.assertEqual(r["reason_codes"], ["unspecified_stop"])
        self.assertNotIn("123.45", json.dumps(r))
        self.assertEqual(r["request_attempt_count"], 1)
        self.assertFalse(r["production_changed"])

    def test_sandbox_does_not_log_exception(self) -> None:
        with mock.patch.object(transport.subprocess, "run") as run:
            run.return_value = SimpleNamespace(returncode=2, stdout=b"123.45", stderr=b"SENSITIVE")
            with self.assertRaisesRegex(transport.GlobalStop, "sandbox_nonzero_exit"):
                transport.parse_in_sandbox(b"%PDF-DUMMY", sandbox_cmd=["docker"])
            self.assertTrue(run.called)

    def test_sanitized_result_only(self) -> None:
        payload = {
            "status": "structural_metadata_only_hold",
            "reason_codes": ["no_first_release_vintage_proof"],
            "page_count_band": "1_to_50",
            "table9_title_seen": True,
            "unadjusted_index_role_seen": True,
            "percent_change_role_seen": True,
            "target_label_seen": True,
            "target_scope_seen": True,
            "ambiguous_layout": False,
            "vintage_proven": False,
            "identifier_values_retained": False,
            "economic_values_retained": False,
            "network_requests": 0,
        }
        with mock.patch.object(transport.subprocess, "run") as run:
            run.return_value = SimpleNamespace(returncode=0, stdout=json.dumps(payload).encode(), stderr=b"")
            got = transport.parse_in_sandbox(b"%PDF-DUMMY", sandbox_cmd=["docker"])
        self.assertEqual(got, payload)

    def test_reject_unexpected_numeric_field(self) -> None:
        payload = {
            "status": "structural_metadata_only_hold",
            "reason_codes": [],
            "page_count_band": "unknown",
            "table9_title_seen": False,
            "unadjusted_index_role_seen": False,
            "percent_change_role_seen": False,
            "target_label_seen": False,
            "target_scope_seen": False,
            "ambiguous_layout": True,
            "vintage_proven": False,
            "identifier_values_retained": False,
            "economic_values_retained": False,
            "network_requests": 0,
            "index_level": 123.45,
        }
        with mock.patch.object(transport.subprocess, "run") as run:
            run.return_value = SimpleNamespace(returncode=0, stdout=json.dumps(payload).encode(), stderr=b"")
            with self.assertRaisesRegex(transport.GlobalStop, "sanitized_schema_mismatch"):
                transport.parse_in_sandbox(b"%PDF-DUMMY", sandbox_cmd=["docker"])


HAS_PYPDF = importlib.util.find_spec("pypdf") is not None
if HAS_PYPDF:
    from scripts.score_v2_1f_wpu0561_pdf_v12_synthetic import _build_synthetic_pdf
    from scripts.score_v2_1f_wpu0561_pdf_v13_parser import inspect_bytes


@unittest.skipUnless(HAS_PYPDF, "pypdf fixture parser exists only in isolated test job")
class SyntheticPDFParserTests(unittest.TestCase):
    def test_nominal_structure_remains_hold_without_vintage(self) -> None:
        out = inspect_bytes(_build_synthetic_pdf("nominal"))
        self.assertEqual(out["status"], "structural_metadata_only_hold")
        self.assertTrue(out["table9_title_seen"])
        self.assertTrue(out["unadjusted_index_role_seen"])
        self.assertTrue(out["target_scope_seen"])
        self.assertTrue(out["target_label_seen"])
        self.assertFalse(out["vintage_proven"])
        self.assertEqual(out["reason_codes"], ["no_first_release_vintage_proof"])

    def test_reject_wrong_header(self) -> None:
        out = inspect_bytes(_build_synthetic_pdf("percent_only"))
        self.assertEqual(out["status"], "fail_closed")
        self.assertIn("missing_index_level_header", out["reason_codes"])

    def test_reject_wrong_table(self) -> None:
        out = inspect_bytes(_build_synthetic_pdf("wrong_table"))
        self.assertEqual(out["status"], "fail_closed")
        self.assertIn("missing_table9_title", out["reason_codes"])

    def test_reject_wrong_month_and_never_claim_proof(self) -> None:
        out = inspect_bytes(_build_synthetic_pdf("wrong_month"))
        self.assertFalse(out["vintage_proven"])

    def test_reject_domestic_variant(self) -> None:
        out = inspect_bytes(_build_synthetic_pdf("domestic_variant"))
        self.assertEqual(out["status"], "fail_closed")
        self.assertIn("target_label_variant", out["reason_codes"])

    def test_reject_duplicate_target(self) -> None:
        out = inspect_bytes(_build_synthetic_pdf("duplicate_target"))
        self.assertEqual(out["status"], "fail_closed")
        self.assertIn("ambiguous_repeated_title", out["reason_codes"])

    def test_reject_no_target(self) -> None:
        out = inspect_bytes(_build_synthetic_pdf("no_target"))
        self.assertIn("missing_exact_crude_label", out["reason_codes"])

    def test_wrong_magic_holds(self) -> None:
        out = inspect_bytes(_build_synthetic_pdf("invalid_magic"))
        self.assertEqual(out["status"], "fail_closed")
        self.assertIn("unexpected_pdf_magic", out["reason_codes"])

    def test_all_results_no_economic_text(self) -> None:
        for name in ("nominal", "numeric_text", "domestic_variant", "duplicate_target"):
            out = inspect_bytes(_build_synthetic_pdf(name))
            self.assertFalse(out["economic_values_retained"])
            self.assertFalse(out["identifier_values_retained"])
            self.assertFalse(out["vintage_proven"])
            self.assertNotIn("123.45", json.dumps(out))


if __name__ == "__main__":
    unittest.main()
