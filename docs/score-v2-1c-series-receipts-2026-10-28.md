# Score v2.1C series-specific rights and release-timing receipts — 2026-10-28

Status: **public-evidence engineering review only**.

This packet does not approve any source and is not a legal conclusion.

## Executive finding

The eight-slot v2.1C candidate is **not yet fully rights-ready**.

Six slots have comparatively strong zero-budget/public-domain evidence:
- Board H.10 broad USD;
- EIA WTI spot;
- Board H.4.1 total assets;
- Board H.15 10Y real yield;
- Board H.15 2Y Treasury;
- Board H.15 10Y Treasury.

Two composite slots remain materially conditional:
- Board FCI-G;
- OFR FSI.

The issue is not simply copyright ownership of the federal web page. Both composites rely on private/non-Board market inputs, and the relevant federal disclaimers preserve privately owned-rights caveats.

## Board source-family rule

The Board states that, unless otherwise indicated, information on its website is public domain and may be copied/distributed without permission, with citation requested. It separately warns that non-Board material requires permission from its owner and does not represent that use will not infringe privately owned rights.

Engineering implication: direct Board statistical releases are strong candidates, but composite outputs with private inputs remain conditional until their published-output scope is confirmed.

## H.10 / broad dollar

The Board H.10 release page documents:
- daily broad-dollar observations;
- Monday 4:15 p.m. ET publication for the previous business week;
- holiday-Monday deferral to the following business day;
- preformatted Daily Indexes CSV and XML delivery.

Point-in-time consequence: a Friday Score cannot use the same week's broad-dollar observations. They normally become available the following Monday.

## EIA WTI spot

EIA explicitly permits use/distribution of its website data, files and databases, subject to acknowledgment and third-party protected-material exceptions.

The WTI historical pages expose daily history and release-date metadata. Therefore point-in-time research must bind observations to the EIA publication/release date, not assume same-day market observation availability.

Rights status is strong; exact historical publication timing still requires a conservative reconstruction rule.

## FCI-G

The Board publishes:
- monthly baseline CSV;
- quarterly CSV;
- definitions;
- code;
- updated estimates.

However, the methodology aggregates financial variables that include non-Board/private data sources. The Board's general public-domain rule does not erase privately owned-rights caveats.

FCI-G therefore remains blocked for a rights-minimized real-data study until the intended use of the **published aggregate Board output** is specifically cleared or a cleaner replacement is designed.

It also has a vintage issue: the Board updates estimates, so point-in-time research needs publication-version tracking.

## OFR FSI

OFR's legal notice is favorable for OFR-created federal-employee work, but the FSI creates a more explicit private-input problem.

OFR's own indicator table states that **all series are pulled from Datastream by Refinitiv** and lists proprietary indicators from ICE, S&P, Cboe, MSCI, JPMorgan and others.

OFR also:
- publishes with a two-business-day lag;
- publishes a revision history;
- has issued corrections to an underlying data feed.

Therefore OFR FSI must remain blocked pending review of whether the published aggregate output may be used in the proposed commercial derived Score without inheriting restrictions from the underlying licensed feeds.

## H.4.1 / WALCL

Board H.4.1:
- is released Thursday, generally 4:30 p.m. ET;
- exposes table CSVs and full XML;
- is governed by the Board public-domain default absent a series-specific exception.

For a Friday Score, the current Wednesday level may enter only after the Thursday release.

## H.15 / DFII10, DGS2, DGS10

Board H.15:
- is posted Monday-Friday at 4:15 p.m. ET;
- exposes Treasury Constant Maturities CSV and full XML;
- contains the nominal and inflation-indexed constant-maturity series required here.

Point-in-time research must use the latest observation actually included in a release posted by Friday cutoff. Observation date alone is insufficient.

## Candidate disposition

v2.1C is now best described as **6 strong + 2 blocked composite slots**.

This is an improvement over the proprietary-v2 path, but it is not yet a complete rights-cleared alternative.

The next zero-budget engineering choice is therefore:

1. obtain explicit scope confirmation for the published FCI-G and OFR FSI aggregate outputs; or
2. design two public-domain-only replacement slots that are computed from direct federal/EIA inputs without composite proprietary underlyings.

No real-data work is authorized by this receipt.
