#!/usr/bin/env python3
"""Fail-closed WPU0561 column-semantics preflight.

Current repository state is design-only/HOLD. A future live run requires a new
explicit owner authorization under Issue #244, an active receipt, a separate
dispatch marker, and workflow activation.

The parser may retain a numeric-looking cell only when a non-numeric header has
first classified that column as a commodity/series identifier field. Economic
index and percent-change values are never emitted, logged, or persisted.
"""

from __future__ import annotations

import http.client
import io
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOST = "www.bls.gov"
START = "2013-01-01"
END = "2026-10-23"
REQUEST_BUDGET = 2
MAX_BODY_BYTES = 64 * 1024 * 1024

HTML_PATH = "/news.release/archives/ppi_05152013.htm"
XLSX_PATH = "/ppi/detailed-report/ppi-detailed-report-april-2026.xlsx"
FIXED_RESOURCES = [HTML_PATH, XLSX_PATH]

ACTIVE_RECEIPT = (
    ROOT / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-authorization.json"
)
DISPATCH = (
    ROOT / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-dispatch.json"
)
CONTRACT = (
    ROOT / "governance/score-v2-1f-bls-wpu0561-column-semantics-preflight-execution-contract.json"
)

USER_AGENT_RE = re.compile(
    r"^USD-Impact-Score-v2\.1F-WPU0561-column-semantics/1\.0 \(contact: .+\)$"
)
IDENTIFIER_HEADERS = (
    "commodity code",
    "series code",
    "series id",
    "item code",
    "code",
)
DESCRIPTION_HEADERS = ("commodity", "item", "description")
ECONOMIC_HEADERS = ("index", "percent", "change", "value")
CHALLENGE_MARKERS = (
    "access denied",
    "verify you are human",
    "captcha",
    "request blocked",
    "automated request blocked",
)


class RequestBudget:
    def __init__(self, maximum: int = REQUEST_BUDGET) -> None:
        self.maximum = maximum
        self.count = 0

    def consume(self) -> None:
        if self.count >= self.maximum:
            raise RuntimeError("BLS column-semantics request budget exceeded")
        self.count += 1


class HtmlTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.current_table: list[list[str]] | None = None
        self.current_row: list[str] | None = None
        self.current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        lowered = tag.lower()
        if lowered == "table":
            self.current_table = []
        elif lowered == "tr" and self.current_table is not None:
            self.current_row = []
        elif lowered in {"td", "th"} and self.current_row is not None:
            self.current_cell = []

    def handle_data(self, data: str) -> None:
        if self.current_cell is not None:
            self.current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in {"td", "th"} and self.current_cell is not None and self.current_row is not None:
            self.current_row.append(" ".join(self.current_cell).strip())
            self.current_cell = None
        elif lowered == "tr" and self.current_row is not None and self.current_table is not None:
            self.current_table.append(self.current_row)
            self.current_row = None
        elif lowered == "table" and self.current_table is not None:
            self.tables.append(self.current_table)
            self.current_table = None


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def _validate_authorization_and_dispatch() -> str:
    if not ACTIVE_RECEIPT.exists() or not DISPATCH.exists():
        raise RuntimeError("v2.1F WPU0561 column-semantics authorization is not active")

    receipt = _load(ACTIVE_RECEIPT)
    dispatch = _load(DISPATCH)
    contract = _load(CONTRACT)

    if receipt.get("decision_status") != "approved":
        raise RuntimeError("column-semantics receipt is not approved")
    if receipt.get("issue") != "https://github.com/usdimpact/usd-impact-pipeline/issues/244":
        raise RuntimeError("column-semantics issue changed")
    if receipt.get("execution_scope") != "bls_wpu0561_column_semantics_preflight_only":
        raise RuntimeError("column-semantics scope changed")
    if receipt.get("data_window") != {"start": START, "end": END}:
        raise RuntimeError("column-semantics window changed")
    if receipt.get("request_budget") != REQUEST_BUDGET:
        raise RuntimeError("column-semantics request budget changed")
    if receipt.get("allowed_host") != HOST:
        raise RuntimeError("column-semantics host changed")
    if receipt.get("fixed_resources") != FIXED_RESOURCES:
        raise RuntimeError("column-semantics resource set changed")

    user_agent = receipt.get("contact_user_agent")
    if not isinstance(user_agent, str) or not USER_AGENT_RE.fullmatch(user_agent):
        raise RuntimeError("contactable project User-Agent is missing or invalid")

    auth = receipt.get("authorizations", {})
    for field in (
        "response_body_ephemeral_retrieval",
        "column_semantics_preflight",
        "numeric_identifier_field_read",
    ):
        if auth.get(field) is not True:
            raise RuntimeError(f"{field} is not authorized")
    for field in (
        "economic_value_extraction",
        "real_data_research",
        "full_historical_reconstruction",
        "candidate_score_computation",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if contract.get("state") != "column_semantics_preflight_authorized":
        raise RuntimeError("column-semantics execution contract is not active")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("active receipt is not expected")
    if contract.get("dispatch_marker_expected_now") is not True:
        raise RuntimeError("dispatch is not expected")
    if contract.get("request_budget") != REQUEST_BUDGET:
        raise RuntimeError("contract request budget changed")

    current = contract.get("current_state", {})
    for field in (
        "response_body_ephemeral_retrieval_authorized",
        "column_semantics_preflight_authorized",
        "numeric_identifier_field_read_authorized",
    ):
        if current.get(field) is not True:
            raise RuntimeError(f"{field} must be true")
    for field in (
        "economic_value_extraction_authorized",
        "real_data_research_authorized",
        "full_historical_reconstruction_authorized",
        "candidate_score_computation_authorized",
        "research_ledger_mutation_authorized",
        "public_artifact_replacement_authorized",
        "production_authorized",
    ):
        if current.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if dispatch.get("state") != "approved_dispatch":
        raise RuntimeError("column-semantics dispatch is invalid")
    if dispatch.get("phase") != "bls_wpu0561_column_semantics_preflight":
        raise RuntimeError("column-semantics dispatch phase changed")
    if dispatch.get("request_budget") != REQUEST_BUDGET:
        raise RuntimeError("column-semantics dispatch budget changed")
    if dispatch.get("fixed_resources") != FIXED_RESOURCES:
        raise RuntimeError("column-semantics dispatch resources changed")
    if dispatch.get("economic_value_extraction_authorized") is not False:
        raise RuntimeError("economic value extraction must remain forbidden")
    if dispatch.get("production_authorized") is not False:
        raise RuntimeError("Production must remain forbidden")

    activation_commit = contract.get("authorization_activation_merge_commit")
    if not isinstance(activation_commit, str) or len(activation_commit) != 40:
        raise RuntimeError("activation commit is not pinned")
    if dispatch.get("authorization_activation_merge_commit") != activation_commit:
        raise RuntimeError("dispatch is not pinned to activation")

    return user_agent


def _validate_request_path(path: str) -> None:
    if path not in FIXED_RESOURCES:
        raise RuntimeError("request is outside the two fixed BLS resources")


def _request_once(
    path: str,
    *,
    budget: RequestBudget,
    user_agent: str,
) -> tuple[dict[str, object], bytes]:
    _validate_request_path(path)
    budget.consume()
    connection = http.client.HTTPSConnection(HOST, timeout=45)
    try:
        connection.request("GET", path, headers={"User-Agent": user_agent})
        response = connection.getresponse()
        if 300 <= response.status < 400:
            raise RuntimeError("column-semantics preflight rejects redirects")
        if response.status in {401, 403, 429}:
            raise RuntimeError(f"BLS access-control stop: HTTP {response.status}")
        if response.status != 200:
            raise RuntimeError(f"BLS retrieval returned HTTP {response.status}")

        length = response.getheader("Content-Length")
        if length is not None and int(length) > MAX_BODY_BYTES:
            raise RuntimeError("BLS response body exceeds in-memory size limit")
        payload = response.read(MAX_BODY_BYTES + 1)
        if len(payload) > MAX_BODY_BYTES:
            raise RuntimeError("BLS response body exceeds in-memory size limit")

        content_type = (response.getheader("Content-Type") or "").lower()
        if path.endswith(".htm"):
            prefix = payload[:65536].decode("utf-8", errors="ignore").lower()
            if any(marker in prefix for marker in CHALLENGE_MARKERS):
                raise RuntimeError("BLS access challenge detected")
            if "html" not in content_type and "<html" not in prefix:
                raise RuntimeError("unexpected HTML response")
            fmt = "html"
        elif path.endswith(".xlsx"):
            if not payload.startswith(b"PK"):
                raise RuntimeError("unexpected XLSX signature")
            fmt = "xlsx"
        else:
            raise RuntimeError("unsupported fixed resource format")

        return {
            "method": "GET",
            "host": HOST,
            "path": path,
            "status": response.status,
            "format": fmt,
            "content_type": content_type.split(";", 1)[0],
        }, payload
    finally:
        connection.close()


def _normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _semantic_role(header: str) -> str | None:
    normalized = _normalize_header(header)
    if any(term in normalized for term in IDENTIFIER_HEADERS):
        return "identifier"
    if any(term in normalized for term in ECONOMIC_HEADERS):
        return "economic"
    if any(term in normalized for term in DESCRIPTION_HEADERS):
        return "description"
    return None


def _normalize_identifier(value: str) -> str | None:
    compact = re.sub(r"\s+", "", value).upper()
    if compact == "WPU0561":
        return "WPU0561"
    if compact == "05-61":
        return "0561"
    if compact == "0561":
        return "0561"
    if compact == "561":
        return "0561"
    return None


def _analyze_rows(rows: list[list[str]], *, container: str) -> dict[str, object]:
    header_evidence: list[dict[str, object]] = []
    identifier_columns: set[int] = set()
    description_columns: set[int] = set()
    economic_columns: set[int] = set()

    for row_number, row in enumerate(rows, start=1):
        for column_index, cell in enumerate(row, start=1):
            role = _semantic_role(cell)
            if role is None:
                continue
            header_evidence.append(
                {
                    "container": container,
                    "row": row_number,
                    "column": column_index,
                    "header": re.sub(r"\s+", " ", cell).strip(),
                    "role": role,
                }
            )
            if role == "identifier":
                identifier_columns.add(column_index)
            elif role == "description":
                description_columns.add(column_index)
            elif role == "economic":
                economic_columns.add(column_index)

    matches: list[dict[str, object]] = []
    for row_number, row in enumerate(rows, start=1):
        row_text = " ".join(row)
        if not re.search(r"\bCrude\s+petroleum\b", row_text, re.IGNORECASE):
            continue
        identifiers: set[str] = set()
        for column_index in identifier_columns:
            if column_index <= len(row):
                identifier = _normalize_identifier(row[column_index - 1])
                if identifier:
                    identifiers.add(identifier)
        if "05-61" in row_text:
            identifiers.add("0561")
        matches.append(
            {
                "container": container,
                "row": row_number,
                "identifiers": sorted(identifiers),
                "mapping_status": (
                    "mapped_to_0561" if "0561" in identifiers or "WPU0561" in identifiers
                    else "description_only"
                ),
            }
        )

    return {
        "headers": header_evidence,
        "identifier_columns": sorted(identifier_columns),
        "description_columns": sorted(description_columns),
        "economic_columns": sorted(economic_columns),
        "matches": matches,
    }


def _extract_html_semantics(payload: bytes) -> list[dict[str, object]]:
    parser = HtmlTableParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    parser.close()
    return [
        _analyze_rows(table, container=f"table {index}")
        for index, table in enumerate(parser.tables, start=1)
        if table
    ]


def _column_number(reference: str) -> int:
    letters = "".join(ch for ch in reference if ch.isalpha()).upper()
    value = 0
    for ch in letters:
        value = value * 26 + (ord(ch) - ord("A") + 1)
    return value


def _xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        payload = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(payload)
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    output: list[str] = []
    for item in root.findall("m:si", ns):
        output.append("".join(node.text or "" for node in item.findall(".//m:t", ns)))
    return output


def _xlsx_sheet_map(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    ns_main = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rel_ns = {"p": "http://schemas.openxmlformats.org/package/2006/relationships"}
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall("p:Relationship", rel_ns)
    }
    output: list[tuple[str, str]] = []
    for sheet in workbook.findall("m:sheets/m:sheet", ns_main):
        rel_id = sheet.attrib.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        )
        if not rel_id or rel_id not in targets:
            continue
        target = targets[rel_id].lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        output.append((sheet.attrib.get("name", "unnamed"), target))
    return output


def _xlsx_string(cell: ET.Element, shared: list[str], ns: dict[str, str]) -> str | None:
    cell_type = cell.attrib.get("t")
    if cell_type == "s":
        value = cell.find("m:v", ns)
        if value is None or value.text is None:
            return None
        try:
            index = int(value.text)
        except ValueError:
            return None
        return shared[index] if 0 <= index < len(shared) else None
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//m:t", ns))
    if cell_type == "str":
        value = cell.find("m:v", ns)
        return value.text if value is not None else None
    return None


def _extract_xlsx_semantics(payload: bytes) -> list[dict[str, object]]:
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    reports: list[dict[str, object]] = []
    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        shared = _xlsx_shared_strings(archive)
        for sheet_name, sheet_path in _xlsx_sheet_map(archive):
            root = ET.fromstring(archive.read(sheet_path))
            rows: list[dict[int, tuple[str | None, str | None, str | None]]] = []
            for row in root.findall(".//m:row", ns):
                cells: dict[int, tuple[str | None, str | None, str | None]] = {}
                for cell in row.findall("m:c", ns):
                    ref = cell.attrib.get("r", "")
                    column = _column_number(ref)
                    text = _xlsx_string(cell, shared, ns)
                    raw_node = cell.find("m:v", ns)
                    raw = raw_node.text if raw_node is not None else None
                    cells[column] = (text, raw, cell.attrib.get("t"))
                rows.append(cells)

            identifier_columns: set[int] = set()
            description_columns: set[int] = set()
            economic_columns: set[int] = set()
            headers: list[dict[str, object]] = []

            for row_number, cells in enumerate(rows, start=1):
                for column, (text, _raw, _cell_type) in cells.items():
                    if text is None:
                        continue
                    role = _semantic_role(text)
                    if role is None:
                        continue
                    headers.append(
                        {
                            "sheet": sheet_name,
                            "row": row_number,
                            "column": column,
                            "header": re.sub(r"\s+", " ", text).strip(),
                            "role": role,
                        }
                    )
                    if role == "identifier":
                        identifier_columns.add(column)
                    elif role == "description":
                        description_columns.add(column)
                    elif role == "economic":
                        economic_columns.add(column)

            matches: list[dict[str, object]] = []
            for row_number, cells in enumerate(rows, start=1):
                strings = [text for text, _raw, _type in cells.values() if text]
                if not any(re.search(r"\bCrude\s+petroleum\b", text, re.IGNORECASE) for text in strings):
                    continue
                identifiers: set[str] = set()
                identifier_types: list[dict[str, object]] = []
                for column in sorted(identifier_columns):
                    if column not in cells:
                        continue
                    text, raw, cell_type = cells[column]
                    candidate = text
                    if candidate is None and raw is not None and re.fullmatch(r"\d{1,8}", raw):
                        candidate = raw
                    if candidate is not None:
                        normalized = _normalize_identifier(candidate)
                        if normalized:
                            identifiers.add(normalized)
                            identifier_types.append(
                                {
                                    "column": column,
                                    "cell_type": cell_type or "numeric",
                                    "normalized_identifier": normalized,
                                }
                            )
                matches.append(
                    {
                        "sheet": sheet_name,
                        "row": row_number,
                        "identifiers": sorted(identifiers),
                        "identifier_fields": identifier_types,
                        "mapping_status": (
                            "mapped_to_0561" if "0561" in identifiers or "WPU0561" in identifiers
                            else "description_only"
                        ),
                    }
                )

            if headers or matches:
                reports.append(
                    {
                        "sheet": sheet_name,
                        "headers": headers,
                        "identifier_columns": sorted(identifier_columns),
                        "description_columns": sorted(description_columns),
                        "economic_columns": sorted(economic_columns),
                        "matches": matches,
                    }
                )
    return reports


def run_preflight() -> dict[str, object]:
    user_agent = _validate_authorization_and_dispatch()
    budget = RequestBudget()

    html_meta, html_body = _request_once(HTML_PATH, budget=budget, user_agent=user_agent)
    html_semantics = _extract_html_semantics(html_body)
    del html_body

    xlsx_meta, xlsx_body = _request_once(XLSX_PATH, budget=budget, user_agent=user_agent)
    xlsx_semantics = _extract_xlsx_semantics(xlsx_body)
    del xlsx_body

    if budget.count != REQUEST_BUDGET:
        raise RuntimeError("column-semantics preflight did not consume exact request budget")

    statuses = [
        match["mapping_status"]
        for report in html_semantics + xlsx_semantics
        for match in report.get("matches", [])
    ]
    mapped = any(status == "mapped_to_0561" for status in statuses)

    return {
        "status": "passed" if mapped else "ambiguous",
        "scope": "bls_wpu0561_column_semantics_preflight_only",
        "data_window": {"start": START, "end": END},
        "request_count": budget.count,
        "resources": [html_meta, xlsx_meta],
        "html_semantics": html_semantics,
        "xlsx_semantics": xlsx_semantics,
        "wpu0561_mapping_proven": mapped,
        "response_bodies_persisted": False,
        "economic_values_extracted": False,
        "economic_values_logged": False,
        "economic_values_persisted": False,
        "full_historical_reconstruction_performed": False,
        "candidate_score_computed": False,
        "research_ledger_modified": False,
        "public_artifacts_modified": False,
        "production_modified": False,
    }


def main() -> int:
    print(json.dumps(run_preflight(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
