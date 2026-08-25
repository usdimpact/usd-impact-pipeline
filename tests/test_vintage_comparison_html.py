import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.build_vintage_comparison import build_vintage_comparison, write_html


class VintageComparisonHtmlTests(unittest.TestCase):
    def test_human_readable_audit_is_static_complete_and_non_predictive(self):
        report = build_vintage_comparison(
            generated_at=datetime(2026, 8, 24, tzinfo=timezone.utc)
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "vintage-audit.html"
            write_html(report, output)
            html = output.read_text(encoding="utf-8")

        self.assertIn(
            "As-published vs current recalculated score vintages",
            html,
        )
        self.assertIn("Descriptive revision audit only.", html)
        self.assertIn("not a predictive backtest", html)
        self.assertIn("current recalculated value minus as-published value", html)
        self.assertIn("score_v2_vintage_comparison_latest.json", html)
        self.assertIn("score_v2_vintage_comparison_latest.csv", html)
        self.assertNotIn("<script", html.lower())
        self.assertEqual(
            html.count("<tbody>"),
            2,
            "The page should expose the valid-vintage table and excluded-archive table.",
        )
        for row in report["vintages"][-3:]:
            self.assertIn(row["score_week"], html)
            self.assertIn(row["as_published_regime"], html)
        for row in report["excluded_archives"]:
            self.assertIn(row["archive_id"], html)
            self.assertIn(row["reason"], html)


if __name__ == "__main__":
    unittest.main()
