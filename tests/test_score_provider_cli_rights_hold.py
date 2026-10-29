"""Offline negative tests for original Score provider-retrieval entrypoints.

Never request source observations. A malformed or plausibly "approved" v1
policy must still block all direct Python provider-consuming paths.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import usd_impact_score_v2 as score
from scripts import build_score_repro_bundle as bundle
from scripts import score_publication_rights_gate as gate


class ScoreProviderCLIRightsHoldTests(unittest.TestCase):
    def test_canonical_hold_denies_library_fetch_before_both_providers(self) -> None:
        with (
            patch.object(score, "fetch_yahoo", side_effect=AssertionError("Yahoo contacted")) as yahoo,
            patch.object(score, "fetch_fred", side_effect=AssertionError("FRED contacted")) as fred,
        ):
            with self.assertRaisesRegex(PermissionError, "rights HOLD"):
                score.fetch_all_inputs("2099-01-01", None)
            yahoo.assert_not_called()
            fred.assert_not_called()

    def test_manual_score_modes_deny_before_log_cache_output_or_fetch(self) -> None:
        for options in (
            (),
            ("--test",),
            ("--web",),
            ("--web", "--test"),
            ("--backtest",),
        ):
            with self.subTest(mode=options), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                output = root / "uncreated-score-output"
                previous = Path.cwd()
                try:
                    os.chdir(root)
                    with (
                        patch.object(sys, "argv", ["usd_impact_score_v2.py", "--output-dir", str(output), *options]),
                        patch.object(score, "setup_logging") as setup,
                        patch.object(score, "fetch_all_inputs", side_effect=AssertionError("provider fetch")) as fetch,
                        patch.object(score.pd, "read_parquet", side_effect=AssertionError("cache accessed")) as cache,
                        contextlib.redirect_stderr(io.StringIO()) as stderr,
                    ):
                        status = score.main()
                    self.assertEqual(status, 3)
                    self.assertIn("rights HOLD", stderr.getvalue())
                    setup.assert_not_called()
                    fetch.assert_not_called()
                    cache.assert_not_called()
                    self.assertFalse(output.exists())
                    self.assertFalse((root / "logs").exists())
                    self.assertFalse((root / ".pipeline_cache").exists())
                finally:
                    os.chdir(previous)

    def test_direct_repro_live_refetch_denied_before_score_read_or_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "not-created.json"
            missing_input = Path(tmp) / "not-read-score.json"
            with (
                patch.object(sys, "argv", [
                    "build_score_repro_bundle.py",
                    "--score-json", str(missing_input),
                    "--output", str(output),
                    "--live-refetch",
                ]),
                patch.object(bundle, "_load_score_json", side_effect=AssertionError("read score")) as read,
                patch.object(bundle, "_live_weekly", side_effect=AssertionError("provider fetch")) as live,
                contextlib.redirect_stderr(io.StringIO()) as stderr,
            ):
                status = bundle.main()
            self.assertEqual(status, 3)
            self.assertIn("rights HOLD", stderr.getvalue())
            read.assert_not_called()
            live.assert_not_called()
            self.assertFalse(output.exists())

    def test_direct_repro_helper_denies_before_fetch_all_inputs(self) -> None:
        with patch.object(score, "fetch_all_inputs", side_effect=AssertionError("provider fetch")) as fetch:
            with self.assertRaisesRegex(PermissionError, "rights HOLD"):
                bundle._live_weekly({"metadata": {}, "weeks": []})
            fetch.assert_not_called()

    def test_missing_or_malformed_pinned_policy_stays_denied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "no-policy.json"
            damaged = Path(tmp) / "damaged.json"
            invalid_utf8 = Path(tmp) / "unreadable-utf8.json"
            damaged.write_text("{invalid", encoding="utf-8")
            invalid_utf8.write_bytes(b"\\xff")
            for path in (missing, damaged, invalid_utf8):
                with self.subTest(policy=str(path)), patch.object(
                    gate, "CANONICAL_REPOSITORY_POLICY", path
                ):
                    with self.assertRaisesRegex(PermissionError, "rights HOLD"):
                        gate.require_score_provider_rights()

    def test_valid_looking_v1_allow_with_receipt_cannot_open_retrieval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "policy.json"
            review = json.loads(gate.CANONICAL_REPOSITORY_POLICY.read_text(encoding="utf-8"))
            review.update({
                "state": "allow",
                "approved_by": "Synthetic Review Owner",
                "decision_receipt": "https://github.com/usdimpact/usd-impact-pipeline/issues/155#issuecomment-12345",
            })
            path.write_text(json.dumps(review), encoding="utf-8")
            with patch.object(gate, "CANONICAL_REPOSITORY_POLICY", path):
                self.assertEqual(
                    gate.load_policy(path)["reason"],
                    "v1-allow-not-an-authorized-rights-release-contract",
                )
                with self.assertRaisesRegex(PermissionError, "rights HOLD"):
                    gate.require_score_provider_rights()

    def test_caller_working_directory_and_environment_are_not_policy_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = root / "governance/score-publication-rights-gate.json"
            fake.parent.mkdir(parents=True)
            fake.write_text('{"version": 99, "state": "allow"}', encoding="utf-8")
            old_cwd = Path.cwd()
            try:
                os.chdir(root)
                with patch.dict(os.environ, {"USD_IMPACT_SCORE_ALLOW": "true"}):
                    self.assertNotEqual(gate.CANONICAL_REPOSITORY_POLICY, fake)
                    with self.assertRaisesRegex(PermissionError, "rights HOLD"):
                        gate.require_score_provider_rights()
            finally:
                os.chdir(old_cwd)

    def test_offline_pure_score_and_repro_functions_remain_callable(self) -> None:
        # The guard belongs at data-access / output entrypoints, not in
        # deterministic pure calculations used by frozen research tests.
        self.assertEqual(score.label_regime(0.0), "Neutral / transitional")
        self.assertEqual(score.WEIGHTS["UST_2Y"], 0.125)
        self.assertIsInstance(bundle.INPUT_HISTORY_SCOPE, str)


if __name__ == "__main__":
    unittest.main()
