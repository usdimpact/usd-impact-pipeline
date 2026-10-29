#!/usr/bin/env python3
"""Owner-authorized Issue #258 design-v8 container header-band inventory.

Python standard library only. Exactly one attempt is available for each fixed
resource. Redirects and retries are forbidden. Response bodies remain ephemeral.
All text is numeric-redacted before structural selection or persistence.
Identifier values and economic values are never read from numeric cells and are
never persisted in output.
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
USER_AGENT = "USD-Impact-Score-v2.1F-WPU0561-container-header-band/1.0 (contact: support@usd-impact.com)"
HTML_PATH = "/news.release/archives/ppi_05152013.htm"
XLSX_PATH = "/ppi/detailed-report/ppi-detailed-report-april-2026.xlsx"
FIXED_RESOURCES = [HTML_PATH, XLSX_PATH]
MAX_RESPONSE_BYTES = 50 * 1024 * 1024
MAX_HEADER_BAND_ROWS = 32
MAX_HEADER_BAND_CELLS = 128

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


class SemanticStop(RuntimeError):
    """A fail-closed semantic condition after the authorized fetches."""


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

    if design.get("version") != 8 or design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 frozen design v8 changed")

    exact = design.get("exact_label_candidate_policy", {})
    discriminator = design.get("xlsx_context_discriminator_policy", {})
    band = design.get("container_header_band_policy", {})
    if exact.get("expected_html_narrowing") != "3 -> 1":
        raise RuntimeError("v6 HTML prerequisite changed")
    if exact.get("expected_xlsx_narrowing") != "29 -> 2":
        raise RuntimeError("v6 XLSX prerequisite changed")
    if discriminator.get("expected_direct_commodity_survivors") != 1:
        raise RuntimeError("v6 direct-commodity prerequisite changed")
    if discriminator.get("row_number_as_selector") is not False:
        raise RuntimeError("row numbers must not be selection semantics")
    if band.get("candidate_row_as_selector") is not False:
        raise RuntimeError("candidate row must not be selection semantics")
    if band.get("inspect_top_rows") != MAX_HEADER_BAND_ROWS:
        raise RuntimeError("header-band row bound changed")
    if band.get("maximum_persisted_text_cells_per_selected_container") != MAX_HEADER_BAND_CELLS:
        raise RuntimeError("header-band cell bound changed")
    if band.get("identifier_values") != "forbidden":
        raise RuntimeError("identifier-value policy changed")
    if band.get("economic_values") != "forbidden":
        raise RuntimeError("economic-value policy changed")
    if band.get("response_body_persistence") is not False:
        raise RuntimeError("response-body persistence policy changed")

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
        raise RuntimeError("header-band preflight must be authorized")
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
    if dispatch.get("phase") != "bls_wpu0561_container_header_band_inventory_preflight":
        raise RuntimeError("Issue #258 dispatch phase changed")
    if dispatch.get("issue") != ISSUE:
        raise RuntimeError("Issue #258 dispatch issue changed")
    if dispatch.get("design_version") != 8:
        raise RuntimeError("Issue #258 dispatch design version changed")
    if dispatch.get("request_budget") != 2:
        raise RuntimeError("Issue #258 dispatch budget changed")
    if dispatch.get("max_economic_observations_total") != 0:
        raise RuntimeError("Issue #258 dispatch economic observation budget changed")
    if dispatch.get("fixed_resources") != FIXED_RESOURCES:
        raise RuntimeError("Issue #258 dispatch resources changed")
    if dispatch.get("inspect_top_rows") != MAX_HEADER_BAND_ROWS:
        raise RuntimeError("Issue #258 dispatch row bound changed")
    if dispatch.get("maximum_persisted_text_cells_per_selected_container") != MAX_HEADER_BAND_CELLS:
        raise RuntimeError("Issue #258 dispatch cell bound changed")
    if dispatch.get("identifier_value_read_authorized") is not False:
        raise RuntimeError("identifier value reads must remain forbidden")
    if dispatch.get("economic_value_read_authorized") is not False:
        raise RuntimeError("economic value reads must remain forbidden")
    if dispatch.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if contract.get("state") != "ambiguity_diagnostics_v8_container_header_band_authorized":
        raise RuntimeError("Issue #258 execution contract is not dispatched-active")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("Issue #258 active receipt must be expected")
    if contract.get("dispatch_marker_expected_now") is not True:
        raise RuntimeError("Issue #258 dispatch marker must be expected")
    current = contract.get("current_state", {})
    if current.get("response_body_ephemeral_retrieval_authorized") is not True:
        raise RuntimeError("ephemeral retrieval must be active")
    if current.get("ambiguity_diagnostics_preflight_authorized") is not True:
        raise RuntimeError("header-band preflight must be active")
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


def _parse_html_containers(body: bytes) -> list[tuple[str, list[list[str]]]]:
    parser = _ContextHTMLTables()
    parser.feed(body.decode("utf-8", errors="replace"))
    parser.close()
    return [(f"table {index}", rows) for index, rows in enumerate(parser.tables, start=1)]


def _parse_xlsx_containers(body: bytes) -> list[tuple[str, list[list[str]]]]:
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
            containers.append((sheet_name, _sheet_rows_safe(archive.read(sheet_name), shared)))
    return containers


def _exact_candidates(
    containers: list[tuple[str, list[list[str]]]],
) -> list[tuple[str, int, list[list[str]]]]:
    output: list[tuple[str, int, list[list[str]]]] = []
    for container_name, rows in containers:
        for row_number in diagnostic.exact_target_rows(rows):
            output.append((container_name, row_number, rows))
    return output


def _select_v8_containers(
    html_containers: list[tuple[str, list[list[str]]]],
    xlsx_containers: list[tuple[str, list[list[str]]]],
) -> tuple[tuple[str, list[list[str]]], tuple[str, list[list[str]]]]:
    html_candidates = _exact_candidates(html_containers)
    if len(html_candidates) != 1:
        raise SemanticStop("v6_html_exact_label_prerequisite_failed")

    xlsx_candidates = _exact_candidates(xlsx_containers)
    if len(xlsx_candidates) != 2:
        raise SemanticStop("v6_xlsx_exact_label_prerequisite_failed")

    classified: list[tuple[str, int, list[list[str]], str]] = []
    for container_name, row_number, rows in xlsx_candidates:
        status = str(
            diagnostic.classify_exact_target_context(rows, row_number)["context_status"]
        )
        classified.append((container_name, row_number, rows, status))

    direct = [
        item
        for item in classified
        if item[3] == "commodity_unprocessed_nonfood_context"
    ]
    stage = [
        item
        for item in classified
        if item[3] == "stage_intermediate_demand_context"
    ]
    if len(direct) != 1 or len(stage) != 1:
        raise SemanticStop("v6_xlsx_context_discriminator_prerequisite_failed")

    html_name, _html_row, html_rows = html_candidates[0]
    xlsx_name, _xlsx_row, xlsx_rows, _status = direct[0]
    return (html_name, html_rows), (xlsx_name, xlsx_rows)


def _header_band_result(
    resource_path: str,
    selected: tuple[str, list[list[str]]],
) -> dict[str, Any]:
    container_name, rows = selected
    band = diagnostic.container_header_band_inventory(
        rows,
        max_rows=MAX_HEADER_BAND_ROWS,
        max_cells=MAX_HEADER_BAND_CELLS,
    )
    return {
        "resource_path": resource_path,
        "container": container_name,
        "band_start_row": band["band_start_row"],
        "band_end_row": band["band_end_row"],
        "cells": band["cells"],
        "blank_rows": band["blank_rows"],
        "recognized_header_role_rows": band["recognized_header_role_rows"],
        "first_nonempty_row": band["first_nonempty_row"],
        "last_nonempty_row": band["last_nonempty_row"],
        "truncated": band["truncated"],
    }


def run_preflight() -> dict[str, Any]:
    user_agent = _validate_authorization_and_dispatch()
    budget = RequestBudget()
    transport: list[dict[str, Any]] = []
    bodies: dict[str, bytes] = {}

    for path in FIXED_RESOURCES:
        status, body = _request_once(path, user_agent, budget)
        if status == "transport_dns_failure":
            transport.append(
                {
                    "resource_path": path,
                    "transport_status": "failed",
                    "semantic_status": "not_evaluated",
                    "transport_reason": "transport_dns_failure",
                }
            )
            continue
        assert body is not None
        transport.append(
            {
                "resource_path": path,
                "transport_status": "passed",
                "semantic_status": "pending",
            }
        )
        bodies[path] = body

    if set(bodies) != set(FIXED_RESOURCES):
        for item in transport:
            if item.get("semantic_status") == "pending":
                item["semantic_status"] = "not_evaluated"
        return {
            "status": "partial_transport",
            "issue": ISSUE,
            "design_version": 8,
            "request_attempt_count": budget.count,
            "transport": transport,
            "selected_containers": [],
            "identifier_values_retained": False,
            "economic_values_retained": False,
            "full_historical_reconstruction": False,
            "candidate_score_computed": False,
            "research_ledger_modified": False,
            "public_artifacts_modified": False,
            "production_modified": False,
        }

    html_containers = _parse_html_containers(bodies[HTML_PATH])
    xlsx_containers = _parse_xlsx_containers(bodies[XLSX_PATH])
    del bodies

    try:
        html_selected, xlsx_selected = _select_v8_containers(
            html_containers,
            xlsx_containers,
        )
    except SemanticStop as exc:
        for item in transport:
            item["semantic_status"] = "evaluated_fail_closed"
        return {
            "status": "ambiguous",
            "issue": ISSUE,
            "design_version": 8,
            "request_attempt_count": budget.count,
            "transport": transport,
            "semantic_stop_reason": str(exc),
            "selected_containers": [],
            "identifier_values_retained": False,
            "economic_values_retained": False,
            "full_historical_reconstruction": False,
            "candidate_score_computed": False,
            "research_ledger_modified": False,
            "public_artifacts_modified": False,
            "production_modified": False,
        }

    selected = [
        _header_band_result(HTML_PATH, html_selected),
        _header_band_result(XLSX_PATH, xlsx_selected),
    ]
    for item in transport:
        item["semantic_status"] = "evaluated"

    return {
        "status": "completed",
        "issue": ISSUE,
        "design_version": 8,
        "request_attempt_count": budget.count,
        "transport": transport,
        "selected_containers": selected,
        "identifier_values_retained": False,
        "economic_values_retained": False,
        "full_historical_reconstruction": False,
        "candidate_score_computed": False,
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
                    "design_version": 8,
                    "global_stop_reason": str(exc),
                    "identifier_values_retained": False,
                    "economic_values_retained": False,
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
