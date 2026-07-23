#!/usr/bin/env python3
"""Rebuild dashboard HTML after commentary files have been generated."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from usd_impact_score_v2 import build_graphic_payload, export_html, setup_logging  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    frame = pd.read_csv(args.csv, parse_dates=["date"]).set_index("date")
    if "score" not in frame.columns or "regime" not in frame.columns:
        raise ValueError("Pipeline CSV is missing score or regime columns.")

    score = frame["score"]
    logger = setup_logging(Path("logs"))
    en_path = args.output_dir / "en" / "index.html"
    es_path = args.output_dir / "es" / "index.html"
    en_path.parent.mkdir(parents=True, exist_ok=True)
    es_path.parent.mkdir(parents=True, exist_ok=True)

    export_html(build_graphic_payload(frame, score, lang="en"), en_path, logger)
    export_html(build_graphic_payload(frame, score, lang="es"), es_path, logger)
    print("Rebuilt English and Spanish dashboards with current commentary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
