"""Offline fail-closed review for the four-source exact-series rights matrix.

The test reads only repository policy metadata. It does not access federal
provider data, databases, credentials, services, releases, or market values.
"""

from __future__ import annotations

from datetime import date
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


def assert_h10_lineage_fail_closed(matrix: dict) -> None:
    """Reject unversioned 2019 H.10 identifiers, backcasts and hidden grants."""
    h10 = next(
        source for source in matrix["sources"]
        if source["id"] == "fed_h10_nominal_broad"
    )
    identity = h10["exact_series_identity"]
    history = identity["published_transition_history"]
    assert identity["publisher_native_series_key"] == "H10/H10/JRXWTFB_N.B"
    assert history["primary_source_url"] == (
        "https://www.federalreserve.gov/releases/h10/h10_technical_qa.htm"
    )
    assert history["mnemonic_current"] == "JRXWTFB_N"
    assert history["same_mnemonic_historically_reassigned"] is True
    assert history["legacy_mnemonic_through"] == "2019-02-03"
    assert history["legacy_mnemonic_semantics"] == "OLD_BROAD_GOODS_TRADE_ONLY"
    assert history["revised_mnemonic_effective"] == "2019-02-04"
    assert history["revised_mnemonic_semantics"] == "NEW_BROAD_GOODS_AND_SERVICES_TRADE"
    assert history["legacy_goods_only_alias"] == "V0.JRXWTFB_N"
    assert history["legacy_goods_only_updates_end"] == "2019-12-31"
    assert history["new_methodology_historical_estimates_back_to"] == "2006-01"
    assert history["daily_index_rebasing_effective"] == "2019-06-24"
    assert history["daily_base_before"] == "JANUARY_2_2006_EQUALS_100"
    assert history["daily_base_after"] == "JANUARY_2006_MONTHLY_AVERAGE_EQUALS_100"
    assert date.fromisoformat(history["legacy_mnemonic_through"]) < date.fromisoformat(
        history["revised_mnemonic_effective"]
    ) < date.fromisoformat(history["daily_index_rebasing_effective"])
    for risk in (
        "same_identifier_proves_economic_comparability",
        "historical_retroactive_dataset_proves_contemporaneous_availability",
        "original_as_published_vintages_verified",
        "historical_stitching_or_splicing_authorized",
        "real_data_access_approved",
    ):
        assert history[risk] is False, risk
    assert identity["units_or_base_fully_reconciled"] is False
    assert h10["transport"]["direct_access_to_real_data_approved"] is False


def assert_metadata_stays_research_only(matrix: dict) -> None:
    """Publisher docs may prove sample tags but never unlock a live data path."""
    review = matrix["metadata_reconciliation_2026_10_30"]
    assert review["state"] == "STATIC_PUBLISHER_DOCUMENTATION_ONLY"
    assert review["precise_treasury_live_response_verified"] is False
    assert review["precise_eia_api_route_or_history_parity_verified"] is False
    assert review["commercial_rights_reviewed_and_granted"] is False
    assert review["source_requests_performed"] is False
    assert review["real_observations_fetched_or_stored"] is False
    assert review["all_permissions_still_false"] is True
    assert review["source_modification_or_pipeline_switch_authorized"] is False
    assert review["production_release_authorized"] is False
    assert len(review["verified_docs"]) >= 4
    sources = {source["id"]: source for source in matrix["sources"]}
    for tenor, field in (
        ("treasury_direct_2yr_par", "BC_2YEAR"),
        ("treasury_direct_10yr_par", "BC_10YEAR"),
    ):
        source = sources[tenor]
        identity = source["exact_series_identity"]
        transport = source["transport"]
        assert identity["candidate_feed_field"] == field
        assert identity["candidate_feed_field_metadata_verified"] is True
        assert identity["feed_field_evidence_class"] == (
            "PUBLISHER_ILLUSTRATIVE_XML_SCHEMA_ONLY"
        )
        assert identity["feed_field_evidence_url"] == (
            "https://home.treasury.gov/system/files/276/yield-rates-xml.png"
        )
        assert identity["nominal_par_curve_example_odata_type"] == "Edm.Double"
        assert identity["publisher_native_series_key"] is None
        assert identity["native_key_verified_from_publisher_metadata"] is False
        assert identity["feed_field_runtime_presence_verified"] is False
        assert transport["exact_field_mapping_verified"] is False
        assert transport["live_response_or_vintage_verified"] is False
        assert transport["all_history_pagination_retrieval_authorized"] is False
        assert transport["release_receipt_collection_authorized"] is False
        assert transport["publisher_documented_zero_based_all_page_pagination"] is True
        assert transport["publisher_documented_missing_null_elements_omitted"] is True
        assert transport["direct_access_to_real_data_approved"] is False
    eia = sources["eia_crude_stocks_weekly"]
    categories = eia["exact_series_identity"]["publisher_documented_stock_categories"]
    assert categories["weekly_ending_stocks_excluding_spr_series"] == "WCESTUS1"
    assert categories["commercial_excluding_lease_stock_table"] == (
        "PET_STOC_WSTK_A_EPC0_SAX_MBBL_W"
    )
    assert categories["historical_commercial_including_lease_stock_table"] == (
        "PET_STOC_WSTK_A_EPC0_SAXL_MBBL_W"
    )
    assert categories["including_lease_stock_table_displayed_through_year"] == 2016
    assert categories["total_stocks_lease_exclusion_note_effective"] == "2005-01"
    assert categories["source_table_label_mapping_documented"] is True
    assert categories["exact_full_history_series_identity_or_vintage_parity_verified"] is False
    assert categories["old_lease_inclusive_series_equivalent_to_new_excluding_lease"] is False
    assert categories["crude_price_substitute"] is False
    assert eia["transport"]["official_machine_readable_product_verified"] is False
    assert eia["transport"]["legacy_wpsr_series_id_to_current_api_route_verified"] is False
    assert eia["transport"]["automated_retrieval_policy_documented"] is True
    assert eia["transport"]["excessive_bot_retrieval_permitted"] is False
    assert eia["transport"]["automated_retrieval_program_approved"] is False
    assert eia["cadence"]["exact_selected_source_first_publication_time_proven"] is False
    assert eia["transport"]["direct_access_to_real_data_approved"] is False


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
        for key, field, selector in [
            ("treasury_direct_2yr_par", "BC_2YEAR", "daily_treasury_yield_curve:2YR"),
            ("treasury_direct_10yr_par", "BC_10YEAR", "daily_treasury_yield_curve:10YR"),
        ]:
            with self.subTest(key=key):
                item = index[key]
                self.assertIsNone(
                    item["exact_series_identity"]["publisher_native_series_key"]
                )
                self.assertFalse(
                    item["exact_series_identity"]["native_key_verified_from_publisher_metadata"]
                )
                self.assertEqual(
                    item["exact_series_identity"]["internal_candidate_selector"], selector
                )
                self.assertEqual(
                    item["exact_series_identity"]["candidate_feed_field"], field
                )
                self.assertTrue(
                    item["exact_series_identity"]["candidate_feed_field_metadata_verified"]
                )
                self.assertEqual(
                    item["exact_series_identity"]["feed_field_evidence_class"],
                    "PUBLISHER_ILLUSTRATIVE_XML_SCHEMA_ONLY",
                )
                self.assertFalse(
                    item["exact_series_identity"]["feed_field_runtime_presence_verified"]
                )
                self.assertEqual(
                    item["exact_series_identity"]["nominal_par_curve_example_odata_type"],
                    "Edm.Double",
                )
                self.assertFalse(item["transport"]["exact_field_mapping_verified"])
                self.assertFalse(item["transport"]["live_response_or_vintage_verified"])
                self.assertFalse(item["transport"]["all_history_pagination_retrieval_authorized"])
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

    def test_h10_mnemonic_lineage_and_base_are_not_implicitly_equivalent(self) -> None:
        assert_h10_lineage_fail_closed(self.matrix)
        h10 = self.matrix["sources"][0]
        self.assertEqual(h10["id"], "fed_h10_nominal_broad")
        self.assertFalse(h10["permissions"]["public_history_distribution"])
        self.assertFalse(h10["permissions"]["live_source_retrieval"])

    def test_malformed_h10_transition_and_rights_claims_fail_closed(self) -> None:
        bad_cases = (
            ("same_mnemonic_historically_reassigned", False),
            ("same_identifier_proves_economic_comparability", True),
            ("historical_retroactive_dataset_proves_contemporaneous_availability", True),
            ("original_as_published_vintages_verified", True),
            ("historical_stitching_or_splicing_authorized", True),
            ("real_data_access_approved", True),
            ("daily_index_rebasing_effective", "2019-01-01"),
            ("legacy_goods_only_alias", "JRXWTFB_N"),
        )
        for key, fake_value in bad_cases:
            with self.subTest(key=key):
                bad = copy.deepcopy(self.matrix)
                bad["sources"][0]["exact_series_identity"][
                    "published_transition_history"
                ][key] = fake_value
                with self.assertRaises(AssertionError):
                    assert_h10_lineage_fail_closed(bad)

    def test_treasury_eia_official_metadata_does_not_grant_real_data_rights(self) -> None:
        assert_metadata_stays_research_only(self.matrix)
        assert_no_rights_granted(self.matrix)

    def test_metadata_grant_spoofing_is_rejected(self) -> None:
        for key in (
            "precise_treasury_live_response_verified",
            "precise_eia_api_route_or_history_parity_verified",
            "commercial_rights_reviewed_and_granted",
            "source_requests_performed",
            "real_observations_fetched_or_stored",
            "source_modification_or_pipeline_switch_authorized",
            "production_release_authorized",
        ):
            with self.subTest(flag=key):
                bad = copy.deepcopy(self.matrix)
                bad["metadata_reconciliation_2026_10_30"][key] = True
                with self.assertRaises(AssertionError):
                    assert_metadata_stays_research_only(bad)
        for source_id, field in (
            ("treasury_direct_2yr_par", "exact_field_mapping_verified"),
            ("treasury_direct_10yr_par", "release_receipt_collection_authorized"),
            ("eia_crude_stocks_weekly", "automated_retrieval_program_approved"),
        ):
            with self.subTest(source_id=source_id,flag=field):
                bad = copy.deepcopy(self.matrix)
                source = next(s for s in bad["sources"] if s["id"] == source_id)
                source["transport"][field] = True
                with self.assertRaises(AssertionError):
                    assert_metadata_stays_research_only(bad)
        bad = copy.deepcopy(self.matrix)
        bad["sources"][1]["exact_series_identity"][
            "publisher_documented_stock_categories"
        ]["old_lease_inclusive_series_equivalent_to_new_excluding_lease"] = True
        with self.assertRaises(AssertionError):
            assert_metadata_stays_research_only(bad)

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
