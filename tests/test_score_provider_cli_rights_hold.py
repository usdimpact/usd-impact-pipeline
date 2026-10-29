"""No-network tests for a guarded launcher around immutable Score engines.

The original Score CLI and reproduction builder are deliberately *not* edited:
the 2026-08 Score v3 holdout lock pins both byte-for-byte. These tests verify
the supported manual launcher refuses to start either program under HOLD.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import score_provider_guarded_cli as launcher
from scripts import score_publication_rights_gate as gate


REPO_ROOT = Path(__file__).resolve().parents[1]


class ScoreProviderCLIRightsHoldTests(unittest.TestCase):
    def test_current_policy_denies_score_manual_launcher_without_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for args in (
                ("score",),
                ("score", "--web", "--output-dir", str(root / "public")),
                ("score", "--test"),
                ("score", "--web", "--test", "--backtest"),
            ):
                with self.subTest(arguments=args):
                    with (
                        patch.object(launcher.subprocess, "run", side_effect=AssertionError("would launch frozen engine")) as run,
                        contextlib.redirect_stderr(io.StringIO()) as stderr,
                    ):
                        status = launcher.main(list(args))
                    self.assertEqual(status, 3)
                    self.assertIn("rights HOLD", stderr.getvalue())
                    run.assert_not_called()
            self.assertFalse((root / "public").exists())

    def test_current_policy_denies_repro_modes_before_input_or_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "not-present-score.json"
            output = root / "never-written-bundle.json"
            for args in (
                ("repro", "--score-json", str(input_path), "--output", str(output), "--live-refetch"),
                ("repro", "--score-json", str(input_path), "--output", str(output),
                 "--weekly-levels", str(root / "not-present.csv")),
            ):
                with self.subTest(arguments=args):
                    with (
                        patch.object(launcher.subprocess, "run", side_effect=AssertionError("would read input")) as run,
                        contextlib.redirect_stderr(io.StringIO()) as stderr,
                    ):
                        status = launcher.main(list(args))
                    self.assertEqual(status, 3)
                    self.assertIn("rights HOLD", stderr.getvalue())
                    run.assert_not_called()
                    self.assertFalse(output.exists())

    def test_missing_malformed_and_invalid_utf8_rights_files_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "missing-policy.json"
            malformed = root / "malformed.json"
            invalid_utf8 = root / "invalid-utf8.json"
            malformed.write_text("{not-a-json-policy", encoding="utf-8")
            invalid_utf8.write_bytes(bytes([255]))
            for policy in (missing, malformed, invalid_utf8):
                with self.subTest(policy=policy.name), patch.object(
                    gate, "CANONICAL_REPOSITORY_POLICY", policy
                ):
                    with (
                        patch.object(launcher.subprocess, "run", side_effect=AssertionError("launch")) as run,
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        self.assertEqual(launcher.main(["score"]), 3)
                    run.assert_not_called()

    def test_plausible_v1_allow_receipt_still_cannot_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mock_policy = Path(tmp) / "rights.json"
            source = json.loads(gate.CANONICAL_REPOSITORY_POLICY.read_text(encoding="utf-8"))
            source.update({
                "state": "allow",
                "approved_by": "Synthetic Test Approver",
                "decision_receipt": "https://github.com/usdimpact/usd-impact-pipeline/issues/155#issuecomment-12345",
            })
            mock_policy.write_text(json.dumps(source), encoding="utf-8")
            with patch.object(gate, "CANONICAL_REPOSITORY_POLICY", mock_policy):
                self.assertEqual(
                    gate.load_policy(mock_policy)["reason"],
                    "v1-allow-not-an-authorized-rights-release-contract",
                )
                with patch.object(launcher.subprocess, "run", side_effect=AssertionError("launch")) as run:
                    with contextlib.redirect_stderr(io.StringIO()):
                        self.assertEqual(launcher.main(["repro", "--live-refetch"]), 3)
                    run.assert_not_called()

    def test_cwd_fake_allow_and_environment_do_not_bypass_repo_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = root / "governance/score-publication-rights-gate.json"
            fake.parent.mkdir()
            fake.write_text('{"state":"allow"}', encoding="utf-8")
            old = Path.cwd()
            try:
                os.chdir(root)
                with (
                    patch.dict(os.environ, {"USD_IMPACT_SCORE_ALLOW": "true"}),
                    patch.object(launcher.subprocess, "run", side_effect=AssertionError("launch")) as run,
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    self.assertNotEqual(gate.CANONICAL_REPOSITORY_POLICY, fake)
                    self.assertEqual(launcher.main(["score", "--test"]), 3)
                    run.assert_not_called()
            finally:
                os.chdir(old)

    def test_frozen_engine_and_reproduction_builder_hashes_are_unchanged(self) -> None:
        lock = json.loads(
            (REPO_ROOT / "research/score_v3_engine_lock.json").read_text(encoding="utf-8")
        )
        for source in ("usd_impact_score_v2.py", "scripts/build_score_repro_bundle.py"):
            with self.subTest(path=source):
                expected = lock["immutable_files"][source]
                actual = hashlib.sha256((REPO_ROOT / source).read_bytes()).hexdigest()
                self.assertEqual(actual, expected)

    def test_launcher_passes_safe_argument_vector_without_shell_on_future_authority(self) -> None:
        # Simulate a future *reviewed* rights decision by mocking the gate.
        # Subprocess is mocked: no Python engine or provider is executed.
        fake_process = type("Run", (), {"returncode": 0})()
        for operation, argv, module in (
            ("score", ["--web", "--output-dir", "public"], "usd_impact_score_v2"),
            ("repro", ["--live-refetch", "--score-json", "synthetic.json"],
             "scripts.build_score_repro_bundle"),
        ):
            with self.subTest(operation=operation):
                with (
                    patch.object(launcher, "require_score_provider_rights", return_value=None),
                    patch.object(launcher.subprocess, "run", return_value=fake_process) as run,
                ):
                    self.assertEqual(launcher.main([operation, *argv]), 0)
                run.assert_called_once_with(
                    [sys.executable, "-m", module, *argv],
                    cwd=launcher.REPO_ROOT,
                    check=False,
                )

    def test_invalid_command_never_checks_provider_or_runs(self) -> None:
        with (
            patch.object(launcher, "require_score_provider_rights") as gate_check,
            patch.object(launcher.subprocess, "run") as run,
            contextlib.redirect_stderr(io.StringIO()),
        ):
            with self.assertRaises(SystemExit) as result:
                launcher.main(["unknown", "--web"])
            self.assertNotEqual(result.exception.code, 0)
            gate_check.assert_not_called()
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
