#!/usr/bin/env python3
"""Dry-run the locked Score v2 predictive and Score v3 shadow readers.

This rehearsal uses provider-free synthetic evidence aligned to the first
preregistered holdout week (2026-08-28), copies only locked contracts into
isolated temporary workspaces, and invokes both readers with write=False.

No real research ledger, repository public path, network service, or cloud
resource is modified.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts import build_synthetic_private_score_evidence as synthetic
from scripts import score_v2_predictive_ingestion as predictive
from scripts import score_v3_shadow_ingestion as shadow

REHEARSAL_WEEK = "2026-08-28"
ATTESTATION_RUN_ID = "99999999"
ATTESTATION_URL = "https://github.com/usdimpact/usd-impact-pipeline/actions/runs/99999999"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy(repo_root: Path, workspace: Path, relative: str) -> None:
    source = repo_root / relative
    target = workspace / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _write_score(workspace: Path, score: float, regime: str) -> None:
    target = workspace / "public/data/usd_impact_score_v2.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {
                "metadata": {
                    "latest_date": REHEARSAL_WEEK,
                    "latest_score": score,
                    "latest_regime": regime,
                },
                "weeks": [],
            }
        ),
        encoding="utf-8",
    )


def _write_bundle(workspace: Path, bundle: dict[str, Any]) -> None:
    latest = workspace / "public/data/score_repro_bundle_latest.json"
    archive = workspace / f"public/archive/{REHEARSAL_WEEK}/repro_bundle.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    archive.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(bundle, sort_keys=True).encode("utf-8")
    latest.write_bytes(raw)
    archive.write_bytes(raw)


def _aligned_bundle() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="score-full-reader-source-") as tmp:
        root = Path(tmp)
        synthetic.build(root)
        bundle = json.loads(
            (root / "score_repro_bundle_latest.json").read_text(encoding="utf-8")
        )
    bundle["score_week"] = REHEARSAL_WEEK
    return bundle


def _prepare_predictive(repo_root: Path, workspace: Path) -> tuple[Path, str]:
    for relative in (
        "research/score_v2_predictive_preregistration.json",
        "research/score_v2_predictive_implementation_contract.json",
        "research/score_v2_predictive_manifest.json",
        "research/score_v3_initialization_2026-08-21.csv",
    ):
        _copy(repo_root, workspace, relative)

    manifest_path = workspace / "research/score_v2_predictive_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["entries"] = []
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path, _sha(manifest_path)


def _prepare_v3(repo_root: Path, workspace: Path) -> tuple[Path, str]:
    for relative in (
        "research/score_v3_initialization_2026-08-21.csv",
        "research/score_v3_initialization_2026-08-21.manifest.json",
        "research/score_v3_prospective_manifest.json",
        "research/score_v3_preregistration.json",
    ):
        _copy(repo_root, workspace, relative)

    manifest_path = workspace / "research/score_v3_prospective_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["entries"] = []
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path, _sha(manifest_path)


def rehearse(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    bundle = _aligned_bundle()
    score = float(bundle["published"]["score"])
    regime = str(bundle["published"]["regime"])

    with tempfile.TemporaryDirectory(prefix="score-full-reader-dry-run-") as tmp:
        root = Path(tmp)
        predictive_root = root / "predictive"
        v3_root = root / "v3"

        predictive_manifest, predictive_before = _prepare_predictive(
            repo_root, predictive_root
        )
        _write_score(predictive_root, score, regime)
        _write_bundle(predictive_root, bundle)

        v3_manifest, v3_before = _prepare_v3(repo_root, v3_root)
        _write_score(v3_root, score, regime)
        _write_bundle(v3_root, bundle)

        timestamp = datetime(2026, 8, 28, 23, 0, tzinfo=timezone.utc)

        predictive_report = predictive.ingest(
            predictive_root,
            recorded_at=timestamp,
            attestation_run_id=ATTESTATION_RUN_ID,
            attestation_url=ATTESTATION_URL,
            write=False,
        )
        v3_report = shadow.ingest(
            v3_root,
            ingested_at=timestamp,
            attestation_run_id=ATTESTATION_RUN_ID,
            attestation_url=ATTESTATION_URL,
            write=False,
        )

        predictive_after = _sha(predictive_manifest)
        v3_after = _sha(v3_manifest)

        predictive_output = predictive_root / "research/predictive"
        v3_output = v3_root / "research/prospective"

        if predictive_report.get("status") != "validated_dry_run":
            raise RuntimeError("predictive locked reader did not complete dry-run")
        if v3_report.get("status") != "validated_dry_run":
            raise RuntimeError("V3 locked reader did not complete dry-run")
        if predictive_report.get("writes_performed") is not False:
            raise RuntimeError("predictive locked reader unexpectedly wrote")
        if v3_report.get("writes_performed") is not False:
            raise RuntimeError("V3 locked reader unexpectedly wrote")
        if predictive_before != predictive_after:
            raise RuntimeError("predictive manifest changed during dry-run")
        if v3_before != v3_after:
            raise RuntimeError("V3 manifest changed during dry-run")
        if predictive_output.exists():
            raise RuntimeError("predictive output directory was created during dry-run")
        if v3_output.exists():
            raise RuntimeError("V3 output directory was created during dry-run")
        if predictive_report["source_v2_bundle_sha256"] != v3_report["source_v2_bundle_sha256"]:
            raise RuntimeError("locked readers used different source bundle hashes")

        return {
            "schema_version": "score-private-full-reader-dry-run-v1",
            "status": "passed",
            "review_only": True,
            "synthetic_rehearsal": True,
            "week": REHEARSAL_WEEK,
            "predictive_status": predictive_report["status"],
            "v3_status": v3_report["status"],
            "source_bundle_sha256": predictive_report["source_v2_bundle_sha256"],
            "predictive_manifest_unchanged": True,
            "v3_manifest_unchanged": True,
            "predictive_output_written": False,
            "v3_output_written": False,
            "locked_readers_modified": False,
            "network_access_performed": False,
            "cloud_action_performed": False,
            "repository_public_paths_modified": False,
            "production_change_authorized": False,
            "real_provider_evidence_authorized": False,
            "public_replacement_authorized": False,
        }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    print(json.dumps(rehearse(repo_root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
