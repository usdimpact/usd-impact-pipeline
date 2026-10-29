"""Offline-only adversarial contract tests for the dormant Score public prototype.

Synthetic 2099 Friday rows only: no real Score files, provider observations,
history, private evidence storage, network access or publication permissions.
"""
from __future__ import annotations

import copy
import csv
import json
import math
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from scripts import build_score_public_safe_artifact as safe


def source() -> dict:
    starts = date(2099, 1, 2)  # Friday; deliberately not a live market date
    values = (
        (0.00, "Neutral / transitional"),
        (0.31, "Firm dollar regime"),
        (1.25, "Strong dollar regime"),
        (-0.70, "Soft dollar regime"),
        (-1.30, "Weak dollar regime"),
        (-0.05, "Neutral / transitional"),
    )
    return {
        "metadata": {
            "pipeline": "usd_impact_score_v2",
            "generated_at_utc": "2099-02-13T22:00:00+00:00",
            "weights": dict(safe.EXPECTED_WEIGHTS),
            "source_provenance": {"unpublished": "synthetic private only"},
        },
        "weeks": [
            {"date": str(starts + timedelta(days=7 * i)),
             "score": score, "regime": regime,
             "synthetic_component": "MUST_NOT_COPY"}
            for i, (score, regime) in enumerate(values)
        ],
    }


class AggregateSafeSyntheticContractTests(unittest.TestCase):
    def prepared(self) -> dict:
        output = safe.build_public_safe_payload(source())
        safe.assert_public_safe(output)
        return output

    def test_synthetic_contract_preserves_only_reviewed_fields(self) -> None:
        payload = self.prepared()
        self.assertEqual(set(payload), safe.ROOT_KEYS)
        self.assertEqual(len(payload["history"]), 6)
        self.assertEqual(payload["metadata"]["pipeline"], "usd_impact_score_v2")
        self.assertEqual(payload["latest"]["score"], -0.05)
        self.assertNotIn("synthetic_component", json.dumps(payload))
        self.assertNotIn("source_provenance", json.dumps(payload))

    def test_synthetic_csv_has_exact_aggregate_columns(self) -> None:
        payload = self.prepared()
        with tempfile.TemporaryDirectory() as tmp:
            j = Path(tmp) / "score.json"
            c = Path(tmp) / "score.csv"
            safe.write_outputs(payload, j, c)
            self.assertEqual(json.loads(j.read_text(encoding="utf-8")), payload)
            with c.open(encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream)
                self.assertEqual(reader.fieldnames, ["date", "score", "regime"])
                self.assertEqual(len(list(reader)), 6)

    def test_nonfinite_history_score_denied(self) -> None:
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value):
                raw = source()
                raw["weeks"][2]["score"] = value
                with self.assertRaisesRegex(ValueError, "finite"):
                    safe.build_public_safe_payload(raw)

    def test_nonfinite_methodology_weight_denied(self) -> None:
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value):
                raw = source()
                raw["metadata"]["weights"]["DXY"] = value
                with self.assertRaisesRegex(ValueError, "finite"):
                    safe.build_public_safe_payload(raw)

    def test_boolean_score_denied(self) -> None:
        raw = source()
        raw["weeks"][0]["score"] = True
        with self.assertRaisesRegex(ValueError, "must be numeric"):
            safe.build_public_safe_payload(raw)

    def test_excessively_large_numeric_score_denied(self) -> None:
        raw = source()
        raw["weeks"][0]["score"] = 10 ** 1000
        with self.assertRaisesRegex(ValueError, "finite"):
            safe.build_public_safe_payload(raw)

    def test_source_invalid_friday_denied(self) -> None:
        raw = source()
        raw["weeks"][0]["date"] = "2099-01-03"  # Saturday
        with self.assertRaisesRegex(ValueError, "Friday"):
            safe.build_public_safe_payload(raw)

    def test_source_invalid_calendar_date_denied(self) -> None:
        raw = source()
        raw["weeks"][0]["date"] = "2099-02-30"
        with self.assertRaisesRegex(ValueError, "valid calendar date"):
            safe.build_public_safe_payload(raw)

    def test_source_nonmonotonic_history_denied(self) -> None:
        raw = source()
        raw["weeks"][1]["date"] = raw["weeks"][0]["date"]
        with self.assertRaisesRegex(ValueError, "chronological"):
            safe.build_public_safe_payload(raw)

    def test_source_untrusted_regime_denied(self) -> None:
        raw = source()
        raw["weeks"][-1]["regime"] = '=IMPORTDATA("https://bad.example/")'
        with self.assertRaisesRegex(ValueError, "inconsistent regime"):
            safe.build_public_safe_payload(raw)

    def test_source_regime_must_match_frozen_thresholds(self) -> None:
        raw = source()
        raw["weeks"][1]["regime"] = "Weak dollar regime"
        with self.assertRaisesRegex(ValueError, "inconsistent regime"):
            safe.build_public_safe_payload(raw)

    def test_schema_version_mismatch_denied(self) -> None:
        output = self.prepared()
        output["schema_version"] = "unreviewed-safe-2"
        with self.assertRaisesRegex(ValueError, "schema version"):
            safe.assert_public_safe(output)

    def test_root_unknown_fields_denied(self) -> None:
        output = self.prepared()
        output["metadata_private_price_copy"] = "unreviewed"
        with self.assertRaisesRegex(ValueError, "aggregate payload"):
            safe.assert_public_safe(output)

    def test_metadata_unknown_fields_denied(self) -> None:
        output = self.prepared()
        output["metadata"]["debug_json"] = {"historic_source": "redacted"}
        with self.assertRaisesRegex(ValueError, "aggregate metadata"):
            safe.assert_public_safe(output)

    def test_extra_weight_driver_denied(self) -> None:
        raw = source()
        raw["metadata"]["weights"]["EXTRA_SOURCE"] = 0.01
        with self.assertRaisesRegex(ValueError, "methodology weights"):
            safe.build_public_safe_payload(raw)

    def test_frozen_weight_value_denied_on_change(self) -> None:
        raw = source()
        raw["metadata"]["weights"]["SPX"] = 0.8
        with self.assertRaisesRegex(ValueError, "frozen methodology"):
            safe.build_public_safe_payload(raw)

    def test_frozen_pipeline_name_denied_on_change(self) -> None:
        raw = source()
        raw["metadata"]["pipeline"] = "provider=https://example.invalid"
        with self.assertRaisesRegex(ValueError, "frozen v2 identifier"):
            safe.build_public_safe_payload(raw)

    def test_generated_at_rejects_non_utc_offset(self) -> None:
        raw = source()
        raw["metadata"]["generated_at_utc"] = "2099-01-09T22:00:00+02:00"
        with self.assertRaisesRegex(ValueError, "UTC offset"):
            safe.build_public_safe_payload(raw)

    def test_generated_at_rejects_naive_timestamp(self) -> None:
        raw = source()
        raw["metadata"]["generated_at_utc"] = "2099-01-09T22:00:00"
        with self.assertRaisesRegex(ValueError, "UTC offset"):
            safe.build_public_safe_payload(raw)

    def test_synthetic_null_generated_at_remains_supported(self) -> None:
        raw = source()
        raw["metadata"]["generated_at_utc"] = None
        self.assertIsNone(safe.build_public_safe_payload(raw)["metadata"]["generated_at_utc"])

    def test_latest_component_leak_denied(self) -> None:
        output = self.prepared()
        output["latest"]["weekly_level"] = {"BTC": "fake"}
        with self.assertRaisesRegex(ValueError, "forbidden keys"):
            safe.assert_public_safe(output)

    def test_latest_unknown_field_denied(self) -> None:
        output = self.prepared()
        output["latest"]["unreviewed"] = 1
        with self.assertRaisesRegex(ValueError, "latest"):
            safe.assert_public_safe(output)

    def test_latest_week_mismatch_denied(self) -> None:
        output = self.prepared()
        output["latest"]["week_ending"] = "2099-01-02"
        with self.assertRaisesRegex(ValueError, "latest date"):
            safe.assert_public_safe(output)

    def test_latest_score_mismatch_denied(self) -> None:
        output = self.prepared()
        output["latest"]["score"] = 2
        with self.assertRaisesRegex(ValueError, "latest score"):
            safe.assert_public_safe(output)

    def test_weekly_change_mismatch_denied(self) -> None:
        output = self.prepared()
        output["latest"]["week_over_week_change"] = 42
        with self.assertRaisesRegex(ValueError, "weekly aggregate change"):
            safe.assert_public_safe(output)

    def test_four_week_change_mismatch_denied(self) -> None:
        output = self.prepared()
        output["latest"]["four_week_change"] = 42
        with self.assertRaisesRegex(ValueError, "four-week aggregate change"):
            safe.assert_public_safe(output)

    def test_history_hash_mismatch_denied(self) -> None:
        output = self.prepared()
        output["release_evidence"]["aggregate_history_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA256"):
            safe.assert_public_safe(output)

    def test_history_row_unknown_field_denied(self) -> None:
        output = self.prepared()
        output["history"][0]["provider_url"] = "https://no-provider.example"
        with self.assertRaisesRegex(ValueError, "history row 0"):
            safe.assert_public_safe(output)

    def test_metadata_n_weeks_mismatch_denied(self) -> None:
        output = self.prepared()
        output["metadata"]["n_weeks"] = 8
        with self.assertRaisesRegex(ValueError, "week count"):
            safe.assert_public_safe(output)

    def test_metadata_bool_week_count_denied(self) -> None:
        output = self.prepared()
        output["metadata"]["n_weeks"] = True
        with self.assertRaisesRegex(ValueError, "week count"):
            safe.assert_public_safe(output)

    def test_writer_rejects_bad_payload_before_creating_files(self) -> None:
        output = self.prepared()
        output["latest"]["score"] = float("nan")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "no_output"
            with self.assertRaisesRegex(ValueError, "finite"):
                safe.write_outputs(output, target / "a.json", target / "a.csv")
            self.assertFalse(target.exists())

    def test_frozen_metadata_schema_is_still_closed(self) -> None:
        schema = json.loads((
            Path(__file__).resolve().parents[1] /
            "schemas/score_public_safe.schema.json"
        ).read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["properties"]), safe.ROOT_KEYS)
        self.assertFalse(schema["properties"]["history"]["items"]["additionalProperties"])

    def test_no_provider_network_in_transform_module(self) -> None:
        source_text = (Path(__file__).resolve().parents[1] /
                       "scripts/build_score_public_safe_artifact.py").read_text(encoding="utf-8")
        for marker in ("import yfinance", "pandas_datareader", "requests.get(", "urlopen("):
            self.assertNotIn(marker, source_text)


if __name__ == "__main__":
    unittest.main()
