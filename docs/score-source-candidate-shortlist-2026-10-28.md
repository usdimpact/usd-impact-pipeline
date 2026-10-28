# Score licensed-source candidate shortlist — 2026-10-28

Status: **public evidence only / no vendor selected / no purchase / no real data / HOLD remains active**.

## Purpose

Convert the source-replacement architecture into a practical shortlist of authoritative commercial data paths that can later be evaluated under the fail-closed candidate framework.

This document is not a procurement decision and does not authorize any subscription, contract, credential, real-data rehearsal, or source switch.

## Candidate shortlist

### DXY — ICE Data Indices

Public official material identifies the ICE U.S. Dollar Index as an ICE Data Indices benchmark and lists daily/historical access through ICE Data API, ICE Consolidated History, ICE Consolidated Feed, and ICE Data Files.

Assessment: **strong candidate**.

Why:
- same intended benchmark family;
- direct rights-owner data path;
- history since 1996 exceeds the Score requirement.

Still unresolved:
- commercial terms;
- exact end-of-day/close field semantics;
- derived/public output rights;
- pricing.

### SPX — S&P Dow Jones Indices

S&P DJI offers licensed index-level data subscriptions, historical end-of-day index levels, API delivery, SFTP, and third-party licensed vendor access.

Assessment: **strong candidate**.

Why:
- direct rights-owner path;
- explicit index-level data product;
- historical API delivery.

Still unresolved:
- S&P response to case 01036004;
- derived/public output rights;
- machine-readable publication terms;
- pricing.

### VIX — Cboe

Cboe Global Indices Feed explicitly includes VIX and offers direct feed, end-of-day files, historical files, cloud access, and vendor delivery.

Assessment: **strong candidate**.

Why:
- direct administrator/source path;
- explicit VIX availability;
- historical and end-of-day delivery options.

Still unresolved:
- derived/public output rights;
- exact field/session convention;
- pricing.

### WTI — CME Group

CME offers market data APIs, DataMine historical data, cloud delivery, and licensed distributor access.

Assessment: **conditional candidate**.

The commercial source path is strong, but semantic parity is not automatic because the current Yahoo `CL=F` convenience series is provider-defined. A licensed CME feed would need an explicitly defined continuation/roll policy before it can be considered equivalent.

Still unresolved:
- close vs settlement;
- front-contract selection;
- roll schedule;
- back-adjustment policy;
- derived/public output rights;
- pricing.

### GOLD — CME Group

The same CME commercial data infrastructure is available for COMEX Gold.

Assessment: **conditional candidate**.

As with WTI, the main obstacle is semantic parity with Yahoo `GC=F`, not data availability.

Still unresolved:
- close vs settlement;
- continuous/front-contract construction;
- roll and adjustment convention;
- derived/public output rights;
- pricing.

### BTC — CME Group / CF Benchmarks

CME CF BRR and BRTI are regulated/professional Bitcoin pricing benchmarks. CME states that customers require a Market Data License Agreement and that creation/distribution of derived works requires a separate Derived Data License Agreement.

Assessment: **commercially plausible, but likely semantic mismatch**.

The current Yahoo `BTC-USD` series is not automatically equivalent to:
- CME CF BRR;
- CME CF BRTI;
- another composite reference rate.

Any switch would require an explicit decision on the intended Bitcoin price convention and likely a methodology/protocol review.

## Priority order

Recommended evaluation order:

1. **DXY**
2. **SPX**
3. **VIX**
4. **WTI**
5. **GOLD**
6. **BTC**

Rationale:
- DXY/SPX/VIX have the clearest authoritative first-party source identity and closest semantic fit.
- WTI/Gold require futures-continuation reconstruction.
- BTC requires a deeper price-definition decision before parity can even be meaningfully tested.

## What to do when a provider responds

For S&P/Cboe/CME/FRED replies:

1. scope the response to the exact provider/product;
2. update issue #155;
3. update only the relevant candidate rights fields;
4. do not move a candidate beyond `pending` unless commercial/internal/derived-use scope is explicitly supported;
5. keep real-data parity as `not_run` until separately authorized.

## Current boundary

No provider is selected.

No subscription, fee, contract, API credential, real-data pull, public replacement, research-ledger mutation, or Production change is authorized.
