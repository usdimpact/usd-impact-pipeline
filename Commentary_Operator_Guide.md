# Weekly USD Impact Score — Operator Guide

This guide describes the current automated production system. It replaces the original manual-commentary routine while preserving the same principles: deterministic output, a complete dated archive, explicit methodology limits, and no trade recommendations.

## Operating model

The weekly score, English commentary, Spanish commentary, bridge data, dashboards, and archive are generated as one release. Operators do not edit `commentary/latest*.md` during a normal weekly cycle.

The authoritative workflow is `.github/workflows/weekly.yml`:

1. Friday at 22:00 UTC, the workflow runs the score pipeline with the locked Python environment.
2. The pipeline records and validates the raw observation date and canonical source identity for each of the eight drivers.
3. Commentary is generated deterministically from the score JSON. No external model or current-event narrative is introduced.
4. The English and Spanish dashboards are rebuilt with the matching commentary.
5. The complete release is archived under its score date.
6. Local consistency validation must pass before the workflow creates a publication branch.
7. A pull request is opened from that isolated branch.
8. `Weekly score quality` is dispatched against the exact publication commit.
9. The PR is squash-merged only when that exact run passes.
10. Cloudflare Pages deploys the resulting `main` commit.

The previous production release remains live if any step fails.

## Normal weekly verification

The normal operator task is verification, not writing.

After the Friday run, confirm:

- `Weekly USD Impact Score` completed successfully.
- The automated publication PR was merged rather than left open.
- The PR head SHA has a successful `Weekly score quality` run.
- `public/data/weekly_input_latest.json` reports the intended Friday date.
- The score and bridge JSON contain identical provenance for all eight drivers, each with `status: fresh` and `retrieval_mode: live`.
- The English dashboard contains `Automated Regime Commentary` and the same date.
- The Spanish dashboard contains `Comentario Automático de Régimen` and the same date.
- The dated archive contains `en.html`, `es.html`, `score.json`, and `weekly_input.json`.
- `commentary/latest.md` exactly matches `commentary/latest_en.md`.

The Saturday health workflow automates the production-facing portion of this checklist.

## Recovery and incident handling

### Automatic recovery

At 00:15 UTC Saturday, `weekly-recovery.yml` inspects the latest `weekly.yml` run on `main`.

- It skips recovery when a recent run succeeded.
- It skips recovery while the latest run is queued or still running.
- It dispatches one catch-up run when the latest run failed, is stale, or is absent.

The recovery workflow does not bypass the publication PR or exact-commit quality gate.

### Health failure

At 02:00 UTC Saturday, `weekly-health.yml` verifies GitHub Actions and the deployed Cloudflare Pages outputs. If a check fails, it opens or updates one issue titled `Weekly USD Impact pipeline requires attention`.

When that issue appears:

1. Open the linked weekly workflow run and identify the first failed step.
2. Confirm that `main` and the live dashboard still contain the last validated release.
3. Inspect any open `automation/weekly-usd-impact-*` PR before dispatching another run.
4. Fix code or data handling on a dedicated branch; do not edit generated production files to bypass validation.
5. Rerun the affected workflow only after the cause is understood.
6. Rerun the health workflow after deployment. A successful check comments on and closes the health issue.

### Source freshness failure

The pipeline fails before publication when a canonical input has no usable observation, reports an observation after the intended score week, exceeds its age limit, or would produce a score for an older Friday. This behavior protects against silent partial-source publication.

When the failure names a driver:

1. Open the failed workflow log and record the driver, observation date, calculated age, and configured limit.
2. Check the canonical provider page recorded in the source contract; do not substitute an unofficial value directly into generated output.
3. Determine whether the provider is delayed, the ticker/series failed, or the fetch library returned incomplete data.
4. Preserve the previous live release while the source is investigated.
5. Fix fetch handling on a dedicated branch when the provider has current data but the pipeline cannot retrieve it.
6. Change a freshness limit only through a separately reviewed operational-policy PR supported by evidence of normal provider timing.
7. Rerun the weekly workflow after the source or code issue is resolved. Do not edit `observation_date`, `age_days`, `status`, or `retrieval_mode` in generated JSON.

### Manual dispatch

Manual execution is appropriate for a verified recovery or a controlled release test. It is not a substitute for diagnosing repeated source-data, dependency, or validation failures.

Before manual dispatch, confirm that no weekly or recovery run is queued or in progress. The weekly concurrency group does not cancel in-progress work, so duplicate runs can queue and waste time even though the publication guard protects production.

## Generated commentary contract

The generator derives commentary only from the completed score payload:

- latest score and regime;
- week-over-week and four-week changes;
- positive and negative contribution breadth;
- three largest absolute component contributions; and
- nearest regime boundary.

The output must continue to state what the score does and does not mean. It must not add forecasts, event claims, causal certainty, performance promises, or buy/sell language.

English and Spanish are both required for every release. `commentary/latest.md` is an exact English compatibility alias and must never remain on an older date.

## File ownership

| Path | Owner | Rule |
| --- | --- | --- |
| `usd_impact_score_v2.py` | Score pipeline | Methodology changes require a separately versioned review. |
| `scripts/generate_weekly_commentary.py` | Commentary generator | Must remain deterministic and bilingual. |
| `scripts/validate_weekly_release.py` | Publication guard | Must fail closed; never weaken it to publish. |
| `commentary/latest*.md` | Generator | Do not hand-edit during normal operation. |
| `commentary/archive/` | Immutable release history | Never delete or rewrite a published edition. |
| `public/archive/` | Immutable dashboard/data history | Preserve complete dated snapshots. |
| `requirements.lock` | Production environment | Update only through a dedicated dependency PR. |
| Source provenance in score/bridge JSON | Score pipeline and commentary generator | Must describe the raw provider observations and match exactly across both files. |

## Source freshness contract

The source guard is operational and does not modify the v2 methodology. It runs before scoring and records provenance before the existing holiday-calendar forward fill.

| Driver | Provider series | Maximum age at score week |
| --- | --- | ---: |
| DXY | Yahoo Finance `DX-Y.NYB` | 3 calendar days |
| WTI | Yahoo Finance `CL=F` | 3 calendar days |
| S&P 500 | Yahoo Finance `^GSPC` | 3 calendar days |
| VIX | Yahoo Finance `^VIX` | 3 calendar days |
| Bitcoin | Yahoo Finance `BTC-USD` | 2 calendar days |
| Gold | Yahoo Finance `GC=F` | 3 calendar days |
| U.S. 2-year Treasury yield | FRED `DGS2` | 4 calendar days |
| U.S. 10-year Treasury yield | FRED `DGS10` | 4 calendar days |

The limits allow ordinary holidays and routine FRED publication lag but reject a driver that is effectively one weekly cycle behind. A publishable release must also use live retrieval. Cached input mode remains available for development but cannot satisfy the post-2026-08-14 publication contract.

## Methodology interpretation

The v2 score uses full-sample standardization. At each run, the current sample mean and standard deviation are applied across the complete history. This has two consequences:

1. The current dashboard can revise earlier historical score values when new observations are added.
2. A historical backtest computed from the current full sample is descriptive and contains information from the later sample in its normalization.

Therefore, do not describe the v2 backtest as out-of-sample, free of look-ahead, predictive, or a trading strategy. Do not hard-code a hit rate in commentary or documentation. The generated `public/data/backtest_results.json` is the current descriptive result.

Dated archives are the authoritative record of what readers actually saw at publication time. When comparing one week with another, specify whether the comparison uses:

- the latest recalculated historical series; or
- the as-published values from dated archives.

The automated commentary currently uses the internally consistent recalculated series from the current run.

## Safe change procedure

Before changing pipeline behavior:

1. Record the current `main` commit and confirm the latest weekly, quality, recovery, and health runs are green.
2. Create a dedicated branch from that exact commit.
3. Keep the PR limited to one change class: dependencies, operations, rendering, or methodology.
4. Run compile checks, the complete offline unit suite, and release consistency validation.
5. Compare `public/data`, `commentary`, and `public/archive` against the base commit.
6. For a non-methodology PR, require zero unexplained score, regime, weight, threshold, or historical-series changes.
7. Open the PR as a draft and inspect the remote diff before requesting merge.
8. Keep the PR unmerged if any generated output changes unexpectedly.

Methodology experiments should use a separate v3/shadow path. They must not replace v2 production outputs until the comparison period, acceptance criteria, documentation, and migration plan are approved.

## Monthly governance review

On the first Saturday of each month:

- review weekly and health run reliability;
- review dependency and action updates without merging them automatically;
- confirm archives are continuous or document missing editions caused by incidents;
- compare current recalculated history with dated as-published values;
- review the descriptive backtest language and compliance wording; and
- confirm no stale manual commentary or unused workflow definition can be mistaken for production.

## Compliance

The score and commentary are educational and informational. They are not investment, financial, or trading advice and are not recommendations to buy or sell any asset. Relationships can change by regime. Historical results do not indicate future results. Operators must preserve source transparency, methodology limitations, and the dated audit trail.
