#!/usr/bin/env python3
"""Decide whether the weekly release workflow needs one recovery dispatch."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass(frozen=True)
class RecoveryDecision:
    should_dispatch: bool
    reason: str


def parse_github_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def decide_weekly_recovery(
    runs: list[dict],
    *,
    now: datetime,
    max_age: timedelta,
) -> RecoveryDecision:
    """Request one dispatch when the expected Friday run failed or is absent."""
    if not runs:
        return RecoveryDecision(True, "no Weekly USD Impact Score run was found")

    latest = runs[0]
    status = str(latest.get("status") or "unknown")
    conclusion = str(latest.get("conclusion") or "unknown")

    if status in {"queued", "in_progress", "pending", "waiting", "requested"}:
        return RecoveryDecision(False, f"latest run is still {status}")

    created_at = latest.get("createdAt")
    if not created_at:
        return RecoveryDecision(True, "latest run has no creation timestamp")

    try:
        age = now.astimezone(timezone.utc) - parse_github_time(str(created_at))
    except ValueError:
        return RecoveryDecision(True, f"latest run has an invalid creation timestamp: {created_at}")

    if age < timedelta(0):
        return RecoveryDecision(True, "latest run timestamp is in the future")

    if age > max_age:
        return RecoveryDecision(
            True,
            f"latest run is stale ({age.total_seconds() / 3600:.1f} hours old)",
        )

    if status == "completed" and conclusion == "success":
        return RecoveryDecision(False, "latest recent run completed successfully")

    return RecoveryDecision(
        True,
        f"latest recent run ended with status={status}, conclusion={conclusion}",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-file", type=Path, required=True)
    parser.add_argument("--max-age-hours", type=float, default=6)
    parser.add_argument("--now", help="Optional ISO-8601 clock override for tests or manual diagnosis")
    args = parser.parse_args()

    runs = json.loads(args.runs_file.read_text(encoding="utf-8"))
    if not isinstance(runs, list):
        raise ValueError("GitHub run data must be a JSON list")

    now = parse_github_time(args.now) if args.now else datetime.now(timezone.utc)
    decision = decide_weekly_recovery(
        runs,
        now=now,
        max_age=timedelta(hours=args.max_age_hours),
    )
    action = "dispatch" if decision.should_dispatch else "skip"
    print(f"Recovery decision: {action} — {decision.reason}")
    return 0 if decision.should_dispatch else 1


if __name__ == "__main__":
    raise SystemExit(main())
