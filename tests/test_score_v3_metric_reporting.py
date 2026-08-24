from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import score_v3_metric_reporting as reporting
from scripts import score_v3_metrics as metrics


REPO = Path(__file__).resolve().parents[1]


class ScoreV3MetricReportingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        manifest = self.root / "research/score_v3_prospective_manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text('{"entries":[]}\n', encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _state(self, completed: int) -> dict:
        rows = [
            {
                "week": f"prospective-week-{i + 1:03d}",
                "effective_correlated_component_count": 2.0,
                "dominant_absolute_contribution_share": 0.25,
                "leave_one_out_regime_match": {},
                "regime": "Neutral / transitional",
            }
            for i in range(completed)
        ]
        return {
            "contract_sha256": "a" * 64,
            "prospective_weeks": completed,
            "future_revision_immunity": {model_id: True for model_id in metrics.MODEL_IDS},
            "weekly_metrics": {model_id: list(rows) for model_id in metrics.MODEL_IDS},
        }

    @staticmethod
    def _checkpoint_report(completed: int) -> dict:
        formal = completed == 52
        return {
            "report_type": "score_v3_prospective_endpoint_checkpoint",
            "research_only": True,
            "predictive_claim": False,
            "metric_contract_sha256": "a" * 64,
            "stage": "formal_52_week_review" if formal else "interim",
            "completed_prospective_weeks_available": completed,
            "evaluation_weeks": completed,
            "ranking_performed": False,
            "candidate_selection_performed": formal,
            "summaries": {"fixture": {"completed_weeks": completed}},
            **({"selection": {"decision": "keep_v2"}} if formal else {}),
        }

    def _manifest_patch(self, completed: int):
        payload = {"entries": [{"week": str(i)} for i in range(completed)]}
        return (
            patch.object(reporting.manifest_v3, "load_manifest", return_value=payload),
            patch.object(reporting.manifest_v3, "validate_manifest", return_value=None),
        )

    def test_weekly_validation_emits_no_endpoint_values(self) -> None:
        with patch.object(reporting.metrics, "build_weekly_metrics", return_value=self._state(1)):
            report = reporting.validate_weekly(self.root)
        self.assertEqual(report["prospective_weeks"], 1)
        self.assertIs(report["metric_state_validated"], True)
        self.assertIs(report["endpoint_values_emitted"], False)
        self.assertIs(report["ranking_performed"], False)
        self.assertIs(report["candidate_selection_performed"], False)
        self.assertIs(report["production_promotion_performed"], False)
        self.assertNotIn("summaries", report)
        self.assertNotIn("weekly_metrics", report)
        self.assertNotIn("effective_correlated_component_count", json.dumps(report))

    def test_future_revision_immunity_failure_fails_closed(self) -> None:
        state = self._state(1)
        state["future_revision_immunity"]["V3_E52"] = False
        with patch.object(reporting.metrics, "build_weekly_metrics", return_value=state):
            with self.assertRaisesRegex(RuntimeError, "future-revision immunity failed"):
                reporting.validate_weekly(self.root)

    def test_missed_prior_checkpoint_cannot_be_silently_backfilled(self) -> None:
        with patch.object(reporting.metrics, "build_weekly_metrics", return_value=self._state(14)):
            with self.assertRaisesRegex(RuntimeError, "Missing required Score v3 checkpoint report 013"):
                reporting.validate_weekly(self.root)

    def test_noncheckpoint_week_validates_without_writing_endpoint_report(self) -> None:
        with patch.object(reporting.metrics, "build_weekly_metrics", return_value=self._state(12)):
            report = reporting.checkpoint_if_due(self.root)
        self.assertEqual(report["status"], "validated_no_checkpoint_due")
        self.assertIs(report["checkpoint_due"], False)
        self.assertIs(report["checkpoint_written"], False)
        self.assertFalse((self.root / reporting.CHECKPOINT_DIR).exists())

    def test_interim_checkpoint_is_deterministic_and_idempotent(self) -> None:
        manifest = self.root / "research/score_v3_prospective_manifest.json"
        manifest.write_text('{"fixture":"checkpoint-13"}\n', encoding="utf-8")
        load_manifest, validate_manifest = self._manifest_patch(13)
        with (
            patch.object(reporting.metrics, "build_weekly_metrics", return_value=self._state(13)),
            patch.object(reporting.metrics, "build_checkpoint_report", return_value=self._checkpoint_report(13)),
            load_manifest,
            validate_manifest,
        ):
            first = reporting.checkpoint_if_due(self.root)
            second = reporting.checkpoint_if_due(self.root)
        self.assertEqual(first["status"], "checkpoint_written")
        self.assertEqual(second["status"], "checkpoint_already_recorded_noop")
        path = self.root / first["checkpoint_file"]
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["stage"], "interim")
        self.assertIs(payload["ranking_performed"], False)
        self.assertIs(payload["candidate_selection_performed"], False)
        self.assertIs(payload["production_promotion_performed"], False)

    def test_tampered_checkpoint_fails_instead_of_overwriting_history(self) -> None:
        manifest = self.root / "research/score_v3_prospective_manifest.json"
        manifest.write_text('{"fixture":"checkpoint-13"}\n', encoding="utf-8")
        load_manifest, validate_manifest = self._manifest_patch(13)
        with (
            patch.object(reporting.metrics, "build_weekly_metrics", return_value=self._state(13)),
            patch.object(reporting.metrics, "build_checkpoint_report", return_value=self._checkpoint_report(13)),
            load_manifest,
            validate_manifest,
        ):
            first = reporting.checkpoint_if_due(self.root)
        path = self.root / first["checkpoint_file"]
        path.write_text('{"tampered":true}\n', encoding="utf-8")
        load_manifest, validate_manifest = self._manifest_patch(13)
        with (
            patch.object(reporting.metrics, "build_weekly_metrics", return_value=self._state(13)),
            patch.object(reporting.metrics, "build_checkpoint_report", return_value=self._checkpoint_report(13)),
            load_manifest,
            validate_manifest,
        ):
            with self.assertRaisesRegex(RuntimeError, "differs from deterministic recomputation"):
                reporting.checkpoint_if_due(self.root)

    def test_formal_52_week_checkpoint_records_selection_but_never_promotes(self) -> None:
        for checkpoint in (13, 26, 39):
            path = self.root / reporting.CHECKPOINT_DIR / f"score_v3_checkpoint_{checkpoint:03d}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n", encoding="utf-8")
        manifest = self.root / "research/score_v3_prospective_manifest.json"
        manifest.write_text('{"fixture":"checkpoint-52"}\n', encoding="utf-8")
        load_manifest, validate_manifest = self._manifest_patch(52)
        with (
            patch.object(reporting.metrics, "build_weekly_metrics", return_value=self._state(52)),
            patch.object(reporting.metrics, "build_checkpoint_report", return_value=self._checkpoint_report(52)),
            load_manifest,
            validate_manifest,
        ):
            report = reporting.checkpoint_if_due(self.root)
        payload = json.loads((self.root / report["checkpoint_file"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["stage"], "formal_52_week_review")
        self.assertIs(payload["candidate_selection_performed"], True)
        self.assertIs(payload["production_change"], False)
        self.assertIs(payload["production_promotion_performed"], False)

    def test_checkpoint_schedule_is_exactly_preregistered(self) -> None:
        self.assertEqual(reporting.CHECKPOINTS, (13, 26, 39, 52))

    def test_shadow_workflow_wires_silent_validation_and_checkpoint_only_writes(self) -> None:
        workflow = (REPO / ".github/workflows/score-v3-shadow.yml").read_text(encoding="utf-8")
        self.assertIn("python -m scripts.score_v3_metric_reporting", workflow)
        self.assertIn("steps.ingest.outputs.status != 'pre_holdout_noop'", workflow)
        self.assertIn("steps.metrics.outputs.checkpoint_written == 'true'", workflow)
        self.assertIn("prospective/checkpoints/score_v3_checkpoint_(013|026|039|052)", workflow)
        self.assertIn("research/score_v3_metric_implementation_contract.json", workflow)
        self.assertIn("scripts/score_v3_metrics.py", workflow)
        self.assertIn("scripts/score_v3_metric_reporting.py", workflow)
        self.assertIn("never promotes a research candidate to production automatically", workflow)
        self.assertNotIn("git add public/", workflow)


if __name__ == "__main__":
    unittest.main()
