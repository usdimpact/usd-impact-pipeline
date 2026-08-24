#!/usr/bin/env python3
"""Verify the pre-holdout Score v2 predictive engine file lock."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

LOCK_PATH = Path("research/score_v2_predictive_engine_lock.json")
LOCK_FILE_SHA256 = "2dfc4531a115bfd9ff22dcde4fc0602b312bb5684aeb4591f823594bb57665d1"
IMPLEMENTATION_COMMIT_SHA = "b08a057dc4372d0ab48a25d9fab0950dd0b3c11e"
PREREGISTRATION_COMMIT_SHA = "89bf56bafd594987176f31efaa926ecf02228289"
SHA64 = re.compile(r"^[0-9a-f]{64}$")


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
        raise RuntimeError(f"Cannot read locked implementation file from Git: {revision}:{path}")
    return result.stdout


def verify(root: Path = Path("."), *, filesystem_only: bool = False) -> dict[str, Any]:
    root = root.resolve()
    lock_path = root / LOCK_PATH
    if _sha256(lock_path.read_bytes()) != LOCK_FILE_SHA256:
        raise RuntimeError("Predictive engine lock file differs from its frozen SHA-256")
    lock = _read_json(lock_path)
    if set(lock) != {
        "lock_id",
        "lock_version",
        "locked_date",
        "research_only",
        "production_change",
        "implementation_commit_sha",
        "preregistration_commit_sha",
        "preregistration_file_sha256",
        "immutable_files",
        "change_policy",
        "automatic_override_allowed",
    }:
        raise RuntimeError("Predictive engine lock fields differ from the closed contract")
    if lock.get("lock_id") != "usd_impact_score_v2_predictive_engine_2026-08-25":
        raise RuntimeError("Predictive engine lock ID drifted")
    if lock.get("lock_version") != 1 or lock.get("locked_date") != "2026-08-25":
        raise RuntimeError("Predictive engine lock version/date drifted")
    if lock.get("research_only") is not True or lock.get("production_change") is not False:
        raise RuntimeError("Predictive engine lock must remain research-only")
    if lock.get("implementation_commit_sha") != IMPLEMENTATION_COMMIT_SHA:
        raise RuntimeError("Predictive implementation commit lock mismatch")
    if lock.get("preregistration_commit_sha") != PREREGISTRATION_COMMIT_SHA:
        raise RuntimeError("Predictive preregistration commit lock mismatch")
    if lock.get("automatic_override_allowed") is not False:
        raise RuntimeError("Predictive engine lock unexpectedly permits automatic override")

    immutable = lock.get("immutable_files")
    if not isinstance(immutable, dict) or len(immutable) != 9:
        raise RuntimeError("Predictive engine immutable-file set drifted")
    for relative, expected_hash in immutable.items():
        if not isinstance(relative, str) or relative.startswith(("/", "..")):
            raise RuntimeError("Predictive engine lock contains an unsafe path")
        if not isinstance(expected_hash, str) or not SHA64.fullmatch(expected_hash):
            raise RuntimeError(f"Predictive engine lock has an invalid hash for {relative}")
        current_hash = _sha256((root / relative).read_bytes())
        if current_hash != expected_hash:
            raise RuntimeError(f"Predictive engine file drifted from its pre-holdout lock: {relative}")
        if not filesystem_only:
            committed_hash = _sha256(_git_bytes(root, IMPLEMENTATION_COMMIT_SHA, relative))
            if committed_hash != expected_hash:
                raise RuntimeError(f"Implementation commit does not contain the locked bytes: {relative}")

    if not filesystem_only:
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", IMPLEMENTATION_COMMIT_SHA, "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if ancestry.returncode != 0:
            raise RuntimeError("Locked predictive implementation commit is not an ancestor of HEAD")

    return {
        "status": "verified",
        "filesystem_only": filesystem_only,
        "lock_file_sha256": LOCK_FILE_SHA256,
        "implementation_commit_sha": IMPLEMENTATION_COMMIT_SHA,
        "immutable_files": len(immutable),
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
            f"Score v2 predictive engine lock verified at {report['implementation_commit_sha']}: "
            f"{report['immutable_files']} immutable files"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
