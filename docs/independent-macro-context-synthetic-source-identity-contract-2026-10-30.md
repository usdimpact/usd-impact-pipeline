# Independent Macro Context Panel — source-unit/definition interlock (2026-10-30)

**Status:** Synthetic-only engineering review. NOT real-data access, a publisher assertion, an approved model specification, a public release, or a rights decision. This is a companion to [Issue #313](https://github.com/usdimpact/usd-impact-pipeline/issues/313), merged [PR #312](https://github.com/usdimpact/usd-impact-pipeline/pull/312) and the owner/counsel question queue from [PR #314](https://github.com/usdimpact/usd-impact-pipeline/pull/314). Existing [Score Issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155) remains legally and operationally separate.

## Gap found

The existing 2099-only synthetic evaluator matched source ID, snapshot, reference week and version-first-seen receipt. Its invented scalar did not explicitly carry a measurement unit or an economic definition tag. An incorrectly prepared test input could therefore use different units or definitions for successive weeks, or could mix the Treasury nominal-par and real-yield curve families, while still producing a plausible descriptive direction. This is particularly relevant where source metadata has known methodological and historical definition breaks.

## Purely local correction

The dormant synthetic observation dataclass now requires two additional fields for every invented source/period/snapshot:

- **unit:** must match the fixed candidate's local expected unit — Board nominal Broad Dollar index (`index`), EIA ending crude stocks excluding SPR (`thousand_barrels`), Treasury 2Y and 10Y nominal par yields (`yield_percent`). This is a contract for invented test data, not a verified statement that the live runtime delivers the candidate in that exact encoding.
- **basis_id:** a local string beginning `CANDIDATE:` that locks the proposed source-definition family. The H.10 tag explicitly denotes post-2019 goods-and-services Broad Dollar after the June 2019 rebasing; EIA denotes the unreconciled WCESTUS1 excluding-SPR series rather than the separate lease-stock-inclusive category; Treasury marks direct *nominal* par-curve candidate fields illustrated by the Treasury publisher, not real/TIPS yields.

These expected values are frozen in the synthetic module's `SOURCE_UNITS` and `SOURCE_BASIS_IDS` dictionaries and copied into the existing strictly inactive [new-model governance draft](../governance/independent-macro-context-fallback-draft-2026-10-30.json). An observation whose unit or basis differs fails closed with an explicit error **before** any synthetic direction is calculated. No automatic conversion, imputation, source switching or historical stitching is permitted.

**Important limitation:** A matching candidate tag can be typed by anyone and is **not** a signature, an authenticated provider assertion, an actual first-publication receipt, historical-vintage equivalence, a copyright waiver or a legal license. Real source provenance, H.10 pre/post-2019 comparability, EIA historical lease-stock definitions, Treasury field continuity and commercial reuse must be independently reviewed at the later rights-controlled Stage D/E boundary. The synthetic first-seen checker still requires separate invented actual timestamps.

## Primary-source evidence context

- [Board H.10 technical Q&A](https://www.federalreserve.gov/releases/h10/h10_technical_qa.htm) documents the goods-only to goods-and-services redesign effective February 4, 2019 and daily Broad Dollar index rebasing effective June 24, 2019; a reused mnemonic or current revised backcast cannot prove original historical publication.
- [EIA current metadata and category inventory](score-treasury-eia-publisher-metadata-review-2026-10-30.md) distinguishes WCESTUS1 ending stocks excluding SPR, the table explicitly excluding lease stock, and a different historical category including lease stock. Their full as-published numerical equivalence has **not** been established.
- [U.S. Treasury official XML documentation](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed) distinguishes the *nominal par* from *real par* yield-curve product. Its example documents BC_2YEAR and BC_10YEAR fields, but not future live field availability or original market-input licensing.

No real provider numeric observation was requested, copied, printed, transformed or included in this patch. Only already-documented rights/metadata pages were consulted.

## Synthetic acceptance and non-release controls

Only these four existing/new files change in the review PR:

1. `scripts/independent_macro_context_synthetic.py`: adds mandatory invented unit and basis fields and rejects mismatches.
2. `tests/test_independent_macro_context_synthetic.py`: adds positive and negative synthetic fixture checks; refuses million-versus-thousand barrel conversion drift, basis substitution (H.10 old goods-only, EIA lease-stock, Treasury real yields), missing/invalid metadata, and source-tag disclosure.
3. `governance/independent-macro-context-fallback-draft-2026-10-30.json`: records the exact local unit/basis candidate mapping as **non-authoritative**; all rights and owner/Production flags remain FALSE.
4. This document.

All 2099 numeric values remain invented. The output stays qualitative (no source numeric values, unit strings, or basis identifiers). Full protected quality, CodeQL and frozen-research validation is required before any merge; `[CF-Pages-Skip]` prevents an unnecessary Pages deployment. This does not enable live source adapters, research storage, website/member UI, historical archive modification, licensing expenditure or Production.

**Status after a technically successful review remains: 56/56 candidate source rights denied; 14 external authorities denied; source data, historical as-of, legal permissions, and public publication all HOLD.**


## Follow-up: impossible pre-period synthetic release interlock (Oct 30, 2026)

**Finding.** The earlier pure invented-receipt evaluator correctly enforced version `initial_release <= version_published <= first_seen` and the as-of cutoff. An internally consistent *invented* receipt could nonetheless label a full Friday-ending H.10/EIA source period as already published **before that Friday had ended**, or represent Friday Treasury data as published **on Thursday**. Those impossible period claims could influence a fully fabricated `SYNTHETIC_ONLY_COMPLETE` candidate result. They are not genuine publisher timing receipts.

**Conservative local constraint.** The dormant panel evaluator now fails before selecting any synthetic source observation if an invented **initial** release violates these minimal *reference-period chronology* floors (interpreted in `America/New_York`, compared as UTC instants):

| Candidate source family | Synthetic-only earliest possible period floor | Why this is only a floor |
| --- | --- | --- |
| H.10 weekly Friday reference and EIA weekly ending inventories | **Saturday 00:00 ET after** the reference Friday | A completed Friday-ending reference period cannot be known before it ends. H.10/EIA actual release is normally later; this does **not** infer Monday/Wednesday delivery or rights |
| Treasury nominal 2Y and 10Y daily Friday observations | **Friday 00:00 ET on** the reference date | No Friday observation can be reported as already published on Thursday. Actual Treasury publication is normally later, and both maturities still require one verified coherent curve snapshot |

The guard is checked independently for **both** consecutive invented 2099+ Fridays. It uses only standard-library timezone handling and never moves/changes actual timestamps. It **does not** assume a release is available on Saturday or at Friday midnight: the existing first-seen, coherent Treasury-pair, version visibility, and no-lookahead checks remain mandatory. The all-false rights/Production fields are untouched.

Two new adversarial test methods (multiple subcases) cover all four source IDs on both weeks, fabricated causally ordered but pre-period published receipts, admissible candidate floor-boundary examples, and equivalent UTC timestamps for the Treasury pair. All numerical fixtures remain deliberately invented in year 2099, not observations.

**External scheduling caution.** The Board's [2026-07-16 DDP announcement](https://www.federalreserve.gov/data/data-download-fred-information.htm) confirms its custom “Build Your Package” facility is scheduled for retirement during the **week of November 9, 2026**. Direct Board XML continuity, exact source identity, copyrights, actual publisher-first-release times and retention permissions remain unresolved. The candidate lower-bound validator is **not** a replacement for any of those decisions, and FRED is **not** authorized as an automatic alternative.

**Scope:** This isolated follow-up modifies only `scripts/independent_macro_context_synthetic.py`, `tests/test_independent_macro_context_synthetic.py`, and this existing explanatory record. It does not change the original frozen eight-driver Score or its histories, active site, synthetic rights matrix, workflows, external requests, evidence storage, private emails, or public outputs. Issue #313 remains source/methodology/legal **HOLD**, separate from Score #155 and FRED retention #282. A protected exact-head CI review and non-deploy merge convention are mandatory.
