from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "branded-domain-readiness.yml"


class BrandedDomainReadinessWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_workflow_is_manual_only(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertNotIn("\n  push:", self.text)
        self.assertNotIn("\n  schedule:", self.text)

    def test_origins_are_exact_and_bounded(self):
        self.assertIn("https://score.usd-impact.com", self.text)
        self.assertIn("https://usd-impact-pipeline.pages.dev", self.text)
        self.assertIn('Refusing to verify an unapproved origin', self.text)

    def test_required_public_paths_are_verified(self):
        required_paths = [
            "/en/",
            "/archive/en/",
            "/data/research/score_v2_vintage_comparison_latest.html",
            "/data/research/score_v2_vintage_comparison_latest.json",
            "/data/research/score_v2_vintage_comparison_latest.csv",
            "/data/score_v2_data_semantics.json",
            "/data/weekly_input_latest.json",
        ]
        for path in required_paths:
            with self.subTest(path=path):
                self.assertIn(path, self.text)

    def test_cutover_requires_equivalent_content(self):
        self.assertIn("sha256sum", self.text)
        self.assertIn("Content mismatch", self.text)
        self.assertIn("redirected to pages.dev", self.text)

    def test_security_posture_is_checked(self):
        required_fragments = [
            "x-content-type-options: nosniff",
            "referrer-policy: strict-origin-when-cross-origin",
            "permissions-policy: camera=(), microphone=(), geolocation=()",
            "x-permitted-cross-domain-policies: none",
            "default-src 'none'",
            "script-src-attr 'none'",
            "frame-ancestors https://www.usd-impact.com https://usd-impact.com",
        ]
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.text)

    def test_workflow_declares_read_only_permissions(self):
        self.assertIn("permissions:\n  contents: read", self.text)
        self.assertIn("network reads only", self.text)
        self.assertIn("does not modify DNS", self.text)


if __name__ == "__main__":
    unittest.main()
