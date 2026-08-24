#!/usr/bin/env python3
"""Anti-peeking reporting gate for the Score v2 predictive study."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts import score_v2_predictive_ingestion as ingestion
from scripts import score_v2_predictive_manifest as manifest_v2p
from scripts import score_v2_predictive_metrics as metrics

CHECKPOINTS = (13, 26, 39, 52)
INTERIM_CHECKPOINTS = (13, 26, 39)
CHECKPOINT_DIR = Path("research/predictive/checkpoints")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _checkpoint_path(root: Path, resolved: int) -> Path:
    return root / CHECKPOINT_DIR / f"score_v2_predictive_checkpoint_{resolved:03d}.json"


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object in {path}")
    return payload


def _validate_checkpoint(root: Path, manifest: dict[str, Any], resolved: int) -> None:
    path = _checkpoint_path(root, resolved)
    payload = _read_json(path)
    expected_prefix = metrics.evidence_prefix_sha256(manifest["entries"], resolved)
    for field, expected in {
        "$schema": "../../score_v2_predictive_checkpoint.schema.json",
        "reporting_version": 1,
        "study": "usd_impact_score_v2_one_week_dxy_direction_2026-08-25",
        "research_only": True,
        "production_change": False,
        "resolved_predictions": resolved,
        "weekly_observations": resolved + 1,
        "locked_preregistration_commit_sha": manifest_v2p.LOCKED_PREREGISTRATION_SHA,
        "implementation_contract_sha256": manifest_v2p.IMPLEMENTATION_CONTRACT_SHA256,
        "evidence_prefix_sha256": expected_prefix,
        "automatic_site_claim_performed": False,
        "production_promotion_performed": False,
    }.items():
        if payload.get(field) != expected:
            raise RuntimeError(f"Predictive checkpoint {resolved:03d} {field} mismatch")
    if resolved in INTERIM_CHECKPOINTS:
        if payload.get("report_type") != "predictive_integrity_checkpoint":
            raise RuntimeError(f"Predictive interim checkpoint {resolved:03d} type drifted")
        if payload.get("endpoint_values_emitted") is not False:
            raise RuntimeError(f"Predictive interim checkpoint {resolved:03d} exposed endpoint values")
        if payload.get("performance_calculated") is not False:
            raise RuntimeError(f"Predictive interim checkpoint {resolved:03d} calculated performance")
        forbidden = {"primary_endpoint", "comparators", "secondary_endpoints", "meaningful_predictive_evidence_gate"}
        if forbidden.intersection(payload):
            raise RuntimeError(f"Predictive interim checkpoint {resolved:03d} contains performance fields")
    else:
        expected = metrics.build_formal_report(root)
        if payload != expected:
            raise RuntimeError("Formal predictive checkpoint differs from locked deterministic recomputation")


def validate_weekly(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    manifest = manifest_v2p.load_manifest(root / manifest_v2p.MANIFEST_PATH)
    status = manifest_v2p.validate_manifest(manifest, root=root)
    records = ingestion.validate_all_records(root, manifest)
    resolved = int(status["resolved_predictions"])

    for checkpoint in CHECKPOINTS:
        path = _checkpoint_path(root, checkpoint)
        if checkpoint < resolved and not path.exists():
            raise RuntimeError(
                f"Missing required predictive checkpoint {checkpoint:03d}; "
                "do not reconstruct it after later outcomes are visible"
            )
        if path.exists():
            if checkpoint > resolved:
                raise RuntimeError(f"Predictive checkpoint {checkpoint:03d} exists before it is due")
            _validate_checkpoint(root, manifest, checkpoint)

    return {
        "report_type": "predictive_weekly_integrity_validation",
        "reporting_version": 1,
        "research_only": True,
        "production_change": False,
        "predictive_power_status": "not_established_pending_52_resolved_predictions",
        "weekly_observations": int(status["weekly_observations"]),
        "resolved_predictions": resolved,
        "latest_week": records[-1]["week"] if records else None,
        "record_integrity_validated": True,
        "endpoint_values_emitted": False,
        "performance_calculated": False,
        "automatic_site_claim_performed": False,
        "production_promotion_performed": False,
    }


def checkpoint_if_due(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    validation = validate_weekly(root)
    resolved = int(validation["resolved_predictions"])
    if resolved not in CHECKPOINTS:
        return {
            **validation,
            "status": "validated_no_checkpoint_due",
            "checkpoint_due": False,
            "checkpoint_written": False,
            "checkpoint_file": None,
        }

    manifest = manifest_v2p.load_manifest(root / manifest_v2p.MANIFEST_PATH)
    path = _checkpoint_path(root, resolved)
    if resolved in INTERIM_CHECKPOINTS:
        payload: dict[str, Any] = {
            "$schema": "../../score_v2_predictive_checkpoint.schema.json",
            "report_type": "predictive_integrity_checkpoint",
            "reporting_version": 1,
            "study": "usd_impact_score_v2_one_week_dxy_direction_2026-08-25",
            "research_only": True,
            "production_change": False,
            "resolved_predictions": resolved,
            "weekly_observations": resolved + 1,
            "latest_week": validation["latest_week"],
            "locked_preregistration_commit_sha": manifest_v2p.LOCKED_PREREGISTRATION_SHA,
            "implementation_contract_sha256": manifest_v2p.IMPLEMENTATION_CONTRACT_SHA256,
            "evidence_prefix_sha256": metrics.evidence_prefix_sha256(manifest["entries"], resolved),
            "endpoint_values_emitted": False,
            "performance_calculated": False,
            "integrity": {
                "consecutive_weekly_grid": True,
                "immutable_bundle_binding": True,
                "append_only_record_hashes": True,
                "failed_or_missing_origins": 0,
            },
            "decision_performed": False,
            "automatic_site_claim_performed": False,
            "production_promotion_performed": False,
        }
    else:
        payload = metrics.build_formal_report(root)

    raw = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != raw:
            raise RuntimeError(f"Existing predictive checkpoint differs from deterministic recomputation: {path}")
        status = "checkpoint_already_recorded_noop"
        written = False
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(raw, encoding="utf-8")
        status = "checkpoint_written"
        written = True

    return {
        **validation,
        "status": status,
        "checkpoint_due": True,
        "checkpoint_written": written,
        "checkpoint_file": str(path.relative_to(root)),
        "checkpoint_sha256": _sha256_file(path),
        "formal_performance_report": resolved == 52,
    }


def readiness(root: Path = Path(".")) -> dict[str, Any]:
    validation = validate_weekly(root)
    return {
        **validation,
        "status": "predictive_implementation_ready",
        "first_origin": manifest_v2p.FIRST_ORIGIN.isoformat(),
        "required_resolved_predictions": manifest_v2p.PREDICTIVE_ORIGINS,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--mode", choices=("readiness", "run"), default="run")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = readiness(args.root) if args.mode == "readiness" else checkpoint_if_due(args.root)
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
