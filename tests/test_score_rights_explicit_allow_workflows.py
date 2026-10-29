"""Explicit-allow, fail-closed contract for all active Score rights-gated workflows.

Offline-only file assertions. This test must never contact a market provider.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
MONITORED = (
    "weekly.yml",
    "weekly-recovery.yml",
    "weekly-health.yml",
    "research-validation.yml",
    "score-v3-shadow.yml",
    "score-v2-predictive.yml",
    "score-research-evidence-health.yml",
    "repro-rehearsal.yml",
)
LEGACY_NEGATIVE_CONDITIONS = (
    "steps.rights.outputs.hold != 'true'",
    "needs.preflight.outputs.rights_hold != 'true'",
    "needs.rights-gate.outputs.hold != 'true'",
)
EXPLICIT_ALLOW_CONDITIONS = {
    "weekly.yml": (
        "steps.rights.outputs.hold == 'false'",
        "needs.preflight.outputs.rights_hold == 'false'",
    ),
    "weekly-recovery.yml": ("steps.rights.outputs.hold == 'false'",),
    "weekly-health.yml": ("steps.rights.outputs.hold == 'false'",),
    "research-validation.yml": ("steps.rights.outputs.hold == 'false'",),
    "score-v3-shadow.yml": ("needs.rights-gate.outputs.hold == 'false'",),
    "score-v2-predictive.yml": ("needs.rights-gate.outputs.hold == 'false'",),
    "score-research-evidence-health.yml": (
        "steps.rights.outputs.hold == 'false'",
    ),
    "repro-rehearsal.yml": ("steps.rights.outputs.hold == 'false'",),
}


class ExplicitAllowScoreRightsGateTests(unittest.TestCase):
    def test_active_score_workflows_require_positive_allow_evidence(self) -> None:
        self.assertEqual(set(MONITORED), set(EXPLICIT_ALLOW_CONDITIONS))
        for name in MONITORED:
            with self.subTest(workflow=name):
                source = (WORKFLOWS / name).read_text(encoding="utf-8")
                self.assertIn("Evaluate Score publication rights gate", source)
                for old_condition in LEGACY_NEGATIVE_CONDITIONS:
                    self.assertNotIn(old_condition, source)
                for condition in EXPLICIT_ALLOW_CONDITIONS[name]:
                    self.assertIn(condition, source)

    def test_reproduction_rehearsal_never_fetches_under_missing_allow(self) -> None:
        source = (WORKFLOWS / "repro-rehearsal.yml").read_text(encoding="utf-8")
        self.assertLess(
            source.index("Evaluate Score publication rights gate"),
            source.index("Rehearse full release bundle and archive path"),
        )
        self.assertIn(
            "if: steps.rights.outputs.hold == 'false'",
            source,
        )

    def test_policy_remains_hold_without_approval_receipt(self) -> None:
        raw = json.loads(
            (ROOT / "governance/score-publication-rights-gate.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(raw["state"], "hold")
        self.assertIsNone(raw["decision_receipt"])
        self.assertIsNone(raw["approved_by"])

    def test_gate_logic_missing_invalid_policy_is_hold(self) -> None:
        from scripts.score_publication_rights_gate import evaluate_policy

        for raw in (None, {}, {"state": "allow"}, {"state": "unknown"}):
            with self.subTest(raw=raw):
                self.assertIs(evaluate_policy(raw)["hold"], True)


if __name__ == "__main__":
    unittest.main()
