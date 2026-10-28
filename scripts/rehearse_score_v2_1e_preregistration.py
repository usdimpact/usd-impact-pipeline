#!/usr/bin/env python3
"""Synthetic-only point-in-time/vintage rehearsal for Score v2.1E."""

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
    "ENERGY": 50,
    "FIN_CONDITIONS": 10,
    "FIN_STRESS": 4,
    "LIQUIDITY": 4,
    "REAL_YIELD": 4,
    "UST_2Y": 4,
    "UST_10Y": 4,
}
MIN_HISTORY = 104
CLIP = 3.5


@dataclass(frozen=True)
class Event:
    slot: str
    observation_date: date
    released_at: datetime
    value: float
    vintage_id: str


def friday_cutoff(friday: date) -> datetime:
    return datetime.combine(friday, time(23, 59, 59), tzinfo=NY)


def add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year = month_index // 12
    month = month_index % 12 + 1
    return date(year, month, min(value.day, 28))


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

    # Choose the latest reference/observation date actually available, then the
    # latest vintage of that same observation available by this historical cutoff.
    latest_obs = max(event.observation_date for event in eligible)
    same_obs = [event for event in eligible if event.observation_date == latest_obs]
    return max(same_obs, key=lambda event: event.released_at)


def _synthetic_events(start_friday: date, weeks: int) -> list[Event]:
    events: list[Event] = []

    # Monthly BLS-like PPI events. The initial release for reference month m
    # arrives on the 10th of m+1; a revision arrives on the 10th of m+2.
    first_month = date(start_friday.year - 1, 11, 1)
    for month_idx in range(48):
        ref_month = add_months(first_month, month_idx)
        initial_month = add_months(ref_month, 1)
        revision_month = add_months(ref_month, 2)
        base = 80.0 + 0.35 * month_idx + 2.0 * math.sin(month_idx / 3.0)
        events.append(
            Event(
                "ENERGY",
                ref_month,
                datetime(initial_month.year, initial_month.month, 10, 8, 30, tzinfo=NY),
                base,
                f"bls-{ref_month.isoformat()}-initial",
            )
        )
        events.append(
            Event(
                "ENERGY",
                ref_month,
                datetime(revision_month.year, revision_month.month, 10, 8, 30, tzinfo=NY),
                base + 0.25,
                f"bls-{ref_month.isoformat()}-revision1",
            )
        )

    for i in range(weeks):
        friday = start_friday + timedelta(days=7 * i)
        prior_friday = friday - timedelta(days=7)
        monday = friday - timedelta(days=4)
        wednesday = friday - timedelta(days=2)
        thursday = friday - timedelta(days=1)

        # H.10: prior business-week value released current Monday.
        events.append(
            Event(
                "USD",
                prior_friday,
                datetime.combine(monday, time(16, 15), NY),
                100.0 + 0.03 * i + 1.5 * math.sin(i / 7.0),
                f"h10-{friday.isoformat()}",
            )
        )

        # H.8: Wednesday bank-credit value released Friday 16:15.
        bank_credit = 17000.0 + 20.0 * i + 90.0 * math.sin(i / 9.0)
        events.append(
            Event(
                "FIN_CONDITIONS",
                wednesday,
                datetime.combine(friday, time(16, 15), NY),
                bank_credit,
                f"h8-{friday.isoformat()}-original",
            )
        )
        # One later correction for a probe week. It must never mutate the
        # already-selected earlier Friday vintage.
        if i == 80:
            next_friday = friday + timedelta(days=7)
            events.append(
                Event(
                    "FIN_CONDITIONS",
                    wednesday,
                    datetime.combine(next_friday, time(12, 0), NY),
                    bank_credit + 500.0,
                    f"h8-{friday.isoformat()}-later-correction",
                )
            )

        # H.4.1 Wednesday levels released Thursday.
        primary = max(0.0, 1.5 + 1.2 * math.sin(i / 5.0) + (8.0 if i % 37 == 0 else 0.0))
        total_assets = 6000000.0 * (1.0 + 0.0007 * i + 0.002 * math.sin(i / 11.0))
        events.append(
            Event(
                "FIN_STRESS",
                wednesday,
                datetime.combine(thursday, time(16, 30), NY),
                primary,
                f"h41-primary-{friday.isoformat()}",
            )
        )
        events.append(
            Event(
                "LIQUIDITY",
                wednesday,
                datetime.combine(thursday, time(16, 30), NY),
                total_assets,
                f"h41-assets-{friday.isoformat()}",
            )
        )

        # H.15: prior-day observations released Friday 16:15.
        events.append(
            Event(
                "REAL_YIELD",
                thursday,
                datetime.combine(friday, time(16, 15), NY),
                1.0 + 0.006 * i + 0.15 * math.sin(i / 8.0),
                f"h15-real-{friday.isoformat()}",
            )
        )
        events.append(
            Event(
                "UST_2Y",
                thursday,
                datetime.combine(friday, time(16, 15), NY),
                2.0 + 0.008 * i + 0.12 * math.cos(i / 6.0),
                f"h15-2y-{friday.isoformat()}",
            )
        )
        events.append(
            Event(
                "UST_10Y",
                thursday,
                datetime.combine(friday, time(16, 15), NY),
                3.0 + 0.006 * i + 0.10 * math.sin(i / 10.0),
                f"h15-10y-{friday.isoformat()}",
            )
        )

    return events


def _selected_rows(events: list[Event], start_friday: date, weeks: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for i in range(weeks):
        friday = start_friday + timedelta(days=7 * i)
        values: dict[str, float] = {}
        observations: dict[str, str] = {}
        releases: dict[str, str] = {}
        vintages: dict[str, str] = {}
        for slot in SLOTS:
            event = latest_eligible(events, slot, friday)
            if event is None:
                raise RuntimeError(f"missing eligible synthetic event for {slot} {friday}")
            values[slot] = event.value
            observations[slot] = event.observation_date.isoformat()
            releases[slot] = event.released_at.isoformat()
            vintages[slot] = event.vintage_id
        rows.append({
            "friday": friday,
            "values": values,
            "observations": observations,
            "releases": releases,
            "vintages": vintages,
        })
    return rows


def _transform(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    transformed_rows: list[dict[str, object]] = []
    for idx, row in enumerate(rows):
        values = row["values"]
        t: dict[str, float] = {
            "USD": float(values["USD"]),
            "ENERGY": math.log(float(values["ENERGY"])),
            "FIN_STRESS": math.log1p(float(values["FIN_STRESS"])),
            "REAL_YIELD": float(values["REAL_YIELD"]),
            "UST_2Y": float(values["UST_2Y"]),
            "UST_10Y": float(values["UST_10Y"]),
        }
        if idx >= 13:
            current_credit = float(values["FIN_CONDITIONS"])
            prior_credit = float(rows[idx - 13]["values"]["FIN_CONDITIONS"])
            current_assets = float(values["LIQUIDITY"])
            prior_assets = float(rows[idx - 13]["values"]["LIQUIDITY"])
            t["FIN_CONDITIONS"] = -math.log(current_credit / prior_credit)
            t["LIQUIDITY"] = math.log(current_assets / prior_assets)
        transformed_rows.append({"friday": row["friday"], "transformed": t})
    return transformed_rows


def _pit_scores(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    complete = [row for row in rows if set(row["transformed"]) == set(SLOTS)]
    scores: list[dict[str, object]] = []
    for idx in range(MIN_HISTORY, len(complete)):
        history = complete[:idx]
        current = complete[idx]
        z: dict[str, float] = {}
        for slot in SLOTS:
            hist_values = [float(item["transformed"][slot]) for item in history]
            sd = stdev(hist_values)
            if sd == 0:
                raise RuntimeError(f"zero synthetic standard deviation for {slot}")
            raw = (float(current["transformed"][slot]) - mean(hist_values)) / sd
            z[slot] = max(-CLIP, min(CLIP, raw))
        scores.append({
            "friday": current["friday"],
            "history_end": history[-1]["friday"],
            "history_count": len(history),
            "score": sum(z[slot] * WEIGHTS[slot] for slot in SLOTS),
        })
    return scores


def rehearse() -> dict[str, object]:
    start = date(2013, 1, 4)
    weeks = 150
    events = _synthetic_events(start, weeks)
    rows = _selected_rows(events, start, weeks)
    transformed = _transform(rows)
    scores = _pit_scores(transformed)

    all_release_times_within_cutoff = all(
        datetime.fromisoformat(released) <= friday_cutoff(row["friday"])
        for row in rows
        for released in row["releases"].values()
    )

    # Find a Friday between an initial BLS release and its later revision.
    energy_probe = next(
        row for row in rows
        if row["vintages"]["ENERGY"].endswith("-initial")
        and row["friday"] >= date(2013, 3, 15)
    )
    energy_initial_vintage_used = energy_probe["vintages"]["ENERGY"].endswith("-initial")

    # H.8 probe week 80 must retain its original release even though a correction
    # is published one week later.
    h8_probe = rows[80]
    h8_original_vintage_preserved = h8_probe["vintages"]["FIN_CONDITIONS"].endswith("-original")

    current_week_excluded = all(
        item["history_end"] < item["friday"] for item in scores
    )

    if not all_release_times_within_cutoff:
        raise RuntimeError("post-cutoff synthetic release entered candidate")
    if not energy_initial_vintage_used:
        raise RuntimeError("later BLS revision leaked backward into an earlier Friday")
    if not h8_original_vintage_preserved:
        raise RuntimeError("later H.8 correction rewrote an earlier Friday")
    if not current_week_excluded:
        raise RuntimeError("current week entered its own normalization history")
    if not scores:
        raise RuntimeError("synthetic rehearsal produced no point-in-time scores")

    return {
        "status": "passed",
        "synthetic_only": True,
        "real_data_accessed": False,
        "weeks_generated": weeks,
        "pit_scores": len(scores),
        "all_release_times_within_cutoff": all_release_times_within_cutoff,
        "bls_initial_vintage_preserved_before_revision": energy_initial_vintage_used,
        "h8_original_vintage_preserved_before_correction": h8_original_vintage_preserved,
        "current_week_excluded_from_own_normalization": current_week_excluded,
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
