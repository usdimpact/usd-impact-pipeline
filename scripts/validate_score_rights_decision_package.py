#!/usr/bin/env python3
"""Validate the pending Score rights decision package.

This validator intentionally accepts only the pre-decision state. It prevents a
review packet from being mistaken for a provider/counsel disposition or a
Production authorization.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED_CLASSES = {"A", "B", "C", "D", "E", "F"}


def _read(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    gate = _read(repo_root / "governance/score-publication-rights-gate.json")
    surface = _read(repo_root / "governance/score-public-rights-surface.json")
    migration = _read(repo_root / "governance/score-private-research-migration-contract.json")
    matrix = _read(repo_root / "governance/score-rights-decision-matrix.json")
    template = _read(repo_root / "governance/score-rights-decision-receipt.template.json")

    if gate.get("state") != "hold" or gate.get("decision_receipt") is not None:
        raise RuntimeError("publication rights gate is not unresolved HOLD")
    if surface.get("state") != "hold" or surface.get("production_change_authorized") is not False:
        raise RuntimeError("public rights surface is not HOLD-bound")
    if migration.get("state") != "review_only":
        raise RuntimeError("private migration contract is not review-only")
    if migration.get("real_provider_evidence_authorized") is not False:
        raise RuntimeError("real provider evidence is unexpectedly authorized")
    if migration.get("public_replacement_authorized") is not False:
        raise RuntimeError("public replacement is unexpectedly authorized")

    if matrix.get("state") != "provider_counsel_decision_required":
        raise RuntimeError("decision matrix is not pending provider/counsel decision")
    if matrix.get("legal_conclusion") is not None:
        raise RuntimeError("decision matrix must not contain a legal conclusion")
    if matrix.get("production_change_authorized") is not False:
        raise RuntimeError("decision matrix unexpectedly authorizes Production")
    if set(matrix.get("classes", {})) != EXPECTED_CLASSES:
        raise RuntimeError("decision matrix class set mismatch")

    evidence = matrix.get("engineering_evidence")
    if not isinstance(evidence, dict):
        raise RuntimeError("decision matrix lacks engineering evidence")
    for field in (
        "private_boundary_proven",
        "aggregate_safe_transform_proven",
        "locked_reader_compatibility_proven",
        "full_locked_reader_write_false_dry_run_proven",
    ):
        if evidence.get(field) is not True:
            raise RuntimeError(f"engineering evidence not proven: {field}")
    if evidence.get("production_migration_performed") is not False:
        raise RuntimeError("decision matrix claims Production migration occurred")

    if template.get("decision_status") != "hold":
        raise RuntimeError("decision receipt template must remain HOLD")
    if template.get("decision_authority") is not None:
        raise RuntimeError("decision receipt template must not name an authority")
    if template.get("decided_at_utc") is not None:
        raise RuntimeError("decision receipt template must not claim a decision time")
    if template.get("approved_public_schema") is not None:
        raise RuntimeError("decision receipt template must not approve a public schema")
    if template.get("production_authorized") is not False:
        raise RuntimeError("decision receipt template must not authorize Production")

    classes = template.get("public_classes")
    if not isinstance(classes, dict) or set(classes) != EXPECTED_CLASSES:
        raise RuntimeError("decision receipt template class set mismatch")
    if any(item.get("treatment") != "pending" for item in classes.values()):
        raise RuntimeError("all template class treatments must remain pending")

    providers = template.get("provider_dispositions")
    if not isinstance(providers, list) or not providers:
        raise RuntimeError("decision receipt template lacks provider dispositions")
    if any(item.get("status") != "pending" for item in providers):
        raise RuntimeError("all template provider dispositions must remain pending")

    return {
        "status": "passed",
        "rights_gate": "hold",
        "decision_required": True,
        "legal_conclusion_recorded": False,
        "provider_dispositions_pending": len(providers),
        "public_classes_pending": len(classes),
        "production_authorized": False,
        "real_provider_evidence_authorized": False,
        "public_replacement_authorized": False,
    }


def main() -> int:
    report = validate(Path(__file__).resolve().parents[1])
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
