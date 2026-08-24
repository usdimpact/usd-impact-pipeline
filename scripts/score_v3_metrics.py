#!/usr/bin/env python3
"""Prospective endpoint evaluator for the preregistered Score v3 shadow study.

Research-only. This module never fetches live market data. Candidate prospective
weeks come from immutable shadow artifacts; v2 benchmark weeks come from the
immutable production reproduction archive. Endpoint reporting is blocked except
at the preregistered 13/26/39-week interim checkpoints and the formal 52-week
selection review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import usd_impact_score_v2 as score_v2
from scripts import build_score_repro_bundle as repro
from scripts import freeze_score_v3_initialization as freeze_v3
from scripts import score_v3_candidates as v3
from scripts import score_v3_manifest as manifest_v3

CONTRACT_PATH = Path("research/score_v3_metric_implementation_contract.json")
SCHEMA_PATH = Path("research/score_v3_metric_implementation_contract.schema.json")
BENCHMARK_ID = "V2_BASELINE"
MODEL_IDS = (BENCHMARK_ID, *v3.EXPECTED_CANDIDATE_IDS)
WINDOW = 52
INTERIM_CHECKPOINTS = (13, 26, 39)
FORMAL_SELECTION_WEEK = 52
NUMERIC_TOLERANCE = 1e-12


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object in {path}")
    return payload


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_metric_contract(root: Path = Path(".")) -> tuple[dict[str, Any], str]:
    root = root.resolve()
    path = root / CONTRACT_PATH
    contract = _read_json(path)
    digest = _sha256_file(path)
    init_manifest = freeze_v3.verify_frozen(
        root / freeze_v3.DEFAULT_MATRIX_PATH,
        root / freeze_v3.DEFAULT_MANIFEST_PATH,
    )
    protocol = v3.load_protocol(root / v3.PROTOCOL_PATH)
    schema = _read_json(root / SCHEMA_PATH)

    if contract.get("contract_id") != "usd_impact_score_v3_metric_implementation_2026-08-24":
        raise RuntimeError("Unexpected Score v3 metric contract id")
    if contract.get("contract_version") != 1 or contract.get("registered_date") != "2026-08-24":
        raise RuntimeError("Unexpected Score v3 metric contract version/date")
    if contract.get("research_only") is not True or contract.get("production_change") is not False:
        raise RuntimeError("Metric contract must remain research-only")
    if contract.get("predictive_claim") is not False or contract.get("trading_strategy_claim") is not False:
        raise RuntimeError("Metric contract may not make predictive/trading claims")
    if contract.get("locked_preregistration_commit_sha") != v3.LOCKED_PREREGISTRATION_SHA:
        raise RuntimeError("Metric contract preregistration lock mismatch")
    if contract.get("prospective_holdout_start") != "2026-08-28":
        raise RuntimeError("Metric contract holdout start drifted")

    initialization = contract.get("initialization") or {}
    if initialization.get("matrix_sha256") != init_manifest.get("matrix_sha256"):
        raise RuntimeError("Metric contract initialization hash mismatch")
    if initialization.get("historical_data_status") != "retrospective_current_vintage_not_as_published":
        raise RuntimeError("Metric contract historical status drifted")
    if initialization.get("replacement_allowed") is not False:
        raise RuntimeError("Metric contract unexpectedly permits initialization replacement")

    models = contract.get("models") or {}
    if models.get("benchmark_id") != BENCHMARK_ID:
        raise RuntimeError("Metric contract benchmark id drifted")
    if tuple(models.get("candidate_ids") or ()) != v3.EXPECTED_CANDIDATE_IDS:
        raise RuntimeError("Metric contract candidate set drifted")
    if tuple(models.get("driver_order") or ()) != v3.EXPECTED_DRIVERS:
        raise RuntimeError("Metric contract driver order drifted")

    loo = contract.get("leave_one_driver_out") or {}
    if loo.get("variants") != 8 or loo.get("remaining_absolute_weight_sum") != 1.0:
        raise RuntimeError("Leave-one-driver-out contract drifted")
    if loo.get("weight_rule") != "rescale_remaining_signed_weights_proportionally":
        raise RuntimeError("Leave-one-driver-out weight convention drifted")

    corr = contract.get("correlation_concentration") or {}
    if corr.get("window_weeks") != WINDOW:
        raise RuntimeError("Correlation window drifted")
    if corr.get("week_t_excluded") is not True or corr.get("future_weeks_excluded") is not True:
        raise RuntimeError("Correlation window must remain prior-only")
    if corr.get("nonfinite_off_diagonal_replacement") != 0.0 or corr.get("diagonal_forced_to") != 1.0:
        raise RuntimeError("Correlation non-finite convention drifted")

    reporting = contract.get("reporting_policy") or {}
    if tuple(reporting.get("interim_checkpoint_weeks") or ()) != INTERIM_CHECKPOINTS:
        raise RuntimeError("Interim reporting schedule drifted")
    if reporting.get("formal_selection_week") != FORMAL_SELECTION_WEEK:
        raise RuntimeError("Formal selection boundary drifted")
    if reporting.get("selection_before_52_allowed") is not False:
        raise RuntimeError("Metric contract unexpectedly permits early selection")

    selection = contract.get("selection_implementation") or {}
    if selection.get("primary_within_5_percent_rule") != "abs(a-b) <= 0.05 * max(a,b)":
        raise RuntimeError("Primary tie convention drifted")
    if selection.get("loo_within_2_percentage_points_rule") != "abs(a-b) <= 0.02":
        raise RuntimeError("LOO tie convention drifted")
    if float(selection.get("numeric_equality_tolerance", -1.0)) != NUMERIC_TOLERANCE:
        raise RuntimeError("Selection numeric tolerance drifted")
    if tuple(selection.get("simplicity_order") or ()) != v3.EXPECTED_CANDIDATE_IDS:
        raise RuntimeError("Selection simplicity order drifted")

    sources = contract.get("prospective_sources") or {}
    if sources.get("live_provider_refetch_allowed") is not False:
        raise RuntimeError("Live provider refetch must remain prohibited")
    if sources.get("later_revised_provider_history_allowed") is not False:
        raise RuntimeError("Later revised history must remain prohibited")

    if schema.get("title") != "USD Impact Score v3 prospective metric implementation contract":
        raise RuntimeError("Metric contract schema title drifted")
    if schema.get("additionalProperties") is not False:
        raise RuntimeError("Metric contract schema must remain closed")
    if "selection_implementation" not in set(schema.get("required") or []):
        raise RuntimeError("Metric contract schema is missing required selection contract")

    prereg_ids = tuple(item["candidate_id"] for item in protocol["candidates"])
    if prereg_ids != v3.EXPECTED_CANDIDATE_IDS:
        raise RuntimeError("Locked preregistration candidate order drifted")
    return contract, digest


def _initialization_levels(root: Path) -> pd.DataFrame:
    freeze_v3.verify_frozen(
        root / freeze_v3.DEFAULT_MATRIX_PATH,
        root / freeze_v3.DEFAULT_MANIFEST_PATH,
    )
    data = pd.read_csv(root / freeze_v3.DEFAULT_MATRIX_PATH, parse_dates=["date"]).set_index("date")
    data = data[list(v3.EXPECTED_DRIVERS)].dropna().sort_index()
    if data.empty or data.index[-1].date().isoformat() != "2026-08-21":
        raise RuntimeError("Frozen Score v3 initialization matrix cutoff drifted")
    return data


def v2_bootstrap(root: Path) -> list[dict[str, Any]]:
    data = _initialization_levels(root)
    mu = data.mean()
    sd = data.std(ddof=1)
    invalid = sd.isna() | ~np.isfinite(sd) | (sd <= 0)
    if invalid.any():
        raise RuntimeError("Invalid v2 frozen bootstrap standard deviation")
    z = ((data - mu) / sd).clip(lower=-score_v2.ZSCORE_CLIP, upper=score_v2.ZSCORE_CLIP)
    rows = [
        {
            "week": idx.date().isoformat(),
            "z_clipped": {driver: float(z.loc[idx, driver]) for driver in v3.EXPECTED_DRIVERS},
        }
        for idx in z.index[-WINDOW:]
    ]
    if len(rows) != WINDOW:
        raise RuntimeError("V2 bootstrap does not contain exactly 52 rows")
    return rows


def candidate_bootstrap(root: Path, candidate_id: str) -> list[dict[str, Any]]:
    data = _initialization_levels(root)
    protocol = v3.load_protocol(root / v3.PROTOCOL_PATH)
    series = v3.compute_candidate_series(data, candidate_id, protocol=protocol)
    if len(series) < WINDOW:
        raise RuntimeError(f"Candidate {candidate_id} lacks 52 retrospective component rows")
    rows = [
        {"week": row["week"], "z_clipped": {d: float(row["z_clipped"][d]) for d in v3.EXPECTED_DRIVERS}}
        for row in series[-WINDOW:]
    ]
    return rows


def leave_one_out_variants(
    zscores: dict[str, float],
    weights: dict[str, float],
    *,
    protocol: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    if set(zscores) != set(v3.EXPECTED_DRIVERS) or set(weights) != set(v3.EXPECTED_DRIVERS):
        raise RuntimeError("Leave-one-out inputs must contain exactly eight drivers")
    variants: dict[str, dict[str, Any]] = {}
    for omitted in v3.EXPECTED_DRIVERS:
        remaining = {d: float(w) for d, w in weights.items() if d != omitted}
        abs_sum = sum(abs(value) for value in remaining.values())
        if abs_sum <= 0:
            raise RuntimeError("Leave-one-out remaining weight budget is zero")
        normalized = {d: value / abs_sum for d, value in remaining.items()}
        normalized_abs_sum = sum(abs(value) for value in normalized.values())
        if not math.isclose(normalized_abs_sum, 1.0, rel_tol=0, abs_tol=NUMERIC_TOLERANCE):
            raise RuntimeError("Leave-one-out normalized weight budget is not 1.0")
        score = float(sum(float(zscores[d]) * normalized[d] for d in normalized))
        variants[omitted] = {
            "score": score,
            "regime": v3.regime_label(score, protocol),
            "remaining_absolute_weight_sum": normalized_abs_sum,
        }
    return variants


def concentration_metrics(
    prior_history: list[dict[str, Any]],
    contributions: dict[str, float],
    *,
    current_week: str,
) -> dict[str, Any]:
    if len(prior_history) < WINDOW:
        raise RuntimeError("Need 52 prior component rows for correlation endpoint")
    window = prior_history[-WINDOW:]
    if any(item["week"] >= current_week for item in window):
        raise RuntimeError("Correlation window includes week t or future data")
    frame = pd.DataFrame(
        [{d: float(item["z_clipped"][d]) for d in v3.EXPECTED_DRIVERS} for item in window],
        columns=list(v3.EXPECTED_DRIVERS),
    )
    corr_abs = np.abs(frame.corr().to_numpy(dtype=float))
    corr_abs = np.nan_to_num(corr_abs, nan=0.0, posinf=1.0, neginf=1.0)
    np.fill_diagonal(corr_abs, 1.0)

    values = np.array([float(contributions[d]) for d in v3.EXPECTED_DRIVERS], dtype=float)
    gross = float(np.abs(values).sum())
    if not math.isfinite(gross) or gross <= 0:
        raise RuntimeError("Gross absolute contribution must be positive")
    shares = np.abs(values) / gross
    hhi = float(shares @ shares)
    corr_index = float(shares @ corr_abs @ shares)
    if hhi <= 0 or corr_index <= 0:
        raise RuntimeError("Invalid concentration index")
    effective_uncorrelated = float(1.0 / hhi)
    effective_correlated = min(float(1.0 / corr_index), effective_uncorrelated)
    return {
        "correlation_window_start": window[0]["week"],
        "correlation_window_end": window[-1]["week"],
        "ordinary_contribution_hhi": hhi,
        "effective_uncorrelated_component_count": effective_uncorrelated,
        "absolute_correlation_adjusted_concentration_index": corr_index,
        "effective_correlated_component_count": effective_correlated,
        "dominant_absolute_contribution_share": float(shares.max()),
    }


def _load_prospective_records(root: Path) -> list[dict[str, Any]]:
    manifest_path = root / manifest_v3.MANIFEST_PATH
    manifest = manifest_v3.load_manifest(manifest_path)
    manifest_v3.validate_manifest(
        manifest,
        initialization_manifest_path=root / manifest_v3.INITIALIZATION_MANIFEST_PATH,
    )
    records: list[dict[str, Any]] = []
    for entry in manifest["entries"]:
        week = str(entry["week"])
        result_path = root / "research" / "prospective" / Path(str(entry["candidate_result_file"])).name
        if not result_path.exists():
            raise RuntimeError(f"Missing prospective candidate result for {week}")
        if _sha256_file(result_path) != entry["candidate_result_sha256"]:
            raise RuntimeError(f"Prospective candidate result hash mismatch for {week}")
        result = _read_json(result_path)
        if result.get("week") != week:
            raise RuntimeError(f"Prospective candidate result week mismatch for {week}")
        if result.get("locked_preregistration_commit_sha") != v3.LOCKED_PREREGISTRATION_SHA:
            raise RuntimeError(f"Prospective candidate result protocol mismatch for {week}")
        if set(result.get("candidates") or {}) != set(v3.EXPECTED_CANDIDATE_IDS):
            raise RuntimeError(f"Prospective candidate set mismatch for {week}")

        archive_path = root / f"public/archive/{week}/repro_bundle.json"
        if not archive_path.exists():
            raise RuntimeError(f"Missing immutable v2 archive bundle for {week}")
        archive_hash = _sha256_file(archive_path)
        if archive_hash != entry["source_v2_bundle_sha256"]:
            raise RuntimeError(f"V2 archive hash differs from prospective manifest for {week}")
        if result.get("source_v2_bundle_sha256") != archive_hash:
            raise RuntimeError(f"Candidate result v2 bundle hash mismatch for {week}")
        bundle = _read_json(archive_path)
        repro.verify_bundle(bundle)
        if bundle.get("score_week") != week:
            raise RuntimeError(f"V2 archive week mismatch for {week}")
        records.append({"entry": entry, "result": result, "bundle": bundle})
    return records


def _candidate_state(result: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    payload = result["candidates"][candidate_id]
    return {
        "week": result["week"],
        "score": float(payload["score"]),
        "regime": str(payload["regime"]),
        "z_clipped": {d: float(payload["z_clipped"][d]) for d in v3.EXPECTED_DRIVERS},
        "weights": {d: float(payload["weights"][d]) for d in v3.EXPECTED_DRIVERS},
        "contributions": {d: float(payload["contributions"][d]) for d in v3.EXPECTED_DRIVERS},
    }


def _v2_state(bundle: dict[str, Any]) -> dict[str, Any]:
    components = bundle.get("components") or {}
    if set(components) != set(v3.EXPECTED_DRIVERS):
        raise RuntimeError("V2 bundle driver set mismatch")
    weights = {d: float(components[d]["weight"]) for d in v3.EXPECTED_DRIVERS}
    if not math.isclose(sum(abs(v) for v in weights.values()), 1.0, rel_tol=0, abs_tol=NUMERIC_TOLERANCE):
        raise RuntimeError("V2 bundle absolute weight budget drifted")
    published = bundle.get("published") or {}
    return {
        "week": str(bundle["score_week"]),
        "score": float(published["score"]),
        "regime": str(published["regime"]),
        "z_clipped": {d: float(components[d]["z_clipped"]) for d in v3.EXPECTED_DRIVERS},
        "weights": weights,
        "contributions": {d: float(components[d]["contribution"]) for d in v3.EXPECTED_DRIVERS},
    }


def _revision_immunity(root: Path, records: list[dict[str, Any]]) -> dict[str, bool]:
    if not records:
        return {candidate_id: True for candidate_id in v3.EXPECTED_CANDIDATE_IDS}
    levels = _initialization_levels(root).copy()
    for record in records:
        result = record["result"]
        week = pd.Timestamp(result["week"])
        source_levels = result.get("source_weekly_levels") or {}
        if set(source_levels) != set(v3.EXPECTED_DRIVERS):
            raise RuntimeError(f"Invalid source levels for {result['week']}")
        levels.loc[week, list(v3.EXPECTED_DRIVERS)] = [float(source_levels[d]) for d in v3.EXPECTED_DRIVERS]
    levels = levels.sort_index()
    protocol = v3.load_protocol(root / v3.PROTOCOL_PATH)
    immunity = {candidate_id: True for candidate_id in v3.EXPECTED_CANDIDATE_IDS}
    for record in records:
        result = record["result"]
        for candidate_id in v3.EXPECTED_CANDIDATE_IDS:
            stored = result["candidates"][candidate_id]
            recomputed = v3.compute_candidate_week(
                levels,
                result["week"],
                candidate_id,
                protocol=protocol,
            )
            if not math.isclose(
                float(stored["score"]),
                float(recomputed["score"]),
                rel_tol=0,
                abs_tol=NUMERIC_TOLERANCE,
            ) or stored["regime"] != recomputed["regime"]:
                immunity[candidate_id] = False
    return immunity


def build_weekly_metrics(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    contract, contract_sha = load_metric_contract(root)
    records = _load_prospective_records(root)
    protocol = v3.load_protocol(root / v3.PROTOCOL_PATH)
    histories: dict[str, list[dict[str, Any]]] = {BENCHMARK_ID: v2_bootstrap(root)}
    histories.update(
        {candidate_id: candidate_bootstrap(root, candidate_id) for candidate_id in v3.EXPECTED_CANDIDATE_IDS}
    )
    immunity = _revision_immunity(root, records)
    rows: dict[str, list[dict[str, Any]]] = {model_id: [] for model_id in MODEL_IDS}

    for record in records:
        states = {BENCHMARK_ID: _v2_state(record["bundle"])}
        states.update(
            {candidate_id: _candidate_state(record["result"], candidate_id) for candidate_id in v3.EXPECTED_CANDIDATE_IDS}
        )
        for model_id, state in states.items():
            concentration = concentration_metrics(
                histories[model_id],
                state["contributions"],
                current_week=state["week"],
            )
            loo = leave_one_out_variants(state["z_clipped"], state["weights"], protocol=protocol)
            agreement = {
                driver: loo[driver]["regime"] == state["regime"] for driver in v3.EXPECTED_DRIVERS
            }
            rows[model_id].append(
                {
                    "week": state["week"],
                    "score": state["score"],
                    "regime": state["regime"],
                    "leave_one_out_regime_match": agreement,
                    **concentration,
                }
            )
            histories[model_id].append(
                {"week": state["week"], "z_clipped": dict(state["z_clipped"])}
            )

    return {
        "contract_sha256": contract_sha,
        "research_only": True,
        "predictive_claim": False,
        "prospective_weeks": len(records),
        "future_revision_immunity": {BENCHMARK_ID: True, **immunity},
        "weekly_metrics": rows,
        "contract": contract,
    }


def summarize_model(
    rows: list[dict[str, Any]],
    *,
    future_revision_immunity: bool,
) -> dict[str, Any]:
    if not rows:
        raise RuntimeError("Cannot summarize zero prospective weeks")
    eff = np.array([float(row["effective_correlated_component_count"]) for row in rows], dtype=float)
    dominant = np.array([float(row["dominant_absolute_contribution_share"]) for row in rows], dtype=float)
    loo_rates = {}
    for driver in v3.EXPECTED_DRIVERS:
        loo_rates[driver] = float(
            np.mean([bool(row["leave_one_out_regime_match"][driver]) for row in rows])
        )
    regimes = [str(row["regime"]) for row in rows]
    turnover = (
        float(sum(left != right for left, right in zip(regimes, regimes[1:])) / (len(regimes) - 1))
        if len(regimes) >= 2
        else None
    )
    return {
        "completed_weeks": len(rows),
        "future_revision_immunity": bool(future_revision_immunity),
        "median_effective_correlated_component_count": float(np.median(eff)),
        "minimum_leave_one_driver_out_regime_agreement": float(min(loo_rates.values())),
        "leave_one_driver_out_regime_agreement": loo_rates,
        "regime_turnover_rate": turnover,
        "dominant_absolute_contribution_share": float(np.median(dominant)),
    }


def reporting_stage(completed_weeks: int) -> str:
    if completed_weeks in INTERIM_CHECKPOINTS:
        return "interim"
    if completed_weeks >= FORMAL_SELECTION_WEEK:
        return "formal_52_week_review"
    raise RuntimeError(
        f"endpoint_reporting_not_allowed:{completed_weeks}; "
        "allowed interim checkpoints are 13/26/39 and selection review begins at 52"
    )


def select_candidate(summaries: dict[str, dict[str, Any]], *, completed_weeks: int) -> dict[str, Any]:
    if completed_weeks < FORMAL_SELECTION_WEEK:
        raise RuntimeError("candidate_selection_not_allowed_before_52_weeks")
    benchmark = summaries[BENCHMARK_ID]
    v2_turnover = benchmark["regime_turnover_rate"]
    if v2_turnover is None:
        raise RuntimeError("V2 turnover is unavailable at formal selection")
    v2_loo = float(benchmark["minimum_leave_one_driver_out_regime_agreement"])
    v2_eff = float(benchmark["median_effective_correlated_component_count"])

    eligibility: dict[str, dict[str, Any]] = {}
    contenders: list[str] = []
    for candidate_id in v3.EXPECTED_CANDIDATE_IDS:
        item = summaries[candidate_id]
        turnover = item["regime_turnover_rate"]
        finite = all(
            math.isfinite(float(item[key]))
            for key in (
                "median_effective_correlated_component_count",
                "minimum_leave_one_driver_out_regime_agreement",
                "dominant_absolute_contribution_share",
            )
        ) and turnover is not None and math.isfinite(float(turnover))
        gates = {
            "future_revision_immunity": item["future_revision_immunity"] is True,
            "finite_endpoints": finite,
            "turnover_gate": finite and float(turnover) <= 1.25 * float(v2_turnover) + NUMERIC_TOLERANCE,
            "leave_one_out_gate": finite and float(item["minimum_leave_one_driver_out_regime_agreement"]) >= v2_loo - 0.05 - NUMERIC_TOLERANCE,
            "primary_improvement_gate": finite and float(item["median_effective_correlated_component_count"]) >= 1.10 * v2_eff - NUMERIC_TOLERANCE,
        }
        eligible = all(gates.values())
        eligibility[candidate_id] = {"eligible_and_improved": eligible, "gates": gates}
        if eligible:
            contenders.append(candidate_id)

    if not contenders:
        return {
            "candidate_selection_performed": True,
            "selected": BENCHMARK_ID,
            "decision": "keep_v2",
            "eligibility": eligibility,
            "tie_break_path": ["no_candidate_passed_all_gates_and_10_percent_improvement"],
        }

    max_eff = max(float(summaries[c]["median_effective_correlated_component_count"]) for c in contenders)
    primary_pool = [
        c for c in contenders
        if abs(float(summaries[c]["median_effective_correlated_component_count"]) - max_eff)
        <= 0.05 * max(float(summaries[c]["median_effective_correlated_component_count"]), max_eff)
        + NUMERIC_TOLERANCE
    ]
    if len(primary_pool) == 1:
        selected = primary_pool[0]
        path = ["highest_primary_endpoint_outside_5_percent_tie"]
    else:
        max_loo = max(float(summaries[c]["minimum_leave_one_driver_out_regime_agreement"]) for c in primary_pool)
        loo_pool = [
            c for c in primary_pool
            if abs(float(summaries[c]["minimum_leave_one_driver_out_regime_agreement"]) - max_loo)
            <= 0.02 + NUMERIC_TOLERANCE
        ]
        if len(loo_pool) == 1:
            selected = loo_pool[0]
            path = ["primary_within_5_percent", "higher_minimum_leave_one_out_agreement"]
        else:
            min_turnover = min(float(summaries[c]["regime_turnover_rate"]) for c in loo_pool)
            turnover_pool = [
                c for c in loo_pool
                if abs(float(summaries[c]["regime_turnover_rate"]) - min_turnover)
                <= NUMERIC_TOLERANCE
            ]
            selected = next(c for c in v3.EXPECTED_CANDIDATE_IDS if c in turnover_pool)
            path = [
                "primary_within_5_percent",
                "loo_within_2_percentage_points",
                "lower_turnover",
                "simplicity_order_if_still_tied",
            ]
    return {
        "candidate_selection_performed": True,
        "selected": selected,
        "decision": "candidate_selected_for_separate_production_review",
        "eligibility": eligibility,
        "tie_break_path": path,
    }


def build_checkpoint_report(root: Path = Path(".")) -> dict[str, Any]:
    metrics = build_weekly_metrics(root)
    completed = int(metrics["prospective_weeks"])
    stage = reporting_stage(completed)
    evaluation_weeks = FORMAL_SELECTION_WEEK if completed >= FORMAL_SELECTION_WEEK else completed
    summaries = {
        model_id: summarize_model(
            metrics["weekly_metrics"][model_id][:evaluation_weeks],
            future_revision_immunity=bool(metrics["future_revision_immunity"][model_id]),
        )
        for model_id in MODEL_IDS
    }
    report: dict[str, Any] = {
        "report_type": "score_v3_prospective_endpoint_checkpoint",
        "research_only": True,
        "predictive_claim": False,
        "metric_contract_sha256": metrics["contract_sha256"],
        "stage": stage,
        "completed_prospective_weeks_available": completed,
        "evaluation_weeks": evaluation_weeks,
        "ranking_performed": False,
        "candidate_selection_performed": False,
        "summaries": summaries,
    }
    if stage == "formal_52_week_review":
        report["selection"] = select_candidate(summaries, completed_weeks=evaluation_weeks)
        report["candidate_selection_performed"] = True
    return report


def readiness_report(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    contract, contract_sha = load_metric_contract(root)
    manifest = manifest_v3.load_manifest(root / manifest_v3.MANIFEST_PATH)
    manifest_v3.validate_manifest(
        manifest,
        initialization_manifest_path=root / manifest_v3.INITIALIZATION_MANIFEST_PATH,
    )
    bootstraps = {BENCHMARK_ID: len(v2_bootstrap(root))}
    bootstraps.update(
        {candidate_id: len(candidate_bootstrap(root, candidate_id)) for candidate_id in v3.EXPECTED_CANDIDATE_IDS}
    )
    return {
        "report_type": "score_v3_metric_implementation_readiness",
        "research_only": True,
        "predictive_claim": False,
        "metric_contract_sha256": contract_sha,
        "prospective_holdout_start": contract["prospective_holdout_start"],
        "prospective_weeks_stored": len(manifest["entries"]),
        "bootstrap_rows": bootstraps,
        "week_t_excluded": True,
        "live_provider_refetch_allowed": False,
        "interim_checkpoints": list(INTERIM_CHECKPOINTS),
        "formal_selection_week": FORMAL_SELECTION_WEEK,
        "ranking_performed": False,
        "candidate_selection_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--mode", choices=("readiness", "checkpoint"), default="readiness")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = readiness_report(args.root) if args.mode == "readiness" else build_checkpoint_report(args.root)
    raw = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
