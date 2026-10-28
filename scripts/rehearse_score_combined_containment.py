#!/usr/bin/env python3
"""No-write readiness rehearsal for the combined Score rights containment design.

Review-only. Requires the active HOLD manifest, exercises aggregate-only public
Score/research transforms, and builds the provider-free synthetic private
evidence fixture in temporary storage.

No provider retrieval, cloud storage, public artifact replacement, workflow
dispatch, or Production mutation is performed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from scripts import build_score_public_safe_artifact as public_score
from scripts import build_score_public_safe_research as public_research
from scripts import build_synthetic_private_score_evidence as synthetic_private

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


def _assert_public_payload_safe(label: str, payload: dict[str, Any]) -> None:
    raw = json.dumps(payload, sort_keys=True)
    for term in FORBIDDEN_PUBLIC_TERMS:
        if term in raw:
            raise RuntimeError(f"{label} contains forbidden public term: {term}")


def rehearse(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()

    publication_gate = _load_json(
        repo_root / "governance" / "score-publication-rights-gate.json",
        "publication rights gate",
    )
    surface = _load_json(
        repo_root / "governance" / "score-public-rights-surface.json",
        "public rights surface manifest",
    )

    if publication_gate.get("state") != "hold":
        raise RuntimeError("publication rights gate is not HOLD")
    if publication_gate.get("decision_receipt") is not None:
        raise RuntimeError("publication rights gate unexpectedly has a decision receipt")
    if surface.get("state") != "hold":
        raise RuntimeError("public rights surface manifest is not HOLD")
    if surface.get("production_change_authorized") is not False:
        raise RuntimeError("public rights surface unexpectedly authorizes Production")

    expected_classes = {"A", "B", "C", "D", "E", "F"}
    if set((surface.get("classes") or {}).keys()) != expected_classes:
        raise RuntimeError("public rights surface class set changed unexpectedly")

    score_source = _load_json(
        repo_root / "public/data/usd_impact_score_v2.json",
        "current Score source",
    )
    safe_score = public_score.build_public_safe_payload(score_source)
    public_score.assert_public_safe(safe_score)

    pit_source = _load_json(
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

    safe_pit = public_research.build_point_in_time(pit_source)
    safe_robustness = public_research.build_robustness(robustness_source)
    safe_vintage = public_research.build_vintage(vintage_source)

    for label, payload in (
        ("public-safe Score", safe_score),
        ("public-safe point-in-time", safe_pit),
        ("public-safe robustness", safe_robustness),
        ("public-safe vintage", safe_vintage),
    ):
        _assert_public_payload_safe(label, payload)

    with tempfile.TemporaryDirectory(prefix="score-combined-containment-") as tmp:
        synthetic_root = Path(tmp) / "private-evidence"
        synthetic_report = synthetic_private.build(synthetic_root)

        if synthetic_report.get("synthetic_rehearsal") is not True:
            raise RuntimeError("synthetic private evidence lacks rehearsal marker")
        if synthetic_report.get("do_not_publish") is not True:
            raise RuntimeError("synthetic private evidence lacks do-not-publish marker")
        if synthetic_report.get("provider_derived_values") is not False:
            raise RuntimeError("synthetic private evidence is not provider-free")

        latest_raw = (synthetic_root / "score_repro_bundle_latest.json").read_bytes()
        latest_sha = hashlib.sha256(latest_raw).hexdigest()
        if latest_sha != synthetic_report.get("latest_sha256"):
            raise RuntimeError("synthetic private evidence latest hash mismatch")

    return {
        "status": "passed",
        "review_only": True,
        "writes_performed": False,
        "provider_refetch_performed": False,
        "cloud_storage_action_performed": False,
        "production_workflow_changed": False,
        "publication_gate_state": publication_gate["state"],
        "rights_surface_state": surface["state"],
        "rights_surface_classes": sorted(expected_classes),
        "production_change_authorized": surface["production_change_authorized"],
        "public_static_path_count": len(surface.get("static_paths") or []),
        "public_archive_pattern_count": len(surface.get("dated_archive_patterns") or []),
        "score_week": safe_score["latest"]["week_ending"],
        "aggregate_score": safe_score["latest"]["score"],
        "aggregate_regime": safe_score["latest"]["regime"],
        "public_safe_history_rows": len(safe_score["history"]),
        "public_safe_score_sha256": _sha256_json(safe_score),
        "public_safe_point_in_time_sha256": _sha256_json(safe_pit),
        "public_safe_robustness_sha256": _sha256_json(safe_robustness),
        "public_safe_vintage_sha256": _sha256_json(safe_vintage),
        "synthetic_private_latest_sha256": synthetic_report["latest_sha256"],
        "synthetic_private_archive_count": synthetic_report["archive_count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    print(json.dumps(rehearse(args.repo_root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
