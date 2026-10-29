"""Static, synthetic-only gates for eight-driver no-added-license source study.

Never fetch any real market observations, import the live score module, or
enable a rights decision based on a research candidate's availability.
"""

from __future__ import annotations

import ast
import json
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "governance/score-zero-license-phase-a-feasibility-2026-10-29.json"
SOURCE = ROOT / "usd_impact_score_v2.py"
RIGHTS = ROOT / "governance/score-publication-rights-gate.json"
PRIVATE = ROOT / "governance/score-private-research-migration-contract.json"

EXPECTED_TICKERS = {
    "DXY": "DX-Y.NYB",
    "WTI": "CL=F",
    "SPX": "^GSPC",
    "VIX": "^VIX",
    "BTC": "BTC-USD",
    "GOLD": "GC=F",
    "UST_2Y": "DGS2",
    "UST_10Y": "DGS10",
}
EXPECTED_WEIGHTS = {
    "DXY": 0.125,
    "WTI": -0.125,
    "SPX": -0.125,
    "VIX": 0.125,
    "BTC": -0.125,
    "GOLD": -0.125,
    "UST_2Y": 0.125,
    "UST_10Y": 0.125,
}


def frozen_literal(name: str) -> object:
    """Read a source-code constant via AST, not by importing any live module."""
    module = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    assignments = [
        statement.value
        for statement in module.body
        if isinstance(statement, ast.Assign)
        for target in statement.targets
        if isinstance(target, ast.Name) and target.id == name
    ]
    if len(assignments) != 1:
        raise AssertionError(f"Expected one frozen assignment: {name}")
    return ast.literal_eval(assignments[0])


class SourceFeasibilityStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_frozen_eight_driver_contract_matches_actual_code(self) -> None:
        m = self.manifest
        source_tickers = frozen_literal("TICKERS")
        actual_weights = frozen_literal("WEIGHTS")
        self.assertEqual(set(source_tickers), set(EXPECTED_TICKERS))
        self.assertEqual(set(actual_weights), set(EXPECTED_WEIGHTS))
        self.assertEqual(
            {k: v[1] for k, v in source_tickers.items()}, EXPECTED_TICKERS
        )
        self.assertEqual(actual_weights, EXPECTED_WEIGHTS)
        by_name = {d["driver"]: d for d in m["drivers"]}
        self.assertEqual(set(by_name), set(EXPECTED_TICKERS))
        self.assertEqual(len(m["drivers"]), 8)
        self.assertEqual(m["original_model"]["drivers"], 8)
        self.assertEqual(m["original_model"]["weights_magnitude"], 0.125)
        self.assertEqual(
            {k: d["legacy_weight"] for k, d in by_name.items()},
            EXPECTED_WEIGHTS,
        )
        self.assertEqual(
            {k: d["legacy_series"] for k, d in by_name.items()},
            EXPECTED_TICKERS,
        )

    def test_no_market_retrieval_rights_or_public_output_are_approved(self) -> None:
        m = self.manifest
        self.assertEqual(m["state"], "RESEARCH_ONLY_HOLD")
        self.assertFalse(m["decision"]["exact_zero_license_eight_driver_equivalent_feasible"])
        self.assertFalse(m["decision"]["identified_complete_eight_driver_license_safe_pipeline"])
        for name, granted in m["authorizations"].items():
            with self.subTest(authorization=name):
                self.assertIs(granted, False)
        policy = json.loads(RIGHTS.read_text(encoding="utf-8"))
        private = json.loads(PRIVATE.read_text(encoding="utf-8"))
        self.assertEqual(policy["state"], "hold")
        self.assertIsNone(policy["decision_receipt"])
        self.assertIsNone(policy["approved_by"])
        self.assertTrue(private["development_synthetic_rehearsal_authorized"])
        self.assertFalse(private["real_provider_evidence_authorized"])
        self.assertFalse(private["public_replacement_authorized"])
        self.assertFalse(private["production_change_authorized"])

    def test_cannot_infer_licenses_or_exact_parity_from_candidate_urls(self) -> None:
        m = self.manifest
        found = set()
        for driver in m["drivers"]:
            self.assertFalse(driver["original_score_licensing_approved"])
            self.assertFalse(driver["source_switch_approved"])
            self.assertTrue(driver["candidates"])
            for item in driver["candidates"]:
                with self.subTest(driver=driver["driver"], candidate=item["id"]):
                    self.assertNotIn(item["id"], found)
                    found.add(item["id"])
                    self.assertIn(item["research_gate"], m["candidate_classifications"])
                    self.assertTrue(item["primary_url"].startswith("https://"))
                    self.assertTrue(item["commercial_rights_evidence"])
                    self.assertTrue(item["relation_to_original"])
                    self.assertIs(item["source_rights_granted"], False)
                    self.assertIs(item["full_series_parity_verified"], False)
                    self.assertIs(item["public_derived_output_granted"], False)
                    self.assertIs(item["real_source_retrieval_authorized"], False)
        self.assertEqual(len(found), 15)

    def test_exclude_deceptively_free_or_embedded_proprietary_market_prices(self) -> None:
        candidates = {
            c["id"]: c
            for driver in self.manifest["drivers"]
            for c in driver["candidates"]
        }
        for name in ("coingecko_demo", "coinmetrics_community"):
            self.assertEqual(candidates[name]["research_gate"], "EXCLUDE_FREE_COMMERCIAL")
        self.assertEqual(
            candidates["eia_cushing_wti_spot"]["research_gate"],
            "BLOCKED_THIRD_PARTY_RIGHTS",
        )
        self.assertIn(
            "Refinitiv",
            candidates["eia_cushing_wti_spot"]["commercial_rights_evidence"],
        )
        self.assertEqual(
            candidates["ofr_financial_stress_index"]["research_gate"],
            "BLOCKED_EMBEDDED_PROPRIETARY_INPUTS",
        )
        self.assertEqual(
            candidates["world_bank_pinksheet_gold"]["research_gate"],
            "BLOCKED_SOURCE_SPECIFIC_RIGHTS_AND_CADENCE",
        )

    def test_four_signal_alternative_is_not_eight_driver_score(self) -> None:
        alternate = self.manifest["alternative_design"]
        self.assertEqual(alternate["status"], "SYNTHETIC_DESIGN_ONLY")
        self.assertEqual(len(alternate["candidate_signals"]), 4)
        self.assertTrue(alternate["signals_not_equal_legacy_eight"])
        for key in (
            "approved_methodology",
            "weights_assigned",
            "point_in_time_coverage_verified",
            "source_licenses_cleared",
            "production_candidate",
            "public_name_approved",
        ):
            with self.subTest(field=key):
                self.assertIs(alternate[key], False)
        self.assertNotEqual(alternate["name"], self.manifest["original_model"]["name"])

    def test_official_source_release_lags_break_same_friday_completeness(self) -> None:
        # Fabricated calendar: Friday June 5, 2099. No market prices, requests,
        # historical provider observations or credential-bearing URLs.
        fri = date(2099, 6, 5)
        self.assertEqual(fri.weekday(), 4)
        monday = fri + timedelta(days=3)
        wednesday = fri + timedelta(days=5)
        self.assertEqual(monday.weekday(), 0)
        self.assertEqual(wednesday.weekday(), 2)
        self.assertGreater(monday, fri)
        self.assertGreater(wednesday, fri)
        rules = self.manifest["release_lag_constraints"]
        self.assertIn("previous business week", rules["fed_h10_rule"])
        self.assertIn("following Wednesday", rules["eia_wpsr_rule"])
        self.assertTrue(rules["no_future_data_approval"])
        self.assertFalse(rules["first_seen_timestamps_verified"])
        self.assertFalse(rules["holiday_calendar_verified"])
        self.assertIn("first_publication_at <= as_of_at", rules["rule"])

    def test_official_source_links_cannot_implicitly_grant_license(self) -> None:
        entries = self.manifest["primary_sources"]
        urls = [entry["url"] for entry in entries]
        self.assertEqual(len(urls), len(set(urls)))
        for entry in entries:
            self.assertTrue(entry["url"].startswith("https://"))
            self.assertTrue(entry["topic"])
        self.assertTrue(self.manifest["explicit_no_go"])
        self.assertTrue(self.manifest["next_phase_authorization_required"])


if __name__ == "__main__":
    unittest.main()
