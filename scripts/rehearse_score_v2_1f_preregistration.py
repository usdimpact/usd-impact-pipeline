#!/usr/bin/env python3
"""Synthetic-only point-in-time/vintage rehearsal for Score v2.1F."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from statistics import mean, stdev
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
SLOTS = ("USD", "ENERGY", "FIN_CONDITIONS", "FIN_STRESS", "LIQUIDITY")
WEIGHTS = {
    "USD": 0.2,
    "ENERGY": -0.2,
    "FIN_CONDITIONS": 0.2,
    "FIN_STRESS": 0.2,
    "LIQUIDITY": -0.2,
}
MAX_AGE = {
    "USD": 10,
    "FIN_CONDITIONS": 10,
    "FIN_STRESS": 4,
    "LIQUIDITY": 4,
}
ENERGY_MAX_RELEASE_AGE = 45
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
    eligible: list[Event] = []
    for event in events:
        if event.slot != slot or event.released_at > cutoff or event.observation_date > friday:
            continue
        if slot == "ENERGY":
            if (friday - event.released_at.date()).days > ENERGY_MAX_RELEASE_AGE:
                continue
        elif (friday - event.observation_date).days > MAX_AGE[slot]:
            continue
        eligible.append(event)
    if not eligible:
        return None
    latest_obs = max(event.observation_date for event in eligible)
    same_obs = [event for event in eligible if event.observation_date == latest_obs]
    return max(same_obs, key=lambda event: event.released_at)

def _synthetic_events(start_friday: date, weeks: int) -> list[Event]:
    events: list[Event] = []
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

        events.append(
            Event(
                "USD",
                prior_friday,
                datetime.combine(monday, time(16, 15), NY),
                100.0 + 0.03 * i + 1.5 * math.sin(i / 7.0),
                f"h10-{friday.isoformat()}",
            )
        )

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
    return events

def _selected_rows(events: list[Event], start_friday: date, weeks: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for i in range(weeks):
        friday = start_friday + timedelta(days=7 * i)
        values: dict[str, float] = {}
        releases: dict[str, str] = {}
        vintages: dict[str, str] = {}
        for slot in SLOTS:
            event = latest_eligible(events, slot, friday)
            if event is None:
                raise RuntimeError(f"missing eligible synthetic event for {slot} {friday}")
            values[slot] = event.value
            releases[slot] = event.released_at.isoformat()
            vintages[slot] = event.vintage_id
        rows.append(
            {
                "friday": friday,
                "values": values,
                "releases": releases,
                "vintages": vintages,
            }
        )
    return rows

def _transform(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    transformed_rows: list[dict[str, object]] = []
    for idx, row in enumerate(rows):
        values = row["values"]
        transformed: dict[str, float] = {
            "USD": float(values["USD"]),
            "ENERGY": math.log(float(values["ENERGY"])),
            "FIN_STRESS": math.log1p(float(values["FIN_STRESS"])),
        }
        if idx >= 13:
            current_credit = float(values["FIN_CONDITIONS"])
            prior_credit = float(rows[idx - 13]["values"]["FIN_CONDITIONS"])
            current_assets = float(values["LIQUIDITY"])
            prior_assets = float(rows[idx - 13]["values"]["LIQUIDITY"])
            transformed["FIN_CONDITIONS"] = -math.log(current_credit / prior_credit)
            transformed["LIQUIDITY"] = math.log(current_assets / prior_assets)
        transformed_rows.append({"friday": row["friday"], "transformed": transformed})
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
        scores.append(
            {
                "friday": current["friday"],
                "history_end": history[-1]["friday"],
                "history_count": len(history),
                "score": sum(z[slot] * WEIGHTS[slot] for slot in SLOTS),
            }
        )
    return scores

def rehearse() -> dict[str, object]:
    start = date(2013, 1, 11)
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

    energy_probe = next(
        row
        for row in rows
        if row["vintages"]["ENERGY"].endswith("-initial")
        and row["friday"] >= date(2013, 3, 15)
    )
    energy_initial_vintage_used = energy_probe["vintages"]["ENERGY"].endswith("-initial")
    h8_probe = rows[80]
    h8_original_vintage_preserved = h8_probe["vintages"]["FIN_CONDITIONS"].endswith("-original")
    current_week_excluded = all(item["history_end"] < item["friday"] for item in scores)

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
        "slot_count": len(SLOTS),
        "h15_present": False,
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
        "absolute_weight_sum": sum(abs(value) for value in WEIGHTS.values()),
        "live_vintage_preflight_authorized": False,
        "full_candidate_research_authorized": False,
        "production_authorized": False,
    }

def main() -> int:
    print(json.dumps(rehearse(), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
