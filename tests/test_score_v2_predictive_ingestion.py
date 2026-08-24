from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts import score_v2_predictive_ingestion as ingestion
from tests.predictive_test_support import REPO, copy_predictive_contract, write_bundle, write_score


class ScoreV2PredictiveIngestionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        copy_predictive_contract(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _ingest(self, week: str = "2026-08-28") -> dict:
        return ingestion.ingest(
            self.root,
            recorded_at=datetime.fromisoformat(f"{week}T23:00:00+00:00"),
            attestation_run_id="12345",
            attestation_url="https://github.com/usdimpact/usd-impact-pipeline/actions/runs/12345",
        )

    def test_pre_holdout_is_claim_safe_noop(self) -> None:
        write_score(self.root, "2026-08-21", 0.0)
        result = self._ingest("2026-08-21")
        self.assertEqual(result["status"], "pre_holdout_noop")
        self.assertIs(result["writes_performed"], False)
        self.assertFalse((self.root / "research/predictive").exists())

    def test_first_origin_freezes_predictions_before_next_outcome(self) -> None:
        write_score(self.root, "2026-08-28", 1.0)
        write_bundle(self.root, "2026-08-28", score=1.0, dxy_level=100.0)
        result = self._ingest()
        self.assertEqual(result["status"], "ingested")
        self.assertEqual(result["weekly_observations"], 1)
        self.assertEqual(result["resolved_predictions"], 0)
        record = json.loads(
            (self.root / "research/predictive" / result["weekly_record_file"]).read_text()
        )
        self.assertEqual(record["record_role"], "predictive_origin")
        self.assertEqual(record["frozen_predictions"]["model_direction"], "up")
        self.assertEqual(record["frozen_predictions"]["always_up_direction"], "up")
        self.assertEqual(
            record["frozen_predictions"]["momentum_prior_source"],
            "frozen_2026-08-21_initialization",
        )
        self.assertEqual(record["source_v2_bundle"]["attestation_run_id"], 12345)

    def test_same_week_is_idempotent_and_changed_bundle_fails(self) -> None:
        write_score(self.root, "2026-08-28", -1.0)
        write_bundle(self.root, "2026-08-28", score=-1.0, dxy_level=97.0)
        first = self._ingest()
        second = self._ingest()
        self.assertEqual(first["status"], "ingested")
        self.assertEqual(second["status"], "already_ingested_noop")
        write_bundle(self.root, "2026-08-28", score=-1.0, dxy_level=96.0)
        with self.assertRaisesRegex(RuntimeError, "source archive hash mismatch|different v2 bundle"):
            self._ingest()

    def test_gap_cannot_be_backfilled_after_outcome_is_visible(self) -> None:
        write_score(self.root, "2026-09-04", 1.0)
        write_bundle(self.root, "2026-09-04", score=1.0, dxy_level=101.0)
        with self.assertRaisesRegex(RuntimeError, "backfill is prohibited"):
            self._ingest("2026-09-04")
        manifest = json.loads((self.root / "research/score_v2_predictive_manifest.json").read_text())
        self.assertEqual(manifest["entries"], [])

    def test_latest_archive_hash_mismatch_fails_closed(self) -> None:
        write_score(self.root, "2026-08-28", 0.0)
        write_bundle(
            self.root,
            "2026-08-28",
            score=0.0,
            dxy_level=100.0,
            archive_same=False,
        )
        with self.assertRaisesRegex(RuntimeError, "hashes differ"):
            self._ingest()

    def test_source_and_workflow_have_no_provider_refetch_or_schedule(self) -> None:
        source = (REPO / "scripts/score_v2_predictive_ingestion.py").read_text(encoding="utf-8")
        for forbidden in ("fetch_all_inputs(", "yfinance", "fred.stlouisfed.org"):
            self.assertNotIn(forbidden, source)
        workflow = (REPO / ".github/workflows/score-v2-predictive.yml").read_text(encoding="utf-8")
        self.assertIn('workflows: ["Score v2 reproduction attestation"]', workflow)
        self.assertIn("github.event.workflow_run.event == 'push'", workflow)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", workflow)
        self.assertIn("gh pr create", workflow)
        self.assertNotIn("gh pr merge", workflow)
        self.assertNotIn("gh workflow run", workflow)
        self.assertNotIn("actions: write", workflow)
        self.assertNotIn("issues: write", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertNotIn("git add public/", workflow)


if __name__ == "__main__":
    unittest.main()
