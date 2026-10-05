#!/usr/bin/env python3
"""Phase A proof for historical release dependency provenance.

Trust facts are supplied by a future independently governed resolver. Candidate-controlled
bundle fields can be checked against trust facts but cannot establish them.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
TRUSTED_KEYS = {"week","publication_sha","generator_sha","trusted_base_sha","bundle_path","bundle_sha256","lock_path","lock_sha256"}


def _git_env() -> dict[str,str]:
    return {"PATH": os.environ.get("PATH","/usr/bin:/bin"),"GIT_CONFIG_NOSYSTEM":"1","GIT_CONFIG_GLOBAL":os.devnull}


def _git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git","-c","core.useReplaceRefs=false",*args],cwd=root,stderr=subprocess.STDOUT,env=_git_env())


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
        subprocess.check_call(["git","-c","core.useReplaceRefs=false","merge-base","--is-ancestor",older,newer],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=_git_env())
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
    return {"status":"verified_historical_release_environment","week":trusted["week"],"publication_sha":trusted["publication_sha"],"generator_sha":trusted["generator_sha"],"bundle_sha256":trusted["bundle_sha256"],"lock_sha256":trusted["lock_sha256"]}
