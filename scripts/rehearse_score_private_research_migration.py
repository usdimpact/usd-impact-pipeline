#!/usr/bin/env python3
"""No-write Development migration rehearsal for Score rights containment.

Builds provider-free synthetic private evidence in a temporary directory,
extracts the exact research inputs needed by the future private readers, derives
an aggregate-only public Score view, and proves the public view contains none of
the private component fields.

No network, cloud storage, public artifact replacement, provider retrieval, or
Production mutation is performed.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from scripts import build_score_public_safe_artifact as public_safe
from scripts import build_synthetic_private_score_evidence as synthetic
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
    path = repo_root / "governance" / "score-private-research-migration-contract.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("private research migration contract must be an object")
    return payload


def rehearse(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    contract = _load_contract(repo_root)

    if contract.get("state") != "review_only":
        raise RuntimeError("private research migration contract is not review-only")
    if contract.get("production_change_authorized") is not False:
        raise RuntimeError("Production change is unexpectedly authorized")
    if contract.get("real_provider_evidence_authorized") is not False:
        raise RuntimeError("real provider evidence is unexpectedly authorized")
    if contract.get("public_replacement_authorized") is not False:
        raise RuntimeError("public replacement is unexpectedly authorized")

    with tempfile.TemporaryDirectory(prefix="score-private-research-migration-") as tmp:
        private_root = Path(tmp) / "private-evidence"
        synthetic_report = synthetic.build(private_root)
        week = str(synthetic_report["latest_week"])
        latest = private_root / "score_repro_bundle_latest.json"

        bundle, bundle_sha = adapter.load_private_bundle(
            latest,
            expected_week=week,
            require_synthetic=True,
        )
        predictive = adapter.predictive_observation(bundle)
        source_levels = adapter.v3_source_levels(bundle)

        source = {
            "metadata": {
                "pipeline": "usd_impact_score_v2",
                "generated_at_utc": "2099-01-09T00:00:00Z",
                "weights": {name: float(weight) for name, weight in WEIGHTS.items()},
            },
            "weeks": [
                {
                    "date": "2099-01-02",
                    "score": 0.0,
                    "regime": "Neutral / transitional",
                },
                {
                    "date": "2099-01-09",
                    "score": float(bundle["published"]["score"]),
                    "regime": str(bundle["published"]["regime"]),
                },
            ],
        }
        safe = public_safe.build_public_safe_payload(source)
        public_safe.assert_public_safe(safe)

        serialized = json.dumps(safe, sort_keys=True)
        for marker in FORBIDDEN_PUBLIC_MARKERS:
            if marker in serialized:
                raise RuntimeError(f"aggregate-safe public payload leaked private marker: {marker}")

        if predictive["score"] != safe["latest"]["score"]:
            raise RuntimeError("private research score differs from aggregate-safe public score")
        if set(source_levels) != set(WEIGHTS):
            raise RuntimeError("private V3 source-level driver set mismatch")

    return {
        "status": "passed",
        "review_only": True,
        "writes_performed": False,
        "network_access_performed": False,
        "cloud_storage_action_performed": False,
        "provider_refetch_performed": False,
        "production_change_authorized": False,
        "real_provider_evidence_authorized": False,
        "public_replacement_authorized": False,
        "synthetic_week": week,
        "private_bundle_sha256": bundle_sha,
        "private_v3_driver_count": len(source_levels),
        "private_predictive_score": predictive["score"],
        "public_safe_latest_score": safe["latest"]["score"],
        "public_safe_history_rows": len(safe["history"]),
        "public_safe_schema_version": safe["schema_version"],
        "public_private_score_equal": predictive["score"] == safe["latest"]["score"],
        "private_component_values_exposed_publicly": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    print(json.dumps(rehearse(args.repo_root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
