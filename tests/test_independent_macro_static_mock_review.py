"""No-network static-source guards for the never-deployed P3 Macro Context mock.

All fixtures and strings under mock-review/ are fictional. No Vercel project
is linked, no provider data is fetched, no historical Score is read and no
authenticated preview/deployment is performed by this test module.
"""
from __future__ import annotations

import json
import re
import unittest
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mock-review" / "independent-macro-context"
HTML_PATH = SOURCE / "index.html"
ROBOTS_PATH = SOURCE / "robots.txt"
CONFIG_PATH = SOURCE / "vercel.json"
README_PATH = SOURCE / "README.md"
RIGHTS_PATH = ROOT / "governance" / "independent-macro-context-fallback-draft-2026-10-30.json"
SCORE_RIGHTS_PATH = ROOT / "governance" / "score-publication-rights-gate.json"
SOURCE_SCHEMA_PATH = ROOT / "schemas" / "independent_macro_context_synthetic_preview.schema.json"

EXPECTED_FILES = {"index.html", "robots.txt", "vercel.json", "README.md"}
EXPECTED_DIALS = (
    ("Dollar breadth", "UP"),
    ("Crude inventories", "DRAW"),
    ("Treasury curve level", "POSITIVE"),
    ("Treasury curve direction", "FLATTENING"),
)
EXPECTED_TIME_ATTRS = ("2099-06-12", "2099-06-05")
DANGEROUS_TAGS = {
    "script", "iframe", "frame", "frameset", "object", "embed", "video",
    "audio", "source", "img", "picture", "link", "form", "input", "button",
    "textarea", "select", "canvas", "svg", "base", "portal",
}
DANGEROUS_ATTRS = {
    "src", "srcset", "action", "formaction", "poster", "ping",
    "data", "background", "nonce", "integrity",
}


class ParsedMock(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.visible: list[str] = []
        self.capture: str | None = None
        self.names: list[str] = []
        self.readings: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        self.tags.append((tag, values))
        if tag == "h3" and values.get("class") == "dial-name":
            self.capture = "name"
            self.names.append("")
        if tag == "div" and "reading" in (values.get("class") or "").split():
            self.capture = "reading"
            self.readings.append("")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if self.capture == "name" and tag == "h3":
            self.capture = None
        elif self.capture == "reading" and tag == "div":
            self.capture = None

    def handle_data(self, data: str) -> None:
        self.visible.append(data)
        if self.capture == "name":
            self.names[-1] += data
        elif self.capture == "reading":
            self.readings[-1] += data


def parse_and_check_markup(source: str) -> ParsedMock:
    parsed = ParsedMock()
    parsed.feed(source)
    parsed.close()
    forbidden = [(tag, values) for tag, values in parsed.tags if tag in DANGEROUS_TAGS]
    if forbidden:
        raise ValueError("forbidden active, external, form or media HTML tag")
    for tag, attrs in parsed.tags:
        if any(key in DANGEROUS_ATTRS or key.startswith("on") for key in attrs):
            raise ValueError("external/resource or event-handler attribute")
        if "href" in attrs and attrs["href"] != "#main":
            raise ValueError("external or non-skip navigation is disallowed")
        if tag == "meta" and attrs.get("http-equiv") in ("refresh", "content-security-policy"):
            raise ValueError("unreviewed meta HTTP behavior")
    if re.search(
        r"https?://|(?<!:)//[a-z]|@import|@font-face|\burl\s*\(|"
        r"fetch\s*\(|XMLHttpRequest|WebSocket|EventSource|navigator\.|/api/",
        source, flags=re.IGNORECASE,
    ):
        raise ValueError("external application, font, script or network capability")
    if "SYNTHETIC — NOT MARKET DATA — NOT PUBLISHED" not in source:
        raise ValueError("visible global synthetic disclosure absent")
    if "SYNTHETIC_DO_NOT_PUBLISH" not in source:
        raise ValueError("exact fixture marker missing")
    if "Not the original Weekly Score." not in source:
        raise ValueError("separation from paid-license Score lost")
    robots = [attrs.get("content") for tag, attrs in parsed.tags
              if tag == "meta" and attrs.get("name") == "robots"]
    if robots != ["noindex,nofollow,noarchive,nosnippet"]:
        raise ValueError("HTML indexing control missing or altered")
    if any(tag == "link" or attrs.get("rel") == "canonical"
           for tag, attrs in parsed.tags):
        raise ValueError("canonical or linked resource must not exist")
    times = [attrs.get("datetime") for tag, attrs in parsed.tags if tag == "time"]
    if tuple(times) != EXPECTED_TIME_ATTRS:
        raise ValueError("invented period dates changed")
    reference, previous = [date.fromisoformat(t) for t in times]
    if reference.year < 2099 or previous.year < 2099:
        raise ValueError("real date cannot enter synthetic markup")
    if reference.weekday() != 4 or previous.weekday() != 4:
        raise ValueError("invented reference periods must be Fridays")
    if previous + timedelta(days=7) != reference:
        raise ValueError("invented weeks must be consecutive")
    dials = tuple(zip((n.strip() for n in parsed.names),
                      (v.strip() for v in parsed.readings), strict=True))
    if dials != EXPECTED_DIALS:
        raise ValueError("invented fixed four-dial labels changed")
    if any(tag == "a" and attrs.get("href") != "#main" for tag, attrs in parsed.tags):
        raise ValueError("no external navigation in mock")
    visible = " ".join(parsed.visible)
    if re.search(r"\$\s*\d|\b\d+(?:\.\d+)?\s*(?:bps|barrels|bbl|USD)\b",
                 visible, flags=re.IGNORECASE):
        raise ValueError("numeric financial/source observation is forbidden")
    if not any(tag == "main" and attrs.get("id") == "main"
               for tag, attrs in parsed.tags):
        raise ValueError("accessible main landmark absent")
    if not any(tag == "a" and attrs.get("href") == "#main"
               for tag, attrs in parsed.tags):
        raise ValueError("accessible skip link absent")
    return parsed


def assert_static_vercel_security(config: dict) -> None:
    if set(config) != {"version", "headers"} or type(config.get("version")) is not int or config["version"] != 2:
        raise ValueError("project config may contain only static security headers")
    rules = config.get("headers")
    if not isinstance(rules, list) or len(rules) != 1 or rules[0].get("source") != "/(.*)":
        raise ValueError("security rules must cover every path")
    if set(rules[0]) != {"source", "headers"}:
        raise ValueError("unreviewed extra config rule")
    values = rules[0]["headers"]
    headers = {h.get("key"): h.get("value") for h in values}
    if len(headers) != len(values) or set(headers) != {
        "X-Robots-Tag", "Cache-Control", "Content-Security-Policy",
        "Referrer-Policy", "X-Content-Type-Options", "Permissions-Policy"
    }:
        raise ValueError("unreviewed, missing or duplicate HTTP security headers")
    if headers["X-Robots-Tag"] != "noindex, nofollow, noarchive, nosnippet":
        raise ValueError("HTTP noindex protection missing")
    if headers["Cache-Control"] != "private, no-store, max-age=0, must-revalidate":
        raise ValueError("mock HTML must not be cached publicly")
    if headers["Referrer-Policy"] != "no-referrer" or headers["X-Content-Type-Options"] != "nosniff":
        raise ValueError("information-flow header missing")
    if headers["Permissions-Policy"] != "geolocation=(), microphone=(), camera=(), payment=()":
        raise ValueError("permissions policy has expanded")
    csp = headers["Content-Security-Policy"]
    required = (
        "default-src 'none'", "script-src 'none'", "style-src 'unsafe-inline'",
        "img-src 'none'", "font-src 'none'", "connect-src 'none'",
        "media-src 'none'", "object-src 'none'", "form-action 'none'",
        "frame-ancestors 'none'", "base-uri 'none'", "worker-src 'none'",
        "manifest-src 'none'", "upgrade-insecure-requests"
    )
    if [c.strip() for c in csp.split(";")] != list(required):
        raise ValueError("static content security policy changed")


class StandaloneMacroContextMockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = HTML_PATH.read_text(encoding="utf-8")
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    def test_exact_self_contained_inventory_and_no_imported_credentials(self) -> None:
        self.assertEqual({p.name for p in SOURCE.iterdir()}, EXPECTED_FILES)
        for path in SOURCE.iterdir():
            self.assertTrue(path.is_file())
            self.assertLess(path.stat().st_size, 100_000)
        self.assertFalse(any((SOURCE / f).exists()
                             for f in (".env", "package.json", "package-lock.json",
                                       ".vercel", "sitemap.xml", "manifest.json")))
        self.assertIn("SYNTHETIC_DO_NOT_PUBLISH", self.html)

    def test_accessible_scriptless_html_with_only_invented_periods(self) -> None:
        p = parse_and_check_markup(self.html)
        self.assertEqual(len(p.names), 4)
        self.assertEqual(len(p.readings), 4)
        self.assertIn("2099-06-12", self.html)
        self.assertIn("2099-06-05", self.html)

    def test_known_four_dial_vocabulary_matches_existing_synthetic_schema(self) -> None:
        schema = json.loads(SOURCE_SCHEMA_PATH.read_text(encoding="utf-8"))
        slots = schema["properties"]["dial_labels"]["prefixItems"]
        self.assertEqual(
            [s["prefixItems"][0]["const"] for s in slots],
            ["dollar_breadth", "crude_inventory",
             "treasury_curve_level", "treasury_curve_direction"],
        )
        for slot, (_, label) in zip(slots, EXPECTED_DIALS, strict=True):
            self.assertIn(label, slot["prefixItems"][1]["enum"])
        self.assertEqual(schema["properties"]["fixture_marker"]["const"],
                         "SYNTHETIC_DO_NOT_PUBLISH")
        for field in ("rights_cleared", "publish_authorized",
                      "production_authorized", "real_data_fetch_authorized"):
            self.assertIs(schema["properties"][field]["const"], False)

    def test_robots_and_all_paths_security_headers(self) -> None:
        self.assertEqual(ROBOTS_PATH.read_text(encoding="utf-8"),
                         "User-agent: *\nDisallow: /\n")
        assert_static_vercel_security(self.config)

    def test_mutations_that_introduce_data_or_discovery_are_rejected(self) -> None:
        variants = [
            self.html.replace("SYNTHETIC_DO_NOT_PUBLISH", "LIVE"),
            self.html.replace("2099-06-12", "2026-10-30"),
            self.html.replace("2099-06-05", "2099-06-06"),
            self.html.replace("noindex,nofollow,noarchive,nosnippet", "index,follow"),
            self.html.replace('class="reading sea">DRAW', 'class="reading sea">BUY'),
            self.html.replace("</main>", '<img src="https://data.invalid/ticker"></main>'),
            self.html.replace("</main>", "<script>fetch('/api/market')</script></main>"),
            self.html.replace("</style>", '@import url("https://cdn.invalid/font");</style>'),
        ]
        for i, variant in enumerate(variants):
            self.assertNotEqual(variant, self.html)
            with self.subTest(mutant=i), self.assertRaises(ValueError):
                parse_and_check_markup(variant)

    def test_security_config_mutations_are_rejected(self) -> None:
        variants = [
            self.config | {"git": {"deploymentEnabled": True}},
            self.config | {"rewrites": [{"source": "/(.*)", "destination": "https://data.invalid"}]},
        ]
        for changes in variants:
            with self.assertRaises(ValueError):
                assert_static_vercel_security(changes)
        for name, value in (
            ("Content-Security-Policy", "default-src *; connect-src *"),
            ("Cache-Control", "public, max-age=86400"),
            ("X-Robots-Tag", "index, follow"),
        ):
            copy = json.loads(json.dumps(self.config))
            rule = next(h for h in copy["headers"][0]["headers"] if h["key"] == name)
            rule["value"] = value
            with self.subTest(header=name), self.assertRaises(ValueError):
                assert_static_vercel_security(copy)

    def test_rights_and_original_score_remain_hold(self) -> None:
        panel = json.loads(RIGHTS_PATH.read_text(encoding="utf-8"))
        legacy = json.loads(SCORE_RIGHTS_PATH.read_text(encoding="utf-8"))
        rights = [value for src in panel["source_permissions"].values()
                  for value in src["rights"].values()]
        self.assertEqual(len(rights), 56)
        self.assertTrue(all(x is False for x in rights))
        self.assertEqual(len(panel["external_authorities"]), 14)
        self.assertTrue(all(v is False for v in panel["external_authorities"].values()))
        self.assertEqual(panel["publication_control"]["status"], "HOLD")
        self.assertEqual(legacy["state"], "hold")
        self.assertIsNone(legacy["decision_receipt"])

    def test_readme_separates_source_preparation_from_preview_approval(self) -> None:
        text = README_PATH.read_text(encoding="utf-8")
        for phrase in (
            "P3 static mock source", "P4", "NOT STARTED",
            "No JavaScript", "No remote", "SYNTHETIC_DO_NOT_PUBLISH",
            "prj_oQ3dGEvHmWRBMYAnQaRYIsY6URu1",
            "Do not", "Preview-only",
        ):
            self.assertIn(phrase.lower(), text.lower())
        self.assertNotIn("VERCEL_TOKEN=", text)
        self.assertNotIn("OPENAI_API_KEY=", text)


if __name__ == "__main__":
    unittest.main()
