# Score v2.1E federal/BLS public-domain zero-budget alternative — 2026-10-28

Status: **design only / public-evidence exact-series receipts only**.

## Why v2.1E exists

v2.1D removed composite private-input indexes but retained EIA Cushing WTI as its energy slot.

Further official-source review found that EIA identifies that WTI series as Refinitiv/LSEG data republished on the EIA website. EIA's general reuse framework does not clear separately protected third-party material.

v2.1E therefore replaces that slot with BLS Producer Price Index crude petroleum, series **WPU0561**.

This is not a WTI-equivalent substitution. It is a separately versioned methodology candidate.

## Exact series inventory

| Slot | Direct series | Transformation |
|---|---|---|
| USD | H10/H10/JRXWTFB_N.B | level |
| Energy | BLS WPU0561 | natural-log level |
| Financial conditions | H8/H8/B1001NCBA | negative 13-week log change |
| Financial stress | H41/H41/RESPPALDP_N.WW | log1p level |
| Liquidity | H41/H41/RESPPA_N.WW | 13-week log change |
| Real yield | H15/H15/RIFLGFCY10_XII_N.B | level |
| 2Y Treasury | H15/H15/RIFLGFCY02_N.B | level |
| 10Y Treasury | H15/H15/RIFLGFCY10_N.B | level |

## Rights posture

The seven Board slots inherit the Board's public-domain default unless a series-specific exception exists.

BLS states that everything it publishes is public domain except previously copyrighted photographs and illustrations. The crude-petroleum PPI is a published BLS statistical series.

No legal conclusion or source approval is made here. The repository continues to require source-specific checks and keeps issue #155 on HOLD.

## Energy methodology tradeoff

WPU0561 is monthly, not daily.

That creates several intentional consequences:

- the energy channel changes more slowly than WTI;
- the value must not be treated as if known at month end;
- the value becomes eligible only after the scheduled BLS PPI release;
- BLS states PPI observations can be revised for four months;
- historical point-in-time research therefore needs the actual vintage available at each Friday cutoff.

If historical BLS vintages cannot be reconstructed conservatively, real-data research must fail closed rather than substitute current-vintage history.

## Exact direct-release advantages

The candidate does not require:
- Yahoo/yfinance;
- ICE DXY;
- CME futures;
- S&P 500;
- Cboe VIX;
- Refinitiv/LSEG WTI;
- ETF proxies;
- composite indexes built from proprietary market feeds.

The remaining concerns are methodological and vintage/revision controls rather than an identified paid market-feed requirement.

## Research boundary

No real data may be fetched under this design.

The next safe step is a preregistration that freezes:
- BLS release-vintage handling;
- H.8 benchmark-revision policy;
- mixed-frequency release eligibility;
- sparse primary-credit diagnostics;
- redundancy diagnostics;
- hard acceptance thresholds;
- synthetic-only timing/revision tests.

A separate owner authorization is still required before any real-data research.
