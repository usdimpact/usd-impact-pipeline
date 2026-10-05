#!/usr/bin/env python3
"""Release-environment provenance verification.

Historical releases are anchored to the first protected Git commit that added
their dated reproduction bundle. A brand-new release candidate is instead
bound to the explicitly active online runtime profile. Candidate metadata alone
never establishes a historical trust anchor.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from scripts.execution_environment import verify_profile

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
TRUSTED_KEYS = {"week","publication_sha","generator_sha","trusted_base_sha","bundle_path","bundle_sha256","lock_path","lock_sha256"}


def _git_env() -> dict[str,str]:
    return {
        "PATH": os.environ.get("PATH","/usr/bin:/bin"),
        "GIT_CONFIG_NOSYSTEM":"1",
        "GIT_CONFIG_GLOBAL":os.devnull,
    }


def _git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(
        ["git","-c","core.useReplaceRefs=false",*args],
        cwd=root,
        stderr=subprocess.STDOUT,
        env=_git_env(),
    )


def _git_text(root: Path, *args: str) -> str:
    return _git(root, *args).decode("utf-8").strip()


def _safe_path(value: object) -> str:
    if not isinstance(value,str) or not value:
        raise ValueError("trusted path must be a safe relative path")
    p=Path(value)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError("trusted path must be a safe relative path")
    return value


def _regular_blob(root: Path, commit: str, path: str) -> bytes:
    if not SHA40.fullmatch(commit):
        raise ValueError("commit must be a full lowercase SHA")
    path=_safe_path(path)
    row=_git(root,"ls-tree",commit,"--",path).decode().strip().split()
    if len(row)<3 or row[0] not in {"100644","100755"} or row[1]!="blob":
        raise ValueError("trusted path is not an exact regular-file blob")
    return _git(root,"show",f"{commit}:{path}")


def _ancestor(root: Path, older: str, newer: str) -> None:
    try:
        subprocess.check_call(
            ["git","-c","core.useReplaceRefs=false","merge-base","--is-ancestor",older,newer],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=_git_env(),
        )
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"{older} is not an ancestor of {newer}") from exc


def verify_historical_release(root: Path, trusted: dict[str,Any]) -> dict[str,Any]:
    if set(trusted) != TRUSTED_KEYS:
        raise ValueError("trusted release fields differ from closed schema")
    for key in ("publication_sha","generator_sha","trusted_base_sha"):
        if not SHA40.fullmatch(str(trusted[key])):
            raise ValueError(f"{key} must be a full lowercase SHA")
    for key in ("bundle_sha256","lock_sha256"):
        if not SHA256.fullmatch(str(trusted[key])):
            raise ValueError(f"{key} must be lowercase SHA-256")
    _ancestor(root,trusted["generator_sha"],trusted["publication_sha"])
    _ancestor(root,trusted["publication_sha"],trusted["trusted_base_sha"])
    bundle_raw=_regular_blob(root,trusted["publication_sha"],trusted["bundle_path"])
    if hashlib.sha256(bundle_raw).hexdigest()!=trusted["bundle_sha256"]:
        raise ValueError("trusted bundle digest mismatch")
    bundle=json.loads(bundle_raw)
    if not isinstance(bundle,dict) or bundle.get("score_week")!=trusted["week"]:
        raise ValueError("trusted bundle week mismatch")
    if bundle.get("pipeline_git_sha")!=trusted["generator_sha"]:
        raise ValueError("trusted bundle generator SHA mismatch")
    if bundle.get("requirements_lock_sha256")!=trusted["lock_sha256"]:
        raise ValueError("trusted bundle lock digest mismatch")
    lock_raw=_regular_blob(root,trusted["generator_sha"],trusted["lock_path"])
    if hashlib.sha256(lock_raw).hexdigest()!=trusted["lock_sha256"]:
        raise ValueError("generator dependency lock digest mismatch")
    return {
        "status":"verified_historical_release_environment",
        "week":trusted["week"],
        "publication_sha":trusted["publication_sha"],
        "generator_sha":trusted["generator_sha"],
        "bundle_sha256":trusted["bundle_sha256"],
        "lock_sha256":trusted["lock_sha256"],
    }


def resolve_release_environment(root: Path, week: str) -> dict[str, Any]:
    root = root.resolve()
    archive_rel = f"public/archive/{week}/repro_bundle.json"

    # The offline frozen worker intentionally has no .git directory. Its root
    # dependency lock is itself part of the frozen engine identity.
    if not (root / ".git").exists():
        lock = root / "requirements.lock"
        return {
            "mode": "frozen_offline_worker",
            "lock_path": "requirements.lock",
            "lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
        }

    head = _git_text(root, "rev-parse", "HEAD")
    history = _git_text(root, "log", "--format=%H", "--reverse", "--", archive_rel)
    commits = [line for line in history.splitlines() if line]
    profile = verify_profile(root, root / "runtime/active-environment.json")

    rehearsal_override = os.environ.get("USD_IMPACT_REHEARSAL_ACTIVE_RUNTIME") == "1"
    if rehearsal_override:
        if os.environ.get("GITHUB_WORKFLOW") != "Score v2 reproduction acceptance rehearsal":
            raise ValueError("active-runtime rehearsal override is not authorized for this workflow")
        if os.environ.get("GITHUB_EVENT_NAME") not in {"pull_request", "workflow_dispatch"}:
            raise ValueError("active-runtime rehearsal override is not allowed in this event context")
        return {
            "mode": "active_runtime_rehearsal",
            "lock_path": profile["lock_path"],
            "lock_sha256": profile["lock_sha256"],
            "profile_id": profile["profile_id"],
        }

    # Before a new archive path is committed, or while validating the exact
    # commit that first introduces it, bind it to the active runtime candidate.
    if not commits or commits[0] == head:
        return {
            "mode": "active_runtime_candidate",
            "lock_path": profile["lock_path"],
            "lock_sha256": profile["lock_sha256"],
            "profile_id": profile["profile_id"],
        }

    publication_sha = commits[0]
    bundle_raw = _regular_blob(root, publication_sha, archive_rel)
    bundle = json.loads(bundle_raw)
    generator_sha = str(bundle.get("pipeline_git_sha", ""))
    lock_sha = str(bundle.get("requirements_lock_sha256", ""))
    trusted = {
        "week": week,
        "publication_sha": publication_sha,
        "generator_sha": generator_sha,
        "trusted_base_sha": head,
        "bundle_path": archive_rel,
        "bundle_sha256": hashlib.sha256(bundle_raw).hexdigest(),
        "lock_path": "requirements.lock",
        "lock_sha256": lock_sha,
    }
    verified = verify_historical_release(root, trusted)
    current_archive = root / archive_rel
    if not current_archive.is_file():
        raise ValueError("historical release archive is missing from current checkout")
    if hashlib.sha256(current_archive.read_bytes()).hexdigest() != verified["bundle_sha256"]:
        raise ValueError("historical release archive bytes differ from first publication")
    return {
        "mode": "historical_release",
        "lock_path": "requirements.lock",
        "lock_sha256": verified["lock_sha256"],
        "publication_sha": publication_sha,
        "generator_sha": verified["generator_sha"],
        "bundle_sha256": verified["bundle_sha256"],
    }
