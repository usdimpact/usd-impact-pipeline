#!/usr/bin/env python3
"""One-off live historical-vintage feasibility preflight for Score v2.1F.

The runner is intentionally unusable in the packet-only state. It requires a
separately approved active receipt, an activated execution contract, and a
separate dispatch marker before any network request. It never computes the
candidate Score and never persists or logs source/component values.
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
ACTIVE_RECEIPT = ROOT / "governance/score-v2-1f-live-vintage-preflight-authorization.json"
CONTRACT = ROOT / "governance/score-v2-1f-live-vintage-preflight-execution-contract.json"
DISPATCH = ROOT / "governance/score-v2-1f-live-vintage-preflight-dispatch.json"
EXPECTED_SERIES = [
    "H10/H10/JRXWTFB_N.B",
    "WPU0561",
    "H8/H8/B1001NCBA",
    "H41/H41/RESPPALDP_N.WW",
    "H41/H41/RESPPA_N.WW",
]
FED_FAMILIES = {
    "H10": {
        "index_path": "/releases/h10/",
        "archive_code": "h10",
        "landing_tokens": (("foreign exchange rates",), ("h.10", "h10")),
        "tokens": (("broad",), ("dollar",)),
        "sample_dates": (date(2013, 1, 7), date(2020, 1, 6), date(2025, 1, 6)),
    },
    "H8": {
        "index_path": "/releases/h8/",
        "archive_code": "h8",
        "landing_tokens": (("assets and liabilities",), ("commercial banks",)),
        "tokens": (("bank credit",), ("commercial banks",)),
        "sample_dates": (date(2013, 1, 11), date(2020, 1, 10), date(2025, 1, 10)),
    },
    "H41": {
        "index_path": "/releases/h41/",
        "archive_code": "h41",
        "landing_tokens": (("factors affecting reserve balances",), ("h.4.1", "h41")),
        "tokens": (("primary credit",), ("total assets",)),
        "sample_dates": (date(2013, 1, 3), date(2020, 1, 2), date(2025, 1, 2)),
    },
}
BLS_NEWS_ARCHIVE_PATH = "/bls/news-release/ppi.htm"
BLS_MINIMUM_RELEASES = 160
BLS_SAMPLE_RELEASES = (
    (date(2013, 10, 29), "/news.release/archives/ppi_10292013.htm"),
    (date(2020, 2, 19), "/news.release/archives/ppi_02192020.htm"),
    (date(2026, 10, 15), "/news.release/archives/ppi_10152026.htm"),
)
MAX_BYTES = 30 * 1024 * 1024
USER_AGENT = "USD-Impact-v2.1F-private-vintage-preflight/1.0"

def _load(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload

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

def _validate_path(path: str) -> None:
    if not path.startswith("/") or "\\" in path or "://" in path:
        raise RuntimeError("source path is not canonical")
    if any(part in {".", ".."} for part in path.split("/")):
        raise RuntimeError("source path traversal is forbidden")

def _validate_active_authorization_and_dispatch() -> None:
    if not ACTIVE_RECEIPT.exists():
        raise RuntimeError("v2.1F live vintage preflight authorization is not active")
    if not DISPATCH.exists():
        raise RuntimeError("v2.1F live vintage preflight dispatch is not active")

    receipt = _load(ACTIVE_RECEIPT)
    contract = _load(CONTRACT)
    dispatch = _load(DISPATCH)

    if receipt.get("decision_status") != "approved":
        raise RuntimeError("v2.1F preflight receipt is not approved")
    if receipt.get("methodology_version") != "2.1F-design-candidate":
        raise RuntimeError("v2.1F methodology version changed")
    if receipt.get("execution_scope") != "live_historical_vintage_feasibility_preflight_only":
        raise RuntimeError("v2.1F preflight scope changed")
    if receipt.get("exact_series") != EXPECTED_SERIES:
        raise RuntimeError("v2.1F exact-series inventory changed")
    if receipt.get("data_window") != {"start": START.isoformat(), "end": END.isoformat()}:
        raise RuntimeError("v2.1F authorized data window changed")
    auth = receipt.get("authorizations", {})
    if not isinstance(auth, dict):
        raise RuntimeError("v2.1F receipt authorizations missing")
    if auth.get("real_data_fetch") is not True or auth.get("live_vintage_preflight") is not True:
        raise RuntimeError("v2.1F live preflight flags are not active")
    for field in (
        "real_data_research",
        "candidate_score_computation",
        "paid_data",
        "source_contract_acceptance",
        "research_ledger_mutation",
        "public_artifact_replacement",
        "production",
    ):
        if auth.get(field) is not False:
            raise RuntimeError(f"{field} must remain false during v2.1F preflight")

    if contract.get("state") != "live_vintage_preflight_authorized":
        raise RuntimeError("v2.1F preflight execution contract is not active")
    if contract.get("active_authorization_receipt_expected_now") is not True:
        raise RuntimeError("v2.1F active receipt expectation is false")
    if contract.get("dispatch_marker_expected_now") is not True:
        raise RuntimeError("v2.1F dispatch expectation is false")
    current = contract.get("current_state", {})
    if not isinstance(current, dict):
        raise RuntimeError("v2.1F contract current state missing")
    if current.get("real_data_fetch_authorized") is not True:
        raise RuntimeError("real-data fetch is not active")
    if current.get("live_vintage_preflight_authorized") is not True:
        raise RuntimeError("live preflight is not active")
    for field in (
        "real_data_research_authorized",
        "candidate_score_computation_authorized",
        "paid_data_authorized",
        "source_contract_acceptance_authorized",
        "durable_private_storage_authorized",
        "public_artifact_replacement_authorized",
        "research_ledger_mutation_authorized",
        "production_authorized",
    ):
        if current.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    if dispatch.get("version") != 1 or dispatch.get("state") != "dispatch_once":
        raise RuntimeError("v2.1F dispatch marker is invalid")
    if dispatch.get("phase") != "live_historical_vintage_feasibility_preflight":
        raise RuntimeError("v2.1F dispatch phase changed")
    if dispatch.get("issue") != "https://github.com/usdimpact/usd-impact-pipeline/issues/224":
        raise RuntimeError("v2.1F dispatch issue changed")
    if dispatch.get("data_window") != {"start": START.isoformat(), "end": END.isoformat()}:
        raise RuntimeError("v2.1F dispatch data window changed")
    if dispatch.get("candidate_score_computation_authorized") is not False:
        raise RuntimeError("candidate Score must remain forbidden in dispatch")
    if dispatch.get("production_authorized") is not False:
        raise RuntimeError("Production must remain forbidden in dispatch")
    activation_commit = contract.get("authorization_activation_merge_commit")
    if not isinstance(activation_commit, str) or len(activation_commit) != 40:
        raise RuntimeError("authorization activation merge commit is not pinned")
    if dispatch.get("authorization_activation_merge_commit") != activation_commit:
        raise RuntimeError("dispatch is not pinned to the active authorization merge")

def _get_fixed(host: str, path: str) -> tuple[bytes, str]:
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
                f"official source retrieval returned HTTP {response.status} for {host}{path}"
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

def extract_bls_release_dates(payload: bytes) -> list[date]:
    text = payload.decode("utf-8", errors="replace")
    pattern = re.compile(r"(?i)ppi_(\d{8})\.htm")
    found: set[date] = set()
    for raw in pattern.findall(text):
        try:
            value = date(int(raw[4:8]), int(raw[:2]), int(raw[2:4]))
        except ValueError:
            continue
        if START <= value <= END:
            found.add(value)
    return sorted(found)

def _bls_crude_petroleum_parseable(text: str) -> bool:
    lowered = re.sub(r"\s+", " ", text.lower())
    if "crude petroleum" not in lowered:
        return False
    return bool(
        re.search(r"\b05\s*-\s*61\b", lowered)
        or re.search(r"\b05\s+61\b", lowered)
        or re.search(r"\b0561\b", lowered)
    )

def run_preflight() -> dict[str, object]:
    _validate_active_authorization_and_dispatch()

    fed_summary: dict[str, dict[str, object]] = {}
    for family, cfg in FED_FAMILIES.items():
        index_payload, index_content_type = _get_fed(str(cfg["index_path"]))
        if "html" not in index_content_type and "text" not in index_content_type:
            raise RuntimeError(f"{family} release landing page is not HTML/text")
        landing_text = _html_text(index_payload)
        if not _matches_family(landing_text, cfg["landing_tokens"]):
            raise RuntimeError(f"{family} release landing page identity could not be verified")

        sample_dates = tuple(cfg["sample_dates"])
        parseable = 0
        for released in sample_dates:
            if not (START <= released <= END):
                raise RuntimeError(f"{family} fixed sample is outside the authorized window")
            text = _fed_archive_text(str(cfg["archive_code"]), released)
            if not _matches_family(text, cfg["tokens"]):
                raise RuntimeError(f"{family} sampled archive is not conservatively parseable")
            parseable += 1

        fed_summary[family] = {
            "archive_surface_verified": True,
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
            raise RuntimeError("BLS sampled archive does not expose crude petroleum code 05-61")
        bls_parseable += 1

    return {
        "status": "passed",
        "phase": "live_historical_vintage_feasibility_preflight",
        "authorized_data_window": {"start": START.isoformat(), "end": END.isoformat()},
        "exact_series_count": len(EXPECTED_SERIES),
        "federal_reserve": fed_summary,
        "bls": {
            "archived_news_release_count": len(bls_release_dates),
            "sampled_releases": len(BLS_SAMPLE_RELEASES),
            "crude_petroleum_parseable_samples": bls_parseable,
        },
        "source_payloads_persisted": False,
        "source_values_logged": False,
        "component_values_logged": False,
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
