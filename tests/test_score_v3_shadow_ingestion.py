from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts import score_v3_shadow_ingestion as shadow


REPO = Path(__file__).resolve().parents[1]


class ScoreV3ShadowIngestionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for relative in (
            "research/score_v3_initialization_2026-08-21.csv",
            "research/score_v3_initialization_2026-08-21.manifest.json",
            "research/score_v3_prospective_manifest.json",
            "research/score_v3_preregistration.json",
        ):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / relative, target)

        manifest_path = self.root / "research/score_v3_prospective_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["entries"] = []
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_score(self, week: str) -> None:
        path = self.root / "public/data/usd_impact_score_v2.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "metadata": {
                        "latest_date": week,
                        "latest_score": 0.0,
                        "latest_regime": "Neutral / transitional",
                    },
                    "weeks": [],
                }
            ),
            encoding="utf-8",
        )

    def _write_bundle(self, week: str, *, archive_same: bool = True) -> None:
        init = json.loads(
            (self.root / "research/score_v3_initialization_2026-08-21.manifest.json").read_text()
        )
        # Use positive finite levels; candidate calculations depend on levels,
        # while the v2 reproduction check below intentionally uses zero z-score
        # contributions for a simple neutral published fixture.
        components = {}
        for i, driver in enumerate(init["driver_order"], start=1):
            weight = {
                "DXY": 0.125,
                "WTI": -0.125,
                "SPX": -0.125,
                "VIX": 0.125,
                "BTC": -0.125,
                "GOLD": -0.125,
                "UST_2Y": 0.125,
                "UST_10Y": 0.125,
            }[driver]
            components[driver] = {
                "weekly_level": float(100 * i + 7.5),
                "z_clipped": 0.0,
                "weight": weight,
            }
        bands = [
            {"low": 1.0, "high": None, "label": "Strong dollar regime"},
            {"low": 0.3, "high": 1.0, "label": "Firm dollar regime"},
            {"low": -0.3, "high": 0.3, "label": "Neutral / transitional"},
            {"low": -1.0, "high": -0.3, "label": "Soft dollar regime"},
            {"low": None, "high": -1.0, "label": "Weak dollar regime"},
        ]
        bundle = {
            "score_week": week,
            "pipeline_git_sha": "1" * 40,
            "requirements_lock_sha256": "2" * 64,
            "components": components,
            "calculation": {"regime_bands": bands},
            "published": {"score": 0.0, "regime": "Neutral / transitional"},
        }
        latest = self.root / "public/data/score_repro_bundle_latest.json"
        latest.parent.mkdir(parents=True, exist_ok=True)
        latest.write_text(json.dumps(bundle, sort_keys=True), encoding="utf-8")
        archive = self.root / f"public/archive/{week}/repro_bundle.json"
        archive.parent.mkdir(parents=True, exist_ok=True)
        if archive_same:
            shutil.copy2(latest, archive)
        else:
            altered = dict(bundle)
            altered["pipeline_git_sha"] = "3" * 40
            archive.write_text(json.dumps(altered, sort_keys=True), encoding="utf-8")

    def test_pre_holdout_is_clean_noop_without_reproduction_bundle(self) -> None:
        self._write_score("2026-08-21")
        report = shadow.ingest(
            self.root,
            ingested_at=datetime(2026, 8, 24, tzinfo=timezone.utc),
            attestation_run_id=None,
            attestation_url=None,
        )
        self.assertEqual(report["status"], "pre_holdout_noop")
        self.assertIs(report["writes_performed"], False)
        self.assertFalse((self.root / "research/prospective").exists())

    def test_first_holdout_week_uses_bundle_and_writes_one_atomic_record(self) -> None:
        self._write_score("2026-08-28")
        self._write_bundle("2026-08-28")
        report = shadow.ingest(
            self.root,
            ingested_at=datetime(2026, 8, 28, 23, 0, tzinfo=timezone.utc),
            attestation_run_id="12345",
            attestation_url="https://github.com/usdimpact/usd-impact-pipeline/actions/runs/12345",
        )
        self.assertEqual(report["status"], "ingested")
        result_path = self.root / "research/prospective" / report["candidate_result_file"]
        self.assertTrue(result_path.exists())
        result = json.loads(result_path.read_text())
        self.assertEqual(result["week"], "2026-08-28")
        self.assertIs(result["research_only"], True)
        self.assertIs(result["candidate_selection_performed"], False)
        self.assertEqual(set(result["candidates"]), {"V3_E52", "V3_R260", "V3_MAD260", "V3_GRP_MAD260"})
        self.assertEqual(result["source_v2_attestation"]["workflow_run_id"], 12345)
        manifest = json.loads((self.root / "research/score_v3_prospective_manifest.json").read_text())
        self.assertEqual(len(manifest["entries"]), 1)
        self.assertEqual(manifest["entries"][0]["candidate_result_sha256"], report["candidate_result_sha256"])

    def test_rerunning_same_attested_week_is_idempotent(self) -> None:
        self._write_score("2026-08-28")
        self._write_bundle("2026-08-28")
        kwargs = dict(
            ingested_at=datetime(2026, 8, 28, 23, 0, tzinfo=timezone.utc),
            attestation_run_id="12345",
            attestation_url="https://github.com/usdimpact/usd-impact-pipeline/actions/runs/12345",
        )
        first = shadow.ingest(self.root, **kwargs)
        second = shadow.ingest(self.root, **kwargs)
        self.assertEqual(first["status"], "ingested")
        self.assertEqual(second["status"], "already_ingested_noop")
        self.assertIs(second["writes_performed"], False)

    def test_bundle_archive_hash_mismatch_fails_closed(self) -> None:
        self._write_score("2026-08-28")
        self._write_bundle("2026-08-28", archive_same=False)
        with self.assertRaisesRegex(RuntimeError, "hashes differ"):
            shadow.ingest(
                self.root,
                ingested_at=datetime(2026, 8, 28, 23, 0, tzinfo=timezone.utc),
                attestation_run_id="12345",
                attestation_url="https://github.com/usdimpact/usd-impact-pipeline/actions/runs/12345",
            )
        self.assertFalse((self.root / "research/prospective").exists())

    def test_missing_prior_prospective_week_cannot_be_skipped(self) -> None:
        self._write_score("2026-09-11")
        self._write_bundle("2026-09-11")
        with self.assertRaisesRegex(RuntimeError, "Prospective ledger gap"):
            shadow.ingest(
                self.root,
                ingested_at=datetime(2026, 9, 11, 23, 0, tzinfo=timezone.utc),
                attestation_run_id="12346",
                attestation_url="https://github.com/usdimpact/usd-impact-pipeline/actions/runs/12346",
            )

    def test_ingestion_source_contains_no_live_provider_fetch_path(self) -> None:
        source = (REPO / "scripts/score_v3_shadow_ingestion.py").read_text(encoding="utf-8")
        self.assertNotIn("fetch_all_inputs(", source)
        self.assertNotIn("yfinance", source)
        self.assertNotIn("fred.stlouisfed.org", source)

    def test_workflow_is_downstream_and_research_only(self) -> None:
        workflow = (REPO / ".github/workflows/score-v3-shadow.yml").read_text(encoding="utf-8")
        self.assertIn('workflows: ["Score v2 reproduction attestation"]', workflow)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", workflow)
        self.assertIn("github.event.workflow_run.event == 'push'", workflow)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", workflow)
        self.assertIn('--repo "$GITHUB_REPOSITORY"', workflow)
        self.assertIn("python scripts/validate_weekly_release.py", workflow)
        self.assertIn("gh pr create", workflow)
        self.assertNotIn("gh pr merge", workflow)
        self.assertNotIn("gh workflow run", workflow)
        self.assertNotIn("actions: write", workflow)
        self.assertNotIn("issues: write", workflow)
        self.assertIn("git add research/score_v3_prospective_manifest.json research/prospective/", workflow)
        self.assertNotIn("git add public/", workflow)
        self.assertNotIn("schedule:", workflow)


if __name__ == "__main__":
    unittest.main()
