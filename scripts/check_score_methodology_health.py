#!/usr/bin/env python3
"""Verify public Score v2 methodology artifacts and website links.

This is an operational health check only. It does not affect weekly score
publication. Remote JSON/schema are compared semantically with the checked-in
contracts, and the public methodology page must expose links to both artifacts.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USER_AGENT = "usd-impact-score-methodology-health/1.0"
DEFAULT_PIPELINE_BASE = "https://usd-impact-pipeline.pages.dev"
DEFAULT_SITE_PAGE = "https://www.usd-impact.com/score/methodology/"
EXPECTED_DRIVERS = ["DXY", "WTI", "SPX", "VIX", "BTC", "GOLD", "UST_2Y", "UST_10Y"]


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


def request_bytes(url: str, *, accept: str, attempts: int = 3) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
            with urlopen(request, timeout=30) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status} from {url}")
                return response.read()
        except (HTTPError, URLError, TimeoutError, RuntimeError) as error:
            last_error = error
            if attempt < attempts:
                time.sleep(attempt * 2)
    raise RuntimeError(f"Request failed after {attempts} attempts: {last_error}")


def request_json(url: str) -> dict[str, Any]:
    payload = json.loads(request_bytes(url, accept="application/json").decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object from {url}")
    return payload


def request_text(url: str) -> str:
    return request_bytes(url, accept="text/html").decode("utf-8", errors="replace")


def validate_contract_shape(payload: dict[str, Any]) -> None:
    if payload.get("methodology_version") != "usd_impact_score_v2":
        raise RuntimeError("Remote methodology_version is not usd_impact_score_v2")
    if payload.get("status") != "production":
        raise RuntimeError("Remote methodology status is not production")
    if payload.get("predictive_claim") is not False:
        raise RuntimeError("Remote methodology unexpectedly makes a predictive claim")
    drivers = payload.get("drivers")
    if not isinstance(drivers, list):
        raise RuntimeError("Remote methodology drivers are not an array")
    names = [str(item.get("name")) for item in drivers if isinstance(item, dict)]
    if names != EXPECTED_DRIVERS:
        raise RuntimeError(f"Remote methodology driver order mismatch: {names}")


def validate_schema_shape(payload: dict[str, Any]) -> None:
    if payload.get("title") != "USD Impact Score v2 methodology contract":
        raise RuntimeError("Remote methodology schema title mismatch")
    if payload.get("type") != "object" or payload.get("additionalProperties") is not False:
        raise RuntimeError("Remote methodology schema is not a closed object")
    properties = payload.get("properties") or {}
    methodology = properties.get("methodology_version") or {}
    status = properties.get("status") or {}
    if methodology.get("const") != "usd_impact_score_v2":
        raise RuntimeError("Remote schema methodology_version constraint drifted")
    if status.get("const") != "production":
        raise RuntimeError("Remote schema production-status constraint drifted")


def build_checks(
    *,
    local_contract: dict[str, Any],
    local_schema: dict[str, Any],
    remote_contract: dict[str, Any],
    remote_schema: dict[str, Any],
    methodology_html: str,
    contract_url: str,
    schema_url: str,
) -> list[Check]:
    checks: list[Check] = []
    try:
        validate_contract_shape(remote_contract)
        checks.append(Check("Remote methodology contract shape", True, "Production v2 contract fields are valid."))
    except Exception as error:
        checks.append(Check("Remote methodology contract shape", False, str(error)))

    try:
        validate_schema_shape(remote_schema)
        checks.append(Check("Remote methodology schema shape", True, "Closed schema constraints are valid."))
    except Exception as error:
        checks.append(Check("Remote methodology schema shape", False, str(error)))

    checks.append(
        Check(
            "Remote methodology equals checked-in contract",
            remote_contract == local_contract,
            "Semantic JSON equality confirmed." if remote_contract == local_contract else "Remote contract differs from checked-in public/data/score_v2_methodology.json.",
        )
    )
    checks.append(
        Check(
            "Remote schema equals checked-in schema",
            remote_schema == local_schema,
            "Semantic JSON equality confirmed." if remote_schema == local_schema else "Remote schema differs from checked-in public/data/score_v2_methodology.schema.json.",
        )
    )
    checks.append(
        Check(
            "Public methodology page links contract",
            contract_url in methodology_html and "Machine-readable methodology JSON" in methodology_html,
            "Contract URL and label are present." if contract_url in methodology_html and "Machine-readable methodology JSON" in methodology_html else "Contract URL/label is missing from the public methodology page.",
        )
    )
    checks.append(
        Check(
            "Public methodology page links schema",
            schema_url in methodology_html and "Methodology JSON Schema" in methodology_html,
            "Schema URL and label are present." if schema_url in methodology_html and "Methodology JSON Schema" in methodology_html else "Schema URL/label is missing from the public methodology page.",
        )
    )
    checks.append(
        Check(
            "Public methodology page preserves correlation-overlap disclosure",
            "effective correlated components" in methodology_html and "audit/transparency diagnostic" in methodology_html,
            "Correlation-overlap limitation disclosure is present." if "effective correlated components" in methodology_html and "audit/transparency diagnostic" in methodology_html else "Correlation-overlap audit limitation disclosure is missing.",
        )
    )
    return checks


def render_report(checks: list[Check], generated_at: str, contract_url: str, schema_url: str, page_url: str) -> str:
    healthy = all(check.passed for check in checks)
    lines = [
        "# Score methodology public health report",
        "",
        f"Status: **{'HEALTHY' if healthy else 'UNHEALTHY'}**",
        f"Generated: `{generated_at}`",
        f"Methodology JSON: {contract_url}",
        f"Methodology schema: {schema_url}",
        f"Public methodology page: {page_url}",
        "",
        "## Checks",
        "",
    ]
    for check in checks:
        lines.append(f"- **{'PASS' if check.passed else 'FAIL'} — {check.name}:** {check.detail}")
    if not healthy:
        lines.extend([
            "",
            "## Required action",
            "",
            "Verify the Cloudflare Pages deployment and the USD Impact methodology page. Do not change Score v2 methodology merely to clear an availability check.",
        ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline-base", default=DEFAULT_PIPELINE_BASE)
    parser.add_argument("--site-page", default=DEFAULT_SITE_PAGE)
    parser.add_argument("--contract", type=Path, default=Path("public/data/score_v2_methodology.json"))
    parser.add_argument("--schema", type=Path, default=Path("public/data/score_v2_methodology.schema.json"))
    parser.add_argument("--report", type=Path, default=Path("score-methodology-health-report.md"))
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    base = args.pipeline_base.rstrip("/")
    contract_url = f"{base}/data/score_v2_methodology.json"
    schema_url = f"{base}/data/score_v2_methodology.schema.json"

    local_contract = json.loads(args.contract.read_text(encoding="utf-8"))
    local_schema = json.loads(args.schema.read_text(encoding="utf-8"))
    checks: list[Check] = []

    try:
        remote_contract = request_json(contract_url)
        checks.append(Check("Methodology JSON availability", True, f"Loaded `{contract_url}`."))
    except Exception as error:
        checks.append(Check("Methodology JSON availability", False, str(error)))
        remote_contract = {}

    try:
        remote_schema = request_json(schema_url)
        checks.append(Check("Methodology schema availability", True, f"Loaded `{schema_url}`."))
    except Exception as error:
        checks.append(Check("Methodology schema availability", False, str(error)))
        remote_schema = {}

    try:
        methodology_html = request_text(args.site_page)
        checks.append(Check("Public methodology page availability", True, f"Loaded `{args.site_page}`."))
    except Exception as error:
        checks.append(Check("Public methodology page availability", False, str(error)))
        methodology_html = ""

    checks.extend(
        build_checks(
            local_contract=local_contract,
            local_schema=local_schema,
            remote_contract=remote_contract,
            remote_schema=remote_schema,
            methodology_html=methodology_html,
            contract_url=contract_url,
            schema_url=schema_url,
        )
    )
    report = render_report(checks, generated_at, contract_url, schema_url, args.site_page)
    args.report.write_text(report, encoding="utf-8")
    print(report)
    return 0 if all(check.passed for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
