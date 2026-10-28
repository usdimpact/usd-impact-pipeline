#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

EXPECTED = {
    "USD": "no_specific_exception_identified_in_reviewed_official_publication_path",
    "ENERGY": "no_specific_exception_identified_in_reviewed_official_publication_path",
    "FIN_CONDITIONS": "no_specific_exception_identified_in_reviewed_official_publication_path",
    "FIN_STRESS": "no_specific_exception_identified_in_reviewed_official_publication_path",
    "LIQUIDITY": "no_specific_exception_identified_in_reviewed_official_publication_path",
    "REAL_YIELD": "residual_upstream_provenance_requires_explicit_scope_confirmation",
    "UST_2Y": "residual_upstream_provenance_requires_explicit_scope_confirmation",
    "UST_10Y": "residual_upstream_provenance_requires_explicit_scope_confirmation",
}

def validate(repo_root: Path) -> dict[str, object]:
    review = json.loads((repo_root / "governance/score-v2-1e-upstream-provenance-review.json").read_text())
    hold = json.loads((repo_root / "governance/score-publication-rights-gate.json").read_text())

    if review["state"] != "evidence_only_no_source_approval":
        raise RuntimeError("review state changed")
    for key in ("legal_conclusion", "source_approval", "real_data_fetch_authorized", "real_data_research_authorized", "production_authorized"):
        if review.get(key) is not False:
            raise RuntimeError(f"{key} must remain false in the historical review artifact")
    if hold.get("state") != "hold":
        raise RuntimeError("rights HOLD must remain active")

    rows = review.get("series_review", [])
    if len(rows) != 8:
        raise RuntimeError("all eight v2.1E slots must be reviewed")
    actual = {row["slot"]: row["classification"] for row in rows}
    if actual != EXPECTED:
        raise RuntimeError("provenance classifications changed")

    summary = review.get("summary", {})
    if summary.get("no_specific_exception_identified") != 5:
        raise RuntimeError("expected five slots without a specific exception")
    if summary.get("residual_upstream_provenance") != 3:
        raise RuntimeError("expected three H.15 residual-provenance slots")
    if summary.get("candidate_source_approved") is not False:
        raise RuntimeError("candidate may not be source-approved by this review")

    return {
        "status": "passed",
        "slots_reviewed": 8,
        "h15_residual_slots": 3,
        "source_approval": False,
        "real_data_research_authorized": False,
        "production_authorized": False,
        "rights_hold": True,
    }

if __name__ == "__main__":
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
