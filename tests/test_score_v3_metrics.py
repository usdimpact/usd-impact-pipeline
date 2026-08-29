from __future__ import annotations

import math
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import score_v3_candidates as v3
from scripts import score_v3_metrics as metrics
import usd_impact_score_v2 as score_v2


ROOT = Path(__file__).resolve().parents[1]


def _history() -> list[dict]:
    rows = []
    start = metrics.pd.Timestamp("2025-08-29")
    for i in range(metrics.WINDOW):
        week = start + metrics.pd.Timedelta(days=7 * i)
        rows.append(
            {
                "week": week.date().isoformat(),
                "z_clipped": {
                    driver: float(((i + 1) * (j + 2)) % 17) / 10.0 - 0.8
                    for j, driver in enumerate(v3.EXPECTED_DRIVERS)
                },
            }
        )
    return rows


def _state_payload(week: str, scale: float) -> tuple[dict, dict]:
    protocol = v3.load_protocol(ROOT / v3.PROTOCOL_PATH)
    z = {driver: scale * (i + 1) for i, driver in enumerate(v3.EXPECTED_DRIVERS)}
    candidates = {}
    for candidate_id in v3.EXPECTED_CANDIDATE_IDS:
        weights = v3.candidate_weights(protocol, candidate_id)
        contributions = {driver: z[driver] * weights[driver] for driver in v3.EXPECTED_DRIVERS}
        score = float(sum(contributions.values()))
        candidates[candidate_id] = {
            "score": score,
            "regime": v3.regime_label(score, protocol),
            "z_clipped": dict(z),
            "weights": weights,
            "contributions": contributions,
        }

    v2_weights = {driver: float(score_v2.WEIGHTS[driver]) for driver in v3.EXPECTED_DRIVERS}
    v2_contributions = {driver: z[driver] * v2_weights[driver] for driver in v3.EXPECTED_DRIVERS}
    v2_score = float(sum(v2_contributions.values()))
    bundle = {
        "score_week": week,
        "components": {
            driver: {
                "z_clipped": z[driver],
                "weight": v2_weights[driver],
                "contribution": v2_contributions[driver],
            }
            for driver in v3.EXPECTED_DRIVERS
        },
        "published": {
            "score": v2_score,
            "regime": v3.regime_label(v2_score, protocol),
        },
    }
    result = {"week": week, "candidates": candidates}
    return result, bundle


def _summary(eff: float, loo: float, turnover: float, *, immune: bool = True) -> dict:
    return {
        "completed_weeks": 52,
        "future_revision_immunity": immune,
        "median_effective_correlated_component_count": eff,
        "minimum_leave_one_driver_out_regime_agreement": loo,
        "regime_turnover_rate": turnover,
        "dominant_absolute_contribution_share": 0.25,
    }


class ScoreV3MetricContractTests(unittest.TestCase):
    def test_contract_and_bootstrap_are_ready_before_holdout(self) -> None:
        manifest = metrics.manifest_v3.load_manifest(ROOT / metrics.manifest_v3.MANIFEST_PATH)
        manifest["entries"] = []
        with patch.object(metrics.manifest_v3, "load_manifest", return_value=manifest):
            report = metrics.readiness_report(ROOT)
        self.assertEqual(report["prospective_holdout_start"], "2026-08-28")
        self.assertEqual(report["prospective_weeks_stored"], 0)
        self.assertEqual(set(report["bootstrap_rows"]), set(metrics.MODEL_IDS))
        self.assertTrue(all(value == 52 for value in report["bootstrap_rows"].values()))
        self.assertEqual(len(report["metric_contract_sha256"]), 64)
        self.assertIs(report["ranking_performed"], False)
        self.assertIs(report["candidate_selection_performed"], False)

    def test_v2_bootstrap_is_frozen_current_vintage_through_august_21(self) -> None:
        contract, _ = metrics.load_metric_contract(ROOT)
        rows = metrics.v2_bootstrap(ROOT)
        self.assertEqual(len(rows), 52)
        self.assertEqual(rows[-1]["week"], "2026-08-21")
        self.assertEqual(
            contract["bootstrap"]["v2_benchmark"]["retrospective_status"],
            "retrospective_current_vintage_not_as_published",
        )
        self.assertIs(contract["initialization"]["replacement_allowed"], False)

    def test_leave_one_out_renormalizes_every_remaining_budget_to_one(self) -> None:
        protocol = v3.load_protocol(ROOT / v3.PROTOCOL_PATH)
        weights = v3.candidate_weights(protocol, "V3_GRP_MAD260")
        zscores = {driver: float(i + 1) / 10.0 for i, driver in enumerate(v3.EXPECTED_DRIVERS)}
        variants = metrics.leave_one_out_variants(zscores, weights, protocol=protocol)
        self.assertEqual(set(variants), set(v3.EXPECTED_DRIVERS))
        for payload in variants.values():
            self.assertAlmostEqual(payload["remaining_absolute_weight_sum"], 1.0, places=12)

    def test_correlation_window_excludes_week_t(self) -> None:
        history = _history()
        contributions = {driver: float(i + 1) / 20.0 for i, driver in enumerate(v3.EXPECTED_DRIVERS)}
        report = metrics.concentration_metrics(
            history,
            contributions,
            current_week="2026-08-28",
        )
        self.assertEqual(report["correlation_window_end"], "2026-08-21")
        contaminated = history[1:] + [
            {"week": "2026-08-28", "z_clipped": {d: 99.0 for d in v3.EXPECTED_DRIVERS}}
        ]
        with self.assertRaisesRegex(RuntimeError, "week t or future"):
            metrics.concentration_metrics(
                contaminated,
                contributions,
                current_week="2026-08-28",
            )

    def test_appending_future_record_does_not_revise_past_endpoint_row(self) -> None:
        first_result, first_bundle = _state_payload("2026-08-28", 0.10)
        second_result, second_bundle = _state_payload("2026-09-04", 0.11)
        record1 = {"result": first_result, "bundle": first_bundle}
        record2 = {"result": second_result, "bundle": second_bundle}
        contract = {"contract_id": "fixture"}

        common = dict(
            load_metric_contract=patch.object(metrics, "load_metric_contract", return_value=(contract, "a" * 64)),
            v2_bootstrap=patch.object(metrics, "v2_bootstrap", side_effect=lambda _root: _history()),
            candidate_bootstrap=patch.object(metrics, "candidate_bootstrap", side_effect=lambda _root, _candidate_id: _history()),
            revision=patch.object(
                metrics,
                "_revision_immunity",
                return_value={candidate_id: True for candidate_id in v3.EXPECTED_CANDIDATE_IDS},
            ),
        )
        with common["load_metric_contract"], common["v2_bootstrap"], common["candidate_bootstrap"], common["revision"]:
            with patch.object(metrics, "_load_prospective_records", return_value=[record1]):
                one = metrics.build_weekly_metrics(ROOT)
            with patch.object(metrics, "_load_prospective_records", return_value=[record1, record2]):
                two = metrics.build_weekly_metrics(ROOT)

        for model_id in metrics.MODEL_IDS:
            self.assertEqual(one["weekly_metrics"][model_id][0], two["weekly_metrics"][model_id][0])

    def test_source_contains_no_live_provider_refetch_path(self) -> None:
        source = (ROOT / "scripts/score_v3_metrics.py").read_text(encoding="utf-8")
        self.assertIn('public/archive/{week}/repro_bundle.json', source)
        self.assertNotIn("fetch_all_inputs(", source)
        self.assertNotIn("yfinance", source)
        self.assertNotIn("fred.stlouisfed.org", source)

    def test_noncheckpoint_reporting_is_rejected(self) -> None:
        for completed in (0, 1, 12, 14, 25, 27, 38, 40, 51):
            with self.assertRaisesRegex(RuntimeError, "endpoint_reporting_not_allowed"):
                metrics.reporting_stage(completed)
        for completed in (13, 26, 39):
            self.assertEqual(metrics.reporting_stage(completed), "interim")
        self.assertEqual(metrics.reporting_stage(52), "formal_52_week_review")

    def test_selection_is_rejected_before_52_weeks(self) -> None:
        summaries = {metrics.BENCHMARK_ID: _summary(2.0, 0.80, 0.20)}
        summaries.update({candidate_id: _summary(2.3, 0.82, 0.20) for candidate_id in v3.EXPECTED_CANDIDATE_IDS})
        with self.assertRaisesRegex(RuntimeError, "not_allowed_before_52"):
            metrics.select_candidate(summaries, completed_weeks=51)

    def test_interim_checkpoint_never_ranks_or_selects(self) -> None:
        rows = [
            {
                "week": f"2026-{9 + (i // 4):02d}-{1 + (i % 4) * 7:02d}",
                "regime": "Neutral / transitional",
                "effective_correlated_component_count": 2.0 + i / 100.0,
                "dominant_absolute_contribution_share": 0.25,
                "leave_one_out_regime_match": {d: True for d in v3.EXPECTED_DRIVERS},
            }
            for i in range(13)
        ]
        fake = {
            "contract_sha256": "b" * 64,
            "prospective_weeks": 13,
            "future_revision_immunity": {model_id: True for model_id in metrics.MODEL_IDS},
            "weekly_metrics": {model_id: list(rows) for model_id in metrics.MODEL_IDS},
        }
        with patch.object(metrics, "build_weekly_metrics", return_value=fake):
            report = metrics.build_checkpoint_report(ROOT)
        self.assertEqual(report["stage"], "interim")
        self.assertIs(report["ranking_performed"], False)
        self.assertIs(report["candidate_selection_performed"], False)
        self.assertNotIn("selection", report)

    def test_formal_selection_keeps_v2_without_ten_percent_improvement(self) -> None:
        summaries = {metrics.BENCHMARK_ID: _summary(2.0, 0.80, 0.20)}
        summaries.update(
            {
                "V3_E52": _summary(2.19, 0.82, 0.20),
                "V3_R260": _summary(2.18, 0.82, 0.20),
                "V3_MAD260": _summary(2.17, 0.82, 0.20),
                "V3_GRP_MAD260": _summary(2.16, 0.82, 0.20),
            }
        )
        result = metrics.select_candidate(summaries, completed_weeks=52)
        self.assertEqual(result["decision"], "keep_v2")
        self.assertEqual(result["selected"], metrics.BENCHMARK_ID)

    def test_formal_selection_uses_frozen_tie_break_sequence(self) -> None:
        summaries = {
            metrics.BENCHMARK_ID: _summary(2.0, 0.80, 0.20),
            "V3_E52": _summary(2.30, 0.80, 0.20),
            "V3_R260": _summary(2.29, 0.84, 0.20),
            "V3_MAD260": _summary(2.28, 0.84, 0.15),
            "V3_GRP_MAD260": _summary(2.00, 0.90, 0.10),
        }
        result = metrics.select_candidate(summaries, completed_weeks=52)
        self.assertEqual(result["selected"], "V3_MAD260")
        self.assertEqual(
            result["tie_break_path"],
            [
                "primary_within_5_percent",
                "loo_within_2_percentage_points",
                "lower_turnover",
                "simplicity_order_if_still_tied",
            ],
        )


if __name__ == "__main__":
    unittest.main()
