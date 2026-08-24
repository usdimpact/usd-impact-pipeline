#!/usr/bin/env python3
"""Validate the append-only Score v2 prospective predictive evidence ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

LOCKED_PREREGISTRATION_SHA = "89bf56bafd594987176f31efaa926ecf02228289"
LOCKED_PREREGISTRATION_FILE_SHA256 = (
    "36accc42e4915bb48caa1c4d2fd0fac8ba27c51c0eb988916990c415830e3ca0"
)
IMPLEMENTATION_CONTRACT_SHA256 = (
    "13c2b546abda5c7ba44bdf178371346062d6717c1ed7f10f6a16aac319a9f789"
)
MANIFEST_PATH = Path("research/score_v2_predictive_manifest.json")
PROTOCOL_PATH = Path("research/score_v2_predictive_preregistration.json")
CONTRACT_PATH = Path("research/score_v2_predictive_implementation_contract.json")
FIRST_ORIGIN = date(2026, 8, 28)
PREDICTIVE_ORIGINS = 52
WEEKLY_OBSERVATIONS = 53
INTERIM_CHECKPOINTS = (13, 26, 39)
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
ENTRY_KEYS = {
    "week",
    "record_role",
    "recorded_at_utc",
    "source_v2_bundle_sha256",
    "source_v2_pipeline_commit_sha",
    "source_v2_attestation_status",
    "source_v2_attestation_run_id",
    "locked_preregistration_commit_sha",
    "implementation_contract_sha256",
    "weekly_record_file",
    "weekly_record_sha256",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object in {path}")
    return payload


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    return _read_json(path)


def validate_locked_sources(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    protocol_path = root / PROTOCOL_PATH
    contract_path = root / CONTRACT_PATH
    if sha256_file(protocol_path) != LOCKED_PREREGISTRATION_FILE_SHA256:
        raise RuntimeError("Predictive preregistration file differs from its locked SHA-256")
    if sha256_file(contract_path) != IMPLEMENTATION_CONTRACT_SHA256:
        raise RuntimeError("Predictive implementation contract differs from its locked SHA-256")

    protocol = _read_json(protocol_path)
    contract = _read_json(contract_path)
    if protocol.get("protocol_id") != "usd_impact_score_v2_one_week_dxy_direction_2026-08-25":
        raise RuntimeError("Unexpected predictive preregistration protocol ID")
    if protocol.get("current_predictive_claim_authorized") is not False:
        raise RuntimeError("Preregistration unexpectedly authorizes a current predictive claim")
    if protocol.get("knowledge_boundary", {}).get("first_untouched_prediction_origin") != FIRST_ORIGIN.isoformat():
        raise RuntimeError("Preregistration first origin drifted")
    if protocol.get("knowledge_boundary", {}).get("required_resolved_predictions") != PREDICTIVE_ORIGINS:
        raise RuntimeError("Preregistration sample size drifted")

    if contract.get("contract_id") != "usd_impact_score_v2_predictive_implementation_2026-08-25":
        raise RuntimeError("Unexpected predictive implementation contract ID")
    if contract.get("locked_preregistration_commit_sha") != LOCKED_PREREGISTRATION_SHA:
        raise RuntimeError("Implementation contract preregistration commit lock mismatch")
    if contract.get("locked_preregistration_file_sha256") != LOCKED_PREREGISTRATION_FILE_SHA256:
        raise RuntimeError("Implementation contract preregistration file lock mismatch")
    if contract.get("research_only") is not True or contract.get("production_change") is not False:
        raise RuntimeError("Predictive implementation contract must remain research-only")
    grid = contract.get("study_grid") or {}
    if grid.get("first_origin") != FIRST_ORIGIN.isoformat():
        raise RuntimeError("Predictive implementation first origin drifted")
    if grid.get("predictive_origins") != PREDICTIVE_ORIGINS:
        raise RuntimeError("Predictive implementation origin count drifted")
    if grid.get("weekly_observations") != WEEKLY_OBSERVATIONS:
        raise RuntimeError("Predictive implementation observation count drifted")
    if grid.get("backfill_allowed") is not False or grid.get("week_skip_allowed") is not False:
        raise RuntimeError("Predictive implementation unexpectedly permits gaps or backfill")
    reporting = contract.get("reporting") or {}
    if tuple(reporting.get("integrity_only_resolved_prediction_checkpoints") or ()) != INTERIM_CHECKPOINTS:
        raise RuntimeError("Predictive interim checkpoint schedule drifted")
    if reporting.get("formal_performance_resolved_prediction_checkpoint") != PREDICTIVE_ORIGINS:
        raise RuntimeError("Predictive formal checkpoint drifted")
    if reporting.get("interim_performance_calculation_allowed") is not False:
        raise RuntimeError("Predictive implementation unexpectedly permits interim performance calculation")
    if reporting.get("automatic_site_claim_allowed") is not False:
        raise RuntimeError("Predictive implementation unexpectedly permits an automatic site claim")

    return {
        "status": "verified",
        "locked_preregistration_commit_sha": LOCKED_PREREGISTRATION_SHA,
        "locked_preregistration_file_sha256": LOCKED_PREREGISTRATION_FILE_SHA256,
        "implementation_contract_sha256": IMPLEMENTATION_CONTRACT_SHA256,
    }


def _require_sha(value: Any, *, length: int, field: str) -> str:
    text = str(value)
    pattern = SHA40 if length == 40 else SHA64
    if not pattern.fullmatch(text):
        raise RuntimeError(f"{field} is not a lowercase {length}-hex SHA")
    return text


def validate_manifest(
    manifest: dict[str, Any],
    *,
    root: Path = Path("."),
) -> dict[str, Any]:
    validate_locked_sources(root)
    expected_top = {
        "$schema",
        "manifest_version",
        "study",
        "research_only",
        "production_change",
        "predictive_power_status",
        "append_only",
        "locked_preregistration_commit_sha",
        "locked_preregistration_file_sha256",
        "implementation_contract_sha256",
        "first_prediction_origin",
        "required_predictive_origins",
        "required_weekly_observations",
        "interim_integrity_checkpoints",
        "entries",
    }
    if set(manifest) != expected_top:
        raise RuntimeError("Predictive manifest top-level fields differ from the closed contract")
    if manifest.get("$schema") != "./score_v2_predictive_manifest.schema.json":
        raise RuntimeError("Predictive manifest schema reference drifted")
    if manifest.get("manifest_version") != 1:
        raise RuntimeError("Unsupported predictive manifest version")
    if manifest.get("study") != "usd_impact_score_v2_one_week_dxy_direction_2026-08-25":
        raise RuntimeError("Predictive manifest study ID drifted")
    if manifest.get("research_only") is not True or manifest.get("production_change") is not False:
        raise RuntimeError("Predictive manifest must remain research-only")
    if manifest.get("predictive_power_status") != "not_established_pending_52_resolved_predictions":
        raise RuntimeError("Predictive manifest may not claim established predictive power")
    if manifest.get("append_only") is not True:
        raise RuntimeError("Predictive manifest must remain append-only")
    if manifest.get("locked_preregistration_commit_sha") != LOCKED_PREREGISTRATION_SHA:
        raise RuntimeError("Predictive manifest preregistration commit lock mismatch")
    if manifest.get("locked_preregistration_file_sha256") != LOCKED_PREREGISTRATION_FILE_SHA256:
        raise RuntimeError("Predictive manifest preregistration file lock mismatch")
    if manifest.get("implementation_contract_sha256") != IMPLEMENTATION_CONTRACT_SHA256:
        raise RuntimeError("Predictive manifest implementation contract lock mismatch")
    if manifest.get("first_prediction_origin") != FIRST_ORIGIN.isoformat():
        raise RuntimeError("Predictive manifest first origin drifted")
    if manifest.get("required_predictive_origins") != PREDICTIVE_ORIGINS:
        raise RuntimeError("Predictive manifest origin count drifted")
    if manifest.get("required_weekly_observations") != WEEKLY_OBSERVATIONS:
        raise RuntimeError("Predictive manifest observation count drifted")
    if tuple(manifest.get("interim_integrity_checkpoints") or ()) != INTERIM_CHECKPOINTS:
        raise RuntimeError("Predictive manifest interim checkpoint schedule drifted")

    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise RuntimeError("Predictive manifest entries must be an array")
    if len(entries) > WEEKLY_OBSERVATIONS:
        raise RuntimeError("Predictive manifest exceeds its 53-observation boundary")
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
            raise RuntimeError(f"Predictive manifest entry {index + 1} differs from the closed contract")
        expected_week = FIRST_ORIGIN + timedelta(days=7 * index)
        if entry.get("week") != expected_week.isoformat():
            raise RuntimeError(f"Predictive manifest gap or out-of-order week at entry {index + 1}")
        expected_role = "terminal_outcome" if index == PREDICTIVE_ORIGINS else "predictive_origin"
        if entry.get("record_role") != expected_role:
            raise RuntimeError(f"Predictive manifest record role drifted at {expected_week}")
        if not str(entry.get("recorded_at_utc", "")).endswith("+00:00"):
            raise RuntimeError(f"Predictive manifest entry {expected_week} lacks a UTC timestamp")
        if entry.get("source_v2_attestation_status") != "passed":
            raise RuntimeError(f"Predictive manifest entry {expected_week} lacks passed attestation")
        if not isinstance(entry.get("source_v2_attestation_run_id"), int) or entry["source_v2_attestation_run_id"] < 1:
            raise RuntimeError(f"Predictive manifest entry {expected_week} has invalid attestation run ID")
        if entry.get("locked_preregistration_commit_sha") != LOCKED_PREREGISTRATION_SHA:
            raise RuntimeError(f"Predictive manifest entry {expected_week} protocol lock mismatch")
        if entry.get("implementation_contract_sha256") != IMPLEMENTATION_CONTRACT_SHA256:
            raise RuntimeError(f"Predictive manifest entry {expected_week} contract lock mismatch")
        _require_sha(entry.get("source_v2_bundle_sha256"), length=64, field="source_v2_bundle_sha256")
        _require_sha(entry.get("source_v2_pipeline_commit_sha"), length=40, field="source_v2_pipeline_commit_sha")
        _require_sha(entry.get("weekly_record_sha256"), length=64, field="weekly_record_sha256")
        expected_file = f"score_v2_predictive_week_{expected_week.isoformat()}.json"
        if entry.get("weekly_record_file") != expected_file:
            raise RuntimeError(f"Predictive manifest record filename drifted at {expected_week}")

    return {
        "status": "verified",
        "weekly_observations": len(entries),
        "resolved_predictions": max(0, len(entries) - 1),
        "latest_week": entries[-1]["week"] if entries else None,
        "study_complete": len(entries) == WEEKLY_OBSERVATIONS,
    }


def append_entry(
    manifest: dict[str, Any],
    entry: dict[str, Any],
    *,
    root: Path = Path("."),
) -> dict[str, Any]:
    validate_manifest(manifest, root=root)
    if len(manifest["entries"]) >= WEEKLY_OBSERVATIONS:
        raise RuntimeError("Predictive manifest is complete and cannot accept another entry")
    updated = json.loads(json.dumps(manifest))
    updated["entries"].append(entry)
    validate_manifest(updated, root=root)
    return updated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    path = args.manifest or (root / MANIFEST_PATH)
    report = validate_manifest(load_manifest(path), root=root)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(
            "Score v2 predictive manifest verified: "
            f"{report['weekly_observations']} observations, "
            f"{report['resolved_predictions']} resolved predictions"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
