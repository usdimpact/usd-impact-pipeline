from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ScorePublicationRightsWorkflowTests(unittest.TestCase):
    def read(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_policy_is_currently_hold(self) -> None:
        policy = json.loads(
            (ROOT / "governance/score-publication-rights-gate.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(policy["state"], "hold")
        self.assertEqual(
            policy["issue"],
            "https://github.com/usdimpact/usd-impact-pipeline/issues/155",
        )
        self.assertIsNone(policy["decision_receipt"])
        self.assertIsNone(policy["approved_by"])

    def test_weekly_generation_is_gated_before_provider_fetch(self) -> None:
        workflow = self.read(".github/workflows/weekly.yml")
        gate = workflow.index("Evaluate Score publication rights gate")
        setup = workflow.index("Set up Python 3.11")
        pipeline = workflow.index("Run score pipeline")
        self.assertLess(gate, setup)
        self.assertLess(gate, pipeline)
        self.assertIn(
            "needs.preflight.outputs.rights_hold == 'false' && "
            "needs.preflight.outputs.action == 'generate'",
            workflow,
        )
        self.assertIn(
            "no provider retrieval, generated write, branch push or publication PR",
            workflow,
        )

    def test_recovery_cannot_dispatch_while_hold_is_active(self) -> None:
        workflow = self.read(".github/workflows/weekly-recovery.yml")
        self.assertIn("Evaluate Score publication rights gate", workflow)
        self.assertIn(
            "if: steps.rights.outputs.hold == 'false'\n        env:",
            workflow,
        )
        self.assertIn("gh workflow run weekly.yml", workflow)

    def test_public_research_generation_is_gated(self) -> None:
        workflow = self.read(".github/workflows/research-validation.yml")
        self.assertIn("Evaluate Score publication rights gate", workflow)
        self.assertIn(
            "if: steps.rights.outputs.hold == 'false' && "
            "steps.upstream.outputs.ready == 'true'",
            workflow,
        )
        self.assertNotIn(
            "        if: steps.upstream.outputs.ready == 'true'\n",
            workflow,
        )
        self.assertLess(
            workflow.index("Evaluate Score publication rights gate"),
            workflow.index("Generate live point-in-time and robustness research"),
        )

    def test_prospective_research_jobs_depend_on_rights_gate(self) -> None:
        for path, job in (
            (".github/workflows/score-v3-shadow.yml", "ingest"),
            (".github/workflows/score-v2-predictive.yml", "record"),
        ):
            with self.subTest(path=path):
                workflow = self.read(path)
                self.assertIn("rights-gate:", workflow)
                self.assertIn(f"  {job}:\n    needs: rights-gate", workflow)
                self.assertIn(
                    "needs.rights-gate.outputs.hold == 'false'",
                    workflow,
                )
                self.assertIn(
                    "no research record or PR will be written",
                    workflow,
                )

    def test_reproduction_rehearsal_is_gated_before_live_provider_fetch(self) -> None:
        workflow = self.read(".github/workflows/repro-rehearsal.yml")
        self.assertLess(
            workflow.index("Evaluate Score publication rights gate"),
            workflow.index("Rehearse full release bundle and archive path"),
        )
        for step in (
            "Set up Python 3.11",
            "Install locked dependencies",
            "Verify machine-readable methodology contract",
            "Rehearse full release bundle and archive path",
        ):
            with self.subTest(step=step):
                self.assertIn(
                    f"- name: {step}" + chr(10) + "        if: steps.rights.outputs.hold == 'false'",
                    workflow,
                )
        self.assertIn("no provider retrieval", workflow)
        self.assertIn("python usd_impact_score_v2.py", workflow)
        self.assertIn(
            "if: steps.rights.outputs.hold == 'false' && always()", workflow
        )

    def test_health_checks_do_not_raise_false_freshness_incidents(self) -> None:
        weekly = self.read(".github/workflows/weekly-health.yml")
        self.assertIn("Record rights-review health hold", weekly)
        self.assertIn(
            "if: steps.rights.outputs.hold == 'false' && "
            "steps.health.outcome == 'failure'",
            weekly,
        )
        research = self.read(".github/workflows/score-research-evidence-health.yml")
        self.assertIn("Record rights-review evidence hold", research)
        self.assertIn(
            "if: steps.rights.outputs.hold == 'false' && always()",
            research,
        )
        self.assertIn(
            "if: steps.rights.outputs.hold == 'false' && "
            "steps.health.outcome == 'failure'",
            research,
        )


if __name__ == "__main__":
    unittest.main()
