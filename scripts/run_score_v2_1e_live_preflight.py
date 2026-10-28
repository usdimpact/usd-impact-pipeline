#!/usr/bin/env python3
"""Authorized live historical-vintage feasibility preflight for Score v2.1E.

The preflight may retrieve real official Federal Reserve Board and BLS archive
documents under the active one-off research authorization. It never prints,
persists, or returns source values and it never computes a candidate Score.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
START = date(2013, 1, 1)
END = date(2026, 10, 23)
ALLOWED_HOSTS = {
    "federalreserve.gov",
    "www.federalreserve.gov",
    "bls.gov",
    "www.bls.gov",
    "data.bls.gov",
}
FED_FAMILIES = {
    "H10": {
        "index": "https://www.federalreserve.gov/releases/h10/",
        "archive_code": "h10",
        "minimum_releases": 600,
        "tokens": (("broad", "dollar"),),
    },
    "H8": {
        "index": "https://www.federalreserve.gov/releases/h8/",
        "archive_code": "h8",
        "minimum_releases": 600,
        "tokens": (("bank credit",), ("commercial banks",)),
    },
    "H41": {
        "index": "https://www.federalreserve.gov/releases/h41/",
        "archive_code": "h41",
        "minimum_releases": 600,
        "tokens": (("primary credit",), ("total assets",)),
    },
    "H15": {
        "index": "https://www.federalreserve.gov/releases/h15/",
        "archive_code": "h15",
        "minimum_releases": 3000,
        "tokens": (("2-year", "2 year"), ("10-year", "10 year"), ("inflation-indexed", "inflation indexed")),
    },
}
BLS_REPORT_INDEX = "https://www.bls.gov/ppi/detailed-report/"
EXPECTED_SERIES_COUNT = 8
MAX_BYTES = 30 * 1024 * 1024
USER_AGENT = "USD-Impact-v2.1E-private-research-preflight/1.0"


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https":
        raise RuntimeError("source URL must use HTTPS")
    if host not in ALLOWED_HOSTS:
        raise RuntimeError(f"source host is outside authorization allowlist: {host or '<missing>'}")
    if parsed.username or parsed.password:
        raise RuntimeError("credentials in source URL are forbidden")
    return host


class _SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _get(url: str) -> tuple[bytes, str]:
    _validate_url(url)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    opener = build_opener(_SafeRedirect())
    try:
        with opener.open(request, timeout=45) as response:
            final_url = response.geturl()
            _validate_url(final_url)
            length = response.headers.get("Content-Length")
            if length and int(length) > MAX_BYTES:
                raise RuntimeError("source response exceeds preflight size limit")
            payload = response.read(MAX_BYTES + 1)
            if len(payload) > MAX_BYTES:
                raise RuntimeError("source response exceeds preflight size limit")
            return payload, str(response.headers.get("Content-Type", "")).lower()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"official source retrieval failed for {url}: {exc}") from exc


def _html_text(payload: bytes) -> str:
    text = payload.decode("utf-8", errors="replace")
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _pdf_text(payload: bytes) -> str:
    tool = shutil.which("pdftotext")
    if not tool:
        raise RuntimeError("pdftotext is required for archived PDF feasibility checks")
    proc = subprocess.run(
        [tool, "-layout", "-", "-"],
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError("pdftotext could not parse an official archived PDF")
    return proc.stdout.decode("utf-8", errors="replace")


def _links(payload: bytes, base_url: str) -> list[str]:
    text = payload.decode("utf-8", errors="replace")
    hrefs = re.findall(r'''(?i)href\s*=\s*["']([^"'#]+)''', text)
    result: list[str] = []
    for href in hrefs:
        candidate = urljoin(base_url, html.unescape(href))
        try:
            _validate_url(candidate)
        except RuntimeError:
            continue
        result.append(candidate)
    return result


def extract_fed_release_dates(payload: bytes, code: str) -> list[date]:
    code = code.lower()
    text = payload.decode("utf-8", errors="replace")
    pattern = re.compile(rf"(?i)(?:/releases/)?{re.escape(code)}/(20\d{{6}})(?:/|[.])")
    found: set[date] = set()
    for raw in pattern.findall(text):
        try:
            value = date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
        except ValueError:
            continue
        if START <= value <= END:
            found.add(value)
    return sorted(found)


def _sample_three(items: list):
    if len(items) < 3:
        raise RuntimeError("fewer than three historical archive items are available")
    return [items[0], items[len(items) // 2], items[-1]]


def _matches_family(text: str, token_groups: tuple[tuple[str, ...], ...]) -> bool:
    lowered = text.lower()
    return all(any(token in lowered for token in group) for group in token_groups)


def _fed_archive_text(code: str, released: date) -> str:
    stamp = released.strftime("%Y%m%d")
    base = f"https://www.federalreserve.gov/releases/{code}/{stamp}/"
    try:
        payload, content_type = _get(base)
        text = _pdf_text(payload) if "pdf" in content_type else _html_text(payload)
        if text.strip():
            return text
    except RuntimeError:
        pass
    payload, _ = _get(urljoin(base, f"{code}.pdf"))
    return _pdf_text(payload)


_MONTHS = {
    name.lower(): idx
    for idx, name in enumerate(
        ("January", "February", "March", "April", "May", "June",
         "July", "August", "September", "October", "November", "December"),
        start=1,
    )
}
_BLS_NAME = re.compile(
    r"ppi-detailed-report-([a-z]+)-(20\d{2})\.pdf(?:$|[?])",
    re.IGNORECASE,
)


def extract_bls_report_links(payload: bytes, base_url: str = BLS_REPORT_INDEX) -> list[tuple[date, str]]:
    reports: dict[date, str] = {}
    for link in _links(payload, base_url):
        match = _BLS_NAME.search(link)
        if not match:
            continue
        month = _MONTHS.get(match.group(1).lower())
        if not month:
            continue
        ref = date(int(match.group(2)), month, 1)
        if START <= ref <= END:
            reports[ref] = link
    return sorted(reports.items())


def _bls_wpu0561_parseable(text: str) -> bool:
    lines = [re.sub(r"\s+", " ", line).strip().lower() for line in text.splitlines()]
    for idx, line in enumerate(lines):
        if re.search(r"\b0561\b", line):
            context = " ".join(lines[max(0, idx - 1): idx + 2])
            if "crude petroleum" in context:
                return True
    return False


def _validate_active_authorization() -> None:
    from scripts import validate_score_v2_1e_research_authorization as authorization

    report = authorization.validate(ROOT)
    if report.get("state") != "one_off_private_research_authorized":
        raise RuntimeError("one-off research authorization is not active")
    if report.get("real_data_fetch_authorized") is not True:
        raise RuntimeError("real-data fetch is not authorized")
    if report.get("real_data_research_authorized") is not True:
        raise RuntimeError("real-data research is not authorized")
    if report.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")
    if report.get("data_window") != {"start": START.isoformat(), "end": END.isoformat()}:
        raise RuntimeError("authorized data window does not match preflight")


def run_preflight() -> dict[str, object]:
    _validate_active_authorization()
    if not shutil.which("pdftotext"):
        raise RuntimeError("pdftotext is unavailable; fail closed before archive parsing")

    fed_summary: dict[str, dict[str, int]] = {}
    for family, cfg in FED_FAMILIES.items():
        payload, _ = _get(str(cfg["index"]))
        release_dates = extract_fed_release_dates(payload, str(cfg["archive_code"]))
        if len(release_dates) < int(cfg["minimum_releases"]):
            raise RuntimeError(
                f"{family} historical release enumeration is incomplete "
                f"({len(release_dates)} < {cfg['minimum_releases']})"
            )
        parseable = 0
        for released in _sample_three(release_dates):
            text = _fed_archive_text(str(cfg["archive_code"]), released)
            if not _matches_family(text, cfg["tokens"]):
                raise RuntimeError(f"{family} sampled archive is not conservatively parseable")
            parseable += 1
        fed_summary[family] = {
            "release_count": len(release_dates),
            "sampled_releases": 3,
            "parseable_samples": parseable,
        }

    bls_index, _ = _get(BLS_REPORT_INDEX)
    reports = extract_bls_report_links(bls_index)
    if len(reports) < 160:
        raise RuntimeError(
            f"BLS PPI detailed-report archive enumeration is incomplete ({len(reports)} < 160)"
        )
    bls_parseable = 0
    for _, report_url in _sample_three(reports):
        payload, _ = _get(report_url)
        text = _pdf_text(payload)
        if not _bls_wpu0561_parseable(text):
            raise RuntimeError("BLS sampled detailed report does not expose WPU0561 conservatively")
        bls_parseable += 1

    return {
        "status": "passed",
        "phase": "vintage_feasibility_preflight",
        "authorized_data_window": {"start": START.isoformat(), "end": END.isoformat()},
        "exact_series_count": EXPECTED_SERIES_COUNT,
        "federal_reserve": fed_summary,
        "bls": {
            "detailed_report_count": len(reports),
            "sampled_reports": 3,
            "wpu0561_parseable_samples": bls_parseable,
        },
        "source_hosts_allowlisted": sorted(ALLOWED_HOSTS),
        "source_payloads_persisted": False,
        "raw_values_logged": False,
        "candidate_score_computed": False,
        "public_artifacts_modified": False,
        "research_ledgers_modified": False,
        "production_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_preflight()
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
