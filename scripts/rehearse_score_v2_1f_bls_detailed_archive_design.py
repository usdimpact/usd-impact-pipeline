"""OFFLINE, synthetic-only BLS PPI detailed-report archive-link design rehearsal.

This is NOT a live archive client. The v2.1F Stage 1 receipt was consumed after
the approved GitHub runner received HTTP 403. No network transport is implemented
here, and this code must never be imported into live preflight without a separate
explicit owner decision and a fresh method/source review.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

INDEX_URL = "https://www.bls.gov/ppi/detailed-report/"
ALLOWED_HOST = "www.bls.gov"
_MONTH_YEAR = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+20\d{2}\b",
    re.IGNORECASE,
)
_MEDIA_LABEL = re.compile(r"\b(?:PDF|XLSX)\b", re.IGNORECASE)
_ARCHIVE_EXTENSIONS = (".pdf", ".xlsx")


class _Links(HTMLParser):
    """Collect only anchor href and link-label text from caller-supplied HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a" and self._href is None:
            self._href = next((v for k, v in attrs if k.lower() == "href"), None)
            self._chunks = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join("".join(self._chunks).split())))
            self._href = None
            self._chunks = []


def _validate_synthetic_candidate_href(href: str) -> tuple[str, str]:
    if not isinstance(href, str) or not href or any(c in href for c in ("\r", "\n", "\\", "%")):
        raise ValueError("ambiguous or encoded BLS candidate URL")
    pre = urlsplit(href)
    if pre.scheme and pre.scheme.lower() != "https":
        raise ValueError("BLS candidate must use HTTPS")
    if pre.username or pre.password or pre.query or pre.fragment:
        raise ValueError("BLS candidate cannot contain credentials, query or fragment")
    if any(p in (".", "..") for p in pre.path.split("/")):
        raise ValueError("BLS candidate path traversal")
    url = urljoin(INDEX_URL, href)
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST or parsed.port is not None:
        raise ValueError("BLS candidate is outside the single official archive host")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("BLS candidate URL has disallowed authority components")
    if not parsed.path.startswith("/ppi/") or "//" in parsed.path:
        raise ValueError("BLS candidate is outside the proposed Detailed Report document family")
    kind = next((ext[1:] for ext in _ARCHIVE_EXTENSIONS if parsed.path.lower().endswith(ext)), None)
    if kind is None:
        raise ValueError("BLS detailed-report candidate must be PDF or XLSX")
    return url, kind


def rehearse_synthetic_index(html: str, *, index_status: int, index_url: str = INDEX_URL) -> dict:
    """Classify caller-supplied HTML without fetching/indexing any source values.

    All outputs are design-only, including after an HTTP 200 simulation. Even
    apparently valid archive links do NOT establish live runner accessibility,
    release-time provenance, WPU0561 row existence or a score/reuse permission.
    """
    if index_url != INDEX_URL:
        raise ValueError("unreviewed index path requires a separate owner/source decision")
    if not isinstance(index_status, int) or isinstance(index_status, bool):
        raise ValueError("index_status must be a synthetic integer")
    if index_status != 200:
        return {
            "status": "BLOCKED_FAIL_CLOSED",
            "simulated_http_status": index_status,
            "candidate_urls": [],
            "live_fetch_authorized": False,
            "vintage_verified": False,
            "score_computation_authorized": False,
        }
    if not isinstance(html, str):
        raise TypeError("only supplied synthetic HTML strings are accepted")
    parser = _Links()
    parser.feed(html)
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    for href, label in parser.links:
        # Navigation links are not candidate archive documents. Requiring a
        # month/year + format in the *same synthetic anchor* is intentional.
        # Actual BLS layout handling is NOT certified by this rehearsal.
        if not _MONTH_YEAR.search(label) or not _MEDIA_LABEL.search(label):
            continue
        url, kind = _validate_synthetic_candidate_href(href)
        if url in seen:
            raise ValueError("ambiguous duplicate synthetic BLS archive candidate")
        seen.add(url)
        candidates.append({"candidate_url": url, "synthetic_label": label, "media_type": kind})
    return {
        "status": "DESIGN_CANDIDATES_ONLY" if candidates else "BLOCKED_NO_CANDIDATES",
        "simulated_http_status": index_status,
        "candidate_urls": candidates,
        "live_fetch_authorized": False,
        "vintage_verified": False,
        "score_computation_authorized": False,
    }
