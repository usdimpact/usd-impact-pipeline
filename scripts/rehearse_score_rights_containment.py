#!/usr/bin/env python3
"""No-write rehearsal for the Score rights-containment architecture.

Review-only. This script copies the current strict bundle into a temporary
non-public evidence tree, validates it through score_private_evidence_source,
builds the aggregate-only public-safe payload in memory, and proves both views
refer to the same published Score/week without modifying repository files.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from scripts import build_score_public_safe_artifact as public_safe
from scripts import score_private_evidence_source as private_source


def rehearse(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    score_path = repo_root / "public" / "data" / "usd_impact_score_v2.json"
    bundle_path = repo_root / "public" / "data" / "score_repro_bundle_latest.json"

    score_source = json.loads(score_path.read_text(encoding="utf-8"))
    if not isinstance(score_source, dict):
        raise RuntimeError("Current Score JSON is not an object")

    public_payload = public_safe.build_public_safe_payload(score_source)
    week = str(public_payload["latest"]["week_ending"])

    with tempfile.TemporaryDirectory(prefix="score-rights-rehearsal-") as tmp:
        evidence_root = Path(tmp) / "private-score-evidence"
        latest = evidence_root / "latest" / "repro_bundle.json"
        archive = evidence_root / "archive" / week / "repro_bundle.json"
        latest.parent.mkdir(parents=True)
        archive.parent.mkdir(parents=True)
        shutil.copyfile(bundle_path, latest)
        shutil.copyfile(bundle_path, archive)

        private = private_source.load_private_strict_bundle(
            repo_root,
            evidence_root,
            week,
        )

    published = private.bundle.get("published") or {}
    private_score = float(published.get("score"))
    private_regime = str(published.get("regime"))

    if private_score != float(public_payload["latest"]["score"]):
        raise RuntimeError("Private strict evidence score differs from public-safe aggregate score")
    if private_regime != str(public_payload["latest"]["regime"]):
        raise RuntimeError("Private strict evidence regime differs from public-safe aggregate regime")

    return {
        "status": "passed",
        "review_only": True,
        "writes_performed": False,
        "week_ending": week,
        "aggregate_score": private_score,
        "aggregate_regime": private_regime,
        "private_strict_bundle_sha256": private.sha256,
        "aggregate_history_sha256": public_payload["release_evidence"][
            "aggregate_history_sha256"
        ],
        "public_safe_history_rows": len(public_payload["history"]),
        "private_evidence_loaded_from_public_path": False,
        "provider_refetch_performed": False,
        "production_workflow_changed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    print(json.dumps(rehearse(args.repo_root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
