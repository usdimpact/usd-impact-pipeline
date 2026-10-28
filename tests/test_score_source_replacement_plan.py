from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_source_replacement_plan as validator

REPO_ROOT = Path(__file__).resolve().parents[1]


class ScoreSourceReplacementPlanTests(unittest.TestCase):
    def test_contract_matches_current_score_semantics(self) -> None:
        report = validator.validate(REPO_ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["review_only"])
        self.assertEqual(report["canonical_driver_count"], 8)
        self.assertEqual(report["yfinance_driver_count"], 6)
        self.assertEqual(report["fred_driver_count"], 2)
        self.assertTrue(report["score_formula_unchanged"])
        self.assertFalse(report["production_change_authorized"])
        self.assertFalse(report["real_provider_data_migration_authorized"])
        self.assertFalse(report["provider_purchase_or_contract_authorized"])
        self.assertFalse(report["live_fetch_switch_authorized"])

    def test_yfinance_sources_are_marked_for_replacement_or_explicit_license(self) -> None:
        contract = json.loads(
            (REPO_ROOT / "governance/score-source-neutral-adapter-contract.json")
            .read_text(encoding="utf-8")
        )
        for driver in ("DXY", "WTI", "SPX", "VIX", "BTC", "GOLD"):
            self.assertEqual(
                contract["current_sources"][driver]["rights_state"],
                "replace_or_explicitly_license",
            )

    def test_migration_cannot_change_methodology_to_fit_vendor(self) -> None:
        contract = json.loads(
            (REPO_ROOT / "governance/score-source-neutral-adapter-contract.json")
            .read_text(encoding="utf-8")
        )
        prohibited = set(contract["prohibited_shortcuts"])
        self.assertIn("change_instrument_or_price_semantics_to_fit_vendor", prohibited)
        self.assertIn("change_score_weights_or_formula_during_source_migration", prohibited)
        self.assertIn("mix_new_and_old_sources_without_explicit_parity_evidence", prohibited)

    def test_production_requires_separate_authorization(self) -> None:
        contract = json.loads(
            (REPO_ROOT / "governance/score-source-neutral-adapter-contract.json")
            .read_text(encoding="utf-8")
        )
        self.assertIn(
            "separate_production_authorization",
            contract["replacement_requirements"]["gates_before_production"],
        )


if __name__ == "__main__":
    unittest.main()
