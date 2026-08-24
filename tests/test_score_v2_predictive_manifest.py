from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts import score_v2_predictive_manifest as manifest
from tests.predictive_test_support import copy_predictive_contract


REPO = Path(__file__).resolve().parents[1]


class ScoreV2PredictiveManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        copy_predictive_contract(self.root)
        self.payload = json.loads((self.root / manifest.MANIFEST_PATH).read_text())

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_empty_manifest_is_bound_to_merged_preregistration(self) -> None:
        result = manifest.validate_manifest(self.payload, root=self.root)
        self.assertEqual(result["weekly_observations"], 0)
        self.assertEqual(result["resolved_predictions"], 0)
        self.assertEqual(
            self.payload["locked_preregistration_commit_sha"],
            "89bf56bafd594987176f31efaa926ecf02228289",
        )

    def test_tampered_protocol_fails_locked_hash(self) -> None:
        path = self.root / manifest.PROTOCOL_PATH
        path.write_text(path.read_text() + "\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "locked SHA-256"):
            manifest.validate_manifest(self.payload, root=self.root)

    def test_manifest_cannot_claim_predictive_power(self) -> None:
        altered = copy.deepcopy(self.payload)
        altered["predictive_power_status"] = "established"
        with self.assertRaisesRegex(RuntimeError, "may not claim"):
            manifest.validate_manifest(altered, root=self.root)

    def test_entry_grid_is_gap_intolerant_and_terminal_role_is_fixed(self) -> None:
        template = {
            "week": "2026-08-28",
            "record_role": "predictive_origin",
            "recorded_at_utc": "2026-08-28T23:00:00+00:00",
            "source_v2_bundle_sha256": "a" * 64,
            "source_v2_pipeline_commit_sha": "b" * 40,
            "source_v2_attestation_status": "passed",
            "source_v2_attestation_run_id": 123,
            "locked_preregistration_commit_sha": manifest.LOCKED_PREREGISTRATION_SHA,
            "implementation_contract_sha256": manifest.IMPLEMENTATION_CONTRACT_SHA256,
            "weekly_record_file": "score_v2_predictive_week_2026-08-28.json",
            "weekly_record_sha256": "c" * 64,
        }
        altered = copy.deepcopy(self.payload)
        first = copy.deepcopy(template)
        first["week"] = "2026-09-04"
        first["weekly_record_file"] = "score_v2_predictive_week_2026-09-04.json"
        altered["entries"] = [first]
        with self.assertRaisesRegex(RuntimeError, "gap or out-of-order"):
            manifest.validate_manifest(altered, root=self.root)

        terminal = copy.deepcopy(self.payload)
        for index in range(53):
            entry = copy.deepcopy(template)
            week = manifest.FIRST_ORIGIN.fromordinal(manifest.FIRST_ORIGIN.toordinal() + 7 * index)
            entry["week"] = week.isoformat()
            entry["weekly_record_file"] = f"score_v2_predictive_week_{week.isoformat()}.json"
            if index == 52:
                entry["record_role"] = "predictive_origin"
            terminal["entries"].append(entry)
        with self.assertRaisesRegex(RuntimeError, "record role drifted"):
            manifest.validate_manifest(terminal, root=self.root)


if __name__ == "__main__":
    unittest.main()
