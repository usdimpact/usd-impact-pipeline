import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


class ReproductionSafetyWorkflowTests(unittest.TestCase):
    def test_rehearsal_is_live_strict_and_non_publishing(self):
        workflow = (WORKFLOWS / "repro-rehearsal.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", workflow)
        self.assertIn("python usd_impact_score_v2.py --web --output-dir public --backtest", workflow)
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

    def test_post_merge_attestation_is_read_only(self):
        workflow = (WORKFLOWS / "repro-attestation.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", workflow)
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
