#!/usr/bin/env python3
"""Exercise the strict Score v2 reproduction gate without publishing anything.

This is a plumbing rehearsal only. It deliberately calls the same frozen-bundle
validator used for post-2026-08-28 releases even when the currently completed
week is a legacy date. A passing rehearsal is not production acceptance evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.validate_methodology_contract import validate_contract
from scripts.validate_weekly_release import load_json, validate_reproduction_bundle


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Missing or empty rehearsal artifact: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rehearse(root: Path) -> dict[str, Any]:
    root = root.resolve()
    contract_result = validate_contract(
        root / "public/data/score_v2_methodology.json",
        root / "public/data/score_v2_methodology.schema.json",
    )

    score_payload = load_json(root / "public/data/usd_impact_score_v2.json")
    metadata = score_payload.get("metadata") or {}
    week = str(metadata.get("latest_date", ""))
    if not week:
        raise ValueError("Rehearsal score metadata has no latest_date")

    latest_bundle = root / "public/data/score_repro_bundle_latest.json"
    archived_bundle = root / f"public/archive/{week}/repro_bundle.json"

    # Call the strict validator directly. This intentionally does not consult
    # the legacy-date exemption used by normal publication validation.
    validate_reproduction_bundle(root, metadata, week)

    latest_sha = _sha256(latest_bundle)
    archived_sha = _sha256(archived_bundle)
    if latest_sha != archived_sha:
        raise ValueError("Rehearsal latest/archive reproduction bundle hashes differ")

    provenance = metadata.get("source_provenance") or {}
    if not provenance or any(item.get("retrieval_mode") != "live" for item in provenance.values()):
        raise ValueError("Rehearsal requires live source provenance for all drivers")

    return {
        "study": "usd_impact_score_v2_reproduction_acceptance_rehearsal",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "rehearsal_only": True,
        "acceptance_evidence": False,
        "publication_performed": False,
        "deployment_performed": False,
        "score_week": week,
        "score": float(metadata["latest_score"]),
        "regime": metadata["latest_regime"],
        "methodology_contract_sha256": contract_result["contract_sha256"],
        "latest_bundle_sha256": latest_sha,
        "archived_bundle_sha256": archived_sha,
        "bundle_archive_match": True,
        "strict_offline_reproduction_gate": "passed",
        "live_provenance_driver_count": len(provenance),
        "result": "passed",
        "disclaimer": (
            "This run validates plumbing only. It is not the first real post-implementation "
            "as-published weekly release and cannot close the production acceptance criterion."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    report = rehearse(args.root)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("REHEARSAL ONLY — not production acceptance evidence")
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
