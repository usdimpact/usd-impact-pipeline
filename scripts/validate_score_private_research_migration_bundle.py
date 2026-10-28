#!/usr/bin/env python3
"""Validate one synthetic private Score bundle for research-reader migration.

Review-only / Development synthetic boundary. Reads one local bundle, derives the
narrow research inputs and aggregate-safe public view, and emits a JSON report.
No network access and no writes outside an optional report path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts import build_score_public_safe_artifact as public_safe
from scripts import score_private_evidence_research_adapter as adapter
from usd_impact_score_v2 import WEIGHTS

FORBIDDEN_PUBLIC_MARKERS = (
    '"components"',
    '"weekly_level"',
    '"dxy_weekly_level"',
    '"source_weekly_levels"',
    '"z_clipped"',
    '"contribution"',
)


def _load_contract(repo_root: Path) -> dict[str, Any]:
    payload = json.loads(
        (repo_root / "governance" / "score-private-research-migration-contract.json")
        .read_text(encoding="utf-8")
    )
    if not isinstance(payload, dict):
        raise RuntimeError("private research migration contract must be an object")
    return payload


def validate_bundle(
    *,
    repo_root: Path,
    bundle_path: Path,
    expected_week: str,
) -> dict[str, Any]:
    contract = _load_contract(repo_root.resolve())
    if contract.get("state") != "review_only":
        raise RuntimeError("private research migration contract is not review-only")
    if contract.get("development_synthetic_rehearsal_authorized") is not True:
        raise RuntimeError("Development synthetic rehearsal is not authorized")
    for field in (
        "production_change_authorized",
        "real_provider_evidence_authorized",
        "public_replacement_authorized",
    ):
        if contract.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    bundle, bundle_sha = adapter.load_private_bundle(
        bundle_path,
        expected_week=expected_week,
        require_synthetic=True,
    )
    predictive = adapter.predictive_observation(bundle)
    levels = adapter.v3_source_levels(bundle)

    aggregate_source = {
        "metadata": {
            "pipeline": "usd_impact_score_v2",
            "generated_at_utc": None,
            "weights": {name: float(weight) for name, weight in WEIGHTS.items()},
        },
        "weeks": [
            {
                "date": expected_week,
                "score": predictive["score"],
                "regime": str(bundle["published"]["regime"]),
            }
        ],
    }
    safe = public_safe.build_public_safe_payload(aggregate_source)
    public_safe.assert_public_safe(safe)

    serialized = json.dumps(safe, sort_keys=True)
    for marker in FORBIDDEN_PUBLIC_MARKERS:
        if marker in serialized:
            raise RuntimeError(f"aggregate-safe view leaked private marker: {marker}")

    if safe["latest"]["score"] != predictive["score"]:
        raise RuntimeError("aggregate-safe public score differs from private research score")
    if set(levels) != set(WEIGHTS):
        raise RuntimeError("private V3 driver set mismatch")

    return {
        "schema_version": "score-private-research-read-rehearsal-v1",
        "status": "passed",
        "review_only": True,
        "synthetic_rehearsal": True,
        "do_not_publish": True,
        "week": expected_week,
        "bundle_sha256": bundle_sha,
        "predictive_fields": sorted(predictive),
        "v3_driver_count": len(levels),
        "aggregate_safe_schema_version": safe["schema_version"],
        "aggregate_score": safe["latest"]["score"],
        "aggregate_regime": safe["latest"]["regime"],
        "private_component_values_exposed_publicly": False,
        "production_change_authorized": False,
        "real_provider_evidence_authorized": False,
        "public_replacement_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--expected-week", required=True)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()

    report = validate_bundle(
        repo_root=args.repo_root,
        bundle_path=args.bundle,
        expected_week=args.expected_week,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report_output:
        args.report_output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
