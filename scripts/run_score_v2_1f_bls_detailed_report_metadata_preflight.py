#!/usr/bin/env python3
"""Metadata-only BLS Detailed Report preflight for Score v2.1F.

This runner is intentionally fail-closed. In the current design-only state it
must refuse before any network request. A future live run requires a separately
approved active receipt, activated execution contract, dispatch marker and
reviewed workflow activation.

The runner never downloads historical PDF/XLSX report bodies, never retrieves
or parses WPU0561 values, and never computes Score components.
"""

from __future__ import annotations

import fnmatch
import http.client
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
START = "2013-01-01"
END = "2026-10-23"
BLS_HOST = "www.bls.gov"
ROBOTS_PATH = "/robots.txt"
INDEX_PATH = "/ppi/detailed-report/"
REQUEST_BUDGET = 4
MAX_GET_BYTES = 2 * 1024 * 1024

ACTIVE_RECEIPT = (
    ROOT
    / "governance/score-v2-1f-bls-detailed-report-metadata-preflight-authorization.json"
)
CONTRACT = (
    ROOT
    / "governance/score-v2-1f-bls-detailed-report-metadata-preflight-execution-contract.json"
)
DISPATCH = (
    ROOT
    / "governance/score-v2-1f-bls-detailed-report-metadata-preflight-dispatch.json"
)
USER_AGENT_RE = re.compile(
    r"^USD-Impact-Score-v2\.1F-BLS-metadata-preflight/1\.0 \(contact: .+\)$"
)
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
            raise RuntimeError("BLS metadata request budget exceeded")
        self.count += 1


class ArchiveIndexParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(str(value))

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)


def _load(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def _validate_contact_user_agent(value: object) -> str:
    if not isinstance(value, str) or not USER_AGENT_RE.fullmatch(value):
        raise RuntimeError("contactable project User-Agent is missing or invalid")
    return value


def _validate_authorization_and_dispatch() -> str:
    if not ACTIVE_RECEIPT.exists():
        raise RuntimeError("v2.1F BLS metadata preflight authorization is not active")
    if not DISPATCH.exists():
        raise RuntimeError("v2.1F BLS metadata preflight dispatch is not active")

    receipt = _load(ACTIVE_RECEIPT)
    contract = _load(CONTRACT)
    dispatch = _load(DISPATCH)

    if receipt.get("decision_status") != "approved":
        raise RuntimeError("BLS metadata preflight receipt is not approved")
    if receipt.get("issue") != "https://github.com/usdimpact/usd-impact-pipeline/issues/230":
        raise RuntimeError("BLS metadata preflight decision issue changed")
    if receipt.get("execution_scope") != "bls_detailed_report_metadata_preflight_only":
        raise RuntimeError("BLS metadata preflight scope changed")
    if receipt.get("data_window") != {"start": START, "end": END}:
        raise RuntimeError("BLS metadata preflight data window changed")
    if receipt.get("request_budget") != REQUEST_BUDGET:
        raise RuntimeError("BLS metadata request budget changed")
    if receipt.get("allowed_host") != BLS_HOST:
        raise RuntimeError("BLS metadata host changed")
    user_agent = _validate_contact_user_agent(receipt.get("contact_user_agent"))

    auth = receipt.get("authorizations")
    if not isinstance(auth, dict):
        raise RuntimeError("BLS metadata receipt authorizations missing")
    if auth.get("network_metadata_fetch") is not True:
        raise RuntimeError("network metadata fetch is not authorized")
    if auth.get("bls_metadata_preflight") is not True:
        raise RuntimeError("BLS metadata preflight is not authorized")
    for field in (
        "report_body_download",
        "source_value_retrieval",
        "real_data_research",
        "candidate_score_computation",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if contract.get("state") != "metadata_preflight_authorized":
        raise RuntimeError("BLS metadata execution contract is not active")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("active BLS metadata receipt is not expected")
    if contract.get("dispatch_marker_expected_now") is not True:
        raise RuntimeError("BLS metadata dispatch is not expected")
    if contract.get("request_budget") != REQUEST_BUDGET:
        raise RuntimeError("execution-contract request budget changed")

    current = contract.get("current_state")
    if not isinstance(current, dict):
        raise RuntimeError("BLS metadata contract current state missing")
    if current.get("network_metadata_fetch_authorized") is not True:
        raise RuntimeError("network metadata fetch contract flag is not active")
    if current.get("bls_metadata_preflight_authorized") is not True:
        raise RuntimeError("BLS metadata preflight contract flag is not active")
    for field in (
        "report_body_download_authorized",
        "source_value_retrieval_authorized",
        "real_data_research_authorized",
        "candidate_score_computation_authorized",
        "research_ledger_mutation_authorized",
        "public_artifact_replacement_authorized",
        "production_authorized",
    ):
        if current.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if dispatch.get("state") != "approved_dispatch":
        raise RuntimeError("BLS metadata dispatch marker is invalid")
    if dispatch.get("issue") != "https://github.com/usdimpact/usd-impact-pipeline/issues/230":
        raise RuntimeError("BLS metadata dispatch issue changed")
    if dispatch.get("phase") != "bls_detailed_report_metadata_preflight":
        raise RuntimeError("BLS metadata dispatch phase changed")
    if dispatch.get("data_window") != {"start": START, "end": END}:
        raise RuntimeError("BLS metadata dispatch window changed")
    if dispatch.get("request_budget") != REQUEST_BUDGET:
        raise RuntimeError("BLS metadata dispatch request budget changed")
    if dispatch.get("candidate_score_computation_authorized") is not False:
        raise RuntimeError("candidate Score must remain forbidden")
    if dispatch.get("production_authorized") is not False:
        raise RuntimeError("Production must remain forbidden")

    activation_commit = contract.get("authorization_activation_merge_commit")
    if not isinstance(activation_commit, str) or len(activation_commit) != 40:
        raise RuntimeError("BLS metadata activation commit is not pinned")
    if dispatch.get("authorization_activation_merge_commit") != activation_commit:
        raise RuntimeError("BLS metadata dispatch is not pinned to activation")

    return user_agent


def _validate_request_path(method: str, path: str) -> None:
    if not path.startswith("/") or "\\" in path or "://" in path:
        raise RuntimeError("BLS request path is not canonical")
    if any(part in {".", ".."} for part in path.split("/")):
        raise RuntimeError("BLS request path traversal is forbidden")

    if method == "GET" and path in {ROBOTS_PATH, INDEX_PATH}:
        return
    if method == "HEAD" and path.startswith(INDEX_PATH):
        lowered = path.lower()
        if lowered.endswith(".pdf") or lowered.endswith(".xlsx"):
            return
    raise RuntimeError("request is outside the fixed BLS metadata preflight set")


def _metadata_headers(response: http.client.HTTPResponse) -> dict[str, str]:
    allowed = ("content-type", "content-length", "retry-after", "location")
    output: dict[str, str] = {}
    for name in allowed:
        value = response.getheader(name)
        if value is not None:
            output[name] = str(value)
    return output


def _request_once(
    method: str,
    path: str,
    *,
    budget: RequestBudget,
    user_agent: str,
    read_body: bool,
) -> tuple[dict[str, object], bytes]:
    _validate_request_path(method, path)
    budget.consume()

    connection = http.client.HTTPSConnection(BLS_HOST, timeout=45)
    try:
        connection.request(method, path, headers={"User-Agent": user_agent})
        response = connection.getresponse()
        headers = _metadata_headers(response)
        metadata: dict[str, object] = {
            "method": method,
            "host": BLS_HOST,
            "path": path,
            "status": response.status,
            "headers": headers,
        }

        if 300 <= response.status < 400:
            raise RuntimeError("BLS metadata preflight rejects redirects fail-closed")
        if response.status in {401, 403, 429}:
            raise RuntimeError(
                f"BLS metadata access-control stop: HTTP {response.status} for {path}"
            )
        if method == "HEAD" and response.status == 405:
            raise RuntimeError("BLS report resource rejected HEAD; GET fallback is forbidden")
        if response.status != 200:
            raise RuntimeError(
                f"BLS metadata retrieval returned HTTP {response.status} for {path}"
            )

        if not read_body:
            return metadata, b""

        length = response.getheader("Content-Length")
        if length is not None and int(length) > MAX_GET_BYTES:
            raise RuntimeError("BLS metadata GET response exceeds size limit")
        payload = response.read(MAX_GET_BYTES + 1)
        if len(payload) > MAX_GET_BYTES:
            raise RuntimeError("BLS metadata GET response exceeds size limit")
        if _challenge_detected(payload):
            raise RuntimeError("BLS access challenge detected; fail closed")
        return metadata, payload
    finally:
        connection.close()


def _challenge_detected(payload: bytes) -> bool:
    text = payload.decode("utf-8", errors="ignore").lower()
    return any(marker in text for marker in CHALLENGE_MARKERS)


def _robots_disallows_detailed_report(payload: bytes) -> bool:
    current_agents: list[str] = []
    disallow_patterns: list[str] = []

    for raw_line in payload.decode("utf-8", errors="replace").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = [part.strip() for part in line.split(":", 1)]
        key = key.lower()
        if key == "user-agent":
            current_agents = [value.lower()]
            continue
        if key == "disallow" and "*" in current_agents and value:
            disallow_patterns.append(value)

    target = INDEX_PATH
    for pattern in disallow_patterns:
        if "*" in pattern:
            if fnmatch.fnmatch(target, pattern):
                return True
        elif target.startswith(pattern):
            return True
    return False


def _path_from_href(href: str) -> str:
    absolute = urljoin(f"https://{BLS_HOST}{INDEX_PATH}", href)
    parsed = urlparse(absolute)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() != BLS_HOST:
        raise RuntimeError("archive resource left the approved BLS host")
    if parsed.username or parsed.password:
        raise RuntimeError("credentials in archive resource are forbidden")
    path = parsed.path
    _validate_request_path("HEAD", path)
    return path


def _parse_archive_index(payload: bytes) -> dict[str, object]:
    parser = ArchiveIndexParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    parser.close()

    text = re.sub(r"\s+", " ", " ".join(parser.text_parts)).strip()
    hrefs: list[str] = []
    for href in parser.hrefs:
        lowered = href.lower()
        if ".pdf" not in lowered and ".xlsx" not in lowered:
            continue
        hrefs.append(href)

    paths_2013 = sorted(
        {_path_from_href(href) for href in hrefs if "2013" in href}
    )
    paths_2026 = sorted(
        {_path_from_href(href) for href in hrefs if "2026" in href}
    )
    if not paths_2013:
        raise RuntimeError("official Detailed Report index exposes no 2013 report resource")
    if not paths_2026:
        raise RuntimeError("official Detailed Report index exposes no 2026 report resource")

    selected_2013 = next(
        (path for path in paths_2013 if path.lower().endswith(".pdf")),
        paths_2013[0],
    )
    selected_2026 = next(
        (path for path in paths_2026 if path.lower().endswith(".xlsx")),
        next(
            (path for path in paths_2026 if path.lower().endswith(".pdf")),
            paths_2026[0],
        ),
    )

    corrected = sorted(
        set(re.findall(r"([A-Z][a-z]+\s+\d{4})\s+CORRECTED", text))
    )

    return {
        "has_2013": True,
        "has_2026": True,
        "expected_unavailable_2025_10_seen": bool(
            re.search(r"October\s+2025\s*:\s*Not\s+Available", text, re.IGNORECASE)
        ),
        "corrected_labels": corrected,
        "selected_2013_path": selected_2013,
        "selected_2026_path": selected_2026,
    }


def run_preflight() -> dict[str, object]:
    user_agent = _validate_authorization_and_dispatch()
    budget = RequestBudget()
    requests: list[dict[str, object]] = []

    robots_meta, robots_payload = _request_once(
        "GET",
        ROBOTS_PATH,
        budget=budget,
        user_agent=user_agent,
        read_body=True,
    )
    requests.append(robots_meta)
    if _robots_disallows_detailed_report(robots_payload):
        raise RuntimeError("robots.txt disallows the Detailed Report route")

    index_meta, index_payload = _request_once(
        "GET",
        INDEX_PATH,
        budget=budget,
        user_agent=user_agent,
        read_body=True,
    )
    requests.append(index_meta)
    archive = _parse_archive_index(index_payload)

    for path in (
        str(archive["selected_2013_path"]),
        str(archive["selected_2026_path"]),
    ):
        head_meta, body = _request_once(
            "HEAD",
            path,
            budget=budget,
            user_agent=user_agent,
            read_body=False,
        )
        if body:
            raise RuntimeError("HEAD resource unexpectedly returned a retained body")
        requests.append(head_meta)

    if budget.count != REQUEST_BUDGET:
        raise RuntimeError("BLS metadata preflight did not consume the exact request budget")

    return {
        "status": "passed",
        "scope": "bls_detailed_report_metadata_preflight_only",
        "data_window": {"start": START, "end": END},
        "request_count": budget.count,
        "requests": requests,
        "archive_metadata": archive,
        "report_bodies_downloaded": False,
        "source_values_retrieved": False,
        "source_values_persisted": False,
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
