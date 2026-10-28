#!/usr/bin/env python3
"""Provider-neutral canonical daily-frame adapter for Score migration rehearsals.

Review-only. This module performs no network access and does not alter the
production fetch path. It normalizes provider-shaped daily frames into the
canonical Score v2 driver contract so licensed-source candidates can be
parity-tested before any live migration is considered.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd

from usd_impact_score_v2 import WEIGHTS

CANONICAL_DRIVERS = tuple(WEIGHTS)


@dataclass(frozen=True)
class AdapterSpec:
    provider_id: str
    column_map: Mapping[str, str]
    date_column: str
    value_multiplier: Mapping[str, float] | None = None


def normalize_daily_frame(raw: pd.DataFrame, spec: AdapterSpec) -> pd.DataFrame:
    if not spec.provider_id:
        raise RuntimeError("provider_id is required")
    if spec.date_column not in raw.columns:
        raise RuntimeError(f"missing date column: {spec.date_column}")

    canonical_targets = set(spec.column_map.values())
    if canonical_targets != set(CANONICAL_DRIVERS):
        raise RuntimeError("adapter column map must cover exactly the canonical drivers")
    if len(set(spec.column_map)) != len(spec.column_map):
        raise RuntimeError("adapter source columns must be unique")

    missing_sources = [name for name in spec.column_map if name not in raw.columns]
    if missing_sources:
        raise RuntimeError(f"adapter source columns missing: {missing_sources}")

    frame = raw[[spec.date_column, *spec.column_map.keys()]].copy()
    frame[spec.date_column] = pd.to_datetime(frame[spec.date_column], errors="raise")
    if frame[spec.date_column].dt.tz is not None:
        frame[spec.date_column] = frame[spec.date_column].dt.tz_convert("UTC").dt.tz_localize(None)

    frame = frame.set_index(spec.date_column).sort_index()
    if frame.index.has_duplicates:
        raise RuntimeError("adapter input dates must be unique")

    frame = frame.rename(columns=dict(spec.column_map))
    frame = frame.loc[:, list(CANONICAL_DRIVERS)]

    multipliers = dict(spec.value_multiplier or {})
    unexpected_multiplier = set(multipliers) - set(CANONICAL_DRIVERS)
    if unexpected_multiplier:
        raise RuntimeError(
            f"adapter multipliers contain non-canonical drivers: {sorted(unexpected_multiplier)}"
        )

    for driver in CANONICAL_DRIVERS:
        frame[driver] = pd.to_numeric(frame[driver], errors="coerce")
        multiplier = float(multipliers.get(driver, 1.0))
        if not np.isfinite(multiplier) or multiplier == 0:
            raise RuntimeError(f"invalid multiplier for {driver}")
        frame[driver] = frame[driver] * multiplier

        finite = frame[driver].dropna().astype(float)
        if not np.isfinite(finite.to_numpy()).all():
            raise RuntimeError(f"non-finite values after normalization for {driver}")

    frame.index.name = "date"
    return frame


def canonical_frame_contract(frame: pd.DataFrame) -> dict[str, object]:
    if list(frame.columns) != list(CANONICAL_DRIVERS):
        raise RuntimeError("canonical frame column order mismatch")
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise RuntimeError("canonical frame must use DatetimeIndex")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise RuntimeError("canonical frame dates must be unique and ordered")

    return {
        "driver_count": len(frame.columns),
        "row_count": len(frame),
        "columns": list(frame.columns),
        "date_start": frame.index.min().date().isoformat() if len(frame) else None,
        "date_end": frame.index.max().date().isoformat() if len(frame) else None,
        "extra_columns": [],
    }
