import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


class GitHubActionRuntimeTests(unittest.TestCase):
    def test_official_runtime_actions_use_node24_compatible_majors(self):
        workflow_files = sorted(WORKFLOWS.glob("*.y*ml"))
        self.assertTrue(workflow_files, "No GitHub Actions workflows found")

        combined = "\n".join(path.read_text(encoding="utf-8") for path in workflow_files)
        checkout_versions = re.findall(r"actions/checkout@v(\d+)", combined)
        setup_python_versions = re.findall(r"actions/setup-python@v(\d+)", combined)

        self.assertTrue(checkout_versions, "No actions/checkout reference found")
        self.assertTrue(setup_python_versions, "No actions/setup-python reference found")
        self.assertTrue(all(version == "7" for version in checkout_versions))
        self.assertTrue(all(version == "6" for version in setup_python_versions))
        self.assertNotIn("ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION", combined)


if __name__ == "__main__":
    unittest.main()
