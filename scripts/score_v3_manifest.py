#!/usr/bin/env python3
"""Validate and append to the preregistered Score v3 prospective evidence ledger.

Research-only. The ledger is append-only and is cryptographically bound to the
locked preregistration and frozen 2026-08-21 initialization matrix.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from scripts import score_v3_candidates as v3

MANIFEST_PATH = Path("research/score_v3_prospective_manifest.json")
INITIALIZATION_MANIFEST_PATH = Path("research/score_v3_initialization_2026-08-21.manifest.json")
HOLDOUT_START = date(2026, 8, 28)
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_sha(value: Any, *, length: int, field: str) -> str:
    text = str(value)
    pattern = SHA40 if length == 40 else SHA64
    if not pattern.fullmatch(text):
        raise RuntimeError(f"{field} is not a lowercase {length}-hex SHA")
    return text


def validate_manifest(
    manifest: dict[str, Any],
    *,
    initialization_manifest_path: Path = INITIALIZATION_MANIFEST_PATH,
) -> dict[str, Any]:
    if manifest.get("manifest_version") != 1:
        raise RuntimeError("Unsupported Score v3 prospective manifest version")
    if manifest.get("research_only") is not True:
        raise RuntimeError("Prospective manifest must remain research-only")
    if manifest.get("production_change") is not False:
        raise RuntimeError("Prospective manifest cannot authorize production change")
    if manifest.get("predictive_claim") is not False:
        raise RuntimeError("Prospective manifest cannot make a predictive claim")
    if manifest.get("append_only") is not True:
        raise RuntimeError("Prospective manifest must remain append-only")
    if manifest.get("locked_preregistration_commit_sha") != v3.LOCKED_PREREGISTRATION_SHA:
        raise RuntimeError("Prospective manifest preregistration lock mismatch")
    if manifest.get("prospective_holdout_start") != HOLDOUT_START.isoformat():
        raise RuntimeError("Prospective manifest holdout start mismatch")
    if manifest.get("minimum_completed_weeks_before_selection") != 52:
        raise RuntimeError("Prospective manifest selection boundary must remain 52 weeks")
    if manifest.get("interim_review_weeks") != [13, 26, 39]:
        raise RuntimeError("Prospective manifest interim review schedule drifted")
    if tuple(manifest.get("candidate_ids", [])) != v3.EXPECTED_CANDIDATE_IDS:
        raise RuntimeError("Prospective manifest candidate set drifted")

    init = json.loads(initialization_manifest_path.read_text(encoding="utf-8"))
    bound = manifest.get("initialization", {})
    if bound.get("matrix_sha256") != init.get("matrix_sha256"):
        raise RuntimeError("Prospective manifest initialization matrix hash mismatch")
    if bound.get("cutoff_week") != init.get("cutoff_week"):
        raise RuntimeError("Prospective manifest initialization cutoff mismatch")
    if bound.get("historical_data_status") != init.get("historical_data_status"):
        raise RuntimeError("Prospective manifest initialization status mismatch")
    if bound.get("generator_commit_sha") != init.get("generator_commit_sha"):
        raise RuntimeError("Prospective manifest initialization generator mismatch")

    _require_sha(bound.get("matrix_sha256"), length=64, field="initialization.matrix_sha256")
    _require_sha(bound.get("generator_commit_sha"), length=40, field="initialization.generator_commit_sha")

    seen: set[str] = set()
    previous_week: date | None = None
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise RuntimeError("Prospective manifest entries must be an array")

    for entry in entries:
        week = date.fromisoformat(str(entry.get("week")))
        if week < HOLDOUT_START:
            raise RuntimeError(f"Prospective entry {week} predates holdout start")
        if week.weekday() != 4:
            raise RuntimeError(f"Prospective entry {week} is not a Friday")
        week_text = week.isoformat()
        if week_text in seen:
            raise RuntimeError(f"Duplicate prospective week: {week_text}")
        if previous_week is not None and week <= previous_week:
            raise RuntimeError("Prospective entries must be strictly increasing")
        seen.add(week_text)
        previous_week = week

        if entry.get("source_v2_attestation_status") != "passed":
            raise RuntimeError(f"Prospective entry {week} lacks passed v2 attestation")
        if entry.get("locked_preregistration_commit_sha") != v3.LOCKED_PREREGISTRATION_SHA:
            raise RuntimeError(f"Prospective entry {week} preregistration lock mismatch")
        if entry.get("initialization_matrix_sha256") != init.get("matrix_sha256"):
            raise RuntimeError(f"Prospective entry {week} initialization hash mismatch")
        _require_sha(entry.get("source_v2_bundle_sha256"), length=64, field="source_v2_bundle_sha256")
        _require_sha(entry.get("source_v2_pipeline_commit_sha"), length=40, field="source_v2_pipeline_commit_sha")
        _require_sha(entry.get("candidate_result_sha256"), length=64, field="candidate_result_sha256")
        if not str(entry.get("candidate_result_file", "")).strip():
            raise RuntimeError(f"Prospective entry {week} is missing candidate result file")

    return {
        "status": "verified",
        "entries": len(entries),
        "latest_week": entries[-1]["week"] if entries else None,
        "locked_preregistration_commit_sha": v3.LOCKED_PREREGISTRATION_SHA,
        "initialization_matrix_sha256": init["matrix_sha256"],
    }


def append_entry(
    manifest: dict[str, Any],
    entry: dict[str, Any],
    *,
    initialization_manifest_path: Path = INITIALIZATION_MANIFEST_PATH,
) -> dict[str, Any]:
    # Validate the existing ledger first so an append can never repair or hide
    # pre-existing corruption.
    validate_manifest(manifest, initialization_manifest_path=initialization_manifest_path)
    updated = json.loads(json.dumps(manifest))
    updated["entries"].append(entry)
    validate_manifest(updated, initialization_manifest_path=initialization_manifest_path)
    return updated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--initialization-manifest", type=Path, default=INITIALIZATION_MANIFEST_PATH)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = validate_manifest(
        load_manifest(args.manifest),
        initialization_manifest_path=args.initialization_manifest,
    )
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(
            f"Score v3 prospective manifest verified: {report['entries']} entries; "
            f"initialization {report['initialization_matrix_sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
