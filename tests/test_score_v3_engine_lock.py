from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import verify_score_v3_engine_lock as engine_lock


REPO = Path(__file__).resolve().parents[1]


class ScoreV3EngineLockTests(unittest.TestCase):
    def test_repository_matches_pre_holdout_engine_commit(self) -> None:
        has_locked_history = subprocess.run(
            ["git", "cat-file", "-e", f"{engine_lock.IMPLEMENTATION_COMMIT_SHA}^{{commit}}"],
            cwd=REPO,
            check=False,
            capture_output=True,
        ).returncode == 0
        report = engine_lock.verify(REPO, filesystem_only=not has_locked_history)
        self.assertEqual(
            report["implementation_commit_sha"],
            "4f1a14bcf656197fbfcc904f3f013852cb68cc01",
        )
        self.assertEqual(report["immutable_files"], 15)
        self.assertIs(report["filesystem_only"], not has_locked_history)
        self.assertIs(report["research_only"], True)
        self.assertIs(report["production_change"], False)
        self.assertIs(report["predictive_claim"], False)

    def test_one_byte_engine_change_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lock = json.loads((REPO / engine_lock.LOCK_PATH).read_text(encoding="utf-8"))
            for relative in lock["immutable_files"]:
                source = REPO / relative
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            target_lock = root / engine_lock.LOCK_PATH
            target_lock.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / engine_lock.LOCK_PATH, target_lock)
            changed = root / "scripts/score_v3_candidates.py"
            changed.write_bytes(changed.read_bytes() + b" ")
            with self.assertRaisesRegex(RuntimeError, "engine file drifted"):
                engine_lock.verify(root, filesystem_only=True)

    def test_lock_file_change_fails_before_file_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / engine_lock.LOCK_PATH
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((REPO / engine_lock.LOCK_PATH).read_bytes() + b" ")
            with self.assertRaisesRegex(RuntimeError, "lock file differs"):
                engine_lock.verify(root, filesystem_only=True)

    def test_quality_and_read_only_health_verify_the_lock(self) -> None:
        quality = (REPO / ".github/workflows/quality.yml").read_text(encoding="utf-8")
        health = (REPO / "scripts/check_score_research_evidence_health.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("verify_score_v3_engine_lock --filesystem-only --json", quality)
        self.assertIn("engine_lock_v3.verify", health)


if __name__ == "__main__":
    unittest.main()
