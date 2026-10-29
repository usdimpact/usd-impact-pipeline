"""Review-only regression guard against new unreviewed live Score fetch workflows.

No provider access and no repository writes. Intentionally scoped to direct Score
v2 entrypoints: subprocess indirection and external CI need separate audit.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
DIRECT_SCORE_CALL = re.compile(
    r"\bpython(?:3(?:\.\d+)?)?\s+usd_impact_score_v2\.py\b"
)
APPROVED_REVIEWED_CALLERS = {
    "repro-rehearsal.yml",
    "weekly.yml",
}


class LiveScoreWorkflowScopeTests(unittest.TestCase):
    @staticmethod
    def workflows_with_live_score_command() -> dict[str, str]:
        found: dict[str, str] = {}
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            if DIRECT_SCORE_CALL.search(text):
                found[path.name] = text
        return found

    def test_all_direct_live_score_workflows_have_been_explicitly_reviewed(self) -> None:
        found = self.workflows_with_live_score_command()
        self.assertEqual(
            set(found),
            APPROVED_REVIEWED_CALLERS,
            "A new or removed direct Score v2 live-fetch workflow needs a fresh "
            "rights and provenance review before changing this registry.",
        )

    def test_weekly_provider_fetch_is_downstream_of_fail_closed_hold(self) -> None:
        source = self.workflows_with_live_score_command()["weekly.yml"]
        self.assertLess(
            source.index("Evaluate Score publication rights gate"),
            source.index("Run score pipeline"),
        )
        self.assertIn(
            "needs.preflight.outputs.rights_hold != 'true' && "
            "needs.preflight.outputs.action == 'generate'",
            source,
        )
        self.assertIn(
            "python -m scripts.score_publication_rights_gate --github-output",
            source,
        )

    def test_nonpublishing_rehearsal_requires_hold_check_before_fetch(self) -> None:
        source = self.workflows_with_live_score_command()["repro-rehearsal.yml"]
        self.assertLess(
            source.index("Evaluate Score publication rights gate"),
            source.index("Rehearse full release bundle and archive path"),
        )
        self.assertIn(
            "python -m scripts.score_publication_rights_gate --github-output",
            source,
        )
        for step in (
            "Set up Python 3.11",
            "Install locked dependencies",
            "Verify machine-readable methodology contract",
            "Rehearse full release bundle and archive path",
        ):
            with self.subTest(step=step):
                self.assertIn(
                    f"- name: {step}\n        if: steps.rights.outputs.hold == 'false'",
                    source,
                )

    def test_no_live_refetch_cli_mode_is_embedded_in_workflows(self) -> None:
        # A separate manual executable/CLI audit is still required. These
        # markers catch accidental introduction into existing workflows only.
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertNotIn("--live-refetch", text)

    def test_github_artifacts_are_not_used_for_score_provider_level_snapshots(self) -> None:
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertNotRegex(
                    text,
                    r"(?i)actions/upload-artifact[^\n]*[\s\S]{0,350}"
                    r"score-v2-(?:weekly-levels|provider-evidence)\.(?:csv|json)",
                )


if __name__ == "__main__":
    unittest.main()
