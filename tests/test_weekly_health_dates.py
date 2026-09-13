from datetime import date, datetime, timezone
import unittest

from scripts.check_weekly_health import latest_completed_friday, weekly_run_matches_expected_period


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

    def test_weekly_run_stays_current_through_following_thursday(self):
        run_started = datetime(2026, 9, 11, 23, 52, tzinfo=timezone.utc)
        for current_day in range(12, 18):
            with self.subTest(current_day=current_day):
                now = datetime(2026, 9, current_day, 12, 0, tzinfo=timezone.utc)
                self.assertTrue(weekly_run_matches_expected_period(run_started, now))

    def test_weekly_run_becomes_stale_when_next_friday_completes(self):
        run_started = datetime(2026, 9, 11, 23, 52, tzinfo=timezone.utc)
        now = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
        self.assertFalse(weekly_run_matches_expected_period(run_started, now))

    def test_saturday_run_maps_to_previous_friday_period(self):
        run_started = datetime(2026, 9, 12, 1, 30, tzinfo=timezone.utc)
        now = datetime(2026, 9, 13, 12, 0, tzinfo=timezone.utc)
        self.assertTrue(weekly_run_matches_expected_period(run_started, now))


if __name__ == "__main__":
    unittest.main()
