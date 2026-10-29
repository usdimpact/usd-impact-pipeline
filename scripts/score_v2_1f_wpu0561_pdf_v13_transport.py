#!/usr/bin/env python3
"""Issue #258 PDF structural preflight: strictly scoped, single-request transport.

NO DEFAULT LIVE OPERATION. Live mode requires reviewed protected-main receipt,
dispatch marker, a successful atomic claim made by the separate GitHub Action,
and an exact run-specific environment. No stdout of PDF bytes, decoded text,
numeric identifiers or economic observations.

The BLS binary is sent over stdin to a sandboxed networkless parser; no file
is persisted. The transport code cannot perform an actual live request in CI
unless a separate future owner-activated protected workflow explicitly calls
main --live with all guards present.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import urllib.error
import urllib.request
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PDF_URL = "https://www.bls.gov/ppi/detailed-report/ppi-detailed-report-april-2026.pdf"
USER_AGENT = "USD-Impact-Score-v2.1F-WPU0561-PDF-structural/1.0 (contact: support@usd-impact.com)"
CONTRACT = ROOT / "governance/score-v2-1f-wpu0561-pdf-v13-execution-contract.json"
APPROVAL = ROOT / "governance/score-v2-1f-wpu0561-pdf-v13-owner-decision.json"
RECEIPT = ROOT / "governance/score-v2-1f-wpu0561-pdf-v13-live-authorization.json"
DISPATCH = ROOT / "governance/score-v2-1f-wpu0561-pdf-v13-dispatch.json"
MAX_BYTES = 10 * 1024 * 1024
MAX_RESULT_BYTES = 4096


class GlobalStop(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def load_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise GlobalStop("malformed_governance")
    return obj


def validate_preclaim_gate(environ: dict[str, str] | None = None) -> None:
    env = environ if environ is not None else os.environ
    if not RECEIPT.is_file() or not DISPATCH.is_file():
        raise GlobalStop("missing_separately_activated_receipt_or_dispatch")
    c, approval = load_json(CONTRACT), load_json(APPROVAL)
    receipt, dispatch = load_json(RECEIPT), load_json(DISPATCH)
    if c.get("version") != 13 or approval.get("version") != 13:
        raise GlobalStop("wrong_contract_version")
    if c.get("state") != "approved_one_off_active":
        raise GlobalStop("contract_not_activated")
    live = c.get("authorization_state", {})
    if any(live.get(field) is not True for field in (
        "current_live_BLS_GET", "receipt_created", "dispatch_marker_created",
    )):
        raise GlobalStop("execution_contract_not_live")
    for field in (
        "identifier_read", "economic_value_read", "score_or_reconstruction",
        "research_ledger_change", "public_write", "production_change",
    ):
        if live.get(field) is not False:
            raise GlobalStop("forbidden_scope_activated")
    if c.get("one_off_network", {}).get("target") != PDF_URL:
        raise GlobalStop("different_url_in_contract")
    if approval.get("approval", {}).get("one_off_live_structural_preflight_after_separate_protected_activation") is not True:
        raise GlobalStop("no_owner_preflight_scope")
    if approval.get("approval", {}).get("transient_decoded_page_text_exposure_in_bounded_parser") is not True:
        raise GlobalStop("no_transient_pdf_processing_approval")
    if approval.get("approval", {}).get("economic_observation_read") is not False:
        raise GlobalStop("economic_value_authorization_changed")
    if receipt.get("version") != 13 or receipt.get("decision_status") != "approved":
        raise GlobalStop("receipt_not_approved")
    if receipt.get("exact_url") != PDF_URL or receipt.get("request_budget") != 1:
        raise GlobalStop("receipt_scope_mismatch")
    if receipt.get("raw_PDF_ephemeral_access") is not True:
        raise GlobalStop("receipt_missing_ephemeral_permission")
    for key in ("numeric_identifier_read", "economic_value_read", "score_calculation", "production"):
        if receipt.get(key) is not False:
            raise GlobalStop("receipt_prohibited_scope")
    if dispatch.get("version") != 13 or dispatch.get("state") != "approved_dispatch":
        raise GlobalStop("dispatch_not_active")
    if dispatch.get("exact_url") != PDF_URL or dispatch.get("request_budget") != 1:
        raise GlobalStop("dispatch_scope_mismatch")
    receipt_digest = hashlib.sha256(RECEIPT.read_bytes()).hexdigest()
    if dispatch.get("prior_receipt_sha256") != receipt_digest:
        raise GlobalStop("dispatch_not_linked_to_exact_receipt_bytes")
    if not env.get("GITHUB_REPOSITORY") == "usdimpact/usd-impact-pipeline":
        raise GlobalStop("wrong_github_repository")
    if env.get("GITHUB_REF") != "refs/heads/main" or env.get("GITHUB_EVENT_NAME") != "push":
        raise GlobalStop("not_trusted_main_push")
    if env.get("GITHUB_RUN_ATTEMPT") != "1":
        raise GlobalStop("rerun_forbidden")
def validate_live_gate(environ: dict[str, str] | None = None) -> None:
    env = environ if environ is not None else os.environ
    validate_preclaim_gate(env)
    if env.get("WPU0561_V13_ATOMIC_CLAIM_OK") != "true":
        raise GlobalStop("unique_claim_not_proven")
    if env.get("WPU0561_V13_CLAIMED_SHA") != env.get("GITHUB_SHA"):
        raise GlobalStop("claim_sha_mismatch")
    if env.get("WPU0561_V13_CLAIMED_RUN_ID") != env.get("GITHUB_RUN_ID"):
        raise GlobalStop("claim_run_mismatch")


def fetch_exactly_once(*, opener: Any, budget: list[int]) -> bytes:
    """Dependency-injected opener for offline tests; called at most once in live runner."""
    if budget != [0]:
        raise GlobalStop("request_budget_exhausted")
    budget[0] = 1  # Consume BEFORE any DNS or transport attempt
    request = urllib.request.Request(
        PDF_URL,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/pdf",
            "Connection": "close",
        },
        method="GET",
    )
    try:
        with opener.open(request, timeout=20) as resp:
            if resp.geturl() != PDF_URL:
                raise GlobalStop("url_or_redirect_mismatch")
            if int(resp.getcode()) != 200:
                raise GlobalStop("non_200_response")
            mime = (resp.info().get("Content-Type") or "").split(";")[0].lower().strip()
            if mime != "application/pdf":
                raise GlobalStop("wrong_content_type")
            declared = resp.info().get("Content-Length")
            if declared:
                try:
                    val = int(declared)
                except ValueError as exc:
                    raise GlobalStop("malformed_content_length") from exc
                if val < 1 or val > MAX_BYTES:
                    raise GlobalStop("declared_pdf_size_over_bound")
            content = resp.read(MAX_BYTES + 1)
            if not isinstance(content, bytes) or len(content) > MAX_BYTES:
                raise GlobalStop("pdf_response_over_bound")
    except urllib.error.HTTPError as exc:
        raise GlobalStop("http_failure_no_retry") from exc
    except (urllib.error.URLError, socket.timeout, OSError) as exc:
        raise GlobalStop("transport_failure_no_retry") from exc
    if not content.startswith(b"%PDF-"):
        raise GlobalStop("wrong_magic_or_challenge")
    if b"%%EOF" not in content[-2048:]:
        raise GlobalStop("truncated_pdf_no_eof")
    return content


def configured_sandbox_command(environ: dict[str, str] | None = None) -> list[str]:
    """Fixed sandbox args. No environment-provided shell strings or flags."""
    env = environ if environ is not None else os.environ
    ws = env.get("GITHUB_WORKSPACE")
    temp = env.get("RUNNER_TEMP")
    if not ws or not temp:
        raise GlobalStop("trusted_runner_paths_unavailable")
    root = Path(ws).resolve()
    wheel = (Path(temp) / "pypdf-v13-oneoff").resolve()
    if not root.is_dir() or not wheel.is_dir():
        raise GlobalStop("pinned_wheel_or_checkout_unavailable")
    return [
        "docker", "run", "-i", "--rm",
        "--network", "none",
        "--read-only",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--pids-limit", "64",
        "--memory", "256m",
        "--cpus", "1",
        "--user", "65534:65534",
        "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=16m,uid=65534,gid=65534",
        "--env", "PYTHONPATH=/parser:/repo",
        "--env", "PYTHONDONTWRITEBYTECODE=1",
        "--volume", f"{root}:/repo:ro",
        "--volume", f"{wheel}:/parser:ro",
        "--workdir", "/repo",
        "python:3.11.15-slim-bookworm@sha256:d29f48a31a8b408ed19272ca1e7b10ebae13b240a27e862d3d4217c528e2e0c3",
        "python", "-m", "scripts.score_v2_1f_wpu0561_pdf_v13_parser",
    ]


def parse_in_sandbox(pdf: bytes, *, sandbox_cmd: list[str]) -> dict[str, Any]:
    """Provide in-memory bytes over stdin; never persist raw output or error text."""
    try:
        result = subprocess.run(
            sandbox_cmd,
            input=pdf,
            capture_output=True,
            check=False,
            timeout=90,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GlobalStop("sandbox_launch_or_timeout") from None
    finally:
        # The immutable bytes object remains until function return; it is not logged.
        pass
    if result.returncode != 0:
        raise GlobalStop("sandbox_nonzero_exit")
    if len(result.stdout) > MAX_RESULT_BYTES:
        raise GlobalStop("sanitized_result_over_bound")
    try:
        parsed = json.loads(result.stdout)
    except (ValueError, UnicodeError) as exc:
        raise GlobalStop("invalid_sanitized_result") from None
    if not isinstance(parsed, dict):
        raise GlobalStop("unexpected_sanitized_result")
    allowed = {
        "status", "reason_codes", "page_count_band", "table9_title_seen",
        "unadjusted_index_role_seen", "percent_change_role_seen",
        "target_label_seen", "target_scope_seen", "ambiguous_layout",
        "vintage_proven", "identifier_values_retained", "economic_values_retained",
        "network_requests",
    }
    if set(parsed) != allowed:
        raise GlobalStop("sanitized_schema_mismatch")
    if parsed["identifier_values_retained"] is not False or parsed["economic_values_retained"] is not False:
        raise GlobalStop("numeric_value_leak")
    if parsed["vintage_proven"] is not False:
        raise GlobalStop("unjustified_first_release_proof")
    if parsed["network_requests"] != 0:
        raise GlobalStop("sandbox_network_claim_mismatch")
    for field in (
        "table9_title_seen", "unadjusted_index_role_seen", "percent_change_role_seen",
        "target_label_seen", "target_scope_seen", "ambiguous_layout", "vintage_proven",
        "identifier_values_retained", "economic_values_retained",
    ):
        if type(parsed[field]) is not bool:
            raise GlobalStop("sanitized_boolean_type_error")
    if parsed["page_count_band"] not in ("unknown", "1_to_50", "51_to_200"):
        raise GlobalStop("unapproved_page_count_band")
    if parsed["status"] not in ("structural_metadata_only_hold", "fail_closed"):
        raise GlobalStop("invalid_preflight_status")
    if not isinstance(parsed["reason_codes"], list) or len(parsed["reason_codes"]) > 16:
        raise GlobalStop("unbounded_reason_codes")
    if any(
        not isinstance(v, str) or not v.isascii() or len(v) > 80 or not v.replace("_", "").isalpha()
        for v in parsed["reason_codes"]
    ):
        raise GlobalStop("unsafe_reason_codes")
    return parsed


def safe_failure(reason: str, request_attempts: int) -> dict[str, Any]:
    code = reason if reason.replace("_", "").isalpha() and len(reason) <= 80 else "unspecified_stop"
    return {
        "status": "fail_closed",
        "reason_codes": [code],
        "request_attempt_count": min(request_attempts, 1),
        "identifier_values_retained": False,
        "economic_values_retained": False,
        "score_calculated": False,
        "rights_changed": False,
        "production_changed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    budget = [0]
    try:
        if not args.live:
            raise GlobalStop("live_mode_not_selected")
        validate_live_gate()
        cmd = configured_sandbox_command()
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        body = fetch_exactly_once(opener=opener, budget=budget)
        result = parse_in_sandbox(body, sandbox_cmd=cmd)
        output = {
            **result,
            "request_attempt_count": budget[0],
            "score_calculated": False,
            "rights_changed": False,
            "production_changed": False,
        }
        print(json.dumps(output, sort_keys=True))
        return 0 if output["status"] == "structural_metadata_only_hold" else 2
    except (GlobalStop, ValueError, OSError) as exc:
        reason = str(exc) if isinstance(exc, GlobalStop) else "unexpected_preflight_failure"
        print(json.dumps(safe_failure(reason, budget[0]), sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
