from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts import score_v2_predictive_ingestion as ingestion
from scripts import score_v2_predictive_manifest as manifest
from scripts import score_v2_predictive_metrics as metrics
from scripts import score_v2_predictive_reporting as reporting
from tests.predictive_test_support import copy_predictive_contract, write_bundle, write_score


class ScoreV2PredictiveReportingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        copy_predictive_contract(self.root)
        digest = hashlib.sha512(b"usd-impact-locked-predictive-test-sequence").digest()
        bits = [(byte >> bit) & 1 for byte in digest for bit in range(8)]
        self.directions = ["up" if bit else "down" for bit in bits[:52]]
        self.levels = [100.0]
        for direction in self.directions:
            multiplier = 1.01 if direction == "up" else 0.99
            self.levels.append(self.levels[-1] * multiplier)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _build_observations(self, count: int, *, write_due_checkpoints: bool) -> None:
        for index in range(count):
            week = manifest.FIRST_ORIGIN + timedelta(days=7 * index)
            score = 0.0 if index == 52 else (1.0 if self.directions[index] == "up" else -1.0)
            write_score(self.root, week.isoformat(), score)
            write_bundle(
                self.root,
                week.isoformat(),
                score=score,
                dxy_level=self.levels[index],
            )
            result = ingestion.ingest(
                self.root,
                recorded_at=datetime.combine(week, datetime.min.time(), timezone.utc).replace(hour=23),
                attestation_run_id=str(1000 + index),
                attestation_url=f"https://github.com/usdimpact/usd-impact-pipeline/actions/runs/{1000 + index}",
            )
            self.assertEqual(result["status"], "ingested")
            resolved = int(result["resolved_predictions"])
            if write_due_checkpoints and resolved in (13, 26, 39):
                checkpoint = reporting.checkpoint_if_due(self.root)
                self.assertTrue(checkpoint["checkpoint_written"])

    def test_interim_checkpoint_contains_integrity_only(self) -> None:
        self._build_observations(14, write_due_checkpoints=False)
        result = reporting.checkpoint_if_due(self.root)
        self.assertEqual(result["resolved_predictions"], 13)
        path = self.root / result["checkpoint_file"]
        payload = json.loads(path.read_text())
        self.assertEqual(payload["report_type"], "predictive_integrity_checkpoint")
        self.assertIs(payload["endpoint_values_emitted"], False)
        self.assertIs(payload["performance_calculated"], False)
        for forbidden in (
            "primary_endpoint",
            "comparators",
            "secondary_endpoints",
            "meaningful_predictive_evidence_gate",
        ):
            self.assertNotIn(forbidden, payload)

    def test_missed_interim_checkpoint_cannot_be_reconstructed_later(self) -> None:
        self._build_observations(15, write_due_checkpoints=False)
        with self.assertRaisesRegex(RuntimeError, "do not reconstruct"):
            reporting.validate_weekly(self.root)

    def test_formal_report_uses_locked_math_only_after_52_outcomes(self) -> None:
        self._build_observations(53, write_due_checkpoints=True)
        manifest_payload = json.loads((self.root / manifest.MANIFEST_PATH).read_text())
        self.assertEqual(manifest_payload["entries"][-1]["record_role"], "terminal_outcome")
        terminal = json.loads(
            (
                self.root
                / "research/predictive"
                / manifest_payload["entries"][-1]["weekly_record_file"]
            ).read_text()
        )
        self.assertIsNone(terminal["frozen_predictions"])

        formal = metrics.build_formal_report(self.root)
        self.assertEqual(formal["resolved_predictions"], 52)
        self.assertEqual(formal["primary_endpoint"]["directional_accuracy"], 1.0)
        self.assertEqual(formal["primary_endpoint"]["correct_predictions"], 52)
        self.assertEqual(formal["primary_endpoint"]["circular_shift"]["p_value"], 1 / 52)
        self.assertTrue(formal["meaningful_predictive_evidence_gate"]["passed"])
        self.assertIs(formal["automatic_site_claim_performed"], False)
        self.assertIs(formal["production_promotion_performed"], False)

        result = reporting.checkpoint_if_due(self.root)
        self.assertTrue(result["checkpoint_written"])
        self.assertTrue(result["formal_performance_report"])

    def test_formal_calculation_is_rejected_before_full_sample(self) -> None:
        self._build_observations(2, write_due_checkpoints=False)
        with self.assertRaisesRegex(RuntimeError, "before 52 resolved"):
            metrics.build_formal_report(self.root)


if __name__ == "__main__":
    unittest.main()
