# Score v2.1E timing, vintage and acceptance preregistration — 2026-10-28

Status: **preregistered design only**.

## Purpose

Freeze the first v2.1E research protocol before any real series observations are fetched or viewed.

The key methodological improvement over earlier candidates is that **historical vintage is treated as a first-class input**. A value is not eligible merely because its observation date precedes a Friday. It must be the version actually published and available at that Friday cutoff.

## Exact transforms

- H.10 broad dollar: level.
- BLS WPU0561 crude petroleum PPI: natural-log level.
- H.8 bank credit: negative 13-week log change.
- H.4.1 primary credit: log1p level.
- H.4.1 total assets: 13-week log change.
- H.15 10Y real yield: level.
- H.15 2Y nominal yield: level.
- H.15 10Y nominal yield: level.

## Friday clock

Each candidate week ends Friday at 23:59:59 America/New_York.

For every slot the research record must identify:
1. observation date;
2. publication/release date and time;
3. release/vintage identifier;
4. value as published in that vintage;
5. whether that vintage was available by the Friday cutoff.

## BLS energy vintage rule

BLS crude petroleum PPI WPU0561 is monthly.

BLS states recent PPI observations may be revised for four months. Therefore:
- current revised history cannot be used as a substitute for the originally available value;
- the historical study must reconstruct the release vintage available at each Friday;
- archived BLS PPI release evidence must bind the value;
- if a required vintage cannot be reconstructed conservatively, the candidate week fails closed.

The monthly value may be carried across weekly Score dates only after it has actually been released, up to a maximum age of 50 calendar days.

## H.8 bank-credit vintage rule

H.8 can undergo benchmark revisions, reclassifications and corrections.

The study must use the value present in the H.8 release available at the historical Friday cutoff.

Latest revised H.8 history is not a valid point-in-time replacement.

## H.4.1 and H.15

H.4.1 Wednesday levels become eligible only after the Thursday release.

H.15 values are eligible only when contained in a posted H.15 release. Observation date alone does not prove same-day availability.

## H.10

H.10 normally publishes the previous business week's daily broad-dollar observations the following Monday.

Therefore the broad-dollar slot is deliberately lagged in a Friday Score. The protocol does not backfill the current business week from information that was unavailable at the Friday cutoff.

## Normalization

The candidate uses expanding point-in-time normalization:
- minimum 104 prior complete candidate weeks;
- current week excluded from its own history;
- sample standard deviation, ddof=1;
- z-score clipping at ±3.5;
- no full-sample normalization.

## Sparse primary-credit safeguards

Primary Credit can remain low or unchanged for long periods.

For every 104-week normalization window the transformed stress slot must:
- have at least 5 unique values;
- not have one transformed value occupy more than 95% of the window.

Review is triggered below 10 unique values or above an 80% single-value share.

This tests whether the stress slot is informative enough to standardize without choosing the rule after seeing results.

## Hard gates

The candidate fails if:
- source/reuse scope is undocumented for any slot;
- any lookahead occurs;
- any used value lacks exact release-vintage provenance;
- current revised BLS/H.8 history is substituted for historical vintages;
- a transform-domain error occurs;
- fewer than 104 prior complete weeks exist;
- complete candidate-week coverage is below 97.5%;
- any slot's eligible-week coverage is below 98%;
- more than two candidate weeks are consecutively missing;
- absolute pairwise Spearman exceeds 0.95;
- VIF exceeds 12;
- first principal component exceeds 70% of variance;
- primary-credit sparsity hard gates fail;
- fewer than four of five anchor windows reach 55% expected-sign hit rate;
- any anchor window falls below 35%.

These thresholds are frozen before results are visible.

## No rescue tuning

A failed candidate cannot be rescued by:
- changing transforms;
- changing a hard threshold;
- dropping a slot;
- reweighting the remaining slots;
- using latest revised history;
- inserting a new proxy.

Any such proposal requires a new methodology version and new preregistration.

## Authorization boundary

No real data may be fetched or analyzed under this preregistration.

The next step, after CI validation, remains a separate owner authorization for real-data research.
