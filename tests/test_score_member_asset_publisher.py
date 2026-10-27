from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.publish_score_member_assets import (
    DEVELOPMENT_PROJECT_REF,
    PublicationError,
    collect_assets,
    git_blob_sha,
    member_path,
    publish_batch,
    validate_destination,
)


class ScoreMemberAssetPublisherTests(unittest.TestCase):
    def make_tree(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        files = {
            "public/en/index.html": "<!doctype html><title>EN</title>",
            "public/es/index.html": "<!doctype html><title>ES</title>",
            "public/archive/en/index.html": '<!doctype html><a href="/archive/2026-10-16/en.html">EN archive</a>',
            "public/archive/es/index.html": '<!doctype html><a href="/archive/2026-10-16/es.html">ES archive</a>',
            "public/archive/2026-10-16/en.html": "<!doctype html><title>Dated EN</title>",
            "public/archive/2026-10-16/es.html": "<!doctype html><title>Dated ES</title>",
            "public/data/public.json": "{}",
        }
        for relative, body in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        return tmp, root

    def test_git_blob_sha_matches_git_object_format(self):
        data = b"hello\n"
        expected = hashlib.sha1(b"blob 6\0hello\n").hexdigest()
        self.assertEqual(git_blob_sha(data), expected)

    def test_member_path_accepts_only_premium_html(self):
        self.assertEqual(member_path("public/en/index.html"), "/en/")
        self.assertEqual(member_path("public/es/index.html"), "/es/")
        self.assertEqual(member_path("public/archive/en/index.html"), "/archive/en/")
        self.assertEqual(
            member_path("public/archive/2026-10-16/es.html"),
            "/archive/2026-10-16/es.html",
        )
        self.assertIsNone(member_path("public/data/usd_impact_score_v2.json"))
        self.assertIsNone(member_path("public/archive/2026-10-16/weekly_input.json"))

    def test_collect_assets_is_bounded_script_free_and_provenanced(self):
        tmp, root = self.make_tree()
        self.addCleanup(tmp.cleanup)
        commit = "a" * 40
        rows = collect_assets(root, commit)
        self.assertEqual(len(rows), 6)
        self.assertEqual({r["path"] for r in rows}, {
            "/en/", "/es/", "/archive/en/", "/archive/es/",
            "/archive/2026-10-16/en.html", "/archive/2026-10-16/es.html",
        })
        for row in rows:
            self.assertEqual(row["source_commit"], commit)
            self.assertRegex(row["source_sha"], r"^[0-9a-f]{40}$")
            self.assertEqual(row["content_type"], "text/html; charset=utf-8")

    def test_collect_assets_rejects_script_markup(self):
        tmp, root = self.make_tree()
        self.addCleanup(tmp.cleanup)
        (root / "public/en/index.html").write_text(
            "<!doctype html><script>alert(1)</script>", encoding="utf-8"
        )
        with self.assertRaisesRegex(PublicationError, "script markup"):
            collect_assets(root, "a" * 40)

    def test_development_destination_is_pinned(self):
        url = f"https://{DEVELOPMENT_PROJECT_REF}.supabase.co"
        self.assertEqual(
            validate_destination(
                target="development",
                project_ref=DEVELOPMENT_PROJECT_REF,
                url=url,
            ),
            url,
        )
        with self.assertRaisesRegex(PublicationError, "pinned"):
            validate_destination(
                target="development",
                project_ref="a" * 20,
                url="https://" + ("a" * 20) + ".supabase.co",
            )

    def test_production_destination_requires_main_and_explicit_approval(self):
        ref = "b" * 20
        url = f"https://{ref}.supabase.co"
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(PublicationError, "only from main"):
                validate_destination(target="production", project_ref=ref, url=url)
        with mock.patch.dict(os.environ, {"GITHUB_REF": "refs/heads/main"}, clear=True):
            with self.assertRaisesRegex(PublicationError, "separate explicit approval"):
                validate_destination(target="production", project_ref=ref, url=url)
        with mock.patch.dict(os.environ, {
            "GITHUB_REF": "refs/heads/main",
            "SCORE_MEMBER_ASSET_PRODUCTION_APPROVED": "true",
        }, clear=True):
            self.assertEqual(
                validate_destination(target="production", project_ref=ref, url=url),
                url,
            )

    def test_publish_batch_uses_secret_only_as_request_header(self):
        row = {
            "path": "/en/",
            "content_type": "text/html; charset=utf-8",
            "body": "<!doctype html>",
            "source_commit": "a" * 40,
            "source_sha": "b" * 40,
        }
        response = mock.MagicMock()
        response.__enter__.return_value.status = 201
        response.__exit__.return_value = False
        with mock.patch("urllib.request.urlopen", return_value=response) as opened:
            publish_batch(
                origin="https://example.supabase.co",
                secret_key="sb_secret_" + "x" * 32,
                rows=[row],
            )
        request = opened.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertIn("on_conflict=path", request.full_url)
        self.assertNotIn("sb_secret_", request.full_url)
        self.assertEqual(request.headers["Apikey"], "sb_secret_" + "x" * 32)
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload[0]["path"], "/en/")


if __name__ == "__main__":
    unittest.main()
