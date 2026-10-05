#!/usr/bin/env python3
"""Phase A environment-profile validation. This module never activates or installs a runtime."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import re
from pathlib import Path
from typing import Any

PROFILE_KEYS = {"schema_version","profile_id","status","python","platform","lock_path","legacy_frozen_lock","activation"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
PIN = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s]+)$")


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
    if payload["schema_version"] != 1 or payload["status"] != "candidate_not_active":
        raise ValueError("Phase A profile must remain candidate_not_active")
    if payload["python"] != {"implementation":"CPython","major_minor":"3.11"}:
        raise ValueError("unexpected Python runtime contract")
    if payload["activation"] != {"active":False,"caller_allowlist":[]}:
        raise ValueError("Phase A must not activate callers")
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
    lock = root / _safe_relative(profile["lock_path"], "lock_path")
    legacy = root / _safe_relative(profile["legacy_frozen_lock"]["path"], "legacy_frozen_lock.path")
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
    return {"status":"verified_candidate_not_active","profile_id":profile["profile_id"],"active":False,"candidate_packages":len(candidate),"legacy_packages":len(frozen),"candidate_lock_sha256":sha256_file(lock)}


def verify_installed_packages(lock_path: Path) -> dict[str, Any]:
    expected = parse_lock(lock_path)
    installed = {re.sub(r"[-_.]+","-",d.metadata["Name"]).lower():d.version for d in importlib.metadata.distributions() if d.metadata.get("Name")}
    missing = sorted(k for k in expected if k not in installed)
    wrong = sorted(f"{k}: expected {expected[k]}, got {installed[k]}" for k in expected if k in installed and installed[k] != expected[k])
    if missing or wrong:
        raise ValueError("installed environment differs from lock: " + "; ".join([*(f"missing {x}" for x in missing),*wrong]))
    return {"status":"installed_environment_matches_lock","packages":len(expected)}
