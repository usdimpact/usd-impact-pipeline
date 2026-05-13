#!/usr/bin/env python3
"""Export weekly USD Impact pipeline data into usd-impact weekly input JSON format."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ASSET_CONFIG = {
    "WTI Crude Oil": {
        "what_changed": "WTI should be reviewed through inventory expectations, demand signals, USD direction, refinery conditions, OPEC+ policy, and geopolitical risk.",
        "why_it_matters": "Oil is influenced by both macro forces and physical-market fundamentals. The USD matters, but inventories, refinery demand, supply disruptions, and OPEC+ policy can dominate short-term price behavior.",
        "analyst_comment": "The educational point is that oil is not only a currency story. When physical supply risk changes, WTI can move independently of normal USD correlations.",
        "portfolio_discussion_context": "WTI can be discussed as a macro-sensitive and supply-sensitive commodity relevant to inflation exposure, energy costs, cyclical demand, and geopolitical-risk analysis.",
        "watchpoints": ["EIA weekly petroleum inventories", "OPEC+ guidance", "refinery utilization", "USD direction", "global demand indicators", "geopolitical chokepoints"],
        "risk_to_interpretation": "Weaker demand, higher inventories, diplomatic de-escalation, a stronger USD, or unexpected supply increases could change the interpretation.",
        "sources": ["https://www.eia.gov/petroleum/supply/weekly/", "https://www.cmegroup.com/markets/energy/crude-oil/light-sweet-crude.html", "https://www.investing.com/commodities/crude-oil-news"],
    },
    "LNG / Natural Gas": {
        "what_changed": "LNG and natural gas should be reviewed through storage, weather, production, export flows, regional benchmarks, and infrastructure conditions.",
        "why_it_matters": "Gas markets are highly regional. Storage, weather, pipeline flows, LNG export capacity, terminal outages, and regional pricing can matter more than broad macro trends.",
        "analyst_comment": "The educational point is that gas markets can disconnect from oil and broad commodity narratives when local storage, weather, or infrastructure constraints dominate.",
        "portfolio_discussion_context": "LNG and natural gas can be discussed as high-volatility energy markets with strong regional, seasonal, infrastructure, and geopolitical drivers.",
        "watchpoints": ["EIA natural gas storage", "weather models", "LNG export volumes", "TTF and JKM benchmarks", "pipeline and terminal disruptions", "production trends"],
        "risk_to_interpretation": "Milder weather, high storage, stronger production, weak industrial demand, or lower LNG export flows could change the interpretation.",
        "sources": ["https://www.eia.gov/naturalgas/storage/", "https://www.eia.gov/naturalgas/weekly/", "https://tradingeconomics.com/commodity/natural-gas"],
    },
    "Gold / XAUUSD": {
        "what_changed": "Gold should be reviewed through real-rate expectations, USD direction, ETF flows, central-bank demand, inflation data, and geopolitical risk.",
        "why_it_matters": "Gold is often influenced by real yields, the U.S. dollar, safe-haven demand, central-bank activity, ETF flows, and market expectations around monetary credibility.",
        "analyst_comment": "The educational point is to identify whether gold is reacting mainly to real rates, USD weakness, protection demand, or broader monetary-risk concerns.",
        "portfolio_discussion_context": "Gold can be discussed as a possible diversifier or defensive asset, depending on objectives, volatility tolerance, liquidity needs, and time horizon.",
        "watchpoints": ["U.S. real yields", "DXY direction", "gold ETF flows", "central-bank buying", "inflation data", "geopolitical headlines"],
        "risk_to_interpretation": "Higher real yields, a stronger USD, lower inflation expectations, weaker ETF demand, or reduced geopolitical stress could change the interpretation.",
        "sources": ["https://www.gold.org/goldhub/data", "https://fred.stlouisfed.org/series/DFII10", "https://www.investing.com/commodities/gold-news"],
    },
    "Bitcoin / BTCUSD": {
        "what_changed": "Bitcoin should be reviewed through liquidity expectations, ETF flows, technology-sector sentiment, regulation, custody infrastructure, and broader risk appetite.",
        "why_it_matters": "Bitcoin can behave as a high-volatility liquidity-sensitive asset in the short term, while longer-term narratives are linked to scarcity, institutional adoption, ETFs, custody, and monetary-debasement concerns.",
        "analyst_comment": "The educational point is to separate short-term volatility from the longer-term adoption and monetary-asset discussion.",
        "portfolio_discussion_context": "Bitcoin should be discussed as a high-volatility monetary asset. Any portfolio discussion should include risk tolerance, position sizing, custody, time horizon, and regulatory uncertainty.",
        "watchpoints": ["spot Bitcoin ETF flows", "DXY direction", "real-rate expectations", "Nasdaq correlation", "liquidity conditions", "regulatory headlines", "institutional treasury activity"],
        "risk_to_interpretation": "Tighter liquidity, higher real yields, regulatory pressure, weak ETF demand, custody failures, or risk-off sentiment could change the interpretation.",
        "sources": ["https://www.theblock.co/data/crypto-markets/bitcoin-etf", "https://coinmarketcap.com/currencies/bitcoin/", "https://www.tradingview.com/symbols/BTCUSD/"],
    },
    "DXY": {
        "what_changed": "DXY should be reviewed through Fed expectations, U.S. yields, inflation data, EUR and JPY performance, risk sentiment, and dollar-funding conditions.",
        "why_it_matters": "DXY is a widely followed proxy for U.S. dollar strength, but it is not the whole dollar system. It mainly reflects the dollar against a fixed basket of major currencies.",
        "analyst_comment": "The educational point is to separate DXY from global dollar liquidity. DXY can rise because the euro or yen weakens, while broader dollar-funding conditions may tell a different story.",
        "portfolio_discussion_context": "DXY can be discussed as a cross-asset pressure gauge, especially for commodities, FX pairs, and liquidity-sensitive assets.",
        "watchpoints": ["Fed communication", "U.S. Treasury yields", "inflation data", "EURUSD", "USDJPY", "risk sentiment", "dollar-funding stress indicators"],
        "risk_to_interpretation": "A dovish Fed shift, weaker U.S. data, stronger foreign currencies, or improved global risk appetite could change the interpretation.",
        "sources": ["https://www.ice.com/market-data/indices/us-dollar-index", "https://fred.stlouisfed.org/series/DTWEXBGS", "https://www.tradingview.com/symbols/TVC-DXY/"],
    },
    "EURUSD": {
        "what_changed": "EURUSD should be reviewed through Fed and ECB expectations, rate differentials, inflation data, growth indicators, energy prices, and USD direction.",
        "why_it_matters": "EURUSD reflects relative monetary policy, growth expectations, rate differentials, energy terms of trade, and broad USD direction.",
        "analyst_comment": "The educational point is that EURUSD is not only a euro story. It is also a dollar story, a rate-differential story, and sometimes an energy-risk story.",
        "portfolio_discussion_context": "EURUSD can be discussed as a major FX pair that helps explain global dollar pressure, European macro sensitivity, and FX translation risk.",
        "watchpoints": ["Fed communication", "ECB communication", "U.S. inflation", "eurozone inflation", "growth data", "energy prices", "rate differentials"],
        "risk_to_interpretation": "A hawkish Fed, weaker eurozone growth, renewed energy stress, or higher U.S. yields could change the interpretation.",
        "sources": ["https://www.ecb.europa.eu/", "https://www.federalreserve.gov/monetarypolicy.htm", "https://www.investing.com/currencies/eur-usd-news"],
    },
    "Mag 7 Equities": {
        "what_changed": "The Mag 7 should be reviewed through earnings expectations, AI capital-expenditure commentary, rates, valuation sensitivity, market breadth, regulation, and liquidity conditions.",
        "why_it_matters": "The Mag 7 carries significant weight in major U.S. equity indices. Their performance can influence index direction, investor sentiment, concentration risk, and growth-stock leadership.",
        "analyst_comment": "The educational point is concentration. When a small group of mega-cap stocks drives a large share of index performance, headline index strength may hide weaker breadth underneath.",
        "portfolio_discussion_context": "The Mag 7 can be discussed as a concentration, growth, technology, and valuation-sensitivity topic. The discussion should include diversification, volatility, and sensitivity to interest rates.",
        "watchpoints": ["earnings revisions", "AI capex commentary", "U.S. yields", "Nasdaq breadth", "valuation multiples", "regulatory headlines", "liquidity conditions"],
        "risk_to_interpretation": "Higher rates, weaker earnings guidance, AI monetization concerns, valuation compression, weaker breadth, or regulatory pressure could change the interpretation.",
        "sources": ["https://www.nasdaq.com/market-activity/stocks", "https://www.investing.com/equities/", "https://www.tradingview.com/markets/stocks-usa/market-movers-large-cap/"],
    },
}


DEFAULT_ASSETS = list(ASSET_CONFIG.keys())


def build_asset(asset_name: str) -> dict:
    return {"asset_name": asset_name, **ASSET_CONFIG[asset_name]}


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
