#!/usr/bin/env python3
"""Fail-closed BLS WPU0561 row-presence preflight for Score v2.1F.

Design v2 uses exactly two fixed official BLS resources:
- the archived May 15, 2013 HTML release for April 2013;
- the April 2026 Detailed Report XLSX.

Current repository state is design-only/HOLD. A future live run requires a new
explicit owner authorization under Issue #236, an active receipt, a separately
reviewed dispatch marker, and an activated workflow.

Both response bodies are processed in memory only. Numeric economic values are
never extracted, logged, persisted, or returned.
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
    ROOT
    / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-authorization.json"
)
DISPATCH = (
    ROOT
    / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-dispatch.json"
)
CONTRACT = (
    ROOT
    / "governance/score-v2-1f-bls-wpu0561-row-presence-preflight-execution-contract.json"
)

USER_AGENT_RE = re.compile(
    r"^USD-Impact-Score-v2\.1F-WPU0561-row-presence/2\.0 \(contact: .+\)$"
)
STRUCTURAL_PATTERNS = {
    "WPU0561": re.compile(r"(?<![A-Za-z0-9])WPU0561(?![A-Za-z0-9])", re.IGNORECASE),
    "0561": re.compile(r"(?<![A-Za-z0-9])0561(?![A-Za-z0-9])"),
    "05-61": re.compile(r"(?<![A-Za-z0-9])05-61(?![A-Za-z0-9])"),
    "Crude petroleum": re.compile(r"\bCrude\s+petroleum\b", re.IGNORECASE),
}
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
            raise RuntimeError("BLS row-presence request budget exceeded")
        self.count += 1


class HtmlTableRowParser(HTMLParser):
    """Collect only structural token matches with table/row coordinates."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.table_index = 0
        self.current_table: int | None = None
        self.current_row = 0
        self.in_row = False
        self.row_parts: list[str] = []
        self.matches: list[dict[str, object]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        lowered = tag.lower()
        if lowered == "table":
            self.table_index += 1
            self.current_table = self.table_index
            self.current_row = 0
        elif lowered == "tr" and self.current_table is not None:
            self.current_row += 1
            self.in_row = True
            self.row_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_row:
            self.row_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered == "tr" and self.in_row and self.current_table is not None:
            text = " ".join(self.row_parts)
            identifiers = _matched_identifiers(text)
            if identifiers:
                self.matches.append(
                    {
                        "table": self.current_table,
                        "row": self.current_row,
                        "matched_identifiers": identifiers,
                    }
                )
            self.in_row = False
            self.row_parts = []
        elif lowered == "table":
            self.current_table = None
            self.current_row = 0


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def _validate_contact_user_agent(value: object) -> str:
    if not isinstance(value, str) or not USER_AGENT_RE.fullmatch(value):
        raise RuntimeError("contactable project User-Agent is missing or invalid")
    return value


def _validate_authorization_and_dispatch() -> str:
    if not ACTIVE_RECEIPT.exists() or not DISPATCH.exists():
        raise RuntimeError("v2.1F WPU0561 row-presence authorization is not active")

    receipt = _load(ACTIVE_RECEIPT)
    dispatch = _load(DISPATCH)
    contract = _load(CONTRACT)

    if receipt.get("version") != 2:
        raise RuntimeError("row-presence receipt version changed")
    if receipt.get("decision_status") != "approved":
        raise RuntimeError("row-presence receipt is not approved")
    if receipt.get("issue") != "https://github.com/usdimpact/usd-impact-pipeline/issues/236":
        raise RuntimeError("row-presence decision issue changed")
    if receipt.get("execution_scope") != "bls_wpu0561_row_presence_preflight_only":
        raise RuntimeError("row-presence execution scope changed")
    if receipt.get("data_window") != {"start": START, "end": END}:
        raise RuntimeError("row-presence research window changed")
    if receipt.get("request_budget") != REQUEST_BUDGET:
        raise RuntimeError("row-presence request budget changed")
    if receipt.get("allowed_host") != HOST:
        raise RuntimeError("row-presence host changed")
    if receipt.get("fixed_resources") != FIXED_RESOURCES:
        raise RuntimeError("row-presence fixed resource set changed")

    user_agent = _validate_contact_user_agent(receipt.get("contact_user_agent"))
    auth = receipt.get("authorizations", {})
    if auth.get("response_body_ephemeral_retrieval") is not True:
        raise RuntimeError("ephemeral response-body retrieval is not authorized")
    if auth.get("row_presence_preflight") is not True:
        raise RuntimeError("row-presence preflight is not authorized")
    for field in (
        "source_value_extraction",
        "real_data_research",
        "full_historical_reconstruction",
        "candidate_score_computation",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if contract.get("version") != 2:
        raise RuntimeError("row-presence contract version changed")
    if contract.get("state") != "row_presence_preflight_authorized":
        raise RuntimeError("row-presence execution contract is not active")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("row-presence active receipt is not expected")
    if contract.get("dispatch_marker_expected_now") is not True:
        raise RuntimeError("row-presence dispatch is not expected")
    if contract.get("request_budget") != REQUEST_BUDGET:
        raise RuntimeError("row-presence contract request budget changed")
    if contract.get("fixed_resources") != FIXED_RESOURCES:
        raise RuntimeError("row-presence contract resources changed")

    current = contract.get("current_state", {})
    if current.get("response_body_ephemeral_retrieval_authorized") is not True:
        raise RuntimeError("ephemeral response-body retrieval contract flag is inactive")
    if current.get("row_presence_preflight_authorized") is not True:
        raise RuntimeError("row-presence contract flag is inactive")
    for field in (
        "source_value_extraction_authorized",
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
        raise RuntimeError("row-presence dispatch marker is invalid")
    if dispatch.get("issue") != "https://github.com/usdimpact/usd-impact-pipeline/issues/236":
        raise RuntimeError("row-presence dispatch issue changed")
    if dispatch.get("phase") != "bls_wpu0561_row_presence_preflight":
        raise RuntimeError("row-presence dispatch phase changed")
    if dispatch.get("request_budget") != REQUEST_BUDGET:
        raise RuntimeError("row-presence dispatch budget changed")
    if dispatch.get("fixed_resources") != FIXED_RESOURCES:
        raise RuntimeError("row-presence dispatch resources changed")
    if dispatch.get("source_value_extraction_authorized") is not False:
        raise RuntimeError("source-value extraction must remain forbidden")
    if dispatch.get("candidate_score_computation_authorized") is not False:
        raise RuntimeError("candidate Score must remain forbidden")
    if dispatch.get("production_authorized") is not False:
        raise RuntimeError("Production must remain forbidden")

    activation_commit = contract.get("authorization_activation_merge_commit")
    if not isinstance(activation_commit, str) or len(activation_commit) != 40:
        raise RuntimeError("row-presence activation commit is not pinned")
    if dispatch.get("authorization_activation_merge_commit") != activation_commit:
        raise RuntimeError("row-presence dispatch is not pinned to activation")

    return user_agent


def _validate_request_path(path: str) -> None:
    if path not in FIXED_RESOURCES:
        raise RuntimeError("request is outside the two fixed BLS resources")


def _challenge_detected(payload: bytes) -> bool:
    text = payload[:65536].decode("utf-8", errors="ignore").lower()
    return any(marker in text for marker in CHALLENGE_MARKERS)


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
            raise RuntimeError("row-presence preflight rejects redirects fail-closed")
        if response.status in {401, 403, 429}:
            raise RuntimeError(
                f"BLS row-presence access-control stop: HTTP {response.status}"
            )
        if response.status != 200:
            raise RuntimeError(
                f"BLS row-presence retrieval returned HTTP {response.status}"
            )

        length = response.getheader("Content-Length")
        if length is not None and int(length) > MAX_BODY_BYTES:
            raise RuntimeError("BLS response body exceeds fixed in-memory size limit")
        payload = response.read(MAX_BODY_BYTES + 1)
        if len(payload) > MAX_BODY_BYTES:
            raise RuntimeError("BLS response body exceeds fixed in-memory size limit")

        content_type = (response.getheader("Content-Type") or "").lower()
        if path.endswith(".htm"):
            if _challenge_detected(payload):
                raise RuntimeError("BLS access challenge detected; fail closed")
            prefix = payload[:65536].decode("utf-8", errors="ignore").lower()
            if "html" not in content_type and "<html" not in prefix:
                raise RuntimeError("official HTML resource returned unexpected content")
            fmt = "html"
        elif path.endswith(".xlsx"):
            if not payload.startswith(b"PK"):
                raise RuntimeError("official XLSX resource returned unexpected signature")
            fmt = "xlsx"
        else:
            raise RuntimeError("unsupported fixed resource format")

        metadata = {
            "method": "GET",
            "host": HOST,
            "path": path,
            "status": response.status,
            "format": fmt,
            "content_type": content_type.split(";", 1)[0],
        }
        return metadata, payload
    finally:
        connection.close()


def _matched_identifiers(text: str) -> list[str]:
    return sorted(
        label for label, pattern in STRUCTURAL_PATTERNS.items() if pattern.search(text)
    )


def _extract_html_structural_matches(payload: bytes) -> list[dict[str, object]]:
    parser = HtmlTableRowParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    parser.close()
    return parser.matches


def _xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        payload = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(payload)
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    strings: list[str] = []
    for item in root.findall("m:si", ns):
        parts = [node.text or "" for node in item.findall(".//m:t", ns)]
        strings.append("".join(parts))
    return strings


def _xlsx_sheet_map(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    ns_main = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rel_ns = {"p": "http://schemas.openxmlformats.org/package/2006/relationships"}

    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    target_by_id = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall("p:Relationship", rel_ns)
    }

    output: list[tuple[str, str]] = []
    for sheet in workbook.findall("m:sheets/m:sheet", ns_main):
        name = sheet.attrib.get("name", "unnamed")
        rel_id = sheet.attrib.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        )
        if not rel_id or rel_id not in target_by_id:
            continue
        target = target_by_id[rel_id].lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        output.append((name, target))
    return output


def _xlsx_cell_string(
    cell: ET.Element,
    *,
    shared_strings: list[str],
    ns: dict[str, str],
) -> str | None:
    cell_type = cell.attrib.get("t")
    if cell_type == "s":
        value = cell.find("m:v", ns)
        if value is None or value.text is None:
            return None
        try:
            index = int(value.text)
        except ValueError:
            return None
        if 0 <= index < len(shared_strings):
            return shared_strings[index]
        return None

    if cell_type == "inlineStr":
        parts = [node.text or "" for node in cell.findall(".//m:t", ns)]
        return "".join(parts)

    if cell_type == "str":
        value = cell.find("m:v", ns)
        return value.text if value is not None else None

    # Numeric cells, formulas returning numbers, dates and booleans are ignored.
    return None


def _extract_xlsx_structural_matches(payload: bytes) -> list[dict[str, object]]:
    matches: list[dict[str, object]] = []
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        shared_strings = _xlsx_shared_strings(archive)
        for sheet_name, sheet_path in _xlsx_sheet_map(archive):
            root = ET.fromstring(archive.read(sheet_path))
            for row in root.findall(".//m:row", ns):
                row_number = int(row.attrib.get("r", "0") or "0")
                row_matches: set[str] = set()
                for cell in row.findall("m:c", ns):
                    text = _xlsx_cell_string(
                        cell,
                        shared_strings=shared_strings,
                        ns=ns,
                    )
                    if text is None:
                        continue
                    row_matches.update(_matched_identifiers(text))
                if row_matches:
                    matches.append(
                        {
                            "sheet": sheet_name,
                            "row": row_number,
                            "matched_identifiers": sorted(row_matches),
                        }
                    )
    return matches


def run_preflight() -> dict[str, object]:
    user_agent = _validate_authorization_and_dispatch()
    budget = RequestBudget()

    html_meta, html_body = _request_once(
        HTML_PATH,
        budget=budget,
        user_agent=user_agent,
    )
    html_matches = _extract_html_structural_matches(html_body)
    del html_body

    xlsx_meta, xlsx_body = _request_once(
        XLSX_PATH,
        budget=budget,
        user_agent=user_agent,
    )
    xlsx_matches = _extract_xlsx_structural_matches(xlsx_body)
    del xlsx_body

    if budget.count != REQUEST_BUDGET:
        raise RuntimeError("row-presence preflight did not consume the exact request budget")

    return {
        "status": "passed" if html_matches or xlsx_matches else "no_structural_match",
        "scope": "bls_wpu0561_row_presence_preflight_only",
        "data_window": {"start": START, "end": END},
        "request_count": budget.count,
        "resources": [html_meta, xlsx_meta],
        "html_structural_matches": html_matches,
        "xlsx_structural_matches": xlsx_matches,
        "structurally_identifiable": bool(html_matches or xlsx_matches),
        "response_bodies_persisted": False,
        "numeric_source_values_extracted": False,
        "numeric_source_values_logged": False,
        "numeric_source_values_persisted": False,
        "full_historical_reconstruction_performed": False,
        "candidate_score_computed": False,
        "component_zscores_computed": False,
        "component_contributions_computed": False,
        "alternate_sources_used": False,
        "research_ledger_modified": False,
        "public_artifacts_modified": False,
        "production_modified": False,
    }


def main() -> int:
    print(json.dumps(run_preflight(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
