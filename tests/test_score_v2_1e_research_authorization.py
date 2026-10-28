from __future__ import annotations

import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest import mock

from scripts import validate_score_v2_1e_research_authorization as validator

ROOT = Path(__file__).resolve().parents[1]


class     def test_one_off_research_is_consumed_and_production_is_not_authorized(self) -> None:
        report = validator.validate(ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["state"], "one_off_private_research_blocked")
        self.assertEqual(report["decision_status"], "hold_consumed")
        self.assertEqual(report["historical_owner_decision"], "approved")
        self.assertFalse(report["active_authorization_receipt_present"])
        self.assertTrue(report["historical_authorization_receipt_present"])
        self.assertEqual(report["exact_series_count"], 8)
        self.assertEqual(report["data_window"],
            {"start": "2013-01-01", "end": "2026-10-23"})
        self.assertFalse(report["real_data_fetch_authorized"])
        self.assertFalse(report["real_data_research_authorized"])
        self.assertFalse(report["production_authorized"])
        self.assertTrue(report["rights_hold"])

    def test_historical_approved_receipt_is_preserved_and_active_receipt_is_hold(self) -> None:
        archived = json.loads((ROOT / validator.HISTORICAL_RECEIPT).read_text(encoding="utf-8"))
        active = json.loads((ROOT / validator.ACTIVE_RECEIPT).read_text(encoding="utf-8"))
        self.assertEqual(archived["decision_status"], "approved")
        self.assertEqual(archived["approved_by"],
            "usdimpact owner via Issue #209 approval comment 6477834394")
        self.assertEqual(archived["approved_at"], "2026-10-28T18:55:48Z")
        self.assertTrue(archived["authorizations"]["real_data_research"])
        self.assertEqual(archived["data_window"],
            {"start": "2013-01-01", "end": "2026-10-23"})
        self.assertEqual(active["decision_status"], "hold")
        self.assertIsNone(active["approved_by"])
        self.assertIsNone(active["approved_at"])
        self.assertEqual(active["data_window"], {"start": None, "end": None})
        self.assertFalse(any(active["authorizations"].values()))

"start": "2013-01-01", "end": "2026-10-23"},
        )

    def test_template_remains_hold(self) -> None:
        template = json.loads(
            (
                ROOT
                / "governance/score-v2-1e-real-data-research-authorization.template.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(template["decision_status"], "hold")
        self.assertIsNone(template["approved_by"])
        self.assertIsNone(template["approved_at"])
        self.assertEqual(template["data_window"], {"start": None, "end": None})
        self    def test_non_research_actions_and_failed_research_are_hard_forbidden(self) -> None:
        active = json.loads((ROOT / validator.ACTIVE_RECEIPT).read_text(encoding="utf-8"))
        contract = json.loads((ROOT / "governance/score-v2-1e-real-data-execution-contract.json").read_text(encoding="utf-8"))
        self.assertFalse(any(active["authorizations"].values()))
        self.assertEqual(contract["state"], "one_off_private_research_blocked")
        self.assertFalse(contract["active_authorization_receipt_expected_now"])
        self.assertIsNone(contract["active_authorization_receipt_path"])
        self.assertTrue(all(v is False for v in contract["current_state"].values()))

  self.assertFalse(auth["source_contract_acceptance"])

    def test_execution_contract_allows_only_official_direct_hosts(self) -> None:
        contract = json.loads(
            (
                ROOT / "governance/score-v2-1e-real-data-execution-contract.json"
            ).read_text(encoding="utf-8")
        )
        hosts = set(contract["network_policy"]["allowed_hosts"])
        self.assertIn("www.federalreserve.gov", hosts)
        self.assertIn("www.bls.gov", hosts)
        self.assertIn("data.bls.gov", hosts)
        self.assertFalse(contract["network_policy"]["credentials_required"])
        self.assertIn("Refinitiv", contract["network_policy"]["disallowed_source_families"])
        self.assertIn("Yahoo", contract["network_policy"]["disallowed_source_families"])


    def test_h15_fail_closed_closeout_is_exact_and_value_free(self) -> None:
        stop = json.loads((ROOT / validator.CLOSEOUT).read_text(encoding="utf-8"))
        self.assertEqual(stop["state"], "failed_closed_consumed")
        self.assertEqual(stop["blocked_source_family"], "H15")
        self.assertEqual(stop["blocked_release_date"], "2020-01-06")
        self.assertEqual(stop["failed_official_archive_path"],
            "/releases/h15/20200106/default.htm")
        self.assertEqual(stop["failed_http_status"], 404)
        self.assertEqual(stop["fed_sample_families_reached"], ["H10", "H8", "H41"])
        self.assertFalse(stop["one_off_research_authorized_now"])
        self.assertFalse(stop["full_candidate_score_computed"])
        self.assertFalse(stop["source_or_component_values_persisted"])
        self.assertFalse(stop["retry_under_original_approval_authorized"])
        self.assertFalse(stop["revised_current_history_substitute_authorized"])
        self.assertFalse(stop["alternative_sources_under_original_approval_authorized"])
        self.assertFalse(stop["drop_or_reweight_h15_authorized"])
        self.assertTrue(stop["future_design_requires_new_version_preregistration_and_owner_review"])

    def test_blocked_preflight_never_reaches_official_source_transport(self) -> None:
        from scripts import run_score_v2_1e_live_preflight as preflight
        with mock.patch.object(preflight, "_get_fixed",
                               side_effect=AssertionError("HTTP access must not be attempted")) as fetch:
            with self.assertRaisesRegex(RuntimeError, "not active"):
                preflight.run_preflight()
            fetch.assert_not_called()

    def test_tampered_closeout_or_reactivated_contract_is_rejected(self) -> None:
        copied = [
            validator.ACTIVE_RECEIPT,
            validator.HISTORICAL_RECEIPT,
            validator.CLOSEOUT,
            "governance/score-v2-1e-real-data-research-authorization.schema.json",
            "governance/score-v2-1e-real-data-research-authorization.template.json",
            "governance/score-v2-1e-real-data-execution-contract.json",
            "governance/score-v2-1e-preregistration.json",
            "governance/score-publication-rights-gate.json",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            for item in copied:
                target = sandbox / item
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / item, target)
            stop_path = sandbox / validator.CLOSEOUT
            stop = json.loads(stop_path.read_text(encoding="utf-8"))
            stop["failed_http_status"] = 200
            stop_path.write_text(json.dumps(stop), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "stop evidence changed"):
                validator.validate(sandbox)
            shutil.copyfile(ROOT / validator.CLOSEOUT, stop_path)
            contract_path = sandbox / "governance/score-v2-1e-real-data-execution-contract.json"
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["state"] = "one_off_private_research_authorized"
            contract["current_state"]["real_data_fetch_authorized"] = True
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "permanently blocked"):
                validator.validate(sandbox)
            shutil.copyfile(ROOT / "governance/score-v2-1e-real-data-execution-contract.json", contract_path)
            (sandbox / validator.CLOSEOUT).unlink()
            with self.assertRaises(FileNotFoundError):
                validator.validate(sandbox)


if __name__ == "__main__":
    unittest.main()
