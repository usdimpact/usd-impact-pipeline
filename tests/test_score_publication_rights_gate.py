from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.score_publication_rights_gate import (
    ALLOWED_SCOPE,
    ISSUE_URL,
    REQUIRED_RESUME,
    evaluate_policy,
    load_policy,
    write_github_output,
)


def valid_policy(state: str = "hold") -> dict:
    return {
        "version": 1,
        "state": state,
        "effective_date": "2026-10-28",
        "issue": ISSUE_URL,
        "reason": "review pending",
        "scope": sorted(ALLOWED_SCOPE),
        "resume_requires": sorted(REQUIRED_RESUME),
        "decision_receipt": None,
        "approved_by": None,
    }


class ScorePublicationRightsGateTests(unittest.TestCase):
    def test_current_hold_is_fail_closed(self) -> None:
        result = evaluate_policy(valid_policy())
        self.assertTrue(result["hold"])
        self.assertEqual(result["state"], "hold")

    def test_missing_policy_holds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = load_policy(Path(tmp) / "missing.json")
        self.assertTrue(result["hold"])
        self.assertEqual(result["state"], "invalid")

    def test_malformed_json_holds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "policy.json"
            path.write_text("{", encoding="utf-8")
            result = load_policy(path)
        self.assertTrue(result["hold"])

    def test_unknown_field_holds(self) -> None:
        policy = valid_policy()
        policy["bypass"] = True
        result = evaluate_policy(policy)
        self.assertTrue(result["hold"])
        self.assertEqual(result["reason"], "unexpected-rights-policy-fields")

    def test_scope_cannot_be_narrowed(self) -> None:
        policy = valid_policy()
        policy["scope"] = ["weekly_score_publication_generation"]
        result = evaluate_policy(policy)
        self.assertTrue(result["hold"])
        self.assertEqual(result["reason"], "invalid-rights-policy-scope")

    def test_hold_cannot_smuggle_approval(self) -> None:
        policy = valid_policy()
        policy["approved_by"] = "Owner"
        result = evaluate_policy(policy)
        self.assertTrue(result["hold"])
        self.assertEqual(result["reason"], "hold-policy-must-not-carry-approval")

    def test_allow_requires_named_approver_and_github_receipt(self) -> None:
        policy = valid_policy("allow")
        result = evaluate_policy(policy)
        self.assertTrue(result["hold"])
        self.assertEqual(result["reason"], "allow-policy-missing-approver")

        policy["approved_by"] = "Mircea Albulescu"
        policy["decision_receipt"] = "https://example.com/approval"
        result = evaluate_policy(policy)
        self.assertTrue(result["hold"])
        self.assertEqual(result["reason"], "allow-policy-missing-valid-decision-receipt")

        policy["decision_receipt"] = "https://github.com/usdimpact/usd-impact-pipeline/issues/155#issuecomment-1"
        result = evaluate_policy(policy)
        self.assertFalse(result["hold"])
        self.assertEqual(result["state"], "allow")

    def test_github_output_is_boolean_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "output"
            write_github_output(evaluate_policy(valid_policy()), path)
            values = dict(
                line.split("=", 1)
                for line in path.read_text(encoding="utf-8").splitlines()
            )
        self.assertEqual(values["hold"], "true")
        self.assertEqual(values["state"], "hold")
        self.assertEqual(values["issue"], ISSUE_URL)
        self.assertNotIn("\n", values["reason"])


if __name__ == "__main__":
    unittest.main()
