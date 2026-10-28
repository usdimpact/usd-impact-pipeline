#!/usr/bin/env python3
"""Build aggregate-only public research artifacts for Score rights containment.

Review-only prototype. This transformer consumes existing research outputs after
their calculations have completed and emits narrower publication views. It does
not modify the research engines, methodology, preregistration, source inputs,
workflow triggers, or Production paths.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Any

PIT_SCHEMA_VERSION = "score-public-v2-pit-safe-1"
ROBUSTNESS_SCHEMA_VERSION = "score-public-v2-robustness-safe-1"
VINTAGE_SCHEMA_VERSION = "score-public-v2-vintage-safe-1"

FORBIDDEN_KEYS = {
    "source_provenance",
    "provider",
    "provider_code",
    "series",
    "source_url",
    "drivers",
    "components",
    "weekly_level",
    "z",
    "z_unclipped",
    "z_clipped",
    "contribution",
    "omitted_driver",
    "flipped_driver",
    "dominant_driver",
    "top_pair",
    "top_pairs",
    "component_zscore_revision_summary",
    "component_zscore_revisions",
    "largest_absolute_component_revision",
    "archive_path",
}

VINTAGE_ROW_FIELDS = [
    "archive_id",
    "published_at_utc",
    "score_week",
    "as_published_score",
    "current_recalculated_score",
    "score_difference",
    "absolute_score_difference",
    "as_published_regime",
    "current_recalculated_regime",
    "regime_changed",
    "score_sign_changed",
]


def _require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def _pick(source: dict[str, Any], fields: tuple[str, ...], label: str) -> dict[str, Any]:
    missing = [field for field in fields if field not in source]
    if missing:
        raise ValueError(f"{label} is missing fields: {', '.join(missing)}")
    return {field: source[field] for field in fields}


def assert_aggregate_safe(payload: Any) -> None:
    def walk(value: Any, path: str = "$") -> None:
        if isinstance(value, dict):
            forbidden = FORBIDDEN_KEYS.intersection(value)
            if forbidden:
                raise ValueError(
                    f"aggregate-safe research contains forbidden keys at {path}: "
                    + ", ".join(sorted(forbidden))
                )
            for key, child in value.items():
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(payload)


def build_point_in_time(source: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "study",
        "generated_at_utc",
        "production_methodology_changed",
        "predictive_claim",
        "purpose",
        "min_prior_weeks",
        "first_evaluated_week",
        "last_evaluated_week",
        "evaluated_weeks",
        "summary",
        "anchor_windows",
        "weeks",
        "as_published_vintage",
        "limitations",
    )
    payload = {"schema_version": PIT_SCHEMA_VERSION, **_pick(source, fields, "point-in-time research")}
    _require_dict(payload["summary"], "point-in-time summary")
    _require_list(payload["anchor_windows"], "point-in-time anchor_windows")
    _require_list(payload["weeks"], "point-in-time weeks")
    assert_aggregate_safe(payload)
    return payload


def build_robustness(source: dict[str, Any]) -> dict[str, Any]:
    data = _require_dict(source.get("data"), "robustness data")
    safe_data = _pick(
        data,
        (
            "production_start_date",
            "first_complete_week",
            "latest_complete_week",
            "complete_weeks",
            "latest_production_recalculated_score",
            "latest_production_recalculated_regime",
        ),
        "robustness data",
    )

    fields = (
        "study",
        "generated_at_utc",
        "production_methodology_changed",
        "predictive_claim",
        "as_published_vintage",
        "purpose",
        "point_in_time_normalization",
        "rolling_normalization",
        "regime_threshold_sensitivity",
        "score_distribution",
        "regime_duration",
        "subperiod_stability",
        "limitations",
    )
    payload = {
        "schema_version": ROBUSTNESS_SCHEMA_VERSION,
        **_pick(source, fields, "robustness research"),
        "data": safe_data,
    }
    assert_aggregate_safe(payload)
    return payload


def build_vintage(source: dict[str, Any]) -> dict[str, Any]:
    current = _require_dict(source.get("current_reference"), "vintage current_reference")
    summary = _require_dict(source.get("summary"), "vintage summary")
    vintages = _require_list(source.get("vintages"), "vintage rows")
    excluded = _require_list(source.get("excluded_archives"), "excluded archives")

    safe_summary = _pick(
        summary,
        (
            "archive_files_scanned",
            "valid_vintages",
            "excluded_archives",
            "first_published_at_utc",
            "latest_published_at_utc",
            "mean_signed_score_difference",
            "mean_absolute_score_difference",
            "maximum_absolute_score_difference",
            "maximum_revision_archive_id",
            "maximum_revision_score_week",
            "regime_agreement_rate",
            "score_sign_agreement_rate",
        ),
        "vintage summary",
    )
    safe_vintages: list[dict[str, Any]] = []
    for index, row in enumerate(vintages):
        safe_vintages.append(
            _pick(_require_dict(row, f"vintage row {index}"), tuple(VINTAGE_ROW_FIELDS), f"vintage row {index}")
        )

    safe_excluded = []
    for index, row in enumerate(excluded):
        item = _require_dict(row, f"excluded archive {index}")
        safe_excluded.append(
            _pick(
                item,
                (
                    "archive_id",
                    "reason",
                    "generated_at_utc",
                    "declared_score_week",
                ),
                f"excluded archive {index}",
            )
        )

    payload = {
        "schema_version": VINTAGE_SCHEMA_VERSION,
        **_pick(
            source,
            (
                "study",
                "generated_at_utc",
                "production_methodology_changed",
                "predictive_claim",
                "as_published_vintage",
                "difference_definition",
                "purpose",
                "limitations",
            ),
            "vintage research",
        ),
        "current_reference": _pick(
            current,
            ("sha256", "generated_at_utc", "latest_week"),
            "vintage current_reference",
        ),
        "summary": safe_summary,
        "vintages": safe_vintages,
        "excluded_archives": safe_excluded,
    }
    assert_aggregate_safe(payload)
    return payload


def write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_vintage_csv(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=VINTAGE_ROW_FIELDS)
        writer.writeheader()
        writer.writerows(payload["vintages"])


def render_vintage_html(payload: dict[str, Any]) -> str:
    rows = []
    for item in payload["vintages"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item['score_week']))}</td>"
            f"<td>{float(item['as_published_score']):+.4f}</td>"
            f"<td>{float(item['current_recalculated_score']):+.4f}</td>"
            f"<td>{float(item['score_difference']):+.4f}</td>"
            f"<td>{html.escape(str(item['as_published_regime']))}</td>"
            f"<td>{html.escape(str(item['current_recalculated_regime']))}</td>"
            "</tr>"
        )
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"robots\" content=\"noindex,nofollow\">"
        "<title>USD Impact Score vintage comparison — aggregate view</title></head>"
        "<body><main><h1>Score vintage comparison — aggregate view</h1>"
        "<p>This review artifact contains aggregate Score/regime revision evidence only.</p>"
        "<table><thead><tr><th>Week</th><th>As published Score</th>"
        "<th>Current recalculated Score</th><th>Difference</th>"
        "<th>As published regime</th><th>Current regime</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></main></body></html>"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--point-in-time", type=Path, required=True)
    parser.add_argument("--robustness", type=Path, required=True)
    parser.add_argument("--vintage", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    point_source = json.loads(args.point_in_time.read_text(encoding="utf-8"))
    robustness_source = json.loads(args.robustness.read_text(encoding="utf-8"))
    vintage_source = json.loads(args.vintage.read_text(encoding="utf-8"))

    point = build_point_in_time(_require_dict(point_source, "point-in-time source"))
    robustness = build_robustness(_require_dict(robustness_source, "robustness source"))
    vintage = build_vintage(_require_dict(vintage_source, "vintage source"))

    write_json(point, args.output_dir / "score_v2_point_in_time_public_safe.json")
    write_json(robustness, args.output_dir / "score_v2_robustness_public_safe.json")
    write_json(vintage, args.output_dir / "score_v2_vintage_comparison_public_safe.json")
    write_vintage_csv(vintage, args.output_dir / "score_v2_vintage_comparison_public_safe.csv")
    (args.output_dir / "score_v2_vintage_comparison_public_safe.html").write_text(
        render_vintage_html(vintage),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
