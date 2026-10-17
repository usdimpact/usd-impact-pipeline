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

try:
    from .validate_weekly_release import EXPECTED_DRIVERS, canonical_regime, validate_source_provenance
except ImportError:  # Direct execution of the health script.
    from validate_weekly_release import EXPECTED_DRIVERS, canonical_regime, validate_source_provenance

DRIVERS = frozenset(EXPECTED_DRIVERS)
GITHUB_ACTIONS_APP_ID = 15368


@dataclass(frozen=True)
class PendingReview:
    verified: bool
    reason: str
    pr_url: str = ""
    head_sha: str = ""
    age_hours: float | None = None
    validation_urls: tuple[str, ...] = ()
    next_action: str = ""


class ValidationBlocked(ValueError):
    def __init__(self, reason: str, next_action: str):
        super().__init__(reason)
        self.next_action = next_action


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
        if bridge.get("regime") != canonical_regime(value):
            return False
        generation = bridge.get("generation")
        if (not isinstance(generation, dict) or generation.get("mode") != "deterministic"
                or generation.get("external_model_used") is not False
                or generation.get("external_event_claims_added") is not False):
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

        # Reuse the published source policy; a candidate cannot grant itself a
        # larger freshness allowance or replace a provider/ticker with a label.
        validate_source_provenance(
            {"source_provenance": provenance,
             "source_provenance_version": bridge.get("source_provenance_version")},
            bridge, week,
        )
        if isinstance(bridge.get("source_provenance_version"), bool):
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


def _positive_id(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} is missing or invalid")
    return value


def _latest_pr_run(
    get_json: Callable[[str], Any], repo: str, workflow: str, branch: str, sha: str,
    pr_number: int, created: datetime, now: datetime,
) -> dict[str, Any]:
    params = urlencode({"branch": branch, "event": "pull_request", "head_sha": sha, "per_page": 100})
    url = (
        f"https://api.github.com/repos/{quote(repo, safe='/')}/actions/"
        f"workflows/{quote(workflow, safe='')}/runs?{params}"
    )
    response = get_json(url)
    if not isinstance(response, dict) or not isinstance(response.get("workflow_runs"), list):
        raise ValueError(f"{workflow} PR workflow listing is missing")
    runs = response["workflow_runs"]
    if len(runs) >= 100 or response.get("total_count", len(runs)) != len(runs):
        raise ValueError(f"{workflow} PR workflow listing is incomplete")
    matching = [
        r for r in runs
        if isinstance(r, dict) and r.get("head_sha") == sha
        and r.get("head_branch") == branch and r.get("event") == "pull_request"
    ]
    if not matching:
        raise ValidationBlocked(
            f"{workflow} has no normal PR validation for the current source head",
            "Inspect the existing publication PR's required workflows. A successful manual dispatch does not replace its PR checks.",
        )
    ordered = []
    for run in matching:
        run_id = _positive_id(run.get("id"), "workflow run ID")
        _positive_id(run.get("run_attempt"), "workflow run attempt")
        _positive_id(run.get("workflow_id"), "workflow identity")
        _positive_id(run.get("check_suite_id"), "workflow check suite")
        if (run.get("path") != f".github/workflows/{workflow}"
                or (run.get("repository") or {}).get("full_name") != repo
                or (run.get("head_repository") or {}).get("full_name") != repo):
            raise ValueError(f"{workflow} PR workflow identity is inconsistent")
        associations = run.get("pull_requests")
        if not isinstance(associations, list):
            raise ValueError(f"{workflow} PR association metadata is missing")
        # GitHub may return [] even for a genuine PR run. In that case the
        # exact repository, unique publication branch and source SHA still bind
        # it; populated associations must explicitly agree with the candidate.
        if associations and not any(
            isinstance(pr, dict) and pr.get("number") == pr_number
            and (pr.get("head") or {}).get("sha") == sha
            and (pr.get("base") or {}).get("ref") == "main"
            for pr in associations
        ):
            raise ValueError(f"{workflow} is associated with another pull request")
        started = _utc(run.get("run_started_at"))
        updated = _utc(run.get("updated_at"))
        if (started < created - timedelta(minutes=2) or updated < started
                or updated > now + timedelta(minutes=2)):
            raise ValueError(f"{workflow} PR execution timestamps are inconsistent")
        # Creation order does not order reruns. An older-created workflow may
        # have a newer failed attempt; unresolved executions cannot be ignored.
        if run.get("status") != "completed":
            raise ValidationBlocked(
                f"{workflow} PR run {run_id} is {run.get('status', 'unknown')}",
                f"Wait for the existing PR workflow https://github.com/{repo}/actions/runs/{run_id}; do not regenerate the score.",
            )
        ordered.append((updated, started, run_id, run))
    return max(ordered, key=lambda item: item[:3])[3]


def _run_identity(run: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(run.get(key) for key in (
        "id", "run_attempt", "workflow_id", "path", "event", "head_sha",
        "head_branch", "check_suite_id", "status", "conclusion", "updated_at",
    )) + ((run.get("repository") or {}).get("full_name"),
          (run.get("head_repository") or {}).get("full_name"))


def _pr_workflow_evidence(
    get_json: Callable[[str], Any], repo: str, workflow: str, job_name: str,
    branch: str, sha: str, pr_number: int, created: datetime, now: datetime,
) -> tuple[dict[str, Any], str]:
    run = _latest_pr_run(get_json, repo, workflow, branch, sha, pr_number, created, now)
    run_id, attempt = run["id"], run["run_attempt"]
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}"
    if run.get("conclusion") != "success":
        conclusion = run.get("conclusion", "unknown")
        action = (
            f"Approve the existing {workflow} PR workflow at {run_url}, then wait for its checks; do not regenerate the score."
            if conclusion == "action_required" else
            f"Inspect and resolve the {workflow} PR check at {run_url} before protected publication review."
        )
        raise ValidationBlocked(f"{workflow} PR run {run_id} attempt {attempt}: {conclusion}", action)
    api = f"https://api.github.com/repos/{quote(repo, safe='/')}"
    current = get_json(f"{api}/actions/runs/{run_id}")
    if not isinstance(current, dict) or _run_identity(current) != _run_identity(run):
        raise ValueError(f"{workflow} changed while reading its latest attempt")
    jobs = get_json(f"{api}/actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100")
    if not isinstance(jobs, dict) or not isinstance(jobs.get("jobs"), list):
        raise ValueError(f"{workflow} latest-attempt jobs are missing")
    rows = jobs["jobs"]
    if len(rows) >= 100 or jobs.get("total_count", len(rows)) != len(rows):
        raise ValueError(f"{workflow} latest-attempt jobs are incomplete")
    matching = [job for job in rows if isinstance(job, dict) and job.get("name") == job_name]
    if len(matching) != 1:
        raise ValueError(f"{workflow} must have exactly one {job_name} job")
    job = matching[0]
    job_id = _positive_id(job.get("id"), "workflow job ID")
    _positive_id(job.get("run_id"), "job workflow run ID")
    _positive_id(job.get("run_attempt"), "job workflow run attempt")
    job_url = f"{run_url}/job/{job_id}"
    check_url = job.get("check_run_url")
    if not isinstance(check_url, str) or re.fullmatch(re.escape(f"{api}/check-runs/") + r"[1-9][0-9]*", check_url) is None:
        raise ValueError(f"{workflow} job check URL is not a canonical repository check")
    if (job.get("run_id") != run_id or job.get("run_attempt") != attempt
            or job.get("head_sha") != sha or job.get("html_url") != job_url
            or job.get("status") != "completed" or job.get("conclusion") != "success"):
        raise ValueError(f"{workflow} job does not prove success for this PR source head and attempt")
    check = get_json(check_url)
    if (not isinstance(check, dict) or check.get("id") != int(check_url.rsplit("/", 1)[1])
            or check.get("name") != job_name or check.get("head_sha") != sha
            or (check.get("app") or {}).get("id") != GITHUB_ACTIONS_APP_ID
            or (check.get("check_suite") or {}).get("id") != run["check_suite_id"]
            or check.get("details_url") != job_url
            or check.get("status") != "completed" or check.get("conclusion") != "success"):
        raise ValueError(f"{workflow} linked GitHub Actions check does not match the PR job")
    return run, job_url


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
    pr_url, sha, age_hours = "", "", None
    validation_urls: list[str] = []
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
        pr_number = _positive_id(pr.get("number"), "publication PR number")
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
        if pr_url != f"https://github.com/{repo}/pull/{pr_number}":
            raise ValueError("candidate has no canonical GitHub PR URL")
        created = _utc(pr.get("created_at"))
        if now.tzinfo is None:
            raise ValueError("verification time must have a timezone")
        now_utc = now.astimezone(timezone.utc)
        if created < started - timedelta(minutes=2) or created > now_utc + timedelta(minutes=2):
            raise ValueError("candidate PR creation time is inconsistent")
        age_hours = max(0.0, (now_utc - created).total_seconds() / 3600)
        if max_pending_hours is not None:
            if (isinstance(max_pending_hours, bool) or not isinstance(max_pending_hours, (int, float))
                    or not math.isfinite(max_pending_hours) or max_pending_hours < 0):
                raise ValueError("configured review age limit is invalid")
            if age_hours > max_pending_hours:
                raise ValueError("candidate exceeded the explicitly configured review age")

        validations = []
        for name, job in (("quality.yml", "validate-release"), ("repro-attestation.yml", "attest")):
            run, job_url = _pr_workflow_evidence(
                get_json, repo, name, job, branch, sha, pr_number, created, now_utc,
            )
            validations.append((name, run))
            validation_urls.append(job_url)

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
        # A concurrent PR update, merge or rerun invalidates this observation.
        current_pr = get_json(f"https://api.github.com/repos/{quote(repo, safe='/')}/pulls/{pr_number}")
        if (not isinstance(current_pr, dict) or current_pr.get("state") != "open"
                or current_pr.get("merged_at") or current_pr.get("number") != pr_number):
            raise ValueError("publication PR changed during verification")
        for side in ("head", "base"):
            before, after = pr.get(side) or {}, current_pr.get(side) or {}
            if (after.get("sha") != before.get("sha") or after.get("ref") != before.get("ref")
                    or (after.get("repo") or {}).get("full_name") != repo):
                raise ValueError("publication PR head, base or repository changed during verification")
        merge_state = current_pr.get("mergeable_state")
        if merge_state == "behind":
            raise ValidationBlocked(
                "publication PR is behind main; existing checks do not satisfy strict branch freshness",
                f"Update the existing publication PR branch at {pr_url} from main and wait for fresh normal PR checks; do not regenerate the score.",
            )
        if current_pr.get("mergeable") is not True or merge_state not in {"clean", "blocked"}:
            raise ValidationBlocked(
                f"publication PR mergeability is unresolved or failing: {merge_state}",
                f"Resolve or recheck the existing publication PR's mergeability at {pr_url}, then verify its current PR checks again.",
            )
        for name, run in validations:
            latest = _latest_pr_run(get_json, repo, name, branch, sha, pr_number, created, now_utc)
            if _run_identity(latest) != _run_identity(run):
                raise ValueError(f"{name} PR validation changed during verification")
        return PendingReview(
            verified=True,
            reason="expected-week candidate and both normal PR validation jobs verified at the source head; not deployed",
            pr_url=pr_url,
            head_sha=sha,
            age_hours=age_hours,
            validation_urls=tuple(validation_urls),
            next_action="Review the publication PR and complete GitHub's normal protected merge process. Validation does not authorize publication.",
        )
    except (Exception,) as error:
        # Fail closed, including on GitHub API outages and malformed payloads.
        return PendingReview(
            False, f"{type(error).__name__}: {error}", pr_url, sha, age_hours,
            tuple(validation_urls), getattr(error, "next_action", "Resolve the reported evidence failure before protected publication review."),
        )
