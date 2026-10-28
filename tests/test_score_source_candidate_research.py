from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_source_candidate_research as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreSourceCandidateResearchTests(unittest.TestCase):
    def test_public_research_is_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["public_evidence_only"])
        self.assertEqual(report["candidate_count"], 6)
        self.assertEqual(
            report["drivers"],
            ["DXY", "SPX", "VIX", "WTI", "GOLD", "BTC"],
        )
        self.assertFalse(report["vendor_selected"])
        self.assertFalse(report["real_data_rehearsal_authorized"])
        self.assertFalse(report["provider_purchase_or_contract_authorized"])
        self.assertFalse(report["production_authorized"])

    def test_all_candidates_remain_rights_pending(self) -> None:
        research = json.loads(
            (ROOT / "governance/score-source-candidate-public-research.json")
            .read_text(encoding="utf-8")
        )
        for item in research["candidates"]:
            self.assertEqual(
                item["rights_status"],
                "license_required_or_confirmation_pending",
            )
            self.assertTrue(item["unresolved"])

    def test_no_vendor_selected(self) -> None:
        research = json.loads(
            (ROOT / "governance/score-source-candidate-public-research.json")
            .read_text(encoding="utf-8")
        )
        self.assertTrue(research["recommendation"]["no_vendor_selected"])


if __name__ == "__main__":
    unittest.main()
