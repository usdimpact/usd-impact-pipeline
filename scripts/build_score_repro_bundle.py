#!/usr/bin/env python3
"""Build and verify an immutable USD Impact Score v2 release-reproduction bundle.

This tool does not change the production score methodology. It independently
recomputes the latest production week using the same public v2 functions,
checks that result against the already-generated score JSON, and freezes the
minimal information required to reproduce the published score later without
relying on revised upstream histories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import usd_impact_score_v2 as score_v2

TOLERANCE = 1e-9
BUNDLE_VERSION = 1
METHOD_VERSION = "usd_impact_score_v2"
INPUT_HISTORY_FINGERPRINT_VERSION = 1
INPUT_HISTORY_SCOPE = (
    "complete production weekly input matrix after limited daily alignment, "
    "Friday-ended resampling and complete-case filtering"
)
INPUT_HISTORY_CANONICALIZATION = (
    "UTF-8 CSV; date plus production driver order; YYYY-MM-DD dates; "
    "finite floats formatted with 17 significant digits; LF line endings"
)


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def _load_score_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "metadata" not in payload or "weeks" not in payload:
        raise RuntimeError("Score JSON does not match the v2 output contract")
    return payload


def _moment(value: float) -> float:
    if not np.isfinite(value):
        raise RuntimeError("Non-finite normalization moment")
    return float(value)


def _canonical_history_bytes(
    weekly_clean: pd.DataFrame,
    drivers: list[str],
) -> bytes:
    lines = [",".join(("date", *drivers))]
    for index, row in weekly_clean[drivers].iterrows():
        date_text = pd.Timestamp(index).date().isoformat()
        values = []
        for driver in drivers:
            value = float(row[driver])
            if not np.isfinite(value):
                raise RuntimeError(
                    f"Non-finite weekly input in fingerprint for {driver} {date_text}"
                )
            values.append(format(value, ".17g"))
        lines.append(",".join((date_text, *values)))
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_input_history_fingerprint(
    weekly_clean: pd.DataFrame,
) -> dict[str, Any]:
    """Fingerprint the exact input history without publishing its full values."""
    drivers = list(score_v2.WEIGHTS)
    frame = weekly_clean[drivers].dropna().sort_index()
    if frame.empty or frame.index.has_duplicates:
        raise RuntimeError("Input history must contain unique complete weekly rows")
    if not frame.index.is_monotonic_increasing:
        raise RuntimeError("Input history must be ordered by week")

    first_week = frame.index[0].date().isoformat()
    latest_week = frame.index[-1].date().isoformat()
    driver_fingerprints = {}
    for driver in drivers:
        raw = _canonical_history_bytes(frame, [driver])
        driver_fingerprints[driver] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "sample_start": first_week,
            "sample_end": latest_week,
            "sample_count": len(frame),
        }

    return {
        "version": INPUT_HISTORY_FINGERPRINT_VERSION,
        "scope": INPUT_HISTORY_SCOPE,
        "canonicalization": INPUT_HISTORY_CANONICALIZATION,
        "matrix_sha256": hashlib.sha256(
            _canonical_history_bytes(frame, drivers)
        ).hexdigest(),
        "drivers": driver_fingerprints,
        "raw_provider_payloads_archived": False,
        "public_full_source_history_included": False,
        "purpose": (
            "Bind the release to the exact same-run weekly input history while "
            "avoiding redistribution of complete provider-derived histories."
        ),
    }


def build_bundle(
    weekly_clean: pd.DataFrame,
    source_provenance: dict[str, dict[str, object]],
    score_json: dict[str, Any],
    *,
    generated_at: datetime | None = None,
    git_sha: str | None = None,
    lock_sha256: str | None = None,
) -> dict[str, Any]:
    """Create a reproduction bundle and prove it matches the published score."""
    drivers = list(score_v2.WEIGHTS)
    missing = [driver for driver in drivers if driver not in weekly_clean.columns]
    if missing:
        raise RuntimeError(f"Weekly levels missing required drivers: {missing}")

    weekly_clean = weekly_clean[drivers].dropna().sort_index()
    if weekly_clean.empty or weekly_clean.index.has_duplicates:
        raise RuntimeError(
            "Weekly levels must contain unique complete observations"
        )

    mu = weekly_clean.mean()
    sd = weekly_clean.std()
    z_unclipped = (weekly_clean - mu) / sd
    z = z_unclipped.clip(lower=-score_v2.ZSCORE_CLIP, upper=score_v2.ZSCORE_CLIP)
    score = score_v2.compute_score(z, score_v2.WEIGHTS, _NullLogger())

    latest_date = weekly_clean.index[-1].date().isoformat()
    metadata = score_json["metadata"]
    if metadata.get("latest_date") != latest_date:
        raise RuntimeError(
            f"Score JSON latest date {metadata.get('latest_date')} does not match "
            f"recomputed week {latest_date}"
        )

    published_week = next(
        (row for row in reversed(score_json["weeks"]) if row.get("date") == latest_date),
        None,
    )
    if published_week is None:
        raise RuntimeError(f"Score JSON has no row for {latest_date}")

    components: dict[str, Any] = {}
    reproduced_score = 0.0
    for driver in drivers:
        raw_level = float(weekly_clean[driver].iloc[-1])
        mean = _moment(mu[driver])
        sample_sd = _moment(sd[driver])
        raw_z = _moment(z_unclipped[driver].iloc[-1])
        clipped_z = _moment(z[driver].iloc[-1])
        weight = float(score_v2.WEIGHTS[driver])
        contribution = clipped_z * weight
        reproduced_score += contribution

        published_z = float(published_week[driver])
        if not np.isclose(clipped_z, published_z, atol=TOLERANCE, rtol=0):
            raise RuntimeError(
                f"{driver} recomputed z {clipped_z} does not match published {published_z}"
            )

        source = source_provenance.get(driver)
        if not source:
            raise RuntimeError(f"Missing source provenance for {driver}")

        components[driver] = {
            "weekly_level": raw_level,
            "source_observation_date": source.get("observation_date"),
            "source_provider": source.get("provider"),
            "source_series": source.get("series"),
            "source_url": source.get("source_url"),
            "forward_fill_possible": True,
            "normalization": {
                "sample_start": weekly_clean.index[0].date().isoformat(),
                "sample_end": latest_date,
                "sample_count": int(weekly_clean[driver].count()),
                "mean": mean,
                "sample_std_ddof_1": sample_sd,
            },
            "z_unclipped": raw_z,
            "z_clipped": clipped_z,
            "clip_limit": float(score_v2.ZSCORE_CLIP),
            "weight": weight,
            "contribution": contribution,
        }

    published_score = float(metadata["latest_score"])
    direct_score = float(score.iloc[-1])
    for candidate, label in (
        (reproduced_score, "bundle sum"),
        (direct_score, "pipeline recomputation"),
    ):
        if not np.isclose(candidate, published_score, atol=TOLERANCE, rtol=0):
            raise RuntimeError(
                f"{label} {candidate} does not match published score {published_score}"
            )

    regime = score_v2.label_regime(reproduced_score)
    if regime != metadata.get("latest_regime"):
        raise RuntimeError(
            f"Reproduced regime {regime!r} does not match published "
            f"{metadata.get('latest_regime')!r}"
        )

    generated_at = generated_at or datetime.now(timezone.utc)
    return {
        "bundle_version": BUNDLE_VERSION,
        "methodology_version": METHOD_VERSION,
        "score_week": latest_date,
        "bundle_generated_at_utc": generated_at.isoformat(),
        "pipeline_git_sha": git_sha,
        "requirements_lock_sha256": lock_sha256,
        "calculation": {
            "input_frequency": "weekly Friday-ended levels",
            "production_start_date": score_v2.START_DATE,
            "normalization": "full available complete weekly sample",
            "standard_deviation": "sample standard deviation (ddof=1)",
            "zscore_clip": float(score_v2.ZSCORE_CLIP),
            "weights": {k: float(v) for k, v in score_v2.WEIGHTS.items()},
            "score_formula": "sum(component_z_clipped * weight)",
            "regime_bands": [
                {"low": None if not np.isfinite(low) else float(low),
                 "high": None if not np.isfinite(high) else float(high),
                 "label": label}
                for low, high, label in score_v2.REGIME_BANDS
            ],
        },
        "source_provenance_version": score_json["metadata"].get(
            "source_provenance_version"
        ),
        "input_history_fingerprint": build_input_history_fingerprint(weekly_clean),
        "components": components,
        "published": {
            "score": published_score,
            "regime": metadata["latest_regime"],
        },
        "reproduction": {
            "score": reproduced_score,
            "regime": regime,
            "absolute_tolerance": TOLERANCE,
            "verified_equal_to_published": True,
        },
    }


def reproduce_bundle(bundle: dict[str, Any]) -> tuple[float, str]:
    """Reproduce score and regime using only frozen bundle values."""
    components = bundle["components"]
    score = sum(float(item["z_clipped"]) * float(item["weight"])
                for item in components.values())

    bands = bundle["calculation"]["regime_bands"]
    regime = "Unknown"
    for band in bands:
        low = float("-inf") if band["low"] is None else float(band["low"])
        high = float("inf") if band["high"] is None else float(band["high"])
        if low <= score < high:
            regime = band["label"]
            break
    return score, regime


def verify_bundle(bundle: dict[str, Any]) -> None:
    score, regime = reproduce_bundle(bundle)
    expected = float(bundle["published"]["score"])
    if not np.isclose(score, expected, atol=TOLERANCE, rtol=0):
        raise RuntimeError(f"Bundle reproduces {score}, expected {expected}")
    if regime != bundle["published"]["regime"]:
        raise RuntimeError(
            f"Bundle reproduces regime {regime!r}, expected "
            f"{bundle['published']['regime']!r}"
        )


class _NullLogger:
    def debug(self, *_args, **_kwargs):
        pass

    def info(self, *_args, **_kwargs):
        pass

    def warning(self, *_args, **_kwargs):
        pass

    def error(self, *_args, **_kwargs):
        pass


def _live_weekly(score_json: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    generated = datetime.now(timezone.utc)
    logger = _NullLogger()
    daily = score_v2.fetch_all_inputs(score_v2.START_DATE, logger, as_of=generated)
    provenance = daily.attrs.get("source_provenance")
    if not isinstance(provenance, dict):
        raise RuntimeError("Live fetch did not return source provenance")
    score_v2.validate_source_freshness(
        provenance, score_v2.latest_completed_friday(generated), logger
    )
    weekly = score_v2.resample_weekly(
        daily,
        logger,
        completed_friday=score_v2.latest_completed_friday(generated),
    )
    return weekly[list(score_v2.WEIGHTS)].dropna(), provenance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--score-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--weekly-levels",
        type=Path,
        help=(
            "Exact same-run weekly-level CSV from the score step, or a "
            "deterministic fixture for offline verification"
        ),
    )
    source_group.add_argument(
        "--live-refetch",
        action="store_true",
        help=(
            "Explicitly refetch provider history instead of using a same-run "
            "snapshot; prohibited in the production weekly workflow"
        ),
    )
    args = parser.parse_args()

    score_json = _load_score_json(args.score_json)
    if args.weekly_levels is not None:
        weekly = pd.read_csv(
            args.weekly_levels,
            parse_dates=["date"],
            float_precision="round_trip",
        ).set_index("date")
        provenance = score_json["metadata"].get("source_provenance", {})
    else:
        weekly, provenance = _live_weekly(score_json)

    bundle = build_bundle(
        weekly,
        provenance,
        score_json,
        git_sha=_git_sha(),
        lock_sha256=_sha256(Path("requirements.lock")),
    )
    verify_bundle(bundle)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"Verified reproducibility bundle for {bundle['score_week']}: "
        f"{bundle['published']['score']:+.12f} ({bundle['published']['regime']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
