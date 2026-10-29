"""Offline-only tests for the Score v2.1F v10 recovery guard.

Fixtures contain committed governance records, never BLS responses or economic values.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.validate_score_v2_1f_wpu0561_recovery import (
    EXPECTED_HOLD_FILES,
    MANIFEST_PATH,
    ROOT,
    isolated_restore_drill,
    validate,
)


class RecoveryGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="score-recovery-tests-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for relative in [MANIFEST_PATH, *sorted(EXPECTED_HOLD_FILES)]:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def _change_json(self, relative: str | Path, updater) -> None:
        file = self.root / relative
        value = json.loads(file.read_text(encoding="utf-8"))
        updater(value)
        file.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def test_expected_frozen_hold_passes_without_git_or_network(self) -> None:
        result = validate(self.root)
        self.assertEqual(result["status"], "passed")
        self.assertFalse(result["production_authorized"])
        self.assertFalse(result["pdf_or_bls_network_used"])
        self.assertEqual(result["frozen_blob_count"], 6)

    def test_active_receipt_fails_closed(self) -> None:
        receipt = self.root / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
        receipt.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "active receipt"):
            validate(self.root)

    def test_dispatch_marker_fails_closed(self) -> None:
        dispatch = self.root / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
        dispatch.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "dispatch marker"):
            validate(self.root)

    def test_rights_hold_change_fails_closed(self) -> None:
        self._change_json("governance/score-publication-rights-gate.json", lambda o: o.update(state="approved"))
        with self.assertRaisesRegex(RuntimeError, "frozen v9 content changed"):
            validate(self.root)

    def test_manifest_cannot_activate_pdf_retrieval(self) -> None:
        self._change_json(MANIFEST_PATH, lambda o: o.update(live_bls_or_pdf_retrieval_authorized=True))
        with self.assertRaisesRegex(RuntimeError, "must be unauthorized"):
            validate(self.root)

    def test_manifest_cannot_authorize_production_restore(self) -> None:
        self._change_json(MANIFEST_PATH, lambda o: o["authorizations"].update(production_rollback=True))
        with self.assertRaisesRegex(RuntimeError, "must remain false"):
            validate(self.root)

    def test_baseline_commit_cannot_silently_change(self) -> None:
        self._change_json(MANIFEST_PATH, lambda o: o["baseline"].update(immutable_commit="a" * 40))
        with self.assertRaisesRegex(RuntimeError, "baseline commit changed"):
            validate(self.root)

    def test_inert_workflow_change_fails_closed(self) -> None:
        file = self.root / ".github/workflows/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight.yml"
        file.write_text(file.read_text(encoding="utf-8").replace("if: $" + "{{ false }}", "if: $" + "{{ true }}"), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "frozen v9 content changed"):
            validate(self.root)

    def test_synthetic_recovery_changes_only_throwaway_fixture(self) -> None:
        result = isolated_restore_drill()
        self.assertTrue(result["recovered_hold"])
        self.assertTrue(result["unrelated_changes_preserved"])
        self.assertFalse(result["force_push_used"])
        self.assertFalse(result["real_repository_or_production_changed"])


if __name__ == "__main__":
    unittest.main()
