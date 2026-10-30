"""No-network, invented-only validation of the dormant Score public/retention packet.

Reads governance metadata, the *existing* versioned JSON schema, and the
already-inactive aggregate prototype. Does NOT read public Score file bodies,
connect to provider APIs, generate a real Score, or write publication files.
"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts import build_score_public_safe_artifact as aggregate

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "governance/score-v2-public-schema-retention-review-2026-10-30.json"
SCHEMA = ROOT / "schemas/score_public_safe.schema.json"
INVENTORY = ROOT / "governance/score-current-tree-exposure-inventory-2026-10-29.json"
RIGHTS = ROOT / "governance/score-publication-rights-gate.json"
RIGHTS_MATRIX = ROOT / "governance/score-rights-decision-matrix.json"
DOC = ROOT / "docs/score-v2-public-schema-retention-decision-packet-2026-10-30.md"

EXPECTED_ROOT = {
    "format", "review_date", "decision_state", "controlling_issues",
    "controlling_policy", "historical_metadata_inventory", "scope",
    "aggregate_candidate", "source_and_transport_distinction",
    "snapshot_counts", "inventory_categories", "open_decision_questions",
    "authorization_gates", "interpretation",
}

EXPECTED_QUESTIONS = {
    "upstream_owner_and_transport",
    "commercial_internal_calculation",
    "s_and_p_paid_license_or_separate_methodology",
    "aggregate_and_historical_derived_distribution",
    "methodology_and_attribution",
    "fred_services_api_storage_and_disposal",
    "fred_cryptographic_receipts_and_aggregate_retention",
    "public_git_old_history_and_releases",
    "cloudflare_cache_old_deployments_and_external_copies",
    "github_actions_logs_caches_and_backups",
    "ai_ml_use_and_restricted_provider_data",
    "lawful_private_evidence_storage_or_disposal",
    "reader_migration_and_methodology_reproduction_claims",
    "versioned_public_route_and_legal_safe_rollback",
}


def assert_draft_stays_closed(packet: dict) -> None:
    """Fail on any embedded approval, non-draft state or operational action."""
    if set(packet) != EXPECTED_ROOT:
        raise ValueError("unexpected review plan fields")
    if packet["format"] != "usd-impact-score-v2-public-schema-and-retention-review-v1":
        raise ValueError("unknown review manifest version")
    if packet["decision_state"] != "DRAFT_SYNTHETIC_ONLY_RIGHTS_HOLD":
        raise ValueError("non-HOLD review state")
    candidate = packet["aggregate_candidate"]
    if candidate["status"] != "PROTOTYPE_ONLY_NOT_LICENSE_CLEARED":
        raise ValueError("candidate silently activated")
    if candidate["public_url"] is not None:
        raise ValueError("candidate public URL must remain unset")
    for name in ("public_route_authorized", "production_builder_wired"):
        if candidate[name] is not False:
            raise ValueError("aggregate candidate active: " + name)
    if candidate["aggregate_is_not_automatically_license_safe"] is not True:
        raise ValueError("aggregate erroneously declared licensed")
    if candidate["s_and_p_paid_license_requirement_unfunded"] is not True:
        raise ValueError("upstream S&P budget blocker missing")
    for gate, allowed in packet["authorization_gates"].items():
        if allowed is not False:
            raise ValueError("authorization gate opened: " + gate)
    if not packet["authorization_gates"]:
        raise ValueError("no authorization gates")
    expected_scope = {
        "docs_only_and_synthetic_tests": True,
        "original_engine_modified": False,
        "research_engine_modified": False,
        "public_artifact_modified": False,
        "publication_workflow_modified": False,
        "production_configuration_modified": False,
        "real_provider_data_used": False,
        "provider_permission_granted": False,
    }
    if packet["scope"] != expected_scope:
        raise ValueError("scope unexpectedly expanded")
    if packet["source_and_transport_distinction"]["no_paid_license_budget_approved"] is not True:
        raise ValueError("unfunded license blocker removed")


class ScorePublicSchemaRetentionDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.packet = json.loads(PLAN.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))

    def test_authority_is_draft_hold_and_closed(self) -> None:
        assert_draft_stays_closed(self.packet)
        self.assertEqual(self.packet["review_date"], "2026-10-30")
        self.assertEqual(self.packet["controlling_policy"], "governance/score-publication-rights-gate.json")
        self.assertEqual(
            self.packet["historical_metadata_inventory"],
            "governance/score-current-tree-exposure-inventory-2026-10-29.json",
        )
        self.assertTrue(self.packet["controlling_issues"]["public_distribution"].endswith("/155"))
        self.assertTrue(self.packet["controlling_issues"]["historical_retention"].endswith("/282"))
        self.assertTrue(self.packet["controlling_issues"]["distinct_macro_panel"].endswith("/313"))

    def test_mutated_release_permission_or_public_url_is_rejected(self) -> None:
        for key in self.packet["authorization_gates"]:
            with self.subTest(gate=key):
                mutated = copy.deepcopy(self.packet)
                mutated["authorization_gates"][key] = True
                with self.assertRaisesRegex(ValueError, "gate opened"):
                    assert_draft_stays_closed(mutated)

        for bad in ("https://example.org/score.json", "", 123):
            with self.subTest(public_url=bad):
                mutated = copy.deepcopy(self.packet)
                mutated["aggregate_candidate"]["public_url"] = bad
                with self.assertRaisesRegex(ValueError, "public URL"):
                    assert_draft_stays_closed(mutated)

    def test_policy_and_existing_rights_matrix_still_hold(self) -> None:
        policy = json.loads(RIGHTS.read_text(encoding="utf-8"))
        rights_matrix = json.loads(RIGHTS_MATRIX.read_text(encoding="utf-8"))
        self.assertEqual(policy["state"], "hold")
        self.assertIsNone(policy["decision_receipt"])
        self.assertIsNone(policy["approved_by"])
        self.assertIs(rights_matrix["production_change_authorized"], False)
        self.assertIsNone(rights_matrix["legal_conclusion"])

    def test_candidate_schema_is_existing_version_not_new_live_contract(self) -> None:
        candidate = self.packet["aggregate_candidate"]
        self.assertEqual(candidate["schema"], "schemas/score_public_safe.schema.json")
        self.assertEqual(candidate["builder"], "scripts/build_score_public_safe_artifact.py")
        self.assertEqual(
            candidate["existing_synthetic_contract_tests"],
            "tests/test_score_public_safe_contract_synthetic.py",
        )
        self.assertEqual(candidate["schema_version"], aggregate.SCHEMA_VERSION)
        self.assertEqual(candidate["schema_id"], self.schema["$id"])
        self.assertEqual(self.schema["properties"]["schema_version"]["const"], aggregate.SCHEMA_VERSION)
        self.assertIn("INACTIVE", self.schema["title"])
        self.assertIs(self.schema["additionalProperties"], False)

    def test_closed_field_sets_exactly_mirror_prototype_schema_and_builder(self) -> None:
        proposed = self.packet["aggregate_candidate"]["proposal_field_sets"]
        schema = self.schema["properties"]
        expected = {
            "root": set(schema),
            "metadata": set(schema["metadata"]["properties"]),
            "latest": set(schema["latest"]["properties"]),
            "history_item": set(schema["history"]["items"]["properties"]),
            "release_evidence": set(schema["release_evidence"]["properties"]),
        }
        self.assertEqual(set(proposed), set(expected))
        for key, expected_fields in expected.items():
            with self.subTest(group=key):
                self.assertEqual(set(proposed[key]), expected_fields)
                self.assertEqual(len(proposed[key]), len(expected_fields))
        self.assertEqual(expected["root"], aggregate.ROOT_KEYS)
        self.assertEqual(expected["metadata"], aggregate.METADATA_KEYS)
        self.assertEqual(expected["latest"], aggregate.LATEST_KEYS)
        self.assertEqual(expected["history_item"], aggregate.ALLOWED_HISTORY_KEYS)
        self.assertEqual(expected["release_evidence"], aggregate.EVIDENCE_KEYS)
        for path in ("metadata", "latest", "release_evidence"):
            self.assertIs(schema[path]["additionalProperties"], False)
        self.assertIs(schema["history"]["items"]["additionalProperties"], False)

    def test_every_proposed_leaf_group_requires_rights_review(self) -> None:
        groups = self.packet["aggregate_candidate"]["proposed_field_groups"]
        seen: list[str] = []
        for group in groups:
            self.assertEqual(group["rights_review"], "PENDING")
            self.assertTrue(group["paths"])
            seen.extend(group["paths"])
        expected = {
            "schema_version",
            *("metadata." + f for f in self.packet["aggregate_candidate"]["proposal_field_sets"]["metadata"]),
            *("latest." + f for f in self.packet["aggregate_candidate"]["proposal_field_sets"]["latest"]),
            *("history[]." + f for f in self.packet["aggregate_candidate"]["proposal_field_sets"]["history_item"]),
            *("release_evidence." + f for f in self.packet["aggregate_candidate"]["proposal_field_sets"]["release_evidence"]),
        }
        self.assertEqual(set(seen), expected)
        self.assertEqual(len(seen), len(expected), "duplicate review field path")

    def test_forbidden_fields_cover_full_inactive_converter_guard(self) -> None:
        forbidden = self.packet["aggregate_candidate"]["forbidden_public_data_fields"]
        self.assertEqual(len(forbidden), len(set(forbidden)))
        self.assertTrue(aggregate.FORBIDDEN_KEYS.issubset(set(forbidden)))
        self.assertIn("component_zscore_revisions", forbidden)
        self.assertIn("driver_levels", forbidden)

    def test_count_only_class_c_inventory_matches_frozen_manifest(self) -> None:
        categories = {c["id"]: c for c in self.packet["inventory_categories"]}
        self.assertEqual(len(categories), len(self.packet["inventory_categories"]))
        a = self.inventory
        counts = self.packet["snapshot_counts"]
        self.assertEqual(counts["dated_class_c"], a["dated_archive"]["class_c_dated_file_count"])
        self.assertEqual(counts["latest_class_c"], len(a["current_public_data"]["class_c_paths"]))
        self.assertEqual(counts["current_tree_class_c_total"], a["current_tree_total_class_c_files"])
        self.assertEqual(
            counts["current_tree_class_c_total"],
            counts["dated_class_c"] + counts["latest_class_c"],
        )
        self.assertEqual(counts["current_tree_class_c_total"], 54)
        self.assertEqual(
            counts["dated_archive_directories"],
            a["dated_archive"]["directory_count"],
        )
        self.assertEqual(
            categories["latest_class_c"]["paths"],
            a["current_public_data"]["class_c_paths"],
        )
        self.assertEqual(
            sum(categories[key]["count"] for key in
                ("latest_class_c", "dated_score", "dated_weekly_input", "dated_reproduction")),
            54,
        )
        for key, archive_file in (
            ("dated_score", "score.json"),
            ("dated_weekly_input", "weekly_input.json"),
            ("dated_reproduction", "repro_bundle.json"),
        ):
            self.assertEqual(categories[key]["count"], a["dated_archive"]["file_counts"][archive_file])

    def test_non_class_c_inventory_matches_snapshot_without_opening_data(self) -> None:
        c = {item["id"]: item for item in self.packet["inventory_categories"]}
        a = self.inventory
        snapshot = self.packet["snapshot_counts"]
        self.assertEqual(
            c["git_only_weekly_bridges"]["count"],
            a["git_only_dated_weekly_bridges"]["count"],
        )
        self.assertEqual(
            snapshot["dated_html_en_es"],
            a["dated_archive"]["file_counts"]["en.html"] +
            a["dated_archive"]["file_counts"]["es.html"],
        )
        self.assertEqual(c["dated_archive_html"]["count"], snapshot["dated_html_en_es"])
        for cid, cls in (("research_d", "d"), ("research_e", "e"), ("research_f", "f")):
            self.assertEqual(
                c[cid]["paths"],
                a["current_public_data"]["class_" + cls + "_paths"],
            )
            self.assertEqual(snapshot["research_class_" + cls], c[cid]["count"])

    def test_unverified_copies_remain_unverified_and_no_disposal_authority(self) -> None:
        unknown = {
            "git_history_old_blobs",
            "cloudflare_deployments_cdn_and_previews",
            "github_actions_logs_artifacts_caches",
            "local_parquet_logs_and_runner_temporary",
            "private_storage_backups_external_clones",
        }
        categories = {c["id"]: c for c in self.packet["inventory_categories"]}
        for category in self.packet["inventory_categories"]:
            with self.subTest(category=category["id"]):
                self.assertTrue(category["disposition"].startswith("NO_"))
                self.assertIn(
                    category["evidence"],
                    {"CURRENT_TREE_PATHS", "PARTIAL_METADATA_ONLY", "SOURCE_PATHS_ONLY", "UNVERIFIED"},
                )
        for key in unknown:
            with self.subTest(unverified=key):
                self.assertIsNone(categories[key]["count"])
                self.assertNotEqual(categories[key]["evidence"], "CURRENT_TREE_PATHS")
        self.assertIs(self.packet["authorization_gates"]["historical_deletion_or_purge_allowed"], False)
        self.assertIs(self.packet["authorization_gates"]["public_artifact_mutation_allowed"], False)

    def test_source_owner_and_fred_transport_are_not_conflated(self) -> None:
        facts = self.packet["source_and_transport_distinction"]
        self.assertEqual(facts["current_treasury_transport"], "FRED_DGS2_DGS10")
        self.assertIn("H15", facts["treasury_h15_origin"])
        self.assertIs(facts["fred_public_domain_tag_not_storage_permission"], True)
        self.assertIs(facts["fred_retention_and_disposal_not_cleared"], True)
        self.assertIs(facts["no_direct_h15_substitution_approved"], True)

    def test_open_questions_are_unanswered_and_owners_are_named(self) -> None:
        questions = self.packet["open_decision_questions"]
        self.assertEqual({q["id"] for q in questions}, EXPECTED_QUESTIONS)
        self.assertEqual(len(questions), len(EXPECTED_QUESTIONS))
        for q in questions:
            with self.subTest(question=q["id"]):
                self.assertEqual(q["state"], "PENDING")
                self.assertIsNone(q["receipt"])
                self.assertIn(q["reviewer"], {
                    "PROVIDER_AND_COUNSEL", "OWNER_AND_COUNSEL", "TECHNICAL_REVIEW_AND_OWNER",
                })

    def test_only_invented_2099_history_is_processed_in_memory(self) -> None:
        # No live or historical Score file is loaded as a fixture.
        invented = {
            "metadata": {
                "pipeline": "usd_impact_score_v2",
                "generated_at_utc": None,
                "weights": dict(aggregate.EXPECTED_WEIGHTS),
            },
            "weeks": [
                {"date": "2099-01-02", "score": 0.31, "regime": "Firm dollar regime"},
                {"date": "2099-01-09", "score": -0.05, "regime": "Neutral / transitional"},
            ],
        }
        candidate = aggregate.build_public_safe_payload(invented)
        aggregate.assert_public_safe(candidate)
        self.assertEqual(len(candidate["history"]), 2)
        self.assertEqual(candidate["schema_version"], "score-public-v2-safe-1")
        self.assertNotIn("source_provenance", json.dumps(candidate))
        self.assertFalse(self.packet["authorization_gates"]["aggregate_distribution_cleared"])

        invalid = copy.deepcopy(candidate)
        invalid["history"][0]["weekly_level"] = 11.0  # invented marker only
        with self.assertRaisesRegex(ValueError, "forbidden keys"):
            aggregate.assert_public_safe(invalid)

    def test_owner_document_preserves_no_change_boundary(self) -> None:
        document = DOC.read_text(encoding="utf-8")
        self.assertIn("No provider permission", document)
        self.assertIn("54 Class C", document)
        self.assertIn("PENDING", document)
        self.assertIn("Production", document)
        self.assertIn("historical", document.lower())
        self.assertIn("score-public-v2-safe-1", document)


if __name__ == "__main__":
    unittest.main()
