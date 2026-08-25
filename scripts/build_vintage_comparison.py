#!/usr/bin/env python3
"""Compare as-published Score v2 releases with the current recalculation.

Only the declared latest observation from each dated archive is compared. This
avoids treating every overlapping row in every archive as an independent
publication. Invalid legacy archives are reported and excluded, never repaired
or silently accepted.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

import numpy as np

import usd_impact_score_v2 as score_v2


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CURRENT = ROOT / "public/data/usd_impact_score_v2.json"
DEFAULT_ARCHIVE_ROOT = ROOT / "public/archive"
DEFAULT_JSON_OUTPUT = ROOT / "public/data/research/score_v2_vintage_comparison_latest.json"
DEFAULT_CSV_OUTPUT = ROOT / "public/data/research/score_v2_vintage_comparison_latest.csv"
DEFAULT_HTML_OUTPUT = ROOT / "public/data/research/score_v2_vintage_comparison_latest.html"
ABSOLUTE_TOLERANCE = 1e-12


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Missing or empty score JSON: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a top-level JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _parse_datetime(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _score_index(payload: dict[str, Any], path: Path) -> dict[str, dict[str, Any]]:
    weeks = payload.get("weeks")
    if not isinstance(weeks, list) or not weeks:
        raise ValueError(f"Score JSON has no weekly observations: {path}")
    index: dict[str, dict[str, Any]] = {}
    for row in weeks:
        if not isinstance(row, dict) or not isinstance(row.get("date"), str):
            raise ValueError(f"Invalid weekly observation in {path}")
        if row["date"] in index:
            raise ValueError(f"Duplicate score week {row['date']} in {path}")
        index[row["date"]] = row
    return index


def _archive_rejection(
    archive_id: str,
    path: Path,
    reason: str,
    **details: Any,
) -> dict[str, Any]:
    return {
        "archive_id": archive_id,
        "path": _display_path(path),
        "reason": reason,
        **details,
    }


def _validate_archive(
    archive_id: str,
    path: Path,
    payload: dict[str, Any],
    current_index: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    metadata = payload.get("metadata")
    weeks = payload.get("weeks")
    if not isinstance(metadata, dict) or not isinstance(weeks, list) or not weeks:
        return None, _archive_rejection(archive_id, path, "missing_metadata_or_weeks")

    try:
        generated_at = _parse_datetime(metadata["generated_at_utc"])
        score_week = str(metadata["latest_date"])
        latest = weeks[-1]
    except (KeyError, TypeError, ValueError) as error:
        return None, _archive_rejection(
            archive_id, path, "invalid_publication_metadata", error=str(error)
        )

    if score_week > generated_at.date().isoformat():
        return None, _archive_rejection(
            archive_id,
            path,
            "score_week_after_generation_date",
            generated_at_utc=generated_at.isoformat(),
            declared_score_week=score_week,
        )
    if metadata.get("n_weeks") != len(weeks):
        return None, _archive_rejection(
            archive_id,
            path,
            "metadata_week_count_mismatch",
            declared=metadata.get("n_weeks"),
            actual=len(weeks),
        )
    if not isinstance(latest, dict) or latest.get("date") != score_week:
        return None, _archive_rejection(
            archive_id,
            path,
            "latest_row_date_mismatch",
            declared_score_week=score_week,
            latest_row_date=latest.get("date") if isinstance(latest, dict) else None,
        )

    try:
        latest_score = float(latest["score"])
        declared_score = float(metadata["latest_score"])
        latest_regime = str(latest["regime"])
        declared_regime = str(metadata["latest_regime"])
    except (KeyError, TypeError, ValueError) as error:
        return None, _archive_rejection(
            archive_id, path, "invalid_latest_score_metadata", error=str(error)
        )
    if not np.isclose(latest_score, declared_score, atol=ABSOLUTE_TOLERANCE, rtol=0):
        return None, _archive_rejection(
            archive_id, path, "latest_score_mismatch"
        )
    if latest_regime != declared_regime:
        return None, _archive_rejection(
            archive_id, path, "latest_regime_mismatch"
        )
    if score_week not in current_index:
        return None, _archive_rejection(
            archive_id,
            path,
            "score_week_missing_from_current_history",
            declared_score_week=score_week,
        )

    current = current_index[score_week]
    missing = [
        field for field in (*score_v2.WEIGHTS, "score", "regime")
        if field not in latest or field not in current
    ]
    if missing:
        return None, _archive_rejection(
            archive_id, path, "missing_comparison_fields", fields=missing
        )

    components = {}
    for driver in score_v2.WEIGHTS:
        published_value = float(latest[driver])
        current_value = float(current[driver])
        components[driver] = {
            "as_published_zscore": published_value,
            "current_recalculated_zscore": current_value,
            "difference": current_value - published_value,
        }
    largest_driver = max(
        components,
        key=lambda driver: abs(components[driver]["difference"]),
    )
    score_difference = float(current["score"]) - latest_score
    return {
        "archive_id": archive_id,
        "archive_path": _display_path(path),
        "archive_sha256": _sha256(path),
        "published_at_utc": generated_at.isoformat(),
        "score_week": score_week,
        "as_published_score": latest_score,
        "current_recalculated_score": float(current["score"]),
        "score_difference": score_difference,
        "absolute_score_difference": abs(score_difference),
        "as_published_regime": latest_regime,
        "current_recalculated_regime": str(current["regime"]),
        "regime_changed": latest_regime != str(current["regime"]),
        "score_sign_changed": bool(np.sign(latest_score) != np.sign(float(current["score"]))),
        "largest_absolute_component_revision": {
            "driver": largest_driver,
            "absolute_difference": abs(components[largest_driver]["difference"]),
        },
        "component_zscore_revisions": components,
    }, None


def build_vintage_comparison(
    current_path: Path = DEFAULT_CURRENT,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    *,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    generated_at = (generated_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    current_payload = _load_json(current_path)
    current_index = _score_index(current_payload, current_path)
    current_metadata = current_payload.get("metadata")
    if not isinstance(current_metadata, dict):
        raise ValueError("Current score JSON is missing metadata")

    vintages: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for path in sorted(archive_root.glob("20*/score.json")):
        archive_id = path.parent.name
        try:
            payload = _load_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            excluded.append(_archive_rejection(
                archive_id, path, "unreadable_archive", error=str(error)
            ))
            continue
        vintage, rejection = _validate_archive(
            archive_id, path, payload, current_index
        )
        if vintage is not None:
            vintages.append(vintage)
        elif rejection is not None:
            excluded.append(rejection)

    if not vintages:
        raise RuntimeError("No valid dated score archives are available for comparison")
    vintages.sort(key=lambda row: (row["published_at_utc"], row["archive_id"]))

    score_differences = np.array(
        [row["score_difference"] for row in vintages], dtype=float
    )
    component_summary = {}
    for driver in score_v2.WEIGHTS:
        values = np.array([
            row["component_zscore_revisions"][driver]["difference"]
            for row in vintages
        ], dtype=float)
        component_summary[driver] = {
            "mean_signed_difference": float(values.mean()),
            "mean_absolute_difference": float(np.abs(values).mean()),
            "maximum_absolute_difference": float(np.abs(values).max()),
        }
    max_row = max(vintages, key=lambda row: row["absolute_score_difference"])

    return {
        "study": "usd_impact_score_v2_as_published_vs_current_vintage",
        "generated_at_utc": generated_at.isoformat(),
        "production_methodology_changed": False,
        "predictive_claim": False,
        "as_published_vintage": True,
        "difference_definition": "current_recalculated_value - as_published_value",
        "purpose": (
            "Measure how each valid as-published latest score differs from the "
            "same week in the current full-history recalculation."
        ),
        "current_reference": {
            "path": _display_path(current_path),
            "sha256": _sha256(current_path),
            "generated_at_utc": current_metadata.get("generated_at_utc"),
            "latest_week": current_metadata.get("latest_date"),
        },
        "summary": {
            "archive_files_scanned": len(vintages) + len(excluded),
            "valid_vintages": len(vintages),
            "excluded_archives": len(excluded),
            "first_published_at_utc": vintages[0]["published_at_utc"],
            "latest_published_at_utc": vintages[-1]["published_at_utc"],
            "mean_signed_score_difference": float(score_differences.mean()),
            "mean_absolute_score_difference": float(np.abs(score_differences).mean()),
            "maximum_absolute_score_difference": float(np.abs(score_differences).max()),
            "maximum_revision_archive_id": max_row["archive_id"],
            "maximum_revision_score_week": max_row["score_week"],
            "regime_agreement_rate": float(np.mean([
                not row["regime_changed"] for row in vintages
            ])),
            "score_sign_agreement_rate": float(np.mean([
                not row["score_sign_changed"] for row in vintages
            ])),
            "component_zscore_revision_summary": component_summary,
        },
        "vintages": vintages,
        "excluded_archives": excluded,
        "limitations": [
            "This is a descriptive revision audit, not a predictive backtest or performance test.",
            "Only the latest declared week from each dated archive is treated as an as-published observation.",
            "Differences can combine expanding-sample normalization effects and upstream provider revisions; this artifact does not identify their separate causes.",
            "The legacy archive is incomplete and includes explicitly reported invalid entries; excluded archives are not repaired or silently rewritten.",
            "Archive timestamps and contents are first-party publication records, not independently notarized evidence.",
        ],
    }


def write_csv(report: dict[str, Any], path: Path) -> None:
    fields = [
        "archive_id", "published_at_utc", "score_week", "as_published_score",
        "current_recalculated_score", "score_difference", "absolute_score_difference",
        "as_published_regime", "current_recalculated_regime", "regime_changed",
        "score_sign_changed", "largest_revision_driver",
        "largest_absolute_component_revision",
    ] + [f"{driver}_zscore_difference" for driver in score_v2.WEIGHTS]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for vintage in report["vintages"]:
            row = {key: vintage[key] for key in fields if key in vintage}
            row["largest_revision_driver"] = (
                vintage["largest_absolute_component_revision"]["driver"]
            )
            row["largest_absolute_component_revision"] = (
                vintage["largest_absolute_component_revision"]["absolute_difference"]
            )
            for driver in score_v2.WEIGHTS:
                row[f"{driver}_zscore_difference"] = (
                    vintage["component_zscore_revisions"][driver]["difference"]
                )
            writer.writerow(row)


def _score(value: float) -> str:
    return f"{value:+.3f}"


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def write_html(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    current_reference = report["current_reference"]
    rows = []
    for vintage in reversed(report["vintages"]):
        largest = vintage["largest_absolute_component_revision"]
        regime_change = "Yes" if vintage["regime_changed"] else "No"
        rows.append(
            "<tr>"
            f"<td>{escape(vintage['published_at_utc'])}</td>"
            f"<td>{escape(vintage['score_week'])}</td>"
            f"<td>{_score(float(vintage['as_published_score']))}</td>"
            f"<td>{_score(float(vintage['current_recalculated_score']))}</td>"
            f"<td>{_score(float(vintage['score_difference']))}</td>"
            f"<td>{escape(vintage['as_published_regime'])}</td>"
            f"<td>{escape(vintage['current_recalculated_regime'])}</td>"
            f"<td>{regime_change}</td>"
            f"<td>{escape(str(largest['driver']))} ({float(largest['absolute_difference']):.3f})</td>"
            "</tr>"
        )

    excluded_rows = []
    for excluded in report["excluded_archives"]:
        excluded_rows.append(
            "<tr>"
            f"<td>{escape(str(excluded['archive_id']))}</td>"
            f"<td>{escape(str(excluded['reason']))}</td>"
            "</tr>"
        )
    if not excluded_rows:
        excluded_rows.append('<tr><td colspan="2">None.</td></tr>')

    limitations = "".join(
        f"<li>{escape(str(item))}</li>" for item in report["limitations"]
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="index,follow">
  <title>USD Impact Score v2 | As-published vs current vintage audit</title>
  <meta name="description" content="Human-readable revision audit comparing valid as-published USD Impact Score v2 readings with the same weeks in the current recalculated history.">
  <style>
    :root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f6f7; color: #17202a; }}
    body {{ margin: 0; }}
    main {{ max-width: 1200px; margin: 0 auto; padding: 36px 20px 64px; }}
    h1, h2 {{ line-height: 1.15; }}
    h1 {{ max-width: 900px; margin-bottom: 12px; }}
    p {{ line-height: 1.6; }}
    a {{ color: #163a63; }}
    .lede {{ max-width: 900px; font-size: 1.08rem; }}
    .notice {{ margin: 24px 0; padding: 16px 18px; border-left: 4px solid #9b7a2f; background: #fffaf0; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin: 24px 0; }}
    .card {{ background: #fff; border: 1px solid #dfe3e7; border-radius: 10px; padding: 16px; }}
    .metric {{ font-size: 1.35rem; font-weight: 700; margin-top: 6px; }}
    .table-wrap {{ overflow-x: auto; background: #fff; border: 1px solid #dfe3e7; border-radius: 10px; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 980px; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #edf0f2; text-align: left; vertical-align: top; font-size: 0.92rem; }}
    th {{ background: #f0f2f4; position: sticky; top: 0; }}
    code {{ overflow-wrap: anywhere; }}
    .links {{ display: flex; gap: 14px; flex-wrap: wrap; margin: 18px 0 30px; }}
    .links a {{ display: inline-block; padding: 9px 12px; background: #17202a; color: #fff; text-decoration: none; border-radius: 7px; }}
    footer {{ margin-top: 36px; color: #53606c; font-size: 0.9rem; }}
  </style>
</head>
<body>
<main>
  <p><strong>USD Impact Score v2 research audit</strong></p>
  <h1>As-published vs current recalculated score vintages</h1>
  <p class="lede">This page compares each valid dated archive's declared latest USD Impact Score v2 reading with the same score week in the current full-history recalculation. It is designed to make historical revision risk directly inspectable.</p>

  <div class="notice"><strong>Descriptive revision audit only.</strong> This is not a predictive backtest, performance record, trading signal, probability estimate, or independent audit. Differences can combine expanding-sample normalization effects with upstream provider revisions.</div>

  <div class="grid">
    <div class="card"><div>Valid as-published vintages</div><div class="metric">{int(summary['valid_vintages'])}</div></div>
    <div class="card"><div>Mean absolute score revision</div><div class="metric">{float(summary['mean_absolute_score_difference']):.3f}</div></div>
    <div class="card"><div>Maximum absolute score revision</div><div class="metric">{float(summary['maximum_absolute_score_difference']):.3f}</div></div>
    <div class="card"><div>Regime agreement</div><div class="metric">{_percent(float(summary['regime_agreement_rate']))}</div></div>
    <div class="card"><div>Score-sign agreement</div><div class="metric">{_percent(float(summary['score_sign_agreement_rate']))}</div></div>
    <div class="card"><div>Excluded legacy archives</div><div class="metric">{int(summary['excluded_archives'])}</div></div>
  </div>

  <p><strong>Difference definition:</strong> current recalculated value minus as-published value. Current reference latest week: <code>{escape(str(current_reference.get('latest_week')))}</code>. Audit generated: <code>{escape(str(report['generated_at_utc']))}</code>.</p>

  <div class="links">
    <a href="./score_v2_vintage_comparison_latest.json">Download JSON</a>
    <a href="./score_v2_vintage_comparison_latest.csv">Download CSV</a>
    <a href="/archive/en/">Open score archive</a>
  </div>

  <h2>Vintage-by-vintage comparison</h2>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Published at (UTC)</th><th>Score week</th><th>As published</th><th>Current recalculated</th><th>Difference</th><th>As-published regime</th><th>Current regime</th><th>Regime changed?</th><th>Largest component revision</th>
        </tr>
      </thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </div>

  <h2>Excluded archives</h2>
  <p>Invalid legacy archives are reported rather than repaired or silently accepted.</p>
  <div class="table-wrap">
    <table style="min-width: 520px">
      <thead><tr><th>Archive ID</th><th>Exclusion reason</th></tr></thead>
      <tbody>{''.join(excluded_rows)}</tbody>
    </table>
  </div>

  <h2>Limitations</h2>
  <ul>{limitations}</ul>

  <footer>
    <p>Educational and informational only. Archive timestamps and contents are first-party publication records, not independently notarized evidence. See the public USD Impact Score methodology for the production formula, normalization and validation limitations.</p>
  </footer>
</main>
</body>
</html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", type=Path, default=DEFAULT_CURRENT)
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV_OUTPUT)
    parser.add_argument("--html-output", type=Path, default=DEFAULT_HTML_OUTPUT)
    args = parser.parse_args()

    report = build_vintage_comparison(args.current, args.archive_root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    write_csv(report, args.csv_output)
    write_html(report, args.html_output)
    print(
        "Vintage comparison generated: "
        f"{report['summary']['valid_vintages']} valid, "
        f"{report['summary']['excluded_archives']} excluded."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
