from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import materialize_private_score_evidence as private
from usd_impact_score_v2 import WEIGHTS


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "score_private_evidence_receipt.schema.json"

BANDS = [
    {"low": 1.0, "high": None, "label": "Strong dollar regime"},
    {"low": 0.3, "high": 1.0, "label": "Firm dollar regime"},
    {"low": -0.3, "high": 0.3, "label": "Neutral / transitional"},
    {"low": -1.0, "high": -0.3, "label": "Soft dollar regime"},
    {"low": None, "high": -1.0, "label": "Weak dollar regime"},
]


def bundle(week: str, *, marker: float = 0.0) -> dict:
    components = {}
    for driver, weight in WEIGHTS.items():
        components[driver] = {
            "weekly_level": 100.0 + marker,
            "z_clipped": 0.0,
            "weight": float(weight),
        }
    return {
        "score_week": week,
        "pipeline_git_sha": "1" * 40,
        "requirements_lock_sha256": "2" * 64,
        "components": components,
        "calculation": {"regime_bands": BANDS},
        "published": {"score": 0.0, "regime": "Neutral / transitional"},
    }


class PrivateScoreEvidenceHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.evidence = self.root / "evidence"
        self.worktree = self.root / "worktree"
        self.receipt = self.root / "receipt.json"
        self.evidence.mkdir()
        self.worktree.mkdir()
        (self.worktree / ".git").write_text("gitdir: /tmp/fake\n", encoding="utf-8")
        (self.worktree / private.MARKER_NAME).write_text(
            private.MARKER_VALUE, encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_evidence(self, latest_week: str = "2026-10-23") -> bytes:
        current = json.dumps(
            bundle(latest_week), indent=2, sort_keys=True
        ).encode("utf-8")
        (self.evidence / "score_repro_bundle_latest.json").write_bytes(current)
        for week in ("2026-10-16", latest_week):
            path = self.evidence / "archive" / week / "repro_bundle.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            raw = current if week == latest_week else json.dumps(
                bundle(week, marker=-1.0), indent=2, sort_keys=True
            ).encode("utf-8")
            path.write_bytes(raw)
        return current

    def test_stage_preserves_exact_bytes_and_hash_only_receipt(self) -> None:
        latest_raw = self._write_evidence()
        report = private.stage(self.evidence, self.worktree, self.receipt)

        latest = self.worktree / "public/data/score_repro_bundle_latest.json"
        archive = self.worktree / "public/archive/2026-10-23/repro_bundle.json"
        self.assertEqual(latest.read_bytes(), latest_raw)
        self.assertEqual(archive.read_bytes(), latest_raw)
        self.assertEqual(report["latest_week"], "2026-10-23")
        self.assertEqual(report["archive_count"], 2)
        self.assertIs(report["provider_derived_values_in_receipt"], False)

        receipt_raw = self.receipt.read_text(encoding="utf-8")
        self.assertNotIn("weekly_level", receipt_raw)
        self.assertNotIn("components", receipt_raw)
        self.assertNotIn("DX-Y.NYB", receipt_raw)

    def test_stage_refuses_to_overwrite_existing_evidence(self) -> None:
        self._write_evidence()
        target = self.worktree / "public/data/score_repro_bundle_latest.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("do not overwrite", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "refusing to overwrite"):
            private.stage(self.evidence, self.worktree, self.receipt)
        self.assertEqual(target.read_text(encoding="utf-8"), "do not overwrite")

    def test_stage_requires_byte_identical_latest_archive(self) -> None:
        self._write_evidence()
        archive = self.evidence / "archive/2026-10-23/repro_bundle.json"
        archive.write_text(
            json.dumps(bundle("2026-10-23", marker=9.0), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(RuntimeError, "latest/archive bundle bytes differ"):
            private.stage(self.evidence, self.worktree, self.receipt)

    def test_stage_requires_explicit_ephemeral_marker(self) -> None:
        self._write_evidence()
        (self.worktree / private.MARKER_NAME).unlink()
        with self.assertRaisesRegex(RuntimeError, "reviewed marker"):
            private.stage(self.evidence, self.worktree, self.receipt)

    def test_cleanup_is_hash_guarded(self) -> None:
        self._write_evidence()
        private.stage(self.evidence, self.worktree, self.receipt)
        latest = self.worktree / "public/data/score_repro_bundle_latest.json"
        latest.write_text("mutated", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "changed after materialization"):
            private.cleanup(self.worktree, self.receipt)
        self.assertTrue(latest.exists())

    def test_cleanup_removes_only_receipted_evidence(self) -> None:
        self._write_evidence()
        private.stage(self.evidence, self.worktree, self.receipt)
        unrelated = self.worktree / "research/keep.txt"
        unrelated.parent.mkdir(parents=True, exist_ok=True)
        unrelated.write_text("keep", encoding="utf-8")

        report = private.cleanup(self.worktree, self.receipt)
        self.assertEqual(report["removed_files"], 3)
        self.assertTrue(unrelated.exists())
        self.assertFalse(
            (self.worktree / "public/data/score_repro_bundle_latest.json").exists()
        )
        self.assertFalse(
            (self.worktree / "public/archive/2026-10-23/repro_bundle.json").exists()
        )

    def test_receipt_write_failure_rolls_back_all_staged_evidence(self) -> None:
        self._write_evidence()
        with patch.object(
            private,
            "_write_receipt",
            side_effect=OSError("synthetic receipt write failure"),
        ):
            with self.assertRaisesRegex(OSError, "synthetic receipt write failure"):
                private.stage(self.evidence, self.worktree, self.receipt)

        self.assertFalse(self.receipt.exists())
        self.assertFalse(
            (self.worktree / "public/data/score_repro_bundle_latest.json").exists()
        )
        self.assertFalse(
            (self.worktree / "public/archive/2026-10-16/repro_bundle.json").exists()
        )
        self.assertFalse(
            (self.worktree / "public/archive/2026-10-23/repro_bundle.json").exists()
        )

    def test_cleanup_rejects_tampered_receipt_path_before_deletion(self) -> None:
        self._write_evidence()
        private.stage(self.evidence, self.worktree, self.receipt)
        latest = self.worktree / "public/data/score_repro_bundle_latest.json"
        unrelated = self.worktree / "public/data/unrelated.json"
        unrelated.write_bytes(latest.read_bytes())

        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        receipt["files"][0]["path"] = "public/data/unrelated.json"
        receipt["files"][0]["sha256"] = private.sha256_bytes(unrelated.read_bytes())
        self.receipt.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(RuntimeError, "unapproved path"):
            private.cleanup(self.worktree, self.receipt)
        self.assertTrue(unrelated.exists())
        self.assertTrue(latest.exists())

    def test_cleanup_rejects_receipt_archive_count_mismatch(self) -> None:
        self._write_evidence()
        private.stage(self.evidence, self.worktree, self.receipt)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        receipt["archive_count"] = 99
        self.receipt.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(RuntimeError, "archive_count does not match"):
            private.cleanup(self.worktree, self.receipt)

    def test_cleanup_wraps_malformed_receipt_as_runtime_error(self) -> None:
        self._write_evidence()
        private.stage(self.evidence, self.worktree, self.receipt)
        self.receipt.write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "invalid private evidence receipt"):
            private.cleanup(self.worktree, self.receipt)

    def test_receipt_exclusive_create_never_deletes_existing_file(self) -> None:
        existing = "owned by another process\n"
        self.receipt.write_text(existing, encoding="utf-8")
        receipt = {
            "schema_version": private.RECEIPT_VERSION,
            "latest_week": "2026-10-23",
            "archive_count": 1,
            "files": [
                {
                    "path": private.LATEST_DESTINATION.as_posix(),
                    "sha256": "1" * 64,
                },
                {
                    "path": "public/archive/2026-10-23/repro_bundle.json",
                    "sha256": "2" * 64,
                },
            ],
            "provider_derived_values_in_receipt": False,
            "worktree_contract": "ephemeral-private-evidence-only",
        }
        with self.assertRaises(FileExistsError):
            private._write_receipt(self.receipt, receipt)
        self.assertEqual(self.receipt.read_text(encoding="utf-8"), existing)

    def test_receipt_schema_is_closed_and_hash_only(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(
            set(schema["properties"]),
            {
                "schema_version",
                "latest_week",
                "archive_count",
                "files",
                "provider_derived_values_in_receipt",
                "worktree_contract",
            },
        )
        file_properties = schema["properties"]["files"]["items"]["properties"]
        self.assertEqual(set(file_properties), {"path", "sha256"})
        self.assertIs(
            schema["properties"]["files"]["items"]["additionalProperties"],
            False,
        )

    def test_rejects_repo_paths_for_private_material(self) -> None:
        self._write_evidence()
        with self.assertRaisesRegex(RuntimeError, "outside the repository"):
            private._require_outside_repo(private.REPO_ROOT / "public", "test")


if __name__ == "__main__":
    unittest.main()
