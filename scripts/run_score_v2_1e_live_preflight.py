#!/usr/bin/env python3
"""Authorized live historical-vintage feasibility preflight for Score v2.1E.

The preflight may retrieve real official Federal Reserve Board and BLS archive
documents under the active one-off research authorization. It never prints,
persists, or returns source values and it never computes a candidate Score.
"""

from __future__ import annotations

import argparse
import html
import http.client
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
START = date(2013, 1, 1)
END = date(2026, 10, 23)
FED_HOST = "www.federalreserve.gov"
BLS_HOST = "www.bls.gov"
ALLOWED_HOSTS = {
    "federalreserve.gov",
    FED_HOST,
    "bls.gov",
    BLS_HOST,
    "data.bls.gov",
}
PDFTOTEXT = Path("/usr/bin/pdftotext")
FED_FAMILIES = {
    "H10": {
        "index_path": "/releases/h10/",
        "archive_code": "h10",
        "minimum_releases": 600,
        "tokens": (("broad", "dollar"),),
        "sample_dates": (date(2013, 1, 7), date(2020, 1, 6), date(2025, 1, 6)),
    },
    "H8": {
        "index_path": "/releases/h8/",
        "archive_code": "h8",
        "minimum_releases": 600,
        "tokens": (("bank credit",), ("commercial banks",)),
        "sample_dates": (date(2013, 1, 11), date(2020, 1, 10), date(2025, 1, 10)),
    },
    "H41": {
        "index_path": "/releases/h41/",
        "archive_code": "h41",
        "minimum_releases": 600,
        "tokens": (("primary credit",), ("total assets",)),
        "sample_dates": (date(2013, 1, 3), date(2020, 1, 2), date(2025, 1, 2)),
    },
    "H15": {
        "index_path": "/releases/h15/",
        "archive_code": "h15",
        "minimum_releases": 3000,
        "tokens": (
            ("2-year", "2 year"),
            ("10-year", "10 year"),
            ("inflation-indexed", "inflation indexed"),
        ),
        "sample_dates": (date(2013, 1, 14), date(2020, 1, 6), date(2025, 1, 6)),
    },
}
BLS_REPORT_INDEX_PATH = "/ppi/detailed-report/"
BLS_SAMPLE_REPORT_PATHS = (
    "/ppi/detailed-report/ppi-detailed-report-september-2013.pdf",
    "/ppi/detailed-report/ppi-detailed-report-january-2020.pdf",
    "/ppi/detailed-report/ppi-detailed-report-september-2026.pdf",
)
EXPECTED_SERIES_COUNT = 8
MAX_BYTES = 30 * 1024 * 1024
USER_AGENT = "USD-Impact-v2.1E-private-research-preflight/1.0"


def _validate_url(url: str) -> str:
    """Policy helper used by tests; live retrieval does not accept arbitrary URLs."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https":
        raise RuntimeError("source URL must use HTTPS")
    if host not in ALLOWED_HOSTS:
        raise RuntimeError(f"source host is outside authorization allowlist: {host or '<missing>'}")
    if parsed.username or parsed.password:
        raise RuntimeError("credentials in source URL are forbidden")
    return host


def _validate_path(path: str) -> None:
    if not path.startswith("/") or "\\" in path or "://" in path:
        raise RuntimeError("source path is not canonical")
    if any(part in {".", ".."} for part in path.split("/")):
        raise RuntimeError("source path traversal is forbidden")


def _get_fixed(host: str, path: str) -> tuple[bytes, str]:
    """Retrieve from a fixed official host; redirects are intentionally rejected."""
    if host not in {FED_HOST, BLS_HOST}:
        raise RuntimeError("live source host is outside the fixed preflight set")
    _validate_path(path)
    connection = http.client.HTTPSConnection(host, timeout=45)
    try:
        connection.request("GET", path, headers={"User-Agent": USER_AGENT})
        response = connection.getresponse()
        if 300 <= response.status < 400:
            raise RuntimeError("official source redirect rejected by fail-closed policy")
        if response.status != 200:
            raise RuntimeError(
                f"official source retrieval returned HTTP {response.status} "
                f"for {host}{path}"
            )
        length = response.getheader("Content-Length")
        if length and int(length) > MAX_BYTES:
            raise RuntimeError("source response exceeds preflight size limit")
        payload = response.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise RuntimeError("source response exceeds preflight size limit")
        return payload, str(response.getheader("Content-Type") or "").lower()
    finally:
        connection.close()


def _get_fed(path: str) -> tuple[bytes, str]:
    return _get_fixed(FED_HOST, path)


def _get_bls(path: str) -> tuple[bytes, str]:
    return _get_fixed(BLS_HOST, path)


def _html_text(payload: bytes) -> str:
    text = payload.decode("utf-8", errors="replace")
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _pdf_text(payload: bytes) -> str:
    if not PDFTOTEXT.is_file():
        raise RuntimeError("pdftotext is required for archived PDF feasibility checks")
    proc = subprocess.run(
        [str(PDFTOTEXT), "-layout", "-", "-"],
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError("pdftotext could not parse an official archived PDF")
    return proc.stdout.decode("utf-8", errors="replace")


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


def _matches_family(text: str, token_groups: tuple[tuple[str, ...], ...]) -> bool:
    lowered = text.lower()
    return all(any(token in lowered for token in group) for group in token_groups)


def _fed_archive_text(code: str, released: date) -> str:
    stamp = released.strftime("%Y%m%d")
    html_path = f"/releases/{code}/{stamp}/default.htm"
    try:
        payload, content_type = _get_fed(html_path)
        text = _pdf_text(payload) if "pdf" in content_type else _html_text(payload)
        if text.strip():
            return text
    except RuntimeError:
        pass
    pdf_path = f"/releases/{code}/{stamp}/{code}.pdf"
    payload, _ = _get_fed(pdf_path)
    return _pdf_text(payload)


_MONTH_NAMES = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
)
_MONTHS = {name: idx for idx, name in enumerate(_MONTH_NAMES, start=1)}
_BLS_NAME = re.compile(
    r"ppi-detailed-report-([a-z]+)-(20\d{2})\.pdf",
    re.IGNORECASE,
)


def extract_bls_report_identifiers(payload: bytes) -> list[date]:
    """Count archive month/year identifiers without using them as network paths."""
    text = payload.decode("utf-8", errors="replace")
    reports: set[date] = set()
    for month_name, year_text in _BLS_NAME.findall(text):
        month = _MONTHS.get(month_name.lower())
        if not month:
            continue
        ref = date(int(year_text), month, 1)
        if START <= ref <= END:
            reports.add(ref)
    return sorted(reports)


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
    if not PDFTOTEXT.is_file():
        raise RuntimeError("pdftotext is unavailable; fail closed before archive parsing")

    fed_summary: dict[str, dict[str, int]] = {}
    for family, cfg in FED_FAMILIES.items():
        payload, _ = _get_fed(str(cfg["index_path"]))
        release_dates = extract_fed_release_dates(payload, str(cfg["archive_code"]))
        if len(release_dates) < int(cfg["minimum_releases"]):
            raise RuntimeError(
                f"{family} historical release enumeration is incomplete "
                f"({len(release_dates)} < {cfg['minimum_releases']})"
            )

        sample_dates = tuple(cfg["sample_dates"])
        if not all(released in release_dates for released in sample_dates):
            raise RuntimeError(f"{family} fixed sample identifiers are absent from official index")

        parseable = 0
        for released in sample_dates:
            text = _fed_archive_text(str(cfg["archive_code"]), released)
            if not _matches_family(text, cfg["tokens"]):
                raise RuntimeError(f"{family} sampled archive is not conservatively parseable")
            parseable += 1

        fed_summary[family] = {
            "release_count": len(release_dates),
            "sampled_releases": len(sample_dates),
            "parseable_samples": parseable,
        }

    bls_index, _ = _get_bls(BLS_REPORT_INDEX_PATH)
    report_identifiers = extract_bls_report_identifiers(bls_index)
    if len(report_identifiers) < 160:
        raise RuntimeError(
            f"BLS PPI detailed-report archive enumeration is incomplete "
            f"({len(report_identifiers)} < 160)"
        )

    bls_parseable = 0
    for report_path in BLS_SAMPLE_REPORT_PATHS:
        payload, _ = _get_bls(report_path)
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
            "detailed_report_count": len(report_identifiers),
            "sampled_reports": len(BLS_SAMPLE_REPORT_PATHS),
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
