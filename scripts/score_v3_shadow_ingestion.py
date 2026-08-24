#!/usr/bin/env python3
"""Ingest one attested Score v2 release into the preregistered Score v3 shadow study.

Research-only. The script never fetches Yahoo/FRED for prospective weeks. From
2026-08-28 onward it consumes only the immutable production reproduction bundle
and previously stored research results. It writes one candidate-result artifact
plus one append-only manifest entry atomically after all validation succeeds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from scripts import build_score_repro_bundle as repro
from scripts import freeze_score_v3_initialization as freeze_v3
from scripts import score_v3_candidates as v3
from scripts import score_v3_manifest as manifest_v3

HOLDOUT_START = date(2026, 8, 28)
PROSPECTIVE_DIR = Path("research/prospective")
SCORE_JSON_PATH = Path("public/data/usd_impact_score_v2.json")
LATEST_BUNDLE_PATH = Path("public/data/score_repro_bundle_latest.json")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object in {path}")
    return payload


def latest_published_week(root: Path) -> date:
    score_payload = _read_json(root / SCORE_JSON_PATH)
    metadata = score_payload.get("metadata") or {}
    latest = str(metadata.get("latest_date", ""))
    if not latest:
        raise RuntimeError("Published Score v2 metadata has no latest_date")
    return date.fromisoformat(latest)


def _load_initialization(root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    matrix_path = root / freeze_v3.DEFAULT_MATRIX_PATH
    init_manifest_path = root / freeze_v3.DEFAULT_MANIFEST_PATH
    init_manifest = freeze_v3.verify_frozen(matrix_path, init_manifest_path)
    weekly = pd.read_csv(matrix_path, parse_dates=["date"]).set_index("date")
    return weekly, init_manifest


def _validate_bundle(root: Path, week: date) -> tuple[dict[str, Any], str]:
    latest_path = root / LATEST_BUNDLE_PATH
    archive_path = root / f"public/archive/{week.isoformat()}/repro_bundle.json"
    if not latest_path.exists():
        raise RuntimeError("Strict Score v2 reproduction bundle is missing")
    if not archive_path.exists():
        raise RuntimeError(f"Archived Score v2 reproduction bundle is missing for {week}")
    latest_hash = sha256_file(latest_path)
    archive_hash = sha256_file(archive_path)
    if latest_hash != archive_hash:
        raise RuntimeError("Latest/archive Score v2 reproduction bundle hashes differ")
    bundle = _read_json(latest_path)
    if bundle.get("score_week") != week.isoformat():
        raise RuntimeError("Score v2 reproduction bundle week differs from published latest week")
    repro.verify_bundle(bundle)
    pipeline_sha = str(bundle.get("pipeline_git_sha", ""))
    if len(pipeline_sha) != 40 or any(ch not in "0123456789abcdef" for ch in pipeline_sha):
        raise RuntimeError("Score v2 bundle pipeline_git_sha is invalid")
    return bundle, latest_hash


def _validate_prior_result(
    root: Path,
    entry: dict[str, Any],
    *,
    init_hash: str,
) -> dict[str, Any]:
    result_path = root / "research" / "prospective" / Path(str(entry["candidate_result_file"])).name
    if not result_path.exists():
        raise RuntimeError(f"Prior Score v3 result file is missing: {result_path}")
    if sha256_file(result_path) != entry["candidate_result_sha256"]:
        raise RuntimeError(f"Prior Score v3 result hash mismatch: {entry['week']}")
    result = _read_json(result_path)
    if result.get("week") != entry["week"]:
        raise RuntimeError(f"Prior Score v3 result week mismatch: {entry['week']}")
    if result.get("locked_preregistration_commit_sha") != v3.LOCKED_PREREGISTRATION_SHA:
        raise RuntimeError(f"Prior Score v3 result protocol lock mismatch: {entry['week']}")
    if result.get("initialization_matrix_sha256") != init_hash:
        raise RuntimeError(f"Prior Score v3 result initialization hash mismatch: {entry['week']}")
    levels = result.get("source_weekly_levels")
    if not isinstance(levels, dict) or set(levels) != set(v3.EXPECTED_DRIVERS):
        raise RuntimeError(f"Prior Score v3 result has invalid weekly levels: {entry['week']}")
    return result


def _prospective_history(
    root: Path,
    manifest: dict[str, Any],
    initialization: pd.DataFrame,
    *,
    init_hash: str,
) -> pd.DataFrame:
    weekly = initialization.copy()
    for entry in manifest["entries"]:
        result = _validate_prior_result(root, entry, init_hash=init_hash)
        week = pd.Timestamp(entry["week"])
        if week in weekly.index:
            raise RuntimeError(f"Duplicate weekly level while rebuilding prospective history: {week.date()}")
        levels = {driver: float(result["source_weekly_levels"][driver]) for driver in v3.EXPECTED_DRIVERS}
        if not all(math.isfinite(value) for value in levels.values()):
            raise RuntimeError(f"Non-finite prior prospective levels for {week.date()}")
        weekly.loc[week, list(v3.EXPECTED_DRIVERS)] = [levels[d] for d in v3.EXPECTED_DRIVERS]
    return weekly.sort_index()


def _require_no_gap(manifest: dict[str, Any], week: date) -> None:
    expected_prior_weeks = (week - HOLDOUT_START).days // 7
    if (week - HOLDOUT_START).days % 7 != 0:
        raise RuntimeError(f"Published week {week} is not on the preregistered weekly holdout grid")
    actual = len(manifest["entries"])
    if actual != expected_prior_weeks:
        raise RuntimeError(
            f"Prospective ledger gap: {actual} stored prior weeks, expected {expected_prior_weeks} before {week}"
        )


def ingest(
    root: Path,
    *,
    ingested_at: datetime,
    attestation_run_id: str | None,
    attestation_url: str | None,
    write: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    week = latest_published_week(root)
    if week < HOLDOUT_START:
        return {
            "status": "pre_holdout_noop",
            "research_only": True,
            "published_week": week.isoformat(),
            "prospective_holdout_start": HOLDOUT_START.isoformat(),
            "writes_performed": False,
        }

    if not attestation_run_id or not str(attestation_run_id).isdigit():
        raise RuntimeError("Post-holdout ingestion requires the successful v2 attestation run ID")
    if not attestation_url or not str(attestation_url).startswith("https://github.com/"):
        raise RuntimeError("Post-holdout ingestion requires the successful v2 attestation URL")

    initialization, init_manifest = _load_initialization(root)
    manifest_path = root / manifest_v3.MANIFEST_PATH
    prospective_manifest = manifest_v3.load_manifest(manifest_path)
    manifest_v3.validate_manifest(
        prospective_manifest,
        initialization_manifest_path=root / manifest_v3.INITIALIZATION_MANIFEST_PATH,
    )

    # Validate the immutable v2 source before deciding whether this is a new or
    # repeated ingestion. A same-week rerun is a valid idempotent recovery only
    # when the already-stored ledger entry still points to this exact bundle.
    bundle, bundle_hash = _validate_bundle(root, week)
    entries = prospective_manifest["entries"]
    if entries and entries[-1]["week"] == week.isoformat():
        existing = _validate_prior_result(root, entries[-1], init_hash=init_manifest["matrix_sha256"])
        if entries[-1]["source_v2_bundle_sha256"] != bundle_hash:
            raise RuntimeError("Already-ingested prospective week points to a different v2 bundle")
        return {
            "status": "already_ingested_noop",
            "research_only": True,
            "published_week": week.isoformat(),
            "candidate_result_sha256": entries[-1]["candidate_result_sha256"],
            "candidate_result_file": entries[-1]["candidate_result_file"],
            "writes_performed": False,
            "stored_result_week": existing["week"],
        }

    _require_no_gap(prospective_manifest, week)

    weekly = _prospective_history(
        root,
        prospective_manifest,
        initialization,
        init_hash=init_manifest["matrix_sha256"],
    )

    components = bundle.get("components") or {}
    if set(components) != set(v3.EXPECTED_DRIVERS):
        raise RuntimeError("Score v2 bundle component set differs from v3 protocol driver set")
    current_levels = {driver: float(components[driver]["weekly_level"]) for driver in v3.EXPECTED_DRIVERS}
    if not all(math.isfinite(value) for value in current_levels.values()):
        raise RuntimeError("Score v2 bundle contains non-finite weekly levels")

    current_index = pd.Timestamp(week)
    if current_index in weekly.index:
        raise RuntimeError("Current prospective week already exists in reconstructed history")
    weekly.loc[current_index, list(v3.EXPECTED_DRIVERS)] = [current_levels[d] for d in v3.EXPECTED_DRIVERS]
    weekly = weekly.sort_index()

    protocol = v3.load_protocol(root / v3.PROTOCOL_PATH)
    candidate_results = {
        candidate_id: v3.compute_candidate_week(
            weekly,
            current_index,
            candidate_id,
            protocol=protocol,
        )
        for candidate_id in v3.EXPECTED_CANDIDATE_IDS
    }

    result_payload: dict[str, Any] = {
        "result_schema_version": 1,
        "study": "usd_impact_score_v3_descriptive_research_2026-08-24",
        "research_only": True,
        "production_change": False,
        "predictive_claim": False,
        "candidate_selection_performed": False,
        "week": week.isoformat(),
        "ingested_at_utc": ingested_at.astimezone(timezone.utc).isoformat(),
        "locked_preregistration_commit_sha": v3.LOCKED_PREREGISTRATION_SHA,
        "initialization_matrix_sha256": init_manifest["matrix_sha256"],
        "source_v2_bundle_sha256": bundle_hash,
        "source_v2_pipeline_commit_sha": bundle["pipeline_git_sha"],
        "source_v2_attestation": {
            "status": "passed",
            "workflow_run_id": int(attestation_run_id),
            "workflow_run_url": str(attestation_url),
        },
        "source_v2_published": bundle["published"],
        "source_weekly_levels": current_levels,
        "candidates": candidate_results,
    }
    result_raw = json_bytes(result_payload)
    result_hash = sha256_bytes(result_raw)
    result_name = f"score_v3_shadow_{week.isoformat()}.json"
    result_path = root / PROSPECTIVE_DIR / result_name
    if result_path.exists():
        raise RuntimeError(f"Prospective result path already exists unexpectedly: {result_path}")

    entry = {
        "week": week.isoformat(),
        "ingested_at_utc": result_payload["ingested_at_utc"],
        "source_v2_bundle_sha256": bundle_hash,
        "source_v2_pipeline_commit_sha": bundle["pipeline_git_sha"],
        "source_v2_attestation_status": "passed",
        "locked_preregistration_commit_sha": v3.LOCKED_PREREGISTRATION_SHA,
        "initialization_matrix_sha256": init_manifest["matrix_sha256"],
        "candidate_result_file": result_name,
        "candidate_result_sha256": result_hash,
    }
    updated_manifest = manifest_v3.append_entry(
        prospective_manifest,
        entry,
        initialization_manifest_path=root / manifest_v3.INITIALIZATION_MANIFEST_PATH,
    )
    updated_manifest_raw = json_bytes(updated_manifest)

    if write:
        result_path.parent.mkdir(parents=True, exist_ok=True)
        # Both payloads were fully generated and validated before either write.
        result_path.write_bytes(result_raw)
        manifest_path.write_bytes(updated_manifest_raw)

    return {
        "status": "ingested" if write else "validated_dry_run",
        "research_only": True,
        "published_week": week.isoformat(),
        "source_v2_bundle_sha256": bundle_hash,
        "candidate_result_file": result_name,
        "candidate_result_sha256": result_hash,
        "writes_performed": bool(write),
        "candidate_ids": list(v3.EXPECTED_CANDIDATE_IDS),
    }


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--ingested-at")
    parser.add_argument("--attestation-run-id")
    parser.add_argument("--attestation-url")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    report = ingest(
        args.root,
        ingested_at=_parse_datetime(args.ingested_at),
        attestation_run_id=args.attestation_run_id,
        attestation_url=args.attestation_url,
        write=not args.dry_run,
    )
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
