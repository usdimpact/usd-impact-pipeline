#!/usr/bin/env python3
"""Build a Score v2 reproduction bundle bound to the active online runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from scripts import build_score_repro_bundle as base
from scripts.execution_environment import verify_profile

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "runtime/active-environment.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--score-json", type=Path, required=True)
    parser.add_argument("--weekly-levels", type=Path, required=True)
    parser.add_argument("--provider-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    profile = verify_profile(ROOT, PROFILE)
    if not profile["active"]:
        raise RuntimeError("Active online runtime profile is not enabled")
    lock_path = ROOT / profile["lock_path"]

    score_json = json.loads(args.score_json.read_text(encoding="utf-8"))
    weekly = pd.read_csv(
        args.weekly_levels,
        parse_dates=["date"],
        float_precision="round_trip",
    ).set_index("date")
    provenance = score_json["metadata"].get("source_provenance", {})
    provider_evidence = json.loads(args.provider_evidence.read_text(encoding="utf-8"))

    bundle = base.build_bundle(
        weekly,
        provenance,
        score_json,
        provider_evidence,
        git_sha=base._git_sha(),
        lock_sha256=base._sha256(lock_path),
    )
    base.verify_bundle(bundle)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        f"Verified runtime-bound reproduction bundle for {bundle['score_week']}: "
        f"{bundle['published']['score']:+.12f} ({bundle['published']['regime']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
