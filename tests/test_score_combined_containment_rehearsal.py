from __future__ import annotations

import unittest
from pathlib import Path

from scripts import rehearse_score_combined_containment as rehearsal

REPO_ROOT = Path(__file__).resolve().parents[1]


class ScoreCombinedContainmentRehearsalTests(unittest.TestCase):
    def test_combined_containment_is_hold_bound_and_no_write(self) -> None:
        report = rehearsal.rehearse(REPO_ROOT)

        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["review_only"])
        self.assertFalse(report["writes_performed"])
        self.assertFalse(report["provider_refetch_performed"])
        self.assertFalse(report["cloud_storage_action_performed"])
        self.assertFalse(report["production_workflow_changed"])

        self.assertEqual(report["publication_gate_state"], "hold")
        self.assertEqual(report["rights_surface_state"], "hold")
        self.assertFalse(report["production_change_authorized"])
        self.assertEqual(report["rights_surface_classes"], ["A", "B", "C", "D", "E", "F"])

        self.assertGreaterEqual(report["public_static_path_count"], 20)
        self.assertEqual(report["public_archive_pattern_count"], 1)
        self.assertGreater(report["public_safe_history_rows"], 600)

        for field in (
            "public_safe_score_sha256",
            "public_safe_point_in_time_sha256",
            "public_safe_robustness_sha256",
            "public_safe_vintage_sha256",
            "synthetic_private_latest_sha256",
        ):
            self.assertEqual(len(report[field]), 64)

        self.assertEqual(report["synthetic_private_archive_count"], 2)
        self.assertIsInstance(report["aggregate_score"], float)
        self.assertIsInstance(report["aggregate_regime"], str)
        self.assertTrue(report["aggregate_regime"])


if __name__ == "__main__":
    unittest.main()
