#!/usr/bin/env python3
"""Freeze the retrospective initialization matrix for preregistered Score v3 research.

Research-only. This script snapshots the complete weekly production input levels
through 2026-08-21 using the Score v2 source/data contract. The snapshot is
current-vintage retrospective design information, not an as-published history.
It is deliberately write-once: provider revisions must never replace the frozen
matrix after candidate research begins.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import usd_impact_score_v2 as score_v2

LOCKED_PREREGISTRATION_SHA = "bf49152fa6005edd20b770db287924d56cfa7499"
CUTOFF_WEEK = date(2026, 8, 21)
PROTOCOL_PATH = Path("research/score_v3_preregistration.json")
METHODOLOGY_CONTRACT_PATH = Path("public/data/score_v2_methodology.json")
REQUIREMENTS_LOCK_PATH = Path("requirements.lock")
DEFAULT_MATRIX_PATH = Path("research/score_v3_initialization_2026-08-21.csv")
DEFAULT_MANIFEST_PATH = Path("research/score_v3_initialization_2026-08-21.manifest.json")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _logger() -> logging.Logger:
    logger = logging.getLogger("score_v3_initialization")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)
    return logger


def _load_protocol() -> dict[str, Any]:
    payload = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    boundary = payload.get("knowledge_boundary", {})
    if payload.get("protocol_version") != 1:
        raise RuntimeError("Expected Score v3 preregistration protocol_version=1")
    if boundary.get("latest_observation_already_seen_at_registration") != CUTOFF_WEEK.isoformat():
        raise RuntimeError("Preregistration retrospective cutoff does not match freeze cutoff")
    if boundary.get("prospective_untouched_holdout_start") != "2026-08-28":
        raise RuntimeError("Unexpected prospective holdout start")
    return payload


def canonical_csv_bytes(weekly: pd.DataFrame) -> bytes:
    text = weekly.to_csv(
        index_label="date",
        float_format="%.12g",
        lineterminator="\n",
    )
    return text.encode("utf-8")


def build_live_snapshot(
    *,
    generated_at: datetime,
    generator_commit_sha: str,
) -> tuple[bytes, dict[str, Any]]:
    protocol = _load_protocol()
    drivers = list(score_v2.WEIGHTS)
    logger = _logger()

    daily = score_v2.fetch_all_inputs(
        score_v2.START_DATE,
        logger,
        as_of=generated_at,
    )
    provenance = daily.attrs.get("source_provenance")
    if not isinstance(provenance, dict):
        raise RuntimeError("Live initialization freeze is missing source provenance")
    score_v2.validate_source_freshness(provenance, CUTOFF_WEEK, logger)

    weekly = score_v2.resample_weekly(
        daily,
        logger,
        completed_friday=CUTOFF_WEEK,
    )
    missing = [driver for driver in drivers if driver not in weekly.columns]
    if missing:
        raise RuntimeError(f"Initialization weekly frame missing drivers: {missing}")

    clean = weekly[drivers].dropna().copy()
    if clean.empty:
        raise RuntimeError("Initialization matrix has no complete weekly observations")
    if clean.index[-1].date() != CUTOFF_WEEK:
        raise RuntimeError(
            f"Initialization matrix ended {clean.index[-1].date()}, expected {CUTOFF_WEEK}"
        )
    if not clean.index.is_monotonic_increasing or not clean.index.is_unique:
        raise RuntimeError("Initialization matrix index must be unique and increasing")
    if list(clean.columns) != drivers:
        raise RuntimeError("Initialization driver order differs from production v2")
    if not all(pd.api.types.is_numeric_dtype(clean[col]) for col in clean.columns):
        raise RuntimeError("Initialization matrix contains non-numeric driver columns")

    matrix_bytes = canonical_csv_bytes(clean)
    matrix_hash = sha256_bytes(matrix_bytes)
    requirements_hash = sha256_file(REQUIREMENTS_LOCK_PATH)
    methodology_hash = sha256_file(METHODOLOGY_CONTRACT_PATH)
    protocol_content_hash = sha256_file(PROTOCOL_PATH)

    manifest: dict[str, Any] = {
        "artifact_schema_version": 1,
        "artifact_type": "score_v3_retrospective_initialization_matrix",
        "research_only": True,
        "production_change": False,
        "historical_data_status": "retrospective_current_vintage_not_as_published",
        "may_be_replaced_after_freeze": False,
        "replacement_policy": (
            "Never replace this matrix because later Yahoo/FRED history changes. "
            "A material protocol amendment requiring a reset must create a new versioned artifact."
        ),
        "cutoff_week": CUTOFF_WEEK.isoformat(),
        "prospective_holdout_start": "2026-08-28",
        "generated_at_utc": generated_at.astimezone(timezone.utc).isoformat(),
        "locked_preregistration_commit_sha": LOCKED_PREREGISTRATION_SHA,
        "preregistration_protocol_id": protocol["protocol_id"],
        "preregistration_protocol_version": protocol["protocol_version"],
        "preregistration_file_sha256": protocol_content_hash,
        "generator_commit_sha": generator_commit_sha,
        "production_methodology": "usd_impact_score_v2",
        "production_methodology_contract_sha256": methodology_hash,
        "requirements_lock_sha256": requirements_hash,
        "production_start_date": score_v2.START_DATE,
        "resample_rule": score_v2.RESAMPLE_RULE,
        "driver_order": drivers,
        "weekly_complete_case_required": True,
        "calendar_alignment_forward_fill_limit_observations": 3,
        "matrix_file": DEFAULT_MATRIX_PATH.name,
        "matrix_sha256": matrix_hash,
        "matrix_rows": int(len(clean)),
        "matrix_first_week": clean.index[0].date().isoformat(),
        "matrix_last_week": clean.index[-1].date().isoformat(),
        "source_provenance_version": score_v2.SOURCE_PROVENANCE_VERSION,
        "source_provenance": provenance,
    }
    return matrix_bytes, manifest


def write_once(
    matrix_path: Path,
    manifest_path: Path,
    *,
    generated_at: datetime,
    generator_commit_sha: str,
) -> dict[str, Any]:
    if matrix_path.exists() or manifest_path.exists():
        raise RuntimeError(
            "Initialization artifact already exists; overwrite is forbidden. "
            "Use --verify-frozen instead."
        )

    matrix_bytes, manifest = build_live_snapshot(
        generated_at=generated_at,
        generator_commit_sha=generator_commit_sha,
    )
    matrix_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    matrix_path.write_bytes(matrix_bytes)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_frozen(matrix_path: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    matrix = pd.read_csv(matrix_path, parse_dates=["date"]).set_index("date")
    drivers = list(score_v2.WEIGHTS)

    if manifest.get("artifact_type") != "score_v3_retrospective_initialization_matrix":
        raise RuntimeError("Unexpected initialization artifact type")
    if manifest.get("historical_data_status") != "retrospective_current_vintage_not_as_published":
        raise RuntimeError("Initialization artifact historical-data status is ambiguous")
    if manifest.get("may_be_replaced_after_freeze") is not False:
        raise RuntimeError("Initialization artifact must be immutable after freeze")
    if manifest.get("locked_preregistration_commit_sha") != LOCKED_PREREGISTRATION_SHA:
        raise RuntimeError("Initialization artifact points to the wrong preregistration commit")
    if manifest.get("cutoff_week") != CUTOFF_WEEK.isoformat():
        raise RuntimeError("Initialization artifact cutoff is not 2026-08-21")
    if manifest.get("prospective_holdout_start") != "2026-08-28":
        raise RuntimeError("Initialization artifact has the wrong holdout start")
    if manifest.get("driver_order") != drivers or list(matrix.columns) != drivers:
        raise RuntimeError("Initialization artifact driver contract drifted")
    if matrix.empty or matrix.index[-1].date() != CUTOFF_WEEK:
        raise RuntimeError("Initialization matrix does not end on the locked cutoff")
    if len(matrix) != int(manifest.get("matrix_rows", -1)):
        raise RuntimeError("Initialization matrix row count differs from manifest")
    if sha256_file(matrix_path) != manifest.get("matrix_sha256"):
        raise RuntimeError("Initialization matrix SHA-256 differs from manifest")
    if sha256_file(PROTOCOL_PATH) != manifest.get("preregistration_file_sha256"):
        raise RuntimeError("Current preregistration file differs from the frozen protocol content")
    if sha256_file(METHODOLOGY_CONTRACT_PATH) != manifest.get("production_methodology_contract_sha256"):
        raise RuntimeError("Current Score v2 methodology contract differs from freeze reference")
    return manifest


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX_PATH)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--generated-at")
    parser.add_argument("--generator-commit", default=os.environ.get("GITHUB_SHA", "local"))
    parser.add_argument("--verify-frozen", action="store_true")
    args = parser.parse_args()

    if args.verify_frozen:
        manifest = verify_frozen(args.matrix, args.manifest)
        print(json.dumps({
            "status": "verified",
            "matrix_sha256": manifest["matrix_sha256"],
            "rows": manifest["matrix_rows"],
            "cutoff_week": manifest["cutoff_week"],
            "locked_preregistration_commit_sha": manifest["locked_preregistration_commit_sha"],
        }, indent=2))
        return 0

    manifest = write_once(
        args.matrix,
        args.manifest,
        generated_at=_parse_datetime(args.generated_at),
        generator_commit_sha=args.generator_commit,
    )
    print(json.dumps({
        "status": "frozen",
        "matrix_sha256": manifest["matrix_sha256"],
        "rows": manifest["matrix_rows"],
        "cutoff_week": manifest["cutoff_week"],
        "historical_data_status": manifest["historical_data_status"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
