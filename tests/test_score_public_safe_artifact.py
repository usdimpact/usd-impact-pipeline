from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "build_score_public_safe_artifact.py"
SCORE_PATH = REPO_ROOT / "public" / "data" / "usd_impact_score_v2.json"

spec = importlib.util.spec_from_file_location("score_public_safe", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class ScorePublicSafeArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = json.loads(SCORE_PATH.read_text(encoding="utf-8"))

    def test_preserves_aggregate_score_regime_history_only(self) -> None:
        payload = module.build_public_safe_payload(self.source)

        self.assertEqual(payload["schema_version"], "score-public-v2-safe-1")
        self.assertEqual(len(payload["history"]), len(self.source["weeks"]))
        self.assertEqual(
            payload["latest"]["week_ending"],
            self.source["metadata"]["latest_date"],
        )
        self.assertEqual(
            payload["latest"]["score"],
            self.source["metadata"]["latest_score"],
        )
        self.assertEqual(
            payload["latest"]["regime"],
            self.source["metadata"]["latest_regime"],
        )

        for source_row, safe_row in zip(self.source["weeks"], payload["history"]):
            self.assertEqual(
                safe_row,
                {
                    "date": source_row["date"],
                    "score": source_row["score"],
                    "regime": source_row["regime"],
                },
            )

    def test_forbidden_provider_derived_fields_are_absent(self) -> None:
        payload = module.build_public_safe_payload(self.source)
        module.assert_public_safe(payload)
        raw = json.dumps(payload, sort_keys=True)

        for forbidden in (
            "DX-Y.NYB",
            "CL=F",
            "^GSPC",
            "^VIX",
            "BTC-USD",
            "GC=F",
            "Yahoo Finance",
            "weekly_level",
            "z_unclipped",
            "z_clipped",
            "source_provenance",
            "source_url",
            "contribution",
            "sample_std_ddof_1",
        ):
            self.assertNotIn(forbidden, raw)

    def test_csv_contains_only_date_score_regime(self) -> None:
        payload = module.build_public_safe_payload(self.source)
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "score.json"
            csv_path = Path(tmp) / "score.csv"
            module.write_outputs(payload, json_path, csv_path)

            with csv_path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, ["date", "score", "regime"])
                rows = list(reader)

            self.assertEqual(len(rows), len(payload["history"]))
            self.assertEqual(rows[-1]["date"], payload["latest"]["week_ending"])
            self.assertEqual(float(rows[-1]["score"]), payload["latest"]["score"])
            self.assertEqual(rows[-1]["regime"], payload["latest"]["regime"])

    def test_rejects_forbidden_key_in_public_payload(self) -> None:
        payload = module.build_public_safe_payload(self.source)
        payload["latest"]["weekly_level"] = 123.0
        with self.assertRaisesRegex(ValueError, "forbidden keys"):
            module.assert_public_safe(payload)


if __name__ == "__main__":
    unittest.main()
