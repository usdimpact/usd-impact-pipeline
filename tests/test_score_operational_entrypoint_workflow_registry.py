"""Review-only guard for supported Score workflow/provider execution entrypoints.

All checks read current local YAML text or invented command examples. No
network requests, provider data, GitHub Actions dispatches, writes, or live
Score calls. This is not an access control for arbitrary external Python.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

# The only operational workflows permitted to invoke the immutable original
# Score engine directly are already independently gated by the v1 rights HOLD.
REVIEWED_DIRECT_SCORE_WORKFLOWS = frozenset({
    "weekly.yml",
    "repro-rehearsal.yml",
})
RIGHTS_GATED_SCORE_WORKFLOWS = frozenset({
    "weekly.yml",
    "repro-rehearsal.yml",
    "research-validation.yml",
    "score-v2-predictive.yml",
    "score-v3-shadow.yml",
    "score-research-evidence-health.yml",
    "weekly-health.yml",
    "weekly-recovery.yml",
})

# Detect direct CLI calls plus the previously unregistered -m/module, Python3,
# and shell wrapper variations; do not treat runtime reproduction builder or
# pre-existing metadata-only scripts as the original live-refetch path.
_PYTHON = r"\bpython(?:3(?:\.\d+)?)?\s+(?:(?:-B|-I|-u)\s+)*"
_DIRECT_SCORE = re.compile(
    _PYTHON + r"(?:"
    r"usd_impact_score_v2\.py\b"
    r"|(?:-m\s+usd_impact_score_v2\b)"
    r"|scripts[/\\]build_score_repro_bundle\.py\b"
    r"|(?:-m\s+scripts\.build_score_repro_bundle\b)"
    r")"
)
_SOURCE_HELPER = re.compile(
    r"\b(?:fetch_all_inputs|fetch_fred|fetch_yahoo)\s*\("
)
_DIRECT_FEED = re.compile(
    r"(?i)\b(?:curl|wget)\b[^\n]*(?:fredgraph\.csv|"
    r"fred\.stlouisfed\.org|query1\.finance\.yahoo\.com)"
)
# Any direct --live-refetch outside the frozen/offline rehearsal contract
# requires new source-rights and procedural review, even in a gated workflow.
_LIVE_REFETCH = re.compile(r"(?<![\w-])--live-refetch\b")


def risky_commands(source: str) -> tuple[str, ...]:
    """Return deterministic evidence categories, never fetched observations."""
    found: list[str] = []
    for label, pattern in (
        ("direct_score_or_repro_cli", _DIRECT_SCORE),
        ("direct_provider_function", _SOURCE_HELPER),
        ("direct_source_url", _DIRECT_FEED),
        ("live_refetch_flag", _LIVE_REFETCH),
    ):
        if pattern.search(source):
            found.append(label)
    return tuple(found)


def workflow_inventory() -> dict[str, tuple[str, ...]]:
    return {
        file.name: risky_commands(file.read_text(encoding="utf-8"))
        for file in sorted(WORKFLOWS.glob("*.yml"))
    }


class ScoreOperationalEntrypointRegistryTests(unittest.TestCase):
    def test_all_workflow_files_are_in_inventory_without_live_data(self) -> None:
        files = sorted(WORKFLOWS.glob("*.yml"))
        self.assertGreaterEqual(len(files), 27)
        inventory = workflow_inventory()
        self.assertEqual(set(inventory), {file.name for file in files})
        self.assertEqual(set(REVIEWED_DIRECT_SCORE_WORKFLOWS) - set(inventory), set())
        self.assertEqual(set(RIGHTS_GATED_SCORE_WORKFLOWS) - set(inventory), set())

    def test_unreviewed_workflows_cannot_add_provider_execution(self) -> None:
        inventory = workflow_inventory()
        directly_invoking = {
            path for path, evidence in inventory.items() if evidence
        }
        self.assertEqual(
            directly_invoking,
            REVIEWED_DIRECT_SCORE_WORKFLOWS,
            "Unreviewed operational command detected. Do not grant provider "
            "access or silently add an allowlist entry. Review the exact new "
            "workflow and source-rights/retention state first.",
        )
        for path in directly_invoking:
            self.assertEqual(
                inventory[path], ("direct_score_or_repro_cli",),
                f"Unexpected provider helper, feed, or live-refetch in {path}",
            )

    def test_all_eight_known_score_workflows_still_require_rights_gate(self) -> None:
        for path in sorted(RIGHTS_GATED_SCORE_WORKFLOWS):
            with self.subTest(workflow=path):
                source = (WORKFLOWS / path).read_text(encoding="utf-8")
                self.assertIn("Evaluate Score publication rights gate", source)
                self.assertIn(
                    "python -m scripts.score_publication_rights_gate --github-output",
                    source,
                )
                self.assertNotIn("hold != 'true'", source)
                self.assertNotIn("USD_IMPACT_SCORE_ALLOW", source)

    def test_live_score_entrypoints_remain_downstream_of_explicit_hold(self) -> None:
        weekly = (WORKFLOWS / "weekly.yml").read_text(encoding="utf-8")
        rehearsal = (WORKFLOWS / "repro-rehearsal.yml").read_text(encoding="utf-8")
        self.assertLess(
            weekly.index("Evaluate Score publication rights gate"),
            weekly.index("python usd_impact_score_v2.py"),
        )
        self.assertIn(
            "needs.preflight.outputs.rights_hold == 'false' && "
            "needs.preflight.outputs.action == 'generate'",
            weekly,
        )
        self.assertLess(
            rehearsal.index("Evaluate Score publication rights gate"),
            rehearsal.index("python usd_impact_score_v2.py"),
        )
        self.assertIn(
            "- name: Rehearse full release bundle and archive path\n"
            "        if: steps.rights.outputs.hold == 'false'",
            rehearsal,
        )

    def test_synthetic_bypass_variants_are_detected_before_future_pr_merge(self) -> None:
        commands = (
            "python3 usd_impact_score_v2.py --web",
            "python -m usd_impact_score_v2 --web",
            "python -u -m usd_impact_score_v2 --test",
            "python scripts/build_score_repro_bundle.py --live-refetch",
            "python -m scripts.build_score_repro_bundle --live-refetch",
            'python -c "fetch_all_inputs(\"2099-01-01\", None)"',
            "curl https://fred.stlouisfed.org/graph/fredgraph.csv",
            "wget https://query1.finance.yahoo.com/v8/finance/chart/",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertNotEqual(risky_commands(command), ())

    def test_normal_nonprovider_ci_commands_do_not_false_flag(self) -> None:
        benign = (
            "python -m scripts.score_provider_guarded_cli score --web",
            "python -m scripts.build_runtime_score_repro_bundle --score-json invented.json",
            "python -m scripts.verify_score_v3_engine_lock --filesystem-only",
            "python -m scripts.score_publication_rights_gate --github-output output",
            "python -m unittest discover -s tests -v",
        )
        for command in benign:
            with self.subTest(command=command):
                self.assertEqual(risky_commands(command), ())

    def test_reviewed_manual_launcher_always_checks_before_subprocess(self) -> None:
        source = (ROOT / "scripts/score_provider_guarded_cli.py").read_text(
            encoding="utf-8"
        )
        self.assertLess(
            source.index("require_score_provider_rights()"),
            source.index("subprocess.run(command,"),
        )
        self.assertIn("return 3", source)
        self.assertNotIn("shell=True", source)

    def test_only_v1_gate_may_be_referenced_for_existing_operational_allow(self) -> None:
        # This test is an intentional HOLD on introducing a new release/rights
        # bypass in operational workflow YAML. A future v2 gate requires an
        # independent owner/legal decision and change to these tests.
        for file in sorted(WORKFLOWS.glob("*.yml")):
            source = file.read_text(encoding="utf-8")
            with self.subTest(workflow=file.name):
                self.assertNotIn("USD_IMPACT_SCORE_ALLOW", source)
                self.assertNotIn("--live-refetch", source)


if __name__ == "__main__":
    unittest.main()
