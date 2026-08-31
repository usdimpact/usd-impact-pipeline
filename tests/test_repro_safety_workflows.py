import os
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.post_merge_repro_attestation import _attestation_context


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


class ReproductionSafetyWorkflowTests(unittest.TestCase):
    def test_rehearsal_is_live_strict_and_non_publishing(self):
        workflow = (WORKFLOWS / "repro-rehearsal.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", workflow)
        self.assertIn("python usd_impact_score_v2.py", workflow)
        self.assertIn("--weekly-levels-output", workflow)
        self.assertIn("--weekly-levels", workflow)
        self.assertIn("--provider-evidence-output", workflow)
        self.assertIn("--provider-evidence", workflow)
        self.assertIn("$RUNNER_TEMP/score-v2-rehearsal-weekly-levels.csv", workflow)
        self.assertEqual(
            workflow.count(
                "$RUNNER_TEMP/score-v2-rehearsal-provider-evidence.json"
            ),
            2,
        )
        self.assertNotIn("--live-refetch", workflow)
        self.assertIn("python -m scripts.build_score_repro_bundle", workflow)
        self.assertIn("python -m scripts.rehearse_score_repro_acceptance", workflow)
        self.assertIn('cp -a . "$work"', workflow)
        self.assertIn('rm -rf "public/archive/$WEEK"', workflow)
        self.assertIn("REHEARSAL ONLY", workflow)
        for forbidden in (
            "git push",
            "git commit",
            "git checkout -b",
            "gh pr create",
            "gh pr merge",
            "gh workflow run",
            "vercel",
            "wrangler",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, workflow.lower())

    def test_attestation_is_read_only_and_runs_before_and_after_merge(self):
        workflow = (WORKFLOWS / "repro-attestation.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", workflow)
        self.assertIn("pull_request:", workflow)
        self.assertIn("push:", workflow)
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn("python -m scripts.post_merge_repro_attestation", workflow)
        self.assertIn("python -m scripts.validate_methodology_contract", workflow)
        for forbidden in (
            "git push",
            "git commit",
            "git checkout -b",
            "gh pr create",
            "gh pr merge",
            "gh workflow run",
            "vercel",
            "wrangler",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, workflow.lower())

    def test_attestation_context_only_marks_push_to_main_as_post_merge(self):
        with patch.dict(
            os.environ,
            {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_REF": "refs/pull/31/merge"},
            clear=True,
        ):
            self.assertEqual(_attestation_context(), "pull_request_premerge")

        with patch.dict(
            os.environ,
            {"GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main"},
            clear=True,
        ):
            self.assertEqual(_attestation_context(), "main_post_merge")

        with patch.dict(
            os.environ,
            {"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/main"},
            clear=True,
        ):
            self.assertEqual(_attestation_context(), "manual_or_local_read_only")

        script = (ROOT / "scripts/post_merge_repro_attestation.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"acceptance_candidate": context == "main_post_merge"', script)

    def test_weekly_publication_stops_for_protected_review_after_exact_attestation(self):
        workflow = (WORKFLOWS / "weekly.yml").read_text(encoding="utf-8")
        dispatch = 'gh workflow run repro-attestation.yml --ref "$branch"'
        locate = "--workflow repro-attestation.yml"
        watch = 'gh run watch "$attestation_run_id" --exit-status'
        ready = (
            "Weekly USD Impact Score ${WEEK} passed exact-head quality and "
            "reproduction attestation."
        )

        self.assertIn(dispatch, workflow)
        self.assertIn(locate, workflow)
        self.assertIn('select(.headSha == \\"$head_sha\\")', workflow)
        self.assertIn(watch, workflow)
        self.assertIn(ready, workflow)
        self.assertIn(
            "The workflow then stops with the pull request open for protected human review.",
            workflow,
        )
        self.assertNotIn("gh pr merge", workflow)
        self.assertLess(workflow.index(dispatch), workflow.index(watch))
        self.assertLess(workflow.index(watch), workflow.index(ready))

    def test_weekly_recovery_respects_validated_open_publication_pr(self):
        workflow = (WORKFLOWS / "weekly-recovery.yml").read_text(encoding="utf-8")

        self.assertIn("pull-requests: read", workflow)
        self.assertIn(
            'expected_title="Publish Weekly USD Impact Score — ${expected_week}"',
            workflow,
        )
        self.assertIn(
            'expected_branch_prefix="automation/weekly-usd-impact-${expected_week}-"',
            workflow,
        )
        self.assertIn('quality_success="$(gh run list', workflow)
        self.assertIn('attestation_success="$(gh run list', workflow)
        self.assertIn(
            'if [ "$quality_success" -gt 0 ] && [ "$attestation_success" -gt 0 ]; then',
            workflow,
        )
        self.assertIn(
            "No recovery dispatch: validated publication PR is already open for "
            "protected human review",
            workflow,
        )
        self.assertLess(workflow.index("gh pr list"), workflow.index("weekly_recovery_decision.py"))
        self.assertNotIn("gh pr merge", workflow)

    def test_weekly_score_and_bundle_share_one_provider_fetch(self):
        workflow = (WORKFLOWS / "weekly.yml").read_text(encoding="utf-8")
        snapshot = "$RUNNER_TEMP/score-v2-weekly-levels.csv"
        evidence = "$RUNNER_TEMP/score-v2-provider-evidence.json"
        self.assertEqual(workflow.count(snapshot), 2)
        self.assertEqual(workflow.count(evidence), 2)
        self.assertIn("--weekly-levels-output", workflow)
        self.assertIn("--weekly-levels", workflow)
        self.assertIn("--provider-evidence-output", workflow)
        self.assertIn("--provider-evidence", workflow)
        self.assertNotIn("--live-refetch", workflow)

    def test_new_python_workflows_use_locked_environment(self):
        for workflow_name in ("repro-rehearsal.yml", "repro-attestation.yml"):
            workflow = (WORKFLOWS / workflow_name).read_text(encoding="utf-8")
            with self.subTest(workflow=workflow_name):
                self.assertIn("python-version: '3.11'", workflow)
                self.assertIn("cache-dependency-path: requirements.lock", workflow)
                self.assertIn("python -m pip install -r requirements.lock", workflow)
                self.assertIn("python -m pip check", workflow)

    def test_rehearsal_report_cannot_claim_acceptance(self):
        script = (ROOT / "scripts/rehearse_score_repro_acceptance.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"rehearsal_only": True', script)
        self.assertIn('"acceptance_evidence": False', script)
        self.assertIn('"publication_performed": False', script)
        self.assertIn('"deployment_performed": False', script)


if __name__ == "__main__":
    unittest.main()
