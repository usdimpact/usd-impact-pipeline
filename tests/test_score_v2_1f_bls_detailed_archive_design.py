"""Offline source-design regression checks; never fetch actual BLS observations."""
from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

from scripts import rehearse_score_v2_1f_bls_detailed_archive_design as design

ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE = ROOT / "governance/score-v2-1f-bls-detailed-archive-design-2026-10-28.json"
SCRIPT = ROOT / "scripts/rehearse_score_v2_1f_bls_detailed_archive_design.py"
SYNTHETIC = """
<html><a href="/ppi/synthetic/ppi-example-2013-01.pdf">January 2013 PDF</a>
<a href="/ppi/synthetic/ppi-example-2013-02.xlsx">February 2013 XLSX</a>
<a href="/about/">Site navigation</a></html>
"""


class ScoreV21FBlsAlternativeArchiveDesignTests(unittest.TestCase):
    def test_offline_archive_candidates_are_never_release_authorizations(self) -> None:
        got = design.rehearse_synthetic_index(SYNTHETIC, index_status=200)
        self.assertEqual(got["status"], "DESIGN_CANDIDATES_ONLY")
        self.assertEqual(len(got["candidate_urls"]), 2)
        self.assertEqual([x["media_type"] for x in got["candidate_urls"]], ["pdf", "xlsx"])
        self.assertTrue(all(
            x["candidate_url"].startswith("https://www.bls.gov/ppi/synthetic/")
            for x in got["candidate_urls"]
        ))
        for key in ("live_fetch_authorized", "vintage_verified", "score_computation_authorized"):
            self.assertFalse(got[key], key)

    def test_prior_runner_403_and_other_non_200_status_fail_closed(self) -> None:
        for status in (403, 401, 404, 429, 500, 302):
            result = design.rehearse_synthetic_index(SYNTHETIC, index_status=status)
            self.assertEqual(result["status"], "BLOCKED_FAIL_CLOSED")
            self.assertEqual(result["candidate_urls"], [])
            self.assertFalse(result["live_fetch_authorized"])
            self.assertFalse(result["vintage_verified"])

    def test_no_monthly_archive_candidate_also_fails_closed(self) -> None:
        result = design.rehearse_synthetic_index(
            "<html><p>October 2025: Not Available</p></html>", index_status=200
        )
        self.assertEqual(result["status"], "BLOCKED_NO_CANDIDATES")
        self.assertEqual(result["candidate_urls"], [])

    def test_malicious_or_ambiguous_links_fail_hard(self) -> None:
        bad = [
            "https://example.com/ppi/data.pdf",
            "//example.com/ppi/data.pdf",
            "http://www.bls.gov/ppi/data.pdf",
            "https://www.bls.gov@evil.example/ppi/data.pdf",
            "https://www.bls.gov:444/ppi/data.pdf",
            "/ppi/../data.pdf",
            "/ppi/%2e%2e/data.pdf",
            "/ppi/data.pdf?token=foo",
            "/ppi/data.pdf#section",
            "javascript:alert(1)",
            r"\ppi\data.pdf",
            "/news.release/archives/ppi_20130101.htm",
            "/ppi/data.csv",
        ]
        for href in bad:
            with self.subTest(href=href):
                html = f'<a href="{href}">January 2013 PDF</a>'
                with self.assertRaises(ValueError):
                    design.rehearse_synthetic_index(html, index_status=200)

    def test_url_scope_is_not_silently_changed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unreviewed index"):
            design.rehearse_synthetic_index(
                SYNTHETIC,
                index_status=200,
                index_url="https://data.bls.gov/other-series",
            )
        with self.assertRaises(ValueError):
            design.rehearse_synthetic_index(SYNTHETIC, index_status=True)

    def test_duplicate_candidates_are_ambiguous(self) -> None:
        duplicate = """<a href="/ppi/synthetic/ppi-2013-01.pdf">January 2013 PDF</a>
<a href="/ppi/synthetic/ppi-2013-01.pdf">January 2013 PDF</a>"""
        with self.assertRaisesRegex(ValueError, "duplicate"):
            design.rehearse_synthetic_index(duplicate, index_status=200)

    def test_rehearsal_has_no_network_import_or_live_preflight_caller(self) -> None:
        syntax = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        forbidden = ("requests", "http", "socket", "urllib.request", "urllib3")
        imports = []
        for node in ast.walk(syntax):
            if isinstance(node, ast.Import):
                imports.extend(x.name for x in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        for name in imports:
            self.assertFalse(
                any(name == prefix or name.startswith(prefix + ".") for prefix in forbidden),
                name,
            )

    def test_governance_is_design_only_and_cannot_inherit_consumed_receipt(self) -> None:
        policy = json.loads(GOVERNANCE.read_text(encoding="utf-8"))
        self.assertEqual(policy["state"], "offline_design_only")
        self.assertEqual(policy["methodology_version"], "2.1F-design-candidate")
        self.assertEqual(policy["proposed_official_index"], design.INDEX_URL)
        self.assertEqual(policy["original_blocker_http_status"], 403)
        self.assertEqual(policy["source_coverage_status"], "unverified")
        self.assertEqual(policy["index_access_from_runner"], "unverified")
        self.assertEqual(policy["bls_wpu0561_vintage_status"], "unverified")
        self.assertEqual(policy["publication_time_provenance"], "unverified")
        self.assertFalse(any(policy["authorizations"].values()))
        self.assertTrue(policy["new_owner_approval_required_for_any_live_request"])
        self.assertEqual(
            policy["preflight_blocker"],
            "https://github.com/usdimpact/usd-impact-pipeline/issues/228",
        )


if __name__ == "__main__":
    unittest.main()
