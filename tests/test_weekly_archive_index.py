import json
import tempfile
import unittest
from pathlib import Path

from scripts.generate_weekly_archive_index import generate_archive_indexes


class WeeklyArchiveIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        latest = self.root / "public/data/usd_impact_score_v2.json"
        latest.parent.mkdir(parents=True)
        latest.write_text(json.dumps({"metadata": {"latest_date": "2026-07-31"}}))

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_archive(self, directory_week, *, metadata_week=None, complete=True):
        directory = self.root / "public/archive" / directory_week
        directory.mkdir(parents=True)
        payload = {
            "metadata": {
                "latest_date": metadata_week or directory_week,
                "latest_score": -0.42,
                "latest_regime": "Soft dollar regime",
            }
        }
        (directory / "score.json").write_text(json.dumps(payload))
        (directory / "en.html").write_text("English dashboard")
        if complete:
            (directory / "es.html").write_text("Spanish dashboard")

    def test_indexes_include_only_complete_matching_previous_archives(self):
        self.add_archive("2026-07-31")
        self.add_archive("2026-08-07")
        self.add_archive("2026-07-24")
        self.add_archive("2026-07-17")
        self.add_archive("2026-07-10", metadata_week="2026-07-17")
        self.add_archive("2026-07-03", complete=False)

        editions = generate_archive_indexes(self.root)

        self.assertEqual([edition.week.isoformat() for edition in editions], ["2026-07-24", "2026-07-17"])
        english = (self.root / "public/archive/en/index.html").read_text()
        spanish = (self.root / "public/archive/es/index.html").read_text()
        self.assertIn("Previous weeks", english)
        self.assertIn("/archive/2026-07-24/en.html", english)
        self.assertLess(english.index("2026-07-24"), english.index("2026-07-17"))
        self.assertNotIn("/archive/2026-07-31/en.html", english)
        self.assertNotIn("/archive/2026-08-07/en.html", english)
        self.assertNotIn("/archive/2026-07-10/en.html", english)
        self.assertNotIn("/archive/2026-07-03/en.html", english)
        self.assertIn("Semanas anteriores", spanish)
        self.assertIn("/archive/2026-07-24/es.html", spanish)


if __name__ == "__main__":
    unittest.main()
