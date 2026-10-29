"""Fail-closed v1 release-interlock adversarial tests, synthetic local policies only.

These tests must not fetch providers, inspect Score observations, contact counsel,
write public artifacts or authorize a future v2 rights decision.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.score_publication_rights_gate import (
    ALLOWED_SCOPE, ISSUE_URL, REQUIRED_RESUME,
    evaluate_policy, load_policy, write_github_output,
)


REASON = "v1-allow-not-an-authorized-rights-release-contract"
ROOT = Path(__file__).resolve().parents[1]


def synthetic_v1(state: str = "allow") -> dict:
    return {
        "version": 1,
        "state": state,
        "effective_date": "2026-10-29",
        "issue": ISSUE_URL,
        "reason": "Provider counsel review complete - synthetic test only",
        "scope": sorted(ALLOWED_SCOPE),
        "resume_requires": sorted(REQUIRED_RESUME),
        "decision_receipt": (
            "https://github.com/usdimpact/usd-impact-pipeline/issues/155#issuecomment-1234567"
        ),
        "approved_by": "Synthetic Review Owner",
    }


class ScoreRightsV1InterlockTests(unittest.TestCase):
    def assert_rejected(self, p: dict, reason: str | None = None) -> None:
        actual = evaluate_policy(p)
        self.assertIs(actual["hold"], True)
        self.assertNotEqual(actual["state"], "allow")
        self.assertIsNone(actual["decision_receipt"])
        if reason is not None:
            self.assertEqual(actual["reason"], reason)

    def test_valid_synthetic_issue_comment_is_not_a_license(self) -> None:
        self.assert_rejected(synthetic_v1(), REASON)

    def test_valid_synthetic_pull_comment_is_not_a_license(self) -> None:
        p = synthetic_v1()
        p["decision_receipt"] = (
            "https://github.com/usdimpact/usd-impact-pipeline/pull/303#issuecomment-1234567"
        )
        self.assert_rejected(p, REASON)

    def test_valid_synthetic_repository_url_is_not_a_license(self) -> None:
        p = synthetic_v1()
        p["decision_receipt"] = "https://github.com/usdimpact/usd-impact-pipeline/issues/155"
        self.assert_rejected(p, REASON)

    def test_approver_name_is_not_approval(self) -> None:
        for label in ("Owner", "Legal Counsel", "Production Release Manager"):
            with self.subTest(label=label):
                p = synthetic_v1()
                p["approved_by"] = label
                self.assert_rejected(p, REASON)

    def test_unapproved_http_reference_is_rejected(self) -> None:
        p = synthetic_v1()
        p["decision_receipt"] = "http://github.com/usdimpact/usd-impact-pipeline/issues/155"
        self.assert_rejected(p, "allow-policy-missing-valid-decision-receipt")

    def test_lookalike_domain_is_rejected(self) -> None:
        p = synthetic_v1()
        p["decision_receipt"] = (
            "https://github.com.evil.example/usdimpact/usd-impact-pipeline/issues/155"
        )
        self.assert_rejected(p, "allow-policy-missing-valid-decision-receipt")

    def test_wrong_citation_fragment_is_rejected(self) -> None:
        p = synthetic_v1()
        p["decision_receipt"] = (
            "https://github.com/usdimpact/usd-impact-pipeline/issues/155#not-an-audit"
        )
        self.assert_rejected(p, "allow-policy-missing-valid-decision-receipt")

    def test_missing_receipt_is_rejected(self) -> None:
        p = synthetic_v1()
        p["decision_receipt"] = None
        self.assert_rejected(p, "allow-policy-missing-valid-decision-receipt")

    def test_missing_approver_is_rejected(self) -> None:
        p = synthetic_v1()
        p["approved_by"] = None
        self.assert_rejected(p, "allow-policy-missing-approver")

    def test_unapproved_v2_policy_version_is_rejected(self) -> None:
        p = synthetic_v1()
        p["version"] = 2
        self.assert_rejected(p, "unsupported-rights-policy-version")

    def test_extra_approval_fields_fail_closed(self) -> None:
        p = synthetic_v1()
        p["seven_provider_dispositions"] = "approved"
        self.assert_rejected(p, "unexpected-rights-policy-fields")

    def test_missing_review_field_fails_closed(self) -> None:
        p = synthetic_v1()
        p.pop("resume_requires")
        self.assert_rejected(p, "unexpected-rights-policy-fields")

    def test_current_hold_stays_hold(self) -> None:
        p = synthetic_v1("hold")
        p["decision_receipt"] = None
        p["approved_by"] = None
        result = evaluate_policy(p)
        self.assertIs(result["hold"], True)
        self.assertEqual(result["state"], "hold")

    def test_hold_with_synthetic_approver_is_invalid(self) -> None:
        p = synthetic_v1("hold")
        self.assert_rejected(p, "hold-policy-must-not-carry-approval")

    def test_broken_json_policy_file_stays_hold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "policy.json"
            path.write_text("{not-json", encoding="utf-8")
            self.assertTrue(load_policy(path)["hold"])

    def test_load_synthetic_valid_allow_file_still_holds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "policy.json"
            path.write_text(json.dumps(synthetic_v1()) + "\n", encoding="utf-8")
            self.assert_rejected(json.loads(path.read_text(encoding="utf-8")), REASON)
            self.assertEqual(load_policy(path)["reason"], REASON)

    def test_github_output_is_boolean_hold_without_receipt(self) -> None:
        result = evaluate_policy(synthetic_v1())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out"
            write_github_output(result, path)
            data = path.read_text(encoding="utf-8")
        self.assertEqual(data.splitlines()[0], "hold=true")
        self.assertIn("state=invalid", data)
        self.assertNotIn("issuecomment-1234567", data)
        self.assertNotIn("hold=false", data)

    def test_cli_cannot_release_lookalike_approved_v1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy = root / "policy.json"
            output = root / "GITHUB_OUTPUT"
            policy.write_text(json.dumps(synthetic_v1()) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "scripts.score_publication_rights_gate",
                 "--policy", str(policy), "--github-output", str(output)],
                cwd=ROOT, text=True, capture_output=True, check=True, timeout=8,
            )
            self.assertEqual(json.loads(result.stdout)["state"], "invalid")
            self.assertEqual(output.read_text(encoding="utf-8").splitlines()[0],
                             "hold=true")


if __name__ == "__main__":
    unittest.main()
