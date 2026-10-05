#!/usr/bin/env python3
"""Execution-environment profile helpers.

The active online profile is separate from the frozen research lock. This
module validates metadata and installed-package identity; it never installs
packages.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
from pathlib import Path
from typing import Any

PROFILE_KEYS = {"schema_version","profile_id","status","python","platform","lock_path","legacy_frozen_lock","activation"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
PIN = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s]+)$")
EXPECTED_CALLERS = {
    "quality.yml","weekly.yml","python-security.yml","repro-attestation.yml",
    "repro-rehearsal.yml","methodology-health.yml",
    "score-research-evidence-health.yml","research-validation.yml",
    "score-v3-shadow.yml","score-v2-predictive.yml",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_relative(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must stay inside repository root")
    return path


def parse_lock(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = PIN.fullmatch(line)
        if not match:
            raise ValueError(f"lock contains non-exact requirement: {line}")
        name = re.sub(r"[-_.]+", "-", match.group(1)).lower()
        if name in pins:
            raise ValueError(f"duplicate locked package: {name}")
        pins[name] = match.group(2)
    if not pins:
        raise ValueError("lock contains no packages")
    return pins


def load_profile(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != PROFILE_KEYS:
        raise ValueError("environment profile fields differ from closed schema")
    if payload["schema_version"] != 1:
        raise ValueError("unsupported environment profile schema")
    if payload["status"] not in {"candidate_not_active", "active_candidate"}:
        raise ValueError("unsupported environment profile status")
    if payload["python"] != {"implementation":"CPython","major_minor":"3.11"}:
        raise ValueError("unexpected Python runtime contract")
    activation = payload["activation"]
    if not isinstance(activation, dict) or set(activation) != {"active","caller_allowlist"}:
        raise ValueError("activation fields differ from closed schema")
    callers = activation["caller_allowlist"]
    if not isinstance(callers, list) or len(callers) != len(set(callers)):
        raise ValueError("caller_allowlist must be a unique list")
    if payload["status"] == "candidate_not_active":
        if activation != {"active":False,"caller_allowlist":[]}:
            raise ValueError("inactive candidate must not activate callers")
    else:
        if activation.get("active") is not True or set(callers) != EXPECTED_CALLERS:
            raise ValueError("active candidate caller allowlist is incomplete or broadened")
    legacy = payload["legacy_frozen_lock"]
    if not isinstance(legacy, dict) or set(legacy) != {"path","sha256","purpose"}:
        raise ValueError("legacy lock fields differ from closed schema")
    if not SHA256.fullmatch(str(legacy["sha256"])):
        raise ValueError("legacy lock sha256 must be lowercase SHA-256")
    _safe_relative(payload["lock_path"], "lock_path")
    _safe_relative(legacy["path"], "legacy_frozen_lock.path")
    return payload


def verify_profile(root: Path, profile_path: Path) -> dict[str, Any]:
    root = root.resolve()
    profile = load_profile(profile_path)
    lock_rel = _safe_relative(profile["lock_path"], "lock_path")
    legacy_rel = _safe_relative(profile["legacy_frozen_lock"]["path"], "legacy_frozen_lock.path")
    lock = root / lock_rel
    legacy = root / legacy_rel
    for path,label in ((lock,"candidate lock"),(legacy,"legacy lock")):
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"{label} must be a regular file")
    if sha256_file(legacy) != profile["legacy_frozen_lock"]["sha256"]:
        raise ValueError("legacy frozen lock hash mismatch")
    candidate = parse_lock(lock)
    frozen = parse_lock(legacy)
    if candidate.get("urllib3") != "2.8.0":
        raise ValueError("candidate runtime must contain patched urllib3 2.8.0")
    if frozen.get("urllib3") != "2.7.0":
        raise ValueError("legacy frozen lock identity changed")
    return {
        "status": "verified_active_candidate" if profile["activation"]["active"] else "verified_candidate_not_active",
        "profile_id": profile["profile_id"],
        "active": bool(profile["activation"]["active"]),
        "lock_path": lock_rel.as_posix(),
        "lock_sha256": sha256_file(lock),
        "legacy_lock_path": legacy_rel.as_posix(),
        "legacy_lock_sha256": sha256_file(legacy),
        "candidate_packages": len(candidate),
        "legacy_packages": len(frozen),
        "caller_allowlist": list(profile["activation"]["caller_allowlist"]),
    }


def verify_installed_packages(lock_path: Path) -> dict[str, Any]:
    expected = parse_lock(lock_path)
    installed = {
        re.sub(r"[-_.]+","-",d.metadata["Name"]).lower(): d.version
        for d in importlib.metadata.distributions()
        if d.metadata.get("Name")
    }
    missing = sorted(k for k in expected if k not in installed)
    wrong = sorted(
        f"{k}: expected {expected[k]}, got {installed[k]}"
        for k in expected if k in installed and installed[k] != expected[k]
    )
    if missing or wrong:
        raise ValueError(
            "installed environment differs from lock: "
            + "; ".join([*(f"missing {x}" for x in missing), *wrong])
        )
    return {"status":"installed_environment_matches_lock","packages":len(expected)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--profile", type=Path, default=Path("runtime/active-environment.json"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    profile_path = args.profile if args.profile.is_absolute() else root / args.profile
    report = verify_profile(root, profile_path)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"{report['status']}: {report['profile_id']} -> {report['lock_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
