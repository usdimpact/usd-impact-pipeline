import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
CHECKOUT_REF = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7"
SETUP_PYTHON_REF = "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6"


class GitHubActionRuntimeTests(unittest.TestCase):
    def test_official_runtime_actions_use_verified_immutable_revisions(self):
        workflow_files = sorted(WORKFLOWS.glob("*.y*ml"))
        self.assertTrue(workflow_files, "No GitHub Actions workflows found")

        combined = "\n".join(path.read_text(encoding="utf-8") for path in workflow_files)
        checkout_lines = [line.strip() for line in combined.splitlines() if "actions/checkout@" in line]
        setup_python_lines = [line.strip() for line in combined.splitlines() if "actions/setup-python@" in line]

        self.assertTrue(checkout_lines, "No actions/checkout reference found")
        self.assertTrue(setup_python_lines, "No actions/setup-python reference found")
        self.assertTrue(all(line == f"uses: {CHECKOUT_REF}" for line in checkout_lines))
        self.assertTrue(all(line == f"uses: {SETUP_PYTHON_REF}" for line in setup_python_lines))
        self.assertNotIn("ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION", combined)

    def test_python_workflows_install_the_verified_lockfile(self):
        for workflow_name in ("quality.yml", "weekly.yml"):
            workflow = (WORKFLOWS / workflow_name).read_text(encoding="utf-8")
            with self.subTest(workflow=workflow_name):
                self.assertIn("cache-dependency-path: requirements.lock", workflow)
                self.assertIn("python -m pip install -r requirements.lock", workflow)
                self.assertIn("python -m pip check", workflow)


if __name__ == "__main__":
    unittest.main()
