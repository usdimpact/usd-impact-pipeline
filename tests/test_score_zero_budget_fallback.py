from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_zero_budget_fallback as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreZeroBudgetFallbackTests(unittest.TestCase):
    def test_matrix_is_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["review_only"])
        self.assertTrue(report["zero_budget"])
        self.assertEqual(report["driver_count"], 8)
        self.assertFalse(report["exact_v2_zero_budget_path_confirmed"])
        self.assertFalse(report["methodology_change_authorized"])
        self.assertFalse(report["real_data_rehearsal_authorized"])
        self.assertFalse(report["production_authorized"])

    def test_free_candidates_are_not_silent_replacements(self) -> None:
        matrix = json.loads(
            (ROOT / "governance/score-zero-budget-fallback-matrix.json")
            .read_text(encoding="utf-8")
        )
        by_driver = {item["driver"]: item for item in matrix["drivers"]}
        self.assertEqual(by_driver["DXY"]["disposition"], "methodology_change_required")
        self.assertEqual(by_driver["WTI"]["disposition"], "methodology_change_required")
        self.assertEqual(
            by_driver["SPX"]["disposition"],
            "rights_unresolved_not_zero_budget_safe",
        )
        self.assertEqual(
            by_driver["VIX"]["disposition"],
            "rights_unresolved_not_zero_budget_safe",
        )

    def test_no_exact_v2_zero_budget_path_claimed(self) -> None:
        matrix = json.loads(
            (ROOT / "governance/score-zero-budget-fallback-matrix.json")
            .read_text(encoding="utf-8")
        )
        self.assertFalse(matrix["conclusion"]["exact_v2_zero_budget_path_confirmed"])


if __name__ == "__main__":
    unittest.main()
