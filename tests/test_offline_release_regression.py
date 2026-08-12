import hashlib
import json
import logging
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts.generate_weekly_archive_index import generate_archive_indexes
from scripts.generate_weekly_commentary import main as generate_commentary
from scripts.validate_weekly_release import validate
from usd_impact_score_v2 import (
    WEIGHTS,
    ZSCORE_CLIP,
    build_graphic_payload,
    build_output_frame,
    build_source_provenance,
    compute_score,
    compute_zscores,
    export_csv,
    export_html,
    export_json,
    validate_source_freshness,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class OfflineReleaseRegressionTests(unittest.TestCase):
    """Exercise the complete deterministic release path without network data."""

    def setUp(self):
        self.logger = logging.getLogger(self.id())
        self.logger.handlers.clear()
        self.logger.addHandler(logging.NullHandler())

    def test_frozen_fixture_builds_a_complete_expected_release(self):
        expected = json.loads(
            (FIXTURES / "expected_offline_release.json").read_text(encoding="utf-8")
        )
        levels = pd.read_csv(
            FIXTURES / expected["fixture"],
            parse_dates=["date"],
        ).set_index("date")

        zscores = compute_zscores(levels, ZSCORE_CLIP, self.logger)
        score = compute_score(zscores, WEIGHTS, self.logger)
        output = build_output_frame(zscores, score)

        self.assertEqual(output.index[-1].date().isoformat(), expected["latest_date"])
        self.assertAlmostEqual(float(score.iloc[-1]), expected["latest_score"], places=12)
        self.assertEqual(output["regime"].iloc[-1], expected["latest_regime"])

        with tempfile.TemporaryDirectory() as temporary_directory:
            release_root = Path(temporary_directory)
            public = release_root / "public"
            public_data = public / "data"
            public_data.mkdir(parents=True)
            (public / "en").mkdir()
            (public / "es").mkdir()

            csv_path = public_data / "usd_impact_score_v2.csv"
            score_path = public_data / "usd_impact_score_v2.json"
            generated_at = datetime(2024, 4, 19, 22, tzinfo=timezone.utc)
            source_provenance = build_source_provenance(
                levels,
                output.index[-1],
            )
            validate_source_freshness(
                source_provenance,
                output.index[-1],
                self.logger,
            )
            export_csv(output, csv_path, self.logger)
            export_json(
                output,
                score_path,
                self.logger,
                generated_at=generated_at,
                source_provenance=source_provenance,
            )

            score_payload = json.loads(score_path.read_text(encoding="utf-8"))
            score_text = score_path.read_text(encoding="utf-8")
            digest = hashlib.sha256(score_text.encode("utf-8")).hexdigest()
            self.assertEqual(digest, expected["score_payload_sha256"])

            commentary_dir = release_root / "commentary"
            bridge_dir = release_root / "data"
            with patch.object(
                sys,
                "argv",
                [
                    "generate_weekly_commentary.py",
                    "--score-json",
                    str(score_path),
                    "--commentary-dir",
                    str(commentary_dir),
                    "--bridge-dir",
                    str(bridge_dir),
                    "--public-data-dir",
                    str(public_data),
                ],
            ):
                self.assertEqual(generate_commentary(), 0)

            previous_working_directory = Path.cwd()
            try:
                os.chdir(release_root)
                with patch.dict(
                    os.environ,
                    {"MPLCONFIGDIR": str(release_root / ".matplotlib")},
                ):
                    export_html(
                        build_graphic_payload(output, score, lang="en"),
                        public / "en/index.html",
                        self.logger,
                    )
                    export_html(
                        build_graphic_payload(output, score, lang="es"),
                        public / "es/index.html",
                        self.logger,
                    )
            finally:
                os.chdir(previous_working_directory)

            week = expected["latest_date"]
            archive = public / "archive" / week
            archive.mkdir(parents=True)
            shutil.copy2(public / "en/index.html", archive / "en.html")
            shutil.copy2(public / "es/index.html", archive / "es.html")
            shutil.copy2(score_path, archive / "score.json")
            shutil.copy2(public_data / "weekly_input_latest.json", archive / "weekly_input.json")

            editions = generate_archive_indexes(release_root)
            self.assertEqual(editions, [])
            self.assertEqual(validate(release_root), week)

            bridge = json.loads(
                (public_data / "weekly_input_latest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                bridge["source_provenance"],
                score_payload["metadata"]["source_provenance"],
            )

            self.assertEqual(
                (commentary_dir / "latest.md").read_text(encoding="utf-8"),
                (commentary_dir / "latest_en.md").read_text(encoding="utf-8"),
            )
            (commentary_dir / "latest.md").write_text(
                "# Automated Regime Commentary — Week of April 12, 2024\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "commentary/latest.md",
            ):
                validate(release_root)


if __name__ == "__main__":
    unittest.main()
