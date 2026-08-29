from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from scripts import score_v3_candidates as v3
from scripts import score_v3_manifest as manifest_v3


class ScoreV3ProspectiveManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = manifest_v3.load_manifest()
        cls.manifest["entries"] = []
        cls.initialization = json.loads(
            manifest_v3.INITIALIZATION_MANIFEST_PATH.read_text(encoding="utf-8")
        )

    def _entry(self, week: str = "2026-08-28") -> dict[str, str]:
        return {
            "week": week,
            "ingested_at_utc": f"{week}T23:00:00+00:00",
            "source_v2_bundle_sha256": "a" * 64,
            "source_v2_pipeline_commit_sha": "b" * 40,
            "source_v2_attestation_status": "passed",
            "locked_preregistration_commit_sha": v3.LOCKED_PREREGISTRATION_SHA,
            "initialization_matrix_sha256": self.initialization["matrix_sha256"],
            "candidate_result_file": f"score_v3_shadow_{week}.json",
            "candidate_result_sha256": "c" * 64,
        }

    def test_empty_manifest_is_bound_to_locked_protocol_and_matrix(self) -> None:
        report = manifest_v3.validate_manifest(self.manifest)
        self.assertEqual(report["entries"], 0)
        self.assertEqual(report["locked_preregistration_commit_sha"], v3.LOCKED_PREREGISTRATION_SHA)
        self.assertEqual(
            report["initialization_matrix_sha256"],
            self.initialization["matrix_sha256"],
        )
        matrix_path = Path("research") / self.initialization["matrix_file"]
        self.assertEqual(
            self.initialization["matrix_sha256"],
            hashlib.sha256(matrix_path.read_bytes()).hexdigest(),
        )

    def test_first_holdout_week_can_be_appended_without_mutating_existing_manifest(self) -> None:
        original = json.loads(json.dumps(self.manifest))
        updated = manifest_v3.append_entry(self.manifest, self._entry())
        self.assertEqual(self.manifest, original)
        self.assertEqual(len(updated["entries"]), 1)
        self.assertEqual(updated["entries"][0]["week"], "2026-08-28")

    def test_pre_holdout_backfill_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "predates holdout start"):
            manifest_v3.append_entry(self.manifest, self._entry("2026-08-21"))

    def test_duplicate_week_is_rejected(self) -> None:
        once = manifest_v3.append_entry(self.manifest, self._entry("2026-08-28"))
        with self.assertRaisesRegex(RuntimeError, "Duplicate prospective week"):
            manifest_v3.append_entry(once, self._entry("2026-08-28"))

    def test_out_of_order_week_is_rejected(self) -> None:
        once = manifest_v3.append_entry(self.manifest, self._entry("2026-09-04"))
        with self.assertRaisesRegex(RuntimeError, "strictly increasing"):
            manifest_v3.append_entry(once, self._entry("2026-08-28"))

    def test_failed_source_attestation_is_rejected(self) -> None:
        entry = self._entry()
        entry["source_v2_attestation_status"] = "failed"
        with self.assertRaisesRegex(RuntimeError, "lacks passed v2 attestation"):
            manifest_v3.append_entry(self.manifest, entry)

    def test_different_initialization_hash_is_rejected(self) -> None:
        entry = self._entry()
        entry["initialization_matrix_sha256"] = "d" * 64
        with self.assertRaisesRegex(RuntimeError, "initialization hash mismatch"):
            manifest_v3.append_entry(self.manifest, entry)

    def test_manifest_cannot_change_candidate_set_or_selection_boundary(self) -> None:
        modified = copy.deepcopy(self.manifest)
        modified["candidate_ids"].append("V3_POST_HOC")
        with self.assertRaisesRegex(RuntimeError, "candidate set drifted"):
            manifest_v3.validate_manifest(modified)

        modified = copy.deepcopy(self.manifest)
        modified["minimum_completed_weeks_before_selection"] = 26
        with self.assertRaisesRegex(RuntimeError, "52 weeks"):
            manifest_v3.validate_manifest(modified)


if __name__ == "__main__":
    unittest.main()
