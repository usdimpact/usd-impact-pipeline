#!/usr/bin/env python3
"""Validate one generated Weekly USD Impact Score release before publication."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime
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
