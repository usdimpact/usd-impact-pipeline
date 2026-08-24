from __future__ import annotations

import copy
import hashlib
import json
import math
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

import usd_impact_score_v2 as score_v2
from scripts import freeze_score_v3_initialization as freeze_v3
from scripts import score_v3_candidates as v3


class ScoreV3FoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = v3.load_protocol()
        cls.weekly = cls._synthetic_weekly(340)

    @staticmethod
    def _synthetic_weekly(n: int) -> pd.DataFrame:
        index = pd.date_range("2018-01-05", periods=n, freq="W-FRI")
        base = np.arange(n, dtype=float)
        data = {}
        for offset, driver in enumerate(v3.EXPECTED_DRIVERS, start=1):
            # Trend plus two deterministic oscillations keeps std/MAD positive
            # without introducing randomness into the tests.
            data[driver] = (
                50.0 * offset
                + base * (0.07 + offset * 0.003)
                + np.sin(base / (3.0 + offset)) * (1.5 + offset * 0.1)
                + np.cos(base / (7.0 + offset)) * 0.5
            )
        return pd.DataFrame(data, index=index)

    def test_locked_protocol_candidate_set_is_exact(self) -> None:
        ids = tuple(item["candidate_id"] for item in self.protocol["candidates"])
        self.assertEqual(ids, v3.EXPECTED_CANDIDATE_IDS)
        self.assertEqual(v3.LOCKED_PREREGISTRATION_SHA, freeze_v3.LOCKED_PREREGISTRATION_SHA)
        self.assertEqual(
            self.protocol["knowledge_boundary"]["prospective_untouched_holdout_start"],
            "2026-08-28",
        )

    def test_unregistered_fifth_candidate_fails_closed(self) -> None:
        modified = copy.deepcopy(self.protocol)
        fifth = copy.deepcopy(modified["candidates"][0])
        fifth["candidate_id"] = "V3_POST_HOC"
        modified["candidates"].append(fifth)
        path = Path("tests/.tmp_score_v3_protocol.json")
        try:
            path.write_text(json.dumps(modified), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Candidate set differs"):
                v3.load_protocol(path)
        finally:
            path.unlink(missing_ok=True)

    def test_every_candidate_has_absolute_weight_budget_one(self) -> None:
        for candidate_id in v3.EXPECTED_CANDIDATE_IDS:
            weights = v3.candidate_weights(self.protocol, candidate_id)
            self.assertEqual(set(weights), set(v3.EXPECTED_DRIVERS))
            self.assertTrue(
                math.isclose(
                    sum(abs(value) for value in weights.values()),
                    1.0,
                    rel_tol=0,
                    abs_tol=1e-12,
                )
            )

    def test_protocol_regime_thresholds_match_production_v2(self) -> None:
        probes = [-3.0, -1.0, -0.999, -0.3, -0.299, 0.0, 0.299, 0.3, 0.999, 1.0, 3.0]
        for score in probes:
            self.assertEqual(v3.regime_label(score, self.protocol), score_v2.label_regime(score))

    def test_week_t_is_not_in_its_own_normalization_history(self) -> None:
        week = self.weekly.index[300]
        for candidate_id in v3.EXPECTED_CANDIDATE_IDS:
            row = v3.compute_candidate_week(self.weekly, week, candidate_id, protocol=self.protocol)
            self.assertLess(pd.Timestamp(row["history_end"]), week)
            if candidate_id == "V3_E52":
                self.assertEqual(row["history_count"], 300)
            else:
                self.assertEqual(row["history_count"], 260)

    def test_future_rows_cannot_revise_a_prior_candidate_score(self) -> None:
        week = self.weekly.index[300]
        appended = self.weekly.copy()
        future_index = pd.date_range(
            self.weekly.index[-1] + pd.Timedelta(days=7),
            periods=20,
            freq="W-FRI",
        )
        future = pd.DataFrame(
            {
                driver: np.linspace(10000 + i, 50000 + i, len(future_index))
                for i, driver in enumerate(v3.EXPECTED_DRIVERS)
            },
            index=future_index,
        )
        appended = pd.concat([appended, future])

        for candidate_id in v3.EXPECTED_CANDIDATE_IDS:
            before = v3.compute_candidate_week(self.weekly, week, candidate_id, protocol=self.protocol)
            after = v3.compute_candidate_week(appended, week, candidate_id, protocol=self.protocol)
            self.assertAlmostEqual(before["score"], after["score"], places=14)
            self.assertEqual(before["regime"], after["regime"])
            self.assertEqual(before["history_end"], after["history_end"])
            self.assertEqual(before["history_count"], after["history_count"])

    def test_zscore_clip_is_exactly_plus_minus_3_5(self) -> None:
        extreme = self.weekly.copy()
        week = extreme.index[300]
        extreme.loc[week, "DXY"] = 1e12
        extreme.loc[week, "WTI"] = -1e12
        for candidate_id in v3.EXPECTED_CANDIDATE_IDS:
            row = v3.compute_candidate_week(extreme, week, candidate_id, protocol=self.protocol)
            self.assertEqual(row["clip"], 3.5)
            self.assertLessEqual(max(row["z_clipped"].values()), 3.5)
            self.assertGreaterEqual(min(row["z_clipped"].values()), -3.5)
            self.assertEqual(row["z_clipped"]["DXY"], 3.5)
            self.assertEqual(row["z_clipped"]["WTI"], -3.5)

    def test_zero_mad_scale_fails_closed_without_fallback(self) -> None:
        index = pd.date_range("2018-01-05", periods=261, freq="W-FRI")
        constant = pd.DataFrame(
            {driver: np.ones(len(index)) for driver in v3.EXPECTED_DRIVERS},
            index=index,
        )
        constant.iloc[-1] = 2.0
        for candidate_id in ("V3_MAD260", "V3_GRP_MAD260"):
            with self.assertRaisesRegex(RuntimeError, "zero_or_invalid_scale"):
                v3.compute_candidate_week(
                    constant,
                    index[-1],
                    candidate_id,
                    protocol=self.protocol,
                )

    def test_structural_readiness_does_not_select_or_rank_candidates(self) -> None:
        report = v3.structural_readiness_report(self.weekly)
        self.assertIs(report["research_only"], True)
        self.assertIs(report["predictive_claim"], False)
        self.assertIs(report["candidate_selection_performed"], False)
        self.assertEqual(
            tuple(item["candidate_id"] for item in report["candidates"]),
            v3.EXPECTED_CANDIDATE_IDS,
        )
        for item in report["candidates"]:
            self.assertIs(item["all_scores_finite"], True)
            self.assertAlmostEqual(item["absolute_weight_budget"], 1.0, places=12)

    def test_frozen_artifact_is_self_consistent_when_present(self) -> None:
        matrix = freeze_v3.DEFAULT_MATRIX_PATH
        manifest_path = freeze_v3.DEFAULT_MANIFEST_PATH
        if not matrix.exists() and not manifest_path.exists():
            self.skipTest("One-time initialization freeze has not completed yet")
        self.assertTrue(matrix.exists())
        self.assertTrue(manifest_path.exists())
        manifest = freeze_v3.verify_frozen(matrix, manifest_path)
        self.assertEqual(manifest["matrix_last_week"], "2026-08-21")
        self.assertEqual(manifest["cutoff_week"], "2026-08-21")
        self.assertEqual(manifest["prospective_holdout_start"], "2026-08-28")
        self.assertEqual(manifest["locked_preregistration_commit_sha"], v3.LOCKED_PREREGISTRATION_SHA)
        self.assertEqual(
            manifest["matrix_sha256"],
            hashlib.sha256(matrix.read_bytes()).hexdigest(),
        )
        self.assertIs(manifest["may_be_replaced_after_freeze"], False)
        self.assertEqual(
            manifest["historical_data_status"],
            "retrospective_current_vintage_not_as_published",
        )


if __name__ == "__main__":
    unittest.main()
