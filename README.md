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
2. Build the weekly v2 score and deterministic English and Spanish commentary.
3. Rebuild the bilingual dashboards, bridge JSON, and dated archive.
4. Run `scripts/validate_weekly_release.py` before any remote write.
5. Commit generated files to an isolated `automation/weekly-usd-impact-*` branch.
6. Open a publication PR and dispatch `Weekly score quality` against the exact head SHA.
7. Squash-merge only after that exact quality run succeeds.
8. Allow Cloudflare Pages to deploy the validated `main` commit.
9. Verify production through the Saturday health workflow.

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
- For a failed weekly run, investigate the open publication branch or health issue before manually dispatching another run.

## Compliance

The USD Impact Score and its commentary are educational and informational. They are not investment, financial, or trading advice and are not recommendations to buy or sell any asset. Relationships can change by market regime, historical results do not indicate future results, and users should conduct independent research and consult qualified professionals where appropriate.
