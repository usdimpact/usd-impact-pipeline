# Phase B — Federal public-source macro study: rights, timing, vintage and synthetic as-of design

**Prepared:** 2026-10-29. **State:** `SYNTHETIC_DESIGN_REVIEW_ONLY_HOLD`. **No real provider observations fetched, stored, checked or compared.** No source switch, formula/weights/name/branding approval, outreach, new provider account, paid license, or Production/Cloudflare/Supabase change.

**Governing issues:** [Score rights #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155), [FRED/source retention #282](https://github.com/usdimpact/usd-impact-pipeline/issues/282). Parent: [eight-driver Phase A](score-zero-additional-license-phase-a-feasibility-2026-10-29.md). [Phase B machine-readable rights manifest](../governance/score-public-source-phase-b-design-2026-10-29.json).

## Decision

**Conditional proceed for synthetic-only engineering research. NO-GO for a new/live public indicator.** These four federal signals could support a *distinct* macro project, but do not replace the eight-driver USD Impact Score, and no source-specific real-data/retention/public-license decision or new method has been approved.

Four candidate signals: Federal Reserve **Broad Nominal Dollar Index** (not ICE DXY), EIA **U.S. commercial crude oil stocks excluding SPR** (not WTI futures or privately sourced WTI spot), Treasury **2-year nominal par yield**, and Treasury **10-year nominal par yield from the exact same curve snapshot**. No signs, weights, bands, model name, backtest, reporting schedule or rights grants are approved. Do not splice them into the legacy 617-week Score history.

## Rights crosswalk — official publisher evidence

| Proposed signal | Publisher source and stated rights | Outstanding conditions | Gate |
|---|---|---|---|
| **Fed H.10 Broad Dollar** | [Board disclaimer](https://www.federalreserve.gov/disclaimer.htm): Board-authored website information generally public domain absent a contrary indication, with attribution; third-party material is excepted. [H.10](https://www.federalreserve.gov/releases/h10/) provides Broad Index timing/methodology. | Verify this exact series has no private rights caveat, permissible commercial use, retention, public derived aggregates, source attribution and stable native transport. The [DDP Build Your Package retirement notice](https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H10) targets the **week of Nov 9, 2026**. Do not reroute to FRED automatically. | **Conditional government-source research; no ingestion approval** |
| **EIA surveyed crude inventories** | [EIA Copyrights and Reuse](https://www.eia.gov/about/copyrights_reuse.php) generally permits government-produced data reuse with acknowledgement/publication date, explicitly excepting private licensed material. [WPSR](https://www.eia.gov/petroleum/supply/weekly/) includes surveyed stock aggregates. | Confirm exact source ID, definition, units, corrections, license exceptions, official direct download rights, storage/backups, commercial derived outputs and citation. EIA [documents Refinitiv-sourced historical WTI/Brent spot](https://www.eia.gov/analysis/handbook/pdf/STEO_Crude_Oil_Price.pdf): that material is **not** automatically licensed downstream. | **Conditional government-survey research, not WTI futures** |
| **Treasury nominal 2Y** | [Treasury methodology](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology) describes an official par yield computed using indicative market bid quotations and usually published by 18:00 ET, potentially late. [XML feed](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed) documents year/month requests. | Upstream quote rights, source transport, commercial retention, aggregate/public derivative, correction timing, complete period and FRED/H.15 as-of parity all require separate assessment. | **Rights/vintage pending; synthetic-only** |
| **Treasury nominal 10Y** | Same published Treasury curve and methodology. [Treasury FAQ](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/interest-rates-frequently-asked-questions) explains constant-maturity par points. | Same rights; require **identical immutable curve vintage** for 2Y and 10Y. No blending 2Y corrections with older 10Y values. | **Rights/vintage pending; synthetic-only** |

**Counsel/source-owner questions (not sent):** For the exact native series and direct publisher transport, what commercial non-display/internal use, temporary calculation, historical retention/version receipts, immutable backup/log limits, source citations, commercial public aggregates, machine-readable history and prior archive treatment are permitted? Are any upstream exchange or market quotation rights embedded? Source owner and distributor may impose separate conditions. A government site's general public-domain statement is not a guarantee for every item on that site.

## Publication-as-of: receipts, never schedule assumptions

**An observation date is not a publication receipt.** Future rights-approved research would need an authenticated publisher release time, the specific **version's** publication time, independently recorded first-seen time, exact series and immutable snapshot/version ID, source rights, timezone and retention scope. The following clock is **an invented example using no values**:

| Fictional reference week: Friday June 5, 2099 | Illustrative usual publisher release (America/New_York) | Effect |
|---|---|---|
| Treasury curve 2Y+10Y | Friday June 5, ~18:00 ET (may be later) | 18:00 **EDT is 22:00 UTC**: the legacy Friday ~22:00 UTC cutoff may be too early even for Treasury |
| Fed Board H.10 | Monday June 8, 16:15 ET for previous business week, later if holiday | Friday calculation cannot use the previous week's final H.10 publication |
| EIA WPSR | Wednesday June 10, 10:30 ET for prior Friday, later if holiday | Friday or Tuesday calculation cannot yet use official inventory data |
| Possible subsequent evaluation | After actual receipts for all four, potentially Thursday | **Not a release approval or guaranteed date**; each actual timestamp must pass |

Board [H.10 explicitly moves Monday holidays](https://www.federalreserve.gov/releases/h10/); EIA [publishes special holiday dates/times](https://www.eia.gov/petroleum/supply/weekly/schedule.php); Treasury [may publish after 18:00 ET](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology). Convert to UTC with `America/New_York` and daylight-saving rules: **18:00 ET corresponds to 22:00 UTC in summer, 23:00 UTC in winter**.

**Revision is not a hypothetical threat:** the Board [announced August 12, 2026](https://www.federalreserve.gov/feeds/h10.html) that errors in its August 10 H.10 release (in August 3 observations) were corrected on August 12. A retrospective download cannot automatically prove which original vintage was visible on August 10. Synthetic tests model a made-up June 2099 correction, never Board numerical values.

A future as-of version may be evaluated only when:
- `initial_release_at <= version_published_at <= first_seen_at <= as_of_at`, all timezone-aware and independently evidenced;
- the intended Friday reference period and exact source match;
- the latest **available as of cutoff** revision is chosen (later corrections cannot backfill earlier knowledge);
- Treasury 2Y and 10Y share the exact curve snapshot ID and revision;
- absent, contradictory, unauthorized, naive or stale receipts are **HOLD**.

**No calendar-only release guess** may stand in for actual source release and first-seen evidence. A future storage mechanism for real version receipts also needs explicit rights and preservation approval.

## Synthetic-only technical acceptance

- [Pure standard-library validator](../scripts/score_public_source_phase_b_synthetic.py) accepts only **2099+ Friday-week metadata records** with `SYNTHETIC_DO_NOT_PUBLISH` and `SYNTHETIC:` ID prefixes. No market values, HTTP calls, provider scripts, open-file operations, credentials or persistence.
- [Synthetic tests](../tests/test_score_public_source_phase_b_synthetic.py) cover Friday/Monday/Wednesday lookahead, synthetic holiday shifts, delayed first-seen, correction vintages, Treasury same-curve integrity, DST, wrong source/week/markers, duplicate/reordered revision IDs, missing/noncausal timestamps and rights guards.
- A successful fictional eligibility check returns `SYNTHETIC_ONLY_COMPLETE` plus **snapshot identifiers only**. It expressly returns `publish_authorized=false` and `real_source_retrieval_authorized=false`. Four synthetically available receipts do not prove a complete real dataset, legal entitlement, historical parity, model validity or public release permission.

## Phase B go/no-go and independent approvals

**GO now only for:** documentation review, source/owner rights questions, official calendar and methodology notes, invented fixtures, pure offline tests, as-of/revision schema design and protected technical CI.

**NO-GO until new explicit approval for:**
1. Any direct H.10/EIA/Treasury real observations, whether manually downloaded or fetched by API. Also prohibit FRED as an unauthorized alternative transport.
2. Commercial retained source/version receipts, historical snapshots or public derived data without series- and transport-specific legal disposition.
3. A four-signal model's economic thesis, signs, normalizations, weights, release lag, band thresholds, product name, old Score comparison or new historical chart.
4. Retrospective backtests without lawful, **actual contemporaneous first-seen vintages**, correction history, holiday treatment and non-look-ahead controls.
5. Public-site or membership source/consumer changes, preservation of already public Class C/E/F artifacts, Git/Pages/cache purge, rollback or Production deployment.

**Next decision:** Once source-rights counsel and owner decide the precise permitted series/use and whether a **different** four-signal product is wanted, request separate authorization for a narrow real-data parity/transport proof in a lawful environment. Do not infer permission from synthetic green CI.

**Operational status unchanged:** Original USD Impact Score v2 rights `hold` with null approval receipt; Development synthetic-only private evidence authorized; real source evidence, public replacement and Production remain unauthorized. No email sent, licensing agreement purchased, live observation copied or Production environment altered by this Phase B package.
