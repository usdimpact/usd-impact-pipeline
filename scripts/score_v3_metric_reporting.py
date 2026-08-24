#!/usr/bin/env python3
"""Governed reporting wrapper for the preregistered Score v3 shadow study.

Every prospective week is silently recomputed through the locked metric evaluator
for integrity. Durable endpoint reports are emitted only at the preregistered
13/26/39-week interim checkpoints and the 52-week formal review. This module
never fetches live market data and never promotes a research candidate to
production.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts import score_v3_metrics as metrics
from scripts import score_v3_manifest as manifest_v3

CHECKPOINTS = (13, 26, 39, 52)
CHECKPOINT_DIR = Path("research/prospective/checkpoints")
REPORTING_VERSION = 1


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _checkpoint_path(root: Path, completed_weeks: int) -> Path:
    return root / CHECKPOINT_DIR / f"score_v3_checkpoint_{completed_weeks:03d}.json"


def _latest_week(metric_state: dict[str, Any]) -> str | None:
    rows = metric_state["weekly_metrics"][metrics.BENCHMARK_ID]
    return str(rows[-1]["week"]) if rows else None


def validate_weekly(root: Path = Path(".")) -> dict[str, Any]:
    """Recompute all locked metrics without exposing endpoint values."""
    root = root.resolve()
    state = metrics.build_weekly_metrics(root)
    completed = int(state["prospective_weeks"])
    immunity = state["future_revision_immunity"]
    if not all(bool(immunity[model_id]) for model_id in metrics.MODEL_IDS):
        failed = [model_id for model_id in metrics.MODEL_IDS if not bool(immunity[model_id])]
        raise RuntimeError(f"Score v3 future-revision immunity failed for: {', '.join(failed)}")

    # Once a checkpoint is in the past, its immutable report must already exist.
    # This prevents a missed 13/26/39/52 report from being silently skipped and
    # reconstructed only after additional prospective outcomes have been seen.
    for checkpoint in CHECKPOINTS:
        if checkpoint < completed and not _checkpoint_path(root, checkpoint).exists():
            raise RuntimeError(
                f"Missing required Score v3 checkpoint report {checkpoint:03d}; "
                "do not skip or backfill it after later prospective weeks"
            )

    return {
        "report_type": "score_v3_weekly_metric_integrity_validation",
        "reporting_version": REPORTING_VERSION,
        "research_only": True,
        "production_change": False,
        "predictive_claim": False,
        "metric_contract_sha256": state["contract_sha256"],
        "prospective_weeks": completed,
        "latest_week": _latest_week(state),
        "metric_state_validated": True,
        "endpoint_values_emitted": False,
        "ranking_performed": False,
        "candidate_selection_performed": False,
        "production_promotion_performed": False,
    }


def checkpoint_if_due(
    root: Path = Path("."),
    *,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Validate weekly state and deterministically write only an allowed checkpoint."""
    root = root.resolve()
    validation = validate_weekly(root)
    completed = int(validation["prospective_weeks"])
    if completed not in CHECKPOINTS:
        return {
            **validation,
            "status": "validated_no_checkpoint_due",
            "checkpoint_due": False,
            "checkpoint_written": False,
            "checkpoint_file": None,
        }

    checkpoint = metrics.build_checkpoint_report(root)
    if int(checkpoint["evaluation_weeks"]) != completed:
        raise RuntimeError("Checkpoint evaluation window does not match the due checkpoint")
    if completed in (13, 26, 39):
        if checkpoint["stage"] != "interim":
            raise RuntimeError("Interim Score v3 checkpoint stage drifted")
        if checkpoint["ranking_performed"] is not False:
            raise RuntimeError("Interim Score v3 checkpoint attempted ranking")
        if checkpoint["candidate_selection_performed"] is not False:
            raise RuntimeError("Interim Score v3 checkpoint attempted candidate selection")
    elif completed == 52:
        if checkpoint["stage"] != "formal_52_week_review":
            raise RuntimeError("Formal Score v3 checkpoint stage drifted")
        if checkpoint["candidate_selection_performed"] is not True:
            raise RuntimeError("Formal Score v3 review did not apply the locked selection rule")

    manifest_path = root / manifest_v3.MANIFEST_PATH
    manifest = manifest_v3.load_manifest(manifest_path)
    manifest_v3.validate_manifest(
        manifest,
        initialization_manifest_path=root / manifest_v3.INITIALIZATION_MANIFEST_PATH,
    )
    if len(manifest["entries"]) != completed:
        raise RuntimeError("Prospective manifest count differs from metric evaluator count")

    checkpoint["reporting_version"] = REPORTING_VERSION
    checkpoint["prospective_manifest_sha256"] = _sha256_file(manifest_path)
    checkpoint["latest_week"] = validation["latest_week"]
    checkpoint["production_change"] = False
    checkpoint["production_promotion_performed"] = False

    directory = (root / output_dir) if output_dir is not None else (root / CHECKPOINT_DIR)
    path = directory / f"score_v3_checkpoint_{completed:03d}.json"
    raw = json.dumps(checkpoint, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != raw:
            raise RuntimeError(f"Existing Score v3 checkpoint differs from deterministic recomputation: {path}")
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
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    report = checkpoint_if_due(args.root)
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
