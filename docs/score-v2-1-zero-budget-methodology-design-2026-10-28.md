# Score v2.1 zero-budget methodology design — 2026-10-28

Status: **design only / no real-data research / no methodology activation / no Production**.

Controlling issues:
- #155 — rights HOLD;
- #179 — source replacement;
- #187 — v2.1 zero-budget methodology design.

## 1. Why v2.1 exists

Score v2 was built around eight canonical drivers with fixed signs and equal absolute weights. The zero-budget rights review now shows that preserving all eight current source semantics may not be possible without paid proprietary data.

The design problem is therefore not "find any free ticker." It is:

> Can a rights-safe, zero-cost methodology preserve the economic intent of Score v2 closely enough to justify a separately versioned Score v2.1?

The answer is **not yet known**. This packet defines how that question must be tested later.

## 2. Phase-1 isolation principle

The first v2.1 research candidate must change **source semantics only**.

The following remain frozen to Score v2 for the initial comparison:

- eight conceptual driver slots;
- canonical order;
- signs;
- equal absolute weights of 0.125;
- Friday-ended weekly sampling;
- z-score machinery;
- sample standard deviation convention;
- z-score clip at 3.5;
- regime bands.

This is essential. Changing sources and re-optimizing weights simultaneously would make it impossible to determine whether differences came from the new data semantics or from formula tuning.

Any weight, sign, clipping, normalization, threshold, or regime-band change belongs in a later separately preregistered experiment.

## 3. Driver-by-driver design status

### DXY

Current: ICE DXY via Yahoo/yfinance.

Zero-budget design candidate: Federal Reserve Nominal Broad U.S. Dollar Index (`DTWEXBGS`).

Status: **methodology substitution candidate**.

This is not equivalent to DXY. The basket, weights, and construction differ. It can only be evaluated as a new v2.1 USD-strength definition.

### WTI

Current: Yahoo `CL=F` continuous/front-futures convenience series.

Zero-budget design candidate: EIA/FRED WTI Cushing spot (`DCOILWTICO`).

Status: **methodology substitution candidate**.

Spot WTI is not a futures continuation series. A change would alter roll exposure and potentially weekly behavior.

### SPX

Current: S&P 500 index.

Status: **rights blocked**.

FRED availability does not independently resolve S&P commercial/derived-use rights. No ETF proxy may be silently substituted.

### VIX

Current: Cboe VIX index.

Status: **rights blocked**.

FRED availability does not independently grant Cboe derived/public-use rights. VIX futures or another volatility measure cannot silently replace VIX.

### BTC

Current: Yahoo `BTC-USD`.

Status: **zero-budget source unresolved**.

Before any candidate exists, the methodology must explicitly define the intended Bitcoin price convention: single venue, composite, benchmark, fixing time, timezone, and revision behavior.

### GOLD

Current: Yahoo `GC=F`.

Status: **zero-budget source unresolved**.

Spot gold is not automatically equivalent to COMEX futures. Any switch requires an explicit gold-price definition.

### UST 2Y / UST 10Y

Current: FRED `DGS2` / `DGS10`.

Status: **retain if rights/use are confirmed**.

No methodological substitution is currently needed.

## 4. No partial-score shortcut

If one required conceptual driver cannot be sourced under the approved v2.1 definition, the candidate fails closed.

The design forbids:

- dropping a driver;
- automatically renormalizing remaining weights;
- carrying an old provider value indefinitely;
- inserting an unapproved proxy;
- mixing v2 and v2.1 components without an explicit transition protocol.

This prevents a nominally "same" Score from silently changing composition.

## 5. Research measurements

When real-data research is separately authorized, the comparison must report at least:

- weekly observation coverage;
- overlap weeks;
- Pearson and Spearman driver correlation;
- weekly direction agreement;
- standardized driver-value difference;
- aggregate Score correlation;
- aggregate Score mean absolute difference;
- aggregate Score maximum absolute difference;
- regime agreement;
- regime transition-date differences;
- behavior across the existing historical regime windows;
- freshness failures;
- missing weeks.

These are **measurements**, not current acceptance thresholds.

## 6. Threshold discipline

No numeric acceptance thresholds are approved by this document.

Before any real candidate data are examined, a preregistration must freeze:

- candidate definitions;
- data cutoff;
- evaluation window;
- rights evidence;
- missing-history policy;
- revision policy;
- calendar/timezone treatment;
- metrics;
- acceptance thresholds;
- stop conditions.

Thresholds may not be selected or relaxed after results are visible.

## 7. Missing history

The target remains January 1, 2015 where the candidate source supports it.

A source with shorter history cannot be silently padded.

The future preregistration must decide, before data inspection, whether:
- the candidate is rejected for insufficient history;
- the common comparison window is shortened for research only;
- a separately justified historical bridge is allowed.

No bridge is authorized here.

## 8. Revisions and point-in-time integrity

Every candidate must document whether historical observations can be revised.

A future research protocol must distinguish:
- currently published history;
- point-in-time values, where available;
- later revisions.

No lookahead is allowed. The comparison must not use information that would not have been available at the relevant weekly observation date if the goal is historical behavior evaluation.

## 9. Versioning

Score v2 history is immutable.

If v2.1 is ever accepted:
- it receives a new methodology version;
- any reconstructed historical series is labeled **recomputed v2.1 history**;
- v2 and v2.1 must not be spliced into one unversioned time series;
- an explicit transition date is required;
- public explanations must describe changed driver semantics.

## 10. Public/private target

If rights later permit publication, the preferred public surface remains aggregate-safe:

Public:
- date;
- aggregate Score;
- regime;
- aggregate history;
- methodology version;
- weights;
- regime bands;
- approved high-level provenance;
- non-value-bearing hashes.

Private by default:
- raw provider values;
- component daily/weekly histories;
- normalization moments;
- component z-scores;
- contributions;
- provider-specific reproduction inputs.

## 11. Gates before real-data research

No real-data v2.1 comparison may start until all are true:

1. #155 permits the relevant research use;
2. candidate rights are documented;
3. source semantics are frozen;
4. metrics and thresholds are preregistered;
5. data cutoff is preregistered;
6. revision policy is preregistered;
7. missing-history policy is preregistered;
8. separate real-data research authorization is recorded.

## 12. Gates before activation

Even successful research would not authorize Production.

Activation additionally requires:
- reviewed research results;
- explicit v2.1 methodology decision;
- approved public/private schema;
- archive transition plan;
- research-reader/versioning plan;
- exact-head CI;
- separate Production authorization.

## Current conclusion

The project is prepared to test a zero-budget v2.1 methodology later, but **no complete eight-driver v2.1 candidate currently exists** because SPX/VIX rights and BTC/Gold zero-budget definitions remain unresolved.

That incompleteness is intentional and fail-closed.
