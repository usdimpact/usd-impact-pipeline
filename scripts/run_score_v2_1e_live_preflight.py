#!/usr/bin/env python3
"""Authorized live historical-vintage feasibility preflight for Score v2.1E.

Retrieves only official Federal Reserve Board and BLS HTML archive pages under
the active one-off research authorization. Source values are never printed or
persisted, and this phase never computes a candidate Score.
"""

from __future__ import annotations

import argparse
import http.client
import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
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
BLS_NEWS_ARCHIVE_PATH = "/bls/news-release/ppi.htm"
BLS_MINIMUM_RELEASES = 160
BLS_SAMPLE_RELEASES = (
    (date(2013, 10, 29), "/news.release/archives/ppi_10292013.htm"),
    (date(2020, 2, 19), "/news.release/archives/ppi_02192020.htm"),
    (date(2026, 10, 15), "/news.release/archives/ppi_10152026.htm"),
)
EXPECTED_SERIES_COUNT = 8
MAX_BYTES = 30 * 1024 * 1024
USER_AGENT = "USD-Impact-v2.1E-private-research-preflight/1.0"


def _validate_url(url: str) -> str:
    """Policy helper used by tests; live retrieval accepts only fixed hosts."""
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
    """Retrieve from one fixed official host; redirects are rejected."""
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


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._suppressed_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in {"script", "style"}:
            self._suppressed_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self._suppressed_depth:
            self._suppressed_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._suppressed_depth:
            self.parts.append(data)


def _html_text(payload: bytes) -> str:
    parser = _VisibleTextParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    parser.close()
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def extract_fed_release_dates(payload: bytes, code: str) -> list[date]:
    code = code.lower()
    text = payload.decode("utf-8", errors="replace")
    pattern = re.compile(rf"(?i)(?:/releases/)?{re.escape(code)}/(20\d{{6}})\b")
    found: set[date] = set()
    for raw in pattern.findall(text):
        try:
            value = date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
        except ValueError:
            continue
        if START <= value <= END:
            found.add(value)
    return sorted(found)


def extract_bls_release_dates(payload: bytes) -> list[date]:
    """Count archived BLS PPI release identifiers without using them as requests."""
    text = payload.decode("utf-8", errors="replace")
    pattern = re.compile(rf"(?i)(?:/releases/)?{re.escape(code)}/(20\d{{6}})\b")
    found: set[date] = set()
    for raw in pattern.findall(text):
        try:
            value = date(int(raw[4:8]), int(raw[:2]), int(raw[2:4]))
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
    payload, content_type = _get_fed(f"/releases/{code}/{stamp}/default.htm")
    if "html" not in content_type and "text" not in content_type:
        raise RuntimeError("Federal Reserve sampled archive is not HTML/text")
    text = _html_text(payload)
    if not text:
        raise RuntimeError("Federal Reserve sampled archive is empty")
    return text


def _bls_crude_petroleum_parseable(text: str) -> bool:
    lowered = re.sub(r"\s+", " ", text.lower())
    if "crude petroleum" not in lowered:
        return False
    return bool(
        re.search(r"\b05\s*-\s*61\b", lowered)
        or re.search(r"\b05\s+61\b", lowered)
        or re.search(r"\b0561\b", lowered)
    )


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

    bls_index, _ = _get_bls(BLS_NEWS_ARCHIVE_PATH)
    bls_release_dates = extract_bls_release_dates(bls_index)
    if len(bls_release_dates) < BLS_MINIMUM_RELEASES:
        raise RuntimeError(
            f"BLS PPI archived-news enumeration is incomplete "
            f"({len(bls_release_dates)} < {BLS_MINIMUM_RELEASES})"
        )

    fixed_dates = tuple(released for released, _ in BLS_SAMPLE_RELEASES)
    if not all(released in bls_release_dates for released in fixed_dates):
        raise RuntimeError("BLS fixed sample identifiers are absent from official archive index")

    bls_parseable = 0
    for _, release_path in BLS_SAMPLE_RELEASES:
        payload, content_type = _get_bls(release_path)
        if "html" not in content_type and "text" not in content_type:
            raise RuntimeError("BLS sampled archive is not HTML/text")
        text = _html_text(payload)
        if not _bls_crude_petroleum_parseable(text):
            raise RuntimeError(
                "BLS sampled archived release does not expose crude petroleum code 05-61"
            )
        bls_parseable += 1

    return {
        "status": "passed",
        "phase": "vintage_feasibility_preflight",
        "authorized_data_window": {"start": START.isoformat(), "end": END.isoformat()},
        "exact_series_count": EXPECTED_SERIES_COUNT,
        "federal_reserve": fed_summary,
        "bls": {
            "archived_news_release_count": len(bls_release_dates),
            "sampled_releases": len(BLS_SAMPLE_RELEASES),
            "crude_petroleum_parseable_samples": bls_parseable,
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
