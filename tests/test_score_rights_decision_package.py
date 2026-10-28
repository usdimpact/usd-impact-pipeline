from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_score_rights_decision_package as validator

REPO_ROOT = Path(__file__).resolve().parents[1]


class ScoreRightsDecisionPackageTests(unittest.TestCase):
    def test_pending_package_validates_fail_closed(self) -> None:
        report = validator.validate(REPO_ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["rights_gate"], "hold")
        self.assertTrue(report["decision_required"])
        self.assertFalse(report["legal_conclusion_recorded"])
        self.assertEqual(report["provider_dispositions_pending"], 5)
        self.assertEqual(report["public_classes_pending"], 6)
        self.assertFalse(report["production_authorized"])
        self.assertFalse(report["real_provider_evidence_authorized"])
        self.assertFalse(report["public_replacement_authorized"])

    def test_receipt_schema_cannot_authorize_production(self) -> None:
        schema = json.loads(
            (REPO_ROOT / "governance/score-rights-decision-receipt.schema.json")
            .read_text(encoding="utf-8")
        )
        production = schema["properties"]["production_authorized"]
        self.assertEqual(production, {"const": False})

    def test_template_is_not_a_decision(self) -> None:
        template = json.loads(
            (REPO_ROOT / "governance/score-rights-decision-receipt.template.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(template["decision_status"], "hold")
        self.assertIsNone(template["decided_at_utc"])
        self.assertIsNone(template["decision_authority"])
        self.assertIsNone(template["authority_reference"])
        self.assertIsNone(template["approved_public_schema"])
        self.assertFalse(template["replication_claim_wording_approved"])
        self.assertFalse(template["archive_treatment_approved"])
        self.assertFalse(template["private_evidence_boundary_approved"])
        self.assertFalse(template["production_authorized"])
        self.assertTrue(
            all(item["treatment"] == "pending" for item in template["public_classes"].values())
        )
        self.assertTrue(
            all(item["status"] == "pending" for item in template["provider_dispositions"])
        )

    def test_matrix_requires_separate_production_authorization(self) -> None:
        matrix = json.loads(
            (REPO_ROOT / "governance/score-rights-decision-matrix.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(matrix["state"], "provider_counsel_decision_required")
        self.assertIsNone(matrix["legal_conclusion"])
        self.assertFalse(matrix["production_change_authorized"])
        self.assertFalse(matrix["engineering_evidence"]["production_migration_performed"])
        self.assertIn("separate_production_authorization", matrix["release_requires"])


if __name__ == "__main__":
    unittest.main()
