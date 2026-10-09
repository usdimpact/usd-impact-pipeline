"""Fail-closed evidence for a weekly release awaiting protected GitHub review.

This module is read-only. It never dispatches a workflow or changes a publication.
"""
from __future__ import annotations

import base64
import json
import math
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable
from urllib.parse import quote, urlencode

DRIVERS = frozenset({"DXY", "WTI", "SPX", "VIX", "BTC", "GOLD", "UST_2Y", "UST_10Y"})
GITHUB_ACCEPT = "application/vnd.github+json"


@dataclass(frozen=True)
class PendingReview:
    verified: bool
    reason: str
    pr_url: str = ""
    head_sha: str = ""
    age_hours: float | None = None


def _utc(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("missing GitHub timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("GitHub timestamp must have a timezone")
    return parsed.astimezone(timezone.utc)


def _friday(value: str) -> date:
    parsed = date.fromisoformat(value)
    if parsed.weekday() != 4:
        raise ValueError("score week must be Friday")
    return parsed


def valid_score_bridge(bridge: Any, week: str) -> bool:
    """Validate a published/live bridge without pulling fresh market data."""
    try:
        completed = _friday(week)
        if not isinstance(bridge, dict) or bridge.get("week_ending") != week:
            return False
        value = bridge.get("score")
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
            return False
        if not isinstance(bridge.get("regime"), str) or not bridge["regime"].strip():
            return False

        provenance = bridge.get("source_provenance")
        drivers = bridge.get("drivers")
        if not isinstance(provenance, dict) or set(provenance) != DRIVERS:
            return False
        if not isinstance(drivers, list) or len(drivers) != len(DRIVERS):
            return False
        contribution_total = 0.0
        observed = set()
        for row in drivers:
            if not isinstance(row, dict) or row.get("name") not in DRIVERS or row["name"] in observed:
                return False
            observed.add(row["name"])
            contribution = row.get("contribution")
            if isinstance(contribution, bool) or not isinstance(contribution, (int, float)) or not math.isfinite(contribution):
                return False
            contribution_total += contribution
        if observed != DRIVERS or not math.isclose(contribution_total, value, rel_tol=0, abs_tol=1e-8):
            return False

        for name, source in provenance.items():
            if not isinstance(source, dict):
                return False
            if (source.get("driver") != name or source.get("score_week") != week
                    or source.get("status") != "fresh" or source.get("retrieval_mode") != "live"):
                return False
            if not isinstance(source.get("provider"), str) or not source["provider"].strip():
                return False
            if not isinstance(source.get("series"), str) or not source["series"].strip():
                return False
            observed_date = date.fromisoformat(source["observation_date"])
            age = source.get("age_days")
            limit = source.get("max_age_days")
            if any(isinstance(v, bool) or not isinstance(v, int) for v in (age, limit)):
                return False
            if age < 0 or limit < 0 or age > limit or (completed - observed_date).days != age:
                return False
        return True
    except (ValueError, TypeError, KeyError, OverflowError):
        return False


def _candidate_json(get_json: Callable[[str], Any], repo: str, path: str, sha: str) -> dict[str, Any]:
    url = (
        f"https://api.github.com/repos/{quote(repo, safe='/')}/contents/"
        f"{quote(path, safe='/')}?{urlencode({'ref': sha})}"
    )
    response = get_json(url)
    if not isinstance(response, dict) or response.get("encoding") != "base64":
        raise ValueError(f"candidate path has no base64 GitHub content: {path}")
    if response.get("type") != "file":
        raise ValueError(f"candidate path is not a regular file: {path}")
    raw = base64.b64decode(response.get("content", ""), validate=False)
    if not raw:
        raise ValueError(f"candidate path is empty: {path}")
    decoded = json.loads(raw.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError(f"candidate path is not an object: {path}")
    return decoded


def _exact_head_success(
    get_json: Callable[[str], Any], repo: str, workflow: str, branch: str, sha: str
) -> bool:
    params = urlencode({"branch": branch, "event": "workflow_dispatch", "per_page": 100})
    url = (
        f"https://api.github.com/repos/{quote(repo, safe='/')}/actions/"
        f"workflows/{quote(workflow, safe='')}/runs?{params}"
    )
    response = get_json(url)
    if not isinstance(response, dict) or not isinstance(response.get("workflow_runs"), list):
        return False
    runs = response["workflow_runs"]
    if len(runs) >= 100:
        return False  # Refuse a possibly incomplete first page.
    matching = [
        r for r in runs
        if isinstance(r, dict) and r.get("head_sha") == sha
        and r.get("head_branch") == branch and r.get("event") == "workflow_dispatch"
    ]
    # GitHub returns newest runs first: never ignore a later failing rerun.
    return bool(matching) and matching[0].get("status") == "completed" and matching[0].get("conclusion") == "success"


def verify_pending_review(
    *,
    repo: str,
    expected_week: str,
    deployed_week: str,
    weekly_run: dict[str, Any] | None,
    get_json: Callable[[str], Any],
    now: datetime,
    max_pending_hours: float | None = None,
) -> PendingReview:
    """Prove exactly one approved-for-review candidate, never infer publication.

    No pending age limit is hardcoded. An escalation policy must be explicitly
    approved and passed as max_pending_hours; old/stale deployments otherwise
    remain UNHEALTHY unless the protected candidate is proven anew each check.
    """
    try:
        expected = _friday(expected_week)
        deployed = _friday(deployed_week)
        if deployed != expected - timedelta(days=7):
            raise ValueError("live release is not the immediately previous completed week")
        if not isinstance(weekly_run, dict):
            raise ValueError("expected weekly run is missing")
        if weekly_run.get("status") != "completed" or weekly_run.get("conclusion") != "success":
            raise ValueError("latest weekly run has not succeeded")
        if weekly_run.get("event") not in {"schedule", "workflow_dispatch"}:
            raise ValueError("weekly run has an unexpected event")
        if weekly_run.get("head_branch") != "main":
            raise ValueError("weekly run was not on main")
        run_id = weekly_run.get("id")
        if isinstance(run_id, bool) or not isinstance(run_id, int) or run_id <= 0:
            raise ValueError("weekly run ID missing")
        started = _utc(weekly_run.get("run_started_at") or weekly_run.get("created_at"))
        run_week = started.date() - timedelta(days=(started.weekday() - 4) % 7)
        if run_week != expected:
            raise ValueError("weekly run belongs to a different Friday")

        params = urlencode({"state": "open", "base": "main", "per_page": 100})
        url = f"https://api.github.com/repos/{quote(repo, safe='/')}/pulls?{params}"
        response = get_json(url)
        if not isinstance(response, list) or len(response) >= 100:
            raise ValueError("open publication PR listing is missing or incomplete")
        branch = f"automation/weekly-usd-impact-{expected_week}-{run_id}"
        title = f"Publish Weekly USD Impact Score \u2014 {expected_week}"
        candidates = [
            pr for pr in response
            if isinstance(pr, dict)
            and pr.get("title") == title
            and isinstance(pr.get("head"), dict)
            and pr["head"].get("ref") == branch
        ]
        if len(candidates) != 1:
            raise ValueError("exact publication PR is missing or ambiguous")
        pr = candidates[0]
        if (pr.get("state") != "open" or pr.get("merged_at")
                or not isinstance(pr.get("base"), dict)
                or pr["base"].get("ref") != "main"):
            raise ValueError("candidate is not an open PR against main")
        head_repo = pr["head"].get("repo") or {}
        base_repo = pr["base"].get("repo") or {}
        if head_repo.get("full_name") != repo or base_repo.get("full_name") != repo:
            raise ValueError("candidate is not a same-repository publication PR")
        sha = pr["head"].get("sha")
        if not isinstance(sha, str) or re.fullmatch(r"[0-9a-f]{40}", sha) is None:
            raise ValueError("candidate has no immutable 40-character head SHA")
        pr_url = pr.get("html_url")
        if not isinstance(pr_url, str) or not pr_url.startswith(f"https://github.com/{repo}/pull/"):
            raise ValueError("candidate has no canonical GitHub PR URL")
        created = _utc(pr.get("created_at"))
        now_utc = now.astimezone(timezone.utc)
        if created < started - timedelta(minutes=2) or created > now_utc + timedelta(minutes=2):
            raise ValueError("candidate PR creation time is inconsistent")
        age_hours = max(0.0, (now_utc - created).total_seconds() / 3600)
        if max_pending_hours is not None and (max_pending_hours < 0 or age_hours > max_pending_hours):
            raise ValueError("candidate exceeded the explicitly configured review age")

        for name in ("quality.yml", "repro-attestation.yml"):
            if not _exact_head_success(get_json, repo, name, branch, sha):
                raise ValueError(f"{name} has no successful exact-head dispatch")

        bridge = _candidate_json(get_json, repo, "public/data/weekly_input_latest.json", sha)
        archived_bridge = _candidate_json(
            get_json, repo, f"public/archive/{expected_week}/weekly_input.json", sha
        )
        score = _candidate_json(
            get_json, repo, f"public/archive/{expected_week}/score.json", sha
        )
        bundle = _candidate_json(
            get_json, repo, f"public/archive/{expected_week}/repro_bundle.json", sha
        )
        if not valid_score_bridge(bridge, expected_week) or bridge != archived_bridge:
            raise ValueError("candidate bridge is invalid or differs from dated archive")
        metadata = score.get("metadata")
        if not isinstance(metadata, dict) or (
            metadata.get("latest_date") != expected_week
            or metadata.get("latest_score") != bridge["score"]
            or metadata.get("latest_regime") != bridge["regime"]
            or metadata.get("source_provenance") != bridge["source_provenance"]
        ):
            raise ValueError("candidate archive score and source provenance disagree")
        if (bundle.get("score_week") != expected_week
                or not isinstance(bundle.get("published"), dict)
                or bundle["published"].get("score") != bridge["score"]
                or bundle["published"].get("regime") != bridge["regime"]):
            raise ValueError("candidate reproduction bundle disagrees with published score")
        return PendingReview(
            verified=True,
            reason="exact expected-week PR, source vintage, and both head-bound validations verified",
            pr_url=pr_url,
            head_sha=sha,
            age_hours=age_hours,
        )
    except (Exception,) as error:
        # Fail closed, including on GitHub API outages and malformed payloads.
        return PendingReview(False, f"{type(error).__name__}: {error}")
