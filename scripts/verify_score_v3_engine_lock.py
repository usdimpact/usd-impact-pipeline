#!/usr/bin/env python3
"""Verify the pre-holdout Score v3 research engine file lock."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

LOCK_PATH = Path("research/score_v3_engine_lock.json")
LOCK_FILE_SHA256 = "4858e5a6735cc0fb0c6000769cb846c60cd3e36d551c1371396315b020470a99"
IMPLEMENTATION_COMMIT_SHA = "4f1a14bcf656197fbfcc904f3f013852cb68cc01"
PREREGISTRATION_COMMIT_SHA = "bf49152fa6005edd20b770db287924d56cfa7499"
PREREGISTRATION_FILE_SHA256 = "54cfd363bb72e21e99285014c5ece3c3ce08a98dbdfc316dfadaf82de98b2cf4"
METRIC_CONTRACT_SHA256 = "d366b0f7e0f41b0702f867a38ce3f80277f41b49ae788e5846324fffb83b2dc7"
SHA64 = re.compile(r"^[0-9a-f]{64}$")
IMMUTABLE_FILES = {
    "requirements.lock",
    "usd_impact_score_v2.py",
    "research/score_v3_preregistration.json",
    "research/score_v3_metric_implementation_contract.json",
    "research/score_v3_metric_implementation_contract.schema.json",
    "research/score_v3_initialization_2026-08-21.csv",
    "research/score_v3_initialization_2026-08-21.manifest.json",
    "research/score_v3_prospective_manifest.schema.json",
    "scripts/build_score_repro_bundle.py",
    "scripts/freeze_score_v3_initialization.py",
    "scripts/score_v3_candidates.py",
    "scripts/score_v3_manifest.py",
    "scripts/score_v3_shadow_ingestion.py",
    "scripts/score_v3_metrics.py",
    "scripts/score_v3_metric_reporting.py",
}


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object in {path}")
    return payload


def _git_bytes(root: Path, revision: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Cannot read locked Score v3 file from Git: {revision}:{path}")
    return result.stdout


def verify(root: Path = Path("."), *, filesystem_only: bool = False) -> dict[str, Any]:
    root = root.resolve()
    lock_path = root / LOCK_PATH
    if _sha256(lock_path.read_bytes()) != LOCK_FILE_SHA256:
        raise RuntimeError("Score v3 engine lock file differs from its frozen SHA-256")
    lock = _read_json(lock_path)
    if set(lock) != {
        "lock_id",
        "lock_version",
        "locked_date",
        "prospective_holdout_start",
        "research_only",
        "production_change",
        "predictive_claim",
        "implementation_commit_sha",
        "preregistration_commit_sha",
        "preregistration_file_sha256",
        "metric_contract_sha256",
        "immutable_files",
        "change_policy",
        "automatic_override_allowed",
    }:
        raise RuntimeError("Score v3 engine lock fields differ from the closed contract")
    if lock.get("lock_id") != "usd_impact_score_v3_research_engine_2026-08-25":
        raise RuntimeError("Score v3 engine lock ID drifted")
    if lock.get("lock_version") != 1 or lock.get("locked_date") != "2026-08-25":
        raise RuntimeError("Score v3 engine lock version/date drifted")
    if lock.get("prospective_holdout_start") != "2026-08-28":
        raise RuntimeError("Score v3 engine lock holdout boundary drifted")
    if lock.get("research_only") is not True or lock.get("production_change") is not False:
        raise RuntimeError("Score v3 engine lock must remain research-only")
    if lock.get("predictive_claim") is not False:
        raise RuntimeError("Score v3 engine lock unexpectedly makes a predictive claim")
    if lock.get("implementation_commit_sha") != IMPLEMENTATION_COMMIT_SHA:
        raise RuntimeError("Score v3 implementation commit lock mismatch")
    if lock.get("preregistration_commit_sha") != PREREGISTRATION_COMMIT_SHA:
        raise RuntimeError("Score v3 preregistration commit lock mismatch")
    if lock.get("preregistration_file_sha256") != PREREGISTRATION_FILE_SHA256:
        raise RuntimeError("Score v3 preregistration file lock mismatch")
    if lock.get("metric_contract_sha256") != METRIC_CONTRACT_SHA256:
        raise RuntimeError("Score v3 metric contract lock mismatch")
    if lock.get("automatic_override_allowed") is not False:
        raise RuntimeError("Score v3 engine lock unexpectedly permits automatic override")

    immutable = lock.get("immutable_files")
    if not isinstance(immutable, dict) or set(immutable) != IMMUTABLE_FILES:
        raise RuntimeError("Score v3 immutable-file set drifted")
    for relative, expected_hash in immutable.items():
        if not isinstance(relative, str) or relative.startswith(("/", "..")):
            raise RuntimeError("Score v3 engine lock contains an unsafe path")
        if not isinstance(expected_hash, str) or not SHA64.fullmatch(expected_hash):
            raise RuntimeError(f"Score v3 engine lock has an invalid hash for {relative}")
        current_hash = _sha256((root / relative).read_bytes())
        if current_hash != expected_hash:
            raise RuntimeError(f"Score v3 engine file drifted from its pre-holdout lock: {relative}")
        if not filesystem_only:
            committed_hash = _sha256(_git_bytes(root, IMPLEMENTATION_COMMIT_SHA, relative))
            if committed_hash != expected_hash:
                raise RuntimeError(f"Score v3 implementation commit lacks locked bytes: {relative}")

    if not filesystem_only:
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", IMPLEMENTATION_COMMIT_SHA, "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if ancestry.returncode != 0:
            raise RuntimeError("Locked Score v3 implementation commit is not an ancestor of HEAD")

    return {
        "status": "verified",
        "filesystem_only": filesystem_only,
        "lock_file_sha256": LOCK_FILE_SHA256,
        "implementation_commit_sha": IMPLEMENTATION_COMMIT_SHA,
        "immutable_files": len(immutable),
        "research_only": True,
        "production_change": False,
        "predictive_claim": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--filesystem-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = verify(args.root, filesystem_only=args.filesystem_only)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            f"Score v3 engine lock verified at {report['implementation_commit_sha']}: "
            f"{report['immutable_files']} immutable files"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
