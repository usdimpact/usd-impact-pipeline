#!/usr/bin/env python3
"""Locked formal evaluator for the Score v2 one-week DXY predictive study."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from scripts import score_v2_predictive_ingestion as ingestion
from scripts import score_v2_predictive_manifest as manifest_v2p

N = 52
TOLERANCE = 1e-12
WILSON_Z = 1.959963984540054


def _canonical_sha(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def evidence_prefix_sha256(entries: list[dict[str, Any]], resolved_predictions: int) -> str:
    required_observations = resolved_predictions + 1
    if len(entries) < required_observations:
        raise RuntimeError("Predictive evidence prefix is shorter than the requested checkpoint")
    return _canonical_sha({"entries": entries[:required_observations]})


def _direction(value: float) -> str:
    return "up" if value >= 0 else "down"


def _accuracy(predictions: list[str], outcomes: list[str]) -> tuple[int, float]:
    if len(predictions) != len(outcomes) or not predictions:
        raise RuntimeError("Prediction and outcome sequences must have equal non-zero length")
    correct = sum(prediction == outcome for prediction, outcome in zip(predictions, outcomes))
    return correct, correct / len(predictions)


def _average_ranks(values: list[float]) -> list[float]:
    ordered = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and values[ordered[end]] == values[ordered[start]]:
            end += 1
        average = ((start + 1) + end) / 2.0
        for position in range(start, end):
            ranks[ordered[position]] = average
        start = end
    return ranks


def _pearson(left: list[float], right: list[float]) -> float | None:
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    left_centered = [value - left_mean for value in left]
    right_centered = [value - right_mean for value in right]
    denominator = math.sqrt(
        sum(value * value for value in left_centered)
        * sum(value * value for value in right_centered)
    )
    if denominator == 0:
        return None
    return sum(a * b for a, b in zip(left_centered, right_centered)) / denominator


def _spearman(left: list[float], right: list[float]) -> float | None:
    return _pearson(_average_ranks(left), _average_ranks(right))


def _wilson(correct: int, total: int) -> tuple[float, float]:
    proportion = correct / total
    z2 = WILSON_Z * WILSON_Z
    denominator = 1 + z2 / total
    center = (proportion + z2 / (2 * total)) / denominator
    half_width = (
        WILSON_Z
        * math.sqrt((proportion * (1 - proportion) / total) + z2 / (4 * total * total))
        / denominator
    )
    return max(0.0, center - half_width), min(1.0, center + half_width)


def _circular_shift_result(predictions: list[str], outcomes: list[str], observed_correct: int) -> dict[str, Any]:
    qualifying = 0
    for shift in range(1, N):
        shifted_correct = sum(predictions[(index + shift) % N] == outcomes[index] for index in range(N))
        if shifted_correct >= observed_correct:
            qualifying += 1
    return {
        "nonzero_shifts_evaluated": N - 1,
        "qualifying_nonzero_shifts": qualifying,
        "p_value": (1 + qualifying) / N,
        "comparison": "shifted_correct_count >= observed_correct_count",
    }


def build_formal_report(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    manifest = manifest_v2p.load_manifest(root / manifest_v2p.MANIFEST_PATH)
    status = manifest_v2p.validate_manifest(manifest, root=root)
    if status["resolved_predictions"] != N or status["weekly_observations"] != N + 1:
        raise RuntimeError("Formal predictive performance cannot be calculated before 52 resolved predictions")
    records = ingestion.validate_all_records(root, manifest)

    origins = records[:N]
    outcomes_records = records[1 : N + 1]
    scores = [float(record["as_published_observation"]["score"]) for record in origins]
    origin_dxy = [float(record["as_published_observation"]["dxy_weekly_level"]) for record in origins]
    outcome_dxy = [float(record["as_published_observation"]["dxy_weekly_level"]) for record in outcomes_records]
    returns = [math.log(outcome / origin) for origin, outcome in zip(origin_dxy, outcome_dxy)]
    actual = [_direction(value) for value in returns]
    model = [str(record["frozen_predictions"]["model_direction"]) for record in origins]
    always_up = [str(record["frozen_predictions"]["always_up_direction"]) for record in origins]
    momentum = [str(record["frozen_predictions"]["momentum_direction"]) for record in origins]

    model_correct, model_accuracy = _accuracy(model, actual)
    always_correct, always_accuracy = _accuracy(always_up, actual)
    momentum_correct, momentum_accuracy = _accuracy(momentum, actual)
    circular = _circular_shift_result(model, actual, model_correct)
    lower, upper = _wilson(model_correct, N)
    best_benchmark = max(always_accuracy, momentum_accuracy)
    benchmark_lift = model_accuracy - best_benchmark

    gates = {
        "exactly_52_consecutive_non_backfilled_resolved_predictions": True,
        "all_records_bound_to_immutable_as_published_bundles": True,
        "directional_accuracy_at_least_0_60": model_accuracy + TOLERANCE >= 0.60,
        "circular_shift_p_value_at_most_0_05": circular["p_value"] <= 0.05 + TOLERANCE,
        "accuracy_at_least_0_05_above_best_comparator": benchmark_lift + TOLERANCE >= 0.05,
    }
    passed = all(gates.values())
    result = (
        "bounded_one_week_dxy_directional_predictive_evidence_established_in_this_sample"
        if passed
        else "meaningful_one_week_dxy_directional_predictive_evidence_not_established_under_this_protocol"
    )

    return {
        "$schema": "../../score_v2_predictive_checkpoint.schema.json",
        "report_type": "predictive_formal_52_result",
        "reporting_version": 1,
        "study": "usd_impact_score_v2_one_week_dxy_direction_2026-08-25",
        "research_only": True,
        "production_change": False,
        "resolved_predictions": N,
        "weekly_observations": N + 1,
        "latest_week": records[-1]["week"],
        "locked_preregistration_commit_sha": manifest_v2p.LOCKED_PREREGISTRATION_SHA,
        "implementation_contract_sha256": manifest_v2p.IMPLEMENTATION_CONTRACT_SHA256,
        "evidence_prefix_sha256": evidence_prefix_sha256(manifest["entries"], N),
        "endpoint_values_emitted": True,
        "performance_calculated": True,
        "primary_endpoint": {
            "directional_accuracy": model_accuracy,
            "correct_predictions": model_correct,
            "total_predictions": N,
            "wilson_95_interval": {"lower": lower, "upper": upper},
            "circular_shift": circular,
        },
        "comparators": {
            "always_up": {"accuracy": always_accuracy, "correct_predictions": always_correct},
            "one_week_dxy_momentum": {"accuracy": momentum_accuracy, "correct_predictions": momentum_correct},
            "best_comparator_accuracy": best_benchmark,
            "model_lift_over_best_comparator": benchmark_lift,
        },
        "secondary_endpoints": {
            "spearman_score_next_week_return": _spearman(scores, returns),
            "accuracy_lift_over_always_up": model_accuracy - always_accuracy,
            "accuracy_lift_over_momentum": model_accuracy - momentum_accuracy,
            "confirmatory": False,
        },
        "meaningful_predictive_evidence_gate": {
            "all_conditions_required": True,
            "conditions": gates,
            "passed": passed,
            "result": result,
        },
        "interpretation_boundary": (
            "A pass supports only a bounded one-week DXY directional association in this prospective sample. "
            "It does not establish trading profitability, causal power, calibration, performance for other "
            "assets, or durable future accuracy. Evidence remains first-party until independently reproduced or audited."
        ),
        "automatic_site_claim_performed": False,
        "production_promotion_performed": False,
    }
