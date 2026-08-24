# USD Impact Score weekly pipeline

This repository calculates and publishes the bilingual Weekly USD Impact Score. The production contract is deliberately fail-closed: generation happens away from `main`, the complete release is validated on its exact commit, and only a passing publication pull request can reach the Cloudflare Pages deployment.

## Authoritative automation

Only workflow files inside `.github/workflows/` are executable GitHub Actions workflows.

| Workflow | Schedule / trigger | Responsibility |
| --- | --- | --- |
| `weekly.yml` | Friday 22:00 UTC | Generate the score, immutable reproduction bundle, commentary, bridge data, dashboards, and dated archive; open and merge a guarded publication PR. |
| `quality.yml` | PR, push, or manual dispatch | Compile Python, verify the machine-readable methodology contract, run the offline regression suite, and validate the committed weekly release. |
| `weekly-recovery.yml` | Saturday 00:15 UTC | Dispatch one catch-up run only when the expected weekly run failed, is stale, or never arrived. |
| `weekly-health.yml` | Saturday 02:00 UTC | Verify the completed workflow, deployed bridge JSON, and English and Spanish dashboards. |
| `research-validation.yml` | Saturday 04:30 UTC / guarded path pushes | Publish research-only point-in-time and robustness diagnostics plus an as-published-versus-current revision audit, without blocking the core weekly score. |
| `repro-rehearsal.yml` | Relevant PRs or manual dispatch | Run a live, non-publishing rehearsal of the complete score → bundle → archive → strict offline-reproduction path. A pass is explicitly not production acceptance evidence. |
| `repro-attestation.yml` | Relevant PRs, pushes to `main`, or manual dispatch | Read-only reproduction verification before merge and after merge. Only a successful push-to-`main` attestation can mark a strict release as a production acceptance candidate. |

The root-level `weekly.yml` is a non-executable compatibility pointer. The canonical workflow is `.github/workflows/weekly.yml`.

## Publication sequence

1. Verify that the machine-readable v2 methodology contract still matches production constants.
2. Fetch DXY, WTI, S&P 500, VIX, Bitcoin, gold, and the U.S. 2-year and 10-year Treasury yields once for the release run.
3. Record the provider, series, source URL, and latest raw observation date for every driver before holiday forward filling.
4. Reject the run if the score week is not the latest completed Friday or any source is missing, future-dated, or beyond its driver-specific freshness limit.
5. Build the weekly v2 score.
6. Hand the exact same-run complete weekly input matrix and a hashes-only provider-derived daily evidence receipt to the bundle step through non-public ephemeral files; freeze and independently verify `public/data/score_repro_bundle_latest.json` from the latest weekly levels, normalization moments, z-scores, weights, contributions, source provenance, daily and weekly complete-matrix/per-driver SHA-256 fingerprints, pipeline SHA, and dependency-lock hash.
7. Generate deterministic English and Spanish commentary, bridge data, and dashboards.
8. Archive the score, bridge, dashboards, and reproduction bundle under `public/archive/YYYY-MM-DD/`.
9. Run `scripts/validate_weekly_release.py` before any remote write. Beginning with 2026-08-28, this independently recomputes the release from the frozen archived bundle and requires the latest/archive bundles to match.
10. Commit generated files to an isolated `automation/weekly-usd-impact-*` branch.
11. Open a publication PR and dispatch `Weekly score quality` against the exact head SHA.
12. Run the read-only reproduction attestation on the PR. For strict releases it can prove the bundle and archive are internally reproducible, but a PR run is always pre-merge evidence and cannot mark production acceptance.
13. Squash-merge only after the required quality/reproduction gates succeed.
14. Allow Cloudflare Pages to deploy the validated `main` commit.
15. Run the read-only push-to-`main` reproduction attestation and the Saturday health checks. Only the successful push-to-`main` attestation can identify a 2026-08-28-or-later strict release as a production acceptance candidate.

A generation, data-quality, test, validation, PR, merge, deployment, or attestation failure never authorizes weakening the methodology or publication contract.

## Reproducible environment

Python 3.11 is the production runtime.

- `requirements.txt` contains the human-maintained direct dependency ranges.
- `requirements.lock` contains the exact direct and transitive versions used by production and CI.
- GitHub Actions are pinned to immutable revisions, with the reviewed major version retained in a comment.
- Every strict reproduction bundle records the SHA-256 of `requirements.lock`.

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
python -m scripts.validate_methodology_contract --json
python -m unittest discover -s tests -v
python scripts/validate_weekly_release.py
```

The offline regression suite exercises score calculation, CSV/JSON export, bilingual commentary, bridge generation, dashboard rendering, archiving, archive indexing, frozen-bundle reproduction, methodology-contract parity, and final release validation without relying on later Yahoo/FRED revisions.

### Non-publishing live acceptance rehearsal

`repro-rehearsal.yml` exists to remove execution risk before the first strict production bundle. It:

- uses live Yahoo/FRED source retrieval and the locked production environment;
- copies the repository into an ephemeral runner directory;
- executes the same score, bundle, commentary, dashboard, and archive sequence used by the Friday workflow;
- invokes the strict archived-bundle validator directly even when the currently completed week is still a legacy release;
- writes only a CI job summary/report inside the ephemeral runner; and
- contains no Git push, PR creation/merge, deployment, or production-write path.

A rehearsal result is always labelled `rehearsal_only: true` and `acceptance_evidence: false`. It cannot substitute for the first genuine 2026-08-28-or-later as-published release.

### Pre-merge and post-merge attestation

`repro-attestation.yml` is read-only and runs on relevant release/methodology pull requests as well as relevant pushes to `main`.

For a pull request it:

- validates the public methodology contract against production constants;
- records legacy status for releases before 2026-08-28; or
- for 2026-08-28 and later, independently reproduces the frozen bundle without downloading market history, verifies latest/archive bundle identity, checks the dependency-lock hash, and confirms the bundle's pipeline Git SHA is an ancestor of the checked-out PR commit.

A pull-request run is always labelled `pull_request_premerge` and cannot set `acceptance_candidate: true`.

After the release lands on `main`, the same workflow runs again in `main_post_merge` context. Only that push-to-`main` context can set `acceptance_candidate: true` for a strict 2026-08-28-or-later release after every frozen-bundle check passes.

Manual/local read-only runs are also never production acceptance candidates. The workflow records its result in the immutable GitHub Actions run/job summary and does not regenerate or mutate the release.

## Output contract

The main website bridge is:

```text
data/weekly_input_YYYY-MM-DD.json
```

The public latest copy is:

```text
public/data/weekly_input_latest.json
```

Other production/review outputs include:

- `public/data/usd_impact_score_v2.csv`
- `public/data/usd_impact_score_v2.json`
- `public/data/score_repro_bundle_latest.json` for newly generated strict releases
- `public/data/score_v2_methodology.json`
- `public/data/score_v2_methodology.schema.json`
- `public/data/score_v2_data_semantics.json`
- `public/data/score_v2_data_semantics.schema.json`
- `public/data/research/score_v2_robustness_latest.json`
- `public/data/research/score_v2_point_in_time_latest.json`
- `public/data/research/score_v2_vintage_comparison_latest.json`
- `public/data/research/score_v2_vintage_comparison_latest.csv`
- `public/en/index.html`
- `public/es/index.html`
- `public/archive/YYYY-MM-DD/`
- `commentary/latest_en.md`
- `commentary/latest_es.md`
- `commentary/latest.md`, maintained as an exact English compatibility alias

### Machine-readable methodology contract

`public/data/score_v2_methodology.json` is the public, machine-readable production specification. It freezes the public contract for:

- the eight providers/series and freshness limits;
- fixed signed weights;
- 2015-01-01 production start date;
- Friday-ended weekly resampling;
- full-sample weekly-level normalization;
- sample standard deviation with `ddof=1`;
- ±3.5 z-score clipping;
- limited three-observation daily forward fill and complete-case weekly requirement;
- fixed regime thresholds;
- no explicit correlation adjustment or weight rebalancing;
- reproduction-bundle version/boundary; and
- explicit descriptive/non-predictive scope boundaries.

`scripts/validate_methodology_contract.py` reconstructs the expected public contract directly from `usd_impact_score_v2.py` constants and fails CI on any mismatch. `score_v2_methodology.schema.json` is supplied for third-party JSON tooling. Methodology changes therefore require a deliberate code + public-contract update rather than silently drifting in one layer.

### Machine-readable data semantics

`public/data/score_v2_data_semantics.json` supplements—without changing—the frozen production methodology contract. It discloses the exact Yahoo `Close` field and `auto_adjust=True` retrieval choice, FRED observation-date field, outer-join and three-observation holiday fill, Friday-ended last-observation rule, and the absence of retained intraday settlement/publication timestamps.

For WTI (`CL=F`) and gold (`GC=F`), it also makes the replication boundary explicit: the pipeline consumes Yahoo's provider-defined continuous front-month histories and does not independently control contract selection, roll calendars, or back adjustment. A cross-vendor live reconstruction must not assume identical history. From the strict-release boundary, the reproduction bundle freezes the actual weekly levels used. `scripts/validate_data_semantics_contract.py` fails CI if these disclosures drift from the implementation.

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

Releases dated through 2026-08-07 remain valid provenance-legacy artifacts and are not rewritten. Releases from 2026-08-14 onward require provenance version 1.

### Immutable score reproduction boundary

Releases through 2026-08-21 predate the immutable reproduction-bundle publication contract and remain explicit legacy artifacts. Beginning with 2026-08-28, a release cannot pass validation unless:

- the latest and dated archived reproduction bundles both exist and match;
- each component's frozen weekly level, mean, sample standard deviation, unclipped/clipped z-score, fixed weight, and contribution independently recompute;
- the re-summed score and regime equal the published values within the fixed tolerance;
- source identity/provenance agree with the release metadata;
- the dependency-lock SHA-256 matches the checked-in lockfile; and
- the bundle carries a valid pipeline Git SHA and canonical methodology metadata.

The strict validator performs this proof from the frozen artifact; it does not download revised Yahoo/FRED history.

The production score and bundle steps use one provider fetch. The exact complete weekly input matrix and hashes-only daily evidence receipt are passed between those steps only inside the runner and are blocked from the public output tree. The public bundle records canonical SHA-256 fingerprints for the complete weekly matrix, the pre-forward-fill provider-derived daily matrix, and each driver at both stages. This detects later source-history changes without redistributing the full provider-derived history. It also freezes the latest weekly levels and all calculation moments needed to reproduce the published score.

These fingerprints are not a substitute for a complete raw-data archive: they begin after field selection and numeric parsing, original transport bytes are not hashed, and raw Yahoo/FRED response payloads and the full provider-derived history are not published or claimed as archived. The conservative rights and access-control boundary is documented in [`docs/source-retention-policy.md`](docs/source-retention-policy.md).

## Methodology and historical vintages

USD Impact Score v2 standardizes each component against the full available sample, clips z-scores at ±3.5, and applies fixed equal-magnitude transmission weights.

Because the mean and standard deviation use the full sample available at each run, adding a new observation can revise previously calculated historical values and, occasionally, historical regime labels. Dated archive folders preserve what was actually published at each release. The current dashboard history and current-vintage robustness research are recalculations using the latest source history; they are not immutable series of as-published historical values.

The JSON and CSV vintage-comparison artifacts measure this difference directly. They compare only the declared latest observation in each valid dated archive with the same score week in the current recalculation, publish file hashes, and explicitly list invalid legacy archives instead of repairing or silently accepting them. The audit is descriptive and first-party. It cannot separate expanding-sample normalization effects from upstream provider revisions, and it is not independent audit evidence or an out-of-sample predictive test.

The generated legacy backtest is descriptive across selected historical regime windows. The point-in-time and robustness research explicitly tests normalization/specification sensitivity, including leave-one-out and adversarial sign flips. It also publishes score-distribution and consecutive regime-duration diagnostics, which the generated dashboards visualize. Neither is a predictive forecast test, a trading strategy, or evidence of guaranteed future performance. Current research results must be read from the published JSON artifacts rather than hard-coded into operational documentation.

A separate [Score v2 one-week DXY predictive protocol](docs/score-v2-predictive-preregistration.md) was preregistered on August 25, 2026, before its first eligible origin on August 28. It requires 52 consecutive, non-backfilled future predictions and does not authorize any current predictive or trading claim. Earlier information was available when Score v2 and the prediction rule were selected and is explicitly treated as retrospective design information, not untouched test evidence.

## Change-safety rules

- Never push generated releases directly to `main`.
- Never weaken `scripts/validate_weekly_release.py` to make a failing release pass.
- Never treat a rehearsal as production acceptance evidence.
- Never treat a pre-merge or manual attestation as production acceptance evidence.
- Keep dependency, infrastructure, research, and production-methodology changes separable and reviewable.
- Do not change weights, regime thresholds, data transformations, or source tickers without a separately versioned methodology review.
- Update the machine-readable methodology contract in the same explicitly versioned methodology review whenever production constants intentionally change.
- Preserve dated archives and previously published commentary.
- Never bypass a freshness failure by editing observation dates, age limits, status fields, or retrieval mode in generated JSON.
- For a failed weekly run, investigate the open publication branch or health issue before manually dispatching another run.

## Compliance

The USD Impact Score and its commentary are educational and informational. They are not investment, financial, or trading advice and are not recommendations to buy or sell any asset. Relationships can change by market regime, historical results do not indicate future results, and users should conduct independent research and consult qualified professionals where appropriate.
