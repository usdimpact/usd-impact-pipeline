from __future__ import annotations

import unittest
from pathlib import Path

from scripts import rehearse_score_full_containment as rehearsal

REPO_ROOT = Path(__file__).resolve().parents[1]


class ScoreFullContainmentRehearsalTests(unittest.TestCase):
    def test_full_containment_rehearses_without_network_or_writes(self) -> None:
        report = rehearsal.rehearse(REPO_ROOT)

        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["review_only"])
        self.assertFalse(report["writes_performed"])
        self.assertFalse(report["provider_refetch_performed"])
        self.assertFalse(report["cloud_storage_action_performed"])
        self.assertFalse(report["production_workflow_changed"])
        self.assertEqual(report["rights_gate_state"], "hold")

        self.assertGreater(report["public_safe_history_rows"], 600)
        self.assertEqual(len(report["public_safe_score_sha256"]), 64)
        self.assertEqual(len(report["public_safe_point_in_time_sha256"]), 64)
        self.assertEqual(len(report["public_safe_robustness_sha256"]), 64)
        self.assertEqual(len(report["public_safe_vintage_sha256"]), 64)
        self.assertEqual(len(report["private_strict_bundle_sha256"]), 64)
        self.assertEqual(len(report["synthetic_private_latest_sha256"]), 64)
        self.assertEqual(report["synthetic_private_archive_count"], 2)

        self.assertEqual(report["score_week"], "2026-10-23")
        self.assertIsInstance(report["aggregate_score"], float)
        self.assertIsInstance(report["aggregate_regime"], str)
        self.assertTrue(report["aggregate_regime"])


if __name__ == "__main__":
    unittest.main()
