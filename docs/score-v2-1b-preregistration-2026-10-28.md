# Score v2.1B transformation and research preregistration — 2026-10-28

Status: **preregistered design only**.

This document freezes the first research specification for the official-macro v2.1B candidate before any real candidate data are run.

## 1. Core principle

The research must answer one question:

> Does the predeclared eight-slot official-macro architecture produce a robust, non-degenerate, point-in-time USD regime indicator under a zero-paid-data constraint?

The protocol is not allowed to evolve in response to observed results.

## 2. Frozen transformations

| Slot | Series | Frozen transformation | Reason |
|---|---|---|---|
| USD | DTWEXBGS | level | measures prevailing broad-dollar regime |
| Energy | DCOILWTICO | natural-log level | preserves price level while reducing multiplicative scale effects |
| Financial conditions | NFCI | level | index already represents financial tightness |
| Financial stress | STLFSI4 | level | index directly represents stress relative to normal |
| Liquidity | WALCL | 13-week log change | captures liquidity impulse rather than long-run balance-sheet trend |
| Real yield | DFII10 | level | prevailing real-rate pressure |
| 2Y Treasury | DGS2 | level | front-end nominal-rate pressure |
| 10Y Treasury | DGS10 | level | long-end nominal-rate pressure |

These choices are now frozen for the first candidate study.

## 3. Point-in-time availability

The candidate clock is Friday 23:59:59 America/New_York.

A data point is eligible only when it was genuinely available by that cutoff.

Observation dates are not sufficient evidence of availability.

Important source behavior already documented from official pages:

- H.10 broad-dollar data are released Monday at 4:15 p.m. ET for the previous business week.
- NFCI is released Wednesday at 8:30 a.m. ET and covers the previous Friday.
- WALCL is a Wednesday level released through H.4.1, normally the next day.
- H.15 is posted every business day at 4:15 p.m. ET.
- STLFSI4 is a Friday-ending weekly index released during the following week.

Therefore a historical candidate built by simply resampling observation dates to Friday would be invalid.

## 4. Weekly construction

For each completed Friday:

1. determine the Friday research cutoff;
2. consider only values actually released by that cutoff;
3. select the newest eligible value for each slot;
4. enforce each slot's maximum observation age;
5. apply the frozen transformation;
6. require all eight transformed slots;
7. if any slot is missing or stale, produce no candidate Score for that Friday.

There is no dynamic reweighting.

## 5. Normalization

The first v2.1B candidate uses expanding point-in-time normalization.

For week t:

- only complete candidate weeks strictly before t are normalization history;
- minimum history is 104 complete weeks;
- current week t is excluded from its own mean and standard deviation;
- sample standard deviation uses ddof=1;
- z-scores are clipped to ±3.5.

The output target starts 2015-01-02, while data collection may begin in 2013 to seed the two-year history requirement.

This deliberately avoids full-sample lookahead.

## 6. Formula

The first candidate retains equal absolute weights:

- USD +0.125
- Energy -0.125
- Financial conditions +0.125
- Financial stress +0.125
- Liquidity -0.125
- Real yield +0.125
- 2Y +0.125
- 10Y +0.125

The existing regime bands are retained for the first candidate research only so that source/architecture behavior can be evaluated before any threshold redesign.

## 7. Hard acceptance gates

A real-data candidate is rejected if any of these fail:

- rights/reuse scope documented for all eight slots;
- zero lookahead violations;
- availability provenance exists for every used weekly value;
- zero transform-domain failures;
- 104 prior complete weeks for each evaluated week;
- at least 97.5% complete candidate-week coverage;
- at least 98% eligible-week coverage for each slot;
- no more than two consecutive missing candidate weeks;
- no pairwise absolute Spearman correlation above 0.95;
- maximum VIF no greater than 12;
- first principal component explains no more than 70% of slot variance;
- at least four of the five preregistered historical anchor windows achieve >=55% expected-sign hit rate;
- no anchor window has expected-sign hit rate below 35%.

These numbers are fixed before results are viewed.

## 8. Review gates

The following trigger review rather than automatic acceptance:

- pairwise |Spearman| > 0.85;
- VIF > 8;
- first principal component > 60%;
- neutral regime > 70% of weeks;
- any one regime > 75% of weeks;
- positive non-neutral or negative non-neutral regimes below 5% of weeks;
- removing one slot changes more than 30% of regime labels.

A review gate cannot be solved by silently changing a threshold or deleting a slot.

## 9. Historical anchors

The first candidate uses the same five descriptive regime windows already present in the repository:

- 2015-16 oil/EM stress: expected positive;
- 2018 Fed tightening: expected positive;
- March 2020 funding stress: expected positive;
- April 2020-October 2021 post-Fed-liquidity phase: expected negative;
- 2022 tightening cycle: expected positive.

These are descriptive robustness anchors, not investment-return targets.

## 10. No predictive claim

The candidate remains a macro regime indicator.

This protocol does not authorize optimizing for:
- future equity returns;
- trading profits;
- Sharpe ratio;
- hit rates on investment decisions;
- any recommendation or investment claim.

## 11. Stop conditions

Research must stop rather than adapt if:

- a source requires paid licensing under the zero-budget constraint;
- release timing cannot be reconstructed conservatively;
- reuse rights are unresolved;
- a transformation domain is invalid;
- a hard gate fails;
- a proposed methodology change is suggested after results are visible.

Any revised candidate requires a new preregistration version.

## 12. Authorization boundary

This document does not authorize fetching or testing real candidate data.

The next real-data step requires a separate owner authorization after source reuse scope and historical availability rules are documented.
