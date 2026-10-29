#!/usr/bin/env python3
"""Optional rights-checked launcher for the *frozen* original Score CLI.

Do not alter the pre-holdout engine or its reproduction builder: both are
byte-for-byte pinned by the Score v3 research lock.  This launcher is the
supported manual route; it cannot prevent arbitrary direct Python imports or
calls to the immutable legacy files.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from scripts.score_publication_rights_gate import require_score_provider_rights


REPO_ROOT = Path(__file__).resolve().parent.parent
COMMANDS = {
    "score": ("-m", "usd_impact_score_v2"),
    "repro": ("-m", "scripts.build_score_repro_bundle"),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rights-checked manual launcher for frozen Score v2 programs"
    )
    parser.add_argument("operation", choices=sorted(COMMANDS))
    args, forwarded = parser.parse_known_args(argv)
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]

    # First operation after parsing: no source cache, provider payload, log,
    # input Score JSON, temporary file or subprocess can be opened under HOLD.
    try:
        require_score_provider_rights()
    except PermissionError as error:
        print(str(error), file=sys.stderr)
        return 3

    # A future reviewed rights v2 protocol must clear the canonical gate
    # before this branch can become reachable.  Avoid shell interpolation.
    command = [sys.executable, *COMMANDS[args.operation], *forwarded]
    return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
