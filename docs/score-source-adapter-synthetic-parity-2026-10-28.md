# Score provider-neutral adapter synthetic parity — 2026-10-28

Status: **review-only / synthetic only / no live source switch / issue #155 HOLD remains active**.

Related:
- issue #155 — rights HOLD;
- issue #179 — licensed/commercial-safe source replacement;
- `governance/score-source-neutral-adapter-contract.json`;
- `scripts/score_source_adapter.py`;
- `scripts/rehearse_score_source_adapter_parity.py`.

## Purpose

Prove that provider-specific schemas and units can be normalized into the current Score v2 canonical daily input contract without changing Score semantics.

This packet does **not** select a vendor or fetch real provider data.

## Synthetic fixtures

Two deliberately different provider-shaped fixtures are used.

### Synthetic Alpha

Schema examples:
- `dollar_idx`;
- `crude_front`;
- `sp500`;
- `ust2_pct`;
- `ust10_pct`.

Treasury yields are already represented in percentage-point units.

### Synthetic Beta

Schema examples:
- `usd_index_level`;
- `wti_continuous`;
- `spx_index`;
- `ust2_bps`;
- `ust10_bps`.

Treasury yields are represented in basis points and require explicit ×0.01 normalization.

Both fixtures encode the same synthetic economics.

## Adapter boundary

The provider-neutral adapter accepts:

- provider identifier;
- date column;
- provider-column -> canonical-driver mapping;
- optional explicit per-driver unit multiplier.

It returns exactly:

`DXY, WTI, SPX, VIX, BTC, GOLD, UST_2Y, UST_10Y`

with:
- a sorted unique daily DatetimeIndex;
- no extra columns;
- numeric finite values or missing observations;
- canonical driver ordering.

The adapter performs no network access.

## Parity proof

The rehearsal requires both provider fixtures to produce equal:

1. canonical daily frames;
2. canonical daily SHA-256;
3. limited three-observation forward-fill result;
4. Friday-ended weekly input matrix;
5. full-sample z-scores;
6. aggregate Score;
7. regime labels.

The equality proof uses the existing Score v2 production functions after normalization. This is deliberate: the adapter is tested as a source boundary, not as a replacement Score implementation.

## What this proves

It proves the architecture can absorb differences in:
- field names;
- timestamp representation;
- simple deterministic unit conversion;

without changing Score v2 mathematics.

## What this does not prove

It does **not** prove that a real candidate provider is semantically equivalent.

Real-provider parity must still resolve:
- exact instrument identity;
- official close/settlement field;
- futures continuation/roll convention;
- adjustment/back-adjustment behavior;
- timezone/session boundary;
- trading calendar;
- revision policy;
- historical coverage;
- missing-data behavior;
- licensing for internal use, retention and derived/public outputs.

In particular, unit conversion is insufficient to establish parity for `CL=F` or `GC=F`; their continuous-futures construction must be explicitly matched or separately approved as a methodology change.

## Future candidate-provider procedure

For each candidate source:

1. document rights and semantic contract before using real data;
2. implement only the provider adapter;
3. run synthetic adapter tests first;
4. obtain separate authorization before real Development data;
5. compare canonical daily histories;
6. compare Friday weekly levels;
7. compare Score components and aggregate Score;
8. record all non-equivalent weeks;
9. do not switch Production until all issue #155/#179 gates are met.

## Current boundary

No provider purchase, credentials, real provider fetch, public artifact change, research-ledger mutation, yfinance removal, or Production change is authorized by this packet.
