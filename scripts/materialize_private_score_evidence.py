#!/usr/bin/env python3
"""Stage private Score reproduction evidence into an ephemeral research worktree.

Review-only prototype. This helper is intentionally not wired into Production.
It preserves the frozen research engines' existing file contract without making
provider-derived reproduction bundles part of the public repository/web tree.

Safety model:
- source evidence must live outside the repository and outside the worktree;
- destination must be an explicitly marked ephemeral git worktree outside the
  repository;
- existing destination evidence files are never overwritten;
- only strict reproduction bundle bytes are staged;
- the receipt contains hashes/paths only, never provider-derived values;
- cleanup deletes only files whose hashes still match the receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from scripts import build_score_repro_bundle as repro
from usd_impact_score_v2 import WEIGHTS

REPO_ROOT = Path(__file__).resolve().parents[1]
MARKER_NAME = ".private-score-evidence-worktree"
MARKER_VALUE = "score-private-evidence-ephemeral-v1\n"
RECEIPT_VERSION = "score-private-evidence-receipt-v1"
WEEK_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve()


def _require_outside_repo(path: Path, label: str) -> Path:
    resolved = _resolved(path)
    if resolved == REPO_ROOT or _is_relative_to(resolved, REPO_ROOT):
        raise RuntimeError(f"{label} must remain outside the repository")
    return resolved


def _require_ephemeral_worktree(path: Path) -> Path:
    root = _require_outside_repo(path, "worktree root")
    if not root.is_dir():
        raise RuntimeError("worktree root must exist")
    if not (root / ".git").exists():
        raise RuntimeError("worktree root must be a git checkout/worktree")
    marker = root / MARKER_NAME
    if not marker.is_file() or marker.read_text(encoding="utf-8") != MARKER_VALUE:
        raise RuntimeError(
            f"worktree root must contain {MARKER_NAME} with the reviewed marker value"
        )
    return root


def _require_evidence_root(path: Path, worktree_root: Path) -> Path:
    root = _require_outside_repo(path, "private evidence root")
    if not root.is_dir():
        raise RuntimeError("private evidence root must exist")
    if root == worktree_root or _is_relative_to(root, worktree_root):
        raise RuntimeError("private evidence root must remain outside the worktree")
    if _is_relative_to(worktree_root, root):
        raise RuntimeError("worktree must not be nested inside the private evidence root")
    return root


def _safe_destination(worktree_root: Path, relative: Path) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError(f"unsafe destination path: {relative}")
    target = worktree_root / relative
    resolved_parent = target.parent.resolve()
    if resolved_parent != worktree_root and not _is_relative_to(
        resolved_parent, worktree_root
    ):
        raise RuntimeError(f"destination escapes ephemeral worktree: {relative}")
    return target


def _load_bundle(path: Path, expected_week: str | None = None) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid reproduction bundle {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"reproduction bundle must be an object: {path}")

    week = str(payload.get("score_week", ""))
    if not WEEK_RE.fullmatch(week):
        raise RuntimeError(f"reproduction bundle has invalid score_week: {path}")
    if expected_week is not None and week != expected_week:
        raise RuntimeError(
            f"archive week mismatch: folder {expected_week}, bundle {week}"
        )

    components = payload.get("components")
    if not isinstance(components, dict) or set(components) != set(WEIGHTS):
        raise RuntimeError(f"reproduction bundle component set is invalid: {path}")
    repro.verify_bundle(payload)
    return payload


def discover_evidence(evidence_root: Path) -> tuple[Path, str, list[tuple[str, Path]]]:
    latest = evidence_root / "score_repro_bundle_latest.json"
    if not latest.is_file():
        raise RuntimeError("private evidence root is missing score_repro_bundle_latest.json")
    latest_payload = _load_bundle(latest)
    latest_week = str(latest_payload["score_week"])

    archive_root = evidence_root / "archive"
    archives: list[tuple[str, Path]] = []
    if archive_root.is_dir():
        for week_dir in sorted(archive_root.iterdir()):
            if not week_dir.is_dir() or not WEEK_RE.fullmatch(week_dir.name):
                continue
            bundle_path = week_dir / "repro_bundle.json"
            if not bundle_path.is_file():
                raise RuntimeError(
                    f"private archive directory is missing repro_bundle.json: {week_dir}"
                )
            _load_bundle(bundle_path, expected_week=week_dir.name)
            archives.append((week_dir.name, bundle_path))

    matching = [path for week, path in archives if week == latest_week]
    if len(matching) != 1:
        raise RuntimeError(
            f"private archive must contain exactly one bundle for latest week {latest_week}"
        )
    if latest.read_bytes() != matching[0].read_bytes():
        raise RuntimeError("private latest/archive bundle bytes differ")

    return latest, latest_week, archives


def _require_receipt_path(path: Path, worktree_root: Path, evidence_root: Path) -> Path:
    receipt = _require_outside_repo(path, "receipt path")
    if receipt == worktree_root or _is_relative_to(receipt, worktree_root):
        raise RuntimeError("receipt must remain outside the ephemeral worktree")
    if receipt == evidence_root or _is_relative_to(receipt, evidence_root):
        raise RuntimeError("receipt must remain outside the private evidence root")
    return receipt


def _validate_receipt(receipt: Any) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise RuntimeError("private evidence receipt must be an object")
    expected_keys = {
        "schema_version",
        "latest_week",
        "archive_count",
        "files",
        "provider_derived_values_in_receipt",
        "worktree_contract",
    }
    if set(receipt) != expected_keys:
        raise RuntimeError("private evidence receipt has unexpected fields")
    if receipt.get("schema_version") != RECEIPT_VERSION:
        raise RuntimeError("unsupported private evidence receipt")
    latest_week = receipt.get("latest_week")
    if not isinstance(latest_week, str) or not WEEK_RE.fullmatch(latest_week):
        raise RuntimeError("private evidence receipt has invalid latest_week")
    archive_count = receipt.get("archive_count")
    if (
        not isinstance(archive_count, int)
        or isinstance(archive_count, bool)
        or archive_count < 1
    ):
        raise RuntimeError("private evidence receipt has invalid archive_count")
    if receipt.get("provider_derived_values_in_receipt") is not False:
        raise RuntimeError("private evidence receipt value boundary is invalid")
    if receipt.get("worktree_contract") != "ephemeral-private-evidence-only":
        raise RuntimeError("private evidence receipt worktree contract is invalid")

    files = receipt.get("files")
    if not isinstance(files, list) or not files:
        raise RuntimeError("private evidence receipt has no staged files")

    seen: set[str] = set()
    archive_weeks: list[str] = []
    latest_seen = 0
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise RuntimeError("private evidence receipt file entry is invalid")
        path = item.get("path")
        expected_hash = item.get("sha256")
        if not isinstance(path, str) or path in seen:
            raise RuntimeError("private evidence receipt file path is invalid or duplicated")
        if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
            raise RuntimeError("private evidence receipt file hash is invalid")
        seen.add(path)

        if path == LATEST_DESTINATION.as_posix():
            latest_seen += 1
            continue
        match = ARCHIVE_DESTINATION_RE.fullmatch(path)
        if match is None:
            raise RuntimeError("private evidence receipt contains an unapproved path")
        archive_weeks.append(match.group(1))

    if latest_seen != 1:
        raise RuntimeError("private evidence receipt must contain exactly one latest bundle")
    if len(archive_weeks) != archive_count:
        raise RuntimeError("private evidence receipt archive_count does not match files")
    if archive_weeks.count(latest_week) != 1:
        raise RuntimeError(
            "private evidence receipt must contain exactly one archive for latest_week"
        )
    return receipt


def _write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    _validate_receipt(receipt)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
    except Exception:
        if path.exists():
            path.unlink()
        raise


def stage(
    evidence_root_arg: Path,
    worktree_root_arg: Path,
    receipt_arg: Path,
) -> dict[str, Any]:
    worktree_root = _require_ephemeral_worktree(worktree_root_arg)
    evidence_root = _require_evidence_root(evidence_root_arg, worktree_root)
    receipt_path = _require_receipt_path(receipt_arg, worktree_root, evidence_root)
    if receipt_path.exists():
        raise RuntimeError("receipt already exists; refusing to overwrite it")

    latest, latest_week, archives = discover_evidence(evidence_root)
    plan: list[tuple[Path, Path]] = [
        (latest, LATEST_DESTINATION)
    ]
    plan.extend(
        (
            source,
            Path("public/archive") / week / "repro_bundle.json",
        )
        for week, source in archives
    )

    for _source, relative in plan:
        target = _safe_destination(worktree_root, relative)
        if target.exists():
            raise RuntimeError(
                f"refusing to overwrite existing worktree evidence file: {relative}"
            )

    staged: list[dict[str, str]] = []
    try:
        for source, relative in plan:
            target = _safe_destination(worktree_root, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = source.read_bytes()
            target.write_bytes(raw)
            staged.append(
                {
                    "path": relative.as_posix(),
                    "sha256": sha256_bytes(raw),
                }
            )
    except Exception:
        for item in reversed(staged):
            target = _safe_destination(worktree_root, Path(item["path"]))
            if target.exists() and sha256_bytes(target.read_bytes()) == item["sha256"]:
                target.unlink()
        raise

    receipt = {
        "schema_version": RECEIPT_VERSION,
        "latest_week": latest_week,
        "archive_count": len(archives),
        "files": staged,
        "provider_derived_values_in_receipt": False,
        "worktree_contract": "ephemeral-private-evidence-only",
    }
    try:
        _write_receipt(receipt_path, receipt)
    except Exception:
        for item in reversed(staged):
            target = _safe_destination(worktree_root, Path(item["path"]))
            if target.exists() and sha256_bytes(target.read_bytes()) == item["sha256"]:
                target.unlink()
        raise
    return receipt


def cleanup(worktree_root_arg: Path, receipt_arg: Path) -> dict[str, Any]:
    worktree_root = _require_ephemeral_worktree(worktree_root_arg)
    receipt_path = _require_outside_repo(receipt_arg, "receipt path")
    if receipt_path == worktree_root or _is_relative_to(receipt_path, worktree_root):
        raise RuntimeError("receipt must remain outside the ephemeral worktree")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid private evidence receipt: {exc}") from exc
    receipt = _validate_receipt(receipt)
    files = receipt["files"]

    targets: list[Path] = []
    for item in files:
        if not isinstance(item, dict):
            raise RuntimeError("private evidence receipt file entry is invalid")
        relative = Path(str(item.get("path", "")))
        expected_hash = str(item.get("sha256", ""))
        target = _safe_destination(worktree_root, relative)
        if not target.is_file():
            raise RuntimeError(f"staged evidence file is missing: {relative}")
        actual_hash = sha256_bytes(target.read_bytes())
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"staged evidence file changed after materialization: {relative}"
            )
        targets.append(target)

    for target in targets:
        target.unlink()

    return {
        "schema_version": RECEIPT_VERSION,
        "removed_files": len(targets),
        "provider_derived_values_in_receipt": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    stage_parser = sub.add_parser("stage")
    stage_parser.add_argument("--evidence-root", type=Path, required=True)
    stage_parser.add_argument("--worktree-root", type=Path, required=True)
    stage_parser.add_argument("--receipt", type=Path, required=True)

    cleanup_parser = sub.add_parser("cleanup")
    cleanup_parser.add_argument("--worktree-root", type=Path, required=True)
    cleanup_parser.add_argument("--receipt", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "stage":
        report = stage(args.evidence_root, args.worktree_root, args.receipt)
    else:
        report = cleanup(args.worktree_root, args.receipt)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
