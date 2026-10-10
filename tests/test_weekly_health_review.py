"""Offline review-state fixtures: no network, no publication, no workflow dispatch."""
from __future__ import annotations

import base64
import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

from scripts.check_weekly_health import Check, classify_health, render_report, write_health_status_output
from scripts.weekly_health_review import DRIVERS, valid_score_bridge, verify_pending_review


EXPECTED = "2026-10-09"
PREVIOUS = "2026-10-02"
RUN_ID = 123456
BRANCH = f"automation/weekly-usd-impact-{EXPECTED}-{RUN_ID}"
HEAD = "a" * 40
NOW = datetime(2026, 10, 10, 7, tzinfo=timezone.utc)
REPO = "usdimpact/usd-impact-pipeline"


def bridge(week=EXPECTED):
    names = sorted(DRIVERS)
    return {
        "week_ending": week,
        "score": -0.5,
        "regime": "Soft dollar regime",
        "drivers": [{"name": name, "contribution": -0.0625} for name in names],
        "source_provenance": {
            name: {
                "driver": name,
                "provider": "provider",
                "series": "canonical-ticker",
                "score_week": week,
                "observation_date": week,
                "status": "fresh",
                "retrieval_mode": "live",
                "age_days": 0,
                "max_age_days": 3,
            }
            for name in names
        },
    }


def weekly_run():
    return {
        "id": RUN_ID,
        "status": "completed",
        "conclusion": "success",
        "event": "schedule",
        "head_branch": "main",
        "run_started_at": "2026-10-10T00:55:00Z",
        "created_at": "2026-10-10T00:55:00Z",
    }


def pr():
    return {
        "title": f"Publish Weekly USD Impact Score \u2014 {EXPECTED}",
        "html_url": f"https://github.com/{REPO}/pull/133",
        "state": "open",
        "merged_at": None,
        "created_at": "2026-10-10T01:05:00Z",
        "head": {"ref": BRANCH, "sha": HEAD, "repo": {"full_name": REPO}},
        "base": {"ref": "main", "repo": {"full_name": REPO}},
    }


def encoded(payload):
    return {
        "type": "file",
        "encoding": "base64",
        "content": base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii"),
    }


class ReadOnlyGitHubFixture:
    def __init__(self):
        candidate = bridge()
        self.prs = [pr()]
        self.quality = [self.run_check()]
        self.attestation = [self.run_check()]
        self.files = {
            "public/data/weekly_input_latest.json": candidate,
            f"public/archive/{EXPECTED}/weekly_input.json": copy.deepcopy(candidate),
            f"public/archive/{EXPECTED}/score.json": {
                "metadata": {
                    "latest_date": EXPECTED,
                    "latest_score": -0.5,
                    "latest_regime": "Soft dollar regime",
                    "source_provenance": copy.deepcopy(candidate["source_provenance"]),
                }
            },
            f"public/archive/{EXPECTED}/repro_bundle.json": {
                "score_week": EXPECTED, "published": {"score": -0.5, "regime": "Soft dollar regime"}
            },
        }
        self.seen = []

    @staticmethod
    def run_check(conclusion="success", sha=HEAD):
        return {
            "head_sha": sha,
            "head_branch": BRANCH,
            "event": "workflow_dispatch",
            "status": "completed",
            "conclusion": conclusion,
        }

    def get(self, url):
        self.seen.append(url)
        uri = urlparse(url)
        params = parse_qs(uri.query)
        if uri.path.endswith("/pulls"):
            assert params["state"] == ["open"] and params["base"] == ["main"]
            return copy.deepcopy(self.prs)
        if uri.path.endswith("/actions/workflows/quality.yml/runs"):
            assert params["branch"] == [BRANCH] and params["event"] == ["workflow_dispatch"]
            return {"workflow_runs": copy.deepcopy(self.quality)}
        if uri.path.endswith("/actions/workflows/repro-attestation.yml/runs"):
            return {"workflow_runs": copy.deepcopy(self.attestation)}
        if "/contents/" in uri.path:
            assert params["ref"] == [HEAD], "Every candidate file must be pinned to exact head."
            name = uri.path.split("/contents/", 1)[1]
            return encoded(self.files[name])
        raise AssertionError(f"unexpected external query {url}")


class WeeklyHealthReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ReadOnlyGitHubFixture()

    def check(self, **overrides):
        args = {
            "repo": REPO,
            "expected_week": EXPECTED,
            "deployed_week": PREVIOUS,
            "weekly_run": weekly_run(),
            "get_json": self.fixture.get,
            "now": NOW,
        }
        args.update(overrides)
        return verify_pending_review(**args)

    def test_valid_source_contract_requires_exact_eight_fresh_live_drivers(self):
        self.assertTrue(valid_score_bridge(bridge(), EXPECTED))
        for mutate in (
            lambda b: b["source_provenance"]["BTC"].update(status="stale"),
            lambda b: b["source_provenance"]["DXY"].update(retrieval_mode="cached"),
            lambda b: b["source_provenance"]["WTI"].update(observation_date="2026-10-10"),
            lambda b: b["source_provenance"]["GOLD"].update(age_days=5),
            lambda b: b["drivers"].pop(),
            lambda b: b["drivers"][0].update(contribution=2.0),
            lambda b: b["source_provenance"].pop("VIX"),
        ):
            sample = bridge()
            mutate(sample)
            self.assertFalse(valid_score_bridge(sample, EXPECTED))

    def test_exact_head_review_is_pending_and_never_assumes_publication(self):
        decision = self.check()
        self.assertTrue(decision.verified, decision.reason)
        self.assertEqual(decision.head_sha, HEAD)
        self.assertEqual(decision.pr_url, f"https://github.com/{REPO}/pull/133")
        self.assertGreater(decision.age_hours, 0)
        self.assertEqual(len(self.fixture.seen), 7)

    def test_missing_or_wrong_run_cannot_validate_a_pr(self):
        self.assertFalse(self.check(weekly_run=None).verified)
        for key, value in (
            ("id", 999), ("conclusion", "failure"), ("status", "queued"),
            ("head_branch", "release"), ("event", "pull_request"),
            ("run_started_at", "2026-10-03T00:55:00Z"),
        ):
            run = weekly_run()
            run[key] = value
            self.assertFalse(self.check(weekly_run=run).verified, key)

    def test_no_prior_complete_release_or_very_old_vintage_is_not_pending(self):
        self.assertFalse(self.check(deployed_week=EXPECTED).verified)
        self.assertFalse(self.check(deployed_week="2026-09-25").verified)

    def test_only_exact_candidate_branch_base_head_and_same_repo_are_allowed(self):
        for field, value in (
            ("title", "Publish Weekly USD Impact Score \u2014 2026-10-02"),
            ("state", "closed"),
            ("merged_at", "2026-10-10T01:20:00Z"),
        ):
            sample = pr()
            sample[field] = value
            self.fixture.prs = [sample]
            self.assertFalse(self.check().verified, field)
        self.fixture.prs = [pr()]
        for side, key, value in (
            ("head", "ref", "automation/weekly-usd-impact-2026-10-09-999"),
            ("head", "sha", "b" * 40),
            ("head", "repo", {"full_name": "other/fork"}),
            ("base", "repo", {"full_name": "other/fork"}),
            ("base", "ref", "dev"),
        ):
            sample = pr()
            sample[side][key] = value
            self.fixture.prs = [sample]
            self.assertFalse(self.check().verified, f"{side}.{key}")

    def test_absent_duplicate_or_unbounded_pr_list_is_rejected(self):
        self.fixture.prs = []
        self.assertFalse(self.check().verified)
        self.fixture.prs = [pr(), pr()]
        self.assertFalse(self.check().verified)
        self.fixture.prs = [pr()] * 100
        self.assertFalse(self.check().verified)

    def test_both_exact_head_checks_are_mandatory(self):
        self.fixture.quality = []
        self.assertFalse(self.check().verified)
        self.fixture.quality = [self.fixture.run_check(sha="b" * 40)]
        self.assertFalse(self.check().verified)
        self.fixture.quality = [self.fixture.run_check(conclusion="failure"), self.fixture.run_check()]
        self.assertFalse(self.check().verified, "Latest failed rerun must take precedence")
        self.fixture.quality = [self.fixture.run_check()]
        self.fixture.attestation = [self.fixture.run_check(conclusion="failure")]
        self.assertFalse(self.check().verified)

    def test_candidate_bridge_archive_and_reproduction_must_agree(self):
        self.fixture.files["public/data/weekly_input_latest.json"]["source_provenance"]["GOLD"]["status"] = "stale"
        self.assertFalse(self.check().verified)
        self.fixture = ReadOnlyGitHubFixture()
        self.fixture.files[f"public/archive/{EXPECTED}/weekly_input.json"]["score"] = 0.25
        self.assertFalse(self.check().verified)
        self.fixture = ReadOnlyGitHubFixture()
        self.fixture.files[f"public/archive/{EXPECTED}/score.json"]["metadata"]["latest_score"] = 0.25
        self.assertFalse(self.check().verified)
        self.fixture = ReadOnlyGitHubFixture()
        self.fixture.files[f"public/archive/{EXPECTED}/repro_bundle.json"]["published"]["score"] = 0.25
        self.assertFalse(self.check().verified)

    def test_rejected_on_transport_error_not_reported_healthy(self):
        def offline(_url):
            raise TimeoutError("unreachable")
        result = self.check(get_json=offline)
        self.assertFalse(result.verified)
        self.assertIn("TimeoutError", result.reason)

    def test_configured_review_age_limit_escalates_without_default_invention(self):
        self.assertTrue(self.check().verified)
        self.assertFalse(self.check(max_pending_hours=2).verified)

    def test_report_marks_delayed_publication_not_healthy(self):
        checks = [
            Check("Latest weekly workflow conclusion", True, "success"),
            Check("Score date freshness", False, "Last live is previous Friday"),
            Check("Protected review evidence", True, "Head SHA verified"),
        ]
        report = render_report(
            checks,
            {
                "generated_at": NOW.isoformat(),
                "expected_date": EXPECTED,
                "pending_pr_url": f"https://github.com/{REPO}/pull/133",
                "pending_head_sha": HEAD,
                "pending_age_hours": "5.9",
            },
            status="PENDING_PROTECTED_REVIEW",
        )
        self.assertIn("Status: **PENDING_PROTECTED_REVIEW**", report)
        self.assertIn("DEFERRED \u2014 Score date freshness", report)
        self.assertIn("not deployed", report.lower())
        self.assertNotIn("Status: **HEALTHY**", report)
        self.assertIn(HEAD, report)


    def test_status_selection_defers_only_freshness_during_verified_review(self):
        from scripts.weekly_health_review import PendingReview
        verified = PendingReview(True, "verified", "https://github.com/usdimpact/usd-impact-pipeline/pull/133", HEAD, 5.9)
        rejected = PendingReview(False, "unverified")

        live = [
            Check("Latest weekly workflow conclusion", True, "success"),
            Check("Live source provenance", True, "all eight fresh at publication"),
            Check("Score date freshness", True, "expected week live"),
            Check("EN archive dashboard availability", True, "live"),
            Check("ES archive dashboard availability", True, "live"),
            Check("EN current route member gate", True, "protected"),
            Check("ES current route member gate", True, "protected"),
        ]
        self.assertEqual(classify_health(live, rejected), "HEALTHY")
        prior = [
            Check(c.name, False if c.name == "Score date freshness" else c.passed, c.detail)
            for c in live
        ] + [Check("Protected review evidence", True, "verified")]
        self.assertEqual(classify_health(prior, verified), "PENDING_PROTECTED_REVIEW")
        self.assertEqual(classify_health(prior, rejected), "UNHEALTHY")
        for failed in ("Live source provenance", "EN current route member gate", "ES archive dashboard availability"):
            damaged = [
                Check(c.name, False if c.name == failed else c.passed, c.detail)
                for c in prior
            ]
            self.assertEqual(classify_health(damaged, verified), "UNHEALTHY", failed)


    def test_actions_status_output_is_explicit_and_fail_closed(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "github_output"
            path.write_text("", encoding="utf-8")
            write_health_status_output(path, "PENDING_PROTECTED_REVIEW")
            self.assertEqual(path.read_text(encoding="utf-8"), "status=PENDING_PROTECTED_REVIEW\n")
            write_health_status_output(path, "HEALTHY")
            self.assertIn("status=HEALTHY\n", path.read_text(encoding="utf-8"))
            with self.assertRaises(ValueError):
                write_health_status_output(path, "READY_TO_MERGE")

    def test_workflow_never_closes_a_health_issue_for_pending_review(self):
        workflow_path = Path(__file__).resolve().parents[1] / ".github/workflows/weekly-health.yml"
        workflow = workflow_path.read_text(encoding="utf-8")
        self.assertIn("pull-requests: read", workflow)
        self.assertIn('--github-output "$GITHUB_OUTPUT"', workflow)
        self.assertIn(
            "if: steps.health.outcome == 'success' && steps.health.outputs.status == 'PENDING_PROTECTED_REVIEW'",
            workflow,
        )
        close_step = workflow.split("- name: Close recovered health issue", 1)[1]
        self.assertIn(
            "if: steps.health.outcome == 'success' && steps.health.outputs.status == 'HEALTHY'",
            close_step,
        )
        self.assertNotIn("if: steps.health.outcome == 'success'\n", close_step)
        self.assertIn("if: steps.health.outcome == 'failure'", workflow)

if __name__ == "__main__":
    unittest.main()
