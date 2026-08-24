# USD Impact Score v3 — preregistered descriptive research protocol

**Protocol ID:** `usd_impact_score_v3_descriptive_research_2026-08-24`  
**Protocol version:** 1  
**Registration date:** August 24, 2026  
**Latest observation already seen when this protocol was defined:** August 21, 2026  
**First prospective untouched week:** August 28, 2026  
**Production change authorized by this document:** **No**

The machine-readable authoritative companion is [`score_v3_preregistration.json`](./score_v3_preregistration.json). This document explains the rationale and rules in review-friendly form. If prose and JSON ever conflict, the conflict must be resolved by a versioned protocol amendment before affected prospective evidence is used.

## 1. Why this protocol exists

Score v2 is transparent and deterministic, but the institutional review completed on August 24, 2026 identified two material specification limitations:

1. **Normalization revision dependence.** v2 normalizes weekly levels using the full available sample. A later observation changes historical means and standard deviations, so historical scores and regime labels can move after the fact. Current-vintage point-in-time research found only about 40% regime-label agreement between prior-only normalization and the latest full-sample recalculation over the available evaluated history.
2. **Correlated-driver concentration.** Equal nominal driver weights do not imply eight independent information channels. The latest published diagnostics show substantial overlap, including very high 2Y/10Y component correlation and a materially lower correlation-adjusted effective component count than the ordinary contribution count.

Those findings justify research. They do **not** justify changing production after looking at whichever alternative appears most attractive retrospectively.

This protocol therefore defines the v3 research candidates and decision rules **before** any observation dated August 28, 2026 or later is allowed to influence model selection.

## 2. Honesty boundary: what is and is not untouched

All market history through **August 21, 2026** has already influenced the problem definition. It is therefore retrospective design information. It may be used for implementation testing, sanity checks and failure analysis, but it must not be described as an untouched out-of-sample test of these v3 candidates.

The first truly prospective holdout observation under this protocol is the completed week ending **August 28, 2026**.

A formal candidate-selection decision is prohibited until at least **52 completed prospective weeks** have accumulated. Interim reviews after 13, 26 and 39 weeks may report implementation status and preregistered metrics, but they may not:

- add a candidate because it looks promising;
- remove a candidate because it looks weak, except for a genuine implementation impossibility documented by a protocol amendment;
- alter a formula, window, weight, clip or regime threshold;
- change the selection metric or tie-break rules;
- name a winner; or
- recommend production promotion.

## 3. Research construct

The construct remains a **contemporaneous descriptive U.S. dollar regime state**.

This protocol does not study or claim:

- future asset returns;
- probability of dollar appreciation;
- a trade entry/exit signal;
- portfolio allocation;
- strategy PnL; or
- predictive accuracy.

If USD Impact later wants a predictive model, it requires a separate preregistration that specifies the forecast target, horizon, loss function, training set, validation set and untouched test period before results are inspected.

## 4. Data contract

The research retains the same eight interpretation channels as v2:

- DXY
- WTI
- S&P 500
- VIX
- Bitcoin
- gold
- U.S. 2-year Treasury yield
- U.S. 10-year Treasury yield

The v2 provider identities, freshness rules, pre-fill source provenance, limited calendar-alignment forward fill, Friday-ended resampling and complete-case requirements remain the reference data contract unless a separately versioned protocol amendment is registered before affected prospective evidence is used.

### Prospective data source

Beginning August 28, 2026, prospective v3 research should consume the **immutable as-published weekly input/reproduction artifacts** produced by the production pipeline wherever the required weekly raw level is present. It should not later rebuild the prospective holdout from revised Yahoo/FRED history merely because revised data improve a candidate result.

### Retrospective initialization snapshot

Historical data before the prospective boundary are not fully available as immutable as-published raw vintages. Before the first v3 candidate time series is calculated, implementation must therefore freeze and hash one current-vintage retrospective weekly-level matrix used to initialize state. That snapshot may not later be replaced to improve candidate performance.

## 5. Constants shared by all eligible v3 candidates

Unless a candidate explicitly specifies a different fixed weight structure:

- frequency: Friday-ended weekly observations;
- input type: weekly levels;
- minimum prior history: 52 complete weeks;
- week `t` normalization may use only observations strictly before `t`;
- z-score clipping: ±3.5;
- primary regime thresholds remain the existing v2 thresholds:
  - `>= +1.0`: Strong dollar regime
  - `+0.3 to < +1.0`: Firm dollar regime
  - `-0.3 to < +0.3`: Neutral / transitional
  - `-1.0 to < -0.3`: Soft dollar regime
  - `< -1.0`: Weak dollar regime
- thresholds are not eligible for optimization;
- no regression-fitted target weights are permitted; and
- production v2 remains unchanged throughout the research period.

Keeping the regime thresholds fixed is intentional: the primary experiment should not hide normalization or concentration changes by simultaneously retuning the language bands.

## 6. Incumbent benchmark

### `V2_BASELINE` — benchmark only

Current production v2 remains the incumbent comparison series. It is **not** an eligible v3 candidate under this protocol.

Weights:

| Driver | Weight |
| --- | ---: |
| DXY | +0.125 |
| WTI | -0.125 |
| S&P 500 | -0.125 |
| VIX | +0.125 |
| Bitcoin | -0.125 |
| Gold | -0.125 |
| U.S. 2Y | +0.125 |
| U.S. 10Y | +0.125 |

The benchmark remains useful because every prospective metric must be calculated over the same dates for v2 and the eligible v3 candidates.

## 7. Preregistered candidates

Only the following four candidate IDs are eligible. No fifth candidate may be added after the prospective holdout starts under protocol version 1.

### `V3_E52` — expanding prior-only mean/std

For week `t`:

- use all complete weeks strictly before `t`;
- require at least 52 prior weeks;
- compute arithmetic mean and sample standard deviation (`ddof=1`) for each driver;
- standardize the current weekly level;
- clip at ±3.5; and
- apply the unchanged v2 fixed weights.

This is the simplest direct fix for v2's historical normalization revision problem.

### `V3_R260` — 260-week prior-only mean/std

For week `t`:

- use exactly the prior 260 complete weeks;
- compute arithmetic mean and sample standard deviation (`ddof=1`);
- standardize the current weekly level;
- clip at ±3.5; and
- apply the unchanged v2 fixed weights.

The window is fixed at 260 weeks before prospective evidence. The previously studied 104/156/260 variants are known retrospective diagnostics; this protocol does not pretend that the historical comparison was unseen. Only 260 is carried forward as the preregistered rolling mean/std candidate.

### `V3_MAD260` — 260-week prior-only robust normalization

For week `t`:

- use exactly the prior 260 complete weeks;
- center each driver on its historical median;
- scale by `1.4826 × median(|x - median(x)|)`;
- clip at ±3.5; and
- apply the unchanged v2 fixed weights.

If a driver has zero robust scale, the candidate week must fail closed. A substitute scale may not be selected after observing the result.

This candidate asks whether a robust location/scale treatment is less sensitive to extreme historical observations without altering the driver interpretation or weights.

### `V3_GRP_MAD260` — robust normalization + ex-ante group-balanced weights

Normalization is identical to `V3_MAD260`. The only additional change is an ex-ante fixed grouping intended to stop the count of raw drivers from silently determining the influence of an interpretation channel.

Four groups receive equal **absolute** weight of 0.25:

| Group | Drivers | Fixed signed driver weights |
| --- | --- | --- |
| Direct dollar | DXY | DXY +0.25 |
| Commodity / store of value | WTI, gold | WTI -0.125; gold -0.125 |
| Risk / liquidity | S&P 500, VIX, Bitcoin | SPX -1/12; VIX +1/12; BTC -1/12 |
| Rates | U.S. 2Y, U.S. 10Y | +0.125 each |

The signs remain the existing transmission assumptions. The group weights are not fitted to returns, hit rates, correlations or any target.

## 8. Retrospective diagnostics

Historical checks through August 21, 2026 are required for engineering and interpretation, but they are explicitly marked **retrospective / not untouched**.

Required diagnostics include:

- finite score and regime coverage;
- week-to-week regime turnover;
- leave-one-driver-out regime agreement;
- fixed-threshold sensitivity;
- normalization-window sensitivity;
- rolling component correlations;
- ordinary contribution HHI/effective component count;
- absolute-correlation-adjusted contribution concentration heuristic;
- dominant absolute contribution share;
- net-to-gross contribution ratio;
- subperiod score distributions; and
- comparison with the current-vintage v2 recalculation.

The familiar 2015–16, 2018, March 2020, 2020–21 and 2022 windows may be shown for interpretation. Their sign hit rates may not determine the v3 winner.

## 9. Prospective primary endpoints

Every endpoint is calculated over exactly the same prospective weeks for v2 and each candidate.

### 9.1 Future-revision immunity — hard gate

Once a candidate week is stored from frozen as-of inputs and prior history, appending later weeks must not change that earlier score. Failure is disqualifying.

### 9.2 Median effective correlated component count — primary comparative endpoint

Use the preregistered contribution-concentration method already published for v2:

- form absolute contribution shares `p_i`;
- compute a 52-week prior component-correlation matrix where sufficient history exists;
- use the absolute-correlation-adjusted concentration `p'|R|p`; and
- report effective correlated components as its reciprocal.

Higher is preferred, but it is still a transparency heuristic—not a covariance portfolio-diversification measure.

### 9.3 Minimum leave-one-driver-out regime agreement

For each candidate, calculate eight fixed leave-one-driver-out variants and take the minimum prospective regime-label agreement. Higher indicates less dependence on a single input.

### 9.4 Regime turnover rate

Measure the share of consecutive prospective weeks in which the regime label changes. Lower is preferred only within the eligibility bounds; a nearly frozen indicator is not automatically superior.

### 9.5 Dominant absolute contribution share

Measure the median prospective fraction of gross absolute contribution supplied by the largest driver. Lower is preferred.

## 10. Eligibility gates

A candidate is excluded before ranking if any of the following occurs:

1. week-`t` normalization includes week `t` or a later observation;
2. a stored prospective week changes when later weeks are appended;
3. the candidate does not produce a finite score whenever its declared history is available, except an explicitly fail-closed zero-scale event;
4. implementation differs from the preregistered formula, weights, clip or thresholds;
5. prospective regime turnover exceeds **1.25×** the v2 turnover rate over the same weeks;
6. minimum leave-one-driver-out regime agreement is more than **5 percentage points below** v2 over the same weeks; or
7. promotion is being justified by retrospective anchor hit rate, future returns, strategy PnL or another non-preregistered outcome.

These gates deliberately allow the correct result to be “no v3 candidate justified promotion.”

## 11. Candidate-selection rule after 52 prospective weeks

No optimized composite score will be invented after seeing the data.

The fixed decision sequence is:

1. Exclude every candidate failing an eligibility gate.
2. Among eligible candidates, consider the candidate with the highest median prospective effective correlated component count **only if it exceeds the v2 benchmark by at least 10%** over the same prospective weeks.
3. If the leading candidates are within 5% of one another on that endpoint, prefer the candidate with higher minimum leave-one-driver-out regime agreement.
4. If still tied within 2 percentage points, prefer lower prospective regime turnover.
5. If still tied, use the fixed simplicity order: `V3_E52` → `V3_R260` → `V3_MAD260` → `V3_GRP_MAD260`.
6. If no candidate satisfies the gates and improvement condition, **keep v2 in production** and report that the preregistered study did not justify promotion.

## 12. Threshold sensitivity

Three threshold maps may be reported exactly as robustness diagnostics:

- narrower: neutral ±0.20, strong ±0.80;
- production-like: neutral ±0.30, strong ±1.00;
- wider: neutral ±0.40, strong ±1.20.

They may not be used to select new production thresholds under this protocol.

## 13. Reporting schedule and anti-peeking rules

Prospective candidate values may be stored weekly once research implementation is separately approved.

Interim reports are permitted after 13, 26 and 39 completed prospective weeks. Their purpose is transparency and defect detection, not candidate selection.

Formal selection review occurs only after **52 completed prospective weeks**.

If a genuine implementation defect requires changing a candidate formula or decision rule, USD Impact must:

1. publish a versioned protocol amendment;
2. state the reason before affected evidence is used for selection; and
3. reset the prospective holdout clock for every affected candidate.

Purely cosmetic documentation corrections do not reset the holdout.

## 14. Production promotion requires a separate decision

Even a candidate that wins the preregistered research does **not** automatically become production Score v3.

Production promotion additionally requires:

- a separate public Score v3 methodology document;
- a machine-readable v3 methodology contract;
- a separate code review changing the model version rather than overwriting v2 silently;
- an agreed parallel shadow period before replacing the public v2 score;
- confirmation that all production data-quality and reproducibility gates remain fail-closed; and
- compliance language that remains descriptive unless an entirely separate predictive protocol has succeeded.

## 15. Explicit exclusions

Protocol version 1 excludes:

- any production v2 change;
- a canonical 2008 v2/v3 backtest;
- regression-fitted driver weights;
- optimized regime thresholds;
- future-return or PnL optimization;
- adding a candidate because it looks good after August 28, 2026 data are observed; and
- claiming predictive validity from contemporaneous regime interpretation.

## 16. Expected institutional outcome

The purpose of preregistration is not to guarantee that v3 wins. It is to make a future conclusion credible in either direction:

- **promote a separately versioned v3** only if a preregistered candidate improves the intended robustness properties on genuinely prospective data without violating the guardrails; or
- **retain v2** if the alternatives do not clear the predeclared evidence bar.

That no-change outcome is a valid research result.
