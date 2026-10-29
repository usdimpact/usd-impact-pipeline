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
| Merge | `usd_impact_score_v2.py`, `fetch_all_data()` | FRED and Yahoo frames joined into one daily matrix | Derived/in-memory mixing; characterize subsequent writes |
| Local exports | `usd_impact_score_v2.py:export_csv()`, `export_json()`, `_daily_cache.parquet` and output directories | Code contains disk-writing paths | Potential exposure; actual execution/retention not verified |
| Committed weekly input | `data/weekly_input_2026-10-23.json` | DGS2/DGS10 source and observation metadata under weekly driver entries | Confirmed committed persistence; weekly schema contains per-driver derived z-scores/contributions; source-specific rights unresolved |
| Public latest input | `public/data/weekly_input_latest.json` | Public driver entries with FRED source metadata | Confirmed public path; file contains UST_2Y/UST_10Y per-driver z-scores and contributions as well as source metadata; terms treatment unresolved |
| Historical public input | `public/archive/2026-10-23/weekly_input.json` and other dated archives | DGS2/DGS10 are present in dated public archive files | Confirmed archived persistence; enumerate full set |
| Public component histories | `public/data/usd_impact_score_v2.csv`, `public/data/usd_impact_score_v2.json`, `public/data/score_repro_bundle_latest.json` | Existing containment plan describes multiweek component values and weekly provider-derived values | Repo-document evidence; inspect exact current file schemas and deployment before remediation |
| Independent validation | `scripts/validate_weekly_release.py`, `public/data/score_v2_methodology.json` | DGS2/DGS10 embedded in source/provenance and release contracts | Metadata alone is not evidence of stored observations |

## Scope not yet verified

- All actual GitHub Actions commands and upload paths, Pages/CDN/Cloudflare/Vercel deployment surfaces, object storage, job logs, backup retention, CI caches, local runner files, private evidence handoffs, old commit history, and third-party mirrors.
- Whether hashes, normalization moments, mixed-source aggregates, and independently computed non-reversible aggregate history qualify as FRED Content or prohibited derived works. **Do not assume either permission or prohibition; obtain written interpretation.**
- Whether the same H.15 observations can be sourced directly from the Federal Reserve Board, whether its license/terms permit the required retention/commercial use, and whether source and calendar parity can be demonstrated without changing Score methodology.
- Whether the current job remains scheduled or guarded; source-file presence does not prove that a release currently runs.


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
- [ ] Completed all runtime/CI/backup persistence inventory.
- [ ] Confirmed retained value classes and rights interpretation.
- [ ] Evaluated direct H.15 terms and exact-source parity feasibility.
- [ ] Introduced synthetic-only tests and independently reviewed a fail-closed rights contract.
- [ ] Obtained explicit legal/provider and release approvals.

This is a **review artifact only**. Issue #155 HOLD remains active. No existing data, workflows, public artifacts, method, credentials, entitlements, or production config are changed by this document.
