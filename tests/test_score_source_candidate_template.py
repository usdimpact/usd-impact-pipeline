from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_source_candidate_template as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreSourceCandidateTemplateTests(unittest.TestCase):
    def test_template_is_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["review_only"])
        self.assertEqual(report["candidate_count"], 6)
        self.assertEqual(
            report["drivers"],
            ["DXY", "WTI", "SPX", "VIX", "BTC", "GOLD"],
        )
        self.assertTrue(report["all_rights_pending"])
        self.assertTrue(report["all_parity_not_run"])
        self.assertFalse(report["provider_preselected"])
        self.assertFalse(report["live_fetch_switch_authorized"])
        self.assertFalse(report["production_authorized"])

    def test_schema_cannot_authorize_production(self) -> None:
        schema = json.loads(
            (ROOT / "governance/score-source-candidate-evaluation.schema.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(schema["properties"]["production_authorized"], {"const": False})

    def test_template_does_not_preselect_candidates(self) -> None:
        template = json.loads(
            (ROOT / "governance/score-source-candidate-evaluation.template.json")
            .read_text(encoding="utf-8")
        )
        for item in template["evaluations"]:
            candidate = item["candidate"]
            self.assertTrue(all(value is None for value in candidate.values()))
            self.assertEqual(item["decision"]["status"], "pending")
            self.assertFalse(item["production_authorized"])


if __name__ == "__main__":
    unittest.main()
