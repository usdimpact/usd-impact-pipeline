# Separate no-budget Macro Context Panel — synthetic-only fallback (2026-10-30)

**Status: DRAFT / UNAPPROVED INTERNAL NAME / RIGHTS HOLD / SYNTHETIC ONLY.**

This is implementation research for an alternative educational product after S&P Dow Jones Indices confirmed that USD Impact's original S&P 500-inclusive Score use case requires a paid license, and the owner confirmed a **USD 0** market-data licensing budget. It is **not** a resumption, modification or rebranding of the eight-driver Score v2. It is not an investment recommendation.

Controlling decisions: [Legacy public Score Issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155) (HOLD), [FRED/underlying Treasury Issue #282](https://github.com/usdimpact/usd-impact-pipeline/issues/282) (HOLD). Parent work:
- [Phase B source timing design](../governance/score-public-source-phase-b-design-2026-10-29.json);
- [Four exact-series / 14-rights decision matrix](../governance/score-four-source-exact-series-rights-matrix-2026-10-29.json);
- [Separate new-model rights draft](../governance/independent-macro-context-fallback-draft-2026-10-30.json).

"Public-Source Macro Context Panel" is an **internal working title**, not approved branding or proof that these series may be commercially redistributed.

## 1. Proposed economic output — three independent dials, no composite Score

| Dial | Source identities | Purely descriptive synthetic 2099 computation | Interpretation and important non-equivalence |
| --- | --- | --- | --- |
| Dollar breadth | Board H.10 daily nominal Broad Dollar Index, H10/H10/JRXWTFB_N.B | Compare selected Friday index level to previous Friday; UP / DOWN / UNCHANGED | Trade-weighted broad dollar. **Not** ICE USDX/DXY and does not reproduce the original Score's DXY factor |
| Reported crude inventories | EIA WPSR U.S. crude oil stocks excluding SPR, publisher code WCESTUS1 | Compare current Friday stocks against prior Friday; BUILD / DRAW / UNCHANGED | Stock change. **Not** WTI price, CME futures or reliable proof of crude-price direction |
| Nominal yield curve | Direct U.S. Treasury 2Y and 10Y nominal par CMT yields, same immutable curve revision | Compare 10Y minus 2Y; POSITIVE / INVERTED / FLAT. Compare current vs prior week's slope; STEEPENING / FLATTENING / UNCHANGED | Nominal curve shape, not a real rate or policy recommendation |

A three-dial panel returns **four qualitative labels** because the Treasury curve has level and direction. It does not normalize, average, weight, predict, backtest, or publish a combined USD Impact Score number.

**No historical bridge:** Existing Score v2's 617-week history is not the history of these signals. No conversion, reweighting, splicing, rescaling, backfill, reuse of derived values, or claim of old-method continuity is permitted. Existing Score artifacts remain preserved under separate legal review.

## 2. Why zero subscription is not automatic commercial rights clearance

The draft is budget-aware but **not yet rights-cleared**, even though these government sites are accessible without commercial feed subscriptions.

- **Federal Reserve H.10:** [Board public-domain disclaimer](https://www.federalreserve.gov/disclaimer.htm) generally permits Board-authored material with credit, but expressly excepts protected third-party content. The Board's [2019 dollar-index revision paper](https://www.federalreserve.gov/econres/notes/feds-notes/revisions-to-the-federal-reserve-dollar-indexes-20190115.html) and [technical Q&A](https://www.federalreserve.gov/releases/h10/h10_technical_qa.htm) document the 2019-02-04 change from goods-only to goods-and-services methodology under a reused mnemonic, plus a 2019-06-24 daily base change. Current backcasts cannot establish historical first-publication vintages. The [2026 DDP transition](https://www.federalreserve.gov/data/data-download-fred-information.htm) removes "Build Your Package" during the week of November 9, 2026, with historical release-page XML retained. Never silently substitute FRED.
- **EIA WPSR:** [EIA Copyrights and Reuse](https://www.eia.gov/about/copyrights_reuse.php) covers government-produced material subject to private/third-party exceptions. This candidate is reported weekly crude **stocks**, not a Refinitiv WTI/Brent spot series. [EIA's release schedule](https://www.eia.gov/petroleum/supply/weekly/schedule.php) usually lists Wednesday 10:30 ET with holiday exceptions. Verify survey source, lease-stock scope, first release and corrections before any real use.
- **Direct Treasury:** [Treasury curve/feed documentation](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed) and [Data.gov CC0 catalog metadata](https://catalog.data.gov/dataset/interest-rate-statistics-daily-treasury-yield-curve-rates) are **evidence to assess**, not an authorization covering every upstream source or activity. The nominal Treasury curve uses indicative market quotations with FRBNY origin. Exact 2Y/10Y direct XML field mapping, source/transport permissions, revision history and retention remain unverified. No implicit FRED API fallback.

The proposal lists **14 denied rights dimensions for each of 4 exact candidates: 56/56 FALSE**, plus **14 independent external decision gates FALSE**. Neither government domain names nor synthetic tests grant commercial rights or permission to retrieve original numerical observations.

## 3. Release timing and revision safeguards

A reference week's official government series do not become observable simultaneously by Friday:

1. H.10 usually covers the previous week and releases the following Monday around 16:15 ET; holiday/revision exceptions apply.
2. EIA usually releases last Friday's stock number the following Wednesday around 10:30 ET; holiday exceptions apply.
3. Treasury daily yields may publish Friday later than a same-Friday Score cutoff, usually around 18:00 ET or later.
4. All 4 inputs for **each of two consecutive reference Fridays** need authentic first-publication, revision-publication and first-seen receipts no later than evaluation time. A calendar or expected publishing clock does **not** prove a release was seen.
5. Treasury 2Y/10Y must share one snapshot and revision, for each week.
6. Missing, revised-late, stale, mismatched or unverified sources => return HOLD **without labels**. A later correction can affect only later as-of evaluations.

Only invented 2099+ weekly dates/values are accepted by the prototype. No real historical vintages are fetched, copied, or inferred.

## 4. Deliverable and tests

- Synthetic engine: scripts/independent_macro_context_synthetic.py imports only the existing Phase B synthetic receipt checker. No market provider SDK, HTTP, filesystem, storage, Score v2 engine, HTML or JSON publisher.
- Rights matrix: governance/independent-macro-context-fallback-draft-2026-10-30.json records the independent model and 56 denied permissions.
- Tests: tests/test_independent_macro_context_synthetic.py checks invented source values/directions, wrong version, delayed release, no-lookahead, Treasury pairing, real-date rejection, no data leakage, rights flags and direct-result constructor bypass attempts.
- **Synthetic preview result contract (offline only):** Even when `SyntheticContextPanel` is instantiated directly instead of being returned by the evaluator, it must carry exactly two consecutive canonical ISO Fridays **2099+**; a COMPLETE preview contains exactly four ordered, enumerated dial labels and **no** blockers; a HOLD preview contains **no** labels and a bounded, deduplicated list of known, week-scoped failure codes. Publication and access flags must all be the literal Boolean `False` (not `None`, `0`, or other falsy aliases). This rejects forged historical dates, extra trading directives, hidden duplicate labels, unscoped blocker text and logically contradictory states.
- **Trust boundary:** A correctly constructed synthetic preview is still **not** proof that underlying receipts were evaluated or that any source is licensed. The constructor only validates representation and invariant consistency; authorization, provenance, economic approval, real-data retention and Production remain separate explicit HOLD gates. Python in-process objects are not a security or signature boundary.
- The prototype does **not** change: Source v2 inputs or formula; Cloudflare Pages/public artifact files; production jobs; provider/merchant subscriptions; Supabase/private real-data retention; member/dashboard/research readers; correspondence or historical Git archives.

Offline invented-data tests have no market-data license fee. This does not prove a future real-data product has zero legal, administrative or infrastructure costs.

## 5. Separate decisions before any real-source implementation

**Stage C (this PR):** independently specified qualitative methodology and synthetic as-of proof of concept. Not live.

**Stage D (needs distinct owner/source review):** confirm exact H.10/EIA/Treasury origin and reused-mnemonic rights, direct feed version continuity, protected third-party exceptions, historical first-publication receipts, permitted retention/disposal, owner economic methodology/naming, EIA definitions and direct Treasury XML fields. Avoid actual observation requests until explicit authorization.

**Stage E (requires completed rights and owner approval):** propose separate live adapters/retention, security and audit design, separately authorized source access, independent public artifact schema, non-Production previews, educational/compliance review, exact-head validation, and a distinct Production release. Do NOT use the old Score v1 allow state.

**Current state: no provider market-data retrieval, no live backtest, no real historical retention, no publishing, no deployment, no commerce.**
