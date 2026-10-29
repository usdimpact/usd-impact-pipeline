"""Independent four-series / three-dial context panel, synthetic 2099 only.

No historical observations, external connections, live source releases,
real provider values, source switching, or any public Score artifacts.
"""
from __future__ import annotations

import ast
import json
import unittest
from dataclasses import asdict, replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.independent_macro_context_synthetic import (
    DIALS, PANEL_ID, SOURCE_UNITS,
    SyntheticContextPanel, SyntheticObservation, evaluate_synthetic_context,
)
from scripts.score_public_source_phase_b_synthetic import (
    REQUIRED_IDS, SYNTHETIC_MARKER, SyntheticReceipt,
)

ROOT = Path(__file__).resolve().parents[1]
ET = ZoneInfo("America/New_York")
PREV = date(2099, 6, 5)
WEEK = date(2099, 6, 12)


def stamp(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2099, 6, day, hour, minute, tzinfo=ET)


def receipts_for(week: date) -> list[SyntheticReceipt]:
    previous = week == PREV
    day_h10 = 8 if previous else 15
    day_eia = 10 if previous else 17
    day_treasury = 5 if previous else 12
    versions = [
        ("fed_h10_nominal_broad", stamp(day_h10, 16, 15), f"SYNTHETIC:H10-{week}"),
        ("eia_crude_stocks_weekly", stamp(day_eia, 10, 30), f"SYNTHETIC:EIA-{week}"),
        ("treasury_direct_2yr_par", stamp(day_treasury, 18), f"SYNTHETIC:CURVE-{week}"),
        ("treasury_direct_10yr_par", stamp(day_treasury, 18), f"SYNTHETIC:CURVE-{week}"),
    ]
    return [
        SyntheticReceipt(
            source_id=source_id,
            reference_week=week,
            initial_release_at=released,
            version_published_at=released,
            first_seen_at=released + timedelta(minutes=1),
            revision=0,
            snapshot_id=snapshot,
            record_id=f"SYNTHETIC:{source_id}-{week}-R0",
            fixture_marker=SYNTHETIC_MARKER,
        )
        for source_id, released, snapshot in versions
    ]


def fixture() -> tuple[list[SyntheticReceipt], list[SyntheticObservation]]:
    receipts = receipts_for(PREV) + receipts_for(WEEK)
    prev = {
        "fed_h10_nominal_broad": 100.0, "eia_crude_stocks_weekly": 500000.0,
        "treasury_direct_2yr_par": 4.00, "treasury_direct_10yr_par": 4.40,
    }
    curr = {
        "fed_h10_nominal_broad": 101.0, "eia_crude_stocks_weekly": 498000.0,
        "treasury_direct_2yr_par": 4.10, "treasury_direct_10yr_par": 4.30,
    }
    values = prev | {}
    observations = [
        SyntheticObservation(r.source_id, r.reference_week, r.snapshot_id,
                             (prev if r.reference_week == PREV else curr)[r.source_id])
        for r in receipts
    ]
    return receipts, observations


class IndependentMacroContextSyntheticTests(unittest.TestCase):
    def test_complete_four_series_three_dials_no_score(self) -> None:
        receipts, observations = fixture()
        panel = evaluate_synthetic_context(receipts, observations, WEEK, stamp(17, 10, 32))
        self.assertEqual(panel.status, "SYNTHETIC_ONLY_COMPLETE")
        self.assertEqual(panel.panel_id, PANEL_ID)
        self.assertEqual(dict(panel.dial_labels), {
            "dollar_breadth": "UP",
            "crude_inventory": "DRAW",
            "treasury_curve_level": "POSITIVE",
            "treasury_curve_direction": "FLATTENING",
        })
        self.assertFalse(panel.publish_authorized)
        self.assertFalse(panel.real_data_fetch_authorized)
        self.assertFalse(panel.rights_cleared)
        self.assertFalse(panel.production_authorized)
        self.assertFalse(panel.blockers)

    def test_no_source_numbers_in_preview_result(self) -> None:
        r, o = fixture()
        output = json.dumps(asdict(evaluate_synthetic_context(r, o, WEEK, stamp(17, 10, 32))))
        for item in ("498000.0", "500000.0", "101.0", "4.30", "4.40",
                     "source_provenance", "Yahoo", "S&P 500",
                     "usd_impact_score_v2.json", "weights", "market_price"):
            self.assertNotIn(item, output)
        self.assertIn(SYNTHETIC_MARKER, output)
        self.assertNotIn('"score":', output)

    def test_not_complete_before_wednesday_first_seen(self) -> None:
        r, o = fixture()
        t = stamp(17, 10, 30)
        result = evaluate_synthetic_context(r, o, WEEK, t)
        self.assertEqual(result.status, "SYNTHETIC_ONLY_HOLD")
        self.assertIn("NOT_FIRST_SEEN_BY_CUTOFF", " ".join(result.blockers))
        self.assertEqual(result.dial_labels, ())

    def test_friday_after_treasury_does_not_have_weekly_context(self) -> None:
        r, o = fixture()
        result = evaluate_synthetic_context(r, o, WEEK, stamp(12, 18, 2))
        self.assertEqual(result.status, "SYNTHETIC_ONLY_HOLD")
        self.assertFalse(result.dial_labels)

    def test_holiday_style_EIA_delay_blocks_scheduled_wednesday(self) -> None:
        r, o = fixture()
        idx = next(i for i, x in enumerate(r)
                   if x.reference_week == WEEK and x.source_id == "eia_crude_stocks_weekly")
        original = r[idx]
        delayed = stamp(18, 12, 0)
        r[idx] = replace(original, initial_release_at=delayed,
                         version_published_at=delayed, first_seen_at=delayed + timedelta(minutes=1))
        self.assertEqual(
            evaluate_synthetic_context(r, o, WEEK, stamp(17, 11, 0)).status,
            "SYNTHETIC_ONLY_HOLD",
        )
        self.assertEqual(
            evaluate_synthetic_context(r, o, WEEK, stamp(18, 12, 2)).status,
            "SYNTHETIC_ONLY_COMPLETE",
        )

    def test_missing_one_source_receipt_blocks(self) -> None:
        r, o = fixture()
        r = [x for x in r if not (x.reference_week == WEEK and
                                  x.source_id == "fed_h10_nominal_broad")]
        result = evaluate_synthetic_context(r, o, WEEK, stamp(17, 11))
        self.assertEqual(result.status, "SYNTHETIC_ONLY_HOLD")
        self.assertIn("MISSING_SYNTHETIC_RECEIPT", " ".join(result.blockers))

    def test_missing_prior_week_source_blocks(self) -> None:
        r, o = fixture()
        r = [x for x in r if not (x.reference_week == PREV and
                                  x.source_id == "eia_crude_stocks_weekly")]
        self.assertEqual(
            evaluate_synthetic_context(r, o, WEEK, stamp(17, 11)).status,
            "SYNTHETIC_ONLY_HOLD",
        )

    def test_missing_observation_of_chosen_revision_blocks(self) -> None:
        r, o = fixture()
        o = o[:-1]
        result = evaluate_synthetic_context(r, o, WEEK, stamp(17, 11))
        self.assertEqual(result.status, "SYNTHETIC_ONLY_HOLD")
        self.assertIn("NO_MATCHING_VISIBLE_SYNTHETIC_VALUE", " ".join(result.blockers))

    def test_value_from_wrong_snapshot_cannot_pass(self) -> None:
        r, o = fixture()
        o[-1] = replace(o[-1], snapshot_id="SYNTHETIC:OTHER-CURVE")
        result = evaluate_synthetic_context(r, o, WEEK, stamp(17, 11))
        self.assertEqual(result.status, "SYNTHETIC_ONLY_HOLD")
        self.assertIn("NO_MATCHING_VISIBLE_SYNTHETIC_VALUE", " ".join(result.blockers))

    def test_treasury_tenors_must_share_current_curve_snapshot(self) -> None:
        r, o = fixture()
        idx = next(i for i, x in enumerate(r)
                   if x.reference_week == WEEK and
                   x.source_id == "treasury_direct_10yr_par")
        r[idx] = replace(r[idx], snapshot_id="SYNTHETIC:CURVE-OTHER")
        result = evaluate_synthetic_context(r, o, WEEK, stamp(17, 11))
        self.assertIn("TREASURY_CURVE_SNAPSHOT_MISMATCH", " ".join(result.blockers))
        self.assertFalse(result.dial_labels)

    def test_both_reference_fridays_require_coherent_treasury_receipt_times(self) -> None:
        # The qualitative panel must suppress ALL labels if either Friday's
        # nominal Treasury curve falsely claims one snapshot with two receipt
        # timelines.  This uses fictitious 2099 receipts and observations.
        for changed_week in (PREV, WEEK):
            for field, seconds, expected in (
                ("initial_release_at", -30, "TREASURY_CURVE_INITIAL_RELEASE_MISMATCH"),
                ("version_published_at", 30, "TREASURY_CURVE_VERSION_PUBLICATION_MISMATCH"),
                ("first_seen_at", 30, "TREASURY_CURVE_FIRST_SEEN_MISMATCH"),
            ):
                with self.subTest(week=changed_week, field=field):
                    receipts, observations = fixture()
                    idx = next(
                        idx for idx, rec in enumerate(receipts)
                        if rec.reference_week == changed_week
                        and rec.source_id == "treasury_direct_10yr_par"
                    )
                    ten = receipts[idx]
                    receipts[idx] = replace(
                        ten, **{field: getattr(ten, field) + timedelta(seconds=seconds)}
                    )
                    result = evaluate_synthetic_context(
                        receipts, observations, WEEK, stamp(17, 11, 0)
                    )
                    self.assertEqual(result.status, "SYNTHETIC_ONLY_HOLD")
                    self.assertEqual(result.dial_labels, ())
                    self.assertIn(
                        f"{changed_week}:{expected}", result.blockers
                    )
                    self.assertFalse(result.publish_authorized)

    def test_future_H10_correction_does_not_leak_to_old_cutoff(self) -> None:
        r, o = fixture()
        original = next(x for x in r if
                        x.reference_week == WEEK and x.source_id == "fed_h10_nominal_broad")
        published = stamp(18, 12)
        r.append(replace(
            original, revision=1, version_published_at=published,
            first_seen_at=published + timedelta(minutes=1),
            snapshot_id="SYNTHETIC:H10-2099-06-12-REVISION",
            record_id="SYNTHETIC:H10-2099-06-12-R1",
        ))
        o.append(SyntheticObservation(
            "fed_h10_nominal_broad", WEEK,
            "SYNTHETIC:H10-2099-06-12-REVISION", 99.0,
        ))
        original_panel = evaluate_synthetic_context(r, o, WEEK, stamp(18, 11, 59))
        revised_panel = evaluate_synthetic_context(r, o, WEEK, stamp(18, 12, 2))
        self.assertEqual(dict(original_panel.dial_labels)["dollar_breadth"], "UP")
        self.assertEqual(dict(revised_panel.dial_labels)["dollar_breadth"], "DOWN")

    def test_unchanged_dials_and_inverted_curve(self) -> None:
        r, o = fixture()
        o = [
            replace(x, value=100.0) if x.source_id == "fed_h10_nominal_broad"
            else replace(x, value=500000.0) if x.source_id == "eia_crude_stocks_weekly"
            else replace(x, value=4.8) if x.source_id == "treasury_direct_2yr_par"
            else replace(x, value=4.1) if x.source_id == "treasury_direct_10yr_par"
            else x
            for x in o
        ]
        result = evaluate_synthetic_context(r, o, WEEK, stamp(17, 11))
        labels = dict(result.dial_labels)
        self.assertEqual(labels["dollar_breadth"], "UNCHANGED")
        self.assertEqual(labels["crude_inventory"], "UNCHANGED")
        self.assertEqual(labels["treasury_curve_level"], "INVERTED")
        self.assertEqual(labels["treasury_curve_direction"], "UNCHANGED")

    def test_curve_steepening_in_independent_scenario(self) -> None:
        r, o = fixture()
        o = [
            replace(x, value=4.8) if x.reference_week == WEEK and
            x.source_id == "treasury_direct_10yr_par" else x
            for x in o
        ]
        result = evaluate_synthetic_context(r, o, WEEK, stamp(17, 11))
        self.assertEqual(dict(result.dial_labels)["treasury_curve_direction"], "STEEPENING")

    def test_rejects_real_historical_or_non_friday_dates(self) -> None:
        r, o = fixture()
        for invalid in (date(2026, 10, 30), date(2099, 6, 13),
                        datetime(2099, 6, 12, 0, 0, tzinfo=timezone.utc)):
            with self.subTest(value=invalid):
                with self.assertRaisesRegex(ValueError, "synthetic Friday"):
                    evaluate_synthetic_context(r, o, invalid, stamp(17, 11))

    def test_rejects_current_2099_first_friday_without_2099_prior(self) -> None:
        r, o = fixture()
        with self.assertRaisesRegex(ValueError, "previous week"):
            evaluate_synthetic_context(r, o, date(2099, 1, 2), stamp(17, 11))

    def test_rejects_real_asof_timestamp(self) -> None:
        r, o = fixture()
        with self.assertRaisesRegex(ValueError, "synthetic 2099"):
            evaluate_synthetic_context(r, o, WEEK, datetime(
                2026, 10, 30, tzinfo=timezone.utc,
            ))

    def test_rejects_timezone_naive_cutoff(self) -> None:
        r, o = fixture()
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            evaluate_synthetic_context(r, o, WEEK, datetime(2099, 6, 17, 11))

    def test_rejects_stray_week_receipt(self) -> None:
        r, o = fixture()
        r[0] = replace(r[0], reference_week=date(2099, 5, 29))
        with self.assertRaisesRegex(ValueError, "unexpected week"):
            evaluate_synthetic_context(r, o, WEEK, stamp(17, 11))

    def test_rejects_stray_week_observation(self) -> None:
        r, o = fixture()
        o[0] = replace(o[0], reference_week=date(2099, 5, 29))
        with self.assertRaisesRegex(ValueError, "outside synthetic"):
            evaluate_synthetic_context(r, o, WEEK, stamp(17, 11))

    def test_rejects_non_synthetic_observation_id(self) -> None:
        r, o = fixture()
        o[0] = replace(o[0], snapshot_id="REAL:UNKNOWN")
        with self.assertRaisesRegex(ValueError, "invented synthetic"):
            evaluate_synthetic_context(r, o, WEEK, stamp(17, 11))

    def test_rejects_missing_synthetic_fixture_marker(self) -> None:
        r, o = fixture()
        o[0] = replace(o[0], fixture_marker="")
        with self.assertRaisesRegex(ValueError, "synthetic observation marker"):
            evaluate_synthetic_context(r, o, WEEK, stamp(17, 11))

    def test_rejects_nonfinite_or_bools(self) -> None:
        for invalid in (float("nan"), float("inf"), -float("inf"), True, "100"):
            with self.subTest(value=invalid):
                r, o = fixture()
                o[0] = replace(o[0], value=invalid)
                with self.assertRaisesRegex(ValueError, "numeric|finite"):
                    evaluate_synthetic_context(r, o, WEEK, stamp(17, 11))

    def test_rejects_nonpositive_broad_index_and_stocks(self) -> None:
        for source in ("fed_h10_nominal_broad", "eia_crude_stocks_weekly"):
            with self.subTest(source=source):
                r, o = fixture()
                i = next(i for i, x in enumerate(o) if x.source_id == source)
                o[i] = replace(o[i], value=0)
                with self.assertRaisesRegex(ValueError, "must be positive"):
                    evaluate_synthetic_context(r, o, WEEK, stamp(17, 11))

    def test_rejects_duplicate_observation_and_receipt(self) -> None:
        r, o = fixture()
        with self.assertRaisesRegex(ValueError, "duplicate synthetic observation"):
            evaluate_synthetic_context(r, o + [o[0]], WEEK, stamp(17, 11))
        with self.assertRaisesRegex(ValueError, "duplicate synthetic receipt ID"):
            evaluate_synthetic_context(r + [r[0]], o, WEEK, stamp(17, 11))

    def test_rejects_unknown_source(self) -> None:
        r, o = fixture()
        o[0] = replace(o[0], source_id="S&P_500")
        with self.assertRaisesRegex(ValueError, "unrecognized candidate source"):
            evaluate_synthetic_context(r, o, WEEK, stamp(17, 11))

    def test_no_results_can_claim_rights_or_production(self) -> None:
        kwargs = dict(status="SYNTHETIC_ONLY_COMPLETE", reference_week=str(WEEK),
                      previous_week=str(PREV), panel_id=PANEL_ID, dial_labels=(),
                      blockers=())
        for field in ("rights_cleared", "real_data_fetch_authorized",
                      "publish_authorized", "production_authorized"):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "cannot grant"):
                    SyntheticContextPanel(**kwargs, **{field: True})

    def test_four_input_ids_are_exact_existing_earlier_phase_B_ids(self) -> None:
        self.assertEqual(set(SOURCE_UNITS), set(REQUIRED_IDS))
        self.assertEqual(set(DIALS), {
            "dollar_breadth", "crude_inventory",
            "treasury_curve_level", "treasury_curve_direction",
        })

    def test_new_governance_register_refuses_every_right_and_source_fetch(self) -> None:
        proposal = json.loads(
            (ROOT / "governance/independent-macro-context-fallback-draft-2026-10-30.json")
            .read_text(encoding="utf-8")
        )
        old = json.loads(
            (ROOT / "governance/score-four-source-exact-series-rights-matrix-2026-10-29.json")
            .read_text(encoding="utf-8")
        )
        rights = json.loads(
            (ROOT / "governance/score-publication-rights-gate.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(proposal["status"], "SYNTHETIC_ONLY_DESIGN_HOLD")
        self.assertFalse(proposal["legacy_score_replacement"])
        self.assertFalse(proposal["legacy_score_histories_compatible"])
        self.assertEqual(proposal["source_count"], 4)
        self.assertEqual(set(proposal["source_permissions"]), set(REQUIRED_IDS))
        self.assertEqual(proposal["permission_dimensions"],
                         old["decision_policy"]["permission_dimensions"])
        self.assertEqual(len(proposal["permission_dimensions"]), 14)
        for candidate in proposal["source_permissions"].values():
            self.assertEqual(set(candidate["rights"]),
                             set(proposal["permission_dimensions"]))
            self.assertTrue(all(value is False for value in candidate["rights"].values()))
        self.assertEqual(old["source_count"], 4)
        self.assertEqual(len(old["sources"]), 4)
        self.assertTrue(all(
            all(value is False for value in s["permissions"].values())
            for s in old["sources"]
        ))
        self.assertTrue(all(value is False
                            for value in proposal["external_authorities"].values()))
        self.assertEqual(proposal["publication_control"]["status"], "HOLD")
        self.assertFalse(proposal["publication_control"]["public_release_authorized"])
        self.assertEqual(proposal["cost_policy"]["paid_market_data_budget_usd"], 0)
        self.assertFalse(proposal["methodology"]["no_composite_score"] is False)
        self.assertEqual(rights["state"], "hold")
        self.assertIsNone(rights["decision_receipt"])

    def test_main_source_has_no_provider_network_io_or_v1_engine_import(self) -> None:
        text = (ROOT / "scripts/independent_macro_context_synthetic.py").read_text(
            encoding="utf-8"
        )
        for forbidden in ("import yfinance", "import requests",
                          "import urllib", "import pandas",
                          "import usd_impact_score_v2", "urlopen(",
                          "read_text(", "write_text(", "open("):
            with self.subTest(marker=forbidden):
                self.assertNotIn(forbidden, text)
        self.assertIn("MIN_SYNTHETIC_YEAR", text)

    def test_separate_four_source_model_and_original_legacy_not_spliced(self) -> None:
        f = (ROOT / "governance/independent-macro-context-fallback-draft-2026-10-30.json")
        proposal = json.loads(f.read_text(encoding="utf-8"))
        self.assertFalse(proposal["constraints"]["original_score_617_week_history_may_be_spliced"])
        self.assertFalse(proposal["methodology"]["no_trading_signal_or_investment_recommendation"] is False)
        self.assertFalse(proposal["implementation"]["no_v1_score_import"] is False)
        self.assertFalse(proposal["implementation"]["no_workflow_wiring"] is False)


if __name__ == "__main__":
    unittest.main()
