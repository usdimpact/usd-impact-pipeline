#!/usr/bin/env python3
"""Decide whether the Weekly Score workflow must generate or exit as a no-op.

The preflight runs before any live provider retrieval or generated-file write.
An already published expected week is immutable: its checked-in release and any
frozen predictive origin must validate exactly before the workflow can succeed
as a no-op.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from scripts import validate_weekly_release


class PreflightError(RuntimeError):
    """Raised when publication state is partial, inconsistent, or invalid."""


@dataclass(frozen=True)
class PreflightResult:
    action: str
    expected_week: str
    published_week: str | None
    reason: str


def latest_completed_friday(value: datetime) -> date:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    utc_date = value.astimezone(timezone.utc).date()
    return utc_date - timedelta(days=(utc_date.weekday() - 4) % 7)


def _read_json(path: Path, label: str) -> dict:
    if not path.is_file() or path.stat().st_size == 0:
        raise PreflightError(f"Missing or empty {label}: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PreflightError(f"Invalid {label}: {path}") from error
    if not isinstance(payload, dict):
        raise PreflightError(f"{label} must be a JSON object: {path}")
    return payload


def _week(value: object, label: str) -> date:
    if not isinstance(value, str) or not value:
        raise PreflightError(f"{label} is missing")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise PreflightError(f"{label} is not an ISO date: {value}") from error
    if parsed.weekday() != 4:
        raise PreflightError(f"{label} must be a Friday: {value}")
    return parsed


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expected_paths(root: Path, week: str) -> tuple[Path, ...]:
    return (
        root / f"public/archive/{week}/score.json",
        root / f"public/archive/{week}/weekly_input.json",
        root / f"public/archive/{week}/repro_bundle.json",
        root / f"public/archive/{week}/en.html",
        root / f"public/archive/{week}/es.html",
        root / f"commentary/archive/{week}_en.md",
        root / f"commentary/archive/{week}_es.md",
        root / f"data/weekly_input_{week}.json",
    )


def _validate_predictive_freeze(root: Path, week: str, archive_bundle: Path) -> None:
    manifest_path = root / "research/score_v2_predictive_manifest.json"
    default_record = root / f"research/predictive/score_v2_predictive_week_{week}.json"
    if not manifest_path.exists():
        if default_record.exists():
            raise PreflightError(
                "Predictive weekly record exists without its append-only manifest"
            )
        return

    manifest = _read_json(manifest_path, "predictive manifest")
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise PreflightError("Predictive manifest entries must be a list")
    matches = [
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("week") == week
    ]
    if len(matches) > 1:
        raise PreflightError(f"Predictive manifest has duplicate entries for {week}")
    if not matches:
        if default_record.exists():
            raise PreflightError(
                f"Predictive record for {week} is not bound by the manifest"
            )
        return

    entry = matches[0]
    archive_hash = _sha256(archive_bundle)
    if entry.get("source_v2_bundle_sha256") != archive_hash:
        raise PreflightError(f"Predictive source archive hash mismatch: {week}")

    record_name = str(entry.get("weekly_record_file", ""))
    if not record_name or Path(record_name).name != record_name:
        raise PreflightError(f"Predictive manifest record path is invalid for {week}")
    record_path = root / "research/predictive" / record_name
    if not record_path.is_file():
        raise PreflightError(f"Predictive weekly record is missing for {week}")
    if entry.get("weekly_record_sha256") != _sha256(record_path):
        raise PreflightError(f"Predictive weekly record hash mismatch: {week}")

    record = _read_json(record_path, "predictive weekly record")
    source = record.get("source_v2_bundle")
    if record.get("week") != week or not isinstance(source, dict):
        raise PreflightError(f"Predictive weekly record contract mismatch: {week}")
    if source.get("sha256") != archive_hash:
        raise PreflightError(f"Predictive weekly record source hash mismatch: {week}")


def evaluate(root: Path, *, now: datetime) -> PreflightResult:
    root = root.resolve()
    expected_date = latest_completed_friday(now)
    expected = expected_date.isoformat()

    score_path = root / "public/data/usd_impact_score_v2.json"
    bridge_path = root / "public/data/weekly_input_latest.json"
    bundle_path = root / "public/data/score_repro_bundle_latest.json"
    authorities = (score_path, bridge_path, bundle_path)
    present = [path.is_file() for path in authorities]
    current_evidence = [path for path in _expected_paths(root, expected) if path.exists()]

    if not any(present):
        if current_evidence:
            raise PreflightError(
                f"Partial {expected} publication exists without latest release authorities"
            )
        return PreflightResult(
            action="generate",
            expected_week=expected,
            published_week=None,
            reason=f"No prior publication authorities exist; generate {expected}.",
        )
    if not all(present):
        missing = [
            str(path.relative_to(root))
            for path, exists in zip(authorities, present)
            if not exists
        ]
        raise PreflightError(
            "Publication authorities are incomplete: " + ", ".join(missing)
        )

    score = _read_json(score_path, "latest score JSON")
    bridge = _read_json(bridge_path, "latest bridge JSON")
    bundle = _read_json(bundle_path, "latest reproduction bundle")
    authority_weeks = {
        "score": _week(
            (score.get("metadata") or {}).get("latest_date"),
            "score latest_date",
        ),
        "bridge": _week(bridge.get("week_ending"), "bridge week_ending"),
        "bundle": _week(bundle.get("score_week"), "bundle score_week"),
    }
    unique_weeks = set(authority_weeks.values())
    if len(unique_weeks) != 1:
        detail = ", ".join(
            f"{name}={week.isoformat()}" for name, week in authority_weeks.items()
        )
        raise PreflightError(f"Publication authorities disagree: {detail}")

    published_date = unique_weeks.pop()
    published = published_date.isoformat()
    if published_date > expected_date:
        raise PreflightError(
            f"Published week {published} is later than expected completed Friday {expected}"
        )
    if published_date < expected_date:
        if current_evidence:
            relative = ", ".join(
                str(path.relative_to(root)) for path in current_evidence
            )
            raise PreflightError(
                f"Partial {expected} publication exists while latest authorities remain "
                f"at {published}: {relative}"
            )
        return PreflightResult(
            action="generate",
            expected_week=expected,
            published_week=published,
            reason=f"Latest complete publication is {published}; generate {expected}.",
        )

    required = _expected_paths(root, expected)
    missing = [
        str(path.relative_to(root))
        for path in required
        if not path.is_file() or path.stat().st_size == 0
    ]
    if missing:
        raise PreflightError(
            f"Published week {expected} is incomplete: " + ", ".join(missing)
        )

    archived_score_path = root / f"public/archive/{expected}/score.json"
    archived_bridge_path = root / f"public/archive/{expected}/weekly_input.json"
    archived_bundle_path = root / f"public/archive/{expected}/repro_bundle.json"
    dated_bridge_path = root / f"data/weekly_input_{expected}.json"
    if _read_json(archived_score_path, "archived score JSON") != score:
        raise PreflightError(
            f"Archived score JSON differs from latest score JSON for {expected}"
        )
    if _read_json(archived_bridge_path, "archived bridge JSON") != bridge:
        raise PreflightError(
            f"Archived bridge JSON differs from latest bridge JSON for {expected}"
        )
    if _read_json(dated_bridge_path, "dated bridge JSON") != bridge:
        raise PreflightError(
            f"Dated bridge JSON differs from latest bridge JSON for {expected}"
        )
    if _read_json(archived_bundle_path, "archived reproduction bundle") != bundle:
        raise PreflightError(
            f"Archived reproduction bundle differs from latest bundle for {expected}"
        )

    try:
        validated_week = validate_weekly_release.validate(root)
    except Exception as error:
        raise PreflightError(
            f"Existing published release failed strict validation for {expected}: {error}"
        ) from error
    if validated_week != expected:
        raise PreflightError(
            f"Strict release validation returned {validated_week}, expected {expected}"
        )

    _validate_predictive_freeze(root, expected, archived_bundle_path)
    return PreflightResult(
        action="noop",
        expected_week=expected,
        published_week=published,
        reason=(
            f"Week {expected} is already fully published, reproducible, and bound to "
            "its frozen predictive evidence; no provider retrieval or generated write "
            "is allowed."
        ),
    )


def _write_github_output(path: Path, result: PreflightResult) -> None:
    safe_reason = result.reason.replace("\r", " ").replace("\n", " ")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"action={result.action}\n")
        handle.write(f"week={result.expected_week}\n")
        handle.write(f"published_week={result.published_week or ''}\n")
        handle.write(f"reason={safe_reason}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--now", help="Optional ISO-8601 UTC clock override for tests")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    now = (
        datetime.fromisoformat(args.now.replace("Z", "+00:00"))
        if args.now
        else datetime.now(timezone.utc)
    )
    try:
        result = evaluate(args.root, now=now)
    except PreflightError as error:
        print(f"Weekly publication preflight failed: {error}", file=sys.stderr)
        return 1

    print(
        f"Weekly publication preflight: action={result.action}; "
        f"expected_week={result.expected_week}; "
        f"published_week={result.published_week or 'none'}"
    )
    print(result.reason)
    if args.github_output:
        _write_github_output(args.github_output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
