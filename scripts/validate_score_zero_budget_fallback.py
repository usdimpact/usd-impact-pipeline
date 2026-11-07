#!/usr/bin/env python3
"""Read-only audit of the current zero-budget publishing HOLD; never a release gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED = ["DXY", "WTI", "SPX", "VIX", "BTC", "GOLD", "UST_2Y", "UST_10Y"]
NEXT_STEP = "review_existing_independent_panel_rights_and_methodology_only"
PERMISSION_COUNT = 14
SOURCE_COUNT = 4
AUTHORITY_COUNT = 14


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def _false(record: dict[str, Any], fields: tuple[str, ...], context: str) -> None:
    if not isinstance(record, dict):
        raise RuntimeError(f"{context} must be an object")
    for field in fields:
        if record.get(field) is not False:
            raise RuntimeError(f"{context}.{field} must remain false")


def validate_snapshot(
    matrix: dict[str, Any],
    gate: dict[str, Any],
    provider: dict[str, Any],
    panel: dict[str, Any],
) -> dict[str, Any]:
    """Verify a non-authorizing evidence snapshot. No network, writes or releases."""
    if gate.get("state") != "hold" or gate.get("decision_receipt") is not None or gate.get("approved_by") is not None:
        raise RuntimeError("canonical Score publication HOLD or empty approval receipt changed")
    if matrix.get("state") != "review_only" or matrix.get("budget_constraint") != "zero_paid_market_data_budget":
        raise RuntimeError("fallback review and zero-budget constraints changed")
    if matrix.get("last_reviewed_utc") != "2026-11-07":
        raise RuntimeError("current fallback checkpoint missing")
    _false(matrix, ("production_authorized", "methodology_change_authorized",
                    "real_data_rehearsal_authorized", "score_publication_authorized",
                    "archive_remediation_authorized", "paid_license_purchase_authorized"), "matrix")

    drivers = matrix.get("drivers")
    if not isinstance(drivers, list) or any(not isinstance(d, dict) for d in drivers):
        raise RuntimeError("fallback driver inventory malformed")
    if [d.get("driver") for d in drivers] != EXPECTED:
        raise RuntimeError("fallback driver inventory mismatch")
    by_driver = {item["driver"]: item for item in drivers}
    if by_driver["SPX"].get("disposition") != "paid_license_required_no_budget":
        raise RuntimeError("S&P paid-license result cannot become a free substitute")
    if by_driver["VIX"].get("disposition") != "rights_unresolved_not_zero_budget_safe":
        raise RuntimeError("VIX derived rights remain unresolved")
    for name in ("DXY", "WTI", "BTC", "GOLD"):
        if by_driver[name].get("exact_semantic_replacement") is not False:
            raise RuntimeError(f"{name} has no authorized exact no-fee replacement")
    for name in ("UST_2Y", "UST_10Y"):
        if by_driver[name].get("disposition") != "rights_and_retention_unresolved":
            raise RuntimeError(f"{name} FRED transport/retention cannot be cleared implicitly")

    recorded = matrix.get("provider_evidence", {})
    sp = recorded.get("s_and_p", {})
    if sp.get("disposition") != "PAID_LICENSE_REQUIRED_FOR_DESCRIBED_USE_CASE" or sp.get("provider_reply_date") != "2026-10-29":
        raise RuntimeError("categorical S&P paid-license checkpoint changed")
    _false(sp, ("written_no_fee_aggregate_permission_received", "paid_license_executed"), "matrix S&P")
    fred = recorded.get("fred_delivery", {})
    if fred.get("state") != "RETENTION_AND_TRANSPORT_HOLD":
        raise RuntimeError("FRED retention review cannot be treated as cleared")
    _false(fred, ("fred_content_retention_cleared", "direct_treasury_or_h15_substitution_approved"), "matrix FRED")
    if provider.get("review_state") != "PROVIDER_PAID_LICENSE_REQUIRED_NO_BUDGET_HOLD":
        raise RuntimeError("latest provider evidence is not the recorded hold")
    if provider.get("provider_reply_date_utc") != "2026-10-29":
        raise RuntimeError("provider reply date changed")
    reply = provider.get("provider_reply", {})
    if reply.get("paid_license_required_for_described_request") is not True:
        raise RuntimeError("provider paid requirement cannot be silently waived")
    _false(reply, ("written_no_fee_aggregate_permission_received", "paid_license_executed"), "provider")
    economics = provider.get("economics", {})
    if economics.get("authorized_additional_market_data_license_budget_usd") != 0:
        raise RuntimeError("no market-data licensing budget authorized")
    _false(economics, ("paid_license_purchase_authorized", "original_eight_driver_score_zero_budget_release_viable"), "economics")
    auth = provider.get("authorizations")
    if not isinstance(auth, dict) or len(auth) != 12 or any(value is not False for value in auth.values()):
        raise RuntimeError("all 12 provider disposition authorizations must remain false")

    alt = matrix.get("independent_alternative", {})
    if alt.get("category") != "INDEPENDENT_THREE_DIAL_CONTEXT_NOT_LEGACY_SCORE" or alt.get("synthetic_only") is not True:
        raise RuntimeError("alternative must remain independent synthetic research")
    if alt.get("license_budget_usd") != 0 or alt.get("governing_issue") != "https://github.com/usdimpact/usd-impact-pipeline/issues/313":
        raise RuntimeError("independent panel identity or budget changed")
    _false(alt, ("old_score_history_compatible", "owner_methodology_approved",
                 "real_data_access_approved", "all_source_rights_cleared",
                 "public_schema_approved", "publication_approved", "production_approved"), "independent alternative")
    if panel.get("status") != "SYNTHETIC_ONLY_DESIGN_HOLD" or panel.get("legacy_score_replacement") is not False:
        raise RuntimeError("separate Panel cannot become Score v2 or release approved")
    if panel.get("methodology", {}).get("no_composite_score") is not True:
        raise RuntimeError("Panel is three descriptive dials, not a new aggregate Score")
    if panel.get("cost_policy", {}).get("paid_market_data_budget_usd") != 0:
        raise RuntimeError("independent panel must retain zero data-license budget")
    source_permissions = panel.get("source_permissions")
    dimensions = panel.get("permission_dimensions")
    if (not isinstance(source_permissions, dict) or len(source_permissions) != SOURCE_COUNT
            or not isinstance(dimensions, list) or len(dimensions) != PERMISSION_COUNT
            or len(set(dimensions)) != PERMISSION_COUNT):
        raise RuntimeError("independent panel rights dimensions or source count changed")
    for source_id, candidate in source_permissions.items():
        rights = candidate.get("rights") if isinstance(candidate, dict) else None
        if not isinstance(rights, dict) or set(rights) != set(dimensions) or any(flag is not False for flag in rights.values()):
            raise RuntimeError(f"{source_id} has a missing, unknown or newly granted permission")
    authorities = panel.get("external_authorities")
    if not isinstance(authorities, dict) or len(authorities) != AUTHORITY_COUNT or any(flag is not False for flag in authorities.values()):
        raise RuntimeError("all 14 external authorities must remain false")
    control = panel.get("publication_control", {})
    if control.get("status") != "HOLD" or control.get("owner_release_receipt") is not None:
        raise RuntimeError("independent panel must remain on publication hold")
    _false(control, ("rights_cleared", "public_release_authorized",
                     "production_authorized", "privacy_security_review_complete"), "panel publication")

    conclusion = matrix.get("conclusion", {})
    if conclusion.get("exact_v2_zero_budget_path_confirmed") is not False or conclusion.get("next_allowed_step") != NEXT_STEP:
        raise RuntimeError("fallback conclusion cannot authorize legacy publication or new model activation")

    return {
        "status": "passed",
        "review_only": True,
        "zero_budget": True,
        "driver_count": len(drivers),
        "source_permissions_denied": SOURCE_COUNT * PERMISSION_COUNT,
        "external_authorities_denied": AUTHORITY_COUNT,
        "exact_v2_zero_budget_path_confirmed": False,
        "methodology_change_authorized": False,
        "real_data_rehearsal_authorized": False,
        "production_authorized": False,
        "publication_authorized": False,
    }


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    return validate_snapshot(
        _load(repo_root / "governance/score-zero-budget-fallback-matrix.json"),
        _load(repo_root / "governance/score-publication-rights-gate.json"),
        _load(repo_root / "governance/score-spdji-provider-disposition-2026-10-30.json"),
        _load(repo_root / "governance/independent-macro-context-fallback-draft-2026-10-30.json"),
    )


def main() -> int:
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
