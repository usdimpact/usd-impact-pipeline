import unittest
from pathlib import Path


class ResearchValidationWorkflowTests(unittest.TestCase):
    def test_live_research_runs_as_package_module(self):
        workflow = Path('.github/workflows/research-validation.yml').read_text(encoding='utf-8')
        self.assertIn('python -m scripts.score_robustness_battery', workflow)
        self.assertIn('python -m scripts.build_vintage_comparison', workflow)
        self.assertNotIn('python scripts/score_robustness_battery.py', workflow)
        self.assertNotIn('python scripts/build_vintage_comparison.py', workflow)

    def test_vintage_publication_is_validated_before_merge(self):
        workflow = Path('.github/workflows/research-validation.yml').read_text(encoding='utf-8')
        self.assertIn('score_v2_vintage_comparison_latest.json', workflow)
        self.assertIn('score_v2_vintage_comparison_latest.csv', workflow)
        self.assertIn("vintage['predictive_claim'] is False", workflow)
        self.assertIn("vintage['as_published_vintage'] is True", workflow)
        self.assertIn("vintage['current_reference']['latest_week'] == expected_week", workflow)
        self.assertIn("date.fromisoformat(row['score_week'])", workflow)

    def test_research_waits_for_current_weekly_release_and_retriggers_on_release(self):
        workflow = Path('.github/workflows/research-validation.yml').read_text(encoding='utf-8')
        self.assertIn("- 'public/data/usd_impact_score_v2.json'", workflow)
        self.assertIn('Check upstream weekly release readiness', workflow)
        self.assertIn("ready = current_week == expected_week", workflow)
        self.assertIn("if: steps.upstream.outputs.ready != 'true'", workflow)
        self.assertIn('Research publication deferred:', workflow)
        self.assertIn("if: steps.upstream.outputs.ready == 'true'", workflow)

    def test_research_failure_remains_visible_and_fail_closed_once_upstream_is_ready(self):
        workflow = Path('.github/workflows/research-validation.yml').read_text(encoding='utf-8')
        self.assertIn('Report research validation failure', workflow)
        self.assertIn("steps.upstream.outputs.ready == 'true' && failure()", workflow)
        self.assertIn('Score v2 research validation requires attention', workflow)
        self.assertIn('The production Weekly USD Impact Score is unaffected.', workflow)


if __name__ == '__main__':
    unittest.main()
