from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_score_public_safe_research as safe


REPO_ROOT = Path(__file__).resolve().parents[1]
PIT_PATH = REPO_ROOT / "public/data/research/score_v2_point_in_time_latest.json"
ROBUSTNESS_PATH = REPO_ROOT / "public/data/research/score_v2_robustness_latest.json"
VINTAGE_PATH = REPO_ROOT / "public/data/research/score_v2_vintage_comparison_latest.json"

FORBIDDEN_RAW_TERMS = (
    '"source_provenance"',
    '"provider_code"',
    '"source_url"',
    '"omitted_driver"',
    '"flipped_driver"',
    '"dominant_driver"',
    '"component_zscore_revisions"',
    '"component_zscore_revision_summary"',
    '"largest_absolute_component_revision"',
    '"archive_path"',
    "Yahoo Finance",
    "DX-Y.NYB",
    "^GSPC",
    "^VIX",
    "CL=F",
    "GC=F",
    "BTC-USD",
)


class PublicSafeResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pit_source = json.loads(PIT_PATH.read_text(encoding="utf-8"))
        cls.robustness_source = json.loads(ROBUSTNESS_PATH.read_text(encoding="utf-8"))
        cls.vintage_source = json.loads(VINTAGE_PATH.read_text(encoding="utf-8"))

    def _assert_raw_safe(self, payload: dict) -> None:
        safe.assert_aggregate_safe(payload)
        raw = json.dumps(payload, sort_keys=True)
        for term in FORBIDDEN_RAW_TERMS:
            self.assertNotIn(term, raw)

    def test_point_in_time_preserves_aggregate_study_without_provenance(self) -> None:
        payload = safe.build_point_in_time(self.pit_source)
        self._assert_raw_safe(payload)

        self.assertEqual(payload["schema_version"], safe.PIT_SCHEMA_VERSION)
        self.assertEqual(len(payload["weeks"]), len(self.pit_source["weeks"]))
        self.assertEqual(payload["summary"], self.pit_source["summary"])
        self.assertNotIn("source_provenance", payload)
        self.assertNotIn("drivers", payload)

    def test_robustness_keeps_only_aggregate_diagnostics(self) -> None:
        payload = safe.build_robustness(self.robustness_source)
        self._assert_raw_safe(payload)

        self.assertEqual(payload["schema_version"], safe.ROBUSTNESS_SCHEMA_VERSION)
        for removed in (
            "leave_one_driver_out",
            "sign_sensitivity",
            "correlation_concentration",
            "rolling_component_correlations",
            "contribution_concentration",
        ):
            self.assertNotIn(removed, payload)
        self.assertNotIn("source_provenance", payload["data"])
        self.assertIn("score_distribution", payload)
        self.assertIn("regime_duration", payload)
        self.assertIn("subperiod_stability", payload)

    def test_vintage_keeps_aggregate_revision_evidence_only(self) -> None:
        payload = safe.build_vintage(self.vintage_source)
        self._assert_raw_safe(payload)

        self.assertEqual(payload["schema_version"], safe.VINTAGE_SCHEMA_VERSION)
        self.assertEqual(len(payload["vintages"]), len(self.vintage_source["vintages"]))
        self.assertNotIn("component_zscore_revision_summary", payload["summary"])
        self.assertNotIn("path", payload["current_reference"])
        for row in payload["vintages"]:
            self.assertEqual(set(row), set(safe.VINTAGE_ROW_FIELDS))

    def test_vintage_csv_and_html_have_no_component_columns(self) -> None:
        payload = safe.build_vintage(self.vintage_source)
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "vintage.csv"
            safe.write_vintage_csv(payload, csv_path)
            with csv_path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, safe.VINTAGE_ROW_FIELDS)
                self.assertEqual(len(list(reader)), len(payload["vintages"]))

            html = safe.render_vintage_html(payload)
            self.assertIn("aggregate Score/regime revision evidence only", html)
            for term in (
                "DXY",
                "WTI",
                "SPX",
                "VIX",
                "BTC",
                "GOLD",
                "UST_2Y",
                "UST_10Y",
                "zscore",
                "contribution",
            ):
                self.assertNotIn(term, html)

    def test_assertion_rejects_component_key_reintroduction(self) -> None:
        payload = safe.build_point_in_time(self.pit_source)
        payload["source_provenance"] = {}
        with self.assertRaisesRegex(ValueError, "forbidden keys"):
            safe.assert_aggregate_safe(payload)


if __name__ == "__main__":
    unittest.main()
