#!/usr/bin/env python3
"""Consolidated no-write rehearsal for Score rights containment.

Review-only. This script exercises the current HOLD gate, aggregate-only public
Score transformation, aggregate-only research transformation, current strict
evidence parity rehearsal, and provider-free synthetic private-evidence fixture.

It performs no provider retrieval, no cloud storage action, no repository write,
no public-file replacement, and no Production workflow mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from scripts import build_score_public_safe_artifact as public_safe
from scripts import build_score_public_safe_research as public_research
from scripts import build_synthetic_private_score_evidence as synthetic_private
from scripts import rehearse_score_rights_containment as parity_rehearsal

FORBIDDEN_PUBLIC_TERMS = (
    "Yahoo Finance",
    "DX-Y.NYB",
    "CL=F",
    "^GSPC",
    "^VIX",
    "BTC-USD",
    "GC=F",
    '"source_provenance"',
    '"source_url"',
    '"weekly_level"',
    '"z_clipped"',
    '"contribution"',
)


def _load_json(path: Path, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must be a JSON object")
    return payload


def _sha256_json(payload: Any) -> str:
    raw = (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def rehearse(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()

    gate_path = repo_root / "governance" / "score-publication-rights-gate.json"
    gate = _load_json(gate_path, "Score publication rights gate")
    if gate.get("state") != "hold":
        raise RuntimeError("Score publication rights gate is not HOLD")
    if gate.get("decision_receipt") is not None or gate.get("approved_by") is not None:
        raise RuntimeError("HOLD gate unexpectedly contains approval metadata")

    score_source = _load_json(
        repo_root / "public" / "data" / "usd_impact_score_v2.json",
        "current Score source",
    )
    safe_score = public_safe.build_public_safe_payload(score_source)
    public_safe.assert_public_safe(safe_score)

    point_source = _load_json(
        repo_root / "public/data/research/score_v2_point_in_time_latest.json",
        "point-in-time research",
    )
    robustness_source = _load_json(
        repo_root / "public/data/research/score_v2_robustness_latest.json",
        "robustness research",
    )
    vintage_source = _load_json(
        repo_root / "public/data/research/score_v2_vintage_comparison_latest.json",
        "vintage research",
    )

    safe_point = public_research.build_point_in_time(point_source)
    safe_robustness = public_research.build_robustness(robustness_source)
    safe_vintage = public_research.build_vintage(vintage_source)

    for label, payload in (
        ("score", safe_score),
        ("point_in_time", safe_point),
        ("robustness", safe_robustness),
        ("vintage", safe_vintage),
    ):
        raw = json.dumps(payload, sort_keys=True)
        for term in FORBIDDEN_PUBLIC_TERMS:
            if term in raw:
                raise RuntimeError(
                    f"aggregate-safe {label} output contains forbidden term: {term}"
                )

    parity = parity_rehearsal.rehearse(repo_root)
    if parity.get("status") != "passed":
        raise RuntimeError("current strict/private aggregate parity rehearsal failed")

    with tempfile.TemporaryDirectory(prefix="score-full-containment-") as tmp:
        synthetic_root = Path(tmp) / "synthetic-private-evidence"
        synthetic = synthetic_private.build(synthetic_root)

        if synthetic.get("provider_derived_values") is not False:
            raise RuntimeError("synthetic private evidence is not provider-free")
        if synthetic.get("do_not_publish") is not True:
            raise RuntimeError("synthetic private evidence lacks do-not-publish guard")
        if synthetic.get("synthetic_rehearsal") is not True:
            raise RuntimeError("synthetic private evidence lacks rehearsal marker")

        latest_path = synthetic_root / "score_repro_bundle_latest.json"
        latest_raw = latest_path.read_bytes()
        if hashlib.sha256(latest_raw).hexdigest() != synthetic["latest_sha256"]:
            raise RuntimeError("synthetic private evidence hash mismatch")

    return {
        "status": "passed",
        "review_only": True,
        "writes_performed": False,
        "provider_refetch_performed": False,
        "cloud_storage_action_performed": False,
        "production_workflow_changed": False,
        "rights_gate_state": gate["state"],
        "score_week": safe_score["latest"]["week_ending"],
        "aggregate_score": safe_score["latest"]["score"],
        "aggregate_regime": safe_score["latest"]["regime"],
        "public_safe_history_rows": len(safe_score["history"]),
        "public_safe_score_sha256": _sha256_json(safe_score),
        "public_safe_point_in_time_sha256": _sha256_json(safe_point),
        "public_safe_robustness_sha256": _sha256_json(safe_robustness),
        "public_safe_vintage_sha256": _sha256_json(safe_vintage),
        "private_strict_bundle_sha256": parity["private_strict_bundle_sha256"],
        "synthetic_private_latest_sha256": synthetic["latest_sha256"],
        "synthetic_private_archive_count": synthetic["archive_count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    print(json.dumps(rehearse(args.repo_root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
