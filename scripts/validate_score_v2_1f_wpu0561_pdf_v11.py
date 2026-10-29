#!/usr/bin/env python3
"""Validate inert BLS PDF v11 design and exercise metadata-only synthetic layout rules.

This module CANNOT retrieve or parse PDFs. It imports no network, PDF or OCR packages.
The synthetic evaluator is a design contract test, not a live preflight or identity proof.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DESIGN = Path("governance/score-v2-1f-bls-wpu0561-pdf-structural-preflight-v11-design.json")
PDF_URL = "https://www.bls.gov/ppi/detailed-report/ppi-detailed-report-april-2026.pdf"
PDF_PATH = "/ppi/detailed-report/ppi-detailed-report-april-2026.pdf"
BASELINE = "0c420f495e6196d34d195d441edf7b707da4f35a"
TABLE_TITLE = "Table 9. Producer price indexes for commodity and service groupings and individual items"
FIELDS = frozenset({
    "fixture_kind", "source_url", "publisher", "reference_month",
    "claimed_release_date", "document_vintage_status", "table_title",
    "table_title_count", "governing_header_roles", "direct_commodity_candidate_count",
    "concept_label", "concept_scope", "identifier_proof", "target_period_columns",
    "target_month", "target_adjustment", "index_basis_status", "revision_status",
    "pdf_extracted", "values_included",
})


def _load(root: Path) -> dict[str, Any]:
    parsed = json.loads((root / DESIGN).read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("v11 design must be a JSON object")
    return parsed


def validate_design(root: Path | None = None) -> dict[str, Any]:
    """Fail closed if v11 ever becomes an executable/authorized contract by accident."""
    document = _load((root or ROOT).resolve())
    if document.get("version") != 11 or document.get("status") != "draft_pre_registration_hold":
        raise RuntimeError("v11 draft-only HOLD changed")
    if document.get("decision_kind") != "design_only_preflight_not_live_authorization":
        raise RuntimeError("v11 design-only decision kind changed")
    if document.get("protected_main_baseline") != BASELINE:
        raise RuntimeError("v9 baseline changed")
    if document.get("authoritative_methodology_design_version") != 9:
        raise RuntimeError("cannot supersede authoritative v9")
    if document.get("authoritative_live_contract_version") != 21:
        raise RuntimeError("cannot supersede v9 live contract")
    if document.get("v8_consumed_run") != (
        "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40901086765"
    ):
        raise RuntimeError("consumed run provenance changed")
    if document.get("prior_requests_consumed") != 2:
        raise RuntimeError("the previous request budget is consumed")

    owner = document.get("owner_approval", {})
    if owner.get("scope") != "design_only_and_recovery_workflows":
        raise RuntimeError("owner design-only approval broadened")
    if any(owner.get(k) is not False for k in (
        "source_boundary_adoption", "live_structural_preflight", "identifier_read",
        "economic_value_read", "production",
    )):
        raise RuntimeError("source adoption / live work remains unauthorized")

    candidate = document.get("source_candidate", {})
    if candidate.get("canonical_url") != PDF_URL or candidate.get("canonical_path") != PDF_PATH:
        raise RuntimeError("exact PDF URL changed")
    if candidate.get("canonical_hostname") != "www.bls.gov" or candidate.get("canonical_scheme") != "https":
        raise RuntimeError("candidate host/protocol changed")
    if candidate.get("reference_month") != "2026-04":
        raise RuntimeError("reference month changed")
    if candidate.get("original_release_date_context") != "2026-05-13":
        raise RuntimeError("news release date changed")
    if candidate.get("target_table_title") != TABLE_TITLE:
        raise RuntimeError("Table 9 description changed")
    if candidate.get("target_series_known_from_prior_evidence") != "WPU0561":
        raise RuntimeError("frozen identity reference changed")
    if candidate.get("target_label_scope") != "Crude petroleum":
        raise RuntimeError("exact target label changed")
    if candidate.get("observation_adjustment") != "unadjusted":
        raise RuntimeError("unadjusted field requirement changed")
    if candidate.get("observation_month_approved") != "2026-04":
        raise RuntimeError("observation month changed")
    if candidate.get("pdf_sha256") is not None:
        raise RuntimeError("PDF was not retrieved; digest must be absent")
    for k in (
        "pdf_retrieved", "pdf_http_status_checked", "content_type_checked",
        "content_length_checked", "first_publication_pdf_vintage_proven",
        "april_2026_table9_title_observed", "april_2026_index_level_schema_observed",
        "series_identity_observed_in_pdf", "domestic_production_alias_approved",
        "actual_original_release_level_observed", "eligible_for_adoption",
    ):
        if candidate.get(k) is not False:
            raise RuntimeError(f"unauthorized PDF/identity state: {k}")

    future = document.get("preflight_plan_if_separately_approved", {})
    if future.get("state") != "proposal_only_not_executable":
        raise RuntimeError("v11 plan became executable")
    if future.get("host_allowlist") != ["www.bls.gov"]:
        raise RuntimeError("host allowlist changed")
    if future.get("exact_path_allowlist") != [PDF_PATH]:
        raise RuntimeError("source path allowlist changed")
    if future.get("http_method_candidate") != "GET" or future.get("potential_max_requests") != 1:
        raise RuntimeError("proposed one-request GET budget changed")
    if future.get("concurrency") != 1 or future.get("retries") != 0 or future.get("redirects") != "reject":
        raise RuntimeError("network fail-closed design changed")
    if future.get("http_401_403_429_or_challenge") != "global_stop":
        raise RuntimeError("response/challenge stop policy changed")
    for name, max_v in (
        ("max_response_bytes", 10485760), ("max_pdf_pages", 200),
        ("max_scanned_table_titles", 12), ("max_retained_sanitized_header_tokens", 96),
        ("max_retained_sanitized_candidate_labels", 4),
    ):
        value = future.get(name)
        if type(value) is not int or value < 1 or value > max_v:
            raise RuntimeError(f"preflight bounds changed: {name}")
    for name in ("max_retained_economic_cells", "max_retained_numeric_identifier_values"):
        if type(future.get(name)) is not int or future[name] != 0:
            raise RuntimeError(f"numeric persistence must remain zero: {name}")
    for name in (
        "response_body_persistence", "pdf_file_persistence", "pdf_text_persistence",
        "raw_request_logs_with_response_content", "source_fallback",
        "dynamic_source_substitution", "runtime_code_exists",
        "request_execution_receipt_exists", "request_dispatch_marker_exists",
    ):
        if future.get(name) is not False:
            raise RuntimeError(f"unsafe preflight activation: {name}")
    if future.get("parser_dependency_lock") != "not_selected":
        raise RuntimeError("parser not yet reviewed")
    if future.get("execution_image_digest") != "not_selected":
        raise RuntimeError("runtime not yet reviewed")
    if future.get("ocr") != "forbidden_until_separately_reviewed":
        raise RuntimeError("OCR gate relaxed")
    if future.get("preserve_process_memory_only") != "requires_independent_security_review":
        raise RuntimeError("transient PDF data exposure is not approved")

    auth = document.get("current_execution_authorization", {})
    if set(auth) != {
        "pdf_http_request", "html_archive_refetch", "pdf_download", "pdf_parse",
        "identifier_value_read", "economic_value_read", "source_substitution",
        "alternate_source", "score_reconstruction", "score_calculation",
        "research_ledger_write", "public_artifact_change", "production_change",
    } or any(v is not False for v in auth.values()):
        raise RuntimeError("current v11 execution authorization is nonzero")
    rights = document.get("rights_and_release_holds", {})
    if rights.get("issue155") != "hold" or rights.get("score_v2_1f") != "hold":
        raise RuntimeError("publication rights and Score HOLD must remain")
    if any(rights.get(k) is not False for k in (
        "public_artifact_write", "research_ledger_mutation", "production",
    )):
        raise RuntimeError("rights/research/Production output activated")
    phases = document.get("stages", [])
    if [x.get("id") for x in phases] != ["M0", "M1", "M2", "M3", "M4", "M5", "M6"]:
        raise RuntimeError("stages changed")
    if any(x.get("network_pdf_authorized") is not False or x.get("economic_value_read") is not False for x in phases):
        raise RuntimeError("no workflow stage may authorize PDF/economic work")
    if any(x.get("status") not in (
        "verified_html_anchor_only", "approved_design_only_2026_10_29",
        "hold", "not_authorized"
    ) for x in phases):
        raise RuntimeError("unapproved workflow stage status")
    return {
        "status": "passed",
        "design_version": 11,
        "state": "draft_pre_registration_hold",
        "existing_methodology_version": 9,
        "existing_live_contract_version": 21,
        "pdf_fetched": False,
        "synthetic_only": True,
        "live_request_authorized": False,
        "identifier_read_authorized": False,
        "economic_read_authorized": False,
        "score_authorized": False,
        "production_authorized": False,
    }


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def classify_synthetic_layout(facts: Any) -> dict[str, Any]:
    """Evaluate invented structured labels only; never accept PDF bytes, pages, or values."""
    reasons: list[str] = []
    if not isinstance(facts, dict):
        return {"status": "hold", "reasons": ["not_a_synthetic_metadata_object"], "live_approval": False}
    if set(facts) != FIELDS:
        reasons.append("unexpected_or_missing_fields")
    if facts.get("fixture_kind") != "synthetic_metadata_only":
        reasons.append("non_synthetic_input")
    if facts.get("source_url") != PDF_URL or facts.get("publisher") != "BLS":
        reasons.append("source_mismatch")
    if facts.get("reference_month") != "2026-04" or facts.get("target_month") != "2026-04":
        reasons.append("target_month_mismatch")
    if facts.get("claimed_release_date") != "2026-05-13":
        reasons.append("release_date_mismatch")
    if facts.get("document_vintage_status") != "synthetic_original_edition":
        reasons.append("edition_unverified")
    if facts.get("table_title_count") != 1 or type(facts.get("table_title_count")) is not int:
        reasons.append("table_title_ambiguous")
    if not isinstance(facts.get("table_title"), str) or _norm(facts["table_title"]) != _norm(TABLE_TITLE):
        reasons.append("wrong_table_title")
    header_roles = facts.get("governing_header_roles")
    if (
        not isinstance(header_roles, list)
        or any(not isinstance(v, str) for v in header_roles)
        or len(header_roles) != len(set(header_roles))
        or not {"commodity_identity", "unadjusted_index_level"}.issubset(header_roles)
        or any(v not in {"commodity_identity", "unadjusted_index_level", "percent_change"} for v in header_roles)
    ):
        reasons.append("missing_ambiguous_or_unsupported_governing_header")
    if type(facts.get("direct_commodity_candidate_count")) is not int or facts["direct_commodity_candidate_count"] != 1:
        reasons.append("candidate_count_not_unique")
    if facts.get("concept_scope") != "direct_commodity":
        reasons.append("not_direct_commodity")
    if not isinstance(facts.get("concept_label"), str) or _norm(facts["concept_label"]) != "crude petroleum":
        reasons.append("concept_label_not_exact")
    if facts.get("identifier_proof") != "synthetic_placeholder_only":
        reasons.append("numeric_identifier_read_or_unproven")
    if type(facts.get("target_period_columns")) is not int or facts["target_period_columns"] != 1:
        reasons.append("observation_column_not_unique")
    if facts.get("target_adjustment") != "unadjusted":
        reasons.append("not_unadjusted")
    if facts.get("index_basis_status") != "synthetic_equivalence_assumption":
        reasons.append("index_basis_not_proven")
    if facts.get("revision_status") != "synthetic_unambiguous":
        reasons.append("revision_ambiguous")
    if facts.get("pdf_extracted") is not False or facts.get("values_included") is not False:
        reasons.append("not_metadata_only")
    return {
        "status": "synthetic_layout_compatible_not_authorized" if not reasons else "hold",
        "reasons": sorted(set(reasons)),
        "live_approval": False,
        "source_adopted": False,
        "numeric_identifier_read": False,
        "economic_value_read": False,
    }


def synthetic_example() -> dict[str, Any]:
    return {
        "fixture_kind": "synthetic_metadata_only",
        "source_url": PDF_URL,
        "publisher": "BLS",
        "reference_month": "2026-04",
        "claimed_release_date": "2026-05-13",
        "document_vintage_status": "synthetic_original_edition",
        "table_title": TABLE_TITLE,
        "table_title_count": 1,
        "governing_header_roles": ["commodity_identity", "unadjusted_index_level", "percent_change"],
        "direct_commodity_candidate_count": 1,
        "concept_label": "Crude petroleum",
        "concept_scope": "direct_commodity",
        "identifier_proof": "synthetic_placeholder_only",
        "target_period_columns": 1,
        "target_month": "2026-04",
        "target_adjustment": "unadjusted",
        "index_basis_status": "synthetic_equivalence_assumption",
        "revision_status": "synthetic_unambiguous",
        "pdf_extracted": False,
        "values_included": False,
    }


if __name__ == "__main__":
    print(json.dumps({
        "contract": validate_design(),
        "synthetic_fixture": classify_synthetic_layout(synthetic_example()),
    }, indent=2, sort_keys=True))
