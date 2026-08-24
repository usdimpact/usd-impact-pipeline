#!/usr/bin/env python3
"""Append one attested weekly observation to the locked Score v2 predictive study.

This research-only collector never fetches provider data. It accepts only the
already-published strict reproduction bundle and its byte-identical dated archive.
The weekly grid is gap-intolerant, so a missed origin cannot be reconstructed
after its outcome is visible.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts import build_score_repro_bundle as repro
from scripts import score_v2_predictive_manifest as manifest_v2p

SCORE_JSON_PATH = Path("public/data/usd_impact_score_v2.json")
LATEST_BUNDLE_PATH = Path("public/data/score_repro_bundle_latest.json")
PREDICTIVE_DIR = Path("research/predictive")
INITIALIZATION_PATH = Path("research/score_v3_initialization_2026-08-21.csv")
INITIALIZATION_SHA256 = "6e17100c061cebc3116fdac9c83708b94a72165957ffbcf688d9a08e9d280580"
INITIALIZATION_WEEK = date(2026, 8, 21)
RECORD_KEYS = {
    "$schema",
    "record_schema_version",
    "study",
    "research_only",
    "production_change",
    "predictive_power_status",
    "record_role",
    "week",
    "recorded_at_utc",
    "locked_preregistration_commit_sha",
    "locked_preregistration_file_sha256",
    "implementation_contract_sha256",
    "source_v2_bundle",
    "as_published_observation",
    "frozen_predictions",
}
SOURCE_KEYS = {
    "sha256",
    "pipeline_commit_sha",
    "attestation_status",
    "attestation_run_id",
    "attestation_url",
}
OBSERVATION_KEYS = {"score", "dxy_weekly_level"}
PREDICTION_KEYS = {
    "model_direction",
    "always_up_direction",
    "momentum_direction",
    "momentum_prior_week",
    "momentum_prior_dxy_level",
    "momentum_prior_source",
}


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object in {path}")
    return payload


def latest_published_week(root: Path) -> date:
    payload = _read_json(root / SCORE_JSON_PATH)
    latest = str((payload.get("metadata") or {}).get("latest_date", ""))
    if not latest:
        raise RuntimeError("Published Score v2 metadata has no latest_date")
    return date.fromisoformat(latest)


def _validate_bundle(root: Path, week: date) -> tuple[dict[str, Any], str]:
    latest_path = root / LATEST_BUNDLE_PATH
    archive_path = root / f"public/archive/{week.isoformat()}/repro_bundle.json"
    if not latest_path.exists():
        raise RuntimeError("Strict Score v2 reproduction bundle is missing")
    if not archive_path.exists():
        raise RuntimeError(f"Archived Score v2 reproduction bundle is missing for {week}")
    latest_hash = sha256_file(latest_path)
    if sha256_file(archive_path) != latest_hash:
        raise RuntimeError("Latest/archive Score v2 reproduction bundle hashes differ")
    bundle = _read_json(latest_path)
    if bundle.get("score_week") != week.isoformat():
        raise RuntimeError("Score v2 reproduction bundle week differs from published latest week")
    repro.verify_bundle(bundle)
    pipeline_sha = str(bundle.get("pipeline_git_sha", ""))
    if not manifest_v2p.SHA40.fullmatch(pipeline_sha):
        raise RuntimeError("Score v2 bundle pipeline_git_sha is invalid")
    published = bundle.get("published") or {}
    components = bundle.get("components") or {}
    if "score" not in published or "DXY" not in components:
        raise RuntimeError("Score v2 bundle lacks the frozen predictor or DXY target level")
    score = float(published["score"])
    dxy = float((components["DXY"] or {}).get("weekly_level"))
    if not math.isfinite(score) or not math.isfinite(dxy) or dxy <= 0:
        raise RuntimeError("Score v2 bundle has a non-finite score or invalid DXY level")
    return bundle, latest_hash


def _initial_dxy_level(root: Path) -> float:
    path = root / INITIALIZATION_PATH
    if sha256_file(path) != INITIALIZATION_SHA256:
        raise RuntimeError("Frozen 2026-08-21 initialization matrix hash mismatch")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or rows[-1].get("date") != INITIALIZATION_WEEK.isoformat():
        raise RuntimeError("Frozen initialization matrix does not end on 2026-08-21")
    value = float(rows[-1]["DXY"])
    if not math.isfinite(value) or value <= 0:
        raise RuntimeError("Frozen initialization DXY level is invalid")
    return value


def _record_path(root: Path, filename: str) -> Path:
    return root / PREDICTIVE_DIR / Path(filename).name


def _validate_record_payload(
    payload: dict[str, Any],
    *,
    entry: dict[str, Any],
    bundle: dict[str, Any],
) -> None:
    if set(payload) != RECORD_KEYS:
        raise RuntimeError(f"Predictive weekly record {entry['week']} differs from the closed contract")
    if payload.get("$schema") != "../score_v2_predictive_week.schema.json":
        raise RuntimeError(f"Predictive weekly record {entry['week']} schema reference drifted")
    if payload.get("record_schema_version") != 1:
        raise RuntimeError(f"Predictive weekly record {entry['week']} version drifted")
    if payload.get("study") != "usd_impact_score_v2_one_week_dxy_direction_2026-08-25":
        raise RuntimeError(f"Predictive weekly record {entry['week']} study ID drifted")
    if payload.get("research_only") is not True or payload.get("production_change") is not False:
        raise RuntimeError(f"Predictive weekly record {entry['week']} must remain research-only")
    if payload.get("predictive_power_status") != "not_established_pending_52_resolved_predictions":
        raise RuntimeError(f"Predictive weekly record {entry['week']} makes an unauthorized claim")
    for field in ("record_role", "week", "recorded_at_utc"):
        if payload.get(field) != entry.get(field):
            raise RuntimeError(f"Predictive weekly record {entry['week']} {field} mismatch")
    if payload.get("locked_preregistration_commit_sha") != manifest_v2p.LOCKED_PREREGISTRATION_SHA:
        raise RuntimeError(f"Predictive weekly record {entry['week']} protocol lock mismatch")
    if payload.get("locked_preregistration_file_sha256") != manifest_v2p.LOCKED_PREREGISTRATION_FILE_SHA256:
        raise RuntimeError(f"Predictive weekly record {entry['week']} protocol file lock mismatch")
    if payload.get("implementation_contract_sha256") != manifest_v2p.IMPLEMENTATION_CONTRACT_SHA256:
        raise RuntimeError(f"Predictive weekly record {entry['week']} contract lock mismatch")

    source = payload.get("source_v2_bundle")
    if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
        raise RuntimeError(f"Predictive weekly record {entry['week']} source contract mismatch")
    expected_source = {
        "sha256": entry["source_v2_bundle_sha256"],
        "pipeline_commit_sha": entry["source_v2_pipeline_commit_sha"],
        "attestation_status": entry["source_v2_attestation_status"],
        "attestation_run_id": entry["source_v2_attestation_run_id"],
    }
    for field, value in expected_source.items():
        if source.get(field) != value:
            raise RuntimeError(f"Predictive weekly record {entry['week']} source {field} mismatch")
    if not str(source.get("attestation_url", "")).startswith("https://github.com/"):
        raise RuntimeError(f"Predictive weekly record {entry['week']} attestation URL is invalid")

    observation = payload.get("as_published_observation")
    if not isinstance(observation, dict) or set(observation) != OBSERVATION_KEYS:
        raise RuntimeError(f"Predictive weekly record {entry['week']} observation contract mismatch")
    score = float(observation["score"])
    dxy = float(observation["dxy_weekly_level"])
    if not math.isfinite(score) or not math.isfinite(dxy) or dxy <= 0:
        raise RuntimeError(f"Predictive weekly record {entry['week']} has invalid numeric values")
    if score != float(bundle["published"]["score"]):
        raise RuntimeError(f"Predictive weekly record {entry['week']} score differs from its bundle")
    if dxy != float(bundle["components"]["DXY"]["weekly_level"]):
        raise RuntimeError(f"Predictive weekly record {entry['week']} DXY level differs from its bundle")

    predictions = payload.get("frozen_predictions")
    if entry["record_role"] == "terminal_outcome":
        if predictions is not None:
            raise RuntimeError("Terminal predictive record must not create a 53rd prediction")
        return
    if not isinstance(predictions, dict) or set(predictions) != PREDICTION_KEYS:
        raise RuntimeError(f"Predictive weekly record {entry['week']} prediction contract mismatch")
    expected_model = "up" if score >= 0 else "down"
    if predictions.get("model_direction") != expected_model:
        raise RuntimeError(f"Predictive weekly record {entry['week']} model direction mismatch")
    if predictions.get("always_up_direction") != "up":
        raise RuntimeError(f"Predictive weekly record {entry['week']} always-up comparator drifted")
    prior = float(predictions.get("momentum_prior_dxy_level"))
    if not math.isfinite(prior) or prior <= 0:
        raise RuntimeError(f"Predictive weekly record {entry['week']} momentum prior is invalid")
    expected_momentum = "up" if math.log(dxy / prior) >= 0 else "down"
    if predictions.get("momentum_direction") != expected_momentum:
        raise RuntimeError(f"Predictive weekly record {entry['week']} momentum direction mismatch")


def validate_all_records(root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    manifest_v2p.validate_manifest(manifest, root=root)
    records: list[dict[str, Any]] = []
    previous_record: dict[str, Any] | None = None
    initial_dxy = _initial_dxy_level(root)
    for index, entry in enumerate(manifest["entries"]):
        path = _record_path(root, entry["weekly_record_file"])
        if not path.exists():
            raise RuntimeError(f"Predictive weekly record is missing: {path}")
        if sha256_file(path) != entry["weekly_record_sha256"]:
            raise RuntimeError(f"Predictive weekly record hash mismatch: {entry['week']}")
        archive = root / f"public/archive/{entry['week']}/repro_bundle.json"
        if not archive.exists() or sha256_file(archive) != entry["source_v2_bundle_sha256"]:
            raise RuntimeError(f"Predictive source archive hash mismatch: {entry['week']}")
        bundle = _read_json(archive)
        repro.verify_bundle(bundle)
        payload = _read_json(path)
        _validate_record_payload(payload, entry=entry, bundle=bundle)
        predictions = payload["frozen_predictions"]
        if index < manifest_v2p.PREDICTIVE_ORIGINS:
            expected_prior_week = INITIALIZATION_WEEK if index == 0 else date.fromisoformat(records[-1]["week"])
            expected_prior_level = initial_dxy if index == 0 else float(
                previous_record["as_published_observation"]["dxy_weekly_level"]
            )
            expected_source = "frozen_2026-08-21_initialization" if index == 0 else "previous_predictive_week_record"
            if predictions["momentum_prior_week"] != expected_prior_week.isoformat():
                raise RuntimeError(f"Predictive weekly record {entry['week']} momentum prior week mismatch")
            if float(predictions["momentum_prior_dxy_level"]) != expected_prior_level:
                raise RuntimeError(f"Predictive weekly record {entry['week']} momentum prior level mismatch")
            if predictions["momentum_prior_source"] != expected_source:
                raise RuntimeError(f"Predictive weekly record {entry['week']} momentum prior source mismatch")
        records.append(payload)
        previous_record = payload
    return records


def _require_attestation(run_id: str | None, url: str | None) -> tuple[int, str]:
    if not run_id or not str(run_id).isdigit() or int(run_id) < 1:
        raise RuntimeError("Predictive ingestion requires the successful v2 attestation run ID")
    if not url or not str(url).startswith("https://github.com/"):
        raise RuntimeError("Predictive ingestion requires the successful v2 attestation URL")
    return int(run_id), str(url)


def ingest(
    root: Path,
    *,
    recorded_at: datetime,
    attestation_run_id: str | None,
    attestation_url: str | None,
    write: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    manifest_v2p.validate_locked_sources(root)
    week = latest_published_week(root)
    if week < manifest_v2p.FIRST_ORIGIN:
        return {
            "status": "pre_holdout_noop",
            "research_only": True,
            "published_week": week.isoformat(),
            "first_prediction_origin": manifest_v2p.FIRST_ORIGIN.isoformat(),
            "writes_performed": False,
        }

    run_id, run_url = _require_attestation(attestation_run_id, attestation_url)
    manifest_path = root / manifest_v2p.MANIFEST_PATH
    manifest = manifest_v2p.load_manifest(manifest_path)
    manifest_v2p.validate_manifest(manifest, root=root)
    records = validate_all_records(root, manifest)

    delta_days = (week - manifest_v2p.FIRST_ORIGIN).days
    if delta_days % 7 != 0:
        raise RuntimeError(f"Published week {week} is not on the preregistered Friday grid")
    expected_index = delta_days // 7
    if len(manifest["entries"]) == manifest_v2p.WEEKLY_OBSERVATIONS:
        if expected_index < manifest_v2p.WEEKLY_OBSERVATIONS - 1:
            raise RuntimeError("Completed predictive manifest extends beyond the published week")
        return {
            "status": "study_complete_noop",
            "research_only": True,
            "published_week": week.isoformat(),
            "weekly_observations": manifest_v2p.WEEKLY_OBSERVATIONS,
            "resolved_predictions": manifest_v2p.PREDICTIVE_ORIGINS,
            "writes_performed": False,
        }

    bundle, bundle_hash = _validate_bundle(root, week)
    entries = manifest["entries"]
    if entries and entries[-1]["week"] == week.isoformat():
        if entries[-1]["source_v2_bundle_sha256"] != bundle_hash:
            raise RuntimeError("Already-recorded predictive week points to a different v2 bundle")
        return {
            "status": "already_ingested_noop",
            "research_only": True,
            "published_week": week.isoformat(),
            "weekly_record_file": entries[-1]["weekly_record_file"],
            "weekly_record_sha256": entries[-1]["weekly_record_sha256"],
            "writes_performed": False,
        }
    if expected_index != len(entries):
        raise RuntimeError(
            f"Predictive ledger gap: {len(entries)} stored prior observations, "
            f"expected {expected_index} before {week}; backfill is prohibited"
        )
    if expected_index >= manifest_v2p.WEEKLY_OBSERVATIONS:
        raise RuntimeError("Predictive study passed its terminal week without a complete ledger")

    observed_score = float(bundle["published"]["score"])
    observed_dxy = float(bundle["components"]["DXY"]["weekly_level"])
    role = "terminal_outcome" if expected_index == manifest_v2p.PREDICTIVE_ORIGINS else "predictive_origin"
    predictions: dict[str, Any] | None = None
    if role == "predictive_origin":
        if expected_index == 0:
            prior_week = INITIALIZATION_WEEK
            prior_dxy = _initial_dxy_level(root)
            prior_source = "frozen_2026-08-21_initialization"
        else:
            prior_record = records[-1]
            prior_week = date.fromisoformat(prior_record["week"])
            prior_dxy = float(prior_record["as_published_observation"]["dxy_weekly_level"])
            prior_source = "previous_predictive_week_record"
        predictions = {
            "model_direction": "up" if observed_score >= 0 else "down",
            "always_up_direction": "up",
            "momentum_direction": "up" if math.log(observed_dxy / prior_dxy) >= 0 else "down",
            "momentum_prior_week": prior_week.isoformat(),
            "momentum_prior_dxy_level": prior_dxy,
            "momentum_prior_source": prior_source,
        }

    timestamp = recorded_at.astimezone(timezone.utc).isoformat()
    payload: dict[str, Any] = {
        "$schema": "../score_v2_predictive_week.schema.json",
        "record_schema_version": 1,
        "study": "usd_impact_score_v2_one_week_dxy_direction_2026-08-25",
        "research_only": True,
        "production_change": False,
        "predictive_power_status": "not_established_pending_52_resolved_predictions",
        "record_role": role,
        "week": week.isoformat(),
        "recorded_at_utc": timestamp,
        "locked_preregistration_commit_sha": manifest_v2p.LOCKED_PREREGISTRATION_SHA,
        "locked_preregistration_file_sha256": manifest_v2p.LOCKED_PREREGISTRATION_FILE_SHA256,
        "implementation_contract_sha256": manifest_v2p.IMPLEMENTATION_CONTRACT_SHA256,
        "source_v2_bundle": {
            "sha256": bundle_hash,
            "pipeline_commit_sha": bundle["pipeline_git_sha"],
            "attestation_status": "passed",
            "attestation_run_id": run_id,
            "attestation_url": run_url,
        },
        "as_published_observation": {
            "score": observed_score,
            "dxy_weekly_level": observed_dxy,
        },
        "frozen_predictions": predictions,
    }
    raw = json_bytes(payload)
    record_hash = sha256_bytes(raw)
    filename = f"score_v2_predictive_week_{week.isoformat()}.json"
    path = _record_path(root, filename)
    if path.exists():
        raise RuntimeError(f"Predictive weekly record path already exists unexpectedly: {path}")

    entry = {
        "week": week.isoformat(),
        "record_role": role,
        "recorded_at_utc": timestamp,
        "source_v2_bundle_sha256": bundle_hash,
        "source_v2_pipeline_commit_sha": bundle["pipeline_git_sha"],
        "source_v2_attestation_status": "passed",
        "source_v2_attestation_run_id": run_id,
        "locked_preregistration_commit_sha": manifest_v2p.LOCKED_PREREGISTRATION_SHA,
        "implementation_contract_sha256": manifest_v2p.IMPLEMENTATION_CONTRACT_SHA256,
        "weekly_record_file": filename,
        "weekly_record_sha256": record_hash,
    }
    updated = manifest_v2p.append_entry(manifest, entry, root=root)
    manifest_raw = json_bytes(updated)

    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        manifest_path.write_bytes(manifest_raw)

    return {
        "status": "ingested" if write else "validated_dry_run",
        "research_only": True,
        "published_week": week.isoformat(),
        "record_role": role,
        "weekly_record_file": filename,
        "weekly_record_sha256": record_hash,
        "source_v2_bundle_sha256": bundle_hash,
        "weekly_observations": len(updated["entries"]),
        "resolved_predictions": max(0, len(updated["entries"]) - 1),
        "writes_performed": bool(write),
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
    parser.add_argument("--recorded-at")
    parser.add_argument("--attestation-run-id")
    parser.add_argument("--attestation-url")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = ingest(
        args.root,
        recorded_at=_parse_datetime(args.recorded_at),
        attestation_run_id=args.attestation_run_id,
        attestation_url=args.attestation_url,
        write=not args.dry_run,
    )
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
