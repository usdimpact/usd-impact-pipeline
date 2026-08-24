import unittest
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import usd_impact_score_v2 as score_v2
from scripts.build_score_repro_bundle import (
    build_bundle,
    build_input_history_fingerprint,
    reproduce_bundle,
    verify_bundle,
)


class NullLogger:
    def debug(self, *_args, **_kwargs):
        pass

    def info(self, *_args, **_kwargs):
        pass


class ScoreReproBundleTests(unittest.TestCase):
    def setUp(self):
        fixture = Path("tests/fixtures/weekly_levels.csv")
        self.weekly = pd.read_csv(fixture, parse_dates=["date"]).set_index("date")
        self.weekly = self.weekly[list(score_v2.WEIGHTS)].dropna()
        z = score_v2.compute_zscores(self.weekly, score_v2.ZSCORE_CLIP, NullLogger())
        score = score_v2.compute_score(z, score_v2.WEIGHTS, NullLogger())
        out = score_v2.build_output_frame(z, score)
        latest_date = out.index[-1].date().isoformat()

        provenance = {
            driver: {
                "driver": driver,
                "provider": "fixture",
                "provider_code": "fixture",
                "series": driver,
                "source_url": "fixture://weekly-levels",
                "observation_date": latest_date,
                "score_week": latest_date,
                "age_days": 0,
                "max_age_days": 0,
                "status": "fresh",
                "retrieval_mode": "fixture",
            }
            for driver in score_v2.WEIGHTS
        }

        self.score_json = {
            "metadata": {
                "latest_date": latest_date,
                "latest_score": float(score.iloc[-1]),
                "latest_regime": out["regime"].iloc[-1],
                "source_provenance_version": 1,
                "source_provenance": provenance,
            },
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

    def test_bundle_reproduces_published_score_offline(self):
        bundle = build_bundle(
            self.weekly,
            self.score_json["metadata"]["source_provenance"],
            self.score_json,
            generated_at=datetime(2026, 8, 24, tzinfo=timezone.utc),
            git_sha="fixture-sha",
            lock_sha256="fixture-lock",
        )
        verify_bundle(bundle)
        score, regime = reproduce_bundle(bundle)

        self.assertAlmostEqual(score, self.score_json["metadata"]["latest_score"], places=12)
        self.assertEqual(regime, self.score_json["metadata"]["latest_regime"])
        self.assertEqual(bundle["methodology_version"], "usd_impact_score_v2")
        self.assertEqual(set(bundle["components"]), set(score_v2.WEIGHTS))
        for driver, component in bundle["components"].items():
            self.assertEqual(component["normalization"]["sample_count"], len(self.weekly))
            self.assertEqual(component["weight"], score_v2.WEIGHTS[driver])

        fingerprint = bundle["input_history_fingerprint"]
        self.assertEqual(fingerprint["version"], 1)
        self.assertEqual(len(fingerprint["matrix_sha256"]), 64)
        self.assertFalse(fingerprint["raw_provider_payloads_archived"])
        self.assertFalse(fingerprint["public_full_source_history_included"])

    def test_input_history_fingerprint_detects_one_driver_revision(self):
        original = build_input_history_fingerprint(self.weekly)
        revised = self.weekly.copy()
        revised.loc[revised.index[0], "DXY"] += 0.0001
        changed = build_input_history_fingerprint(revised)

        self.assertNotEqual(original["matrix_sha256"], changed["matrix_sha256"])
        self.assertNotEqual(
            original["drivers"]["DXY"]["sha256"],
            changed["drivers"]["DXY"]["sha256"],
        )
        self.assertEqual(
            original["drivers"]["WTI"]["sha256"],
            changed["drivers"]["WTI"]["sha256"],
        )

    def test_same_run_snapshot_round_trips_and_cannot_enter_public_tree(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            snapshot = root / "work/weekly-levels.csv"
            score_v2.write_weekly_levels_snapshot(
                self.weekly,
                snapshot,
                NullLogger(),
                public_root=root / "public",
            )
            reloaded = pd.read_csv(
                snapshot,
                parse_dates=["date"],
                float_precision="round_trip",
            ).set_index("date")
            pd.testing.assert_frame_equal(
                reloaded,
                self.weekly,
                check_exact=False,
                rtol=0,
                atol=1e-12,
            )
            self.assertEqual(
                build_input_history_fingerprint(reloaded),
                build_input_history_fingerprint(self.weekly),
            )

            with self.assertRaisesRegex(RuntimeError, "outside the public output tree"):
                score_v2.write_weekly_levels_snapshot(
                    self.weekly,
                    root / "public/data/weekly-levels.csv",
                    NullLogger(),
                    public_root=root / "public",
                )

    def test_tampered_bundle_fails_verification(self):
        bundle = build_bundle(
            self.weekly,
            self.score_json["metadata"]["source_provenance"],
            self.score_json,
        )
        bundle["components"]["DXY"]["z_clipped"] += 0.01
        with self.assertRaises(RuntimeError):
            verify_bundle(bundle)

    def test_mismatched_published_component_fails_closed(self):
        bad = {
            "metadata": dict(self.score_json["metadata"]),
            "weeks": [dict(row) for row in self.score_json["weeks"]],
        }
        bad["weeks"][-1]["GOLD"] += 0.001
        with self.assertRaises(RuntimeError):
            build_bundle(
                self.weekly,
                bad["metadata"]["source_provenance"],
                bad,
            )


if __name__ == "__main__":
    unittest.main()
