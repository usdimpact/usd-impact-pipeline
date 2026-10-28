#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

EXPECTED = {
    "REAL_YIELD": "H15/H15/RIFLGFCY10_XII_N.B",
    "UST_2Y": "H15/H15/RIFLGFCY02_N.B",
    "UST_10Y": "H15/H15/RIFLGFCY10_N.B",
}
CLASSIFICATION = (
    "government_derived_published_output_no_specific_third_party_notice_"
    "identified_on_reviewed_output_path"
)

def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value

def validate(repo_root: Path) -> dict[str, object]:
    review = _load(repo_root / "governance/score-v2-1e-h15-output-scope-review.json")
    prior = _load(repo_root / "governance/score-v2-1e-upstream-provenance-review.json")
    hold = _load(repo_root / "governance/score-publication-rights-gate.json")

    if review.get("state") != "evidence_only_no_source_approval":
        raise RuntimeError("H.15 review state changed")
    for key in (
        "legal_conclusion",
        "source_approval",
        "real_data_fetch_authorized",
        "real_data_research_authorized",
        "public_artifact_replacement_authorized",
        "research_ledger_mutation_authorized",
        "production_authorized",
    ):
        if review.get(key) is not False:
            raise RuntimeError(f"{key} must remain false in the historical review artifact")

    if hold.get("state") != "hold":
        raise RuntimeError("rights HOLD must remain active")

    prior_rows = {row["slot"]: row for row in prior.get("series_review", [])}
    for slot in EXPECTED:
        if prior_rows.get(slot, {}).get("classification") != (
            "residual_upstream_provenance_requires_explicit_scope_confirmation"
        ):
            raise RuntimeError(f"prior residual classification missing for {slot}")

    scope = review.get("scope", {})
    if scope.get("published_government_outputs_only") is not True:
        raise RuntimeError("scope must remain limited to published government outputs")
    for key in (
        "raw_upstream_otc_quotes_in_scope",
        "reconstruction_of_raw_upstream_quotes_in_scope",
        "paid_or_credentialed_source_in_scope",
    ):
        if scope.get(key) is not False:
            raise RuntimeError(f"{key} must remain false")

    rows = review.get("h15_slots", [])
    if len(rows) != 3:
        raise RuntimeError("exactly three H.15 slots must be reviewed")
    actual = {row["slot"]: row["series_id"] for row in rows}
    if actual != EXPECTED:
        raise RuntimeError("H.15 series inventory changed")
    for row in rows:
        if row.get("classification") != CLASSIFICATION:
            raise RuntimeError(f"unexpected classification for {row['slot']}")
        if row.get("raw_upstream_quote_use") is not False:
            raise RuntimeError(f"raw upstream quote use must remain false for {row['slot']}")
        if row.get("source_approved") is not False:
            raise RuntimeError(f"source approval must remain false for {row['slot']}")

    summary = review.get("summary", {})
    if summary.get("h15_slots_reviewed") != 3:
        raise RuntimeError("H.15 review count changed")
    if summary.get("raw_upstream_quote_streams_in_scope") != 0:
        raise RuntimeError("raw upstream quote streams may not enter scope")
    if summary.get("source_approval") is not False:
        raise RuntimeError("source approval may not be asserted")
    if summary.get("rights_hold_remains") is not True:
        raise RuntimeError("rights HOLD must remain explicit")
    if summary.get("active_research_authorization_receipt_present") is not False:
        raise RuntimeError("historical review snapshot changed")

    return {
        "status": "passed",
        "h15_slots_reviewed": 3,
        "published_government_outputs_only": True,
        "raw_upstream_quote_use": False,
        "source_approval": False,
        "real_data_research_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }

if __name__ == "__main__":
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
