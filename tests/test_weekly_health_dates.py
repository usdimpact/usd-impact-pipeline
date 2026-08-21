from datetime import date
import unittest

from scripts.check_weekly_health import latest_completed_friday


class WeeklyHealthDateTests(unittest.TestCase):
    def test_latest_completed_friday_for_each_weekday(self):
        cases = {
            date(2026, 8, 21): date(2026, 8, 21),  # Friday
            date(2026, 8, 22): date(2026, 8, 21),  # Saturday
            date(2026, 8, 23): date(2026, 8, 21),  # Sunday
            date(2026, 8, 24): date(2026, 8, 21),  # Monday
            date(2026, 8, 25): date(2026, 8, 21),  # Tuesday
            date(2026, 8, 26): date(2026, 8, 21),  # Wednesday
            date(2026, 8, 27): date(2026, 8, 21),  # Thursday
        }
        for run_date, expected in cases.items():
            with self.subTest(run_date=run_date):
                self.assertEqual(latest_completed_friday(run_date), expected)


if __name__ == "__main__":
    unittest.main()
