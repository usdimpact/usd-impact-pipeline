# Score v2.1B official-macro zero-budget alternative — design

Status: **design only**.

This candidate is intentionally different from Score v2. It replaces proprietary market-price dependencies with official/public macro-financial proxies and must be evaluated as a new methodology, not as a drop-in source migration.

## Proposed eight slots

| Slot | Series | Role | Sign |
|---|---|---|---:|
| USD | DTWEXBGS | broad USD strength | + |
| Energy | DCOILWTICO | WTI spot / commodity transmission | - |
| Financial conditions | NFCI | overall financial tightness | + |
| Financial stress | STLFSI4 | stress / risk aversion | + |
| Liquidity | WALCL | Fed balance-sheet liquidity | - |
| Real yield | DFII10 | real-rate pressure | + |
| 2Y Treasury | DGS2 | front-end rates | + |
| 10Y Treasury | DGS10 | long-end rates | + |

The absolute weights remain equal at 0.125 for design simplicity, but this is **not** presented as continuity with Score v2. Several slots have changed economic meaning.

## Why this alternative is valuable

It removes required dependence on:
- S&P 500 index licensing;
- Cboe VIX licensing;
- Yahoo BTC-USD;
- COMEX Gold continuation data;
- ICE DXY as the only USD-strength definition.

It therefore gives the project a plausible zero-paid-data research path.

## Important methodological changes

This candidate changes the economic architecture:

- DXY becomes a broad trade-weighted dollar index.
- WTI futures becomes WTI spot.
- SPX becomes a financial-conditions composite.
- VIX becomes a financial-stress composite.
- Bitcoin becomes system liquidity.
- Gold becomes real yield.

This means v2.1B must never be labeled an equivalent v2 continuation.

## Mixed-frequency rule

Candidate sources have daily and weekly frequencies.

The proposed design rule is:
- anchor each Score observation to the completed Friday;
- use only observations that were available on or before that Friday;
- never use a value released after the Friday to populate that Friday;
- no future-dated backfill;
- a missing required slot fails the week closed.

A real research preregistration must document source release lags, because a Wednesday-level series published Thursday and a Friday-ending index published later can create lookahead if naively aligned by observation date.

## Transformation question remains open

No real-data transformation is authorized.

Before research, each slot must freeze whether the standardized input is based on:
- level;
- weekly change;
- log change;
- year-over-year change;
- another justified transformation.

This matters especially for WALCL, where the level contains a strong structural trend.

The transformation choice must be fixed before results are viewed.

## Redundancy risk

The official-macro alternative has two important concentration risks:

1. NFCI and STLFSI4 may overlap strongly.
2. DGS10 and DFII10 may concentrate the rates factor.

Any future research must report:
- pairwise correlation;
- factor concentration;
- leave-one-slot-out sensitivity;
- score distribution and regime balance.

No slot may be removed or reweighted after observing favorable results without a new preregistration.

## Rights rule

"Official" and "free to view" are not treated as automatic commercial/derived-use permission.

Every slot retains a `confirm_reuse_scope` gate.

No real-data research starts until the project records source-specific reuse scope and receives separate authorization.

## Public surface

If this methodology were ever approved, the preferred public surface remains aggregate-safe:
- date;
- aggregate Score;
- regime;
- methodology version;
- weights;
- approved high-level source labels.

Component values, normalization moments, slot z-scores and source-specific reproduction inputs remain private by default.

## Current conclusion

v2.1B is the first **complete conceptual zero-budget alternative** in the repository, but it remains design-only. Its next step is a preregistered, rights-cleared research protocol—not implementation.
