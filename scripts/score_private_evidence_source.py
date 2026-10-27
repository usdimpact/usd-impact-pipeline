#!/usr/bin/env python3
"""Private strict-bundle evidence source adapter.

Review-only prototype for rights-containment migration.

This module does not fetch provider data and is not wired into production or
research workflows. It validates a caller-supplied non-public evidence root,
requires latest/archive byte identity for the requested week, and delegates the
strict bundle structure/arithmetic checks to the existing reproduction verifier.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts import build_score_repro_bundle as repro


@dataclass(frozen=True)
class PrivateEvidenceBundle:
    week: str
    bundle: dict[str, Any]
    sha256: str
    latest_path: Path
    archive_path: Path


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object in {path}")
    return payload


def _assert_non_public_path(root: Path, candidate: Path) -> None:
    public_root = (root / "public").resolve()
    resolved = candidate.resolve()
    if resolved == public_root or resolved.is_relative_to(public_root):
        raise RuntimeError(
            f"Private Score evidence must not be loaded from a public path: {resolved}"
        )


def load_private_strict_bundle(
    repo_root: Path,
    evidence_root: Path,
    week: str,
) -> PrivateEvidenceBundle:
    """Load a strict Score v2 bundle from a non-public evidence tree.

    Expected layout under evidence_root:
      latest/repro_bundle.json
      archive/YYYY-MM-DD/repro_bundle.json

    The adapter intentionally does not define storage, credentials, retention,
    encryption or transport. Those remain separate governance decisions.
    """

    repo_root = repo_root.resolve()
    evidence_root = evidence_root.resolve()

    _assert_non_public_path(repo_root, evidence_root)

    latest_path = evidence_root / "latest" / "repro_bundle.json"
    archive_path = evidence_root / "archive" / week / "repro_bundle.json"

    for path in (latest_path, archive_path):
        _assert_non_public_path(repo_root, path)
        if not path.is_file():
            raise RuntimeError(f"Private strict Score evidence is missing: {path}")

    latest_raw = latest_path.read_bytes()
    archive_raw = archive_path.read_bytes()
    latest_sha = sha256_bytes(latest_raw)
    archive_sha = sha256_bytes(archive_raw)
    if latest_sha != archive_sha:
        raise RuntimeError("Private strict Score latest/archive bundle hashes differ")

    bundle = _read_object(latest_path)
    if bundle.get("score_week") != week:
        raise RuntimeError(
            "Private strict Score evidence week differs from requested week"
        )

    repro.verify_bundle(bundle)

    return PrivateEvidenceBundle(
        week=week,
        bundle=bundle,
        sha256=latest_sha,
        latest_path=latest_path,
        archive_path=archive_path,
    )


def extract_research_levels(
    evidence: PrivateEvidenceBundle,
    expected_drivers: tuple[str, ...] | list[str],
) -> dict[str, float]:
    """Return the exact weekly source levels needed by frozen research readers."""

    components = evidence.bundle.get("components")
    if not isinstance(components, dict):
        raise RuntimeError("Private strict Score evidence has no components object")

    expected = list(expected_drivers)
    if set(components) != set(expected):
        raise RuntimeError("Private strict Score component set differs from research contract")

    levels: dict[str, float] = {}
    for driver in expected:
        component = components.get(driver)
        if not isinstance(component, dict):
            raise RuntimeError(f"Private strict Score component is invalid: {driver}")
        value = component.get("weekly_level")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RuntimeError(f"Private strict Score weekly level is invalid: {driver}")
        levels[driver] = float(value)
    return levels
