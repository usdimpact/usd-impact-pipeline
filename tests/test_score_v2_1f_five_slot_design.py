from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_v2_1f_five_slot_design as validator

ROOT = Path(__file__).resolve().parents[1]


class ScoreV21FFiveSlotDesignTests(unittest.TestCase):
    def test_design_is_fail_closed(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "design_only")
        self.assertEqual(report["slot_count"], 5)
        self.assertTrue(report["h15_slots_removed"])
        self.assertAlmostEqual(report["absolute_weights_sum"], 1.0)
        self.assertFalse(report["result_driven_tuning"])
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_exact_five_slot_inventory_and_weights(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1f-five-slot-design.json").read_text(encoding="utf-8")
        )
        actual = {
            row["slot"]: (row["exact_series_id"], row["transform"], row["weight"])
            for row in design["proposed_slots"]
        }
        self.assertEqual(
            actual,
            {
                "USD": ("H10/H10/JRXWTFB_N.B", "level", 0.2),
                "ENERGY": ("WPU0561", "natural_log_level", -0.2),
                "FIN_CONDITIONS": (
                    "H8/H8/B1001NCBA",
                    "negative_log_change_13_weeks",
                    0.2,
                ),
                "FIN_STRESS": ("H41/H41/RESPPALDP_N.WW", "log1p_level", 0.2),
                "LIQUIDITY": ("H41/H41/RESPPA_N.WW", "log_change_13_weeks", -0.2),
            },
        )

    def test_h15_is_removed_not_proxied(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1f-five-slot-design.json").read_text(encoding="utf-8")
        )
        active = json.dumps(design["proposed_slots"]).lower()
        self.assertNotIn("h15/", active)
        self.assertNotIn("riflgfcy", active)
        self.assertFalse(design["design_principle"]["silent_proxy_substitution"])
        self.assertEqual(len(design["removed_v2_1e_slots"]), 3)

    def test_v21e_authorization_is_not_inherited(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1f-five-slot-design.json").read_text(encoding="utf-8")
        )
        self.assertFalse(design["predecessor"]["authorization_inherited"])
        self.assertFalse(
            (ROOT / "governance/score-v2-1e-real-data-research-authorization.json").exists()
        )

    def test_bls_live_vintage_feasibility_remains_pending(self) -> None:
        design = json.loads(
            (ROOT / "governance/score-v2-1f-five-slot-design.json").read_text(encoding="utf-8")
        )
        energy = next(row for row in design["proposed_slots"] if row["slot"] == "ENERGY")
        self.assertEqual(
            energy["live_archive_feasibility"],
            "pending_separate_authorized_preflight",
        )
        self.assertIn("four months", energy["revision_rule"].lower())
        self.assertIn(
            "current revised history is not an allowed historical-vintage substitute",
            energy["historical_vintage_rule"].lower(),
        )


if __name__ == "__main__":
    unittest.main()
