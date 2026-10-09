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

try:
    from .weekly_health_review import PendingReview, valid_score_bridge, verify_pending_review
except ImportError:  # Direct script execution via python scripts/check_weekly_health.py
    from weekly_health_review import PendingReview, valid_score_bridge, verify_pending_review

USER_AGENT = "usd-impact-weekly-health/1.0"
ENGLISH_HEADING = "Automated Regime Commentary"
SPANISH_HEADING = "Comentario Automático de Régimen"
MEMBER_GATE_HEADING = "Research Membership required"


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


def weekly_run_matches_expected_period(run_started_at: datetime, now: datetime) -> bool:
    """Return true when a weekly run belongs to the currently expected Friday period."""
    return latest_completed_friday(run_started_at.astimezone(timezone.utc).date()) == latest_completed_friday(
        now.astimezone(timezone.utc).date()
    )


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


def render_report(
    checks: list[Check], metadata: dict[str, str], *, status: str | None = None
) -> str:
    status = status or ("HEALTHY" if all(check.passed for check in checks) else "UNHEALTHY")
    if status not in {"HEALTHY", "PENDING_PROTECTED_REVIEW", "UNHEALTHY"}:
        raise ValueError(f"Unrecognized health status: {status}")
    lines = [
        "# Weekly USD Impact health report",
        "",
        f"Status: **{status}**",
        f"Generated: `{metadata['generated_at']}`",
        f"Expected score date: `{metadata.get('expected_date', 'unknown')}`",
    ]
    if metadata.get("workflow_run_url"):
        lines.append(f"Weekly workflow run: {metadata['workflow_run_url']}")

    lines.extend(["", "## Checks", ""])
    for check in checks:
        verdict = "PASS" if check.passed else "FAIL"
        if status == "PENDING_PROTECTED_REVIEW" and check.name == "Score date freshness":
            verdict = "DEFERRED"
        lines.append(f"- **{verdict} — {check.name}:** {check.detail}")

    if status == "PENDING_PROTECTED_REVIEW":
        lines.extend(
            [
                "",
                "## Protected human review required (not deployed)",
                "",
                f"- Verified publication PR: {metadata.get('pending_pr_url', 'unknown')}",
                f"- Exact validated head SHA: `{metadata.get('pending_head_sha', 'unknown')}`",
                f"- Review age: {metadata.get('pending_age_hours', 'unknown')} hours.",
                "- Previous validated public release remains live; do not call this a newly published week.",
                "- Review the PR and authorize its merge separately. Do not dispatch another weekly workflow solely because review is pending.",
            ]
        )
    elif status == "UNHEALTHY":
        lines.extend(
            [
                "",
                "## Required action",
                "",
                "Open the linked weekly workflow run, correct the failed condition, rerun the weekly pipeline if needed, and then rerun this health workflow.",
            ]
        )
    return "\n".join(lines) + "\n"


def classify_health(checks: list[Check], pending: PendingReview) -> str:
    """Only defer the known publication-date mismatch, never a real failure."""
    if all(check.passed for check in checks):
        return "HEALTHY"
    if pending.verified and all(
        check.passed or check.name == "Score date freshness" for check in checks
    ):
        return "PENDING_PROTECTED_REVIEW"
    return "UNHEALTHY"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check weekly USD Impact deployment health.")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--workflow", default="weekly.yml")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--base-url", default="https://usd-impact-pipeline.pages.dev")
    parser.add_argument("--report", type=Path, default=Path("weekly-health-report.md"))
    args = parser.parse_args()

    checks: list[Check] = []
    now = datetime.now(timezone.utc)
    expected_date = latest_completed_friday(now.date()).isoformat()
    metadata = {
        "generated_at": now.isoformat(),
        "expected_date": expected_date,
    }
    token = os.environ.get("GITHUB_TOKEN", "")
    latest_run: dict[str, Any] | None = None
    bridge: dict[str, Any] | None = None
    score_date = ""

    if not args.repo:
        checks.append(Check("GitHub repository", False, "GITHUB_REPOSITORY or --repo was not provided."))
    elif not token:
        checks.append(Check("GitHub authentication", False, "GITHUB_TOKEN was not provided."))
    else:
        try:
            run = github_workflow_run(args.repo, args.workflow, args.branch, token)
            latest_run = run
            metadata["workflow_run_url"] = str(run.get("html_url", ""))
            conclusion = str(run.get("conclusion", "unknown"))
            checks.append(
                Check(
                    "Latest weekly workflow conclusion",
                    conclusion == "success",
                    f"Latest completed run concluded `{conclusion}`.",
                )
            )

            started_at = parse_utc(str(run.get("run_started_at") or run.get("created_at")))
            run_period = latest_completed_friday(started_at.date()).isoformat()
            checks.append(
                Check(
                    "Latest weekly workflow period",
                    weekly_run_matches_expected_period(started_at, now),
                    f"Latest completed run maps to Friday `{run_period}`; expected `{expected_date}`.",
                )
            )
        except Exception as error:
            checks.append(Check("GitHub weekly workflow lookup", False, str(error)))

    base_url = args.base_url.rstrip("/")
    bridge_url = f"{base_url}/data/weekly_input_latest.json"
    try:
        bridge = request_json(bridge_url)
        score_date = str(bridge.get("week_ending", ""))
        checks.append(Check("Latest bridge JSON", True, f"Loaded `{bridge_url}` with week ending `{score_date or 'missing'}`."))
        checks.append(
            Check(
                "Live source provenance",
                valid_score_bridge(bridge, score_date),
                f"Eight fresh, live drivers and additive score are required for live vintage `{score_date}`.",
            )
        )
        checks.append(
            Check(
                "Score date freshness",
                score_date == expected_date,
                f"Deployed week ending is `{score_date or 'missing'}`; expected `{expected_date}`.",
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

    # Verify the actual last validated deployed archive when protected review is pending.
    # Do not mistake a previous completed Friday for the new expected publication.
    prior_week = (date.fromisoformat(expected_date) - timedelta(days=7)).isoformat()
    archive_week = prior_week if score_date == prior_week else expected_date

    # Current score routes are intentionally member-gated. Verify that boundary, then
    # verify deployed dated archive artifacts containing actual EN/ES score pages.
    for language, heading in (("en", ENGLISH_HEADING), ("es", SPANISH_HEADING)):
        current_url = f"{base_url}/{language}/"
        try:
            current_html = request_text(current_url)
            gated = MEMBER_GATE_HEADING in current_html
            checks.append(
                Check(
                    f"{language.upper()} current route member gate",
                    gated,
                    f"Expected member gate {'was found' if gated else 'was not found'} at `{current_url}`.",
                )
            )
        except Exception as error:
            checks.append(Check(f"{language.upper()} current route member gate", False, str(error)))

        archive_url = f"{base_url}/archive/{archive_week}/{language}.html"
        try:
            html = request_text(archive_url)
            checks.append(Check(f"{language.upper()} archive dashboard availability", True, f"Loaded `{archive_url}`."))
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
                    archive_week in html,
                    f"Deployed archive date `{archive_week}` {'was found' if archive_week in html else 'was not found'}.",
                )
            )
        except Exception as error:
            checks.append(Check(f"{language.upper()} archive dashboard availability", False, str(error)))

    pending = PendingReview(False, "not evaluated")
    if bridge is not None and score_date == prior_week and token and args.repo:
        github_headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        pending = verify_pending_review(
            repo=args.repo,
            expected_week=expected_date,
            deployed_week=score_date,
            weekly_run=latest_run,
            get_json=lambda url: request_json(url, headers=github_headers),
            now=now,
        )
        checks.append(
            Check(
                "Protected review evidence",
                pending.verified,
                f"{pending.reason}. PR: {pending.pr_url or 'unverified'}; head: {pending.head_sha or 'unverified'}.",
            )
        )

    status = classify_health(checks, pending)
    if status == "PENDING_PROTECTED_REVIEW":
        metadata["pending_pr_url"] = pending.pr_url
        metadata["pending_head_sha"] = pending.head_sha
        metadata["pending_age_hours"] = f"{pending.age_hours:.1f}"

    report = render_report(checks, metadata, status=status)
    args.report.write_text(report, encoding="utf-8")
    print(report)
    # Pending review is a non-incident but emphatically not a deployed/healthy release.
    # The workflow does not auto-merge; returning zero avoids a false failure issue.
    return 0 if status in {"HEALTHY", "PENDING_PROTECTED_REVIEW"} else 1


if __name__ == "__main__":
    sys.exit(main())
