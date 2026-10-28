# Score zero-budget fallback matrix — 2026-10-28

Status: **review-only / zero-budget planning / issue #155 HOLD remains active**.

## Conclusion

There is currently **no confirmed zero-budget path that preserves Score v2 exactly**.

Some free official data exist, but they are not semantically equivalent to the current inputs:

- **DXY:** the Federal Reserve publishes a free broad dollar index, but it is not ICE DXY.
- **WTI:** EIA publishes free WTI Cushing spot prices, but spot is not the current futures continuation series.
- **SPX:** FRED carries S&P 500 data, but FRED explicitly marks the series copyrighted and pre-approval required. Access through FRED does not resolve USD Impact's commercial/derived-use rights.
- **VIX:** FRED carries VIX, but identifies Cboe copyright and reprint permission. FRED access does not independently grant USD Impact derived/public-use rights.
- **BTC:** no authoritative zero-cost source has yet been identified that both matches the historical Yahoo BTC-USD convention and has confirmed commercial/derived-use rights.
- **Gold:** no authoritative zero-cost source has yet been identified that preserves COMEX continuous/front-contract semantics with confirmed commercial/derived-use rights.
- **DGS2/DGS10:** retain the current FRED path if FRED confirms acceptable use.

## Engineering implication

Do **not** silently substitute free data into Score v2.

Any change such as:
- DXY -> Fed broad dollar index;
- CL futures -> EIA WTI spot;
- GC futures -> spot gold;
- VIX -> another volatility proxy;
- S&P 500 -> ETF/equity proxy;
- Yahoo BTC-USD -> a different crypto benchmark;

changes the economic meaning of at least one driver and therefore requires a separately reviewed methodology version.

## Zero-budget decision tree

1. Provider confirms no-cost permitted use for the current input:
   - keep candidate alive;
   - document scope;
   - request separate Development parity authorization.

2. Provider requires paid licensing:
   - mark candidate unavailable under the current project constraint;
   - do not enter procurement.

3. No exact free replacement exists:
   - preserve #155 HOLD;
   - prepare a v2.1 methodology option only;
   - do not deploy or change Production without explicit methodology/research approval.

## Current recommendation

Wait for S&P/Cboe/CME/FRED replies while keeping the Friday publication gate closed.

If paid licensing is required across the relevant proprietary inputs, the next rational project is not more licensing work; it is a controlled **Score v2.1 zero-budget methodology design** using free official inputs, with explicit backtest/research review before any Production consideration.

No methodology change, real-data rehearsal, public replacement, or Production authorization is granted by this document.
