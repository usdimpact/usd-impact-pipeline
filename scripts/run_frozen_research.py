#!/usr/bin/env python3
"""Run frozen prospective research inside a bounded offline container.

Host mode downloads binary wheels as inert artifacts, records their hashes,
builds from a pinned Python image with network disabled for installation, and
launches the frozen engine with no runtime network. Inside mode is a closed
dispatcher for the two preregistered prospective workflows; arbitrary commands
are never accepted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "runtime/frozen-research-wheelhouse.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
V3_ALLOWED = [
    re.compile(r"^research/score_v3_prospective_manifest\.json$"),
    re.compile(r"^research/prospective/score_v3_shadow_[0-9]{4}-[0-9]{2}-[0-9]{2}\.json$"),
    re.compile(r"^research/prospective/checkpoints/score_v3_checkpoint_(013|026|039|052)\.json$"),
]
V2_ALLOWED = [
    re.compile(r"^research/score_v2_predictive_manifest\.json$"),
    re.compile(r"^research/predictive/score_v2_predictive_week_[0-9]{4}-[0-9]{2}-[0-9]{2}\.json$"),
    re.compile(r"^research/predictive/checkpoints/score_v2_predictive_checkpoint_(013|026|039|052)\.json$"),
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "schema_version","status","source_lock","source_lock_sha256",
        "downloader_lock","base_image","platform","download_policy","runtime_boundary",
    }
    if not isinstance(data, dict) or set(data) != expected:
        raise ValueError("frozen research policy fields differ from closed schema")
    if data["schema_version"] != 1 or data["status"] != "generated_per_run":
        raise ValueError("unsupported frozen research policy")
    if not SHA256.fullmatch(str(data["source_lock_sha256"])):
        raise ValueError("source lock digest is invalid")
    if data["download_policy"] != {
        "only_binary": True,
        "no_source_builds": True,
        "wheel_hashes_retained": True,
    }:
        raise ValueError("frozen wheel download policy was weakened")
    boundary = data["runtime_boundary"]
    if boundary != {
        "network": "none",
        "read_only_root": True,
        "drop_all_capabilities": True,
        "no_new_privileges": True,
        "non_root_uid": 65532,
    }:
        raise ValueError("frozen runtime boundary was weakened")
    return data


def docker_run_args(image: str, output_dir: Path, mode: str, attestation_id: str, attestation_url: str) -> list[str]:
    if mode not in {"score-v3-shadow", "score-v2-predictive"}:
        raise ValueError("unsupported frozen research mode")
    return [
        "docker","run","--rm",
        "--network","none",
        "--read-only",
        "--cap-drop","ALL",
        "--security-opt","no-new-privileges",
        "--pids-limit","256",
        "--memory","2g",
        "--cpus","2",
        "--tmpfs","/work:rw,nosuid,nodev,size=1024m,uid=65532,mode=0700",
        "--mount",f"type=bind,src={output_dir.resolve()},dst=/output",
        image,
        "--inside-mode",mode,
        "--attestation-run-id",attestation_id,
        "--attestation-url",attestation_url,
    ]


def _copy_repo_for_build(source: Path, destination: Path) -> None:
    ignored = shutil.ignore_patterns(".git", ".venv", "__pycache__", "*.pyc")
    shutil.copytree(source, destination, ignore=ignored, symlinks=False)


def _wheel_manifest(wheelhouse: Path, policy: dict[str, Any]) -> dict[str, Any]:
    wheels = []
    for path in sorted(wheelhouse.glob("*.whl")):
        wheels.append({"file": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    if not wheels:
        raise RuntimeError("binary wheelhouse is empty")
    return {
        "schema_version": 1,
        "source_lock": policy["source_lock"],
        "source_lock_sha256": policy["source_lock_sha256"],
        "base_image": policy["base_image"],
        "platform": policy["platform"],
        "wheels": wheels,
    }


def _run_host(args: argparse.Namespace) -> int:
    policy = load_policy()
    source_lock = ROOT / policy["source_lock"]
    if source_lock.is_symlink() or not source_lock.is_file():
        raise RuntimeError("frozen source lock must be a regular file")
    if sha256_file(source_lock) != policy["source_lock_sha256"]:
        raise RuntimeError("frozen source lock digest drifted")

    downloader_lock = ROOT / policy["downloader_lock"]
    if not downloader_lock.is_file():
        raise RuntimeError("patched downloader lock is missing")

    subprocess.check_call(["docker","version"], stdout=subprocess.DEVNULL)
    with tempfile.TemporaryDirectory(prefix="usd-impact-frozen-research-") as td:
        temp = Path(td)
        wheelhouse = temp / "wheelhouse"
        wheelhouse.mkdir()
        subprocess.check_call([
            sys.executable,"-m","pip","download",
            "--disable-pip-version-check",
            "--only-binary=:all:",
            "--dest",str(wheelhouse),
            "--requirement",str(source_lock),
        ])
        manifest = _wheel_manifest(wheelhouse, policy)
        args.wheelhouse_report.parent.mkdir(parents=True, exist_ok=True)
        args.wheelhouse_report.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        context = temp / "context"
        context.mkdir()
        shutil.copy2(source_lock, context / "requirements.lock")
        shutil.copytree(wheelhouse, context / "wheelhouse")
        _copy_repo_for_build(ROOT, context / "repo")
        dockerfile = ROOT / "runtime/research-worker.Dockerfile"
        shutil.copy2(dockerfile, context / "Dockerfile")

        image = f"usd-impact-frozen-research:{os.getpid()}"
        subprocess.check_call(["docker","pull",policy["base_image"]])
        subprocess.check_call([
            "docker","build","--network=none","--pull=false",
            "--file",str(context / "Dockerfile"),
            "--tag",image,
            str(context),
        ])

        output = temp / "output"
        output.mkdir()
        output.chmod(stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        subprocess.check_call(
            docker_run_args(
                image, output, args.mode, args.attestation_run_id, args.attestation_url
            )
        )

        allowed_top = {"research", "reports"}
        unknown = [p.name for p in output.iterdir() if p.name not in allowed_top]
        if unknown:
            raise RuntimeError(f"offline worker emitted unexpected top-level outputs: {unknown}")

        research_out = output / "research"
        if research_out.exists():
            for path in research_out.rglob("*"):
                if not path.is_file():
                    continue
                rel = path.relative_to(research_out)
                target = ROOT / "research" / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)

        reports = output / "reports"
        report_map = {
            "ingest.json": args.ingest_report,
            "governance.json": args.governance_report,
        }
        for name, destination in report_map.items():
            src = reports / name
            if not src.is_file():
                raise RuntimeError(f"offline worker did not emit required report {name}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, destination)

        subprocess.call(["docker","image","rm","--force",image], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return 0


def _run_checked(cwd: Path, cmd: list[str]) -> None:
    env = {
        "PATH": os.environ.get("PATH","/usr/local/bin:/usr/bin:/bin"),
        "HOME": "/work/home",
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
    }
    subprocess.check_call(cmd, cwd=cwd, env=env)


def _file_map(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    research = root / "research"
    if not research.exists():
        return result
    for path in research.rglob("*"):
        if path.is_file():
            result[path.relative_to(root).as_posix()] = sha256_file(path)
    return result


def _allowed(path: str, mode: str) -> bool:
    patterns = V3_ALLOWED if mode == "score-v3-shadow" else V2_ALLOWED
    return any(pattern.fullmatch(path) for pattern in patterns)


def _run_inside(args: argparse.Namespace) -> int:
    if os.geteuid() == 0:
        raise RuntimeError("frozen research worker must not run as root")
    source = Path("/app")
    work = Path("/work/repo")
    output = Path("/output")
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(source, work, symlinks=False)
    before = _file_map(work)

    _run_checked(work, [sys.executable,"-m","scripts.validate_methodology_contract","--json"])
    _run_checked(work, [sys.executable,"scripts/validate_weekly_release.py"])

    reports = output / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    if args.inside_mode == "score-v3-shadow":
        _run_checked(work, [sys.executable,"-m","scripts.verify_score_v3_engine_lock","--filesystem-only","--json"])
        _run_checked(work, [
            sys.executable,"-m","scripts.score_v3_shadow_ingestion",
            "--attestation-run-id",args.attestation_run_id,
            "--attestation-url",args.attestation_url,
            "--report",str(reports / "ingest.json"),
        ])
        _run_checked(work, [
            sys.executable,"-m","scripts.score_v3_metric_reporting",
            "--report",str(reports / "governance.json"),
        ])
    elif args.inside_mode == "score-v2-predictive":
        _run_checked(work, [sys.executable,"-m","scripts.verify_score_v2_predictive_engine_lock","--filesystem-only","--json"])
        _run_checked(work, [
            sys.executable,"-m","scripts.score_v2_predictive_ingestion",
            "--attestation-run-id",args.attestation_run_id,
            "--attestation-url",args.attestation_url,
            "--report",str(reports / "ingest.json"),
        ])
        _run_checked(work, [
            sys.executable,"-m","scripts.score_v2_predictive_reporting",
            "--mode","run",
            "--report",str(reports / "governance.json"),
        ])
    else:
        raise RuntimeError("unsupported inside mode")

    after = _file_map(work)
    changed = sorted(path for path, digest in after.items() if before.get(path) != digest)
    deleted = sorted(path for path in before if path not in after)
    if deleted:
        raise RuntimeError(f"frozen research attempted deletions: {deleted}")
    unexpected = [path for path in changed if not _allowed(path, args.inside_mode)]
    if unexpected:
        raise RuntimeError(f"frozen research changed unexpected paths: {unexpected}")

    research_out = output / "research"
    for rel in changed:
        src = work / rel
        dst = research_out / Path(rel).relative_to("research")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["score-v3-shadow","score-v2-predictive"])
    parser.add_argument("--inside-mode", choices=["score-v3-shadow","score-v2-predictive"])
    parser.add_argument("--attestation-run-id", required=True)
    parser.add_argument("--attestation-url", required=True)
    parser.add_argument("--ingest-report", type=Path)
    parser.add_argument("--governance-report", type=Path)
    parser.add_argument("--wheelhouse-report", type=Path)
    args = parser.parse_args()

    if args.inside_mode:
        return _run_inside(args)
    if not args.mode or not args.ingest_report or not args.governance_report or not args.wheelhouse_report:
        parser.error("host mode requires --mode and all report paths")
    return _run_host(args)


if __name__ == "__main__":
    raise SystemExit(main())
