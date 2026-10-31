"""UI-32 adversarial suite: T01-T25. Invented 2099+ inputs, no network."""
from __future__ import annotations

import ast
import unittest
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.ui32_core_impact_synthetic import (
    AREAS, MARKER, PREFIX, Decision, Receipt, SyntheticStop, assert_independent,
    assert_upstream_causality, compare, fingerprint, normalization, policy_parts,
    require_offline, rights_mock, select_asof, surprise, trend,
)

UTC = timezone.utc
CUTOFF = datetime(2099, 9, 20, tzinfo=UTC)
PUBLISHED = datetime(2099, 7, 7, 13, 30, tzinfo=UTC)
FIRST = date(2099, 6, 30)


def fixture(*, series: str = "CPI", measure: str = "CORE", value: float = 3.2,
            period_end: date = FIRST, economy: str = "US", revision: int = 0,
            published: datetime | None = None, initial: datetime | None = None,
            seen: datetime | None = None, previous_digest: str | None = None,
            target_series_id: str | None = None) -> Receipt:
    if published is None:
        month = period_end.month % 12 + 1
        year = period_end.year + (1 if period_end.month == 12 else 0)
        published = datetime(year, month, 7, 13, 30, tzinfo=UTC)
    if initial is None:
        initial = published
    if seen is None:
        seen = published + timedelta(minutes=1)
    tag = f"{economy}:{series}:{measure}:{period_end.isoformat()}"
    return Receipt(
        economy=economy, source_registry_id=PREFIX + economy + ":SOURCE",
        series_id=PREFIX + f"{economy}:{series}:{measure}", indicator_family=series, measure=measure,
        frequency="M", period_start=date(period_end.year, period_end.month, 1), period_end=period_end,
        unit="pct", adjustment="SA", release_id=PREFIX + tag + ":RELEASE",
        revision=revision, initial_release_at=initial,
        version_published_at=published, revision_effective_at=published,
        first_seen_at=seen, ingested_at=seen + timedelta(minutes=1),
        snapshot_id=PREFIX + tag + f":V{revision}",
        content_digest=f"{revision + 1:064x}", previous_digest=previous_digest,
        value=value, target_series_id=target_series_id,
    )


class Ui32AdversarialCases(unittest.TestCase):
    def stop(self, expected: str, fn) -> None:
        with self.assertRaises(SyntheticStop) as ctx:
            fn()
        self.assertEqual(ctx.exception.code, expected)

    def test_T01_release_after_cutoff(self):
        self.assertEqual(select_asof([fixture()], datetime(2099, 7, 6, tzinfo=UTC)).blockers,
                         ("FUTURE_RELEASE",))

    def test_T02_original_visible_not_future_revision(self):
        old = fixture()
        revised = fixture(revision=1, initial=old.initial_release_at,
                          published=datetime(2099, 10, 5, tzinfo=UTC),
                          previous_digest=old.content_digest, value=4.0)
        selected = select_asof([revised, old], CUTOFF)
        self.assertEqual(selected.status, "SYNTHETIC_ONLY_COMPLETE")
        self.assertEqual(selected.selected, (old.snapshot_id,))
        self.assertNotIn(revised.snapshot_id, selected.selected)

    def test_T03_first_seen_after_cutoff(self):
        delayed = fixture(seen=datetime(2099, 10, 5, tzinfo=UTC))
        self.assertEqual(select_asof([delayed], CUTOFF).blockers, ("FUTURE_FIRST_SEEN",))

    def test_T04_local_clock_offset_and_dst_conflict(self):
        local = datetime(2099, 7, 7, 13, 30, tzinfo=ZoneInfo("America/New_York"))
        self.stop("AMBIGUOUS_TIMESTAMP", lambda: replace(fixture(),
                  local_published_at=local, local_zone="America/New_York"))
        self.stop("AMBIGUOUS_TIMESTAMP", lambda: replace(fixture(),
                  local_published_at=datetime(2099, 7, 7, 9, 30), local_zone="America/New_York"))

    def test_T05_colliding_identity_divergent_digest(self):
        row = fixture()
        self.stop("MALFORMED_LINEAGE", lambda: select_asof([row, replace(
            row, content_digest="a" * 64)], CUTOFF))

    def test_T06_mixed_frequencies(self):
        row = fixture()
        self.stop("MIXED_FREQUENCY", lambda: replace(row, frequency="Q"))

    def test_T07_target_cannot_be_consensus(self):
        self.stop("NO_CONSENSUS", lambda: surprise(fixture(), None, CUTOFF))

    def test_T08_cpi_pce_core_headline_distinction(self):
        row = fixture()
        self.stop("MIXED_MEASURES", lambda: compare(row, fixture(series="PCE"), CUTOFF))
        self.stop("MIXED_MEASURES", lambda: compare(row, fixture(measure="HEADLINE"), CUTOFF))

    def test_T09_current_policy_not_future_expectation(self):
        current = fixture(series="POLICY", measure="CURRENT")
        self.assertEqual(policy_parts(current, None, CUTOFF), (3.2, None))

    def test_T10_future_normalizer_training(self):
        future = fixture(period_end=date(2099, 8, 31),
                         published=datetime(2100, 2, 1, tzinfo=UTC))
        self.stop("NORMALIZATION_LEAKAGE", lambda: normalization([
            fixture(), fixture(period_end=date(2099, 7, 31), value=3.4), future], CUTOFF))

    def test_T11_insufficient_three_release_trend(self):
        self.stop("INSUFFICIENT_HISTORY", lambda: trend([
            fixture(), fixture(period_end=date(2099, 7, 31), value=3.4)], CUTOFF))

    def test_T12_rights_unknown_fail_closed(self):
        self.assertEqual(rights_mock("UNKNOWN"), "SOURCE_RIGHTS_UNKNOWN")
        self.assertEqual(rights_mock("VERIFIED"), "RIGHTS_RESTRICTED")
        with self.assertRaises(ValueError):
            rights_mock(requested_enable=True)

    def test_T13_score_v2_input_boundary(self):
        self.stop("SCORE_V2_SOURCE_BOUNDARY", lambda: assert_independent("score_v2_617_week.csv"))

    def test_T14_idempotent_identical_retry(self):
        row = fixture()
        self.assertEqual(select_asof([row, row], CUTOFF).selected, (row.snapshot_id,))

    def test_T15_unit_and_adjustment_mismatch(self):
        row = fixture()
        self.stop("INVALID_UNIT", lambda: compare(row, replace(row, unit="bp"), CUTOFF))
        self.stop("INVALID_UNIT", lambda: compare(row, replace(row, adjustment="NSA"), CUTOFF))

    def test_T16_all_adapter_requests_denied(self):
        self.stop("UNAUTHORIZED_NETWORK", lambda: require_offline("https://example.invalid"))
        self.assertEqual(rights_mock(), "SOURCE_RIGHTS_UNKNOWN")

    def test_T17_missing_intraday_timestamp(self):
        self.stop("AMBIGUOUS_TIMESTAMP", lambda: replace(fixture(), first_seen_at=None))

    def test_T18_sorted_fingerprints_are_deterministic_unsigned(self):
        rows = [fixture(), fixture(period_end=date(2099, 7, 31), value=4.0)]
        a = fingerprint(rows, CUTOFF)
        self.assertEqual(a, fingerprint(list(reversed(rows)), CUTOFF))
        self.assertEqual(a["signature_status"], "UNSIGNED")
        self.assertFalse(a["publish_authorized"])

    def test_T19_no_reverse_causal_rewrite(self):
        self.stop("REVERSE_CAUSALITY", lambda: assert_upstream_causality(
            rewrite_from_asset_outcome=True))
        self.assertIsNone(assert_upstream_causality())

    def test_T20_no_unsupported_origin_or_feature_activation(self):
        self.stop("SCORE_V2_SOURCE_BOUNDARY", lambda: assert_independent(
            "https://live-provider.example/observations"))
        with self.assertRaises(ValueError):
            Decision("SYNTHETIC_ONLY_COMPLETE", (PREFIX + "S",), (), publish_authorized=True)

    def test_T21_noncausal_publication_and_first_seen(self):
        row = fixture()
        self.stop("MALFORMED_LINEAGE", lambda: replace(
            row, version_published_at=row.initial_release_at - timedelta(minutes=1)))
        self.stop("MALFORMED_LINEAGE", lambda: replace(
            row, first_seen_at=row.version_published_at - timedelta(minutes=1)))

    def test_T22_identical_label_different_source_not_collapsed(self):
        a = fixture()
        b = replace(a, source_registry_id=PREFIX + "OTHER:SOURCE",
                    snapshot_id=PREFIX + "OTHER:SNAPSHOT")
        self.assertEqual(len(select_asof([a, b], CUTOFF).selected), 2)

    def test_T23_real_date_marker_and_privilege_guards(self):
        row = fixture()
        self.stop("AMBIGUOUS_TIMESTAMP", lambda: replace(row, period_start=date(2026, 1, 1)))
        self.stop("SCORE_V2_SOURCE_BOUNDARY", lambda: replace(row, series_id="CPI_US"))
        with self.assertRaises(ValueError):
            replace(row, publish_authorized=True)
        with self.assertRaises(ValueError):
            replace(row, fixture_marker="PRODUCTION")
        self.assertTrue(row.synthetic_only)
        self.assertEqual(row.fixture_marker, MARKER)

    def test_T24_invalid_unit_and_period_release_floor(self):
        self.stop("INVALID_UNIT", lambda: replace(fixture(), unit="usd_per_barrel"))
        self.stop("AMBIGUOUS_TIMESTAMP", lambda: fixture(
            period_end=date(2099, 7, 31), published=datetime(2099, 7, 7, tzinfo=UTC)))

    def test_T25_normalization_cannot_backfill(self):
        future = fixture(period_end=date(2099, 8, 31),
                         published=datetime(2099, 9, 7, tzinfo=UTC),
                         seen=datetime(2099, 10, 1, tzinfo=UTC))
        self.stop("NORMALIZATION_LEAKAGE", lambda: normalization([
            fixture(value=2.0), fixture(period_end=date(2099, 7, 31), value=3.0), future], CUTOFF))

    def test_positive_two_source_selection_and_eight_areas(self):
        self.assertEqual(len(AREAS), 8)
        rows = [fixture(economy=e) for e in sorted(AREAS)]
        d = select_asof(rows, CUTOFF)
        self.assertEqual(d.status, "SYNTHETIC_ONLY_COMPLETE")
        self.assertEqual(len(d.selected), 8)
        self.assertFalse(d.rights_cleared)

    def test_positive_comparability_trend_and_zscore(self):
        rows = [fixture(value=2.0), fixture(period_end=date(2099, 7, 31), value=3.0),
                fixture(period_end=date(2099, 8, 31), value=5.0,
                        published=datetime(2099, 9, 7, tzinfo=UTC))]
        self.assertEqual(compare(rows[0], replace(rows[0], economy="EA",
            source_registry_id=PREFIX + "EA:SOURCE", series_id=PREFIX + "EA:CPI:CORE"), CUTOFF), 0.0)
        self.assertEqual(trend(rows, CUTOFF), "ACCELERATING")
        self.assertGreater(normalization(rows, CUTOFF), 0.0)

    def test_reject_invalid_revision_chain_and_unavailable_original(self):
        row = fixture()
        changed = fixture(revision=1, initial=row.initial_release_at,
                          published=datetime(2099, 10, 5, tzinfo=UTC),
                          previous_digest="a" * 64)
        self.stop("MALFORMED_LINEAGE", lambda: select_asof([row, changed], CUTOFF))
        self.stop("UNAVAILABLE_VINTAGE", lambda: select_asof([changed], CUTOFF))

    def test_direct_decision_cannot_forge_complete(self):
        with self.assertRaisesRegex(ValueError, "direct construction"):
            Decision("SYNTHETIC_ONLY_COMPLETE", (PREFIX + "A",), ())

    def test_cross_series_snapshot_id_collision_rejected(self):
        row = fixture()
        second = fixture(economy="EA")
        self.stop("MALFORMED_LINEAGE", lambda: select_asof([
            row, replace(second, snapshot_id=row.snapshot_id)], CUTOFF))

    def test_offline_execution_with_network_primitives_blocked(self):
        from unittest.mock import patch
        import socket
        import urllib.request
        with patch.object(socket, "create_connection", side_effect=AssertionError("NO NETWORK")) as conn, \
             patch.object(urllib.request, "urlopen", side_effect=AssertionError("NO NETWORK")) as url:
            self.assertEqual(select_asof([fixture()], CUTOFF).status, "SYNTHETIC_ONLY_COMPLETE")
            fingerprint([fixture()], CUTOFF)
            conn.assert_not_called()
            url.assert_not_called()

    def test_period_floor_full_month_quarter_and_daily_exception(self):
        early = datetime(2099, 6, 30, 12, tzinfo=UTC)
        row = fixture()
        self.stop("AMBIGUOUS_TIMESTAMP", lambda: replace(
            row, initial_release_at=early, version_published_at=early,
            revision_effective_at=early, first_seen_at=early + timedelta(minutes=1),
            ingested_at=early + timedelta(minutes=2)))
        self.stop("AMBIGUOUS_TIMESTAMP", lambda: replace(
            row, frequency="Q", period_start=date(2099, 4, 1),
            initial_release_at=early, version_published_at=early,
            revision_effective_at=early, first_seen_at=early + timedelta(minutes=1),
            ingested_at=early + timedelta(minutes=2)))
        daily = replace(row, frequency="D", period_start=FIRST,
            initial_release_at=early, version_published_at=early,
            revision_effective_at=early, first_seen_at=early + timedelta(minutes=1),
            ingested_at=early + timedelta(minutes=2))
        self.assertEqual(select_asof([daily], CUTOFF).status, "SYNTHETIC_ONLY_COMPLETE")

    def test_ingestion_after_cutoff_never_appears_as_known(self):
        row = fixture()
        later = replace(row, ingested_at=datetime(2099, 10, 1, tzinfo=UTC))
        self.assertEqual(select_asof([later], CUTOFF).blockers, ("UNAVAILABLE_VINTAGE",))
        self.assertEqual(select_asof([row], CUTOFF).selected, (row.snapshot_id,))
        self.stop("UNAVAILABLE_VINTAGE", lambda: compare(row, later, CUTOFF))

    def test_consensus_binds_exact_inflation_series_and_vintage(self):
        actual = fixture()
        pre_release = datetime(2099, 7, 6, 13, tzinfo=UTC)
        consensus = fixture(series="CONSENSUS", value=2.8, published=pre_release,
                            target_series_id=actual.series_id)
        self.assertAlmostEqual(surprise(actual, consensus, CUTOFF), 0.4)
        self.stop("NO_CONSENSUS", lambda: surprise(actual, replace(
            consensus, target_series_id=PREFIX + "US:PCE:CORE"), CUTOFF))
        self.stop("NO_CONSENSUS", lambda: surprise(actual, replace(
            consensus, first_seen_at=actual.first_seen_at + timedelta(minutes=10),
            ingested_at=actual.first_seen_at + timedelta(minutes=11)), CUTOFF))
        self.stop("NO_CONSENSUS", lambda: surprise(actual, replace(
            consensus, ingested_at=actual.initial_release_at + timedelta(minutes=1)), CUTOFF))
        self.stop("MIXED_MEASURES", lambda: fixture(series="CONSENSUS"))

    def test_expectations_bound_to_current_policy_series(self):
        current = fixture(series="POLICY", measure="CURRENT")
        expected = fixture(series="EXPECTED_PATH", measure="EXPECTED", value=2.7,
                           target_series_id=current.series_id)
        self.assertEqual(policy_parts(current, expected, CUTOFF), (3.2, 2.7))
        self.assertEqual(policy_parts(current, replace(expected,
            target_series_id=PREFIX + "US:OTHER_POLICY:CURRENT"), CUTOFF), (3.2, None))
        self.assertEqual(policy_parts(current, replace(expected, adjustment="NSA"), CUTOFF),
                         (3.2, None))
        self.stop("MIXED_MEASURES", lambda: fixture(series="EXPECTED_PATH"))
        self.stop("UNAVAILABLE_VINTAGE", lambda: policy_parts(fixture(), None, CUTOFF))

    def test_trend_is_directional_not_second_derivative(self):
        rows = [fixture(value=3.0), fixture(period_end=date(2099, 7, 31), value=2.0),
                fixture(period_end=date(2099, 8, 31), value=1.5)]
        self.assertEqual(trend(rows, CUTOFF), "DECELERATING")
        self.assertEqual(trend(rows[:-1] + [replace(rows[-1], value=3.0)], CUTOFF), "MIXED")
        self.assertEqual(trend(rows[:-1] + [replace(rows[-1], value=2.0)], CUTOFF), "MIXED")
        self.assertEqual(trend([replace(r, value=3.0) for r in rows], CUTOFF), "STABLE")

    def test_normalization_is_order_independent_and_rejects_gaps(self):
        rows = [fixture(value=2.0), fixture(period_end=date(2099, 7, 31), value=3.0),
                fixture(period_end=date(2099, 8, 31), value=5.0)]
        self.assertEqual(normalization(rows, CUTOFF), normalization(list(reversed(rows)), CUTOFF))
        self.stop("INSUFFICIENT_HISTORY", lambda: normalization([rows[0], rows[2],
            fixture(period_end=date(2099, 9, 30), value=6.0,
                    published=datetime(2099, 10, 7, tzinfo=UTC))],
            datetime(2099, 10, 10, tzinfo=UTC)))
        self.stop("MIXED_MEASURES", lambda: trend([rows[0], replace(rows[1],
            source_registry_id=PREFIX + "ALT:SOURCE"), rows[2]], CUTOFF))

    def test_static_source_boundary_stdlib_and_no_imports_of_score(self):
        source = Path(__file__).resolve().parents[1] / "scripts" / "ui32_core_impact_synthetic.py"
        code = source.read_text(encoding="utf-8")
        parsed = ast.parse(code)
        imports = set()
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                imports.update(n.name.split(".")[0] for n in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertEqual(imports, {"__future__", "calendar", "hashlib", "json", "math", "re", "dataclasses",
                                   "datetime", "typing", "zoneinfo"})
        self.assertNotIn("socket", code)
        self.assertNotIn("urllib", code)
        self.assertNotIn("requests", code)
        self.assertNotIn("subprocess", code)
        self.assertNotIn("os.environ", code)
        self.assertNotIn("open(", code)
        self.assertNotIn("score_public_source_phase_b_synthetic", code)
        self.assertNotIn("independent_macro_context_synthetic", code)


if __name__ == "__main__":
    unittest.main()
