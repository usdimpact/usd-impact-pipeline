# Score source replacement inventory — 2026-10-28

Status: **review-only / source-neutral planning / issue #155 HOLD remains active**.

Related:
- issue #155 — Score rights HOLD;
- issue #179 — replace yfinance-delivered Score inputs with licensed/commercial-safe source paths;
- `governance/score-source-neutral-adapter-contract.json`.

## Executive conclusion

The Score engine can be migrated away from the current Yahoo Finance/yfinance delivery path without changing Score v2 mathematics, provided replacement sources preserve the exact canonical input semantics.

The migration should therefore be treated as a **data-source adapter change**, not a methodology change.

No source switch is authorized by this document.

## Current runtime dependency

Production code currently groups six drivers under provider code `yahoo` and retrieves them through `yfinance`:

| Driver | Current symbol | Current delivery path | Current operational meaning |
|---|---|---|---|
| DXY | `DX-Y.NYB` | Yahoo Finance via yfinance | ICE U.S. Dollar Index daily level |
| WTI | `CL=F` | Yahoo Finance via yfinance | WTI crude continuous/front-contract daily close path |
| SPX | `^GSPC` | Yahoo Finance via yfinance | S&P 500 index daily level |
| VIX | `^VIX` | Yahoo Finance via yfinance | Cboe VIX daily level |
| BTC | `BTC-USD` | Yahoo Finance via yfinance | Bitcoin/USD daily spot-style series |
| GOLD | `GC=F` | Yahoo Finance via yfinance | Gold continuous/front-contract daily close path |

Treasury drivers currently use FRED:
- DGS2;
- DGS10.

## Why this work is now prioritized

The yfinance project states that it is not affiliated with Yahoo and describes the Yahoo Finance API path as intended for personal use. Yahoo's public terms separately restrict commercial reuse absent express permission.

The project therefore should not make the long-term commercial/public Score architecture depend on the current yfinance path unless the exact applicable rights are affirmatively documented.

This does not by itself resolve the rights of the upstream S&P, Cboe, CME, ICE or crypto data.

## Runtime seam

`usd_impact_score_v2.py` already separates the following concepts:

### Provider retrieval
- `fetch_yahoo(...)`;
- `fetch_fred(...)`.

### Canonical driver identity
- DXY;
- WTI;
- SPX;
- VIX;
- BTC;
- GOLD;
- UST_2Y;
- UST_10Y.

### Score semantics
- history starts 2015-01-01;
- daily data are mapped into canonical driver columns;
- inputs are joined by date;
- score weeks end Friday (`W-FRI`);
- fixed driver weights remain unchanged;
- z-score clipping remains ±3.5;
- regime bands remain unchanged.

This means a future licensed adapter should output canonical daily driver columns **before** score calculations, without requiring changes to Score weights or regime logic.

## Replacement candidates by rights owner / source class

The following are routing classes, not purchasing decisions.

### DXY

Desired authoritative class:
- ICE U.S. Dollar Index licensed feed or licensed distributor.

Must match:
- exact DXY index definition;
- official/delayed close semantics;
- calendar/date convention;
- historical coverage to at least 2015-01-01;
- revision policy.

Do not substitute a generic broad-dollar index.

### WTI

Desired authoritative class:
- CME/NYMEX licensed futures feed or licensed commercial distributor.

Critical semantic question:
- current `CL=F` behaves as a continuous/front-contract convenience series;
- a replacement must explicitly define roll convention and adjusted/unadjusted treatment.

Do not replace with physical WTI spot or a different futures continuation convention without an approved methodology migration.

### S&P 500

Desired authoritative class:
- S&P DJI licensed index feed or licensed distributor.

Must match:
- S&P 500 index level;
- close/date semantics;
- historical revisions where applicable.

Do not substitute SPY or another investable proxy.

### VIX

Desired authoritative class:
- Cboe licensed index feed or licensed distributor.

Must match:
- official VIX index level;
- close/date convention;
- historical revision behavior.

Do not substitute VIX futures.

### BTC

Desired authoritative class:
- commercially licensed BTC/USD spot/reference feed with explicit redistribution/derived-use rights.

Key decision:
- define whether Score v2 semantics intend one exchange spot close, a composite/reference price, or the historical Yahoo BTC-USD series convention.

A licensed replacement must be parity-tested before selection.

### Gold

Desired authoritative class:
- CME/COMEX licensed futures feed or licensed commercial distributor.

Critical semantic question:
- current `GC=F` is a convenience continuous/front-contract series;
- replacement must define exact roll/adjustment semantics.

Do not replace with XAU spot without an approved methodology migration.

### UST 2Y / UST 10Y

Current:
- FRED DGS2 / DGS10.

Preferred path:
- retain unless rights review identifies a reason to replace;
- preserve exact constant-maturity Treasury-yield semantics.

## Required adapter interface

A future source adapter should return a daily pandas-style frame with exactly these canonical columns:

`DXY, WTI, SPX, VIX, BTC, GOLD, UST_2Y, UST_10Y`

Requirements:
- daily date index;
- finite numeric values or missing values;
- no provider-specific column names after adapter mapping;
- no extra columns;
- deterministic canonical column ordering;
- provider metadata retained separately from calculation values.

## Parity protocol

A replacement provider must be evaluated on all of the following dimensions.

1. **Instrument identity** — same economic series, not a proxy.
2. **Field identity** — close/index level/settlement definition must be explicit.
3. **Adjustment convention** — especially futures and Yahoo auto-adjust behavior.
4. **Futures continuation** — roll schedule and back-adjustment method.
5. **Trading calendar** — holiday/weekend behavior.
6. **Observation date/timezone** — no silent one-day shifts.
7. **Friday resampling** — weekly values must align with current Score semantics.
8. **Missing-data behavior** — no vendor-specific fills before canonical processing.
9. **Revision behavior** — index/data revisions must be understood.
10. **Units** — percentage/yield/index/futures-price units must match.
11. **Historical depth** — sufficient history from 2015-01-01.
12. **Freshness contract** — current maximum age limits must remain explicit.

## Migration order

### Phase A — current packet

- source-neutral contract;
- current-source inventory;
- parity requirements;
- fail-closed validator;
- no runtime changes.

### Phase B — synthetic adapter interface

Future source-only work may:
- add a provider-neutral adapter protocol;
- add synthetic provider fixtures;
- prove canonical frame equivalence;
- leave `fetch_yahoo` and current Production flow untouched.

### Phase C — licensed candidate evaluation

Requires rights/pricing evidence for candidate provider(s).

Allowed only after:
- commercial/internal-use rights are documented;
- retention rights are documented;
- derived/public-output rights are understood;
- provider-specific semantics are documented.

### Phase D — Development real-data parity

Requires a separate authorization under issue #155/#179.

Must compare:
- daily canonical series;
- weekly resampled inputs;
- z-scores;
- contributions;
- aggregate Score;
- regime;
- provenance/fingerprint behavior.

No public replacement occurs in this phase.

### Phase E — Production source migration

Requires:
- successful Development parity;
- research protocol approval where necessary;
- updated release validation;
- archive/provenance treatment;
- exact-head CI;
- separate explicit Production authorization.

## Current files coupled to source identity

At minimum, source migration must account for:

- `usd_impact_score_v2.py`;
- `scripts/validate_weekly_release.py`;
- `scripts/validate_methodology_contract.py`;
- `scripts/validate_data_semantics_contract.py`;
- `tests/test_data_fetch_resilience.py`;
- `requirements.txt`;
- `requirements.lock`;
- `runtime/requirements-2026-10-05.lock`;
- public methodology/source provenance metadata;
- weekly input/reproduction evidence contracts;
- source-retention documentation.

This inventory does not authorize editing those runtime files yet.

## Current HOLD boundary

Do not:
- purchase or accept provider terms;
- add paid provider credentials;
- fetch real replacement-provider data;
- switch live sources;
- modify Score formula or weights;
- change locked research readers;
- rewrite public archives;
- remove yfinance from Production dependencies;
- deploy Production.

Issue #155 remains the controlling rights HOLD, and issue #179 controls source-replacement planning.
