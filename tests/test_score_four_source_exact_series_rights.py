"""Offline fail-closed review for the four-source exact-series rights matrix.

The test reads only repository policy metadata. It does not access federal
provider data, databases, credentials, services, releases, or market values.
"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = (
    ROOT / "governance/score-four-source-exact-series-rights-matrix-2026-10-29.json"
)
BASE_PATH = ROOT / "governance/score-public-source-phase-b-design-2026-10-29.json"
SCORE_GATE_PATH = ROOT / "governance/score-publication-rights-gate.json"
SOURCE_IDS = (
    "fed_h10_nominal_broad",
    "eia_crude_stocks_weekly",
    "treasury_direct_2yr_par",
    "treasury_direct_10yr_par",
)
PERMISSION_DIMENSIONS = frozenset(
    {
        "commercial_internal_ingestion",
        "commercial_non_display_transformation",
        "transient_processing",
        "provider_content_retention",
        "observations_archival",
        "logs_and_cache_retention",
        "backup_and_disaster_recovery_retention",
        "revision_vintage_receipt_retention",
        "public_aggregate_distribution",
        "public_component_distribution",
        "public_history_distribution",
        "ai_ml_processing",
        "downstream_redistribution",
        "live_source_retrieval",
    }
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_no_rights_granted(matrix: dict) -> None:
    """Fail if any exact-source product or permission is silently unlocked."""
    assert matrix["prepared_status"] == "PUBLISHER_METADATA_RESEARCH_ONLY_HOLD"
    assert matrix["decision_policy"]["default"] == "DENY"
    assert matrix["decision_policy"]["no_live_download_or_database_writes"] is True
    assert matrix["product_boundary"]["legacy_eight_driver_score"]["rights_state"] == "HOLD"
    assert (
        matrix["product_boundary"]["proposed_distinct_four_signal_study"][
            "rights_state"
        ]
        == "SYNTHETIC_ONLY_RESEARCH_HOLD"
    )
    for product in matrix["product_boundary"].values():
        for field, value in product.items():
            if field.endswith("_approved") or field.endswith("_authorized") or (
                field == "rights_cleared"
            ):
                assert value is False, field
    assert [s["id"] for s in matrix["sources"]] == list(SOURCE_IDS)
    for source in matrix["sources"]:
        assert set(source["permissions"]) == PERMISSION_DIMENSIONS
        assert all(value is False for value in source["permissions"].values())
        assert source["provider_or_counsel_written_decision_receipt"] is None
        assert source["project_owner_scope_approval_receipt"] is None
        assert source["disposition"] == "EVIDENCE_REVIEW_ONLY_DENY_UNTIL_EXPLICIT_SIGNOFF"
        assert source["transport"]["direct_access_to_real_data_approved"] is False
        assert source["rights_evidence"]["exact_series_clearance"] is False
        assert source["rights_evidence"]["upstream_contributors_audited"] is False
        assert source["rights_evidence"]["proprietary_input_exceptions_excluded"] is False
        assert not source["cadence"]["actual_first_publication_receipt_verified"]
        assert not source["cadence"]["version_first_seen_receipt_verified"]


class FourSourceExactSeriesRightsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = read_json(MATRIX_PATH)
        cls.phase_b = read_json(BASE_PATH)
        cls.score_gate = read_json(SCORE_GATE_PATH)

    def test_exact_series_fail_closed_and_no_approval_receipts(self) -> None:
        assert_no_rights_granted(self.matrix)
        self.assertEqual(self.matrix["source_count"], 4)
        self.assertEqual(
            set(self.matrix["decision_policy"]["permission_dimensions"]),
            PERMISSION_DIMENSIONS,
        )
        self.assertEqual(len(self.matrix["decision_policy"]["permission_dimensions"]), 14)
        self.assertTrue(self.matrix["decision_policy"]["no_implicit_approval_from_public_domain_or_cc0"])
        self.assertTrue(self.matrix["decision_policy"]["rights_grant_requires_exact_series_source_transport_upstream_and_output_scope"])
        self.assertTrue(self.matrix["decision_policy"]["project_owner_permission_required_separately"])
        self.assertTrue(self.matrix["decision_policy"]["explicit_signed_source_or_counsel_disposition_required"])

    def test_consistent_with_phase_b_and_legacy_publication_hold(self) -> None:
        self.assertEqual(
            [s["id"] for s in self.matrix["sources"]],
            self.phase_b["synthetic_contract"]["required_source_ids"],
        )
        self.assertEqual(self.phase_b["status"], "SYNTHETIC_DESIGN_REVIEW_ONLY_HOLD")
        self.assertFalse(self.phase_b["synthetic_contract"]["external_fetch_allowed"])
        self.assertFalse(self.phase_b["synthetic_contract"]["publish_authorized"])
        self.assertTrue(all(not s["cleared"] for s in self.phase_b["sources"]))
        self.assertTrue(
            all(
                value is False
                for key, value in self.phase_b["decision"].items()
                if key.startswith("approve_")
            )
        )
        self.assertEqual(self.score_gate["state"], "hold")
        self.assertIsNone(self.score_gate["decision_receipt"])
        self.assertFalse(
            self.matrix["product_boundary"]["legacy_eight_driver_score"][
                "rights_cleared"
            ]
        )

    def test_identity_evidence_is_not_live_transport_permission(self) -> None:
        index = {s["id"]: s for s in self.matrix["sources"]}
        self.assertEqual(
            index["fed_h10_nominal_broad"]["exact_series_identity"][
                "publisher_native_series_key"
            ],
            "H10/H10/JRXWTFB_N.B",
        )
        self.assertFalse(
            index["fed_h10_nominal_broad"]["exact_series_identity"][
                "units_or_base_fully_reconciled"
            ]
        )
        self.assertFalse(
            index["fed_h10_nominal_broad"]["transport"][
                "automated_post_ddp_transport_verified"
            ]
        )
        self.assertEqual(
            index["eia_crude_stocks_weekly"]["exact_series_identity"][
                "publisher_native_series_key"
            ],
            "WCESTUS1",
        )
        self.assertTrue(
            index["eia_crude_stocks_weekly"]["exact_series_identity"]["excludes_spr"]
        )
        self.assertFalse(
            index["eia_crude_stocks_weekly"]["transport"][
                "official_machine_readable_product_verified"
            ]
        )
        for key, field in [
            ("treasury_direct_2yr_par", "BC_2YEAR"),
            ("treasury_direct_10yr_par", "BC_10YEAR"),
        ]:
            with self.subTest(key=key):
                item = index[key]
                self.assertEqual(
                    item["exact_series_identity"]["candidate_feed_field"], field
                )
                self.assertFalse(
                    item["exact_series_identity"]["candidate_feed_field_metadata_verified"]
                )
                self.assertFalse(item["transport"]["exact_field_mapping_verified"])
                self.assertEqual(
                    item["transport"]["fred_transport_option"],
                    "SEPARATE_RIGHTS_GATE_UNAUTHORIZED",
                )
                self.assertEqual(
                    item["transport"]["official_feed_key"], "daily_treasury_yield_curve"
                )
        self.assertEqual(
            index["treasury_direct_2yr_par"]["exact_series_identity"][
                "requires_same_curve_snapshot_as"
            ],
            "treasury_direct_10yr_par",
        )
        self.assertEqual(
            index["treasury_direct_10yr_par"]["exact_series_identity"][
                "requires_same_curve_snapshot_as"
            ],
            "treasury_direct_2yr_par",
        )

    def test_all_reference_links_are_publisher_grounds_or_transport_policy(self) -> None:
        for source in self.matrix["sources"]:
            self.assertGreaterEqual(len(source["evidence"]), 4)
            self.assertGreaterEqual(len(source["unresolved"]), 3)
            for proof in source["evidence"]:
                with self.subTest(source=source["id"], topic=proof["topic"]):
                    self.assertTrue(proof["url"].startswith("https://"))
                    self.assertTrue(
                        proof["url"].split("/")[2]
                        in {
                            "www.federalreserve.gov",
                            "www.eia.gov",
                            "home.treasury.gov",
                            "catalog.data.gov",
                            "fred.stlouisfed.org",
                        }
                    )
            self.assertNotIn("approved: true", str(source["permissions"]))

    def test_negative_permission_grants_are_detected_offline(self) -> None:
        for bad_field in [
            "commercial_internal_ingestion",
            "provider_content_retention",
            "public_aggregate_distribution",
            "live_source_retrieval",
        ]:
            bad = copy.deepcopy(self.matrix)
            bad["sources"][0]["permissions"][bad_field] = True
            with self.subTest(bad_field=bad_field):
                with self.assertRaises(AssertionError):
                    assert_no_rights_granted(bad)
        bad_receipt = copy.deepcopy(self.matrix)
        bad_receipt["sources"][1]["project_owner_scope_approval_receipt"] = "invented"
        with self.assertRaises(AssertionError):
            assert_no_rights_granted(bad_receipt)

    def test_policy_is_data_only_not_a_market_observation_fixture(self) -> None:
        matrix_text = MATRIX_PATH.read_text(encoding="utf-8")
        self.assertNotIn("SYNTHETIC:", matrix_text)
        self.assertNotIn('"approved": true', matrix_text)
        self.assertNotIn('"cleared": true', matrix_text)
        self.assertNotIn('"real_source_fetch_approved": true', matrix_text)


if __name__ == "__main__":
    unittest.main()
