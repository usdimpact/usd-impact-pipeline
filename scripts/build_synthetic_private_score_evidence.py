#!/usr/bin/env python3
"""Build a synthetic Score private-evidence fixture for storage/handoff rehearsals.

This fixture contains no provider-derived values and is intentionally not a
production-release reproduction bundle. It exists only to exercise the private
storage -> runner temp -> #158 ephemeral-worktree mechanics while rights issue
#155 remains unresolved.

Safety properties:
- no network access;
- fixed far-future synthetic Friday weeks;
- output must remain outside the repository;
- existing files are never overwritten;
- explicit synthetic/do-not-publish markers are embedded in every bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts import build_score_repro_bundle as repro
from scripts import materialize_private_score_evidence as private
from usd_impact_score_v2 import REGIME_BANDS, WEIGHTS

FIXTURE_VERSION = "score-private-evidence-synthetic-v1"
ARCHIVE_WEEKS = ("2099-01-02", "2099-01-09")
LATEST_WEEK = ARCHIVE_WEEKS[-1]


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _bundle(week: str, marker: float) -> dict[str, Any]:
    components = {}
    for index, (driver, weight) in enumerate(WEIGHTS.items()):
        components[driver] = {
            "weekly_level": 1000.0 + marker + float(index),
            "z_clipped": 0.0,
            "weight": float(weight),
        }

    bundle = {
        "synthetic_fixture_version": FIXTURE_VERSION,
        "synthetic_rehearsal": True,
        "do_not_publish": True,
        "score_week": week,
        "pipeline_git_sha": "0" * 40,
        "requirements_lock_sha256": "0" * 64,
        "components": components,
        "calculation": {
            "regime_bands": [
                {
                    "low": None if low == float("-inf") else float(low),
                    "high": None if high == float("inf") else float(high),
                    "label": label,
                }
                for low, high, label in REGIME_BANDS
            ]
        },
        "published": {
            "score": 0.0,
            "regime": "Neutral / transitional",
        },
    }
    repro.verify_bundle(bundle)
    return bundle


def build(output_root_arg: Path) -> dict[str, Any]:
    output_root = private._require_outside_repo(output_root_arg, "synthetic fixture root")
    if output_root.exists() and any(output_root.iterdir()):
        raise RuntimeError("synthetic fixture root must be empty")
    output_root.mkdir(parents=True, exist_ok=True)

    raw_by_week: dict[str, bytes] = {}
    for index, week in enumerate(ARCHIVE_WEEKS):
        payload = _bundle(week, marker=float(index) * 10.0)
        raw = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
        archive_path = output_root / "archive" / week / "repro_bundle.json"
        if archive_path.exists():
            raise RuntimeError(f"refusing to overwrite synthetic archive: {archive_path}")
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        archive_path.write_bytes(raw)
        raw_by_week[week] = raw

    latest_path = output_root / "score_repro_bundle_latest.json"
    if latest_path.exists():
        raise RuntimeError("refusing to overwrite synthetic latest bundle")
    latest_path.write_bytes(raw_by_week[LATEST_WEEK])

    latest, latest_week, archives = private.discover_evidence(output_root)
    if latest_week != LATEST_WEEK or len(archives) != len(ARCHIVE_WEEKS):
        raise RuntimeError("synthetic fixture failed private-evidence discovery")

    return {
        "schema_version": FIXTURE_VERSION,
        "synthetic_rehearsal": True,
        "do_not_publish": True,
        "latest_week": latest_week,
        "archive_count": len(archives),
        "latest_sha256": _sha256(latest.read_bytes()),
        "provider_derived_values": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.output_root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
