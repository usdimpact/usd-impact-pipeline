# USD Impact Score weekly pipeline

This repository calculates and publishes the bilingual Weekly USD Impact Score. The production contract is deliberately fail-closed: generation happens away from `main`, the complete release is validated on its exact commit, and only a passing publication pull request can reach the Cloudflare Pages deployment.

## Authoritative automation

Only workflow files inside `.github/workflows/` are executable GitHub Actions workflows.

| Workflow | Schedule | Responsibility |
| --- | --- | --- |
| `weekly.yml` | Friday 22:00 UTC | Generate the score, commentary, bridge data, dashboards, and dated archive; open and merge a guarded publication PR. |
| `quality.yml` | PR, push, or manual dispatch | Compile Python, run the offline regression suite, and validate the committed weekly release. |
| `weekly-recovery.yml` | Saturday 00:15 UTC | Dispatch one catch-up run only when the expected weekly run failed, is stale, or never arrived. |
| `weekly-health.yml` | Saturday 02:00 UTC | Verify the completed workflow, deployed bridge JSON, and English and Spanish dashboards. |

The root-level `weekly.yml` is a non-executable compatibility pointer. The canonical workflow is `.github/workflows/weekly.yml`.

## Publication sequence

1. Fetch DXY, WTI, S&P 500, VIX, Bitcoin, gold, and the U.S. 2-year and 10-year Treasury yields.
2. Record the provider, series, source URL, and latest raw observation date for every driver before holiday forward filling.
3. Reject the run if the score week is not the latest completed Friday or any source is missing, future-dated, or beyond its driver-specific freshness limit.
4. Build the weekly v2 score and deterministic English and Spanish commentary.
5. Rebuild the bilingual dashboards, bridge JSON, and dated archive.
6. Run `scripts/validate_weekly_release.py` before any remote write.
7. Commit generated files to an isolated `automation/weekly-usd-impact-*` branch.
8. Open a publication PR and dispatch `Weekly score quality` against the exact head SHA.
9. Squash-merge only after that exact quality run succeeds.
10. Allow Cloudflare Pages to deploy the validated `main` commit.
11. Verify production through the Saturday health workflow.

A generation, test, validation, PR, or merge failure leaves the previous production release unchanged.

## Reproducible environment

Python 3.11 is the production runtime.

- `requirements.txt` contains the human-maintained direct dependency ranges.
- `requirements.lock` contains the exact direct and transitive versions used by production and CI.
- GitHub Actions are pinned to immutable revisions, with the reviewed major version retained in a comment.

Create a clean local environment with:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip==26.2.1
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip check
```

Dependency upgrades must be isolated in a dedicated PR and must not be combined with score-methodology changes.

## Verification

Run the same deterministic checks used by quality CI:

```bash
python -m compileall -q usd_impact_score_v2.py scripts tests
python -m unittest discover -s tests -v
python scripts/validate_weekly_release.py
```

The offline regression test builds a complete release from `tests/fixtures/weekly_levels.csv`. It exercises score calculation, CSV and JSON export, bilingual commentary, bridge generation, dashboard rendering, archiving, archive indexing, and final release validation without contacting Yahoo or FRED.

## Output contract

The main website bridge is:

```text
data/weekly_input_YYYY-MM-DD.json
```

The public latest copy is:

```text
public/data/weekly_input_latest.json
```

Other production outputs include:

- `public/data/usd_impact_score_v2.csv`
- `public/data/usd_impact_score_v2.json`
- `public/en/index.html`
- `public/es/index.html`
- `public/archive/YYYY-MM-DD/`
- `commentary/latest_en.md`
- `commentary/latest_es.md`
- `commentary/latest.md`, maintained as an exact English compatibility alias

### Source provenance and freshness

Beginning with the 2026-08-14 release, both score JSON and bridge JSON must contain the same `source_provenance` object for all eight drivers. Each entry records:

- canonical driver name;
- provider and provider code;
- provider series or ticker;
- direct source URL;
- raw observation date used for the score week;
- score week, calendar age, configured maximum age, and `fresh` status; and
- retrieval mode, which must be `live` for a publishable release.

Freshness limits are operational publication safeguards, not score inputs. Bitcoin may be at most two calendar days old; DXY, WTI, S&P 500, VIX, and gold may be at most three days old; and the FRED 2-year and 10-year Treasury series may be at most four days old. These limits accommodate ordinary market holidays and known provider publication timing while rejecting a driver that has stopped updating for a full weekly cycle.

The pipeline captures provenance before its existing limited forward fill. A value copied forward for calendar alignment therefore retains its true provider observation date instead of being mislabeled as a Friday observation.

Releases dated through 2026-08-07 remain valid legacy artifacts and are not rewritten. All newly generated releases include provenance version 1 and fail validation if the provenance is missing or inconsistent.

## Methodology and historical vintages

USD Impact Score v2 standardizes each component against the full available sample, clips z-scores at ±3.5, and applies fixed equal-magnitude transmission weights.

Because the mean and standard deviation use the full sample available at each run, adding a new observation can revise previously calculated historical values and, occasionally, historical regime labels. Dated archive folders preserve what was actually published at each release. The current dashboard history is a recalculation using the latest full sample; it is not an immutable series of as-published vintages.

The generated backtest is descriptive across selected historical regime windows. It is not an out-of-sample forecast, a trading strategy, or evidence of guaranteed future performance. Current results must be read from `public/data/backtest_results.json`; documentation must not hard-code a hit rate.

## Change-safety rules

- Never push generated releases directly to `main`.
- Never weaken `scripts/validate_weekly_release.py` to make a failing release pass.
- Keep dependency, infrastructure, and methodology changes in separate PRs.
- Do not change weights, regime thresholds, data transformations, or source tickers without a separately versioned methodology review.
- Preserve dated archives and previously published commentary.
- Never bypass a freshness failure by editing observation dates, age limits, status fields, or retrieval mode in generated JSON.
- For a failed weekly run, investigate the open publication branch or health issue before manually dispatching another run.

## Compliance

The USD Impact Score and its commentary are educational and informational. They are not investment, financial, or trading advice and are not recommendations to buy or sell any asset. Relationships can change by market regime, historical results do not indicate future results, and users should conduct independent research and consult qualified professionals where appropriate.
