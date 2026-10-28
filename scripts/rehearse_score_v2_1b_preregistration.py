#!/usr/bin/env python3
"""Synthetic-only rehearsal for Score v2.1B preregistered timing and PIT normalization."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from statistics import mean, stdev
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
SLOTS = (
    "USD",
    "ENERGY",
    "FIN_CONDITIONS",
    "FIN_STRESS",
    "LIQUIDITY",
    "REAL_YIELD",
    "UST_2Y",
    "UST_10Y",
)
WEIGHTS = {
    "USD": 0.125,
    "ENERGY": -0.125,
    "FIN_CONDITIONS": 0.125,
    "FIN_STRESS": 0.125,
    "LIQUIDITY": -0.125,
    "REAL_YIELD": 0.125,
    "UST_2Y": 0.125,
    "UST_10Y": 0.125,
}
MAX_AGE = {
    "USD": 10,
    "ENERGY": 5,
    "FIN_CONDITIONS": 10,
    "FIN_STRESS": 10,
    "LIQUIDITY": 4,
    "REAL_YIELD": 4,
    "UST_2Y": 4,
    "UST_10Y": 4,
}
TRANSFORMS = {
    "USD": "level",
    "ENERGY": "natural_log_level",
    "FIN_CONDITIONS": "level",
    "FIN_STRESS": "level",
    "LIQUIDITY": "log_change_13_weeks",
    "REAL_YIELD": "level",
    "UST_2Y": "level",
    "UST_10Y": "level",
}
MIN_HISTORY = 104
CLIP = 3.5


@dataclass(frozen=True)
class Event:
    slot: str
    observation_date: date
    released_at: datetime
    value: float


def friday_cutoff(friday: date) -> datetime:
    return datetime.combine(friday, time(23, 59, 59), tzinfo=NY)


def latest_eligible(events: list[Event], slot: str, friday: date) -> Event | None:
    cutoff = friday_cutoff(friday)
    eligible = [
        event
        for event in events
        if event.slot == slot
        and event.released_at <= cutoff
        and event.observation_date <= friday
        and (friday - event.observation_date).days <= MAX_AGE[slot]
    ]
    if not eligible:
        return None
    return max(eligible, key=lambda item: (item.observation_date, item.released_at))


def _synthetic_events(start_friday: date, weeks: int) -> list[Event]:
    events: list[Event] = []
    for i in range(weeks):
        friday = start_friday + timedelta(days=7 * i)
        prior_friday = friday - timedelta(days=7)
        monday = friday - timedelta(days=4)
        wednesday = friday - timedelta(days=2)
        thursday = friday - timedelta(days=1)

        # H.10: prior business week's Friday released current Monday.
        events.append(Event("USD", prior_friday, datetime.combine(monday, time(16, 15), NY), 100.0 + i * 0.05))

        # Synthetic EIA-like daily spot observation released next day.
        events.append(Event("ENERGY", wednesday, datetime.combine(thursday, time(13, 0), NY), 50.0 + i * 0.12))

        # NFCI and STLFSI: prior Friday, released during current week.
        events.append(Event("FIN_CONDITIONS", prior_friday, datetime.combine(wednesday, time(8, 30), NY), -0.5 + i * 0.002))
        events.append(Event("FIN_STRESS", prior_friday, datetime.combine(wednesday, time(10, 0), NY), -0.4 + i * 0.003))

        # Add an intentionally future-released same-Friday NFCI observation.
        future_wednesday = friday + timedelta(days=5)
        events.append(Event("FIN_CONDITIONS", friday, datetime.combine(future_wednesday, time(8, 30), NY), 9999.0))

        # WALCL: Wednesday level released Thursday.
        events.append(Event("LIQUIDITY", wednesday, datetime.combine(thursday, time(16, 30), NY), 6000000.0 * (1.0 + 0.0008 * i)))

        # H.15-like prior-day rates released Friday 16:15.
        events.append(Event("REAL_YIELD", thursday, datetime.combine(friday, time(16, 15), NY), 1.0 + i * 0.004))
        events.append(Event("UST_2Y", thursday, datetime.combine(friday, time(16, 15), NY), 2.0 + i * 0.006))
        events.append(Event("UST_10Y", thursday, datetime.combine(friday, time(16, 15), NY), 3.0 + i * 0.005))

    return events


def _build_selected(events: list[Event], start_friday: date, weeks: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for i in range(weeks):
        friday = start_friday + timedelta(days=7 * i)
        values: dict[str, float] = {}
        observations: dict[str, str] = {}
        releases: dict[str, str] = {}
        for slot in SLOTS:
            event = latest_eligible(events, slot, friday)
            if event is None:
                raise RuntimeError(f"missing synthetic eligible event for {slot} {friday}")
            values[slot] = event.value
            observations[slot] = event.observation_date.isoformat()
            releases[slot] = event.released_at.isoformat()
        rows.append({
            "friday": friday,
            "values": values,
            "observations": observations,
            "releases": releases,
        })
    return rows


def _transform(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    liquidity_values = [float(row["values"]["LIQUIDITY"]) for row in rows]
    for idx, row in enumerate(rows):
        transformed: dict[str, float] = {}
        values = row["values"]
        transformed["USD"] = float(values["USD"])
        transformed["ENERGY"] = math.log(float(values["ENERGY"]))
        transformed["FIN_CONDITIONS"] = float(values["FIN_CONDITIONS"])
        transformed["FIN_STRESS"] = float(values["FIN_STRESS"])
        if idx >= 13:
            transformed["LIQUIDITY"] = math.log(liquidity_values[idx] / liquidity_values[idx - 13])
        transformed["REAL_YIELD"] = float(values["REAL_YIELD"])
        transformed["UST_2Y"] = float(values["UST_2Y"])
        transformed["UST_10Y"] = float(values["UST_10Y"])
        output.append({"friday": row["friday"], "transformed": transformed})
    return output


def _pit_scores(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    complete = [row for row in rows if set(row["transformed"]) == set(SLOTS)]
    scores: list[dict[str, object]] = []
    for idx in range(MIN_HISTORY, len(complete)):
        history = complete[:idx]
        current = complete[idx]
        z: dict[str, float] = {}
        for slot in SLOTS:
            hist_values = [float(item["transformed"][slot]) for item in history]
            mu = mean(hist_values)
            sd = stdev(hist_values)
            if sd == 0:
                raise RuntimeError(f"zero synthetic standard deviation for {slot}")
            raw = (float(current["transformed"][slot]) - mu) / sd
            z[slot] = max(-CLIP, min(CLIP, raw))
        score = sum(z[slot] * WEIGHTS[slot] for slot in SLOTS)
        scores.append({
            "friday": current["friday"],
            "history_end": history[-1]["friday"],
            "history_count": len(history),
            "score": score,
            "z": z,
        })
    return scores


def rehearse() -> dict[str, object]:
    start = date(2013, 1, 4)
    weeks = 130
    events = _synthetic_events(start, weeks)
    selected = _build_selected(events, start, weeks)
    transformed = _transform(selected)
    scores = _pit_scores(transformed)

    # Prove the intentionally future-released current-Friday NFCI value is excluded.
    probe_idx = 120
    probe = selected[probe_idx]
    friday = probe["friday"]
    expected_prior = friday - timedelta(days=7)
    nfci_future_excluded = probe["observations"]["FIN_CONDITIONS"] == expected_prior.isoformat()
    current_week_excluded_from_history = all(
        item["history_end"] < item["friday"] for item in scores
    )
    all_release_times_within_cutoff = all(
        datetime.fromisoformat(released) <= friday_cutoff(row["friday"])
        for row in selected
        for released in row["releases"].values()
    )

    if not nfci_future_excluded:
        raise RuntimeError("future-released NFCI value entered synthetic Friday score")
    if not current_week_excluded_from_history:
        raise RuntimeError("current week entered its own PIT normalization history")
    if not all_release_times_within_cutoff:
        raise RuntimeError("synthetic value released after cutoff entered candidate")
    if not scores:
        raise RuntimeError("synthetic rehearsal produced no PIT scores")

    return {
        "status": "passed",
        "synthetic_only": True,
        "real_data_accessed": False,
        "weeks_generated": weeks,
        "complete_transformed_weeks": sum(
            1 for row in transformed if set(row["transformed"]) == set(SLOTS)
        ),
        "pit_scores": len(scores),
        "future_released_nfci_excluded": nfci_future_excluded,
        "all_release_times_within_cutoff": all_release_times_within_cutoff,
        "current_week_excluded_from_own_normalization": current_week_excluded_from_history,
        "minimum_prior_complete_weeks": MIN_HISTORY,
        "first_score_history_count": scores[0]["history_count"],
        "first_score_history_end": scores[0]["history_end"].isoformat(),
        "first_score_week": scores[0]["friday"].isoformat(),
        "production_authorized": False,
    }


def main() -> int:
    print(json.dumps(rehearse(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
