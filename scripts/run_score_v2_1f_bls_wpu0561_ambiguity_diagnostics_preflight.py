#!/usr/bin/env python3
"""Owner-authorized Issue #258 design-v5 candidate-context inventory.

Python standard library only. At most one GET attempt is made to each fixed
resource. Redirects and retries are forbidden. Response bodies remain ephemeral.
Identifier values and economic values are never persisted in the diagnostic
output; text is numeric-redacted before candidate context is retained.
"""

from __future__ import annotations

import io
import json
import re
import socket
import urllib.error
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from scripts import score_v2_1f_wpu0561_ambiguity_diagnostics as diagnostic

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
HOST = "www.bls.gov"
USER_AGENT = "USD-Impact-Score-v2.1F-WPU0561-candidate-context/1.0 (contact: support@usd-impact.com)"
HTML_PATH = "/news.release/archives/ppi_05152013.htm"
XLSX_PATH = "/ppi/detailed-report/ppi-detailed-report-april-2026.xlsx"
FIXED_RESOURCES = [HTML_PATH, XLSX_PATH]
MAX_RESPONSE_BYTES = 50 * 1024 * 1024
MAX_CANDIDATES_PER_RESOURCE = 32
MAX_PRECEDING_ROWS = 8
MAX_TEXT_CELLS_PER_CANDIDATE = 64

RECEIPT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
DISPATCH = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
CONTRACT = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json"
DESIGN = ROOT / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json"

CHALLENGE_PHRASES = (
    "access denied",
    "verify you are human",
    "captcha",
    "bot challenge",
    "security challenge",
    "request blocked",
)


class GlobalStop(RuntimeError):
    """A fail-closed condition that cancels any remaining request attempt."""


class RequestBudget:
    def __init__(self) -> None:
        self.count = 0

    def consume(self) -> None:
        if self.count >= 2:
            raise RuntimeError("request budget exceeded")
        self.count += 1


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def _validate_authorization_and_dispatch() -> str:
    if not RECEIPT.exists():
        raise RuntimeError("Issue #258 authorization is not active")
    if not DISPATCH.exists():
        raise RuntimeError("Issue #258 dispatch is not active")

    receipt = _load_json(RECEIPT)
    dispatch = _load_json(DISPATCH)
    contract = _load_json(CONTRACT)
    design = _load_json(DESIGN)

    if design.get("version") != 5 or design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 frozen design v5 changed")
    inventory = design.get("candidate_context_inventory_policy", {})
    if inventory.get("maximum_candidates_per_resource") != MAX_CANDIDATES_PER_RESOURCE:
        raise RuntimeError("candidate limit changed")
    if inventory.get("preceding_rows_per_candidate") != MAX_PRECEDING_ROWS:
        raise RuntimeError("preceding-row limit changed")
    if inventory.get("maximum_persisted_text_cells_per_candidate") != MAX_TEXT_CELLS_PER_CANDIDATE:
        raise RuntimeError("cell limit changed")
    if inventory.get("identifier_values") != "forbidden; this diagnostic does not read or persist identifier values":
        raise RuntimeError("identifier-value policy changed")
    if inventory.get("economic_values") != "forbidden":
        raise RuntimeError("economic-value policy changed")

    if receipt.get("decision_status") != "approved":
        raise RuntimeError("Issue #258 authorization is not approved")
    if receipt.get("issue") != ISSUE:
        raise RuntimeError("Issue #258 authorization issue changed")
    if receipt.get("execution_scope") != "bls_wpu0561_ambiguity_diagnostics_preflight_only":
        raise RuntimeError("Issue #258 execution scope changed")
    if receipt.get("request_budget") != 2:
        raise RuntimeError("Issue #258 request budget changed")
    if receipt.get("max_economic_observations_total") != 0:
        raise RuntimeError("Issue #258 economic observation budget changed")
    if receipt.get("fixed_resources") != FIXED_RESOURCES:
        raise RuntimeError("Issue #258 fixed resources changed")
    if receipt.get("allowed_host") != HOST:
        raise RuntimeError("Issue #258 host changed")
    if receipt.get("contact_user_agent") != USER_AGENT:
        raise RuntimeError("Issue #258 User-Agent changed")

    auth = receipt.get("authorizations", {})
    if auth.get("response_body_ephemeral_retrieval") is not True:
        raise RuntimeError("ephemeral retrieval must be authorized")
    if auth.get("ambiguity_diagnostics_preflight") is not True:
        raise RuntimeError("candidate-context preflight must be authorized")
    for field in (
        "numeric_identifier_field_read",
        "economic_value_read",
        "full_historical_reconstruction",
        "candidate_score_computation",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if dispatch.get("state") != "approved_dispatch":
        raise RuntimeError("Issue #258 dispatch state changed")
    if dispatch.get("phase") != "bls_wpu0561_candidate_context_inventory_preflight":
        raise RuntimeError("Issue #258 dispatch phase changed")
    if dispatch.get("issue") != ISSUE:
        raise RuntimeError("Issue #258 dispatch issue changed")
    if dispatch.get("request_budget") != 2:
        raise RuntimeError("Issue #258 dispatch budget changed")
    if dispatch.get("max_economic_observations_total") != 0:
        raise RuntimeError("Issue #258 dispatch economic observation budget changed")
    if dispatch.get("fixed_resources") != FIXED_RESOURCES:
        raise RuntimeError("Issue #258 dispatch resources changed")
    if dispatch.get("identifier_value_read_authorized") is not False:
        raise RuntimeError("identifier value reads must remain forbidden")
    if dispatch.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if contract.get("state") != "ambiguity_diagnostics_v5_candidate_context_authorized":
        raise RuntimeError("Issue #258 execution contract is not dispatched-active")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("Issue #258 active receipt must be expected")
    if contract.get("dispatch_marker_expected_now") is not True:
        raise RuntimeError("Issue #258 dispatch marker must be expected")
    current = contract.get("current_state", {})
    if current.get("response_body_ephemeral_retrieval_authorized") is not True:
        raise RuntimeError("ephemeral retrieval must be active")
    if current.get("ambiguity_diagnostics_preflight_authorized") is not True:
        raise RuntimeError("candidate-context preflight must be active")
    for field in (
        "numeric_identifier_field_read_authorized",
        "economic_value_read_authorized",
        "full_historical_reconstruction_authorized",
        "candidate_score_computation_authorized",
        "research_ledger_mutation_authorized",
        "public_artifact_replacement_authorized",
        "production_authorized",
    ):
        if current.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    return USER_AGENT


def _looks_like_challenge(body: bytes) -> bool:
    sample = body[:65536].decode("utf-8", errors="ignore").lower()
    return any(phrase in sample for phrase in CHALLENGE_PHRASES)


def _read_response(response: Any) -> bytes:
    body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise GlobalStop("response_size_limit")
    return body


def _request_once(path: str, user_agent: str, budget: RequestBudget) -> tuple[str, bytes | None]:
    if path not in FIXED_RESOURCES:
        raise RuntimeError("request path is not authorized")
    budget.consume()
    request = urllib.request.Request(
        f"https://{HOST}{path}",
        headers={"User-Agent": user_agent, "Accept": "*/*", "Connection": "close"},
        method="GET",
    )
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=30) as response:
            status = int(response.getcode())
            if status != 200:
                raise GlobalStop(f"http_status_{status}")
            body = _read_response(response)
    except urllib.error.HTTPError as exc:
        raise GlobalStop(f"http_status_{int(exc.code)}") from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, socket.gaierror):
            return "transport_dns_failure", None
        raise GlobalStop("transport_failure") from exc
    except socket.gaierror:
        return "transport_dns_failure", None

    if _looks_like_challenge(body):
        raise GlobalStop("access_challenge")
    return "ok", body


def _safe_cell_text(raw: str) -> str:
    return diagnostic.context_safe_text(raw) or ""


class _ContextHTMLTables(HTMLParser):
    """Parse top-level HTML tables while immediately redacting numeric-bearing text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.table_depth = 0
        self.table_index = 0
        self.current_row: list[str] | None = None
        self.current_cell_parts: list[str] | None = None
        self.current_colspan = 1
        self.tables: list[list[list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table":
            self.table_depth += 1
            if self.table_depth == 1:
                self.table_index += 1
                self.tables.append([])
        elif self.table_depth == 1 and tag == "tr":
            self.current_row = []
        elif self.table_depth == 1 and tag in {"th", "td"} and self.current_row is not None:
            self.current_cell_parts = []
            attrs_map = {k.lower(): v for k, v in attrs}
            try:
                self.current_colspan = max(1, int(attrs_map.get("colspan") or "1"))
            except ValueError:
                self.current_colspan = 1

    def handle_data(self, data: str) -> None:
        if self.current_cell_parts is not None:
            self.current_cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.table_depth == 1 and tag in {"th", "td"} and self.current_cell_parts is not None:
            raw = re.sub(r"\s+", " ", " ".join(self.current_cell_parts)).strip()
            safe = _safe_cell_text(raw)
            for _ in range(self.current_colspan):
                assert self.current_row is not None
                self.current_row.append(safe)
            self.current_cell_parts = None
        elif self.table_depth == 1 and tag == "tr":
            if self.current_row is not None:
                self.tables[self.table_index - 1].append(self.current_row)
            self.current_row = None
        elif tag == "table" and self.table_depth:
            self.table_depth -= 1


def _inventory_resource_containers(
    containers: list[tuple[str, list[list[str]]]],
) -> tuple[list[dict[str, Any]], int]:
    output: list[dict[str, Any]] = []
    total_candidates = 0
    for container_name, rows in containers:
        inventory = diagnostic.candidate_context_inventory(
            rows,
            preceding_rows=MAX_PRECEDING_ROWS,
            max_candidates=MAX_CANDIDATES_PER_RESOURCE,
            max_cells_per_candidate=MAX_TEXT_CELLS_PER_CANDIDATE,
        )
        total_candidates += len(inventory)
        if total_candidates > MAX_CANDIDATES_PER_RESOURCE:
            raise GlobalStop("candidate_context_count_exceeds_32_per_resource")
        if inventory:
            output.append({"container": container_name, "candidates": inventory})
    return output, total_candidates


def _inventory_html(body: bytes) -> dict[str, Any]:
    parser = _ContextHTMLTables()
    parser.feed(body.decode("utf-8", errors="replace"))
    containers = [
        (f"table {index}", rows)
        for index, rows in enumerate(parser.tables, start=1)
    ]
    inventory, candidate_count = _inventory_resource_containers(containers)
    return {
        "transport_status": "passed",
        "semantic_status": "evaluated",
        "candidate_count": candidate_count,
        "containers": inventory,
        "candidate_context_truncated": any(
            candidate.get("truncated") is True
            for container in inventory
            for candidate in container.get("candidates", [])
        ),
    }


def _column_number(cell_ref: str) -> int:
    letters = re.match(r"([A-Za-z]+)", cell_ref)
    if not letters:
        return 0
    value = 0
    for ch in letters.group(1).upper():
        value = value * 26 + (ord(ch) - 64)
    return value


def _row_number(cell_ref: str) -> int:
    match = re.search(r"(\d+)$", cell_ref)
    return int(match.group(1)) if match else 0


def _shared_strings_safe(archive: zipfile.ZipFile) -> list[str]:
    try:
        data = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(data)
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    output: list[str] = []
    for si in root.findall(f"{ns}si"):
        raw = "".join(node.text or "" for node in si.iter(f"{ns}t"))
        output.append(_safe_cell_text(raw))
    return output


def _sheet_rows_safe(sheet_data: bytes, shared: list[str]) -> list[list[str]]:
    root = ET.fromstring(sheet_data)
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    rows_map: dict[int, dict[int, str]] = {}
    max_row = 0
    max_col = 0

    for row in root.iter(f"{ns}row"):
        row_num = int(row.attrib.get("r") or "0")
        if row_num <= 0:
            continue
        max_row = max(max_row, row_num)
        row_map = rows_map.setdefault(row_num, {})
        for cell in row.findall(f"{ns}c"):
            ref = cell.attrib.get("r") or ""
            col = _column_number(ref)
            if col <= 0:
                continue
            max_col = max(max_col, col)
            cell_type = cell.attrib.get("t")
            value = ""
            if cell_type == "s":
                node = cell.find(f"{ns}v")
                if node is not None and (node.text or "").isdigit():
                    idx = int(node.text or "0")
                    value = shared[idx] if 0 <= idx < len(shared) else ""
            elif cell_type == "inlineStr":
                raw = "".join(node.text or "" for node in cell.iter(f"{ns}t"))
                value = _safe_cell_text(raw)
            elif cell_type == "str":
                node = cell.find(f"{ns}v")
                value = _safe_cell_text(node.text or "") if node is not None else ""
            else:
                # Numeric/date/formula cached results are deliberately ignored.
                value = ""
            row_map[col] = value

    rows = [
        [rows_map.get(row_num, {}).get(col, "") for col in range(1, max_col + 1)]
        for row_num in range(1, max_row + 1)
    ]

    merge_cells = root.find(f"{ns}mergeCells")
    if merge_cells is not None:
        for merge in merge_cells.findall(f"{ns}mergeCell"):
            ref = merge.attrib.get("ref") or ""
            if ":" not in ref:
                continue
            start, end = ref.split(":", 1)
            sr, sc = _row_number(start), _column_number(start)
            er, ec = _row_number(end), _column_number(end)
            if not (sr and sc and er and ec and sr <= len(rows) and sc <= len(rows[sr - 1])):
                continue
            parent = rows[sr - 1][sc - 1]
            for rr in range(sr, min(er, len(rows)) + 1):
                for cc in range(sc, min(ec, max_col) + 1):
                    if not rows[rr - 1][cc - 1]:
                        rows[rr - 1][cc - 1] = parent
    return rows


def _inventory_xlsx(body: bytes) -> dict[str, Any]:
    if not body.startswith(b"PK"):
        raise GlobalStop("unexpected_xlsx_format")

    containers: list[tuple[str, list[list[str]]]] = []
    with zipfile.ZipFile(io.BytesIO(body), "r") as archive:
        shared = _shared_strings_safe(archive)
        sheet_names = sorted(
            name
            for name in archive.namelist()
            if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name)
        )
        for sheet_name in sheet_names:
            rows = _sheet_rows_safe(archive.read(sheet_name), shared)
            containers.append((sheet_name, rows))

    inventory, candidate_count = _inventory_resource_containers(containers)
    return {
        "transport_status": "passed",
        "semantic_status": "evaluated",
        "candidate_count": candidate_count,
        "containers": inventory,
        "candidate_context_truncated": any(
            candidate.get("truncated") is True
            for container in inventory
            for candidate in container.get("candidates", [])
        ),
    }


def run_preflight() -> dict[str, Any]:
    user_agent = _validate_authorization_and_dispatch()
    budget = RequestBudget()
    resources: list[dict[str, Any]] = []

    for path, kind in ((HTML_PATH, "html"), (XLSX_PATH, "xlsx")):
        transport, body = _request_once(path, user_agent, budget)
        if transport == "transport_dns_failure":
            resources.append(
                {
                    "resource_path": path,
                    "transport_status": "failed",
                    "semantic_status": "not_evaluated",
                    "candidate_count": 0,
                    "transport_reason": "transport_dns_failure",
                }
            )
            continue

        assert body is not None
        result = _inventory_html(body) if kind == "html" else _inventory_xlsx(body)
        result["resource_path"] = path
        resources.append(result)
        del body

    evaluated = sum(1 for item in resources if item.get("semantic_status") == "evaluated")
    if evaluated == 2:
        status = "completed"
    elif evaluated == 1:
        status = "partial_transport"
    else:
        status = "transport_not_evaluated"

    return {
        "status": status,
        "issue": ISSUE,
        "design_version": 5,
        "request_attempt_count": budget.count,
        "request_budget": 2,
        "economic_observation_count": 0,
        "identifier_value_count": 0,
        "resources": resources,
        "full_historical_reconstruction": False,
        "candidate_score_computed": False,
        "component_zscores_computed": False,
        "component_contributions_computed": False,
        "research_ledger_modified": False,
        "public_artifacts_modified": False,
        "production_modified": False,
    }


def main() -> int:
    try:
        report = run_preflight()
    except GlobalStop as exc:
        print(
            json.dumps(
                {
                    "status": "fail_closed",
                    "issue": ISSUE,
                    "design_version": 5,
                    "global_stop_reason": str(exc),
                    "economic_observation_count": 0,
                    "identifier_value_count": 0,
                    "full_historical_reconstruction": False,
                    "candidate_score_computed": False,
                    "research_ledger_modified": False,
                    "public_artifacts_modified": False,
                    "production_modified": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
