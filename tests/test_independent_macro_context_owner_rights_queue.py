"""No-network safeguards for the Macro Context Panel owner/counsel question queue.

The packet is a request for decisions only.  It cannot permit access to
observations, grant rights, publish the original Score, or authorize a new panel.
This suite reads static repository JSON/Markdown; no external modules/services.
"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "governance/independent-macro-context-owner-counsel-decision-queue-2026-10-30.json"
MATRIX = ROOT / "governance/score-four-source-exact-series-rights-matrix-2026-10-29.json"
MACRO = ROOT / "governance/independent-macro-context-fallback-draft-2026-10-30.json"
PHASE_B = ROOT / "governance/score-public-source-phase-b-design-2026-10-29.json"
LEGACY_GATE = ROOT / "governance/score-publication-rights-gate.json"
SUCCESSOR = ROOT / "governance/score-v2-successor-rights-readiness-2026-10-29.json"
MEMO = ROOT / "docs/independent-macro-context-counsel-owner-decision-packet-2026-10-30.md"

SOURCE_IDS = (
    "fed_h10_nominal_broad",
    "eia_crude_stocks_weekly",
    "treasury_direct_2yr_par",
    "treasury_direct_10yr_par",
)
RIGHTS_DIMENSIONS = frozenset(
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
CLOSED_ACTIONS = frozenset(
    {
        "new_provider_contact",
        "paid_license_or_subscription",
        "real_observation_get_or_head",
        "download_real_history_or_backtest",
        "commercial_internal_real_data_calculation",
        "real_data_storage_logs_cache_or_backups",
        "retained_first_seen_receipts",
        "new_supabase_or_external_database_writes",
        "web_scraping_or_polling",
        "switch_to_fred_or_h15",
        "source_adapter_or_model_formula_change",
        "change_existing_score_v1_v2_or_617_week_history",
        "publish_public_or_member_artifacts",
        "change_website_or_cloudflare_vercel_render_resend",
        "purge_or_rewrite_historical_git_pages_archives",
        "authorize_product_name_or_weights",
        "modify_active_rights_gate",
        "turn_on_production",
    }
)


# Pin the *route to review*, not only the Boolean HOLD values. Without these
# anchors a public question queue could silently point future reviewers to a
# different governance file, source, signoff role or approval gate while still
# asserting every literal authorization field is False.
EXPECTED_GOVERNING_RECORDS = {
    "exact_series_rights": "governance/score-four-source-exact-series-rights-matrix-2026-10-29.json",
    "independent_model_draft": "governance/independent-macro-context-fallback-draft-2026-10-30.json",
    "synthetic_phase_b": "governance/score-public-source-phase-b-design-2026-10-29.json",
    "active_legacy_score_gate": "governance/score-publication-rights-gate.json",
    "legacy_rights_successor": "governance/score-v2-successor-rights-readiness-2026-10-29.json",
    "fred_clauses": "governance/fred-terms-clause-crosswalk-2026-10-29.json",
}
EXPECTED_REVIEW_ROLES = (
    "PROJECT_OWNER",
    "SOURCE_OWNER_OR_RIGHTSHOLDER",
    "LEGAL_COUNSEL_OR_AUTHORIZED_RIGHTS_REVIEWER",
    "ENGINEERING_SECURITY",
    "EDUCATIONAL_COMPLIANCE",
)
EXPECTED_OWNER_DECISIONS = frozenset({
    "approve_distinct_product_direction",
    "approve_descriptive_three_dial_four_label_methodology",
    "approve_non_predictive_educational_framing",
    "approve_working_or_final_name",
    "approve_audience_public_vs_member",
    "approve_reporting_schedule_after_verified_wpsr_and_h10",
    "approve_missing_or_revised_data_HOLD_without_labels",
    "approve_explicit_public_schema_and_attributions",
    "approve_historical_first_seen_and_revision_protocol",
    "approve_independent_methodology_evaluation",
    "approve_one_off_rights_scoped_transport_proof",
    "approve_eventual_production_publication",
})
EXPECTED_GATE_NAMES = (
    "SOURCE_ORIGINAL_OWNER_AND_TRANSPORT_IDENTIFICATION",
    "SCOPED_REUSE_AND_COMMERCIAL_RIGHTS_DISPOSITION",
    "ARCHIVE_CACHE_LOG_AND_VINTAGE_RETENTION_DISPOSITION",
    "INDEPENDENT_OWNER_METHOD_DISPLAY_AND_SCHEDULE_DECISION",
    "NARROW_NONPRODUCTION_REAL_SOURCE_PROOF_APPROVAL",
    "PROSPECTIVE_AS_OF_AND_CORRECTION_VALIDATION",
    "INDEPENDENT_PUBLIC_RIGHTS_SCHEMA_SECURITY_COMPLIANCE",
    "SEPARATE_OWNER_PRODUCTION_RELEASE",
)
EXPECTED_SOURCE_FIELDS = frozenset({
    "original_publisher", "role", "display_name", "publisher_series_or_table",
    "publisher_identifier_status", "publisher_terms", "documented_facts",
    "priority_legal_questions", "priority_technical_questions", "missing_evidence",
    "id", "exact_permission_dimensions", "formal_source_or_counsel_rights_receipt",
    "project_owner_scoped_rights_decision_receipt", "source_rights_state",
    "source_license_cost_approval", "transport_test_approved",
})
EXPECTED_SOURCE_IDENTITIES = {
    "fed_h10_nominal_broad": (
        "Federal Reserve Board", "H10/H10/JRXWTFB_N.B",
        "DOCUMENTED_WITH_2019_SEMANTIC_BREAK",
        "H.10 nominal Broad Dollar Index",
        "Nominal trade-weighted Broad Dollar Index (not ICE DXY)",
        (
            "https://www.federalreserve.gov/disclaimer.htm",
            "https://www.federalreserve.gov/releases/h10/h10_technical_qa.htm",
            "https://www.federalreserve.gov/data/data-download-fred-information.htm",
        ),
    ),
    "eia_crude_stocks_weekly": (
        "U.S. Energy Information Administration", "WCESTUS1",
        "DOCUMENTED_LABEL_ONLY_CROSS_SERIES_PARITY_UNVERIFIED",
        "EIA weekly crude stocks excluding SPR",
        "Weekly commercial U.S. crude inventories excluding SPR; NOT WTI or futures",
        (
            "https://www.eia.gov/about/copyrights_reuse.php",
            "https://www.eia.gov/about/privacy_security_policy.php",
            "https://www.eia.gov/petroleum/supply/weekly/schedule.php",
        ),
    ),
    "treasury_direct_2yr_par": (
        "U.S. Department of the Treasury",
        "BC_2YEAR (official historical XML illustration)",
        "STATIC_SCHEMA_VERIFIED_LIVE_FIELD_AND_SERIES_ID_UNVERIFIED",
        "Treasury 2Y nominal par",
        "2Y nominal par constant-maturity yield, not FRED DGS2 transport",
        (
            "https://home.treasury.gov/treasury-daily-interest-rate-xml-feed",
            "https://catalog.data.gov/dataset/interest-rate-statistics-daily-treasury-yield-curve-rates",
            "https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology",
        ),
    ),
    "treasury_direct_10yr_par": (
        "U.S. Department of the Treasury",
        "BC_10YEAR (official historical XML illustration)",
        "STATIC_SCHEMA_VERIFIED_LIVE_FIELD_AND_SERIES_ID_UNVERIFIED",
        "Treasury 10Y nominal par",
        "10Y nominal par constant-maturity yield, not FRED DGS10 transport",
        (
            "https://home.treasury.gov/treasury-daily-interest-rate-xml-feed",
            "https://catalog.data.gov/dataset/interest-rate-statistics-daily-treasury-yield-curve-rates",
            "https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology",
        ),
    ),
}
EXPECTED_APPROVAL_RECEIPTS = frozenset({
    "exact_series_or_upstream", "counsel_retention", "owner_methodology",
    "one_off_transport", "public_output", "production",
})


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_queue_unapproved(queue: dict) -> None:
    """Raise AssertionError if the public packet misrepresents any grant."""
    assert queue["schema_version"] == "independent-macro-context-owner-counsel-review-queue-v1"
    assert queue["status"] == "REQUEST_FOR_DECISIONS_ONLY_NO_RELEASE_OR_EXECUTION"
    assert queue["non_authoritative"] is True
    assert queue["not_a_rights_grant"] is True
    assert queue["not_a_runtime_approval_source"] is True
    assert queue["canonical_rights_matrix_must_remain_denied"] is True
    assert queue["market_data_paid_budget_usd"] == 0
    assert queue["budget_policy"] == "ZERO_PAID_MARKET_DATA_LICENSE_BUDGET"
    assert queue["source_count"] == 4

    # Exact source identity, policy references, reviewer routing, and decision
    # gate *names* are part of the handoff contract. A count-only check is
    # insufficient: redirected controls could make an unchanged HOLD misleading.
    assert queue["controlling_issue"] == "https://github.com/usdimpact/usd-impact-pipeline/issues/313"
    assert queue["legacy_score_issue"] == "https://github.com/usdimpact/usd-impact-pipeline/issues/155"
    assert queue["fred_rights_issue"] == "https://github.com/usdimpact/usd-impact-pipeline/issues/282"
    assert queue["governing_records"] == EXPECTED_GOVERNING_RECORDS
    assert tuple(queue["review_roles"]) == EXPECTED_REVIEW_ROLES
    assert set(queue["owner_decision_prompts"]) == EXPECTED_OWNER_DECISIONS
    assert tuple(g["name"] for g in queue["gate_order"]) == EXPECTED_GATE_NAMES
    assert set(queue["approval_receipts"]) == EXPECTED_APPROVAL_RECEIPTS
    for source in queue["sources"]:
        assert set(source) == EXPECTED_SOURCE_FIELDS
        expected = EXPECTED_SOURCE_IDENTITIES[source["id"]]
        assert (
            source["original_publisher"],
            source["publisher_series_or_table"],
            source["publisher_identifier_status"],
            source["display_name"],
            source["role"],
            tuple(source["publisher_terms"]),
        ) == expected
    for owner_choice in queue["owner_decision_prompts"].values():
        assert set(owner_choice) == {"decision", "evidence_receipt", "authorization"}
    for gate in queue["gate_order"]:
        assert set(gate) == {"step", "name", "ready", "evidence"}
    assert tuple(s["id"] for s in queue["sources"]) == SOURCE_IDS
    assert set(queue["rights_decision_dimensions"]) == RIGHTS_DIMENSIONS
    for source in queue["sources"]:
        assert set(source["exact_permission_dimensions"]) == RIGHTS_DIMENSIONS
        assert all(
            disposition == "UNREVIEWED"
            for disposition in source["exact_permission_dimensions"].values()
        )
        assert source["source_rights_state"] == "NO_DECISION_NO_ACCESS"
        assert source["formal_source_or_counsel_rights_receipt"] is None
        assert source["project_owner_scoped_rights_decision_receipt"] is None
        assert source["source_license_cost_approval"] is False
        assert source["transport_test_approved"] is False
        assert len(source["priority_legal_questions"]) >= 3
        assert len(source["priority_technical_questions"]) >= 3
        assert len(source["missing_evidence"]) >= 3
        for url in source["publisher_terms"]:
            assert url.startswith("https://")
            assert url.split("/")[2] in {
                "www.federalreserve.gov", "www.eia.gov", "home.treasury.gov",
                "catalog.data.gov",
            }
    assert queue["separate_products"]["old_score_v2"]["status"] == "HOLD"
    assert queue["separate_products"]["old_score_v2"]["release_approved"] is False
    assert queue["separate_products"]["old_score_v2"]["original_eight_driver_methodology_unchanged"]
    assert queue["separate_products"]["old_score_v2"]["existing_score_history_may_be_spliced"] is False
    panel = queue["separate_products"]["proposed_panel"]
    assert panel["status"] == "SYNTHETIC_ONLY_DESIGN_HOLD"
    assert panel["distinct_three_dials_four_qualitative_labels"] is True
    assert panel["no_composite_score"] is True
    assert panel["no_weights_or_backtest"] is True
    assert panel["methodology_owner_approved"] is False
    assert panel["publication_approved"] is False
    assert len(queue["owner_decision_prompts"]) == 12
    for decision in queue["owner_decision_prompts"].values():
        assert decision["decision"] == "PENDING_OWNER"
        assert decision["evidence_receipt"] is None
        assert decision["authorization"] is False
    assert len(queue["gate_order"]) == 8
    for i, gate in enumerate(queue["gate_order"], start=1):
        assert gate["step"] == i
        assert gate["ready"] is False
        assert gate["evidence"]
    assert set(queue["external_actions_authorized"]) == CLOSED_ACTIONS
    assert all(x is False for x in queue["external_actions_authorized"].values())
    assert all(v is None for v in queue["approval_receipts"].values())
    assert queue["publication_status"] == "HOLD"
    assert queue["static_publisher_metadata_only"] is True
    assert queue["no_market_observation_values_copied"] is True
    assert queue["no_sender_messages_or_sales_case_reopen"] is True
    assert queue["publisher_docs_not_equal_to_signed_use_scope"] is True
    assert queue["decisions_are_not_guessed_from_federal_domain_or_cc0"] is True
    assert queue["private_correspondence_or_personal_identifiers_in_public_repo"] is False
    assert queue["signed_legal_opinions_in_public_repo"] is False
    assert queue["archived_historical_content_must_not_be_deleted_without_legal_preservation_plan"] is True


class MacroContextCounselOwnerQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.queue = read_json(QUEUE)
        cls.matrix = read_json(MATRIX)
        cls.macro = read_json(MACRO)
        cls.phase = read_json(PHASE_B)
        cls.legacy = read_json(LEGACY_GATE)
        cls.successor = read_json(SUCCESSOR)

    def test_question_queue_cannot_activate_any_source_or_product(self) -> None:
        check_queue_unapproved(self.queue)

    def test_canonical_four_source_rights_remain_denied(self) -> None:
        self.assertEqual(
            tuple(x["id"] for x in self.matrix["sources"]), SOURCE_IDS
        )
        self.assertEqual(
            tuple(self.macro["source_permissions"]), SOURCE_IDS
        )
        self.assertEqual(
            set(self.macro["permission_dimensions"]), RIGHTS_DIMENSIONS
        )
        for s in self.matrix["sources"]:
            with self.subTest(source=s["id"]):
                self.assertEqual(set(s["permissions"]), RIGHTS_DIMENSIONS)
                self.assertTrue(all(x is False for x in s["permissions"].values()))
                self.assertIsNone(s["provider_or_counsel_written_decision_receipt"])
                self.assertIsNone(s["project_owner_scope_approval_receipt"])
                self.assertTrue(
                    all(
                        x is False
                        for x in self.macro["source_permissions"][s["id"]]["rights"].values()
                    )
                )
        self.assertEqual(self.macro["status"], "SYNTHETIC_ONLY_DESIGN_HOLD")
        self.assertFalse(any(self.macro["external_authorities"].values()))
        self.assertEqual(self.macro["cost_policy"]["paid_market_data_budget_usd"], 0)
        self.assertFalse(self.macro["publication_control"]["production_authorized"])
        self.assertIsNone(self.macro["publication_control"]["owner_release_receipt"])

    def test_phase_b_and_original_score_are_independent_holds(self) -> None:
        self.assertEqual(self.phase["status"], "SYNTHETIC_DESIGN_REVIEW_ONLY_HOLD")
        self.assertTrue(all(x["cleared"] is False for x in self.phase["sources"]))
        self.assertFalse(self.phase["synthetic_contract"]["external_fetch_allowed"])
        self.assertFalse(self.phase["synthetic_contract"]["publish_authorized"])
        self.assertTrue(
            all(
                value is False
                for key, value in self.phase["decision"].items()
                if key.startswith("approve_")
            )
        )
        self.assertEqual(self.legacy["state"], "hold")
        self.assertIsNone(self.legacy["decision_receipt"])
        self.assertEqual(self.successor["state"], "DRAFT_ONLY_HOLD_NO_RUNTIME")
        self.assertEqual(self.successor["relationship_count"], 8)
        self.assertEqual(len(self.successor["permission_dimensions"]), 16)
        for relationship in self.successor["relationships"]:
            with self.subTest(relationship=relationship["id"]):
                self.assertEqual(len(relationship["rights"]), 16)
                self.assertTrue(all(x is False for x in relationship["rights"].values()))
        self.assertTrue(
            all(x is False for x in self.successor["external_authority_gates"].values())
        )
        self.assertTrue(
            all(x is False for x in self.successor["authorizations"].values())
        )

    def test_gate_order_prevents_early_real_source_proof(self) -> None:
        gates = {x["name"]: x for x in self.queue["gate_order"]}
        self.assertFalse(
            gates["NARROW_NONPRODUCTION_REAL_SOURCE_PROOF_APPROVAL"]["ready"]
        )
        self.assertFalse(gates["SEPARATE_OWNER_PRODUCTION_RELEASE"]["ready"])
        self.assertEqual(self.queue["owner_decision_prompts"][
            "approve_one_off_rights_scoped_transport_proof"
        ]["decision"], "PENDING_OWNER")
        self.assertFalse(self.queue["external_actions_authorized"]["real_observation_get_or_head"])
        self.assertFalse(self.queue["external_actions_authorized"]["retained_first_seen_receipts"])
        self.assertFalse(self.queue["external_actions_authorized"]["turn_on_production"])

    def test_source_scopes_avoid_bogus_parity_and_cross_licensing(self) -> None:
        sources = {x["id"]: x for x in self.queue["sources"]}
        self.assertIn("H10/H10/JRXWTFB_N.B", sources["fed_h10_nominal_broad"]["publisher_series_or_table"])
        self.assertEqual(sources["eia_crude_stocks_weekly"]["publisher_series_or_table"], "WCESTUS1")
        self.assertIn("BC_2YEAR", sources["treasury_direct_2yr_par"]["publisher_series_or_table"])
        self.assertIn("BC_10YEAR", sources["treasury_direct_10yr_par"]["publisher_series_or_table"])
        self.assertIn("not ICE DXY", sources["fed_h10_nominal_broad"]["role"])
        self.assertIn("NOT WTI", sources["eia_crude_stocks_weekly"]["role"])
        self.assertFalse(self.queue["external_actions_authorized"]["switch_to_fred_or_h15"])

    def test_document_is_usable_and_private_data_free(self) -> None:
        content = MEMO.read_text(encoding="utf-8")
        for needle in (
            "Fourteen independent questions",
            "Owner economic and educational decisions",
            "Legacy Score remains an independent",
            "HOLD",
            "WCESTUS1",
            "BC_2YEAR",
            "BC_10YEAR",
            "14 x 4",
            "FRED",
            "retention",
            "NO DATA GET/HEAD",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, content)
        for forbidden in ("sk-proj-", "ghp_", "SUPABASE_SERVICE_ROLE_KEY"):
            self.assertNotIn(forbidden, content)

    def test_fabricated_permission_cannot_be_registered(self) -> None:
        for source_id in SOURCE_IDS:
            for dimension in (
                "commercial_internal_ingestion",
                "provider_content_retention",
                "revision_vintage_receipt_retention",
                "public_aggregate_distribution",
                "live_source_retrieval",
            ):
                with self.subTest(source_id=source_id,dimension=dimension):
                    bad = copy.deepcopy(self.queue)
                    item = next(x for x in bad["sources"] if x["id"] == source_id)
                    item["exact_permission_dimensions"][dimension] = "ALLOW"
                    with self.assertRaises(AssertionError):
                        check_queue_unapproved(bad)

    def test_fabricated_approvals_and_costs_fail(self) -> None:
        changes = (
            ("market_data_paid_budget_usd", 100),
            ("non_authoritative", False),
            ("not_a_runtime_approval_source", False),
            ("publication_status", "READY"),
            ("no_sender_messages_or_sales_case_reopen", False),
            ("no_market_observation_values_copied", False),
        )
        for key, value in changes:
            with self.subTest(key=key):
                bad = copy.deepcopy(self.queue)
                bad[key] = value
                with self.assertRaises(AssertionError):
                    check_queue_unapproved(bad)

    def test_fabricated_receipt_transport_or_owner_decision_fails(self) -> None:
        bad = copy.deepcopy(self.queue)
        bad["sources"][0]["formal_source_or_counsel_rights_receipt"] = "fabricated"
        with self.assertRaises(AssertionError):
            check_queue_unapproved(bad)
        bad = copy.deepcopy(self.queue)
        bad["sources"][1]["transport_test_approved"] = True
        with self.assertRaises(AssertionError):
            check_queue_unapproved(bad)
        bad = copy.deepcopy(self.queue)
        bad["owner_decision_prompts"]["approve_distinct_product_direction"][
            "decision"
        ] = "APPROVED"
        with self.assertRaises(AssertionError):
            check_queue_unapproved(bad)
        bad = copy.deepcopy(self.queue)
        bad["gate_order"][0]["ready"] = True
        with self.assertRaises(AssertionError):
            check_queue_unapproved(bad)

    def test_any_premature_external_action_is_detected(self) -> None:
        for name in CLOSED_ACTIONS:
            bad = copy.deepcopy(self.queue)
            bad["external_actions_authorized"][name] = True
            with self.subTest(name=name):
                with self.assertRaises(AssertionError):
                    check_queue_unapproved(bad)

    def test_source_spoofing_or_missing_right_cannot_pass(self) -> None:
        bad = copy.deepcopy(self.queue)
        bad["sources"][0]["id"] = "ice_dxy"
        with self.assertRaises(AssertionError):
            check_queue_unapproved(bad)
        bad = copy.deepcopy(self.queue)
        del bad["sources"][0]["exact_permission_dimensions"]["public_history_distribution"]
        with self.assertRaises(AssertionError):
            check_queue_unapproved(bad)
        bad = copy.deepcopy(self.queue)
        bad["source_count"] = 5
        with self.assertRaises(AssertionError):
            check_queue_unapproved(bad)


    def test_review_routing_or_governing_file_cannot_be_redirected(self) -> None:
        mutations = (
            lambda q: q["governing_records"].update(
                active_legacy_score_gate="governance/fake-rights-gate.json"
            ),
            lambda q: q.update(
                controlling_issue="https://github.com/usdimpact/usd-impact-pipeline/issues/1"
            ),
            lambda q: q["review_roles"].__setitem__(2, "ENGINEERING_ONLY"),
            lambda q: q["gate_order"][1].update(name="RIGHTS_AUTO_APPROVED"),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                altered = copy.deepcopy(self.queue)
                mutate(altered)
                with self.assertRaises(AssertionError):
                    check_queue_unapproved(altered)

    def test_source_identifiers_and_policy_links_cannot_be_swapped(self) -> None:
        mutations = (
            (0, "publisher_series_or_table", "DXY_INDEX"),
            (0, "publisher_identifier_status", "LIVE_FULLY_RIGHTS_CLEARED"),
            (1, "role", "WTI futures closing prices"),
            (2, "display_name", "FRED DGS2 official value"),
            (1, "publisher_series_or_table", "WTI_SPOT_PRICE"),
            (2, "publisher_series_or_table", "FRED_DGS2"),
            (3, "original_publisher", "FRED"),
        )
        for index, field, value in mutations:
            with self.subTest(index=index, field=field):
                altered = copy.deepcopy(self.queue)
                altered["sources"][index][field] = value
                with self.assertRaises(AssertionError):
                    check_queue_unapproved(altered)
        altered = copy.deepcopy(self.queue)
        altered["sources"][1]["publisher_terms"][0] = (
            "https://www.eia.gov/about/some-other-policy.php"
        )
        with self.assertRaises(AssertionError):
            check_queue_unapproved(altered)
        altered = copy.deepcopy(self.queue)
        altered["sources"][0]["public_release_authorized"] = True
        with self.assertRaises(AssertionError):
            check_queue_unapproved(altered)

    def test_decision_identity_and_approval_receipt_schema_cannot_be_expanded(self) -> None:
        altered = copy.deepcopy(self.queue)
        original = altered["owner_decision_prompts"].pop(
            "approve_eventual_production_publication"
        )
        altered["owner_decision_prompts"]["approve_instant_auto_release"] = original
        with self.assertRaises(AssertionError):
            check_queue_unapproved(altered)
        altered = copy.deepcopy(self.queue)
        altered["approval_receipts"]["automatic_allowance"] = "UNKNOWN"
        with self.assertRaises(AssertionError):
            check_queue_unapproved(altered)
        altered = copy.deepcopy(self.queue)
        altered["owner_decision_prompts"]["approve_distinct_product_direction"][
            "implicit_authorization"
        ] = True
        with self.assertRaises(AssertionError):
            check_queue_unapproved(altered)
        altered = copy.deepcopy(self.queue)
        altered["gate_order"][7]["release_now"] = True
        with self.assertRaises(AssertionError):
            check_queue_unapproved(altered)

    def test_zero_budget_and_current_rights_are_independent(self) -> None:
        self.assertEqual(self.queue["market_data_paid_budget_usd"], 0)
        self.assertTrue(self.macro["cost_policy"]["no_license_purchase"])
        self.assertFalse(self.queue["separate_products"]["proposed_panel"]["publication_approved"])
        self.assertFalse(self.matrix["product_boundary"]["proposed_distinct_four_signal_study"]["rights_cleared"])
        self.assertFalse(self.matrix["product_boundary"]["legacy_eight_driver_score"]["rights_cleared"])


if __name__ == "__main__":
    unittest.main()
