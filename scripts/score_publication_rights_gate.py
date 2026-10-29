#!/usr/bin/env python3
"""Fail-closed read-only gate for Score public publication workflows.

The gate does not fetch providers, write repository data, dispatch workflows, or
change Production. It reads one reviewed repository policy file and emits a
boolean hold decision for workflow conditions.

Malformed, missing or unrecognized policy is HOLD.
The v1 ALLOW shape (a name and a syntactically valid GitHub URL) cannot
establish actual upstream data rights, seven-source decisions, public schema
approval or separate Production authorization. For v1, ALL ALLOW policies
therefore fail closed until a separately reviewed release protocol exists.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DEFAULT_POLICY = Path("governance/score-publication-rights-gate.json")
ALLOWED_SCOPE = {
    "weekly_score_publication_generation",
    "weekly_recovery_dispatch",
    "scheduled_research_publication_generation",
}
REQUIRED_RESUME = {
    "provider_or_counsel_disposition",
    "approved_public_artifact_schema",
    "approved_private_evidence_boundary_or_explicit_permission",
    "separate_production_authorization",
}
ISSUE_URL = "https://github.com/usdimpact/usd-impact-pipeline/issues/155"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISSUE_COMMENT_RE = re.compile(r"^issuecomment-\d+$")
COMMENTABLE_PATH_RE = re.compile(r"^/usdimpact/usd-impact-pipeline/(?:issues|pull)/\d+$")


def _https_github_url(value: Any) -> bool:
    if not isinstance(value, str) or len(value) > 2048:
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    fragment_ok = (
        not parsed.fragment
        or (
            bool(COMMENTABLE_PATH_RE.fullmatch(parsed.path))
            and bool(ISSUE_COMMENT_RE.fullmatch(parsed.fragment))
        )
    )
    return (
        parsed.scheme == "https"
        and parsed.hostname == "github.com"
        and not parsed.username
        and not parsed.password
        and fragment_ok
        and parsed.path.startswith("/usdimpact/usd-impact-pipeline/")
    )


def evaluate_policy(raw: Any) -> dict[str, Any]:
    fallback = {
        "hold": True,
        "state": "invalid",
        "reason": "missing-or-invalid-rights-policy",
        "issue": ISSUE_URL,
        "decision_receipt": None,
    }
    if not isinstance(raw, dict):
        return fallback

    expected = {
        "version",
        "state",
        "effective_date",
        "issue",
        "reason",
        "scope",
        "resume_requires",
        "decision_receipt",
        "approved_by",
    }
    if set(raw) != expected:
        return {**fallback, "reason": "unexpected-rights-policy-fields"}
    if raw.get("version") != 1:
        return {**fallback, "reason": "unsupported-rights-policy-version"}
    if raw.get("issue") != ISSUE_URL:
        return {**fallback, "reason": "unexpected-rights-policy-issue"}
    if not isinstance(raw.get("reason"), str) or not raw["reason"].strip():
        return {**fallback, "reason": "missing-rights-policy-reason"}
    if not isinstance(raw.get("effective_date"), str) or not DATE_RE.fullmatch(raw["effective_date"]):
        return {**fallback, "reason": "invalid-rights-policy-date"}

    scope = raw.get("scope")
    if not isinstance(scope, list) or set(scope) != ALLOWED_SCOPE or len(scope) != len(ALLOWED_SCOPE):
        return {**fallback, "reason": "invalid-rights-policy-scope"}
    resume = raw.get("resume_requires")
    if not isinstance(resume, list) or set(resume) != REQUIRED_RESUME or len(resume) != len(REQUIRED_RESUME):
        return {**fallback, "reason": "invalid-rights-policy-resume-requirements"}

    state = raw.get("state")
    if state == "hold":
        if raw.get("decision_receipt") is not None or raw.get("approved_by") is not None:
            return {**fallback, "reason": "hold-policy-must-not-carry-approval"}
        return {
            "hold": True,
            "state": "hold",
            "reason": raw["reason"].strip(),
            "issue": ISSUE_URL,
            "decision_receipt": None,
        }

    if state == "allow":
        approver = raw.get("approved_by")
        receipt = raw.get("decision_receipt")
        if not isinstance(approver, str) or len(approver.strip()) < 3:
            return {**fallback, "reason": "allow-policy-missing-approver"}
        if not _https_github_url(receipt):
            return {**fallback, "reason": "allow-policy-missing-valid-decision-receipt"}
        # A GitHub reference is audit metadata, not independently verified
        # source rights or a Production approval. This v1 protocol may never
        # reopen rights-gated provider retrieval or publication. A future v2
        # requires an explicitly reviewed evidence and release protocol.
        return {
            **fallback,
            "reason": "v1-allow-not-an-authorized-rights-release-contract",
        }

    return {**fallback, "reason": "unknown-rights-policy-state"}


def load_policy(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return evaluate_policy(None)
    return evaluate_policy(raw)


# A direct Python invocation need not originate from GitHub Actions, and
# may run from a different current working directory. Never read a relative
# caller-supplied policy for provider access.
CANONICAL_REPOSITORY_POLICY = Path(__file__).resolve().parent.parent / DEFAULT_POLICY


def require_score_provider_rights() -> None:
    """Reject provider-consuming entrypoints unless the reviewed rights gate clears.

    This intentionally uses the same canonical evaluation as the existing
    Actions workflow. The current v1 gate cannot authorize any provider
    retrieval, even with a plausible GitHub receipt or an 'allow' state.
    A future v2 clearance requires its own reviewed, separate implementation.
    No network requests or output files are created by this check.
    """
    decision = load_policy(CANONICAL_REPOSITORY_POLICY)
    if decision.get("hold") is not False:
        raise PermissionError(
            "USD Impact Score provider operations are on rights HOLD. "
            "No provider retrieval or retained real-data processing is permitted. "
            f"Review {ISSUE_URL}."
        )


def write_github_output(result: dict[str, Any], path: Path) -> None:
    lines = [
        f"hold={'true' if result['hold'] else 'false'}",
        f"state={result['state']}",
        f"reason={str(result['reason']).replace(chr(10), ' ').replace(chr(13), ' ')}",
        f"issue={result['issue']}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    result = load_policy(args.policy)
    if args.github_output:
        write_github_output(result, args.github_output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
