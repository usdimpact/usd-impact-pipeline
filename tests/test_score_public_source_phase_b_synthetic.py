"""No-network Phase B as-of, revision and source-rights tests.

Only invented dates and identifiers for year 2099+. No financial observations
are present; tests neither call EIA/Federal Reserve/Treasury nor import Score.
"""

from __future__ import annotations

import ast
import json
import unittest
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.score_public_source_phase_b_synthetic import (
    REQUIRED_IDS,
    SYNTHETIC_MARKER,
    SyntheticAsOfDecision,
    SyntheticReceipt,
    evaluate_synthetic_asof,
)

ROOT = Path(__file__).resolve().parents[1]
ET = ZoneInfo("America/New_York")
FRIDAY = date(2099, 6, 5)


def stamp(day: int, hour: int, minute: int, *, month: int = 6) -> datetime:
    """Synthetic 2099 Eastern timestamp; no historic provider observations."""
    return datetime(2099, month, day, hour, minute, tzinfo=ET)


def receipt(
    source_id: str,
    published: datetime,
    *,
    minutes_after: int = 1,
    snapshot: str = "SYNTHETIC:UNSPECIFIED",
    revision: int = 0,
    original_release: datetime | None = None,
) -> SyntheticReceipt:
    return SyntheticReceipt(
        source_id=source_id,
        reference_week=FRIDAY,
        initial_release_at=original_release or published,
        version_published_at=published,
        first_seen_at=published + timedelta(minutes=minutes_after),
        revision=revision,
        snapshot_id=snapshot,
        record_id=f"SYNTHETIC:{source_id}-R{revision}",
        fixture_marker=SYNTHETIC_MARKER,
    )


def four() -> list[SyntheticReceipt]:
    """One invented Friday 2099-06-05 reference week with provider-like lags."""
    return [
        receipt("fed_h10_nominal_broad", stamp(8, 16, 15), snapshot="SYNTHETIC:H10-R0"),
        receipt("eia_crude_stocks_weekly", stamp(10, 10, 30), snapshot="SYNTHETIC:EIA-R0"),
        receipt("treasury_direct_2yr_par", stamp(5, 18, 0), snapshot="SYNTHETIC:CURVE-R0"),
        receipt("treasury_direct_10yr_par", stamp(5, 18, 0), snapshot="SYNTHETIC:CURVE-R0"),
    ]


class SyntheticAsOfAvailabilityTests(unittest.TestCase):
    def test_four_sources_become_temporally_complete_only_after_eia(self) -> None:
        f = four()
        fri_cutoff = datetime(2099, 6, 5, 22, 0, tzinfo=timezone.utc)
        early = evaluate_synthetic_asof(f, FRIDAY, fri_cutoff)
        self.assertEqual(early.status, "SYNTHETIC_ONLY_HOLD")
        self.assertEqual(len(early.blockers), 4)
        self.assertFalse(early.publish_authorized)
        self.assertFalse(early.real_source_retrieval_authorized)

        monday = evaluate_synthetic_asof(f, FRIDAY, stamp(8, 16, 17))
        self.assertEqual(monday.status, "SYNTHETIC_ONLY_HOLD")
        self.assertEqual(len(monday.selected), 3)
        self.assertIn(
            "eia_crude_stocks_weekly:NOT_FIRST_SEEN_BY_CUTOFF",
            monday.blockers,
        )

        wednesday = evaluate_synthetic_asof(f, FRIDAY, stamp(10, 10, 32))
        self.assertEqual(wednesday.status, "SYNTHETIC_ONLY_COMPLETE")
        self.assertEqual(len(wednesday.selected), 4)
        self.assertEqual(wednesday.blockers, ())
        self.assertFalse(wednesday.publish_authorized)

    def test_scheduled_publication_time_is_not_first_seen_evidence(self) -> None:
        f = four()
        at_scheduled = evaluate_synthetic_asof(f, FRIDAY, stamp(8, 16, 15))
        self.assertNotIn(
            "fed_h10_nominal_broad",
            {source for source, _ in at_scheduled.selected},
        )
        at_first_seen = evaluate_synthetic_asof(f, FRIDAY, stamp(8, 16, 16))
        self.assertIn(
            "fed_h10_nominal_broad",
            {source for source, _ in at_first_seen.selected},
        )
        self.assertEqual(at_first_seen.status, "SYNTHETIC_ONLY_HOLD")

    def test_holiday_release_delay_is_not_overridden_by_monday_schedule(self) -> None:
        f = four()
        f[0] = receipt(
            "fed_h10_nominal_broad",
            stamp(9, 16, 15),
            snapshot="SYNTHETIC:H10-TUESDAY-HOLIDAY-R0",
        )
        monday_after_scheduled = evaluate_synthetic_asof(f, FRIDAY, stamp(8, 17, 0))
        self.assertNotIn(
            "fed_h10_nominal_broad",
            {source for source, _ in monday_after_scheduled.selected},
        )
        after_actual_tuesday = evaluate_synthetic_asof(f, FRIDAY, stamp(10, 10, 32))
        self.assertEqual(after_actual_tuesday.status, "SYNTHETIC_ONLY_COMPLETE")

    def test_a_revision_after_cutoff_does_not_rewrite_prior_asof(self) -> None:
        f = four()
        correction = receipt(
            "fed_h10_nominal_broad",
            stamp(11, 12, 0),
            snapshot="SYNTHETIC:H10-R1-CORRECTED",
            revision=1,
            original_release=stamp(8, 16, 15),
        )
        f.append(correction)
        old = evaluate_synthetic_asof(f, FRIDAY, stamp(11, 11, 59))
        self.assertEqual(old.status, "SYNTHETIC_ONLY_COMPLETE")
        self.assertIn(
            ("fed_h10_nominal_broad", "SYNTHETIC:H10-R0"), old.selected
        )
        new = evaluate_synthetic_asof(f, FRIDAY, stamp(11, 12, 2))
        self.assertEqual(new.status, "SYNTHETIC_ONLY_COMPLETE")
        self.assertIn(
            ("fed_h10_nominal_broad", "SYNTHETIC:H10-R1-CORRECTED"), new.selected
        )
        self.assertFalse(old.publish_authorized and new.publish_authorized)

    def test_correction_not_yet_first_seen_cannot_be_used(self) -> None:
        f = four()
        correction = receipt(
            "fed_h10_nominal_broad",
            stamp(11, 12, 0),
            minutes_after=60,
            snapshot="SYNTHETIC:H10-R1-CORRECTED",
            revision=1,
            original_release=stamp(8, 16, 15),
        )
        f.append(correction)
        asof_before_first_seen = evaluate_synthetic_asof(f, FRIDAY, stamp(11, 12, 30))
        self.assertIn(
            ("fed_h10_nominal_broad", "SYNTHETIC:H10-R0"),
            asof_before_first_seen.selected,
        )
        later = evaluate_synthetic_asof(f, FRIDAY, stamp(11, 13, 1))
        self.assertIn(
            ("fed_h10_nominal_broad", "SYNTHETIC:H10-R1-CORRECTED"),
            later.selected,
        )

    def test_treasury_tenors_must_share_one_curve_vintage(self) -> None:
        f = four()
        f[-1] = replace(f[-1], snapshot_id="SYNTHETIC:OTHER_CURVE_SNAPSHOT")
        out = evaluate_synthetic_asof(f, FRIDAY, stamp(11, 9, 0))
        self.assertEqual(out.status, "SYNTHETIC_ONLY_HOLD")
        self.assertIn("TREASURY_CURVE_SNAPSHOT_MISMATCH", out.blockers)

        f = four()
        ten = f[-1]
        f[-1] = replace(ten, revision=1, record_id="SYNTHETIC:UST-10Y-R1")
        out = evaluate_synthetic_asof(f, FRIDAY, stamp(11, 9, 0))
        self.assertIn("TREASURY_CURVE_REVISION_MISMATCH", out.blockers)

    def test_missing_unverified_release_or_first_seen_fails_closed(self) -> None:
        for key in ("initial_release_at", "version_published_at", "first_seen_at"):
            with self.subTest(field=key):
                f = four()
                f[0] = replace(f[0], **{key: None})
                with self.assertRaisesRegex(ValueError, "unverified"):
                    evaluate_synthetic_asof(f, FRIDAY, stamp(11, 9, 0))
        f = four()
        f[0] = replace(f[0], first_seen_at=stamp(8, 16, 14))
        with self.assertRaisesRegex(ValueError, "non-causal"):
            evaluate_synthetic_asof(f, FRIDAY, stamp(11, 9, 0))

    def test_missing_source_and_mismatched_week_are_not_accepted(self) -> None:
        missing = evaluate_synthetic_asof(four()[:-1], FRIDAY, stamp(11, 9, 0))
        self.assertEqual(missing.status, "SYNTHETIC_ONLY_HOLD")
        self.assertIn(
            "treasury_direct_10yr_par:MISSING_SYNTHETIC_RECEIPT",
            missing.blockers,
        )
        f = four()
        f[0] = replace(f[0], reference_week=date(2099, 6, 12))
        with self.assertRaisesRegex(ValueError, "reference week mismatch"):
            evaluate_synthetic_asof(f, FRIDAY, stamp(11, 9, 0))

    def test_duplicate_or_out_of_order_version_is_rejected(self) -> None:
        f = four()
        with self.assertRaisesRegex(ValueError, "duplicate synthetic receipt ID"):
            evaluate_synthetic_asof(f + [f[0]], FRIDAY, stamp(11, 9, 0))
        f = four()
        with self.assertRaisesRegex(ValueError, "duplicate source revision"):
            evaluate_synthetic_asof(
                f + [replace(f[0], record_id="SYNTHETIC:H10_DUPLICATE")],
                FRIDAY,
                stamp(11, 9, 0),
            )
        f = four()
        f.append(
            receipt(
                "fed_h10_nominal_broad",
                stamp(7, 16, 15),
                revision=1,
                original_release=stamp(7, 16, 15),
                snapshot="SYNTHETIC:OUT_OF_ORDER",
            )
        )
        with self.assertRaisesRegex(ValueError, "out-of-order"):
            evaluate_synthetic_asof(f, FRIDAY, stamp(11, 9, 0))

    def test_rejects_real_dates_unknown_source_and_missing_fixture_marker(self) -> None:
        with self.assertRaisesRegex(ValueError, "synthetic reference"):
            evaluate_synthetic_asof(four(), date(2026, 10, 23), stamp(11, 9, 0))
        with self.assertRaisesRegex(ValueError, "synthetic reference"):
            evaluate_synthetic_asof(four(), date(2099, 6, 6), stamp(11, 9, 0))
        with self.assertRaisesRegex(ValueError, "real/historical as-of"):
            evaluate_synthetic_asof(
                four(), FRIDAY, datetime(2026, 10, 29, tzinfo=timezone.utc)
            )
        f = four()
        f[0] = replace(f[0], source_id="faked_provider")
        with self.assertRaisesRegex(ValueError, "unknown"):
            evaluate_synthetic_asof(f, FRIDAY, stamp(11, 9, 0))
        f = four()
        f[0] = replace(f[0], fixture_marker="")
        with self.assertRaisesRegex(ValueError, "synthetic fixture"):
            evaluate_synthetic_asof(f, FRIDAY, stamp(11, 9, 0))
        f = four()
        f[0] = replace(f[0], snapshot_id="ACTUAL:NOT_ALLOWED")
        with self.assertRaisesRegex(ValueError, "synthetic-only"):
            evaluate_synthetic_asof(f, FRIDAY, stamp(11, 9, 0))

    def test_rejects_naive_datetime_and_rejected_rights_flag(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            evaluate_synthetic_asof(four(), FRIDAY, datetime(2099, 6, 11, 14, 0))
        f = four()
        f[0] = replace(f[0], version_published_at=datetime(2099, 6, 8, 16, 15))
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            evaluate_synthetic_asof(f, FRIDAY, stamp(11, 9, 0))
        with self.assertRaisesRegex(ValueError, "cannot grant rights"):
            SyntheticAsOfDecision(
                status="SYNTHETIC_ONLY_COMPLETE",
                selected=(),
                blockers=(),
                publish_authorized=True,
            )

    def test_dst_matters_for_treasury_friday_close(self) -> None:
        # 18:00 Eastern is not always 22:00 UTC:
        # June is daylight saving (UTC-4); January is standard (UTC-5).
        self.assertEqual(stamp(5, 18, 0).astimezone(timezone.utc).hour, 22)
        winter = datetime(2099, 1, 9, 18, 0, tzinfo=ET)
        self.assertEqual(winter.astimezone(timezone.utc).hour, 23)
        self.assertGreater(
            (stamp(5, 18, 1) - stamp(5, 18, 0)).total_seconds(), 0
        )

    def test_manifest_sources_rights_and_parent_phase_a_consistency(self) -> None:
        manifest = json.loads(
            (ROOT / "governance/score-public-source-phase-b-design-2026-10-29.json")
            .read_text(encoding="utf-8")
        )
        phase_a = json.loads(
            (ROOT / "governance/score-zero-license-phase-a-feasibility-2026-10-29.json")
            .read_text(encoding="utf-8")
        )
        rights = json.loads(
            (ROOT / "governance/score-publication-rights-gate.json")
            .read_text(encoding="utf-8")
        )
        private = json.loads(
            (ROOT / "governance/score-private-research-migration-contract.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["status"], "SYNTHETIC_DESIGN_REVIEW_ONLY_HOLD")
        self.assertEqual(set(manifest["synthetic_contract"]["required_source_ids"]), REQUIRED_IDS)
        self.assertEqual(
            [s["id"] for s in manifest["sources"]],
            phase_a["alternative_design"]["candidate_signals"],
        )
        self.assertEqual(len(manifest["sources"]), 4)
        for source in manifest["sources"]:
            self.assertIs(source["cleared"], False)
            self.assertTrue(source["question"])
            self.assertTrue(source["cite"])
            self.assertTrue(all(url.startswith("https://") for url in source["cite"]))
        for name, granted in manifest["decision"].items():
            if name.startswith("approve_"):
                with self.subTest(decision=name):
                    self.assertIs(granted, False)
        self.assertTrue(manifest["synthetic_contract"]["holiday_schedule_is_only_a_projection"])
        self.assertTrue(manifest["synthetic_contract"]["revision_vintage_must_be_selected_asof"])
        self.assertFalse(manifest["synthetic_contract"]["publish_authorized"])
        self.assertFalse(manifest["synthetic_contract"]["external_fetch_allowed"])
        self.assertEqual(rights["state"], "hold")
        self.assertIsNone(rights["decision_receipt"])
        self.assertFalse(private["real_provider_evidence_authorized"])
        self.assertFalse(private["public_replacement_authorized"])
        self.assertFalse(private["production_change_authorized"])

    def test_synthetic_module_has_no_network_or_file_io(self) -> None:
        module = (
            ROOT / "scripts/score_public_source_phase_b_synthetic.py"
        ).read_text(encoding="utf-8")
        parsed = ast.parse(module)
        imports = [
            node.module or ""
            for node in ast.walk(parsed)
            if isinstance(node, ast.ImportFrom)
        ] + [
            alias.name
            for node in ast.walk(parsed)
            if isinstance(node, ast.Import)
            for alias in node.names
        ]
        self.assertFalse(
            any(name.startswith(
                ("requests", "urllib", "http", "socket", "pandas",
                 "yfinance", "fredapi", "subprocess", "pathlib"))
                for name in imports)
        )
        for forbidden in (
            "urlopen(", "open(", "fetch_fred(", "fetch_yahoo(", "httpx",
            "write_text(", "read_csv(", "read_text(", "os.system("
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, module)


if __name__ == "__main__":
    unittest.main()
