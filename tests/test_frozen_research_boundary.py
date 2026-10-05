import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_frozen_research import docker_run_args, load_policy


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


class FrozenResearchBoundaryTests(unittest.TestCase):
    def test_policy_is_fail_closed(self):
        policy = load_policy(ROOT / "runtime/frozen-research-wheelhouse.json")
        self.assertEqual(policy["source_lock"], "requirements.lock")
        self.assertEqual(
            policy["source_lock_sha256"],
            "a4c6fb90909a04eb267057d3e31049c7fc38b12e8a7d556e79c0141aa0d52db6",
        )
        self.assertTrue(policy["base_image"].startswith("python:3.11.15-slim-bookworm@sha256:"))
        self.assertEqual(policy["runtime_boundary"]["network"], "none")
        self.assertTrue(policy["runtime_boundary"]["read_only_root"])
        self.assertTrue(policy["runtime_boundary"]["drop_all_capabilities"])
        self.assertTrue(policy["runtime_boundary"]["no_new_privileges"])
        self.assertTrue(policy["download_policy"]["only_binary"])
        self.assertTrue(policy["download_policy"]["no_source_builds"])

    def test_runtime_command_has_no_network_and_no_privilege(self):
        with tempfile.TemporaryDirectory() as td:
            args = docker_run_args(
                "frozen:test",
                Path(td),
                "score-v3-shadow",
                "123",
                "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/123",
            )
        joined = " ".join(args)
        self.assertIn("--network none", joined)
        self.assertIn("--read-only", args)
        self.assertIn("--cap-drop ALL", joined)
        self.assertIn("--security-opt no-new-privileges", joined)
        self.assertNotIn("/var/run/docker.sock", joined)

    def test_dockerfile_uses_pinned_image_and_offline_install(self):
        dockerfile = (ROOT / "runtime/research-worker.Dockerfile").read_text(encoding="utf-8")
        self.assertIn("python:3.11.15-slim-bookworm@sha256:", dockerfile)
        self.assertIn("--no-index", dockerfile)
        self.assertIn("--only-binary=:all:", dockerfile)
        self.assertNotIn("apt-get", dockerfile)
        self.assertNotIn("curl ", dockerfile)
        self.assertIn("USER 65532:65532", dockerfile)

    def test_prospective_workflows_never_install_frozen_lock_on_host(self):
        for name in ("score-v3-shadow.yml", "score-v2-predictive.yml"):
            workflow = (WORKFLOWS / name).read_text(encoding="utf-8")
            with self.subTest(workflow=name):
                self.assertIn("python -m scripts.run_frozen_research", workflow)
                self.assertIn(
                    "python -m pip install -r runtime/requirements-2026-10-05.lock",
                    workflow,
                )
                self.assertNotIn("python -m pip install -r requirements.lock", workflow)
                self.assertIn("Retain frozen research wheel hashes", workflow)

    def test_worker_uses_filesystem_only_engine_lock_verification(self):
        worker = (ROOT / "scripts/run_frozen_research.py").read_text(encoding="utf-8")
        self.assertIn(
            '"scripts.verify_score_v3_engine_lock","--filesystem-only","--json"',
            worker,
        )
        self.assertIn(
            '"scripts.verify_score_v2_predictive_engine_lock","--filesystem-only","--json"',
            worker,
        )
        dockerfile = (ROOT / "runtime/research-worker.Dockerfile").read_text(encoding="utf-8")
        self.assertNotIn("apt-get", dockerfile)
        self.assertNotIn(" git ", dockerfile)

    def test_output_tree_is_precreated_for_host_cleanup(self):
        worker = (ROOT / "scripts/run_frozen_research.py").read_text(encoding="utf-8")
        for relative in (
            'Path("reports")',
            'Path("research/prospective")',
            'Path("research/prospective/checkpoints")',
            'Path("research/predictive")',
            'Path("research/predictive/checkpoints")',
        ):
            self.assertIn(relative, worker)
        self.assertIn("directory.chmod(stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)", worker)

    def test_security_workflow_keeps_residual_risk_visible(self):
        workflow = (WORKFLOWS / "python-security.yml").read_text(encoding="utf-8")
        self.assertIn(
            "pip-audit --requirement runtime/requirements-2026-10-05.lock",
            workflow,
        )
        self.assertIn("frozen-research-risk:", workflow)
        self.assertIn("--requirement requirements.lock", workflow)
        self.assertIn("PYSEC-2026-4175", workflow)
        self.assertIn("PYSEC-2026-4176", workflow)
        self.assertIn("PYSEC-2026-4177", workflow)
        self.assertIn("2026-11-05", workflow)
        self.assertIn("found != expected", workflow)
        self.assertIn("No other frozen dependency findings were accepted.", workflow)
        self.assertIn("frozen-research-audit.json", workflow)
        self.assertNotIn("continue-on-error: true", workflow)


if __name__ == "__main__":
    unittest.main()
