#!/usr/bin/env python3
"""Verify the weekly USD Impact workflow and deployed dashboard are current."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

USER_AGENT = "usd-impact-weekly-health/1.0"
ENGLISH_HEADING = "Automated Regime Commentary"
SPANISH_HEADING = "Comentario Automático de Régimen"


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def latest_completed_friday(run_date: date) -> date:
    """Return the most recent Friday that is complete on ``run_date``."""
    return run_date - timedelta(days=(run_date.weekday() - 4) % 7)


def request_bytes(url: str, headers: dict[str, str] | None = None, attempts: int = 3) -> bytes:
    request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    request_headers.update(headers or {})
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            request = Request(url, headers=request_headers)
            with urlopen(request, timeout=30) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status} from {url}")
                return response.read()
        except (HTTPError, URLError, TimeoutError, RuntimeError) as error:
            last_error = error
            if attempt < attempts:
                time.sleep(attempt * 2)

    raise RuntimeError(f"Request failed after {attempts} attempts: {last_error}")


def request_json(url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
    raw = request_bytes(url, headers=headers)
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected a JSON object from {url}")
    return payload


def request_text(url: str) -> str:
    return request_bytes(url, headers={"Accept": "text/html"}).decode("utf-8", errors="replace")


def github_workflow_run(repo: str, workflow: str, branch: str, token: str) -> dict[str, Any]:
    params = urlencode({"branch": branch, "status": "completed", "per_page": 5})
    url = (
        f"https://api.github.com/repos/{quote(repo, safe='/')}/actions/workflows/"
        f"{quote(workflow, safe='')}/runs?{params}"
    )
    payload = request_json(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    runs = payload.get("workflow_runs")
    if not isinstance(runs, list) or not runs:
        raise RuntimeError(f"No completed runs found for {workflow} on {branch}")
    return runs[0]


def render_report(checks: list[Check], metadata: dict[str, str]) -> str:
    healthy = all(check.passed for check in checks)
    lines = [
        "# Weekly USD Impact health report",
        "",
        f"Status: **{'HEALTHY' if healthy else 'UNHEALTHY'}**",
        f"Generated: `{metadata['generated_at']}`",
        f"Expected score date: `{metadata.get('expected_date', 'unknown')}`",
    ]
    if metadata.get("workflow_run_url"):
        lines.append(f"Weekly workflow run: {metadata['workflow_run_url']}")

    lines.extend(["", "## Checks", ""])
    for check in checks:
        lines.append(f"- **{'PASS' if check.passed else 'FAIL'} — {check.name}:** {check.detail}")

    if not healthy:
        lines.extend(
            [
                "",
                "## Required action",
                "",
                "Open the linked weekly workflow run, correct the failed condition, rerun the weekly pipeline if needed, and then rerun this health workflow.",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check weekly USD Impact deployment health.")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--workflow", default="weekly.yml")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--base-url", default="https://usd-impact-pipeline.pages.dev")
    parser.add_argument("--max-run-age-hours", type=float, default=36.0)
    parser.add_argument("--report", type=Path, default=Path("weekly-health-report.md"))
    args = parser.parse_args()

    checks: list[Check] = []
    metadata = {"generated_at": datetime.now(timezone.utc).isoformat()}
    expected_date: str | None = None
    token = os.environ.get("GITHUB_TOKEN", "")

    if not args.repo:
        checks.append(Check("GitHub repository", False, "GITHUB_REPOSITORY or --repo was not provided."))
    elif not token:
        checks.append(Check("GitHub authentication", False, "GITHUB_TOKEN was not provided."))
    else:
        try:
            run = github_workflow_run(args.repo, args.workflow, args.branch, token)
            metadata["workflow_run_url"] = str(run.get("html_url", ""))
            conclusion = str(run.get("conclusion", "unknown"))
            checks.append(
                Check(
                    "Latest weekly workflow conclusion",
                    conclusion == "success",
                    f"Latest completed run concluded `{conclusion}`.",
                )
            )

            completed_at = parse_utc(str(run.get("updated_at") or run.get("created_at")))
            age_hours = (datetime.now(timezone.utc) - completed_at).total_seconds() / 3600
            checks.append(
                Check(
                    "Latest weekly workflow freshness",
                    0 <= age_hours <= args.max_run_age_hours,
                    f"Latest completed run is {age_hours:.1f} hours old; limit is {args.max_run_age_hours:.1f} hours.",
                )
            )

            started_at = parse_utc(str(run.get("run_started_at") or run.get("created_at")))
            expected_date = latest_completed_friday(started_at.date()).isoformat()
            metadata["expected_date"] = expected_date
        except Exception as error:
            checks.append(Check("GitHub weekly workflow lookup", False, str(error)))

    base_url = args.base_url.rstrip("/")
    bridge_url = f"{base_url}/data/weekly_input_latest.json"
    bridge: dict[str, Any] | None = None
    try:
        bridge = request_json(bridge_url)
        score_date = str(bridge.get("week_ending", ""))
        checks.append(Check("Latest bridge JSON", True, f"Loaded `{bridge_url}` with week ending `{score_date or 'missing'}`."))
        checks.append(
            Check(
                "Score date freshness",
                bool(expected_date) and score_date == expected_date,
                f"Deployed week ending is `{score_date or 'missing'}`; expected `{expected_date or 'unknown'}`.",
            )
        )
        checks.append(
            Check(
                "Bridge score metadata",
                isinstance(bridge.get("score"), (int, float)) and isinstance(bridge.get("regime"), str),
                f"Score is `{bridge.get('score')}` and regime is `{bridge.get('regime')}`.",
            )
        )
    except Exception as error:
        checks.append(Check("Latest bridge JSON", False, str(error)))

    for language, heading in (("en", ENGLISH_HEADING), ("es", SPANISH_HEADING)):
        url = f"{base_url}/{language}/"
        try:
            html = request_text(url)
            checks.append(Check(f"{language.upper()} dashboard availability", True, f"Loaded `{url}`."))
            checks.append(
                Check(
                    f"{language.upper()} commentary heading",
                    heading in html,
                    f"Expected heading `{heading}` {'was found' if heading in html else 'was not found'}.",
                )
            )
            checks.append(
                Check(
                    f"{language.upper()} current score date",
                    bool(expected_date) and expected_date in html,
                    f"Expected date `{expected_date or 'unknown'}` {'was found' if expected_date and expected_date in html else 'was not found'}.",
                )
            )
        except Exception as error:
            checks.append(Check(f"{language.upper()} dashboard availability", False, str(error)))

    report = render_report(checks, metadata)
    args.report.write_text(report, encoding="utf-8")
    print(report)
    return 0 if all(check.passed for check in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
