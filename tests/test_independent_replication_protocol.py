import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "public" / "data" / "research" / "independent_replication_protocol.json"
DOC_PATH = ROOT / "docs" / "independent-replication-protocol.md"


class IndependentReplicationProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
        cls.doc = DOC_PATH.read_text(encoding="utf-8")

    def test_status_is_fail_closed_before_external_review(self):
        self.assertEqual(self.protocol["version"], 1)
        self.assertEqual(self.protocol["status"], "prepared_not_executed")
        self.assertFalse(self.protocol["independent_review_completed"])
        self.assertFalse(self.protocol["independent_validation_claim_allowed"])
        self.assertEqual(self.protocol["first_eligible_release_week"], "2026-08-28")

    def test_independence_excludes_first_party_attestations(self):
        criteria = " ".join(self.protocol["independence_criteria"])
        self.assertIn("does not satisfy the independence criterion", criteria)
        self.assertIn("CI", criteria)
        self.assertIn("post-merge attestation", criteria)
        self.assertIn("free to publish MATCH, MISMATCH, AMBIGUOUS or NOT_TESTABLE", criteria)

    def test_strict_release_eligibility_is_required(self):
        eligibility = self.protocol["release_eligibility"]
        self.assertEqual(eligibility["minimum_week_ending"], "2026-08-28")
        self.assertTrue(eligibility["requires_strict_reproduction_bundle"])
        self.assertTrue(eligibility["requires_latest_archive_bundle_identity"])
        self.assertTrue(eligibility["requires_main_post_merge_reproduction_attestation"])
        self.assertTrue(eligibility["requires_exact_release_commit"])
        self.assertTrue(eligibility["requires_requirements_lock_hash_in_bundle"])

    def test_review_materials_cover_frozen_contract(self):
        materials = {item["id"]: item for item in self.protocol["review_materials"]}
        required = {
            "methodology",
            "data_semantics",
            "strict_bundle_latest",
            "strict_bundle_archive",
            "score_json",
            "bridge",
            "dependency_lock",
            "reference_validator_secondary_only",
        }
        self.assertEqual(set(materials), required)
        self.assertEqual(materials["methodology"]["path"], "public/data/score_v2_methodology.json")
        self.assertEqual(materials["strict_bundle_latest"]["path"], "public/data/score_repro_bundle_latest.json")
        self.assertEqual(
            materials["strict_bundle_archive"]["path_template"],
            "public/archive/{week_ending}/score_repro_bundle.json",
        )
        self.assertEqual(materials["dependency_lock"]["path"], "requirements.lock")
        self.assertIn("secondary", materials["reference_validator_secondary_only"]["purpose"].lower())

    def test_primary_test_requires_independent_arithmetic(self):
        steps = " ".join(self.protocol["primary_replication_steps"])
        self.assertIn("Without importing usd_impact_score_v2.py", steps)
        self.assertIn("independently implement", steps)
        self.assertIn("eight drivers", steps)
        self.assertIn("unclipped z-score", steps)
        self.assertIn("signed fixed weight", steps)
        self.assertIn("regime thresholds", steps)
        self.assertIn("Optionally run USD Impact's reference validator only after", steps)

    def test_finding_classes_are_complete_and_non_binary(self):
        classes = {item["class"] for item in self.protocol["required_finding_classes"]}
        self.assertEqual(classes, {"MATCH", "MISMATCH", "AMBIGUOUS", "NOT_TESTABLE"})

    def test_claim_policy_separates_reproducibility_from_prediction(self):
        policy = self.protocol["claim_policy"]
        self.assertIn("protocol prepared", policy["before_external_report"])
        self.assertIn("does not establish predictive power", policy["after_external_report"])
        self.assertIn("preregistered prospective", policy["predictive_power"])
        self.assertIn("does not itself constitute independent review", self.protocol["scope"])

    def test_known_raw_data_boundary_is_explicit(self):
        boundary = self.protocol["known_boundary"]
        self.assertIn("complete raw Yahoo/FRED responses", boundary)
        self.assertIn("not publicly redistributed", boundary)
        self.assertIn("does not claim a complete independent reconstruction", boundary)

    def test_human_protocol_keeps_same_claim_boundary(self):
        self.assertIn("Status:** prepared, not executed", self.doc)
        self.assertIn("does **not** mean an independent review has occurred", self.doc)
        self.assertIn("cannot be relabeled as independent evidence", self.doc)
        self.assertIn("MATCH", self.doc)
        self.assertIn("MISMATCH", self.doc)
        self.assertIn("AMBIGUOUS", self.doc)
        self.assertIn("NOT_TESTABLE", self.doc)
        self.assertIn("does not establish predictive power", self.doc)


if __name__ == "__main__":
    unittest.main()
