"""Offline health fixtures: no network, publication, or workflow dispatch.

Run/check IDs and source/merge SHAs were captured from the October 16 release.
The payloads and review states below are synthesized for regression tests; they
are not claims that the now-published PR #142 is currently pending or open.
"""
from __future__ import annotations

import base64
import contextlib
import copy
import io
import json
import re
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import parse_qs, unquote, urlparse

from scripts import check_weekly_health as health
from scripts.weekly_health_review import PendingReview, valid_score_bridge, verify_pending_review


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "2026-10-16"
PREVIOUS = "2026-10-09"
RUN_ID = 38984976938
PR_NUMBER = 142
BRANCH = f"automation/weekly-usd-impact-{EXPECTED}-{RUN_ID}"
HEAD = "7f7566edceaa658cadaa34863f19baabdc98baa4"
MERGE = "8e13ab0566dd64fc2466a0afef0d5e5377bd42f6"
BASE = "0be6a771e984a09b4ca1793c762f296a7d4dc2ca"
NOW = datetime(2026, 10, 17, 11, tzinfo=timezone.utc)
REPO = "usdimpact/usd-impact-pipeline"
API = f"https://api.github.com/repos/{REPO}"
WEB = f"https://github.com/{REPO}"
PUBLIC = "https://weekly-health.example.test"
PR_URL = f"{WEB}/pull/{PR_NUMBER}"
WORKFLOWS = {
    "quality.yml": {
        "id": 38985037389, "workflow_id": 324588474,
        "suite": 105655440364, "job": 117376724545,
        "name": "validate-release", "dispatch": 38985036037,
    },
    "repro-attestation.yml": {
        "id": 38985037394, "workflow_id": 341416162,
        "suite": 105655440385, "job": 117376772061,
        "name": "attest", "dispatch": 38985142975,
    },
}


def archived_json(week, name):
    return json.loads((ROOT / "public" / "archive" / week / name).read_text(encoding="utf-8"))


def bridge(week=EXPECTED):
    # Immutable released evidence keeps the fixture independent of validator constants.
    return archived_json(week, "weekly_input.json")


def weekly_run():
    return {
        "id": RUN_ID, "status": "completed", "conclusion": "success",
        "event": "schedule", "head_branch": "main", "head_sha": BASE,
        "run_attempt": 1, "path": ".github/workflows/weekly.yml",
        "run_started_at": "2026-10-17T00:08:00Z",
        "created_at": "2026-10-17T00:08:00Z",
        "updated_at": "2026-10-17T00:10:00Z",
        "html_url": f"{WEB}/actions/runs/{RUN_ID}",
        "repository": {"full_name": REPO}, "head_repository": {"full_name": REPO},
    }


def pr():
    return {
        "number": PR_NUMBER,
        "title": f"Publish Weekly USD Impact Score — {EXPECTED}",
        "html_url": PR_URL, "url": f"{API}/pulls/{PR_NUMBER}",
        "state": "open", "merged_at": None, "merged": False,
        "mergeable": True, "mergeable_state": "clean",
        "created_at": "2026-10-17T00:09:20Z", "merge_commit_sha": MERGE,
        "head": {"ref": BRANCH, "sha": HEAD, "repo": {"full_name": REPO}},
        "base": {"ref": "main", "sha": BASE, "repo": {"full_name": REPO}},
    }


def encoded(payload):
    return {
        "type": "file", "encoding": "base64",
        "content": base64.b64encode(json.dumps(payload).encode()).decode("ascii"),
    }


class ReadOnlyGitHubFixture:
    def __init__(self):
        self.prs = [pr()]
        self.pr_after = None
        self.runs = {}
        self.runs_after = {}
        self.run_totals = {}
        self.details = {}
        self.jobs = {}
        self.checks = {}
        self.list_calls = {}
        self.dispatches = {}
        self.seen = []
        for workflow, spec in WORKFLOWS.items():
            run = self.run_check(workflow)
            self.runs[workflow] = [run]
            self.install_evidence(run, spec["name"], spec["job"])
            manual = copy.deepcopy(run)
            manual.update(id=spec["dispatch"], event="workflow_dispatch", run_attempt=1,
                          html_url=f"{WEB}/actions/runs/{spec['dispatch']}")
            self.dispatches[workflow] = [manual]
        self.files = {
            "public/data/weekly_input_latest.json": bridge(),
            f"public/archive/{EXPECTED}/weekly_input.json": bridge(),
            f"public/archive/{EXPECTED}/score.json": archived_json(EXPECTED, "score.json"),
            f"public/archive/{EXPECTED}/repro_bundle.json": archived_json(EXPECTED, "repro_bundle.json"),
        }

    @staticmethod
    def run_check(workflow="quality.yml", **overrides):
        spec = WORKFLOWS[workflow]
        run = {
            "id": spec["id"], "workflow_id": spec["workflow_id"],
            "check_suite_id": spec["suite"], "run_attempt": 2,
            "path": f".github/workflows/{workflow}",
            "head_sha": HEAD, "head_branch": BRANCH, "event": "pull_request",
            "status": "completed", "conclusion": "success",
            "created_at": "2026-10-17T00:09:23Z",
            "run_started_at": "2026-10-17T10:41:30Z",
            "updated_at": "2026-10-17T10:42:47Z",
            "html_url": f"{WEB}/actions/runs/{spec['id']}",
            "url": f"{API}/actions/runs/{spec['id']}",
            "repository": {"full_name": REPO}, "head_repository": {"full_name": REPO},
            # Observed run metadata can omit PR associations. Exact run/job/check
            # source SHA is the binding; the synthetic merge SHA is not a substitute.
            "pull_requests": [],
        }
        run.update(overrides)
        return run

    def install_evidence(self, run, name, job_id):
        self.details[run["id"]] = copy.deepcopy(run)
        details_url = f"{WEB}/actions/runs/{run['id']}/job/{job_id}"
        job = {
            "id": job_id, "run_id": run["id"], "run_attempt": run["run_attempt"],
            "head_sha": run["head_sha"], "head_branch": run["head_branch"],
            "name": name, "status": run["status"], "conclusion": run["conclusion"],
            "started_at": run["run_started_at"], "completed_at": run["updated_at"],
            "check_run_url": f"{API}/check-runs/{job_id}",
            "url": f"{API}/actions/jobs/{job_id}", "html_url": details_url,
        }
        self.jobs[(run["id"], run["run_attempt"])] = [job]
        self.checks[job_id] = {
            "id": job_id, "name": name, "head_sha": run["head_sha"],
            "status": run["status"], "conclusion": run["conclusion"],
            "details_url": details_url, "url": f"{API}/check-runs/{job_id}",
            "app": {"id": 15368, "slug": "github-actions"},
            "check_suite": {"id": run["check_suite_id"], "head_sha": run["head_sha"],
                            "repository": {"full_name": REPO}},
        }

    def set_attempt(self, workflow, attempt, conclusion="success", status="completed"):
        run = self.runs[workflow][0]
        run.update(run_attempt=attempt, conclusion=conclusion, status=status)
        if attempt == 1:
            run.update(run_started_at="2026-10-17T00:09:23Z", updated_at="2026-10-17T00:09:24Z")
        spec = WORKFLOWS[workflow]
        self.install_evidence(run, spec["name"], spec["job"])

    def get(self, url):
        self.seen.append(url)
        uri = urlparse(url)
        params = parse_qs(uri.query)
        if uri.scheme != "https" or uri.netloc != "api.github.com" or not uri.path.startswith(f"/repos/{REPO}/"):
            raise AssertionError(f"Unexpected repository or host: {url}")
        suffix = uri.path.removeprefix(f"/repos/{REPO}/")
        if suffix == "pulls":
            assert params["state"] == ["open"] and params["base"] == ["main"]
            return copy.deepcopy(self.prs)
        if suffix == f"pulls/{PR_NUMBER}":
            return copy.deepcopy(self.pr_after if self.pr_after is not None else self.prs[0])
        match = re.fullmatch(r"actions/workflows/([^/]+)/runs", suffix)
        if match:
            workflow = unquote(match[1])
            assert params["branch"] == [BRANCH]
            if params.get("event") == ["workflow_dispatch"]:
                return {"total_count": 1, "workflow_runs": copy.deepcopy(self.dispatches[workflow])}
            assert params["event"] == ["pull_request"]
            assert params["head_sha"] == [HEAD]
            self.list_calls[workflow] = self.list_calls.get(workflow, 0) + 1
            rows = self.runs_after.get(workflow, self.runs[workflow]) if self.list_calls[workflow] > 1 else self.runs[workflow]
            return {"total_count": self.run_totals.get(workflow, len(rows)), "workflow_runs": copy.deepcopy(rows)}
        match = re.fullmatch(r"actions/runs/(\d+)/attempts/(\d+)/jobs", suffix)
        if match:
            key = tuple(map(int, match.groups()))
            jobs = self.jobs[key]
            return {"total_count": len(jobs), "jobs": copy.deepcopy(jobs)}
        match = re.fullmatch(r"actions/runs/(\d+)", suffix)
        if match:
            return copy.deepcopy(self.details[int(match[1])])
        match = re.fullmatch(r"check-runs/(\d+)", suffix)
        if match:
            return copy.deepcopy(self.checks[int(match[1])])
        if suffix.startswith("contents/"):
            assert params["ref"] == [HEAD], "Candidate content must use its immutable source head."
            return encoded(self.files[unquote(suffix.removeprefix("contents/"))])
        raise AssertionError(f"Unexpected external query: {url}")


class WeeklyHealthReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ReadOnlyGitHubFixture()

    def check(self, **overrides):
        args = dict(repo=REPO, expected_week=EXPECTED, deployed_week=PREVIOUS,
                    weekly_run=weekly_run(), get_json=self.fixture.get, now=NOW)
        args.update(overrides)
        return verify_pending_review(**args)

    def test_valid_source_contract_and_mutated_provenance(self):
        self.assertTrue(valid_score_bridge(bridge(), EXPECTED))
        mutations = {
            "stale": lambda b: b["source_provenance"]["BTC"].update(status="stale"),
            "cached": lambda b: b["source_provenance"]["DXY"].update(retrieval_mode="cached"),
            "future": lambda b: b["source_provenance"]["WTI"].update(observation_date="2026-10-17"),
            "bad age": lambda b: b["source_provenance"]["GOLD"].update(age_days=5),
            "forged SLA": lambda b: b["source_provenance"]["GOLD"].update(observation_date="2026-09-11", age_days=35, max_age_days=999),
            "provider": lambda b: b["source_provenance"]["GOLD"].update(provider="unapproved provider"),
            "provider code": lambda b: b["source_provenance"]["GOLD"].update(provider_code="fixture"),
            "series": lambda b: b["source_provenance"]["GOLD"].update(series="invented"),
            "source URL": lambda b: b["source_provenance"]["GOLD"].update(source_url="https://unapproved.example.test"),
            "version": lambda b: b.update(source_provenance_version=99),
            "missing provenance": lambda b: b["source_provenance"].pop("VIX"),
            "missing driver": lambda b: b["drivers"].pop(),
            "duplicate driver": lambda b: b["drivers"][0].update(name=b["drivers"][1]["name"]),
            "sum": lambda b: b["drivers"][0].update(contribution=2),
            "bool score": lambda b: b.update(score=True),
            "nan score": lambda b: b.update(score=float("nan")),
            "infinite contribution": lambda b: b["drivers"][0].update(contribution=float("inf")),
            "regime": lambda b: b.update(regime="Strong dollar regime"),
            "external claims": lambda b: b["generation"].update(external_event_claims_added=True),
            "external model": lambda b: b["generation"].update(external_model_used=True),
            "missing generation": lambda b: b.pop("generation"),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                sample = bridge()
                mutate(sample)
                self.assertFalse(valid_score_bridge(sample, EXPECTED))

    def test_oct16_source_head_with_approved_attempt_two_is_verified(self):
        decision = self.check()
        self.assertTrue(decision.verified, decision.reason)
        self.assertEqual((decision.pr_url, decision.head_sha), (PR_URL, HEAD))
        self.assertGreater(decision.age_hours, 0)
        self.assertEqual(len(decision.validation_urls), 2)
        for workflow, spec in WORKFLOWS.items():
            self.assertTrue(any(str(spec["id"]) in url for url in decision.validation_urls))
            self.assertIn(f"{API}/actions/runs/{spec['id']}/attempts/2/jobs", [url.split("?")[0] for url in self.fixture.seen])
            self.assertGreaterEqual(self.fixture.list_calls[workflow], 2)
        self.assertIn(f"{API}/pulls/{PR_NUMBER}", self.fixture.seen)
        self.assertTrue(decision.next_action)
        self.assertFalse(any("event=workflow_dispatch" in url for url in self.fixture.seen))

    def test_missing_or_wrong_generation_run_cannot_validate_candidate(self):
        self.assertFalse(self.check(weekly_run=None).verified)
        for key, value in (("id", 999), ("id", True), ("conclusion", "failure"), ("status", "queued"),
                           ("head_branch", "release"), ("event", "pull_request"),
                           ("run_started_at", "2026-10-10T00:08:00Z")):
            with self.subTest(key=key, value=value):
                run = weekly_run()
                run[key] = value
                self.assertFalse(self.check(weekly_run=run).verified)

    def test_live_release_must_be_immediately_previous_friday(self):
        for week in (EXPECTED, "2026-10-02", "2026-10-08", "invalid"):
            with self.subTest(week=week):
                self.assertFalse(self.check(deployed_week=week).verified)

    def test_exact_candidate_identity_and_canonical_url_are_required(self):
        mutations = (
            lambda p: p.update(title="Publish Weekly USD Impact Score — 2026-10-09"),
            lambda p: p.update(state="closed"),
            lambda p: p.update(merged_at="2026-10-17T10:45:00Z"),
            lambda p: p["head"].update(ref=f"automation/weekly-usd-impact-{EXPECTED}-999"),
            lambda p: p["head"].update(sha="b" * 40),
            lambda p: p["head"].update(sha="not-a-sha"),
            lambda p: p["head"].update(repo={"full_name": "other/fork"}),
            lambda p: p["base"].update(repo={"full_name": "other/fork"}),
            lambda p: p["base"].update(ref="dev"),
            lambda p: p.update(html_url="https://unapproved.example.test/pull/142"),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.fixture = ReadOnlyGitHubFixture()
                mutate(self.fixture.prs[0])
                self.assertFalse(self.check().verified)

    def test_missing_duplicate_and_incomplete_candidate_lists_fail_closed(self):
        for candidates in ([], [pr(), pr()], [pr()] * 100):
            with self.subTest(count=len(candidates)):
                self.fixture.prs = candidates
                self.assertFalse(self.check().verified)

    def test_dispatch_success_never_masks_normal_pr_action_required(self):
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow):
                self.fixture = ReadOnlyGitHubFixture()
                self.fixture.set_attempt(workflow, 1, conclusion="action_required")
                result = self.check()
                self.assertFalse(result.verified)
                self.assertEqual((result.pr_url, result.head_sha), (PR_URL, HEAD))
                self.assertRegex(result.next_action.lower(), r"approv|rerun")
                self.assertFalse(any("event=workflow_dispatch" in url for url in self.fixture.seen))

    def test_each_normal_pr_workflow_requires_actual_success(self):
        for workflow in WORKFLOWS:
            for status, conclusion in (("queued", None), ("in_progress", None), ("waiting", None),
                                       ("completed", "failure"), ("completed", "cancelled"),
                                       ("completed", "timed_out"), ("completed", "skipped"),
                                       ("completed", "neutral"), ("completed", None)):
                with self.subTest(workflow=workflow, status=status, conclusion=conclusion):
                    self.fixture = ReadOnlyGitHubFixture()
                    self.fixture.set_attempt(workflow, 2, conclusion, status)
                    self.assertFalse(self.check().verified)

    def test_missing_or_incomplete_workflow_runs_fail_closed(self):
        for workflow in WORKFLOWS:
            self.fixture = ReadOnlyGitHubFixture()
            self.fixture.runs[workflow] = []
            self.assertFalse(self.check().verified)
            self.fixture = ReadOnlyGitHubFixture()
            self.fixture.run_totals[workflow] = 101
            self.assertFalse(self.check().verified)

    def test_later_execution_overrides_api_creation_order(self):
        for status, conclusion in (("completed", "failure"), ("in_progress", None)):
            with self.subTest(status=status):
                self.fixture = ReadOnlyGitHubFixture()
                older = self.fixture.run_check(id=38985037388, created_at="2026-10-17T00:09:22Z",
                                              run_started_at="2026-10-17T10:50:00Z", updated_at="2026-10-17T10:51:00Z",
                                              run_attempt=3, status=status, conclusion=conclusion)
                older.update(html_url=f"{WEB}/actions/runs/{older['id']}", url=f"{API}/actions/runs/{older['id']}")
                self.fixture.runs["quality.yml"].append(older)
                self.fixture.install_evidence(older, "validate-release", 117376724544)
                self.assertFalse(self.check().verified)

    def test_old_completed_failure_can_be_superseded_but_unresolved_run_cannot(self):
        for status, conclusion, expected in (("completed", "failure", True), ("queued", None, False)):
            with self.subTest(status=status):
                self.fixture = ReadOnlyGitHubFixture()
                older = self.fixture.run_check(id=38985037388, created_at="2026-10-17T00:09:22Z",
                                              run_started_at="2026-10-17T00:09:23Z", updated_at="2026-10-17T00:10:00Z",
                                              run_attempt=1, status=status, conclusion=conclusion)
                older.update(html_url=f"{WEB}/actions/runs/{older['id']}", url=f"{API}/actions/runs/{older['id']}")
                self.fixture.runs["quality.yml"].append(older)
                self.fixture.install_evidence(older, "validate-release", 117376724544)
                self.assertEqual(self.check().verified, expected)

    def test_run_detail_is_bound_to_workflow_repository_head_and_attempt(self):
        mutations = {
            "id": lambda r: r.update(id=999),
            "attempt": lambda r: r.update(run_attempt=1),
            "path": lambda r: r.update(path=".github/workflows/unrelated.yml"),
            "event": lambda r: r.update(event="push"),
            "head": lambda r: r.update(head_sha="b" * 40),
            "branch": lambda r: r.update(head_branch="another-branch"),
            "repository": lambda r: r.update(repository={"full_name": "other/fork"}),
            "head repository": lambda r: r.update(head_repository={"full_name": "other/fork"}),
            "failure": lambda r: r.update(conclusion="failure"),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                self.fixture = ReadOnlyGitHubFixture()
                mutate(self.fixture.details[WORKFLOWS["quality.yml"]["id"]])
                self.assertFalse(self.check().verified)

    def test_populated_pr_associations_must_match_the_candidate(self):
        association = {"number": PR_NUMBER, "head": {"sha": HEAD}, "base": {"ref": "main"}}
        cases = (
            (None, False),
            ([dict(association, number=999)], False),
            ([dict(association, head={"sha": "b" * 40})], False),
            ([dict(association, base={"ref": "dev"})], False),
            ([association], True),
        )
        for associations, expected in cases:
            with self.subTest(associations=associations):
                self.fixture = ReadOnlyGitHubFixture()
                run = self.fixture.runs["quality.yml"][0]
                run["pull_requests"] = associations
                self.fixture.details[run["id"]]["pull_requests"] = copy.deepcopy(associations)
                self.assertEqual(self.check().verified, expected)

    def test_current_attempt_job_and_check_must_describe_same_execution(self):
        job_mutations = {
            "run": lambda j: j.update(run_id=999),
            "attempt": lambda j: j.update(run_attempt=1),
            "head": lambda j: j.update(head_sha="b" * 40),
            "name": lambda j: j.update(name="unrelated-job"),
            "failed": lambda j: j.update(conclusion="failure"),
            "pending": lambda j: j.update(status="in_progress", conclusion=None),
            "cross-repo URL": lambda j: j.update(check_run_url="https://api.github.com/repos/other/fork/check-runs/123"),
        }
        for label, mutate in job_mutations.items():
            with self.subTest(label=label):
                self.fixture = ReadOnlyGitHubFixture()
                mutate(self.fixture.jobs[(WORKFLOWS["quality.yml"]["id"], 2)][0])
                self.assertFalse(self.check().verified)
                if label == "cross-repo URL":
                    self.assertFalse(any("/repos/other/fork/" in url for url in self.fixture.seen))
        check_mutations = {
            "id": lambda c: c.update(id=999),
            "head": lambda c: c.update(head_sha="b" * 40),
            "name": lambda c: c.update(name="unrelated-job"),
            "app": lambda c: c.update(app={"id": 999, "slug": "github-actions"}),
            "suite": lambda c: c["check_suite"].update(id=999),
            "failed": lambda c: c.update(conclusion="failure"),
            "details run": lambda c: c.update(details_url=f"{WEB}/actions/runs/999/job/{WORKFLOWS['quality.yml']['job']}"),
            "details job": lambda c: c.update(details_url=f"{WEB}/actions/runs/{WORKFLOWS['quality.yml']['id']}/job/999"),
        }
        for label, mutate in check_mutations.items():
            with self.subTest(label=label):
                self.fixture = ReadOnlyGitHubFixture()
                mutate(self.fixture.checks[WORKFLOWS["quality.yml"]["job"]])
                self.assertFalse(self.check().verified)

    def test_synthetic_merge_sha_cannot_replace_the_source_head(self):
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow):
                self.fixture = ReadOnlyGitHubFixture()
                run = self.fixture.runs[workflow][0]
                run["head_sha"] = MERGE
                spec = WORKFLOWS[workflow]
                self.fixture.install_evidence(run, spec["name"], spec["job"])
                self.assertFalse(self.check().verified)

    def test_final_run_listing_detects_attempt_or_result_race(self):
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow):
                self.fixture = ReadOnlyGitHubFixture()
                updated = copy.deepcopy(self.fixture.runs[workflow])
                updated[0].update(run_attempt=3, status="in_progress", conclusion=None,
                                  run_started_at="2026-10-17T10:55:00Z", updated_at="2026-10-17T10:55:00Z")
                self.fixture.runs_after[workflow] = updated
                self.assertFalse(self.check().verified)
                self.assertGreaterEqual(self.fixture.list_calls[workflow], 2)

    def test_final_pr_detail_detects_head_change_or_merge(self):
        for mutate in (lambda p: p["head"].update(sha="b" * 40),
                       lambda p: p.update(state="closed", merged_at="2026-10-17T10:55:00Z")):
            self.fixture = ReadOnlyGitHubFixture()
            self.fixture.pr_after = pr()
            mutate(self.fixture.pr_after)
            self.assertFalse(self.check().verified)

    def test_final_pr_mergeability_requires_current_conflict_free_branch(self):
        cases = (
            ("behind", True, False),
            ("dirty", False, False),
            ("dirty", True, False),
            ("unknown", None, False),
            ("unknown", True, False),
            ("unstable", True, False),
            ("clean", None, False),
            ("clean", False, False),
            ("blocked", True, True),
        )
        for state, mergeable, expected in cases:
            with self.subTest(state=state, mergeable=mergeable):
                self.fixture = ReadOnlyGitHubFixture()
                self.fixture.pr_after = pr()
                self.fixture.pr_after.update(mergeable=mergeable, mergeable_state=state)
                result = self.check()
                self.assertEqual(result.verified, expected, result.reason)
                self.assertEqual((result.pr_url, result.head_sha), (PR_URL, HEAD))
                if state == "behind":
                    self.assertRegex(result.next_action.lower(), r"update[^\n]*branch")
                    self.assertRegex(result.next_action.lower(), r"fresh[^\n]*(?:check|validation)")

    def test_candidate_bridge_score_and_bundle_must_agree(self):
        cases = (
            ("public/data/weekly_input_latest.json", lambda p: p["source_provenance"]["GOLD"].update(status="stale")),
            (f"public/archive/{EXPECTED}/weekly_input.json", lambda p: p.update(score=0.25)),
            (f"public/archive/{EXPECTED}/score.json", lambda p: p["metadata"].update(latest_score=0.25)),
            (f"public/archive/{EXPECTED}/score.json", lambda p: p["metadata"]["source_provenance"]["GOLD"].update(series="wrong")),
            (f"public/archive/{EXPECTED}/repro_bundle.json", lambda p: p["published"].update(score=0.25)),
        )
        for path, mutate in cases:
            with self.subTest(path=path):
                self.fixture = ReadOnlyGitHubFixture()
                mutate(self.fixture.files[path])
                self.assertFalse(self.check().verified)

    def test_transport_failure_and_explicit_age_limit_fail_closed(self):
        def offline(_url):
            raise TimeoutError("unreachable")
        result = self.check(get_json=offline)
        self.assertFalse(result.verified)
        self.assertIn("TimeoutError", result.reason)
        self.assertTrue(self.check().verified)
        self.assertFalse(self.check(max_pending_hours=2).verified)


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW.astimezone(tz) if tz is not None else NOW.replace(tzinfo=None)


class MainFixture:
    def __init__(self, week=EXPECTED):
        self.github = ReadOnlyGitHubFixture()
        self.week = week
        self.live_bridge = bridge(week)
        self.live_archive = bridge(week)
        self.dashboard_values = {"en": f"{self.live_bridge['score']:.2f}", "es": f"{self.live_bridge['score']:.2f}"}
        self.gates = {"en": True, "es": True}
        self.bad_archive_shape = False
        self.seen = []

    def request_bytes(self, url, headers=None, attempts=3):
        self.seen.append(url)
        if url.startswith(API):
            if "/actions/workflows/weekly.yml/runs" in url:
                payload = {"workflow_runs": [weekly_run()], "total_count": 1}
            else:
                payload = self.github.get(url)
            return json.dumps(payload).encode()
        if not url.startswith(PUBLIC + "/"):
            raise AssertionError(f"Unexpected request: {url}")
        path = urlparse(url).path
        if path == "/data/weekly_input_latest.json":
            return json.dumps(self.live_bridge).encode()
        if path == f"/archive/{self.week}/weekly_input.json":
            return json.dumps([] if self.bad_archive_shape else self.live_archive).encode()
        for language, heading in (("en", health.ENGLISH_HEADING), ("es", health.SPANISH_HEADING)):
            if path == f"/{language}/":
                return (health.MEMBER_GATE_HEADING if self.gates[language] else "Unprotected dashboard").encode()
            if path == f"/archive/{self.week}/{language}.html":
                value = self.dashboard_values[language]
                score_html = "" if value is None else f'<div class="value score-value">{value}</div>'
                return f"<h2>{heading}</h2><time>{self.week}</time>{score_html}".encode()
        raise AssertionError(f"Unexpected public artifact: {url}")


class WeeklyHealthMainTests(unittest.TestCase):
    def run_main(self, fixture):
        with TemporaryDirectory() as directory:
            report = Path(directory) / "health.md"
            output = Path(directory) / "github_output"
            argv = ["check_weekly_health.py", "--repo", REPO, "--base-url", PUBLIC,
                    "--report", str(report), "--github-output", str(output)]
            stdout = io.StringIO()
            with patch.object(health, "datetime", FrozenDateTime), \
                 patch.object(health, "request_bytes", side_effect=fixture.request_bytes), \
                 patch.object(health, "urlopen", side_effect=AssertionError("Network is forbidden")), \
                 patch.dict(health.os.environ, {"GITHUB_TOKEN": "offline-fixture"}), \
                 patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout):
                code = health.main()
            return code, report.read_text(), output.read_text(), stdout.getvalue()

    def assert_state(self, result, state, code):
        self.assertEqual(result[0], code)
        self.assertIn(f"Status: **{state}**", result[1])
        self.assertEqual(result[2], f"status={state}\n")
        self.assertIn(result[1], result[3])

    def test_current_coherent_release_is_healthy(self):
        fixture = MainFixture()
        self.assert_state(self.run_main(fixture), "HEALTHY", 0)
        self.assertIn(f"{PUBLIC}/archive/{EXPECTED}/weekly_input.json", fixture.seen)

    def test_real_array_shaped_pr_transport_reaches_pending_state(self):
        fixture = MainFixture(PREVIOUS)
        result = self.run_main(fixture)
        self.assert_state(result, "PENDING_PROTECTED_REVIEW", 0)
        self.assertIn("DEFERRED — Score date freshness", result[1])
        self.assertIn(PR_URL, result[1])
        self.assertIn(HEAD, result[1])
        self.assertIn("not deployed", result[1].lower())
        self.assertTrue(any(urlparse(url).path.endswith("/pulls") for url in fixture.seen))

    def test_public_json_reader_remains_object_only(self):
        for value in ([], "unexpected", True, 4, None):
            with self.subTest(value=value), patch.object(health, "request_bytes", return_value=json.dumps(value).encode()):
                with self.assertRaises(RuntimeError):
                    health.request_json(f"{PUBLIC}/data/weekly_input_latest.json")
        with patch.object(health, "request_bytes", return_value=b"[]"):
            self.assertEqual(health.request_json(f"{API}/pulls", allow_list=True), [])
        with patch.object(health, "request_bytes", return_value=b"true"):
            with self.assertRaises(RuntimeError):
                health.request_json(f"{API}/pulls", allow_list=True)

    def test_live_archive_mismatch_or_array_cannot_report_recovery(self):
        for shape in ("different", "array"):
            with self.subTest(shape=shape):
                fixture = MainFixture()
                if shape == "array":
                    fixture.bad_archive_shape = True
                else:
                    fixture.live_archive["score"] += 0.01
                self.assert_state(self.run_main(fixture), "UNHEALTHY", 1)

    def test_wrong_or_missing_dashboard_score_cannot_report_recovery(self):
        for language in ("en", "es"):
            for value in ("999", None):
                with self.subTest(language=language, value=value):
                    fixture = MainFixture()
                    fixture.dashboard_values[language] = value
                    self.assert_state(self.run_main(fixture), "UNHEALTHY", 1)

    def test_pending_candidate_does_not_hide_live_source_or_gate_failure(self):
        for damage in ("source", "gate", "archive", "dashboard"):
            with self.subTest(damage=damage):
                fixture = MainFixture(PREVIOUS)
                if damage == "source":
                    fixture.live_bridge["source_provenance"]["GOLD"]["provider"] = "unapproved"
                    fixture.live_archive = copy.deepcopy(fixture.live_bridge)
                elif damage == "gate":
                    fixture.gates["es"] = False
                elif damage == "archive":
                    fixture.live_archive["score"] += 0.01
                else:
                    fixture.dashboard_values["en"] = "999"
                result = self.run_main(fixture)
                self.assert_state(result, "UNHEALTHY", 1)
                # The candidate is valid, but repairing the live failure must
                # take precedence over the candidate's normal merge guidance.
                self.assertIn("PASS — Protected review evidence", result[1])
                required_action = result[1].split("## Required action", 1)[1].strip()
                self.assertTrue(required_action.startswith("Inspect the failed checks"))
                self.assertIn("correct", required_action)
                self.assertIn("verify health", required_action)
                self.assertNotRegex(required_action, r"(?i)\b(?:complete|proceed with|authorize)\b[^\n]*\bmerge\b")

    def test_action_required_stays_unhealthy_with_pr_and_next_action(self):
        fixture = MainFixture(PREVIOUS)
        fixture.github.set_attempt("quality.yml", 1, "action_required")
        result = self.run_main(fixture)
        self.assert_state(result, "UNHEALTHY", 1)
        self.assertIn(PR_URL, result[1])
        self.assertIn(HEAD, result[1])
        self.assertRegex(result[1].lower(), r"approv|rerun")
        self.assertNotIn("Status: **HEALTHY**", result[1])
        required_action = result[1].split("## Required action", 1)[1].strip()
        self.assertTrue(required_action.startswith("Inspect the failed checks"))

    def test_old_release_or_missing_candidate_is_unhealthy(self):
        fixture = MainFixture("2026-10-02")
        self.assert_state(self.run_main(fixture), "UNHEALTHY", 1)
        fixture = MainFixture(PREVIOUS)
        fixture.github.prs = []
        self.assert_state(self.run_main(fixture), "UNHEALTHY", 1)


class WeeklyHealthStateTests(unittest.TestCase):
    def test_missing_checks_cannot_report_healthy_or_pending(self):
        self.assertEqual(health.classify_health([], PendingReview(False, "missing")), "UNHEALTHY")
        self.assertEqual(health.classify_health([], PendingReview(True, "verified", PR_URL, HEAD, 5.9)), "UNHEALTHY")

    def test_status_selection_defers_only_date_freshness(self):
        verified = PendingReview(True, "verified", PR_URL, HEAD, 5.9)
        rejected = PendingReview(False, "unverified")
        names = ("Latest weekly workflow conclusion", "Live source provenance", "Score date freshness",
                 "EN archive dashboard availability", "ES archive dashboard availability",
                 "EN current route member gate", "ES current route member gate")
        live = [health.Check(name, True, "verified") for name in names]
        self.assertEqual(health.classify_health(live, rejected), "HEALTHY")
        prior = [health.Check(c.name, c.name != "Score date freshness", c.detail) for c in live]
        self.assertEqual(health.classify_health(prior, verified), "PENDING_PROTECTED_REVIEW")
        self.assertEqual(health.classify_health(prior, rejected), "UNHEALTHY")
        for failed in names:
            if failed != "Score date freshness":
                damaged = [health.Check(c.name, False if c.name == failed else c.passed, c.detail) for c in prior]
                self.assertEqual(health.classify_health(damaged, verified), "UNHEALTHY", failed)

    def test_actions_status_output_is_typed(self):
        for status in ("HEALTHY", "PENDING_PROTECTED_REVIEW", "UNHEALTHY"):
            with self.subTest(status=status), TemporaryDirectory() as directory:
                path = Path(directory) / "github_output"
                health.write_health_status_output(path, status)
                self.assertEqual(path.read_text(), f"status={status}\n")
                with self.assertRaises(ValueError):
                    health.write_health_status_output(path, "READY_TO_MERGE")

    def test_workflow_close_guard_is_exact_and_requires_typed_healthy(self):
        workflow = (ROOT / ".github/workflows/weekly-health.yml").read_text()
        close_step = workflow.split("- name: Close recovered health issue", 1)[1].split("\n      - name:", 1)[0]
        condition = re.search(r"^\s+if:\s*(.+)$", close_step, re.M).group(1)
        self.assertEqual(condition, "steps.health.outcome == 'success' && steps.health.outputs.status == 'HEALTHY'")
        self.assertIn("pull-requests: read", workflow)
        self.assertIn('--github-output "$GITHUB_OUTPUT"', workflow)
        self.assertIn("steps.health.outcome == 'failure'", workflow)
        self.assertIn("steps.health.outputs.status == 'PENDING_PROTECTED_REVIEW'", workflow)
        self.assertNotIn("gh pr merge", workflow)
        self.assertNotIn("gh workflow run", workflow)


if __name__ == "__main__":
    unittest.main()
