from __future__ import annotations

import base64
import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
HEADERS = PUBLIC / "_headers"
EXPECTED_FRAME_ANCESTORS = {
    "https://www.usd-impact.com",
    "https://usd-impact.com",
}


def load_headers() -> dict[str, str]:
    lines = HEADERS.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "/*":
        raise AssertionError("Cloudflare Pages _headers must start with a /* rule")

    parsed: dict[str, str] = {}
    for raw in lines[1:]:
        if not raw.strip():
            continue
        if not raw.startswith("  ") or ":" not in raw:
            raise AssertionError(f"Invalid _headers entry: {raw!r}")
        name, value = raw.strip().split(":", 1)
        parsed[name.lower()] = value.strip()
    return parsed


def csp_directives(policy: str) -> dict[str, list[str]]:
    directives: dict[str, list[str]] = {}
    for section in policy.split(";"):
        tokens = section.strip().split()
        if tokens:
            directives[tokens[0]] = tokens[1:]
    return directives


class PagesSecurityHeadersTests(unittest.TestCase):
    def test_required_security_headers_are_declared(self) -> None:
        headers = load_headers()
        self.assertEqual(headers["x-content-type-options"], "nosniff")
        self.assertEqual(
            headers["referrer-policy"], "strict-origin-when-cross-origin"
        )
        self.assertEqual(
            headers["permissions-policy"],
            "camera=(), microphone=(), geolocation=()",
        )
        self.assertEqual(
            headers["x-permitted-cross-domain-policies"], "none"
        )
        self.assertNotIn(
            "x-frame-options",
            headers,
            "The score dashboard is intentionally framed by canonical USD Impact pages; use CSP frame-ancestors instead.",
        )

    def test_csp_is_bounded_and_preserves_canonical_embedding(self) -> None:
        directives = csp_directives(load_headers()["content-security-policy"])
        self.assertEqual(directives["default-src"], ["'none'"])
        self.assertEqual(directives["connect-src"], ["'none'"])
        self.assertEqual(directives["object-src"], ["'none'"])
        self.assertEqual(directives["base-uri"], ["'none'"])
        self.assertEqual(directives["form-action"], ["'none'"])
        self.assertEqual(directives["script-src-attr"], ["'none'"])
        self.assertNotIn("'unsafe-inline'", directives["script-src"])
        self.assertEqual(
            set(directives["frame-ancestors"]), EXPECTED_FRAME_ANCESTORS
        )
        self.assertNotIn("*", directives["frame-ancestors"])
        self.assertEqual(directives["img-src"], ["'self'", "data:"])
        self.assertIn("'unsafe-inline'", directives["style-src"])
        self.assertIn("upgrade-insecure-requests", directives)

    def test_inline_script_hash_matches_the_generated_gateway(self) -> None:
        policy = csp_directives(load_headers()["content-security-policy"])
        allowed_hashes = {
            token for token in policy["script-src"] if token.startswith("'sha256-")
        }

        inline_scripts: list[tuple[Path, str]] = []
        script_pattern = re.compile(
            r"<script(?![^>]*\bsrc\s*=)[^>]*>(.*?)</script>",
            flags=re.IGNORECASE | re.DOTALL,
        )
        event_handler_pattern = re.compile(
            r"\son[a-z][a-z0-9_-]*\s*=",
            flags=re.IGNORECASE,
        )

        for html_path in sorted(PUBLIC.rglob("*.html")):
            html = html_path.read_text(encoding="utf-8")
            self.assertIsNone(
                event_handler_pattern.search(html),
                f"Inline event handler is forbidden by script-src-attr 'none': {html_path}",
            )
            for match in script_pattern.finditer(html):
                inline_scripts.append((html_path, match.group(1)))

        self.assertEqual(
            len(inline_scripts),
            1,
            "Only the root language gateway may contain inline JavaScript",
        )
        script_path, script_text = inline_scripts[0]
        self.assertEqual(script_path, PUBLIC / "index.html")
        digest = base64.b64encode(
            hashlib.sha256(script_text.encode("utf-8")).digest()
        ).decode("ascii")
        self.assertIn(
            f"'sha256-{digest}'",
            allowed_hashes,
            "The generated gateway script changed without updating the CSP hash",
        )


if __name__ == "__main__":
    unittest.main()
