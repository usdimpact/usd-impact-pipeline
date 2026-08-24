import unittest
from pathlib import Path


class ResearchValidationWorkflowTests(unittest.TestCase):
    def test_live_research_runs_as_package_module(self):
        workflow = Path('.github/workflows/research-validation.yml').read_text(encoding='utf-8')
        self.assertIn('python -m scripts.score_robustness_battery', workflow)
        self.assertNotIn('python scripts/score_robustness_battery.py', workflow)

    def test_research_failure_remains_visible_and_fail_closed(self):
        workflow = Path('.github/workflows/research-validation.yml').read_text(encoding='utf-8')
        self.assertIn('Report research validation failure', workflow)
        self.assertIn('if: failure()', workflow)
        self.assertIn('Score v2 research validation requires attention', workflow)
        self.assertIn('The production Weekly USD Impact Score is unaffected.', workflow)


if __name__ == '__main__':
    unittest.main()
