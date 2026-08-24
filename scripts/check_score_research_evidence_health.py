#!/usr/bin/env python3
"""Read-only health check for weekly Score v2/v3 research evidence review."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scripts import score_v2_predictive_manifest as manifest_v2
from scripts import score_v3_manifest as manifest_v3

SCORE_PATH = Path("public/data/usd_impact_score_v2.json")
V2_MANIFEST_PATH = Path("research/score_v2_predictive_manifest.json")
V3_MANIFEST_PATH = Path("research/score_v3_prospective_manifest.json")
V3_INITIALIZATION_MANIFEST_PATH = Path(
    "research/score_v3_initialization_2026-08-21.manifest.json"
)
HOLDOUT_START = date(2026, 8, 28)


@dataclass(frozen=True)
class Study:
    study_id: str
    title_prefix: str
    branch_prefix: str


@dataclass(frozen=True)
class StudyHealth:
    study_id: str
    status: str
    published_week: str
    manifest_latest_week: str | None
    open_pr_url: str | None
    detail: str


STUDIES = (
    Study(
        "score_v2_predictive",
        "Record Score v2 predictive evidence — ",
        "automation/score-v2-predictive-",
    ),
    Study(
        "score_v3_shadow",
        "Record Score v3 shadow research — ",
        "automation/score-v3-shadow-",
    ),
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _published_week(root: Path) -> date:
    payload = _read_json(root / SCORE_PATH)
    try:
        week = date.fromisoformat(str(payload["metadata"]["latest_date"]))
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError("Score v2 latest_date is missing or invalid") from error
    if week.weekday() != 4:
        raise RuntimeError(f"Score v2 latest_date is not a Friday: {week}")
    return week


def _validate_open_prs(payload: Any) -> list[dict[str, str]]:
    if not isinstance(payload, list):
        raise RuntimeError("Open-PR input must be a JSON array")
    validated: list[dict[str, str]] = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise RuntimeError(f"Open PR {index} must be an object")
        required = {"title", "url", "headRefName"}
        if not required.issubset(item):
            raise RuntimeError(f"Open PR {index} lacks title, URL, or head branch")
        validated.append({key: str(item[key]) for key in required})
    return validated


def evaluate_study(
    study: Study,
    *,
    published_week: date,
    entry_weeks: list[str],
    open_prs: list[dict[str, str]],
    complete: bool = False,
) -> StudyHealth:
    week = published_week.isoformat()
    latest = entry_weeks[-1] if entry_weeks else None
    if published_week < HOLDOUT_START:
        return StudyHealth(
            study.study_id,
            "not_due",
            week,
            latest,
            None,
            f"Holdout begins {HOLDOUT_START}; no evidence is due.",
        )
    if complete:
        return StudyHealth(
            study.study_id,
            "complete",
            week,
            latest,
            None,
            "The preregistered evidence sample is complete.",
        )
    if week in entry_weeks:
        return StudyHealth(
            study.study_id,
            "landed",
            week,
            latest,
            None,
            "The current published week is present on main.",
        )

    expected_title = f"{study.title_prefix}{week}"
    expected_branch_prefix = f"{study.branch_prefix}{week}-"
    matches = [
        item
        for item in open_prs
        if item["title"] == expected_title
        and item["headRefName"].startswith(expected_branch_prefix)
    ]
    if len(matches) == 1:
        return StudyHealth(
            study.study_id,
            "open_review_required",
            week,
            latest,
            matches[0]["url"],
            "The current evidence PR is open and must pass checks and be reviewed before merge.",
        )
    if len(matches) > 1:
        return StudyHealth(
            study.study_id,
            "duplicate_open_prs",
            week,
            latest,
            None,
            "Multiple exact evidence PRs are open for the current week; investigate without merging blindly.",
        )
    return StudyHealth(
        study.study_id,
        "missing_evidence",
        week,
        latest,
        None,
        "The current week is absent from main and no exact evidence PR is open.",
    )


def build_health(root: Path, open_prs_payload: Any) -> dict[str, Any]:
    root = root.resolve()
    open_prs = _validate_open_prs(open_prs_payload)
    week = _published_week(root)

    v2 = manifest_v2.load_manifest(root / V2_MANIFEST_PATH)
    v2_report = manifest_v2.validate_manifest(v2, root=root)
    v3 = manifest_v3.load_manifest(root / V3_MANIFEST_PATH)
    v3_report = manifest_v3.validate_manifest(
        v3,
        initialization_manifest_path=root / V3_INITIALIZATION_MANIFEST_PATH,
    )

    states = [
        evaluate_study(
            STUDIES[0],
            published_week=week,
            entry_weeks=[str(entry["week"]) for entry in v2["entries"]],
            open_prs=open_prs,
            complete=bool(v2_report["study_complete"]),
        ),
        evaluate_study(
            STUDIES[1],
            published_week=week,
            entry_weeks=[str(entry["week"]) for entry in v3["entries"]],
            open_prs=open_prs,
        ),
    ]
    healthy_statuses = {"not_due", "landed", "complete"}
    healthy = all(state.status in healthy_statuses for state in states)
    return {
        "status": "healthy" if healthy else "attention_required",
        "healthy": healthy,
        "published_week": week.isoformat(),
        "holdout_start": HOLDOUT_START.isoformat(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "evidence_modified": False,
        "production_modified": False,
        "performance_calculated": False,
        "studies": [asdict(state) for state in states],
    }


def render_report(report: dict[str, Any]) -> str:
    lines = [
        "# Score research evidence review health",
        "",
        f"Status: **{report['status'].upper()}**",
        f"Published Score v2 week: `{report['published_week']}`",
        f"Prospective holdout start: `{report['holdout_start']}`",
        "",
        "This is a read-only operational check. It does not calculate performance, modify evidence, or change production.",
        "",
        "## Study state",
        "",
    ]
    for state in report["studies"]:
        line = f"- **{state['study_id']} — {state['status']}:** {state['detail']}"
        if state.get("open_pr_url"):
            line += f" [Review PR]({state['open_pr_url']})"
        lines.append(line)
    if not report["healthy"]:
        lines.extend(
            [
                "",
                "## Required action",
                "",
                "Review and merge an exact open evidence PR only after its checks pass. If evidence is missing, inspect the downstream collector immediately. Do not skip, reconstruct, or backfill the week after later outcomes are visible.",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--open-prs", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=Path("score-research-evidence-health.md"))
    args = parser.parse_args()

    report = build_health(args.root, _read_json(args.open_prs))
    args.report.write_text(render_report(report), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
