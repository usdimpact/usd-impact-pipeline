# Issue #282 — FRED DGS2/DGS10 retention and publication inventory (2026-10-29)

**Status:** preliminary read-only source audit / review-only. **No permission, no Production change and no authority to delete history.**

## Evidence and scope

- FRED support reply dated 2026-10-29 to the USD Impact DGS2/DGS10 commercial/derived-use inquiry: permitted commercial use for appropriately labelled Public Domain datasets, with citation and disposal; states FRED terms do not permit retention/storage.
- [FRED legal terms, prohibited uses (q)](https://fred.stlouisfed.org/legal/#prohibitions) restrict storing, caching, archiving FRED content and incorporating it in databases or compilations. The separate FRED API clause (l) also addresses API caching/storage. The public-domain label is not a waiver of service terms.
- Existing [source-retention-policy.md](source-retention-policy.md) is last reviewed 2026-08-24. It prohibits raw response retention but describes provider-derived weekly evidence and public component artifacts. The Oct 29 support reply requires a more granular lineage and retention review.
- Existing [Score provider rights matrix](score-v2-provider-rights-evidence-matrix-2026-10-28.md), [containment plan](score-v2-public-rights-containment-plan-2026-10-27.md), [zero-budget fallback](score-zero-budget-fallback-2026-10-28.md), and [issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155) remain controlling research/hold references.

## Confirmed paths from read-only inspection of default branch

| Phase | Path / function | Evidence | Disposition |
|---|---|---|---|
| Source configuration | `usd_impact_score_v2.py`, `TICKERS` | UST_2Y=DGS2 and UST_10Y=DGS10, FRED transport | Confirmed FRED dependency; do not substitute silently |
| Fetch | `usd_impact_score_v2.py:fetch_fred()` | `https://fred.stlouisfed.org/graph/fredgraph.csv?id=...`, parsed into a daily pandas DataFrame | Confirmed source; check transient and persistent lifecycle |
| Merge | `usd_impact_score_v2.py`, `fetch_all_inputs()` | FRED and Yahoo frames joined into one daily matrix | Derived/in-memory mixing; characterize subsequent writes |
| Local exports | `usd_impact_score_v2.py:export_csv()`, `export_json()`, `_daily_cache.parquet` and output directories | Code contains disk-writing paths | Potential exposure; actual execution/retention not verified |
| Committed weekly input | `data/weekly_input_2026-10-23.json` | DGS2/DGS10 source and observation metadata under weekly driver entries | Confirmed committed persistence; weekly schema contains per-driver derived z-scores/contributions; source-specific rights unresolved |
| Public latest input | `public/data/weekly_input_latest.json` | Public driver entries with FRED source metadata | Confirmed public path; file contains UST_2Y/UST_10Y per-driver z-scores and contributions as well as source metadata; terms treatment unresolved |
| Historical public input | `public/archive/2026-10-23/weekly_input.json` and other dated archives | DGS2/DGS10 are present in dated public archive files | Confirmed archived persistence; enumerate full set |
| Public component histories | `public/data/usd_impact_score_v2.csv`, `public/data/usd_impact_score_v2.json`, `public/data/score_repro_bundle_latest.json` | Existing containment plan describes multiweek component values and weekly provider-derived values | Repo-document evidence; inspect exact current file schemas and deployment before remediation |
| Independent validation | `scripts/validate_weekly_release.py`, `public/data/score_v2_methodology.json` | DGS2/DGS10 embedded in source/provenance and release contracts | Metadata alone is not evidence of stored observations |

## Runtime production / persistence trace (source-level verified)

| Stage | Writer / carrier | Confirmed behavior | Rights-audit significance |
|---|---|---|---|
| Friday preflight | `.github/workflows/weekly.yml` | Scheduled Friday 22:00 UTC and manual dispatch both call `scripts.score_publication_rights_gate` **before** provider fetch | `governance/score-publication-rights-gate.json` is `hold` dated 2026-10-28. The `run-pipeline` job is gated on `rights_hold != 'true'`. No scheduled new-week publication generation is currently authorized |
| Read/merge | `usd_impact_score_v2.py:fetch_fred`, `fetch_all_inputs` | Downloads FRED CSV, aligns FRED 2Y/10Y with Yahoo drivers, normalizes and computes Score | Unapproved direct reruns can still process mixed data; entrypoints must be inventoried individually |
| CI runner-local | `usd_impact_score_v2.py` + `.github/workflows/weekly.yml` | Writes full weekly level matrix as CSV and daily fingerprint receipt in `$RUNNER_TEMP` for same-run strict reproduction | Ephemeral by design; exact runner retention, logs, workflow artifacts and failure-path cleanup need verification |
| Local `--test` mode | `usd_impact_score_v2.py:main` | Non-web mode may write the combined daily matrix to `_daily_cache.parquet`; `--web` does **not** write that parquet cache. `.gitignore` ignores cache/log paths | Distinguish local/development retention from current CI. Git ignore is not a storage permission or deletion mechanism |
| Logs | `setup_logging`, `compute_zscores` | Writes local `logs/usd_impact_score_v2.log` in web mode, streams to stdout; debug logging emits per-driver mean and standard deviation | GitHub Actions logs may contain derived normalization statistics even if Git never commits the local log. Determine retention/access and whether old logs exist |
| Public output generation | `export_csv`, `export_json` | Writes full Score history (617 weekly observations in 2026-10-23 committed JSON) including UST_2Y/UST_10Y component z-scores | Machine-readable derivative history under rights review |
| Commentary/bridge | `scripts/generate_weekly_commentary.py` | Writes `data/weekly_input_YYYY-MM-DD.json` and `public/data/weekly_input_latest.json`, including driver z-scores/contributions | Both Git-persistent and public latest outputs. Non-public directory naming alone does not prevent exposure in a public repository |
| Strict reproduction | `scripts/build_runtime_score_repro_bundle.py`, `scripts/build_score_repro_bundle.py` | Serializes per-driver weekly level, normalization mean/std, contribution and provider fingerprints to `public/data/score_repro_bundle_latest.json` | Highest concern because the public artifact includes levels and normalization moments, not just aggregate Score |
| Archive | `.github/workflows/weekly.yml` | Copies latest Score, bridge and reproduction bundle to `public/archive/<week>/...` | Dated persistence and Git history; future file deletion alone does not erase past Git objects or edge caches |
| Git publication candidate | `.github/workflows/weekly.yml` | Stages `git add public commentary data`, pushes branch and opens PR; human review/merge is separate | Committed derived output can enter public repository and later Pages deployment. No such new publication should proceed while HOLD |
| Cloudflare Pages delivery | `functions/_middleware.js`, `security/score-public-paths.mjs` | Dashboard HTML is restricted; precise data JSON/CSV paths and dated score/weekly_input/repro_bundle archives are explicitly public | Membership protection does **not** protect these allowlisted data paths. `governance/score-public-rights-surface.json` identifies Class C |
| Other paths | `.github/workflows/research-validation.yml`, `score-v3-shadow.yml`, `score-v2-predictive.yml` | Explicit rights-gate checks stop scheduled derived-data research ingestion/publication while HOLD | No evidence from source review of unauthorized new scheduled ingestion on these workflows |
| Ungated reproduction | `.github/workflows/repro-rehearsal.yml` on `main` at time of audit | Manual/selected PR rehearsal had no rights check despite a live `usd_impact_score_v2.py` call | Follow-up [draft PR #285](https://github.com/usdimpact/usd-impact-pipeline/pull/285) adds fail-closed gate. Its PR Actions rehearsal confirmed fetch step **skipped**, but it is not merged to `main` |
| Read-only attestation | `.github/workflows/repro-attestation.yml` | Reads already committed bundles; does not itself fetch live market data | Distinguish read-only verifier from reproduction rehearsal |

## Deployed endpoint verification (2026-10-29; read-only)

An independent browser fetch returned machine-readable content on each of these current URLs; no values were reproduced in this record:

- `https://score.usd-impact.com/data/weekly_input_latest.json` — current bridge values and source metadata were served.
- `https://score.usd-impact.com/data/score_repro_bundle_latest.json` — strict reproduction bundle with component evidence was served.
- `https://score.usd-impact.com/archive/2026-10-23/repro_bundle.json` — dated bundle served.
- `https://usd-impact-pipeline.pages.dev/data/weekly_input_latest.json` — legacy Pages endpoint served bridge data.
- `https://score.usd-impact.com/en/` — returned HTTP 403 (dashboard HTML protected).

These tests prove the stated endpoints were reachable/denied during inspection; they do not enumerate all cache nodes, older branches, domain variants or historic revisions. Do not equate HTTP 403 on HTML with protection for data endpoints. The public GitHub repository provides a separate distribution channel irrespective of Pages routing.

## Source-specific legal guardrails (not a legal conclusion)

- The current [FRED Terms of Use](https://fred.stlouisfed.org/legal/terms/) prohibit storing/caching/archiving FRED Content in full Terms clause **(q)** and separately address API caching in clause **(l)**. They also address AI/model development/training in clauses **(p)** and API **(k)**. Do not feed provider-derived observations into model-development workflows without separately established permission.
- FRED staff's 2026-10-29 email permits the described commercial use of properly tagged Public Domain datasets **subject to the full terms, source citations and disposal**. It is not permission for all series or all public derivatives.
- [Federal Reserve Board DDP transition notice](https://www.federalreserve.gov/data/data-download-fred-information.htm) confirms removal of custom **Build Your Package** the week of Nov 9, 2026, with preformatted packages to be retired subsequently; historical release XML remains a possible direct-source candidate. Ownership, exact automated-access license, retention, parity and continuity are **not approved**.

## Scope not yet verified

- Complete historic GitHub Actions run logs, artifacts, cache inventories, runner-local retention and cleanup proofs; Cloudflare cache coverage/TTL and alternate domain variants; Vercel/Supabase downstream copies; object storage/backups; old Git history/reflogs and third-party mirrors. The workflow commands and selected live Pages endpoints were verified above.
- Whether hashes, normalization moments, mixed-source aggregates, and independently computed non-reversible aggregate history qualify as FRED Content or prohibited derived works. **Do not assume either permission or prohibition; obtain written interpretation.**
- Whether the same H.15 observations can be sourced directly from the Federal Reserve Board, whether its license/terms permit the required retention/commercial use, and whether source and calendar parity can be demonstrated without changing Score methodology.
- Current workflow configuration is scheduled and rights-gated, but actual upcoming trigger outcomes and all external runners cannot be guaranteed merely from source inspection. The non-publishing live reproduction rehearsal gap is addressed **in draft only** by PR #285.


## Direct Federal Reserve Board H.15 candidate (public-source desk review)

- Official [H.15 Download Program](https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H15) offers a preformatted **Treasury Constant Maturities** CSV package and a complete release XML package.
- The [official package series listing](https://www.federalreserve.gov/datadownload/Review.aspx?filetype=csv&from=&label=include&lastObs=&layout=seriescolumn&rel=H15&series=bf17364827e38702b42a58cf8eaa3f78&to=&type=package) lists two-year `H15/H15/RIFLGFCY02_N.B` and ten-year `H15/H15/RIFLGFCY10_N.B` daily market yield observations. **Candidate mapping only**; no real-data parity assessment has been run.
- Federal Reserve Board's July 16, 2026 notice states that the DDP **Build Your Package** option will be removed during the week of **November 9, 2026** ahead of eventual DDP retirement. Do not design a new integration to depend on that UI path. Investigate release XML and enduring machine-readable Board alternatives, including deprecation support and allowed access/retention, before implementation.
- The Board is the originating H.15 publisher; that does **not** automatically resolve the Board's exact license/attribution/automated-access/storage terms, any FRED-derived historical provenance, or direct-source parity. Keep unknowns as HOLD.
- Future synthetic tests should validate daily date alignment, missing days, holiday handling, release timestamps, unit conventions, revision/vintage expectations, and strict fail-closed response parsing. **No live retrieval or activation in this PR.**

## Risk gates and next executable checks

1. **No additional live FRED fetch for this audit.** Use repository metadata and synthetic fixtures; never include actual provider-derived numeric values in issues, logs or PR descriptions.
2. Inventory all FRED-sourced disk writes, producer/consumer graphs, and persistence durations, including CI outputs and historical releases, with links and evidence classifications.
3. Record six distinct rights per source/transport: commercial access, internal use, transient processing, storage/retention, derived output, public dissemination. Unknown = HOLD. Include separately prohibited AI/model development use.
4. Research direct H.15 source at the Board under its actual terms and supply a synthetic-only adapter acceptance plan with observation calendar and parity tests; do not replace FRED or alter Score v2.
5. Seek written provider/counsel interpretation for aggregate-only derived Score/history, intermediate matrices, hashes and retention of old releases, without asserting that no-cost access implies rights.
6. Before any public artifact cleanup, obtain approved reversible migration, external cache/backup plan, privacy/legal review, reproducibility preservation and explicit release authorization.

## Acceptance checklist

- [x] Confirmed source code linkage to FRED DGS2 and DGS10.
- [x] Confirmed committed weekly and public archive data-file pathways.
- [x] Established material difference between public-domain series status and FRED delivery/retention terms.
- [x] Mapped current source-level Friday, archive, Git publication, Pages allowlist and rehearsal flow; confirmed public endpoint reachability.
- [ ] Completed historical job-log/backup/CDN and downstream persistence inventory.
- [ ] Confirmed retained value classes and rights interpretation.
- [ ] Evaluated direct H.15 terms and exact-source parity feasibility.
- [x] Draft PR #285 adds a workflow-policy regression test and demonstrates a safe no-fetch Actions rehearsal.
- [ ] Independent review and merge of PR #285; comprehensive source-rights gate / synthetic fixture tests.
- [ ] Obtained explicit legal/provider and release approvals.

This is a **review artifact only**. Issue #155 HOLD remains active. No existing data, workflows, public artifacts, method, credentials, entitlements, or production config are changed by this document.
