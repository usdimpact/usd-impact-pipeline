#!/usr/bin/env python3
"""Read-only v10 recovery manifest validator and isolated synthetic Git restoration drill.

No BLS/PDF network request, no direct write to repository, no branch manipulation,
no publication or Production side effects. The optional drill mutates ONLY a
TemporaryDirectory containing an invented Git fixture, then deletes it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path("governance/score-v2-1f-wpu0561-v10-recovery-manifest.json")
V9_SHA = "0c420f495e6196d34d195d441edf7b707da4f35a"
V10_REVIEW_SHA = "698fb0c0d069c598909cc10e875a28cb711d1ea5"
EXPECTED_HOLD_FILES = {
    "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json",
    "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-v8-container-header-band-consumption-2026-10-29.json",
    "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json",
    "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json",
    "governance/score-publication-rights-gate.json",
    ".github/workflows/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight.yml",
}
ACTIVE_RECEIPT = Path("governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.json")
ACTIVE_DISPATCH = Path("governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-dispatch.json")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must be an object")
    return value


def git_blob_sha(data: bytes) -> str:
    prefix = b"blob " + str(len(data)).encode("ascii") + b"\x00"
    return hashlib.sha1(prefix + data).hexdigest()


def _git(root: Path, args: list[str]) -> str:
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if done.returncode:
        raise RuntimeError(f"local Git read/drill failed: {' '.join(args)}: {done.stderr[-400:]}")
    return done.stdout.strip()


def validate(root: Path | None = None, *, verify_git: bool = False) -> dict[str, Any]:
    root = (root or ROOT).resolve()
    manifest = _read_json(root / MANIFEST_PATH)
    if manifest.get("version") != 1 or manifest.get("state") != "design_only_recovery_hold":
        raise RuntimeError("recovery manifest must remain v1 and HOLD")
    if manifest.get("repository") != "usdimpact/usd-impact-pipeline":
        raise RuntimeError("unexpected repository")
    if manifest.get("owner_approval_scope") != "design_only_candidate_bls_pdf_methodology_and_offline_recovery_preparation":
        raise RuntimeError("recovery approval scope broadened")
    if manifest.get("source_boundary_change_authorized") is not False:
        raise RuntimeError("source change must be unauthorized")
    if manifest.get("live_bls_or_pdf_retrieval_authorized") is not False:
        raise RuntimeError("live data/PDF retrieval must be unauthorized")
    base = manifest.get("baseline", {})
    draft = manifest.get("review_snapshot", {})
    if base.get("immutable_commit") != V9_SHA:
        raise RuntimeError("v9 baseline commit changed")
    if base.get("reference_branch") != "backup/score-v2-1f-v9-hold-2026-10-29":
        raise RuntimeError("v9 backup reference changed")
    if draft.get("immutable_commit") != V10_REVIEW_SHA:
        raise RuntimeError("v10 draft snapshot changed")
    if draft.get("reference_branch") != "backup/score-v2-1f-v10-review-2026-10-29":
        raise RuntimeError("v10 backup reference changed")
    if manifest.get("recovery_procedure") != "new_reviewed_pr_never_direct_write_to_protected_main":
        raise RuntimeError("recovery must use a reviewed PR, never direct main reset")
    auth = manifest.get("authorizations", {})
    if not auth or any(value is not False for value in auth.values()):
        raise RuntimeError("all actual execution/recovery permissions must remain false")
    protected = manifest.get("governed_hold_blobs", {})
    if set(protected) != EXPECTED_HOLD_FILES:
        raise RuntimeError("frozen file inventory changed")

    for name, expected in protected.items():
        if not re.fullmatch(r"[0-9a-f]{40}", expected):
            raise RuntimeError("blob checksum is malformed")
        p = root / name
        if not p.is_file() or git_blob_sha(p.read_bytes()) != expected:
            raise RuntimeError(f"frozen v9 content changed: {name}")

    if (root / ACTIVE_RECEIPT).exists() or (root / ACTIVE_DISPATCH).exists():
        raise RuntimeError("an active receipt or dispatch marker is present")
    design = _read_json(root / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-design.json")
    contract = _read_json(root / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-execution-contract.json")
    template = _read_json(root / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight-authorization.template.json")
    consumption = _read_json(root / "governance/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-v8-container-header-band-consumption-2026-10-29.json")
    rights = _read_json(root / "governance/score-publication-rights-gate.json")
    workflow = (root / ".github/workflows/score-v2-1f-bls-wpu0561-ambiguity-diagnostics-preflight.yml").read_text(encoding="utf-8")

    if design.get("version") != 9 or design.get("state") != "design_only_hold":
        raise RuntimeError("v9 design not HOLD")
    if any(design.get("current_authorizations", {}).values()):
        raise RuntimeError("v9 design authorizations are active")
    if contract.get("version") != 21 or contract.get("state") != "ambiguity_diagnostics_v9_structural_feasibility_design_only_hold":
        raise RuntimeError("v9 execution contract changed")
    if any(contract.get("current_state", {}).values()) or contract.get("production_authorized") is not False:
        raise RuntimeError("execution contract authorization flags active")
    if template.get("decision_status") != "hold" or any(template.get("authorizations", {}).values()):
        raise RuntimeError("authorization template is not HOLD")
    if consumption.get("state") != "consumed_after_completed_v8_container_header_band_inventory":
        raise RuntimeError("v8 authorization no longer consumed")
    if rights.get("state") != "hold" or rights.get("decision_receipt") is not None:
        raise RuntimeError("independent rights hold changed")
    if "if: $" + "{{ false }}" not in workflow or "push:" in workflow:
        raise RuntimeError("old BLS workflow must stay inert and without push trigger")

    changed_files: list[str] = []
    if verify_git:
        if not (root / ".git").exists() and not (root / ".git").is_file():
            raise RuntimeError("git verification requires repository checkout")
        _git(root, ["cat-file", "-e", V9_SHA + "^{commit}"])
        _git(root, ["cat-file", "-e", V10_REVIEW_SHA + "^{commit}"])
        _git(root, ["merge-base", "--is-ancestor", V9_SHA, "HEAD"])
        for name, expected in protected.items():
            baseline_bytes = subprocess.run(
                ["git", "show", V9_SHA + ":" + name],
                cwd=root, capture_output=True, check=True
            ).stdout
            if git_blob_sha(baseline_bytes) != expected:
                raise RuntimeError(f"pinned v9 Git baseline mismatched: {name}")
        diff = _git(root, ["diff", "--name-only", V9_SHA, "HEAD", "--"])
        changed_files = sorted(filter(None, diff.splitlines()))
        allowed = set(manifest.get("allowlist_changed_paths", []))
        if not allowed or any(name not in allowed for name in changed_files):
            raise RuntimeError(f"out-of-scope files changed since v9: {sorted(set(changed_files) - allowed)}")
    return {
        "status": "passed",
        "state": manifest["state"],
        "baseline_commit": V9_SHA,
        "review_backup_commit": V10_REVIEW_SHA,
        "frozen_blob_count": len(protected),
        "active_authorization_receipt": False,
        "active_dispatch_marker": False,
        "rights_hold": True,
        "production_authorized": False,
        "source_boundary_change_authorized": False,
        "pdf_or_bls_network_used": False,
        "git_read_only_check": bool(verify_git),
        "changed_files": changed_files,
    }


def isolated_restore_drill() -> dict[str, Any]:
    """Exercise PR-style file recovery in a throwaway repo. No remote or original repo writes."""
    with tempfile.TemporaryDirectory(prefix="score-wpu0561-recovery-drill-") as directory:
        root = Path(directory)
        _git(root, ["init", "-q", "-b", "main"])
        _git(root, ["config", "user.name", "Recovery Drill"])
        _git(root, ["config", "user.email", "drill@example.invalid"])
        file = root / "governance" / "rights.json"
        file.parent.mkdir(parents=True)
        safe = '{"state":"hold","production_authorized":false}\n'
        file.write_text(safe, encoding="utf-8")
        _git(root, ["add", "--", "governance/rights.json"])
        _git(root, ["commit", "-qm", "synthetic HOLD baseline"])
        safe_commit = _git(root, ["rev-parse", "HEAD"])
        file.write_text('{"state":"activated","production_authorized":true}\n', encoding="utf-8")
        (root / "unrelated-notes.txt").write_text("retain unrelated document\n", encoding="utf-8")
        _git(root, ["add", "--", "governance/rights.json", "unrelated-notes.txt"])
        _git(root, ["commit", "-qm", "synthetic accidental change"])
        _git(root, ["switch", "-qc", "recovery-review-only"])
        _git(root, ["restore", "--source", safe_commit, "--", "governance/rights.json"])
        _git(root, ["add", "--", "governance/rights.json"])
        _git(root, ["commit", "-qm", "restore HOLD state via new reviewed branch"])
        if file.read_text(encoding="utf-8") != safe:
            raise RuntimeError("synthetic restoration did not recover HOLD")
        if (root / "unrelated-notes.txt").read_text(encoding="utf-8") != "retain unrelated document\n":
            raise RuntimeError("synthetic restoration clobbered unrelated work")
        if _git(root, ["branch", "--show-current"]) != "recovery-review-only":
            raise RuntimeError("synthetic recovery did not use an isolated review branch")
        return {
            "status": "passed",
            "scope": "throwaway_local_git_repository_only",
            "recovered_hold": True,
            "unrelated_changes_preserved": True,
            "force_push_used": False,
            "real_repository_or_production_changed": False,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-git", action="store_true", help="Read-only compare to pinned git baseline")
    parser.add_argument("--drill", action="store_true", help="Run isolated temporary synthetic Git recovery")
    args = parser.parse_args()
    response = {"guard": validate(verify_git=args.verify_git)}
    if args.drill:
        response["synthetic_drill"] = isolated_restore_drill()
    print(json.dumps(response, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
