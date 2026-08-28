from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path

from scripts import check_score_research_evidence_health as health


ROOT = Path(__file__).resolve().parents[1]


class ScoreResearchEvidenceHealthTests(unittest.TestCase):
    def test_pre_holdout_is_healthy_noop(self) -> None:
        for study in health.STUDIES:
            state = health.evaluate_study(
                study,
                published_week=date(2026, 8, 21),
                entry_weeks=[],
                open_prs=[],
            )
            self.assertEqual(state.status, "not_due")

    def test_landed_current_week_is_healthy(self) -> None:
        state = health.evaluate_study(
            health.STUDIES[0],
            published_week=date(2026, 8, 28),
            entry_weeks=["2026-08-28"],
            open_prs=[],
        )
        self.assertEqual(state.status, "landed")

    def test_exact_open_pr_requires_review(self) -> None:
        state = health.evaluate_study(
            health.STUDIES[0],
            published_week=date(2026, 8, 28),
            entry_weeks=[],
            open_prs=[
                {
                    "title": "Record Score v2 predictive evidence — 2026-08-28",
                    "url": "https://github.com/usdimpact/usd-impact-pipeline/pull/100",
                    "headRefName": "automation/score-v2-predictive-2026-08-28-123",
                }
            ],
        )
        self.assertEqual(state.status, "open_review_required")
        self.assertEqual(state.open_pr_url, "https://github.com/usdimpact/usd-impact-pipeline/pull/100")

    def test_wrong_branch_cannot_mask_missing_evidence(self) -> None:
        state = health.evaluate_study(
            health.STUDIES[1],
            published_week=date(2026, 8, 28),
            entry_weeks=[],
            open_prs=[
                {
                    "title": "Record Score v3 shadow research — 2026-08-28",
                    "url": "https://github.com/usdimpact/usd-impact-pipeline/pull/101",
                    "headRefName": "untrusted/score-v3-2026-08-28",
                }
            ],
        )
        self.assertEqual(state.status, "missing_evidence")

    def test_duplicate_exact_prs_fail_closed(self) -> None:
        prs = [
            {
                "title": "Record Score v3 shadow research — 2026-08-28",
                "url": f"https://github.com/usdimpact/usd-impact-pipeline/pull/{number}",
                "headRefName": f"automation/score-v3-shadow-2026-08-28-{number}",
            }
            for number in (102, 103)
        ]
        state = health.evaluate_study(
            health.STUDIES[1],
            published_week=date(2026, 8, 28),
            entry_weeks=[],
            open_prs=prs,
        )
        self.assertEqual(state.status, "duplicate_open_prs")

    def test_completed_v2_sample_does_not_require_later_weeks(self) -> None:
        state = health.evaluate_study(
            health.STUDIES[0],
            published_week=date(2027, 9, 3),
            entry_weeks=["2027-08-27"],
            open_prs=[],
            complete=True,
        )
        self.assertEqual(state.status, "complete")

    def test_repository_report_remains_claim_safe_across_holdout(self) -> None:
        report = health.build_health(ROOT, [])
        self.assertIs(report["performance_calculated"], False)
        self.assertIs(report["evidence_modified"], False)
        self.assertEqual(report["score_v3_engine_lock_status"], "verified")

        healthy_statuses = {"not_due", "landed", "complete"}
        statuses = {item["status"] for item in report["studies"]}
        expected_healthy = all(status in healthy_statuses for status in statuses)
        self.assertEqual(report["healthy"], expected_healthy)
        self.assertEqual(
            report["status"],
            "healthy" if expected_healthy else "attention_required",
        )

        published_week = date.fromisoformat(report["published_week"])
        if published_week < health.HOLDOUT_START:
            self.assertEqual(statuses, {"not_due"})
        elif "missing_evidence" in statuses:
            self.assertFalse(report["healthy"])

    def test_workflow_is_strictly_read_only(self) -> None:
        workflow = (ROOT / ".github/workflows/score-research-evidence-health.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("contents: read", workflow)
        self.assertIn("pull-requests: read", workflow)
        self.assertIn('--repo "$GITHUB_REPOSITORY"', workflow)
        self.assertIn("actions/setup-python@", workflow)
        self.assertIn("python -m pip install -r requirements.lock", workflow)
        for forbidden in (
            "contents: write",
            "pull-requests: write",
            "issues: write",
            "actions: write",
            "gh pr merge",
            "gh issue",
            "git push",
        ):
            self.assertNotIn(forbidden, workflow)


if __name__ == "__main__":
    unittest.main()
