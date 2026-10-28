#!/usr/bin/env python3
"""No-write compatibility rehearsal for locked Score research readers.

One validated private strict reproduction bundle is materialized only inside a
temporary workspace at the legacy paths expected by the locked Score v2
predictive and Score v3 shadow readers. The locked readers are not modified and
no repository public path is written.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from scripts import build_synthetic_private_score_evidence as synthetic
from scripts import score_private_evidence_research_adapter as private_adapter
from scripts import score_v2_predictive_ingestion as predictive
from scripts import score_v3_shadow_ingestion as shadow
from usd_impact_score_v2 import WEIGHTS


def _materialize_legacy_paths(workspace: Path, bundle_path: Path, week: str) -> None:
    latest = workspace / "public/data/score_repro_bundle_latest.json"
    archive = workspace / f"public/archive/{week}/repro_bundle.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    archive.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bundle_path, latest)
    shutil.copy2(bundle_path, archive)


def validate_bundle_compatibility(bundle_path: Path, expected_week: str) -> dict[str, Any]:
    bundle_path = bundle_path.resolve()
    private_bundle, private_sha = private_adapter.load_private_bundle(
        bundle_path,
        expected_week=expected_week,
        require_synthetic=True,
    )
    private_predictive = private_adapter.predictive_observation(private_bundle)
    private_levels = private_adapter.v3_source_levels(private_bundle)

    with tempfile.TemporaryDirectory(prefix="score-private-reader-legacy-") as tmp:
        workspace = Path(tmp) / "legacy-workspace"
        _materialize_legacy_paths(workspace, bundle_path, expected_week)
        parsed_week = date.fromisoformat(expected_week)

        predictive_bundle, predictive_sha = predictive._validate_bundle(workspace, parsed_week)
        shadow_bundle, shadow_sha = shadow._validate_bundle(workspace, parsed_week)

        predictive_score = float(predictive_bundle["published"]["score"])
        predictive_dxy = float(predictive_bundle["components"]["DXY"]["weekly_level"])
        shadow_levels = {
            driver: float(shadow_bundle["components"][driver]["weekly_level"])
            for driver in WEIGHTS
        }

    if predictive_sha != private_sha or shadow_sha != private_sha:
        raise RuntimeError("locked reader bundle hash differs from private adapter hash")
    if predictive_score != private_predictive["score"]:
        raise RuntimeError("locked predictive reader score differs from private adapter")
    if predictive_dxy != private_predictive["dxy_weekly_level"]:
        raise RuntimeError("locked predictive reader DXY differs from private adapter")
    if shadow_levels != private_levels:
        raise RuntimeError("locked V3 reader levels differ from private adapter")

    return {
        "schema_version": "score-private-reader-compatibility-v1",
        "status": "passed",
        "review_only": True,
        "writes_performed": False,
        "network_access_performed": False,
        "repository_public_paths_modified": False,
        "locked_readers_modified": False,
        "synthetic_week": expected_week,
        "bundle_sha256": private_sha,
        "predictive_score_equal": True,
        "predictive_dxy_equal": True,
        "v3_source_levels_equal": True,
        "v3_driver_count": len(shadow_levels),
        "production_change_authorized": False,
        "real_provider_evidence_authorized": False,
        "public_replacement_authorized": False,
    }


def rehearse() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="score-private-reader-compat-") as tmp:
        private_root = Path(tmp) / "private"
        synthetic_report = synthetic.build(private_root)
        week = str(synthetic_report["latest_week"])
        bundle_path = private_root / "score_repro_bundle_latest.json"
        return validate_bundle_compatibility(bundle_path, week)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--expected-week")
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()

    if args.bundle is not None or args.expected_week is not None:
        if args.bundle is None or not args.expected_week:
            raise SystemExit("--bundle and --expected-week must be provided together")
        report = validate_bundle_compatibility(args.bundle, args.expected_week)
    else:
        report = rehearse()

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report_output:
        args.report_output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
