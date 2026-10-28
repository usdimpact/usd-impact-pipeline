#!/usr/bin/env python3
"""Owner-authorized Issue #258 WPU0561 ambiguity diagnostics.

Python standard library only. The runner performs at most one GET attempt per
fixed resource, never follows redirects, never retries, never persists response
bodies, and never extracts or emits economic values.
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
USER_AGENT = "USD-Impact-Score-v2.1F-WPU0561-ambiguity-diagnostics/1.0 (contact: support@usd-impact.com)"
HTML_PATH = "/news.release/archives/ppi_05152013.htm"
XLSX_PATH = "/ppi/detailed-report/ppi-detailed-report-april-2026.xlsx"
FIXED_RESOURCES = [HTML_PATH, XLSX_PATH]
MAX_RESPONSE_BYTES = 50 * 1024 * 1024

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

    if design.get("version") != 3 or design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 frozen design changed")
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
    for field in (
        "response_body_ephemeral_retrieval",
        "ambiguity_diagnostics_preflight",
        "numeric_identifier_field_read",
    ):
        if auth.get(field) is not True:
            raise RuntimeError(f"{field} must be authorized")
    for field in (
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
    if dispatch.get("phase") != "bls_wpu0561_ambiguity_diagnostics_preflight":
        raise RuntimeError("Issue #258 dispatch phase changed")
    if dispatch.get("issue") != ISSUE:
        raise RuntimeError("Issue #258 dispatch issue changed")
    if dispatch.get("request_budget") != 2:
        raise RuntimeError("Issue #258 dispatch budget changed")
    if dispatch.get("max_economic_observations_total") != 0:
        raise RuntimeError("Issue #258 dispatch economic observation budget changed")
    if dispatch.get("fixed_resources") != FIXED_RESOURCES:
        raise RuntimeError("Issue #258 dispatch resources changed")
    if dispatch.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if contract.get("state") != "ambiguity_diagnostics_authorized":
        raise RuntimeError("Issue #258 execution contract is not dispatched-active")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("Issue #258 active receipt must be expected")
    if contract.get("dispatch_marker_expected_now") is not True:
        raise RuntimeError("Issue #258 dispatch marker must be expected")
    current = contract.get("current_state", {})
    for field in (
        "response_body_ephemeral_retrieval_authorized",
        "ambiguity_diagnostics_preflight_authorized",
        "numeric_identifier_field_read_authorized",
    ):
        if current.get(field) is not True:
            raise RuntimeError(f"{field} must be true")
    for field in (
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


def _sanitize_non_economic_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if not value:
        return ""
    # Keep words and punctuation needed for structural semantics while
    # redacting every numeric token. Identifier values are restored only in a
    # proven identifier column on a Crude petroleum candidate row.
    return re.sub(r"(?<![A-Za-z])\d+(?:[.,]\d+)?(?![A-Za-z])", "<num>", value)


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
    url = f"https://{HOST}{path}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "*/*",
            "Connection": "close",
        },
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


class _SanitizedHTMLTables(HTMLParser):
    def __init__(self, *, targets: set[tuple[int, int, int]] | None = None) -> None:
        super().__init__(convert_charrefs=True)
        self.targets = targets or set()
        self.capture_targets = targets is not None
        self.table_depth = 0
        self.table_index = 0
        self.row_index = 0
        self.current_row: list[str] | None = None
        self.current_cell_parts: list[str] | None = None
        self.current_cell_start_col = 0
        self.current_colspan = 1
        self.tables: list[list[list[str]]] = []
        self.target_values: dict[tuple[int, int, int], str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table":
            self.table_depth += 1
            if self.table_depth == 1:
                self.table_index += 1
                self.row_index = 0
                if not self.capture_targets:
                    self.tables.append([])
        elif self.table_depth == 1 and tag == "tr":
            self.row_index += 1
            self.current_row = []
        elif self.table_depth == 1 and tag in {"th", "td"} and self.current_row is not None:
            self.current_cell_parts = []
            self.current_cell_start_col = len(self.current_row) + 1
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
            if self.capture_targets:
                for offset in range(self.current_colspan):
                    key = (self.table_index, self.row_index, self.current_cell_start_col + offset)
                    if key in self.targets:
                        self.target_values[key] = raw
            else:
                sanitized = _sanitize_non_economic_text(raw)
                for _ in range(self.current_colspan):
                    assert self.current_row is not None
                    self.current_row.append(sanitized)
            self.current_cell_parts = None
        elif self.table_depth == 1 and tag == "tr":
            if not self.capture_targets and self.current_row is not None:
                self.tables[self.table_index - 1].append(self.current_row)
            self.current_row = None
        elif tag == "table" and self.table_depth:
            self.table_depth -= 1


def _candidate_identifier_targets(rows: list[list[str]]) -> set[tuple[int, int]]:
    targets: set[tuple[int, int]] = set()
    anchors = diagnostic.find_header_anchors(rows)
    for index, (_header_start, header_end, _paths, roles) in enumerate(anchors):
        identifier_columns = [column for column, role in roles.items() if role == "identifier"]
        if len(identifier_columns) != 1:
            continue
        identifier_column = identifier_columns[0]
        next_start = anchors[index + 1][0] if index + 1 < len(anchors) else None
        end_row = (next_start - 1) if next_start is not None else len(rows)
        for row_number in range(header_end + 1, end_row + 1):
            row = rows[row_number - 1]
            if any(re.search(r"\bCrude\s+petroleum\b", cell, re.IGNORECASE) for cell in row):
                targets.add((row_number, identifier_column))
    return targets


def _block_to_dict(container: str, block: diagnostic.LocalBlock) -> dict[str, Any]:
    return {
        "container": container,
        "header_stack": {
            "start_row": block.header_start_row,
            "end_row": block.header_end_row,
        },
        "candidate_block": {
            "start_row": block.start_row,
            "end_row": block.end_row,
        },
        "header_paths": {str(k): list(v) for k, v in sorted(block.header_paths.items())},
        "roles": {str(k): v for k, v in sorted(block.roles.items())},
        "revision_context_labels": list(block.revision_context_labels),
        "candidate_rows": list(block.mapped_candidate_rows),
        "candidate_count": len(block.mapped_candidate_rows),
        "normalized_identifier": "0561" if block.identity_status == "proven" else None,
        "identity_status": block.identity_status,
        "block_status": block.block_status,
        "field_status": block.field_status,
        "release_context_status": block.release_context_status,
        "reason_codes": list(block.reason_codes),
    }


def _diagnose_html(body: bytes) -> dict[str, Any]:
    text = body.decode("utf-8", errors="replace")
    first = _SanitizedHTMLTables()
    first.feed(text)

    targets: set[tuple[int, int, int]] = set()
    for table_index, rows in enumerate(first.tables, start=1):
        for row_number, column in _candidate_identifier_targets(rows):
            targets.add((table_index, row_number, column))

    targeted = _SanitizedHTMLTables(targets=targets)
    targeted.feed(text)

    containers: list[dict[str, Any]] = []
    aggregate: dict[str, int] = {}
    for table_index, rows in enumerate(first.tables, start=1):
        for row_number, column in _candidate_identifier_targets(rows):
            key = (table_index, row_number, column)
            raw = targeted.target_values.get(key, "")
            canonical = diagnostic.normalize_identifier(raw)
            while len(rows[row_number - 1]) < column:
                rows[row_number - 1].append("")
            rows[row_number - 1][column - 1] = "0561" if canonical == "0561" else "<identifier-not-0561>"

        blocks = diagnostic.diagnose_local_blocks(rows, source_context="archived_original_release")
        if not blocks:
            continue
        summary = diagnostic.resource_reason_summary(blocks)
        for reason, count in summary.items():
            aggregate[reason] = aggregate.get(reason, 0) + count
        containers.append(
            {
                "container": f"table {table_index}",
                "blocks": [_block_to_dict(f"table {table_index}", block) for block in blocks],
                "reason_summary": summary,
            }
        )

    return {
        "transport_status": "passed",
        "semantic_status": "evaluated",
        "container_count": len(containers),
        "containers": containers,
        "reason_summary": aggregate or {"no_local_header_anchor": 1},
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


def _shared_strings_sanitized(archive: zipfile.ZipFile) -> list[str]:
    try:
        data = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(data)
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    output: list[str] = []
    for si in root.findall(f"{ns}si"):
        raw = "".join(node.text or "" for node in si.iter(f"{ns}t"))
        output.append(_sanitize_non_economic_text(raw))
    return output


def _shared_string_raw_at(archive: zipfile.ZipFile, index: int) -> str:
    try:
        data = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return ""
    root = ET.fromstring(data)
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    for current, si in enumerate(root.findall(f"{ns}si")):
        if current == index:
            return "".join(node.text or "" for node in si.iter(f"{ns}t"))
    return ""


def _sheet_rows_sanitized(sheet_data: bytes, shared: list[str]) -> tuple[list[list[str]], list[str]]:
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
                value = _sanitize_non_economic_text(
                    "".join(node.text or "" for node in cell.iter(f"{ns}t"))
                )
            elif cell_type == "str":
                node = cell.find(f"{ns}v")
                value = _sanitize_non_economic_text(node.text or "") if node is not None else ""
            else:
                # Numeric/date/formula cached results are deliberately not read.
                value = "<numeric-redacted>"
            row_map[col] = value

    rows = [
        [rows_map.get(row_num, {}).get(col, "") for col in range(1, max_col + 1)]
        for row_num in range(1, max_row + 1)
    ]

    merges: list[str] = []
    merge_cells = root.find(f"{ns}mergeCells")
    if merge_cells is not None:
        for merge in merge_cells.findall(f"{ns}mergeCell"):
            ref = merge.attrib.get("ref") or ""
            if not ref or ":" not in ref:
                continue
            merges.append(ref)
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
    return rows, merges


def _target_identifier_values_xlsx(
    archive: zipfile.ZipFile,
    sheet_data: bytes,
    targets: set[tuple[int, int]],
) -> dict[tuple[int, int], str]:
    root = ET.fromstring(sheet_data)
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    output: dict[tuple[int, int], str] = {}
    for row in root.iter(f"{ns}row"):
        row_num = int(row.attrib.get("r") or "0")
        for cell in row.findall(f"{ns}c"):
            ref = cell.attrib.get("r") or ""
            col = _column_number(ref)
            key = (row_num, col)
            if key not in targets:
                continue
            cell_type = cell.attrib.get("t")
            raw = ""
            if cell_type == "s":
                node = cell.find(f"{ns}v")
                if node is not None and (node.text or "").isdigit():
                    raw = _shared_string_raw_at(archive, int(node.text or "0"))
            elif cell_type == "inlineStr":
                raw = "".join(node.text or "" for node in cell.iter(f"{ns}t"))
            else:
                node = cell.find(f"{ns}v")
                raw = node.text or "" if node is not None else ""
            output[key] = "0561" if diagnostic.normalize_identifier(raw) == "0561" else "<identifier-not-0561>"
    return output


def _diagnose_xlsx(body: bytes) -> dict[str, Any]:
    if not body.startswith(b"PK"):
        raise GlobalStop("unexpected_xlsx_format")

    containers: list[dict[str, Any]] = []
    aggregate: dict[str, int] = {}
    with zipfile.ZipFile(io.BytesIO(body), "r") as archive:
        shared = _shared_strings_sanitized(archive)
        sheet_names = sorted(
            name
            for name in archive.namelist()
            if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name)
        )
        for sheet_name in sheet_names:
            sheet_data = archive.read(sheet_name)
            rows, merges = _sheet_rows_sanitized(sheet_data, shared)
            targets = _candidate_identifier_targets(rows)
            target_values = _target_identifier_values_xlsx(archive, sheet_data, targets)
            for (row_number, column), canonical in target_values.items():
                if 1 <= row_number <= len(rows):
                    while len(rows[row_number - 1]) < column:
                        rows[row_number - 1].append("")
                    rows[row_number - 1][column - 1] = canonical

            blocks = diagnostic.diagnose_local_blocks(rows, source_context="detailed_report")
            if not blocks:
                continue
            summary = diagnostic.resource_reason_summary(blocks)
            for reason, count in summary.items():
                aggregate[reason] = aggregate.get(reason, 0) + count
            containers.append(
                {
                    "container": sheet_name,
                    "merge_range_count": len(merges),
                    "blocks": [_block_to_dict(sheet_name, block) for block in blocks],
                    "reason_summary": summary,
                }
            )

    return {
        "transport_status": "passed",
        "semantic_status": "evaluated",
        "container_count": len(containers),
        "containers": containers,
        "reason_summary": aggregate or {"no_local_header_anchor": 1},
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
                    "reason_summary": {"transport_dns_failure": 1},
                }
            )
            continue

        assert body is not None
        result = _diagnose_html(body) if kind == "html" else _diagnose_xlsx(body)
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
        "request_attempt_count": budget.count,
        "request_budget": 2,
        "economic_observation_count": 0,
        "max_economic_observations_total": 0,
        "normalized_identifier": "0561",
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
                    "global_stop_reason": str(exc),
                    "economic_observation_count": 0,
                    "max_economic_observations_total": 0,
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
