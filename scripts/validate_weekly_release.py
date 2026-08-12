#!/usr/bin/env python3
"""Validate one generated Weekly USD Impact Score release before publication."""

from __future__ import annotations

import argparse
import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

EXPECTED_DRIVERS = {
    "DXY", "WTI", "SPX", "VIX", "BTC", "GOLD", "UST_2Y", "UST_10Y"
}
EXPECTED_REGIMES = {
    "Strong dollar regime",
    "Firm dollar regime",
    "Neutral / transitional",
    "Soft dollar regime",
    "Weak dollar regime",
}
SPANISH_MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
PROVENANCE_REQUIRED_FROM = date(2026, 8, 14)
SOURCE_PROVENANCE_VERSION = 1
SOURCE_CONTRACT = {
    "DXY": {
        "provider": "Yahoo Finance via yfinance",
        "provider_code": "yahoo",
        "series": "DX-Y.NYB",
        "source_url": "https://finance.yahoo.com/quote/DX-Y.NYB/history",
        "max_age_days": 3,
    },
    "WTI": {
        "provider": "Yahoo Finance via yfinance",
        "provider_code": "yahoo",
        "series": "CL=F",
        "source_url": "https://finance.yahoo.com/quote/CL%3DF/history",
        "max_age_days": 3,
    },
    "SPX": {
        "provider": "Yahoo Finance via yfinance",
        "provider_code": "yahoo",
        "series": "^GSPC",
        "source_url": "https://finance.yahoo.com/quote/%5EGSPC/history",
        "max_age_days": 3,
    },
    "VIX": {
        "provider": "Yahoo Finance via yfinance",
        "provider_code": "yahoo",
        "series": "^VIX",
        "source_url": "https://finance.yahoo.com/quote/%5EVIX/history",
        "max_age_days": 3,
    },
    "BTC": {
        "provider": "Yahoo Finance via yfinance",
        "provider_code": "yahoo",
        "series": "BTC-USD",
        "source_url": "https://finance.yahoo.com/quote/BTC-USD/history",
        "max_age_days": 2,
    },
    "GOLD": {
        "provider": "Yahoo Finance via yfinance",
        "provider_code": "yahoo",
        "series": "GC=F",
        "source_url": "https://finance.yahoo.com/quote/GC%3DF/history",
        "max_age_days": 3,
    },
    "UST_2Y": {
        "provider": "Federal Reserve Bank of St. Louis (FRED)",
        "provider_code": "fred",
        "series": "DGS2",
        "source_url": "https://fred.stlouisfed.org/series/DGS2",
        "max_age_days": 4,
    },
    "UST_10Y": {
        "provider": "Federal Reserve Bank of St. Louis (FRED)",
        "provider_code": "fred",
        "series": "DGS10",
        "source_url": "https://fred.stlouisfed.org/series/DGS10",
        "max_age_days": 4,
    },
}


def load_json(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Missing or empty JSON file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def require_file(path: Path) -> str:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Missing or empty release file: {path}")
    return path.read_text(encoding="utf-8")


def finite_number(value: object, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def localized_dates(week: str) -> tuple[str, str]:
    date = datetime.strptime(week, "%Y-%m-%d")
    english = date.strftime("%B %d, %Y").replace(" 0", " ")
    spanish = f"{date.day} de {SPANISH_MONTHS[date.month - 1]} de {date.year}"
    return english, spanish


def latest_completed_friday(value: datetime) -> date:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    utc_date = value.astimezone(timezone.utc).date()
    return utc_date - timedelta(days=(utc_date.weekday() - 4) % 7)


def validate_source_provenance(metadata: dict, bridge: dict, week: str) -> None:
    """Validate the provider identity and raw observation date for each driver."""
    week_date = datetime.strptime(week, "%Y-%m-%d").date()
    score_provenance = metadata.get("source_provenance")
    bridge_provenance = bridge.get("source_provenance")
    required = week_date >= PROVENANCE_REQUIRED_FROM

    if score_provenance is None and bridge_provenance is None:
        if required:
            raise ValueError(
                f"Source provenance is required for releases from "
                f"{PROVENANCE_REQUIRED_FROM.isoformat()}"
            )
        return
    if not isinstance(score_provenance, dict) or not isinstance(
        bridge_provenance, dict
    ):
        raise ValueError("Source provenance must exist in both score and bridge JSON")
    if score_provenance != bridge_provenance:
        raise ValueError("Bridge source provenance differs from score metadata")
    if metadata.get("source_provenance_version") != SOURCE_PROVENANCE_VERSION:
        raise ValueError("Unexpected score source provenance version")
    if bridge.get("source_provenance_version") != SOURCE_PROVENANCE_VERSION:
        raise ValueError("Unexpected bridge source provenance version")

    if set(score_provenance) != EXPECTED_DRIVERS:
        raise ValueError("Source provenance must contain exactly the eight drivers")

    for driver, contract in SOURCE_CONTRACT.items():
        item = score_provenance[driver]
        if not isinstance(item, dict):
            raise ValueError(f"Source provenance for {driver} must be an object")
        expected_fields = {
            "driver": driver,
            "provider": contract["provider"],
            "provider_code": contract["provider_code"],
            "series": contract["series"],
            "source_url": contract["source_url"],
            "score_week": week,
            "max_age_days": contract["max_age_days"],
            "status": "fresh",
        }
        for field, expected in expected_fields.items():
            if item.get(field) != expected:
                raise ValueError(
                    f"Source provenance {driver}.{field} does not match "
                    f"the canonical source contract"
                )
        if required and item.get("retrieval_mode") != "live":
            raise ValueError(
                f"Source provenance {driver}.retrieval_mode must be live"
            )

        observation_raw = item.get("observation_date")
        try:
            observation_date = datetime.strptime(
                str(observation_raw), "%Y-%m-%d"
            ).date()
        except ValueError as error:
            raise ValueError(
                f"Source provenance {driver}.observation_date is invalid"
            ) from error
        age_days = (week_date - observation_date).days
        if age_days < 0:
            raise ValueError(
                f"Source provenance {driver} is dated after the score week"
            )
        if item.get("age_days") != age_days:
            raise ValueError(f"Source provenance {driver}.age_days is inconsistent")
        if age_days > contract["max_age_days"]:
            raise ValueError(
                f"Source provenance {driver} is stale by {age_days} days"
            )


def validate(root: Path) -> str:
    score_path = root / "public/data/usd_impact_score_v2.json"
    bridge_path = root / "public/data/weekly_input_latest.json"
    score_payload = load_json(score_path)
    bridge = load_json(bridge_path)

    metadata = score_payload.get("metadata") or {}
    weeks = score_payload.get("weeks") or []
    if len(weeks) < 5:
        raise ValueError("Score history must contain at least five weekly observations")

    latest = weeks[-1]
    week = str(metadata.get("latest_date", ""))
    if not week or latest.get("date") != week:
        raise ValueError("Score metadata latest_date does not match the last weekly observation")
    if bridge.get("week_ending") != week:
        raise ValueError("Bridge week_ending does not match score metadata latest_date")

    generated_at_raw = str(metadata.get("generated_at_utc", ""))
    try:
        generated_at = datetime.fromisoformat(generated_at_raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Score metadata generated_at_utc is not valid ISO-8601") from error
    latest_allowed_week = latest_completed_friday(generated_at)
    if datetime.strptime(week, "%Y-%m-%d").date() != latest_allowed_week:
        raise ValueError(
            f"Score metadata latest_date {week} does not match the latest "
            f"completed Friday {latest_allowed_week}"
        )

    english_date, spanish_date = localized_dates(week)
    score = finite_number(metadata.get("latest_score"), "metadata.latest_score")
    latest_score = finite_number(latest.get("score"), "weeks[-1].score")
    bridge_score = finite_number(bridge.get("score"), "bridge.score")
    if abs(score - latest_score) > 1e-9 or abs(score - bridge_score) > 1e-9:
        raise ValueError("Latest score differs across score metadata, weekly history, and bridge data")

    regime = metadata.get("latest_regime")
    if regime not in EXPECTED_REGIMES:
        raise ValueError(f"Unexpected latest regime: {regime}")
    if latest.get("regime") != regime or bridge.get("regime") != regime:
        raise ValueError("Latest regime differs across score history and bridge data")

    validate_source_provenance(metadata, bridge, week)

    drivers = bridge.get("drivers") or []
    names = {item.get("name") for item in drivers}
    if len(drivers) != 8 or names != EXPECTED_DRIVERS:
        raise ValueError("Bridge data must contain exactly the eight canonical score drivers")
    for item in drivers:
        finite_number(item.get("z"), f"driver {item.get('name')} z")
        finite_number(item.get("weight"), f"driver {item.get('name')} weight")
        contribution = finite_number(
            item.get("contribution"), f"driver {item.get('name')} contribution"
        )
        expected = float(item["z"]) * float(item["weight"])
        if abs(contribution - expected) > 1e-9:
            raise ValueError(f"Driver contribution mismatch for {item.get('name')}")

    generation = bridge.get("generation") or {}
    if generation.get("mode") != "deterministic":
        raise ValueError("Weekly commentary generation mode must remain deterministic")
    if generation.get("external_model_used") is not False:
        raise ValueError("Weekly commentary must not claim use of an external model")
    if generation.get("external_event_claims_added") is not False:
        raise ValueError("Weekly commentary must not add external event claims")

    required_text = {
        root / "commentary/latest.md": [english_date, "Automated Regime Commentary"],
        root / "commentary/latest_en.md": [english_date, "Automated Regime Commentary"],
        root / "commentary/latest_es.md": [spanish_date, "Comentario Automático de Régimen"],
        root / "public/en/index.html": [english_date, "Automated Regime Commentary"],
        root / "public/es/index.html": [spanish_date, "Comentario Automático de Régimen"],
        root / f"commentary/archive/{week}_en.md": [english_date, "Automated Regime Commentary"],
        root / f"commentary/archive/{week}_es.md": [spanish_date, "Comentario Automático de Régimen"],
        root / f"public/archive/{week}/en.html": [english_date, "Automated Regime Commentary"],
        root / f"public/archive/{week}/es.html": [spanish_date, "Comentario Automático de Régimen"],
    }
    for path, needles in required_text.items():
        text = require_file(path)
        for needle in needles:
            if needle not in text:
                raise ValueError(f"{path} does not contain required release marker: {needle}")

    if require_file(root / "commentary/latest.md") != require_file(
        root / "commentary/latest_en.md"
    ):
        raise ValueError("commentary/latest.md must match the canonical English commentary")

    archived_score = load_json(root / f"public/archive/{week}/score.json")
    archived_bridge = load_json(root / f"public/archive/{week}/weekly_input.json")
    if (archived_score.get("metadata") or {}).get("latest_date") != week:
        raise ValueError("Archived score JSON does not match the current release week")
    if archived_bridge != bridge:
        raise ValueError("Archived weekly bridge JSON differs from the latest bridge JSON")

    return week


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    week = validate(args.root.resolve())
    print(f"Weekly USD Impact release validation passed for {week}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
