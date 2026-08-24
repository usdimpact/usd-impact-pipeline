from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import verify_score_v2_predictive_engine_lock as engine_lock


REPO = Path(__file__).resolve().parents[1]


class ScoreV2PredictiveEngineLockTests(unittest.TestCase):
    def test_repository_matches_pre_holdout_engine_commit(self) -> None:
        has_locked_history = subprocess.run(
            ["git", "cat-file", "-e", f"{engine_lock.IMPLEMENTATION_COMMIT_SHA}^{{commit}}"],
            cwd=REPO,
            check=False,
            capture_output=True,
        ).returncode == 0
        report = engine_lock.verify(REPO, filesystem_only=not has_locked_history)
        self.assertEqual(report["implementation_commit_sha"], "b08a057dc4372d0ab48a25d9fab0950dd0b3c11e")
        self.assertEqual(report["immutable_files"], 9)
        self.assertIs(report["filesystem_only"], not has_locked_history)

    def test_one_byte_engine_change_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lock_path = root / engine_lock.LOCK_PATH
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / engine_lock.LOCK_PATH, lock_path)
            lock = json.loads(lock_path.read_text())
            for relative in lock["immutable_files"]:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO / relative, target)
            changed = root / "scripts/score_v2_predictive_metrics.py"
            changed.write_text(changed.read_text() + "\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "drifted from its pre-holdout lock"):
                engine_lock.verify(root, filesystem_only=True)

    def test_quality_and_weekly_workflows_enforce_lock(self) -> None:
        quality = (REPO / ".github/workflows/quality.yml").read_text(encoding="utf-8")
        weekly = (REPO / ".github/workflows/score-v2-predictive.yml").read_text(encoding="utf-8")
        self.assertIn("verify_score_v2_predictive_engine_lock --filesystem-only", quality)
        self.assertIn("verify_score_v2_predictive_engine_lock --json", weekly)
        self.assertIn("research/score_v2_predictive_engine_lock.json", weekly)


if __name__ == "__main__":
    unittest.main()
