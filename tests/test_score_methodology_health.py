from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts import check_score_methodology_health as health


ROOT = Path(__file__).resolve().parents[1]


class ScoreMethodologyHealthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads((ROOT / "public/data/score_v2_methodology.json").read_text())
        cls.schema = json.loads((ROOT / "public/data/score_v2_methodology.schema.json").read_text())
        cls.contract_url = "https://usd-impact-pipeline.pages.dev/data/score_v2_methodology.json"
        cls.schema_url = "https://usd-impact-pipeline.pages.dev/data/score_v2_methodology.schema.json"
        cls.html = (
            f'<a href="{cls.contract_url}">Machine-readable methodology JSON</a>'
            f'<a href="{cls.schema_url}">Methodology JSON Schema</a>'
            '<p>5.82 ordinary effective components and 1.89 effective correlated components; '
            'this is an audit/transparency diagnostic, not a risk model.</p>'
        )

    def test_expected_remote_contract_and_site_links_are_healthy(self) -> None:
        checks = health.build_checks(
            local_contract=self.contract,
            local_schema=self.schema,
            remote_contract=copy.deepcopy(self.contract),
            remote_schema=copy.deepcopy(self.schema),
            methodology_html=self.html,
            contract_url=self.contract_url,
            schema_url=self.schema_url,
        )
        self.assertTrue(all(check.passed for check in checks))

    def test_approved_branded_origin_links_are_healthy(self) -> None:
        branded_html = (
            '<a href="https://score.usd-impact.com/data/score_v2_methodology.json">Machine-readable methodology JSON</a>'
            '<a href="https://score.usd-impact.com/data/score_v2_methodology.schema.json">Methodology JSON Schema</a>'
            '<p>5.82 ordinary effective components and 1.89 effective correlated components; '
            'this is an audit/transparency diagnostic, not a risk model.</p>'
        )
        checks = health.build_checks(
            local_contract=self.contract,
            local_schema=self.schema,
            remote_contract=copy.deepcopy(self.contract),
            remote_schema=copy.deepcopy(self.schema),
            methodology_html=branded_html,
            contract_url=self.contract_url,
            schema_url=self.schema_url,
        )
        self.assertTrue(all(check.passed for check in checks))

    def test_unapproved_mirror_does_not_satisfy_public_link_check(self) -> None:
        mirror_html = (
            '<a href="https://example.com/data/score_v2_methodology.json">Machine-readable methodology JSON</a>'
            '<a href="https://example.com/data/score_v2_methodology.schema.json">Methodology JSON Schema</a>'
            '<p>5.82 ordinary effective components and 1.89 effective correlated components; '
            'this is an audit/transparency diagnostic, not a risk model.</p>'
        )
        checks = health.build_checks(
            local_contract=self.contract,
            local_schema=self.schema,
            remote_contract=copy.deepcopy(self.contract),
            remote_schema=copy.deepcopy(self.schema),
            methodology_html=mirror_html,
            contract_url=self.contract_url,
            schema_url=self.schema_url,
        )
        self.assertFalse(next(c for c in checks if c.name == "Public methodology page links contract").passed)
        self.assertFalse(next(c for c in checks if c.name == "Public methodology page links schema").passed)

    def test_remote_contract_drift_is_visible_even_when_shape_still_valid(self) -> None:
        remote = copy.deepcopy(self.contract)
        remote["drivers"][0]["weight"] = 0.2
        checks = health.build_checks(
            local_contract=self.contract,
            local_schema=self.schema,
            remote_contract=remote,
            remote_schema=copy.deepcopy(self.schema),
            methodology_html=self.html,
            contract_url=self.contract_url,
            schema_url=self.schema_url,
        )
        equality = next(check for check in checks if check.name == "Remote methodology equals checked-in contract")
        self.assertFalse(equality.passed)

    def test_missing_public_link_fails_health(self) -> None:
        checks = health.build_checks(
            local_contract=self.contract,
            local_schema=self.schema,
            remote_contract=copy.deepcopy(self.contract),
            remote_schema=copy.deepcopy(self.schema),
            methodology_html="<html>methodology</html>",
            contract_url=self.contract_url,
            schema_url=self.schema_url,
        )
        self.assertFalse(next(c for c in checks if c.name == "Public methodology page links contract").passed)
        self.assertFalse(next(c for c in checks if c.name == "Public methodology page links schema").passed)

    def test_driver_shape_is_exact_and_ordered(self) -> None:
        health.validate_contract_shape(self.contract)
        remote = copy.deepcopy(self.contract)
        remote["drivers"] = list(reversed(remote["drivers"]))
        with self.assertRaisesRegex(RuntimeError, "driver order mismatch"):
            health.validate_contract_shape(remote)

    def test_health_workflow_is_monitoring_only(self) -> None:
        workflow = (ROOT / ".github/workflows/methodology-health.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", workflow)
        self.assertIn("issues: write", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("pull-requests: write", workflow)
        self.assertNotIn("git push", workflow)
        self.assertNotIn("gh pr merge", workflow)
        self.assertNotIn("vercel", workflow.lower())
        self.assertIn("usd-impact-pipeline.pages.dev", workflow)
        self.assertIn("www.usd-impact.com/score/methodology/", workflow)


if __name__ == "__main__":
    unittest.main()
