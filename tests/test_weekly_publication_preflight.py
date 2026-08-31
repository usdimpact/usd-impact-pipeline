import hashlib
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import weekly_publication_preflight as preflight


NOW = datetime(2026, 8, 31, 19, 0, tzinfo=timezone.utc)
EXPECTED = "2026-08-28"
PRIOR = "2026-08-21"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, value: str = "fixture\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_authorities(root: Path, week: str) -> tuple[dict, dict, dict]:
    score = {"metadata": {"latest_date": week}, "weeks": [{"date": week}]}
    bridge = {"week_ending": week, "score": -0.69}
    bundle = {"score_week": week, "published": {"score": -0.69}}
    write_json(root / "public/data/usd_impact_score_v2.json", score)
    write_json(root / "public/data/weekly_input_latest.json", bridge)
    write_json(root / "public/data/score_repro_bundle_latest.json", bundle)
    return score, bridge, bundle


def write_complete_release(root: Path, week: str, *, predictive: bool = True) -> None:
    score, bridge, bundle = write_authorities(root, week)
    write_json(root / f"public/archive/{week}/score.json", score)
    write_json(root / f"public/archive/{week}/weekly_input.json", bridge)
    archive_bundle = root / f"public/archive/{week}/repro_bundle.json"
    write_json(archive_bundle, bundle)
    write_json(root / f"data/weekly_input_{week}.json", bridge)
    for path in (
        root / f"public/archive/{week}/en.html",
        root / f"public/archive/{week}/es.html",
        root / f"commentary/archive/{week}_en.md",
        root / f"commentary/archive/{week}_es.md",
    ):
        write_text(path)

    if predictive:
        archive_hash = hashlib.sha256(archive_bundle.read_bytes()).hexdigest()
        record = {
            "week": week,
            "source_v2_bundle": {"sha256": archive_hash},
        }
        record_path = (
            root / f"research/predictive/score_v2_predictive_week_{week}.json"
        )
        write_json(record_path, record)
        record_hash = hashlib.sha256(record_path.read_bytes()).hexdigest()
        write_json(
            root / "research/score_v2_predictive_manifest.json",
            {
                "entries": [
                    {
                        "week": week,
                        "source_v2_bundle_sha256": archive_hash,
                        "weekly_record_file": record_path.name,
                        "weekly_record_sha256": record_hash,
                    }
                ]
            },
        )


class WeeklyPublicationPreflightTests(unittest.TestCase):
    def test_latest_completed_friday_is_never_future_dated(self):
        self.assertEqual(preflight.latest_completed_friday(NOW).isoformat(), EXPECTED)

    def test_absent_expected_week_requests_generation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            write_authorities(root, PRIOR)
            result = preflight.evaluate(root, now=NOW)
        self.assertEqual(result.action, "generate")
        self.assertEqual(result.expected_week, EXPECTED)
        self.assertEqual(result.published_week, PRIOR)

    def test_complete_expected_week_is_an_explicit_noop(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            write_complete_release(root, EXPECTED)
            with patch.object(
                preflight.validate_weekly_release,
                "validate",
                return_value=EXPECTED,
            ) as validate:
                result = preflight.evaluate(root, now=NOW)
        self.assertEqual(result.action, "noop")
        self.assertEqual(result.published_week, EXPECTED)
        validate.assert_called_once_with(root.resolve())

    def test_partial_expected_week_fails_closed(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            score, _, _ = write_authorities(root, PRIOR)
            score["metadata"]["latest_date"] = EXPECTED
            write_json(root / "public/data/usd_impact_score_v2.json", score)
            write_text(root / f"public/archive/{EXPECTED}/en.html")
            with self.assertRaisesRegex(preflight.PreflightError, "disagree"):
                preflight.evaluate(root, now=NOW)

    def test_archive_mismatch_fails_before_strict_validator(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            write_complete_release(root, EXPECTED)
            write_json(
                root / f"public/archive/{EXPECTED}/weekly_input.json",
                {"week_ending": EXPECTED, "score": -0.5},
            )
            with patch.object(
                preflight.validate_weekly_release,
                "validate",
            ) as validate:
                with self.assertRaisesRegex(
                    preflight.PreflightError,
                    "Archived bridge",
                ):
                    preflight.evaluate(root, now=NOW)
            validate.assert_not_called()

    def test_predictive_source_hash_mismatch_fails_closed(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            write_complete_release(root, EXPECTED)
            manifest_path = root / "research/score_v2_predictive_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["entries"][0]["source_v2_bundle_sha256"] = "0" * 64
            write_json(manifest_path, manifest)
            with patch.object(
                preflight.validate_weekly_release,
                "validate",
                return_value=EXPECTED,
            ):
                with self.assertRaisesRegex(
                    preflight.PreflightError,
                    "Predictive source archive hash mismatch",
                ):
                    preflight.evaluate(root, now=NOW)

    def test_strict_release_validation_failure_is_fail_closed(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            write_complete_release(root, EXPECTED)
            with patch.object(
                preflight.validate_weekly_release,
                "validate",
                side_effect=ValueError("tampered release"),
            ):
                with self.assertRaisesRegex(
                    preflight.PreflightError,
                    "tampered release",
                ):
                    preflight.evaluate(root, now=NOW)


if __name__ == "__main__":
    unittest.main()
