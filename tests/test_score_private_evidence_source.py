from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "score_private_evidence_source.py"
PUBLIC_BUNDLE = REPO_ROOT / "public" / "data" / "score_repro_bundle_latest.json"

spec = importlib.util.spec_from_file_location("score_private_evidence_source", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class ScorePrivateEvidenceSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.public_bundle = json.loads(PUBLIC_BUNDLE.read_text(encoding="utf-8"))
        cls.week = cls.public_bundle["score_week"]

    def _stage_private(self, root: Path) -> Path:
        evidence = root / "private-score-evidence"
        latest = evidence / "latest" / "repro_bundle.json"
        archive = evidence / "archive" / self.week / "repro_bundle.json"
        latest.parent.mkdir(parents=True)
        archive.parent.mkdir(parents=True)
        shutil.copyfile(PUBLIC_BUNDLE, latest)
        shutil.copyfile(PUBLIC_BUNDLE, archive)
        return evidence

    def test_loads_byte_identical_private_strict_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = self._stage_private(root)
            loaded = module.load_private_strict_bundle(root, evidence, self.week)

            self.assertEqual(loaded.week, self.week)
            self.assertEqual(loaded.bundle["published"], self.public_bundle["published"])
            self.assertEqual(loaded.latest_path.read_bytes(), loaded.archive_path.read_bytes())
            self.assertEqual(len(loaded.sha256), 64)

    def test_extracts_exact_research_levels_without_recalculation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = self._stage_private(root)
            loaded = module.load_private_strict_bundle(root, evidence, self.week)
            drivers = tuple(self.public_bundle["components"])
            levels = module.extract_research_levels(loaded, drivers)

            self.assertEqual(set(levels), set(drivers))
            for driver in drivers:
                self.assertEqual(
                    levels[driver],
                    float(self.public_bundle["components"][driver]["weekly_level"]),
                )

    def test_rejects_public_evidence_root(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "must not be loaded from a public path"):
            module.load_private_strict_bundle(
                REPO_ROOT,
                REPO_ROOT / "public",
                self.week,
            )

    def test_rejects_latest_archive_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = self._stage_private(root)
            archive = evidence / "archive" / self.week / "repro_bundle.json"
            changed = json.loads(archive.read_text(encoding="utf-8"))
            changed["bundle_generated_at_utc"] = "2099-01-01T00:00:00+00:00"
            archive.write_text(json.dumps(changed), encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "latest/archive bundle hashes differ"):
                module.load_private_strict_bundle(root, evidence, self.week)

    def test_rejects_week_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = self._stage_private(root)
            with self.assertRaisesRegex(RuntimeError, "week differs from requested week"):
                module.load_private_strict_bundle(root, evidence, "2099-01-01")


if __name__ == "__main__":
    unittest.main()
