"""Offline regression tests for the live Score Pages perimeter monitor.

Only fabricated HTTP observations are used. No networking, secrets, live
Score inputs or provider-derived data are accessed during these tests.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.check_score_pages_security_posture import (
    MAX_BODY_BYTES,
    ORIGINS,
    REQUEST_TIMEOUT_SECONDS,
    TARGETS,
    CheckTarget,
    HttpObservation,
    fetch_fixed_url,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]

DENIAL_HEADERS = {
    "Content-Type": "text/html; charset=utf-8",
    "Cache-Control": "private, no-store",
    "X-Content-Type-Options": "nosniff",
    "X-Robots-Tag": "noindex, nofollow",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": (
        "default-src 'none'; base-uri 'none'; object-src 'none'; "
        "form-action 'none'; frame-ancestors 'none'"
    ),
}
PREMIUM_DENIAL = (
    b"<html><title>Research Membership required</title>"
    b"<h1>Research Membership required</h1>"
    b'<a href="https://www.usd-impact.com/score/">USD Impact</a></html>'
)
REDEMPTION_GONE = b"Score redemption moved to usd-impact.com"


class PagesSecurityPostureContractTests(unittest.TestCase):
    def test_fixed_roots_and_non_sensitive_monitor_paths(self) -> None:
        self.assertEqual(
            ORIGINS,
            (
                "https://usd-impact-pipeline.pages.dev",
                "https://score.usd-impact.com",
            ),
        )
        self.assertEqual(
            {(target.method, target.path, target.expected_status) for target in TARGETS},
            {
                ("GET", "/en/", 403),
                ("GET", "/score-redeem", 410),
                ("HEAD", "/data/score_v2_methodology.json", 200),
            },
        )
        self.assertEqual(
            [target.read_body for target in TARGETS],
            [True, True, False],
        )
        self.assertLessEqual(MAX_BODY_BYTES, 4096)
        self.assertLessEqual(REQUEST_TIMEOUT_SECONDS, 15)

    def test_premium_denial_is_now_expected(self) -> None:
        target = TARGETS[0]
        self.assertEqual(
            validate(
                target,
                HttpObservation(403, DENIAL_HEADERS, PREMIUM_DENIAL),
            ),
            [],
        )
        bad = validate(
            target,
            HttpObservation(200, DENIAL_HEADERS, b"<html>premium content</html>"),
        )
        self.assertTrue(any("expected HTTP 403" in msg for msg in bad))

    def test_protected_denial_headers_fail_closed(self) -> None:
        target = TARGETS[0]
        for missing in (
            "Cache-Control",
            "X-Content-Type-Options",
            "X-Robots-Tag",
            "Referrer-Policy",
            "Content-Security-Policy",
        ):
            with self.subTest(header=missing):
                headers = dict(DENIAL_HEADERS)
                del headers[missing]
                self.assertTrue(
                    validate(target, HttpObservation(403, headers, PREMIUM_DENIAL)),
                )
        self.assertTrue(
            validate(target, HttpObservation(403, DENIAL_HEADERS, b"unrecognized denial")),
        )

    def test_retired_score_redemption_is_tombstoned(self) -> None:
        target = TARGETS[1]
        self.assertEqual(
            validate(target, HttpObservation(410, DENIAL_HEADERS, REDEMPTION_GONE)),
            [],
        )
        self.assertTrue(
            validate(target, HttpObservation(200, DENIAL_HEADERS, REDEMPTION_GONE)),
        )
        self.assertTrue(
            validate(target, HttpObservation(410, DENIAL_HEADERS, b"wrong tombstone")),
        )

    def test_public_methodology_is_head_only_without_data_body(self) -> None:
        target = TARGETS[2]
        self.assertEqual(
            validate(target, HttpObservation(200, {"Content-Type": "application/json"})),
            [],
        )
        self.assertTrue(
            validate(target, HttpObservation(403, {"Content-Type": "text/plain"})),
        )
        self.assertTrue(
            validate(target, HttpObservation(200, {}, b"unexpected content")),
        )

    def test_unapproved_origin_or_target_fails_before_network(self) -> None:
        for origin, target in (
            ("https://attacker.example", TARGETS[0]),
            (
                ORIGINS[0],
                CheckTarget("marketdata", "/data/weekly_input_latest.json", "GET", 200, True),
            ),
        ):
            with self.subTest(origin=origin, target=target):
                with self.assertRaises(ValueError):
                    fetch_fixed_url(origin, target)

    def test_existing_scheduled_workflow_uses_only_new_monitor(self) -> None:
        text = (
            ROOT / ".github/workflows/pages-security-posture.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("python3 -m scripts.check_score_pages_security_posture", text)
        self.assertIn("schedule:", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("curl --silent", text)
        self.assertNotIn('grep -q \'USD Impact Score\'', text)


if __name__ == "__main__":
    unittest.main()
