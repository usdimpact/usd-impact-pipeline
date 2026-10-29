"""Read-only current-tree Score archive metadata inventory regression (Issue #155).

Never open file bodies from public/archive, public/data, or Git-only dated
weekly_input. This test considers only path names, entry kinds and policy.
The frozen snapshot must be updated under review before an authorized
archive/publication change.
"""

from __future__ import annotations

import json
import re
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "governance/score-current-tree-exposure-inventory-2026-10-29.json"


class ScoreCurrentTreeExposureInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))

    def test_authorizations_remain_false_and_publication_hold(self) -> None:
        policy = json.loads(
            (ROOT / "governance/score-publication-rights-gate.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(policy["state"], "hold")
        self.assertIsNone(policy["decision_receipt"])
        self.assertEqual(self.ledger["status"], "review_only_rights_hold")
        self.assertTrue(self.ledger["authorization"])
        for name, granted in self.ledger["authorization"].items():
            with self.subTest(approval=name):
                self.assertIs(granted, False)

    def test_dated_archive_filenames_only(self) -> None:
        root = ROOT / "public/archive"
        dated = sorted(
            p for p in root.iterdir()
            if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.name)
        )
        expected = self.ledger["dated_archive"]
        self.assertEqual(len(dated), expected["directory_count"])
        self.assertEqual(dated[0].name, expected["first"])
        self.assertEqual(dated[-1].name, expected["last"])
        counts = Counter()
        for directory in dated:
            # Directory metadata only, do not open any archived file bodies.
            for entry in directory.iterdir():
                if entry.is_file():
                    counts[entry.name] += 1
        for name, number in expected["file_counts"].items():
            with self.subTest(filename=name):
                self.assertEqual(counts[name], number)
        self.assertEqual(
            sum(counts[name] for name in ("score.json", "weekly_input.json", "repro_bundle.json")),
            expected["class_c_dated_file_count"],
        )

    def test_unindexed_prior_dates_exist_without_reindexing(self) -> None:
        dates = self.ledger["dated_archive"]
        indexed = set(dates["indexed_prior_dates"])
        omitted = set(dates["prior_dates_not_listed_in_indexes"])
        all_dates = {p.name for p in (ROOT / "public/archive").iterdir()
                     if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.name)}
        self.assertEqual(len(indexed), dates["english_historical_index_date_count"])
        self.assertEqual(len(indexed), dates["spanish_historical_index_date_count"])
        self.assertEqual(
            all_dates - indexed - {dates["current_edition_not_in_historical_indexes"]},
            omitted,
        )
        self.assertTrue((ROOT / "public/archive/en/index.html").is_file())
        self.assertTrue((ROOT / "public/archive/es/index.html").is_file())
        # Actual index HTML dates were checked manually; do not open HTML files in CI.

    def test_current_public_paths_and_git_only_bridges_exist(self) -> None:
        current = self.ledger["current_public_data"]
        self.assertEqual(len(current["class_c_paths"]), 4)
        for cls in ("class_c_paths", "class_d_paths", "class_e_paths", "class_f_paths"):
            for name in current[cls]:
                with self.subTest(path=name):
                    self.assertTrue((ROOT / name).is_file())
        self.assertEqual(
            len(list((ROOT / "data").glob("weekly_input_*.json"))),
            self.ledger["git_only_dated_weekly_bridges"]["count"],
        )
        self.assertEqual(
            self.ledger["current_tree_total_class_c_files"],
            self.ledger["dated_archive"]["class_c_dated_file_count"]
            + len(current["class_c_paths"]),
        )


if __name__ == "__main__":
    unittest.main()
