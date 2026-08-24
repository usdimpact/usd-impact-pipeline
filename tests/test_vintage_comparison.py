import csv
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import usd_impact_score_v2 as score_v2
from scripts.build_vintage_comparison import build_vintage_comparison, write_csv


def score_row(date, score, regime, *, component=0.2):
    return {
        "date": date,
        **{driver: component for driver in score_v2.WEIGHTS},
        "score": score,
        "regime": regime,
    }


def score_payload(generated_at, weeks):
    latest = weeks[-1]
    return {
        "metadata": {
            "generated_at_utc": generated_at,
            "latest_date": latest["date"],
            "latest_score": latest["score"],
            "latest_regime": latest["regime"],
            "n_weeks": len(weeks),
        },
        "weeks": weeks,
    }


class VintageComparisonTests(unittest.TestCase):
    def _write(self, path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_compares_valid_vintages_and_excludes_future_labeled_archive(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            current = root / "current.json"
            archive = root / "archive"
            self._write(current, score_payload(
                "2026-02-13T23:00:00+00:00",
                [
                    score_row("2026-01-30", 0.4, "Firm dollar regime", component=0.2),
                    score_row("2026-02-06", 0.2, "Neutral / transitional", component=0.3),
                ],
            ))
            self._write(archive / "2026-02-01/score.json", score_payload(
                "2026-02-01T10:00:00+00:00",
                [score_row("2026-01-30", 0.5, "Firm dollar regime", component=0.1)],
            ))
            self._write(archive / "2026-02-07/score.json", score_payload(
                "2026-02-07T10:00:00+00:00",
                [score_row("2026-02-06", -0.4, "Soft dollar regime", component=0.1)],
            ))
            self._write(archive / "2026-02-08/score.json", score_payload(
                "2026-02-08T10:00:00+00:00",
                [score_row("2026-02-13", 0.1, "Neutral / transitional")],
            ))

            report = build_vintage_comparison(
                current,
                archive,
                generated_at=datetime(2026, 2, 14, tzinfo=timezone.utc),
            )

            self.assertFalse(report["production_methodology_changed"])
            self.assertFalse(report["predictive_claim"])
            self.assertTrue(report["as_published_vintage"])
            self.assertEqual(
                report["difference_definition"],
                "current_recalculated_value - as_published_value",
            )
            self.assertEqual(report["summary"]["archive_files_scanned"], 3)
            self.assertEqual(report["summary"]["valid_vintages"], 2)
            self.assertEqual(report["summary"]["excluded_archives"], 1)
            self.assertAlmostEqual(
                report["summary"]["mean_absolute_score_difference"], 0.35
            )
            self.assertAlmostEqual(report["summary"]["regime_agreement_rate"], 0.5)
            self.assertEqual(
                report["excluded_archives"][0]["reason"],
                "score_week_after_generation_date",
            )
            first = report["vintages"][0]
            self.assertEqual(first["archive_id"], "2026-02-01")
            self.assertEqual(len(first["archive_sha256"]), 64)
            self.assertAlmostEqual(first["score_difference"], -0.1)
            self.assertAlmostEqual(
                first["component_zscore_revisions"]["DXY"]["difference"], 0.1
            )

            csv_path = root / "comparison.csv"
            write_csv(report, csv_path)
            with csv_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertIn("DXY_zscore_difference", rows[0])

    def test_checked_in_legacy_archive_anomalies_remain_explicit(self):
        report = build_vintage_comparison(
            generated_at=datetime(2026, 8, 24, tzinfo=timezone.utc)
        )
        excluded = {
            row["archive_id"]: row["reason"]
            for row in report["excluded_archives"]
        }
        self.assertEqual(excluded, {
            "2026-05-02": "score_week_after_generation_date",
            "2026-05-09": "score_week_after_generation_date",
            "2026-05-16": "score_week_after_generation_date",
        })
        self.assertGreaterEqual(report["summary"]["valid_vintages"], 15)
        self.assertEqual(
            report["summary"]["archive_files_scanned"],
            report["summary"]["valid_vintages"] + len(excluded),
        )


if __name__ == "__main__":
    unittest.main()
