from __future__ import annotations

import json
import shutil
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
WEIGHTS = {
    "DXY": 0.125,
    "WTI": -0.125,
    "SPX": -0.125,
    "VIX": 0.125,
    "BTC": -0.125,
    "GOLD": -0.125,
    "UST_2Y": 0.125,
    "UST_10Y": 0.125,
}


def copy_predictive_contract(root: Path) -> None:
    for relative in (
        "research/score_v2_predictive_preregistration.json",
        "research/score_v2_predictive_implementation_contract.json",
        "research/score_v2_predictive_manifest.json",
        "research/score_v3_initialization_2026-08-21.csv",
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / relative, target)

    manifest_path = root / "research/score_v2_predictive_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["entries"] = []
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def write_score(root: Path, week: str, score: float) -> None:
    path = root / "public/data/usd_impact_score_v2.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "metadata": {
                    "latest_date": week,
                    "latest_score": score,
                    "latest_regime": regime_for_score(score),
                },
                "weeks": [],
            }
        ),
        encoding="utf-8",
    )


def regime_for_score(score: float) -> str:
    if score >= 1.0:
        return "Strong dollar regime"
    if score >= 0.3:
        return "Firm dollar regime"
    if score >= -0.3:
        return "Neutral / transitional"
    if score >= -1.0:
        return "Soft dollar regime"
    return "Weak dollar regime"


def write_bundle(
    root: Path,
    week: str,
    *,
    score: float,
    dxy_level: float,
    archive_same: bool = True,
) -> None:
    if score not in (-1.0, 0.0, 1.0):
        raise ValueError("Predictive test bundle helper supports only -1, 0, or 1 scores")
    components = {}
    for index, (driver, weight) in enumerate(WEIGHTS.items(), start=1):
        if score == 0:
            z_clipped = 0.0
        else:
            z_clipped = score * (1.0 if weight > 0 else -1.0)
        components[driver] = {
            "weekly_level": dxy_level if driver == "DXY" else float(100 * index + 7.5),
            "z_clipped": z_clipped,
            "weight": weight,
        }
    bands = [
        {"low": 1.0, "high": None, "label": "Strong dollar regime"},
        {"low": 0.3, "high": 1.0, "label": "Firm dollar regime"},
        {"low": -0.3, "high": 0.3, "label": "Neutral / transitional"},
        {"low": -1.0, "high": -0.3, "label": "Soft dollar regime"},
        {"low": None, "high": -1.0, "label": "Weak dollar regime"},
    ]
    bundle = {
        "score_week": week,
        "pipeline_git_sha": "1" * 40,
        "requirements_lock_sha256": "2" * 64,
        "components": components,
        "calculation": {"regime_bands": bands},
        "published": {"score": score, "regime": regime_for_score(score)},
    }
    latest = root / "public/data/score_repro_bundle_latest.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(bundle, sort_keys=True), encoding="utf-8")
    archive = root / f"public/archive/{week}/repro_bundle.json"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive_same:
        shutil.copy2(latest, archive)
    else:
        altered = dict(bundle)
        altered["pipeline_git_sha"] = "3" * 40
        archive.write_text(json.dumps(altered, sort_keys=True), encoding="utf-8")
