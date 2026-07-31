import unittest
from datetime import datetime, timedelta, timezone

from scripts.weekly_recovery_decision import decide_weekly_recovery


NOW = datetime(2026, 8, 1, 0, 15, tzinfo=timezone.utc)
MAX_AGE = timedelta(hours=6)


def run(status="completed", conclusion="success", created_at="2026-07-31T22:57:43Z"):
    return [{"status": status, "conclusion": conclusion, "createdAt": created_at}]


class WeeklyRecoveryDecisionTests(unittest.TestCase):
    def decide(self, runs):
        return decide_weekly_recovery(runs, now=NOW, max_age=MAX_AGE)

    def test_dispatches_after_a_recent_failure(self):
        decision = self.decide(run(conclusion="failure"))
        self.assertTrue(decision.should_dispatch)
        self.assertIn("conclusion=failure", decision.reason)

    def test_skips_after_a_recent_success(self):
        decision = self.decide(run())
        self.assertFalse(decision.should_dispatch)
        self.assertIn("successfully", decision.reason)

    def test_skips_while_the_release_is_still_running(self):
        decision = self.decide(run(status="in_progress", conclusion=None))
        self.assertFalse(decision.should_dispatch)
        self.assertIn("still in_progress", decision.reason)

    def test_dispatches_when_the_latest_run_is_stale(self):
        decision = self.decide(run(created_at="2026-07-24T22:57:43Z"))
        self.assertTrue(decision.should_dispatch)
        self.assertIn("stale", decision.reason)

    def test_dispatches_when_no_run_exists(self):
        decision = self.decide([])
        self.assertTrue(decision.should_dispatch)
        self.assertIn("no Weekly USD Impact Score run", decision.reason)


if __name__ == "__main__":
    unittest.main()
