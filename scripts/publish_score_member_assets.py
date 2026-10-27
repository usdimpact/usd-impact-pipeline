"""Publish premium Score HTML to the private Supabase member asset table.

This publisher never changes the public Cloudflare Pages output. It mirrors only
member HTML after the normal weekly release has been generated and validated.
Writes are fail-closed and require an explicit target, project ref, source commit,
and enable flag. Production additionally requires main + a separate approval flag.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PROJECT_RE = re.compile(r"^[a-z0-9]{20}$")
DATED_HTML_RE = re.compile(r"^public/archive/(\d{4}-\d{2}-\d{2})/(en|es)\.html$")
ROOT_ASSETS = {
    "public/en/index.html": "/en/",
    "public/es/index.html": "/es/",
    "public/archive/en/index.html": "/archive/en/",
    "public/archive/es/index.html": "/archive/es/",
}
DEVELOPMENT_PROJECT_REF = "ycstrcvshdluovtuasjc"


class PublicationError(RuntimeError):
    pass


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def member_path(relative_path: str) -> str | None:
    if relative_path in ROOT_ASSETS:
        return ROOT_ASSETS[relative_path]
    match = DATED_HTML_RE.fullmatch(relative_path)
    if not match:
        return None
    week, language = match.groups()
    return f"/archive/{week}/{language}.html"


def collect_assets(root: Path, source_commit: str) -> list[dict[str, str]]:
    if not SHA_RE.fullmatch(source_commit):
        raise PublicationError("source commit must be a full 40-character lowercase Git SHA")

    candidates = [root / path for path in ROOT_ASSETS]
    archive = root / "public" / "archive"
    if archive.exists():
        candidates.extend(sorted(archive.glob("????-??-??/*.html")))

    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for path in sorted(set(candidates)):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        target = member_path(relative)
        if target is None:
            continue
        if target in seen:
            raise PublicationError(f"duplicate member path: {target}")
        data = path.read_bytes()
        try:
            body = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PublicationError(f"member HTML is not UTF-8: {relative}") from exc
        if "<!doctype html" not in body[:200].lower():
            raise PublicationError(f"member asset is not HTML: {relative}")
        if "<script" in body.lower():
            raise PublicationError(f"member asset contains script markup: {relative}")
        rows.append({
            "path": target,
            "content_type": "text/html; charset=utf-8",
            "body": body,
            "source_commit": source_commit,
            "source_sha": git_blob_sha(data),
        })
        seen.add(target)

    for required in ROOT_ASSETS.values():
        if required not in seen:
            raise PublicationError(f"required member asset missing: {required}")
    if len(rows) < 4:
        raise PublicationError("member asset set is unexpectedly small")
    return rows


def validate_destination(*, target: str, project_ref: str, url: str) -> str:
    if not PROJECT_RE.fullmatch(project_ref):
        raise PublicationError("invalid Supabase project ref")
    parsed = urllib.parse.urlparse(url)
    expected_host = f"{project_ref}.supabase.co"
    if (
        parsed.scheme != "https"
        or parsed.hostname != expected_host
        or parsed.port is not None
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise PublicationError("Supabase URL does not match the explicitly selected project ref")

    if target == "development":
        if project_ref != DEVELOPMENT_PROJECT_REF:
            raise PublicationError("Development publishing is pinned to the isolated Development project")
    elif target == "production":
        if os.environ.get("GITHUB_REF") != "refs/heads/main":
            raise PublicationError("Production publishing is allowed only from main")
        if os.environ.get("SCORE_MEMBER_ASSET_PRODUCTION_APPROVED") != "true":
            raise PublicationError("Production publishing requires separate explicit approval")
    else:
        raise PublicationError("unsupported publish target")
    return f"https://{expected_host}"


def publish_batch(*, origin: str, secret_key: str, rows: list[dict[str, str]]) -> None:
    if not re.fullmatch(r"sb_secret_[A-Za-z0-9_-]{16,}", secret_key):
        raise PublicationError("Supabase secret key is missing or malformed")
    endpoint = origin + "/rest/v1/score_member_assets?on_conflict=path"
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        method="POST",
        headers={
            "apikey": secret_key,
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
            "Cache-Control": "no-store",
            "User-Agent": "usd-impact-score-member-assets/1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status not in (200, 201, 204):
                raise PublicationError(f"Supabase member asset upsert returned HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        raise PublicationError(f"Supabase member asset upsert returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise PublicationError("Supabase member asset upsert could not connect") from exc


def publish_assets(*, origin: str, secret_key: str, rows: list[dict[str, str]], batch_size: int = 10) -> None:
    if batch_size < 1 or batch_size > 25:
        raise PublicationError("batch size must be between 1 and 25")
    for start in range(0, len(rows), batch_size):
        publish_batch(origin=origin, secret_key=secret_key, rows=rows[start:start + batch_size])


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--source-commit", required=True)
    p.add_argument("--target", choices=("development", "production"), required=True)
    p.add_argument("--project-ref", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--batch-size", type=int, default=10)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    rows = collect_assets(Path(args.root).resolve(), args.source_commit)
    url = os.environ.get("SUPABASE_URL", "")
    if args.dry_run and not url:
        url = f"https://{args.project_ref}.supabase.co"
    origin = validate_destination(target=args.target, project_ref=args.project_ref, url=url)

    summary = {
        "target": args.target,
        "project_ref": args.project_ref,
        "source_commit": args.source_commit,
        "asset_count": len(rows),
        "paths": [row["path"] for row in rows],
        "dry_run": args.dry_run,
    }
    if args.dry_run:
        print(json.dumps(summary, sort_keys=True))
        return 0

    if os.environ.get("SCORE_MEMBER_ASSET_PUBLISH_ENABLED") != "true":
        raise PublicationError("member asset publishing is disabled")

    publish_assets(
        origin=origin,
        secret_key=os.environ.get("SUPABASE_SECRET_KEY", ""),
        rows=rows,
        batch_size=args.batch_size,
    )
    print(json.dumps({**summary, "published": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PublicationError as exc:
        print(f"score member asset publication blocked: {exc}", file=sys.stderr)
        raise SystemExit(2)
