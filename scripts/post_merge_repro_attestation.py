#!/usr/bin/env python3
"""Read-only attestation for a candidate or published Score v2 release.

For legacy releases the script records that strict bundle acceptance is not yet
applicable. For 2026-08-28 and later it independently validates the frozen
bundle from the checked-out Git state and proves the bundle's pipeline commit
is an ancestor of the attested commit.

A pull-request run is pre-merge evidence only. Only a successful push-to-main
attestation may identify a strict release as a production acceptance candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.validate_methodology_contract import validate_contract
from scripts.validate_weekly_release import (
    load_json,
    reproduction_bundle_required,
    validate_reproduction_bundle,
)


ROOT = Path(__file__).resolve().parents[1]


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=root, text=True, stderr=subprocess.STDOUT
    ).strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _attestation_context() -> str:
    event = os.environ.get("GITHUB_EVENT_NAME", "local")
    ref = os.environ.get("GITHUB_REF", "")
    if event == "push" and ref == "refs/heads/main":
        return "main_post_merge"
    if event == "pull_request":
        return "pull_request_premerge"
    return "manual_or_local_read_only"


def attest(root: Path) -> dict[str, Any]:
    root = root.resolve()
    contract = validate_contract(
        root / "public/data/score_v2_methodology.json",
        root / "public/data/score_v2_methodology.schema.json",
    )
    score_payload = load_json(root / "public/data/usd_impact_score_v2.json")
    metadata = score_payload.get("metadata") or {}
    week = str(metadata.get("latest_date", ""))
    if not week:
        raise ValueError("Published score metadata has no latest_date")

    attested_sha = _git(root, "rev-parse", "HEAD")
    context = _attestation_context()
    report: dict[str, Any] = {
        "study": "usd_impact_score_v2_reproduction_attestation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "score_week": week,
        "attested_git_sha": attested_sha,
        "attestation_context": context,
        "methodology_contract_sha256": contract["contract_sha256"],
        "production_methodology_changed": False,
        "read_only": True,
    }

    if not reproduction_bundle_required(week):
        report.update(
            {
                "status": "legacy_release_not_applicable",
                "strict_bundle_required": False,
                "acceptance_candidate": False,
                "note": "Strict archived reproduction proof begins with 2026-08-28.",
            }
        )
        return report

    validate_reproduction_bundle(root, metadata, week)
    latest_bundle_path = root / "public/data/score_repro_bundle_latest.json"
    archive_bundle_path = root / f"public/archive/{week}/repro_bundle.json"
    bundle = load_json(latest_bundle_path)
    pipeline_sha = str(bundle["pipeline_git_sha"])

    try:
        subprocess.check_call(
            ["git", "merge-base", "--is-ancestor", pipeline_sha, attested_sha],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as error:
        raise ValueError(
            f"Bundle pipeline commit {pipeline_sha} is not an ancestor of attested commit {attested_sha}"
        ) from error

    latest_hash = _sha256(latest_bundle_path)
    archive_hash = _sha256(archive_bundle_path)
    if latest_hash != archive_hash:
        raise ValueError("Attested latest/archive bundle SHA-256 mismatch")

    report.update(
        {
            "status": "verified",
            "strict_bundle_required": True,
            "acceptance_candidate": context == "main_post_merge",
            "score": float(metadata["latest_score"]),
            "regime": metadata["latest_regime"],
            "bundle_pipeline_git_sha": pipeline_sha,
            "bundle_pipeline_sha_is_attested_ancestor": True,
            "bundle_sha256": latest_hash,
            "archived_bundle_sha256": archive_hash,
            "bundle_archive_match": True,
            "offline_reproduction_gate": "passed",
            "requirements_lock_sha256": bundle["requirements_lock_sha256"],
        }
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    report = attest(args.root)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
