from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_synthetic_private_score_evidence as synthetic
from scripts import rehearse_score_private_research_migration as rehearsal
from scripts import score_private_evidence_research_adapter as adapter
from scripts import rehearse_score_private_reader_compatibility as reader_compat
from usd_impact_score_v2 import WEIGHTS

REPO_ROOT = Path(__file__).resolve().parents[1]


class ScorePrivateResearchMigrationTests(unittest.TestCase):
    def test_rehearsal_is_review_only_and_no_write(self) -> None:
        report = rehearsal.rehearse(REPO_ROOT)

        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["review_only"])
        self.assertFalse(report["writes_performed"])
        self.assertFalse(report["network_access_performed"])
        self.assertFalse(report["cloud_storage_action_performed"])
        self.assertFalse(report["provider_refetch_performed"])
        self.assertFalse(report["production_change_authorized"])
        self.assertFalse(report["real_provider_evidence_authorized"])
        self.assertFalse(report["public_replacement_authorized"])
        self.assertFalse(report["private_component_values_exposed_publicly"])

        self.assertEqual(report["synthetic_week"], "2099-01-09")
        self.assertEqual(len(report["private_bundle_sha256"]), 64)
        self.assertEqual(report["private_v3_driver_count"], len(WEIGHTS))
        self.assertTrue(report["public_private_score_equal"])
        self.assertEqual(report["public_safe_schema_version"], "score-public-v2-safe-1")
        self.assertEqual(report["public_safe_history_rows"], 2)

    def test_adapter_exposes_only_required_research_inputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="score-private-adapter-test-") as tmp:
            root = Path(tmp) / "private"
            report = synthetic.build(root)
            bundle, sha = adapter.load_private_bundle(
                root / "score_repro_bundle_latest.json",
                expected_week=report["latest_week"],
                require_synthetic=True,
            )

            predictive = adapter.predictive_observation(bundle)
            levels = adapter.v3_source_levels(bundle)

            self.assertEqual(set(predictive), {"score", "dxy_weekly_level"})
            self.assertEqual(set(levels), set(WEIGHTS))
            self.assertEqual(len(sha), 64)
            self.assertGreater(predictive["dxy_weekly_level"], 0)
            self.assertTrue(all(value > 0 for value in levels.values()))

    def test_contract_keeps_all_release_boundaries_closed(self) -> None:
        contract = json.loads(
            (REPO_ROOT / "governance" / "score-private-research-migration-contract.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(contract["state"], "review_only")
        self.assertFalse(contract["production_change_authorized"])
        self.assertFalse(contract["real_provider_evidence_authorized"])
        self.assertFalse(contract["public_replacement_authorized"])
        self.assertTrue(contract["development_synthetic_rehearsal_authorized"])
        self.assertIn(
            "separate_production_authorization",
            contract["required_gates_before_public_replacement"],
        )

    def test_locked_readers_accept_temp_materialized_private_bundle(self) -> None:
        report = reader_compat.rehearse()
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["review_only"])
        self.assertFalse(report["writes_performed"])
        self.assertFalse(report["network_access_performed"])
        self.assertFalse(report["repository_public_paths_modified"])
        self.assertFalse(report["locked_readers_modified"])
        self.assertTrue(report["predictive_score_equal"])
        self.assertTrue(report["predictive_dxy_equal"])
        self.assertTrue(report["v3_source_levels_equal"])
        self.assertEqual(report["v3_driver_count"], len(WEIGHTS))
        self.assertFalse(report["production_change_authorized"])
        self.assertFalse(report["real_provider_evidence_authorized"])
        self.assertFalse(report["public_replacement_authorized"])


    def test_manual_read_workflow_is_read_only_and_hold_bound(self) -> None:
        workflow_dir = REPO_ROOT / ".github" / "workflows"
        source = (workflow_dir / "score-private-evidence-read-rehearsal.yml").read_text(
            encoding="utf-8"
        )
        self.assertFalse(
            (workflow_dir / "score-private-research-read-rehearsal.yml").exists()
        )

        self.assertIn("workflow_dispatch:", source)
        self.assertNotIn("schedule:", source)
        self.assertNotIn("push:", source)
        self.assertNotIn("pull_request:", source)
        self.assertIn("id-token: write", source)
        self.assertIn("contents: read", source)
        self.assertIn("github.ref == 'refs/heads/main'", source)
        self.assertIn("SYNTHETIC_WEEK: '2099-01-02'", source)
        self.assertIn("x-score-operation: read", source)
        self.assertNotIn("x-score-operation: write", source)
        self.assertIn(
            "https://xakayexlzyrazuunqlxe.supabase.co/functions/v1/score-private-evidence-broker",
            source,
        )
        self.assertIn("score-private-research-migration-contract.json", source)
        self.assertIn("validate_score_private_research_migration_bundle", source)
        self.assertIn("private-research-migration-report.json", source)
        self.assertIn("actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1", source)
        self.assertIn("runtime/requirements-2026-10-05.lock", source)
        self.assertIn("real_provider_evidence_authorized", source)
        self.assertIn("public_replacement_authorized", source)
        self.assertIn("production_change_authorized", source)
        self.assertNotIn("storage/v1/object", source)
        self.assertNotIn("signedUrl", source)
        self.assertNotIn("signed-url", source)


if __name__ == "__main__":
    unittest.main()
