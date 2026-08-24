#!/usr/bin/env python3
"""Validate one generated Weekly USD Impact Score release before publication."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
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
EXPECTED_WEIGHTS = {
    "DXY": 0.125,
    "WTI": -0.125,
    "SPX": -0.125,
    "VIX": 0.125,
    "BTC": -0.125,
    "GOLD": -0.125,
    "UST_2Y": 0.125,
    "UST_10Y": 0.125,
}
EXPECTED_REGIME_BANDS = [
    {"low": 1.0, "high": None, "label": "Strong dollar regime"},
    {"low": 0.3, "high": 1.0, "label": "Firm dollar regime"},
    {"low": -0.3, "high": 0.3, "label": "Neutral / transitional"},
    {"low": -1.0, "high": -0.3, "label": "Soft dollar regime"},
    {"low": None, "high": -1.0, "label": "Weak dollar regime"},
]
SPANISH_MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
PROVENANCE_REQUIRED_FROM = date(2026, 8, 14)
# Releases through 2026-08-21 are intentionally retained as legacy artifacts.
# The first newly generated weekly release after the bundle implementation is
# 2026-08-28; from that release forward the archived reproduction artifact is a
# mandatory part of the publication contract.
REPRO_BUNDLE_REQUIRED_FROM = date(2026, 8, 28)
SOURCE_PROVENANCE_VERSION = 1
REPRO_BUNDLE_VERSION = 1
REPRO_METHODOLOGY_VERSION = "usd_impact_score_v2"
REPRO_TOLERANCE = 1e-9
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
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
    parsed = datetime.strptime(week, "%Y-%m-%d")
    english = parsed.strftime("%B %d, %Y").replace(" 0", " ")
    spanish = f"{parsed.day} de {SPANISH_MONTHS[parsed.month - 1]} de {parsed.year}"
    return english, spanish


def latest_completed_friday(value: datetime) -> date:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    utc_date = value.astimezone(timezone.utc).date()
    return utc_date - timedelta(days=(utc_date.weekday() - 4) % 7)


def reproduction_bundle_required(week: str) -> bool:
    return datetime.strptime(week, "%Y-%m-%d").date() >= REPRO_BUNDLE_REQUIRED_FROM


def canonical_regime(score: float) -> str:
    if score >= 1.0:
        return "Strong dollar regime"
    if score >= 0.3:
        return "Firm dollar regime"
    if score >= -0.3:
        return "Neutral / transitional"
    if score >= -1.0:
        return "Soft dollar regime"
    return "Weak dollar regime"


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


def validate_reproduction_bundle(root: Path, metadata: dict, week: str) -> None:
    """Independently reproduce a frozen score bundle and its archived copy.

    The validation intentionally consumes only fields frozen inside the bundle,
    plus canonical methodology constants and the checked-in dependency lock.
    It does not download Yahoo/FRED history and therefore proves that a future
    third party can reproduce the as-published score from the release artifact.
    """
    latest_path = root / "public/data/score_repro_bundle_latest.json"
    archive_path = root / f"public/archive/{week}/repro_bundle.json"
    bundle = load_json(latest_path)
    archived = load_json(archive_path)
    if archived != bundle:
        raise ValueError("Archived reproduction bundle differs from latest bundle")

    if bundle.get("bundle_version") != REPRO_BUNDLE_VERSION:
        raise ValueError("Unexpected reproduction bundle version")
    if bundle.get("methodology_version") != REPRO_METHODOLOGY_VERSION:
        raise ValueError("Unexpected reproduction methodology version")
    if bundle.get("score_week") != week:
        raise ValueError("Reproduction bundle score_week does not match release week")

    generated_at_raw = str(bundle.get("bundle_generated_at_utc", ""))
    try:
        datetime.fromisoformat(generated_at_raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Reproduction bundle timestamp is invalid") from error

    pipeline_sha = str(bundle.get("pipeline_git_sha", ""))
    if not SHA40_RE.fullmatch(pipeline_sha):
        raise ValueError("Reproduction bundle pipeline_git_sha must be a 40-char SHA")

    lock_sha = str(bundle.get("requirements_lock_sha256", ""))
    if not SHA256_RE.fullmatch(lock_sha):
        raise ValueError("Reproduction bundle requirements lock hash is invalid")
    lock_path = root / "requirements.lock"
    if not lock_path.is_file():
        raise ValueError("requirements.lock is missing")
    expected_lock_sha = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    if lock_sha != expected_lock_sha:
        raise ValueError("Reproduction bundle requirements lock hash does not match")

    calculation = bundle.get("calculation") or {}
    if calculation.get("input_frequency") != "weekly Friday-ended levels":
        raise ValueError("Unexpected reproduction input frequency")
    if calculation.get("production_start_date") != "2015-01-01":
        raise ValueError("Unexpected reproduction production start date")
    if calculation.get("normalization") != "full available complete weekly sample":
        raise ValueError("Unexpected reproduction normalization contract")
    if calculation.get("standard_deviation") != "sample standard deviation (ddof=1)":
        raise ValueError("Unexpected reproduction standard deviation contract")
    if finite_number(calculation.get("zscore_clip"), "bundle zscore_clip") != 3.5:
        raise ValueError("Unexpected reproduction z-score clip")
    if calculation.get("weights") != EXPECTED_WEIGHTS:
        raise ValueError("Reproduction bundle weights differ from production weights")
    if calculation.get("score_formula") != "sum(component_z_clipped * weight)":
        raise ValueError("Unexpected reproduction score formula")
    if calculation.get("regime_bands") != EXPECTED_REGIME_BANDS:
        raise ValueError("Reproduction bundle regime bands differ from production bands")

    if bundle.get("source_provenance_version") != metadata.get(
        "source_provenance_version"
    ):
        raise ValueError("Reproduction bundle provenance version is inconsistent")
    provenance = metadata.get("source_provenance") or {}
    if set(provenance) != EXPECTED_DRIVERS:
        raise ValueError("Release metadata provenance is incomplete for reproduction")

    components = bundle.get("components") or {}
    if set(components) != EXPECTED_DRIVERS:
        raise ValueError("Reproduction bundle must contain exactly eight components")

    reproduced_score = 0.0
    for driver, expected_weight in EXPECTED_WEIGHTS.items():
        component = components[driver]
        weekly_level = finite_number(
            component.get("weekly_level"), f"bundle {driver} weekly_level"
        )
        normalization = component.get("normalization") or {}
        sample_count = normalization.get("sample_count")
        if not isinstance(sample_count, int) or isinstance(sample_count, bool) or sample_count < 5:
            raise ValueError(f"Reproduction bundle {driver} sample_count is invalid")
        sample_start_raw = str(normalization.get("sample_start", ""))
        sample_end_raw = str(normalization.get("sample_end", ""))
        try:
            sample_start = datetime.strptime(sample_start_raw, "%Y-%m-%d").date()
            sample_end = datetime.strptime(sample_end_raw, "%Y-%m-%d").date()
        except ValueError as error:
            raise ValueError(
                f"Reproduction bundle {driver} normalization dates are invalid"
            ) from error
        if sample_start > sample_end or sample_end.isoformat() != week:
            raise ValueError(
                f"Reproduction bundle {driver} normalization sample endpoint is invalid"
            )

        mean = finite_number(normalization.get("mean"), f"bundle {driver} mean")
        sample_sd = finite_number(
            normalization.get("sample_std_ddof_1"), f"bundle {driver} sample std"
        )
        if sample_sd <= 0:
            raise ValueError(f"Reproduction bundle {driver} sample std must be positive")
        raw_z = finite_number(
            component.get("z_unclipped"), f"bundle {driver} unclipped z"
        )
        clipped_z = finite_number(
            component.get("z_clipped"), f"bundle {driver} clipped z"
        )
        clip_limit = finite_number(
            component.get("clip_limit"), f"bundle {driver} clip limit"
        )
        if clip_limit != 3.5:
            raise ValueError(f"Reproduction bundle {driver} clip limit is invalid")
        recomputed_raw_z = (weekly_level - mean) / sample_sd
        if abs(raw_z - recomputed_raw_z) > REPRO_TOLERANCE:
            raise ValueError(
                f"Reproduction bundle {driver} raw z does not reproduce from frozen moments"
            )
        recomputed_clipped_z = max(-3.5, min(3.5, recomputed_raw_z))
        if abs(clipped_z - recomputed_clipped_z) > REPRO_TOLERANCE:
            raise ValueError(
                f"Reproduction bundle {driver} clipped z does not reproduce"
            )

        weight = finite_number(component.get("weight"), f"bundle {driver} weight")
        if weight != expected_weight:
            raise ValueError(f"Reproduction bundle {driver} weight is invalid")
        contribution = finite_number(
            component.get("contribution"), f"bundle {driver} contribution"
        )
        recomputed_contribution = clipped_z * weight
        if abs(contribution - recomputed_contribution) > REPRO_TOLERANCE:
            raise ValueError(
                f"Reproduction bundle {driver} contribution does not reproduce"
            )
        reproduced_score += recomputed_contribution

        source = provenance[driver]
        source_expectations = {
            "source_observation_date": source.get("observation_date"),
            "source_provider": source.get("provider"),
            "source_series": source.get("series"),
            "source_url": source.get("source_url"),
        }
        for field, expected in source_expectations.items():
            if component.get(field) != expected:
                raise ValueError(
                    f"Reproduction bundle {driver}.{field} differs from release provenance"
                )
        if component.get("forward_fill_possible") is not True:
            raise ValueError(
                f"Reproduction bundle {driver} must disclose forward-fill possibility"
            )

    metadata_score = finite_number(metadata.get("latest_score"), "metadata.latest_score")
    published = bundle.get("published") or {}
    published_score = finite_number(published.get("score"), "bundle published score")
    published_regime = published.get("regime")
    if abs(reproduced_score - metadata_score) > REPRO_TOLERANCE:
        raise ValueError("Frozen reproduction bundle does not reproduce release score")
    if abs(published_score - metadata_score) > REPRO_TOLERANCE:
        raise ValueError("Reproduction bundle published score differs from release score")
    expected_regime = canonical_regime(reproduced_score)
    if expected_regime != metadata.get("latest_regime"):
        raise ValueError("Frozen reproduction bundle does not reproduce release regime")
    if published_regime != expected_regime:
        raise ValueError("Reproduction bundle published regime is inconsistent")

    reproduction = bundle.get("reproduction") or {}
    reproduction_score = finite_number(
        reproduction.get("score"), "bundle reproduction score"
    )
    if abs(reproduction_score - reproduced_score) > REPRO_TOLERANCE:
        raise ValueError("Bundle reproduction score field is inconsistent")
    if reproduction.get("regime") != expected_regime:
        raise ValueError("Bundle reproduction regime field is inconsistent")
    if finite_number(
        reproduction.get("absolute_tolerance"), "bundle reproduction tolerance"
    ) != REPRO_TOLERANCE:
        raise ValueError("Unexpected bundle reproduction tolerance")
    if reproduction.get("verified_equal_to_published") is not True:
        raise ValueError("Reproduction bundle must be marked verified_equal_to_published")


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

    if reproduction_bundle_required(week):
        validate_reproduction_bundle(root, metadata, week)

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
