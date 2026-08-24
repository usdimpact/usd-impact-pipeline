import copy
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import usd_impact_score_v2 as score_v2
from scripts.build_score_repro_bundle import build_bundle
from scripts.validate_weekly_release import (
    REPRO_BUNDLE_REQUIRED_FROM,
    reproduction_bundle_required,
    validate_reproduction_bundle,
)


class NullLogger:
    def debug(self, *_args, **_kwargs):
        pass

    def info(self, *_args, **_kwargs):
        pass


class WeeklyReleaseReproductionBundleTests(unittest.TestCase):
    def setUp(self):
        fixture = Path("tests/fixtures/weekly_levels.csv")
        self.weekly = pd.read_csv(fixture, parse_dates=["date"]).set_index("date")
        self.weekly = self.weekly[list(score_v2.WEIGHTS)].dropna()
        z = score_v2.compute_zscores(
            self.weekly, score_v2.ZSCORE_CLIP, NullLogger()
        )
        score = score_v2.compute_score(z, score_v2.WEIGHTS, NullLogger())
        out = score_v2.build_output_frame(z, score)
        self.week = out.index[-1].date().isoformat()
        provenance = {
            driver: {
                "driver": driver,
                "provider": "fixture",
                "provider_code": "fixture",
                "series": driver,
                "source_url": f"fixture://{driver}",
                "observation_date": self.week,
                "score_week": self.week,
                "age_days": 0,
                "max_age_days": 0,
                "status": "fresh",
                "retrieval_mode": "fixture",
            }
            for driver in score_v2.WEIGHTS
        }
        self.metadata = {
            "latest_date": self.week,
            "latest_score": float(score.iloc[-1]),
            "latest_regime": out["regime"].iloc[-1],
            "source_provenance_version": 1,
            "source_provenance": provenance,
        }
        self.score_json = {
            "metadata": self.metadata,
            "weeks": [
                {
                    "date": idx.date().isoformat(),
                    **{driver: float(row[driver]) for driver in score_v2.WEIGHTS},
                    "score": float(row["score"]),
                    "regime": row["regime"],
                }
                for idx, row in out.iterrows()
            ],
        }
        self.provider_daily_evidence = (
            score_v2.build_provider_derived_daily_fingerprint(
                self.weekly,
                self.week,
                retrieval_run_started_at=datetime(
                    2026, 8, 24, tzinfo=timezone.utc
                ),
                retrieval_mode="live",
            )
        )

    def _make_root_and_bundle(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        lock_content = b"fixture requirements lock\n"
        (root / "requirements.lock").write_bytes(lock_content)
        lock_sha = hashlib.sha256(lock_content).hexdigest()
        bundle = build_bundle(
            self.weekly,
            self.metadata["source_provenance"],
            self.score_json,
            self.provider_daily_evidence,
            generated_at=datetime(2026, 8, 24, tzinfo=timezone.utc),
            git_sha="a" * 40,
            lock_sha256=lock_sha,
        )
        latest_path = root / "public/data/score_repro_bundle_latest.json"
        archive_path = root / f"public/archive/{self.week}/repro_bundle.json"
        latest_path.parent.mkdir(parents=True, exist_ok=True)
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(bundle, indent=2)
        latest_path.write_text(payload, encoding="utf-8")
        archive_path.write_text(payload, encoding="utf-8")
        return temp, root, bundle, latest_path, archive_path

    def test_bundle_requirement_starts_after_legacy_august_21_release(self):
        self.assertEqual(REPRO_BUNDLE_REQUIRED_FROM.isoformat(), "2026-08-28")
        self.assertFalse(reproduction_bundle_required("2026-08-21"))
        self.assertTrue(reproduction_bundle_required("2026-08-28"))
        self.assertTrue(reproduction_bundle_required("2026-09-04"))

    def test_validator_reproduces_bundle_from_frozen_values_only(self):
        temp, root, _bundle, _latest, _archive = self._make_root_and_bundle()
        self.addCleanup(temp.cleanup)
        validate_reproduction_bundle(root, self.metadata, self.week)

    def test_validator_rejects_tampered_frozen_level(self):
        temp, root, bundle, latest_path, archive_path = self._make_root_and_bundle()
        self.addCleanup(temp.cleanup)
        tampered = copy.deepcopy(bundle)
        tampered["components"]["DXY"]["weekly_level"] += 0.25
        payload = json.dumps(tampered, indent=2)
        latest_path.write_text(payload, encoding="utf-8")
        archive_path.write_text(payload, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "raw z does not reproduce"):
            validate_reproduction_bundle(root, self.metadata, self.week)

    def test_validator_rejects_archive_that_differs_from_latest(self):
        temp, root, bundle, _latest_path, archive_path = self._make_root_and_bundle()
        self.addCleanup(temp.cleanup)
        tampered_archive = copy.deepcopy(bundle)
        tampered_archive["published"]["score"] += 0.01
        archive_path.write_text(json.dumps(tampered_archive, indent=2), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Archived reproduction bundle differs"):
            validate_reproduction_bundle(root, self.metadata, self.week)

    def test_validator_rejects_dependency_lock_mismatch(self):
        temp, root, _bundle, _latest, _archive = self._make_root_and_bundle()
        self.addCleanup(temp.cleanup)
        (root / "requirements.lock").write_text("changed lock\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "requirements lock hash does not match"):
            validate_reproduction_bundle(root, self.metadata, self.week)

    def test_validator_rejects_false_raw_provider_archive_claim(self):
        temp, root, bundle, latest_path, archive_path = self._make_root_and_bundle()
        self.addCleanup(temp.cleanup)
        tampered = copy.deepcopy(bundle)
        tampered["input_history_fingerprint"]["raw_provider_payloads_archived"] = True
        payload = json.dumps(tampered, indent=2)
        latest_path.write_text(payload, encoding="utf-8")
        archive_path.write_text(payload, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "must not claim"):
            validate_reproduction_bundle(root, self.metadata, self.week)

    def test_validator_rejects_malformed_input_history_hash(self):
        temp, root, bundle, latest_path, archive_path = self._make_root_and_bundle()
        self.addCleanup(temp.cleanup)
        tampered = copy.deepcopy(bundle)
        tampered["input_history_fingerprint"]["drivers"]["DXY"]["sha256"] = "bad"
        payload = json.dumps(tampered, indent=2)
        latest_path.write_text(payload, encoding="utf-8")
        archive_path.write_text(payload, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "DXY SHA-256 is invalid"):
            validate_reproduction_bundle(root, self.metadata, self.week)

    def test_validator_rejects_false_raw_payload_claim_in_daily_receipt(self):
        temp, root, bundle, latest_path, archive_path = self._make_root_and_bundle()
        self.addCleanup(temp.cleanup)
        tampered = copy.deepcopy(bundle)
        tampered["provider_derived_daily_history_fingerprint"][
            "raw_provider_payloads_archived"
        ] = True
        payload = json.dumps(tampered, indent=2)
        latest_path.write_text(payload, encoding="utf-8")
        archive_path.write_text(payload, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "must not claim raw provider"):
            validate_reproduction_bundle(root, self.metadata, self.week)

    def test_validator_rejects_malformed_provider_daily_hash(self):
        temp, root, bundle, latest_path, archive_path = self._make_root_and_bundle()
        self.addCleanup(temp.cleanup)
        tampered = copy.deepcopy(bundle)
        tampered["provider_derived_daily_history_fingerprint"]["drivers"][
            "DXY"
        ]["sha256"] = "bad"
        payload = json.dumps(tampered, indent=2)
        latest_path.write_text(payload, encoding="utf-8")
        archive_path.write_text(payload, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "DXY SHA-256 is invalid"):
            validate_reproduction_bundle(root, self.metadata, self.week)


if __name__ == "__main__":
    unittest.main()
