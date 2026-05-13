#!/usr/bin/env python3
"""Export weekly USD Impact pipeline data into usd-impact weekly input JSON format."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_ASSETS = [
    "WTI Crude Oil",
    "LNG / Natural Gas",
    "Gold / XAUUSD",
    "Bitcoin / BTCUSD",
    "DXY",
    "EURUSD",
    "Mag 7 Equities",
]


DEFAULT_SOURCES = [
    "https://www.eia.gov/",
    "https://www.investing.com/",
    "https://www.tradingview.com/",
]


def build_asset(asset_name: str) -> dict:
    return {
        "asset_name": asset_name,
        "what_changed": f"{asset_name} remained sensitive to the week’s dominant macro drivers.",
        "why_it_matters": f"{asset_name} can be affected by USD direction, rates, liquidity, risk sentiment, and asset-specific fundamentals.",
        "analyst_comment": f"The educational point is to understand which driver mattered most for {asset_name} this week.",
        "portfolio_discussion_context": f"{asset_name} can be discussed from a risk, volatility, diversification, and time-horizon perspective.",
        "watchpoints": [
            "USD direction",
            "real-rate expectations",
            "liquidity conditions",
            "risk sentiment",
            "asset-specific news",
        ],
        "risk_to_interpretation": f"The interpretation could change if macro conditions or asset-specific fundamentals shift.",
        "sources": DEFAULT_SOURCES,
    }


def export_weekly_input(week_ending: str, output_path: Path) -> None:
    data = {
        "week_ending": week_ending,
        "educational_summary": "This week’s market discussion is centered on the interaction between USD direction, real-rate expectations, liquidity conditions, and cross-asset risk sentiment.",
        "dominant_macro_driver": "USD direction, real-rate expectations, and liquidity conditions",
        "dominant_driver_why_it_matters": "These drivers can influence commodities, precious metals, FX pairs, equity valuation sensitivity, and liquidity-sensitive assets.",
        "assets": [build_asset(asset) for asset in DEFAULT_ASSETS],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Exported weekly input: {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export weekly input JSON for usd-impact.")
    parser.add_argument("--week-ending", required=True, help="Week ending date in YYYY-MM-DD format.")
    parser.add_argument("--output", required=True, type=Path, help="Output JSON path.")
    args = parser.parse_args()

    export_weekly_input(args.week_ending, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
