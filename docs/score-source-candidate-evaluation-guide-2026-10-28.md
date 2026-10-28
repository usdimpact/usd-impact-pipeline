# Score source candidate evaluation guide — 2026-10-28

Status: **review-only / no provider selected / issue #155 HOLD remains active**.

This guide standardizes how potential licensed/commercial-safe source replacements are evaluated under issue #179.

## Why this exists

The source-neutral adapter and synthetic parity path are now proven. The next risk is governance drift: choosing a provider because its API is convenient or because its values look close enough.

A candidate must pass two independent reviews:

1. **rights** — whether the intended internal, retained, derived and public uses are permitted;
2. **semantics/parity** — whether the candidate represents the same economic input expected by Score v2.

Passing one does not imply the other.

## Required rights fields

Every candidate must explicitly disposition:

- commercial internal use;
- retention;
- internal derived use;
- public aggregate Score/regime output;
- public component-derived output;
- machine-readable publication;
- historical archives.

Unknown means `pending`, not implied permission.

## Required semantic fields

Every candidate must document:

- exact instrument identity;
- exact field definition (close, settlement, index level, reference price, etc.);
- units;
- trading calendar;
- timezone/date boundary;
- revision policy;
- history start;
- adjustment convention;
- futures-continuation convention where applicable.

### Driver-specific non-negotiables

**DXY**
- must remain the intended ICE U.S. Dollar Index exposure;
- a broad-dollar proxy is not equivalent.

**WTI**
- must document front-contract/continuous-series construction;
- roll schedule and back-adjustment rules are material;
- spot WTI is not equivalent.

**SPX**
- must represent the S&P 500 index level;
- ETF proxies are not equivalent.

**VIX**
- must represent the VIX index;
- VIX futures are not equivalent.

**BTC**
- must define whether the series is single-venue spot, composite, or reference price;
- replacement of the historical Yahoo BTC-USD convention requires explicit parity evidence.

**GOLD**
- must document the continuous/front-contract construction;
- XAU spot is not automatically equivalent to GC futures.

## Parity progression

A candidate progresses through these stages:

1. `synthetic_adapter` — provider schema can normalize to canonical Score columns using synthetic data.
2. `daily_history` — authorized Development data matches or differences are fully characterized.
3. `weekly_levels` — Friday-ended weekly inputs match or documented deviations are approved.
4. `score_components` — z-scores/contributions match within the approved tolerance.
5. `aggregate_score` — aggregate Score matches within tolerance.
6. `regime` — regime classification matches.

Real-data stages must remain `not_run` until issue #155 and the source contract authorize Development use.

## Candidate decision states

- `pending` — evidence incomplete.
- `reject` — rights or semantics are incompatible.
- `hold` — potentially viable, but material evidence/terms remain unresolved.
- `eligible_for_development_rehearsal` — rights and semantic documentation are sufficient to request a separate Development real-data rehearsal.

None of these states authorize Production.

## Evidence quality

Acceptable evidence can include:
- provider agreement or written licensing response;
- official product documentation;
- authoritative field/calendar/roll methodology;
- provider support case/reference;
- approved internal legal/counsel disposition;
- reproducible parity report from authorized Development data.

Do not treat marketing pages, package documentation, delayed availability, or observed numerical similarity as rights evidence.

## Operational rule

Do not put credentials, API keys, confidential contract text, or provider-derived values into the candidate template.

Record only:
- provider/product identity;
- semantic description;
- rights disposition;
- non-secret references;
- parity outcome;
- conditions.

## Current boundary

The repository template deliberately contains no provider names and no pre-approved candidate. All rights fields start `pending`; all parity fields start `not_run`; Production authorization remains false.
