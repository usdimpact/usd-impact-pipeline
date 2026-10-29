#!/usr/bin/env python3
"""Read-only Cloudflare Pages perimeter health check.

The current Score design intentionally denies premium HTML on Pages (403).
Only the main USD Impact website may authorize Research Membership HTML.
This monitor checks both production Pages origins with fixed paths only and
never fetches live market data, strict evidence, or private customer content.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ORIGINS = (
    "https://usd-impact-pipeline.pages.dev",
    "https://score.usd-impact.com",
)

MAX_BODY_BYTES = 4096
REQUEST_TIMEOUT_SECONDS = 12


@dataclass(frozen=True)
class CheckTarget:
    name: str
    path: str
    method: str
    expected_status: int
    read_body: bool


TARGETS = (
    CheckTarget("premium_html_denied", "/en/", "GET", 403, True),
    CheckTarget("retired_redemption_gone", "/score-redeem", "GET", 410, True),
    CheckTarget(
        "public_methodology_metadata",
        "/data/score_v2_methodology.json",
        "HEAD",
        200,
        False,
    ),
)


@dataclass(frozen=True)
class HttpObservation:
    status: int
    headers: Mapping[str, str]
    body: bytes = b""


def _headers(raw_headers: object) -> dict[str, str]:
    return {str(k).lower(): str(v).strip() for k, v in raw_headers.items()}


def fetch_fixed_url(origin: str, target: CheckTarget) -> HttpObservation:
    """Fetch a fixed allowed URL. Never read a public data-file body."""
    if origin not in ORIGINS or target not in TARGETS:
        raise ValueError("Unapproved origin or target")
    request = Request(
        f"{origin}{target.path}",
        method=target.method,
        headers={"User-Agent": "USD-Impact-Pages-Perimeter-Health/1.0"},
    )
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return HttpObservation(
                status=response.status,
                headers=_headers(response.headers),
                body=response.read(MAX_BODY_BYTES) if target.read_body else b"",
            )
    except HTTPError as error:
        try:
            return HttpObservation(
                status=error.code,
                headers=_headers(error.headers),
                body=error.read(MAX_BODY_BYTES) if target.read_body else b"",
            )
        finally:
            error.close()


def validate(target: CheckTarget, actual: HttpObservation) -> list[str]:
    """Pure, offline-testable policy checks; no HTTP access."""
    errors: list[str] = []
    if actual.status != target.expected_status:
        return [f"expected HTTP {target.expected_status}, observed {actual.status}"]

    if target.name == "public_methodology_metadata":
        if target.method != "HEAD" or target.read_body or actual.body:
            errors.append("metadata check must be body-free HEAD")
        return errors

    headers = {str(k).lower(): str(v).strip().lower() for k, v in actual.headers.items()}
    if headers.get("cache-control") != "private, no-store":
        errors.append("protected operational response must be no-store")
    if headers.get("x-content-type-options") != "nosniff":
        errors.append("missing nosniff")
    if headers.get("x-robots-tag") != "noindex, nofollow":
        errors.append("missing noindex")
    if headers.get("referrer-policy") != "no-referrer":
        errors.append("missing no-referrer policy")
    csp = headers.get("content-security-policy", "")
    if "default-src 'none'" not in csp or "frame-ancestors 'none'" not in csp:
        errors.append("missing restrictive CSP")

    body = actual.body.decode("utf-8", errors="replace")
    if target.name == "premium_html_denied":
        if "Research Membership required" not in body:
            errors.append("expected Pages premium denial body")
        if "https://www.usd-impact.com/score/" not in body:
            errors.append("missing same-origin membership referral")
    elif target.name == "retired_redemption_gone":
        if "Score redemption moved to usd-impact.com" not in body:
            errors.append("missing retired redemption tombstone")
    else:
        errors.append("unrecognized check target")
    return errors


def main() -> int:
    failures = 0
    for origin in ORIGINS:
        for target in TARGETS:
            try:
                errors = validate(target, fetch_fixed_url(origin, target))
            except (URLError, TimeoutError, OSError, ValueError) as exc:
                # Never display fetched response bodies, provider data, or secrets.
                errors = [f"request/contract error ({type(exc).__name__})"]
            if errors:
                failures += 1
                print(f"FAIL {origin} {target.name}: {', '.join(errors)}")
            else:
                print(f"PASS {origin} {target.name}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
