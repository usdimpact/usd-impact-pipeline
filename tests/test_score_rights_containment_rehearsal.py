from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "rehearse_score_rights_containment.py"

spec = importlib.util.spec_from_file_location("score_rights_rehearsal", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class ScoreRightsContainmentRehearsalTests(unittest.TestCase):
    def test_current_release_rehearses_without_writes_or_refetch(self) -> None:
        report = module.rehearse(REPO_ROOT)

        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["review_only"])
        self.assertFalse(report["writes_performed"])
        self.assertFalse(report["private_evidence_loaded_from_public_path"])
        self.assertFalse(report["provider_refetch_performed"])
        self.assertFalse(report["production_workflow_changed"])
        self.assertEqual(len(report["private_strict_bundle_sha256"]), 64)
        self.assertEqual(len(report["aggregate_history_sha256"]), 64)
        self.assertGreater(report["public_safe_history_rows"], 600)


if __name__ == "__main__":
    unittest.main()
