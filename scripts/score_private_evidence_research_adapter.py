#!/usr/bin/env python3
"""Review-only adapter for private Score reproduction evidence.

This module is not wired into Production or the active research workflows. It
defines the narrow reader contract needed to migrate Score v2 predictive and
Score v3 shadow research away from public strict reproduction bundles.

It performs no network access and no writes.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from scripts import build_score_repro_bundle as repro
from usd_impact_score_v2 import WEIGHTS


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("private Score evidence must be a JSON object")
    return payload


def load_private_bundle(
    path: Path,
    *,
    expected_week: str,
    require_synthetic: bool = True,
) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    payload = _read_json(path)
    repro.verify_bundle(payload)

    if payload.get("score_week") != expected_week:
        raise RuntimeError("private Score evidence week mismatch")

    if require_synthetic:
        if payload.get("synthetic_rehearsal") is not True:
            raise RuntimeError("private Score evidence is not marked synthetic")
        if payload.get("do_not_publish") is not True:
            raise RuntimeError("private Score evidence lacks do-not-publish marker")
        if payload.get("pipeline_git_sha") != "0" * 40:
            raise RuntimeError("synthetic private evidence has a non-synthetic pipeline SHA")
        if payload.get("requirements_lock_sha256") != "0" * 64:
            raise RuntimeError("synthetic private evidence has a non-synthetic requirements hash")

    return payload, hashlib.sha256(raw).hexdigest()


def predictive_observation(bundle: dict[str, Any]) -> dict[str, float]:
    published = bundle.get("published")
    components = bundle.get("components")
    if not isinstance(published, dict) or not isinstance(components, dict):
        raise RuntimeError("private Score evidence lacks published/components sections")

    dxy = components.get("DXY")
    if not isinstance(dxy, dict):
        raise RuntimeError("private Score evidence lacks DXY component")

    score = float(published.get("score"))
    dxy_weekly_level = float(dxy.get("weekly_level"))
    if not math.isfinite(score) or not math.isfinite(dxy_weekly_level) or dxy_weekly_level <= 0:
        raise RuntimeError("private Score evidence has invalid predictive values")

    return {"score": score, "dxy_weekly_level": dxy_weekly_level}


def v3_source_levels(bundle: dict[str, Any]) -> dict[str, float]:
    components = bundle.get("components")
    if not isinstance(components, dict):
        raise RuntimeError("private Score evidence lacks components")

    expected = tuple(WEIGHTS.keys())
    if set(components) != set(expected):
        raise RuntimeError("private Score evidence component set differs from production drivers")

    levels: dict[str, float] = {}
    for driver in expected:
        item = components.get(driver)
        if not isinstance(item, dict):
            raise RuntimeError(f"private Score evidence component {driver} is invalid")
        value = float(item.get("weekly_level"))
        if not math.isfinite(value) or value <= 0:
            raise RuntimeError(f"private Score evidence component {driver} level is invalid")
        levels[driver] = value
    return levels
