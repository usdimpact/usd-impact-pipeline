#!/usr/bin/env python3
"""Fail-closed representative WPU0561 index-level preflight.

Current repository state is design-only/HOLD. A future live run requires a new
explicit owner authorization under Issue #252, an active receipt, a separately
reviewed dispatch marker, and an activated workflow.
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
REQUEST_BUDGET = 2
MAX_BODY_BYTES = 64 * 1024 * 1024

HTML_PATH = "/news.release/archives/ppi_05152013.htm"
XLSX_PATH = "/ppi/detailed-report/ppi-detailed-report-april-2026.xlsx"
FIXED_RESOURCES = [HTML_PATH, XLSX_PATH]

ACTIVE_RECEIPT = (
    ROOT / "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-authorization.json"
)
DISPATCH = (
    ROOT / "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-dispatch.json"
)
CONTRACT = (
    ROOT / "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-execution-contract.json"
)

USER_AGENT_RE = re.compile(
    r"^USD-Impact-Score-v2\.1F-WPU0561-representative-index/1\.0 \(contact: .+\)$"
)
IDENTIFIER_HEADERS = ("commodity code", "series code", "series id", "item code")
DESCRIPTION_HEADERS = ("commodity", "item", "description")
REVISION_CONTEXT_TERMS = ("preliminary", "final", "revised", "corrected")
CHALLENGE_MARKERS = (
    "access denied",
    "verify you are human",
    "captcha",
    "request blocked",
    "automated request blocked",
)


class RequestBudget:
    def __init__(self) -> None:
        self.count = 0

    def consume(self) -> None:
        if self.count >= REQUEST_BUDGET:
            raise RuntimeError("representative-index request budget exceeded")
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
        raise RuntimeError("v2.1F representative-index authorization is not active")

    receipt = _load(ACTIVE_RECEIPT)
    dispatch = _load(DISPATCH)
    contract = _load(CONTRACT)

    if receipt.get("decision_status") != "approved":
        raise RuntimeError("representative-index receipt is not approved")
    if receipt.get("issue") != "https://github.com/usdimpact/usd-impact-pipeline/issues/252":
        raise RuntimeError("representative-index issue changed")
    if receipt.get("execution_scope") != "bls_wpu0561_representative_index_preflight_only":
        raise RuntimeError("representative-index scope changed")
    if receipt.get("request_budget") != 2:
        raise RuntimeError("request budget changed")
    if receipt.get("max_observations_total") != 2:
        raise RuntimeError("observation budget changed")
    if receipt.get("max_observations_per_resource") != 1:
        raise RuntimeError("per-resource observation budget changed")
    if receipt.get("fixed_resources") != FIXED_RESOURCES:
        raise RuntimeError("fixed resource set changed")
    if receipt.get("allowed_host") != HOST:
        raise RuntimeError("allowed host changed")

    user_agent = receipt.get("contact_user_agent")
    if not isinstance(user_agent, str) or not USER_AGENT_RE.fullmatch(user_agent):
        raise RuntimeError("contactable project User-Agent is missing or invalid")

    auth = receipt.get("authorizations", {})
    for field in (
        "response_body_ephemeral_retrieval",
        "representative_index_value_read",
        "representative_index_preflight",
    ):
        if auth.get(field) is not True:
            raise RuntimeError(f"{field} is not authorized")
    for field in (
        "full_historical_reconstruction",
        "candidate_score_computation",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if contract.get("state") != "representative_index_preflight_authorized":
        raise RuntimeError("execution contract is not active")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("active receipt is not expected")
    if contract.get("dispatch_marker_expected_now") is not True:
        raise RuntimeError("dispatch is not expected")

    if dispatch.get("state") != "approved_dispatch":
        raise RuntimeError("dispatch marker is invalid")
    if dispatch.get("phase") != "bls_wpu0561_representative_index_preflight":
        raise RuntimeError("dispatch phase changed")
    if dispatch.get("request_budget") != 2:
        raise RuntimeError("dispatch request budget changed")
    if dispatch.get("max_observations_total") != 2:
        raise RuntimeError("dispatch observation budget changed")
    if dispatch.get("fixed_resources") != FIXED_RESOURCES:
        raise RuntimeError("dispatch resources changed")
    if dispatch.get("full_historical_reconstruction_authorized") is not False:
        raise RuntimeError("full historical reconstruction must remain forbidden")
    if dispatch.get("candidate_score_computation_authorized") is not False:
        raise RuntimeError("candidate Score must remain forbidden")
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
            raise RuntimeError("representative-index preflight rejects redirects")
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


def _header_role(value: str) -> str | None:
    normalized = _normalize_header(value)
    identifier = any(term in normalized for term in IDENTIFIER_HEADERS)
    percent_change = (
        "percent" in normalized
        or "%" in normalized
        or "change" in normalized
    )
    index_level = "index" in normalized and not percent_change
    description = any(term in normalized for term in DESCRIPTION_HEADERS)

    if identifier and (percent_change or index_level):
        return "ambiguous"
    if identifier:
        return "identifier"
    if percent_change:
        return "percent_change"
    if index_level:
        return "index_level"
    if description:
        return "description"
    return None


def _normalize_identifier(value: str) -> str | None:
    compact = re.sub(r"\s+", "", value).upper()
    if compact == "WPU0561":
        return "0561"
    if compact in {"05-61", "0561", "561"}:
        return "0561"
    return None


def _parse_numeric(value: str) -> str | None:
    compact = value.strip().replace(",", "")
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", compact):
        return None
    return compact


def _revision_context_labels(rows: list[list[str]]) -> list[str]:
    labels: set[str] = set()
    for row in rows:
        for cell in row:
            normalized = _normalize_header(cell)
            for term in REVISION_CONTEXT_TERMS:
                if term in normalized:
                    labels.add(term)
    return sorted(labels)


def _classify_rows(
    rows: list[list[str]],
    *,
    container: str,
    source_context: str,
) -> dict[str, object]:
    roles: dict[int, str] = {}
    headers: list[dict[str, object]] = []
    for row_number, row in enumerate(rows, start=1):
        for column, text in enumerate(row, start=1):
            role = _header_role(text)
            if role is None:
                continue
            prior = roles.get(column)
            if prior is not None and prior != role:
                roles[column] = "ambiguous"
            else:
                roles[column] = role
            headers.append({
                "container": container,
                "row": row_number,
                "column": column,
                "header": re.sub(r"\s+", " ", text).strip(),
                "role": role,
            })

    identifier_columns = sorted(c for c, r in roles.items() if r == "identifier")
    index_columns = sorted(c for c, r in roles.items() if r == "index_level")
    percent_columns = sorted(c for c, r in roles.items() if r == "percent_change")
    ambiguous_columns = sorted(c for c, r in roles.items() if r == "ambiguous")

    revision_context_labels = _revision_context_labels(rows)

    mapped_rows: list[tuple[int, list[str]]] = []
    for row_number, row in enumerate(rows, start=1):
        if not any(re.search(r"\bCrude\s+petroleum\b", cell, re.IGNORECASE) for cell in row):
            continue
        identifiers = set()
        for column in identifier_columns:
            if column <= len(row):
                normalized = _normalize_identifier(row[column - 1])
                if normalized:
                    identifiers.add(normalized)
        if "0561" in identifiers:
            mapped_rows.append((row_number, row))

    observation = None
    ambiguity = None
    if source_context == "archived_original_release":
        revision_context_status = "archived_release_path"
    elif source_context == "detailed_report":
        if len(revision_context_labels) == 1:
            revision_context_status = revision_context_labels[0]
        elif len(revision_context_labels) == 0:
            revision_context_status = "missing"
        else:
            revision_context_status = "conflicting"
    else:
        revision_context_status = "unknown"

    if revision_context_status in {"missing", "conflicting", "unknown"}:
        ambiguity = "ambiguous_revision_context"
    elif ambiguous_columns:
        ambiguity = "ambiguous_column_semantics"
    elif len(mapped_rows) != 1:
        ambiguity = "mapped_row_count_not_one"
    elif len(index_columns) != 1:
        ambiguity = "index_level_column_count_not_one"
    else:
        row_number, row = mapped_rows[0]
        column = index_columns[0]
        candidate = row[column - 1] if column <= len(row) else ""
        numeric = _parse_numeric(candidate)
        if numeric is None:
            ambiguity = "index_level_cell_not_numeric"
        else:
            observation = {
                "container": container,
                "row": row_number,
                "column": column,
                "normalized_identifier": "0561",
                "semantic": "original_release_index_level",
                "revision_context": revision_context_status,
                "value": numeric,
            }

    return {
        "headers": headers,
        "identifier_columns": identifier_columns,
        "index_level_columns": index_columns,
        "percent_change_columns": percent_columns,
        "ambiguous_columns": ambiguous_columns,
        "mapped_row_count": len(mapped_rows),
        "revision_context_labels": revision_context_labels,
        "revision_context_status": revision_context_status,
        "observation": observation,
        "ambiguity": ambiguity,
    }


def _extract_html_candidate(payload: bytes) -> dict[str, object]:
    parser = HtmlTableParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    parser.close()
    reports = [
        _classify_rows(
            table,
            container=f"table {index}",
            source_context="archived_original_release",
        )
        for index, table in enumerate(parser.tables, start=1)
        if table
    ]
    observations = [r["observation"] for r in reports if r.get("observation")]
    if len(observations) == 1:
        return {"status": "passed", "observation": observations[0], "reports": reports}
    return {"status": "ambiguous", "observation": None, "reports": reports}


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
    return [
        "".join(node.text or "" for node in item.findall(".//m:t", ns))
        for item in root.findall("m:si", ns)
    ]


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


def _xlsx_cell_value(cell: ET.Element, shared: list[str], ns: dict[str, str]) -> str:
    cell_type = cell.attrib.get("t")
    value = cell.find("m:v", ns)
    if cell_type == "s" and value is not None and value.text is not None:
        try:
            index = int(value.text)
        except ValueError:
            return ""
        return shared[index] if 0 <= index < len(shared) else ""
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//m:t", ns))
    return value.text if value is not None and value.text is not None else ""


def _extract_xlsx_candidate(payload: bytes) -> dict[str, object]:
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    reports: list[dict[str, object]] = []
    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        shared = _xlsx_shared_strings(archive)
        for sheet_name, sheet_path in _xlsx_sheet_map(archive):
            root = ET.fromstring(archive.read(sheet_path))
            rows: list[list[str]] = []
            for row in root.findall(".//m:row", ns):
                cells: dict[int, str] = {}
                for cell in row.findall("m:c", ns):
                    column = _column_number(cell.attrib.get("r", ""))
                    cells[column] = _xlsx_cell_value(cell, shared, ns)
                max_column = max(cells, default=0)
                rows.append([cells.get(i, "") for i in range(1, max_column + 1)])
            if rows:
                reports.append(
                    _classify_rows(
                        rows,
                        container=f"sheet {sheet_name}",
                        source_context="detailed_report",
                    )
                )

    observations = [r["observation"] for r in reports if r.get("observation")]
    if len(observations) == 1:
        return {"status": "passed", "observation": observations[0], "reports": reports}
    return {"status": "ambiguous", "observation": None, "reports": reports}


def run_preflight() -> dict[str, object]:
    user_agent = _validate_authorization_and_dispatch()
    budget = RequestBudget()

    html_meta, html_body = _request_once(HTML_PATH, budget=budget, user_agent=user_agent)
    html_result = _extract_html_candidate(html_body)
    del html_body

    xlsx_meta, xlsx_body = _request_once(XLSX_PATH, budget=budget, user_agent=user_agent)
    xlsx_result = _extract_xlsx_candidate(xlsx_body)
    del xlsx_body

    observations = [
        item["observation"]
        for item in (html_result, xlsx_result)
        if item.get("observation") is not None
    ]
    if len(observations) > 2:
        raise RuntimeError("representative observation budget exceeded")

    return {
        "status": (
            "passed"
            if html_result["status"] == "passed" and xlsx_result["status"] == "passed"
            else "ambiguous"
        ),
        "scope": "bls_wpu0561_representative_index_preflight_only",
        "request_count": budget.count,
        "resources": [html_meta, xlsx_meta],
        "html_result": html_result,
        "xlsx_result": xlsx_result,
        "observation_count": len(observations),
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
