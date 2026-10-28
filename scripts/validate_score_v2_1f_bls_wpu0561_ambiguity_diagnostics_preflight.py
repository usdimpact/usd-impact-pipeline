#!/usr/bin/env python3
"""Validate the Issue #258 ambiguity-diagnostics design-only HOLD state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DESIGN = "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json"
TEMPLATE = "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json"
CONTRACT = "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json"
ACTIVE_RECEIPT = "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json"
DISPATCH = "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json"
PREDECESSOR = "governance/score-v2-1f-bls-wpu0561-representative-index-preflight-consumption-2026-10-29.json"
WORKFLOW = ".github/workflows/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight.yml"
ISSUE = "https://github.com/usdimpact/usd-impact-pipeline/issues/258"
EXPECTED_RESOURCES = [
    "/news.release/archives/ppi_05152013.htm",
    "/ppi/detailed-report/ppi-detailed-report-april-2026.xlsx",
]


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    design = _load(root / DESIGN)
    template = _load(root / TEMPLATE)
    contract = _load(root / CONTRACT)
    predecessor = _load(root / PREDECESSOR)
    rights = _load(root / "governance/score-publication-rights-gate.json")
    prereg = _load(root / "governance/score-v2-1f-preregistration.json")
    workflow = (root / WORKFLOW).read_text(encoding="utf-8")

    for relative in (ACTIVE_RECEIPT, DISPATCH):
        if (root / relative).exists():
            raise RuntimeError(f"design-only HOLD must not contain {relative}")

    if predecessor.get("state") != "consumed_after_ambiguous_result":
        raise RuntimeError("Issue #252 consumption evidence changed")
    result = predecessor.get("sanitized_result", {})
    if result.get("request_count") != 2 or result.get("observation_count") != 0:
        raise RuntimeError("Issue #252 sanitized result changed")

    if rights.get("state") != "hold":
        raise RuntimeError("Score publication rights gate must remain HOLD")
    if prereg.get("state") != "preregistered_design_only":
        raise RuntimeError("v2.1F preregistration state changed")

    if design.get("version") != 2:
        raise RuntimeError("Issue #258 hardened design version changed")
    if design.get("state") != "design_only_hold":
        raise RuntimeError("Issue #258 design must remain HOLD")
    if design.get("owner_decision_issue") != ISSUE:
        raise RuntimeError("Issue #258 owner-decision URL changed")
    if [item.get("path") for item in design.get("fixed_resources", [])] != EXPECTED_RESOURCES:
        raise RuntimeError("Issue #258 fixed resources changed")

    budget = design.get("future_live_budget", {})
    if budget.get("request_budget") != 2:
        raise RuntimeError("Issue #258 request budget changed")
    if budget.get("max_economic_observations_total") != 0:
        raise RuntimeError("Issue #258 must allow zero economic observations")
    if budget.get("max_economic_observations_per_resource") != 0:
        raise RuntimeError("Issue #258 per-resource economic observation cap must be zero")

    layered = design.get("layered_result_model", {})
    invariant = layered.get("invariant", "")
    if "must never erase an already proven identity mapping" not in invariant:
        raise RuntimeError("layered identity-preservation invariant changed")
    if "not_evaluated" not in layered.get("semantic_status", []):
        raise RuntimeError("transport failures must support semantic not_evaluated")
    if set(layered.get("identity_status", [])) != {"proven", "not_proven"}:
        raise RuntimeError("identity status model changed")

    policy = design.get("diagnostic_policy", {})
    if policy.get("economic_value_read") is not False:
        raise RuntimeError("economic value read must remain forbidden")
    if policy.get("local_block_required") is not True:
        raise RuntimeError("local candidate block scoping must be required")
    if policy.get("whole_sheet_or_whole_table_role_accumulation_forbidden") is not True:
        raise RuntimeError("whole-container role accumulation must remain forbidden")
    if policy.get("whole_sheet_revision_context_accumulation_forbidden") is not True:
        raise RuntimeError("whole-sheet revision context accumulation must remain forbidden")
    if policy.get("candidate_multiplicity_is_not_identity_failure") is not True:
        raise RuntimeError("candidate multiplicity must not erase identity")
    for reason in ("transport_dns_failure", "not_evaluated", "multiple_candidate_blocks"):
        if reason not in policy.get("allowed_reason_codes", []):
            raise RuntimeError(f"missing required reason code: {reason}")

    block_policy = design.get("local_block_policy", {})
    if block_policy.get("header_stack_max_rows") != 3:
        raise RuntimeError("header stack bound changed")
    if "child/leaf header wins" not in block_policy.get("header_role_precedence", ""):
        raise RuntimeError("child-header precedence changed")
    if "economic cells" not in block_policy.get("merged_header_policy", ""):
        raise RuntimeError("merged-header zero-value rule changed")
    if block_policy.get("numeric_economic_cells") != "must not be parsed or returned":
        raise RuntimeError("economic numeric cells must remain unread")

    identifier_policy = design.get("identifier_normalization_policy", {})
    if identifier_policy.get("prerequisite") != "identifier column must already be proven from non-economic local header semantics":
        raise RuntimeError("identifier normalization prerequisite changed")
    if identifier_policy.get("unicode_normalization") != "NFKC":
        raise RuntimeError("identifier Unicode normalization changed")
    if identifier_policy.get("unrestricted_punctuation_stripping") is not False:
        raise RuntimeError("identifier normalization became too permissive")
    if identifier_policy.get("neighbor_cell_or_row_wide_search") is not False:
        raise RuntimeError("unsafe row-wide identifier fallback enabled")

    transport_policy = design.get("transport_policy", {})
    if "semantic_status=not_evaluated" not in transport_policy.get("dns_failure", ""):
        raise RuntimeError("DNS failure must remain NOT_EVALUATED")
    if transport_policy.get("content_semantics_after_transport_failure") != "not_evaluated":
        raise RuntimeError("transport failure must not become content ambiguity")

    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("all Issue #258 design authorizations must remain false")
    if template.get("decision_status") != "hold":
        raise RuntimeError("authorization template must remain HOLD")
    if template.get("max_economic_observations_total") != 0:
        raise RuntimeError("authorization template economic observation cap must be zero")
    if any(template.get("authorizations", {}).values()):
        raise RuntimeError("authorization template flags must remain false")

    if contract.get("state") != "ambiguity_diagnostics_design_only_hold":
        raise RuntimeError("execution contract must remain design-only HOLD")
    if contract.get("active_authorization_receipt_expected_now") is not False:
        raise RuntimeError("active receipt must not be expected")
    if contract.get("dispatch_marker_expected_now") is not False:
        raise RuntimeError("dispatch must not be expected")
    if contract.get("max_economic_observations_total") != 0:
        raise RuntimeError("contract economic observation cap must be zero")
    if any(contract.get("current_state", {}).values()):
        raise RuntimeError("contract authorization flags must all remain false")
    if contract.get("production_authorized") is not False:
        raise RuntimeError("Production must remain unauthorized")

    if ("if: $" + "{{ false }}") not in workflow:
        raise RuntimeError("Issue #258 workflow must remain inert")
    if "push:" in workflow:
        raise RuntimeError("Issue #258 HOLD workflow must not have a push trigger")

    return {
        "status": "passed",
        "state": "ambiguity_diagnostics_design_only_hold",
        "issue": ISSUE,
        "request_budget": 2,
        "max_economic_observations_total": 0,
        "layered_identity_preservation": True,
        "transport_failure_semantics": "not_evaluated",
        "multirow_header_support": True,
        "active_receipt_present": False,
        "dispatch_present": False,
        "live_request_authorized": False,
        "economic_value_read_authorized": False,
        "candidate_score_computation_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }


def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
