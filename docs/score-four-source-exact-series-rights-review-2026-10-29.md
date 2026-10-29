# Four-signal study — exact-series source and rights matrix (2026-10-29)

**State:** `PUBLISHER_METADATA_RESEARCH_ONLY_HOLD`. This is a **source-identification and rights-decision template**, not a permit, not a model approval, and not authority to retrieve real observations. The [machine-readable matrix](../governance/score-four-source-exact-series-rights-matrix-2026-10-29.json) defaults **all 14 permission dimensions to false for each of four sources**. It supplements the [Phase B design](score-four-source-phase-b-rights-asof-design-2026-10-29.md) and [October 29 Deep Research correction](score-phase-b-deep-research-corrections-2026-10-29.md).

**Governing issues:** [#155 — legacy Score public-derived rights HOLD](https://github.com/usdimpact/usd-impact-pipeline/issues/155), [#282 — FRED/Treasury provenance and retention audit](https://github.com/usdimpact/usd-impact-pipeline/issues/282).

## Publisher-native identities and direct transports

| Phase B candidate | Exact publisher metadata identified | Direct-publisher transport evidence | Still unverified |
|---|---|---|---|
| Fed H.10 **nominal** Broad Dollar Index (not ICE DXY) | Board series **`H10/H10/JRXWTFB_N.B`**, [publisher series metadata](https://www.federalreserve.gov/datadownload/Preview.aspx?pi=400&preview=H10%2FH10%2FJRXWTFB_N.B&rel=H10) and [native series description](https://www.federalreserve.gov/releases/h10/summary/jrxwtfb_nb.htm). | [Board H.10 release page](https://www.federalreserve.gov/releases/h10/) plus [July 16 DDP transition notice](https://www.federalreserve.gov/data/data-download-fred-information.htm): historical release-page XML remains downloadable, while Build Your Package ends the week of **Nov 9, 2026**. | Native H.10 exact-series rights, all non-Board exceptions, post-transition direct automated acquisition, actual version availability receipts, base/unit consistency. **FRED is not authorized as a fallback.** |
| EIA WPSR **weekly crude stocks, excluding SPR** (not WTI price) | [EIA publisher's weekly series `WCESTUS1`](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?f=W&n=PET&s=WCESTUS1) is labeled “Weekly U.S. Ending Stocks excluding SPR of Crude Oil,” in thousand barrels. See also [commercial (excluding lease stock) weekly table](https://www.eia.gov/dnav/pet/PET_STOC_WSTK_A_EPC0_SAX_MBBL_W.htm). | EIA publishes series-history and [weekly report schedule](https://www.eia.gov/petroleum/supply/weekly/schedule.php); normal release is **Wednesday 10:30 a.m. ET**, with published holiday exceptions. | Confirm exact lease-stock/SPR definitions across histories, original survey versus protected contributor inputs, official machine-readable route/terms, revisions and retention; not EIA's separately sourced WTI/Brent spot prices. |
| Treasury **2Y nominal par CMT** | Direct Treasury [nominal daily yield curve](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve), **2 Yr** maturity. Candidate XML tag `BC_2YEAR` comes from existing internal design; exact feed field remains **unverified**. | [Treasury XML feed specification](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed): `daily_treasury_yield_curve` with year/month selectors. | Exact XML field/units, rights for commercial processing and derived history, FRBNY input rights, as-published vintage parity, first-seen source receipts. |
| Treasury **10Y nominal par CMT** | Same direct publisher [nominal daily yield curve](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve), **10 Yr** maturity. Candidate XML tag `BC_10YEAR` is **unverified**. | Same Treasury XML transport; both 2Y/10Y must use **one immutable curve snapshot/vintage**. | Same rights and archival questions, actual same-vintage/field pairing and as-of availability, no assumed FRED DGS10 timing or parity. |

The [Board's 2019 technical Q&A](https://www.federalreserve.gov/releases/h10/h10_technical_qa.htm) documents a change to the **daily** Broad dollar index base, to January 2006 **monthly mean** = 100. A Board DDP metadata page presents an apparently different unit label, while the H.10 release also shows January 2006=100. The precise historical base/unit semantics and the metadata inconsistency **must be reconciled** before ingesting values, rebasing them, or building a historical chart. Documented publisher series identity does not prove the entire methodology.

The [EIA cross-category stock table](https://www.eia.gov/dnav/pet/pet_stoc_wstk_dcu_nus_w.htm) separates commercial crude from SPR, and [EIA's explanation](https://www.eia.gov/TodayinEnergy/detail.php?id=67868) states that commercial crude inventories exclude the reserve. The weekly series is still **not a crude price**; shifting from WTI futures or spot to stocks would create a new economic signal.

## Licensing evidence versus explicit decisions

| Owner/publisher evidence | Supports | **Does not automatically decide** |
|---|---|---|
| [Board disclaimer](https://www.federalreserve.gov/disclaimer.htm) | Board-authored website information generally public-domain when not otherwise indicated; attribution and restrictions on non-Board contributions | H.10 exact index methodology/rights, redistributing derived component histories or storing vintages, post-DDP commercial transport |
| [EIA copyrights and reuse](https://www.eia.gov/about/copyrights_reuse.php) | Government-produced EIA information generally reusable with **source plus publication date** and protected-third-party exceptions | Whether every `WCESTUS1` source field and API path is covered, archives, derived public aggregates, historical corrections, Refinitiv-sourced WTI |
| [Data.gov nominal Treasury catalog](https://catalog.data.gov/dataset/interest-rate-statistics-daily-treasury-yield-curve-rates) | Dataset ID `015-DO-020` lists **CC0 1.0**, last modified Feb 11, 2025 | Exact-delivery/transport terms, upstream indicative market bids, historical store/backup/log rights, public-derived outputs, separate counsel/project approval |
| [Treasury method](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology) and [FAQ](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/interest-rates-frequently-asked-questions) | Treasury produces the par curve from indicative quotes provided through FRBNY; Fed Board's **H.15 republishes** CMT yields | Value equality, historical revisions, timestamp parity, rights over FRED-delivered observations |
| [FRED legal terms](https://fred.stlouisfed.org/legal/terms/) | FRED operates as **St. Louis Fed** distributor with separate content-use and storage restrictions | Permission to substitute FRED for Treasury/Board native transports or retain FRED-sourced content in archives |

**The 14 blocked rights dimensions are independent:** commercial internal ingestion; commercial non-display computation; transient processing; provider content retention; raw observation archival; logs/caches; backups/disaster recovery; revision-vintage receipts; public aggregate distribution; public component distribution; public historical distribution; AI/ML processing; downstream redistribution; and live-source retrieval. An evidence page or catalog CC0 field cannot set any of these `true`.

## Availability and revision constraints

- **H.10:** prior business week's daily information normally released **Monday 16:15 America/New_York**, the next business day after holiday. Aug 10, 2026 H.10 contained Aug 3 errors corrected on **Aug 12**. A current downloaded history cannot prove the Aug 10 vintage.
- **EIA WPSR:** week-ending Friday inventory normally released **following Wednesday 10:30 ET**, but [holidays can move release into Thursday or another date/time](https://www.eia.gov/petroleum/supply/weekly/schedule.php). Corrections and first-seen histories require affirmative proof, not calendar inference.
- **Treasury:** daily nominal curve [normally available **by 18:00 ET**, sometimes later](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology). In summer 18:00 Eastern is **22:00 UTC**, in winter **23:00 UTC**. A Friday 22:00 UTC cutoff cannot assume the newest Friday curve is published.
- The **2Y and 10Y** values must be taken from one version of the same Treasury curve; never splice revised 2Y with pre-revision 10Y. An as-of test requires contemporaneous `initial_release_at`, `version_published_at`, `first_seen_at` and source snapshot ID, all bounded by the cutoff. Synthetic tests already cover this shape; no repeat Supabase evidence writes are needed.

## Required owner/legal decisions, before any new work on actual data

For **each individual series and chosen publisher transport**, obtain documented reviewer/owner decisions on: (1) exact definition and upstream contributors; (2) whether commercial internal acquisition and non-display computation are allowed; (3) whether original observations, intermediate values, first-seen/vintage receipts, logs, caches and backups may be kept, and for how long; (4) whether public aggregate or historical derived outputs may be distributed; (5) citation, re-licensing, AI/ML and onward distribution restrictions; (6) whether native direct transport remains available and permitted. Each decision must explicitly name the series and transport, output scope, effective date and provenance. Merely reviewing a policy is not a signed decision.

**Separate product gates:** The existing **eight-driver USD Impact Score** remains subject to rights HOLD for its ICE/S&P/Cboe/CME/Yahoo/FRED pathways. A potential **different four-signal federal macro study** is not a drop-in substitute; legacy data, weights, Score name, frequency and 617-week history do not transfer. Under no circumstances mark legacy Score rights cleared because a federal-source catalog is permissive.

## Acceptance and next step

1. Maintain `sources[].permissions[*] == false` and null counsel/owner receipts until separate, actual scoped approvals exist. Deny real source retrieval, data retention, external uploads, historical replay, backtests, public output or Production.
2. Verify the new matrix keys and negative rights conditions in a network-free test. Keep the existing Phase B synthetic validator unchanged.
3. Review this as an **independent documentation/test PR** with protected exact-head CI. Do **not** merge a data-source adapter or publish any feed based on it.
4. Later, if approved, request separate permission for a **minimal rights-safe source-transport/first-seen proof** that does not silently invoke FRED or ingest/retain live market observations. This document does not grant such permission.

**Execution boundaries:** No real source data downloads, SQL or Supabase writes, Vercel/Cloudflare/Render/Resend/Lovable mutations, public Score artifact changes, model naming/weights approval, paid license, provider outreach, or Production release.

## October 30, 2026 addendum — H.10 mnemonic lineage and adverse Deep Research claims

**Review type: original-publisher metadata and official terms only.** This supplements the October 29 rights packet without introducing any market observation, dataset download, source adapter, rights grant, model/weight approval, Score history rewrite or Production change.

### Two distinct H.10 revisions affect historical source identity

The Board's [H.10 technical questions](https://www.federalreserve.gov/releases/h10/h10_technical_qa.htm) distinguish **methodology changes** from **index-base changes**:

| Effective date | Board-published change | Implication for an as-of historical study |
| --- | --- | --- |
| **February 4, 2019** | The DDP mnemonic `JRXWTFB_N` was reassigned from the **old goods-trade-only Broad Dollar Index** to a **new broad index whose weights use goods and services trade**. Its old goods-only methodology was also made available under `V0.JRXWTFB_N`, maintained until December 31, 2019. | An unchanged mnemonic is **not** proof of unchanged economic methodology. A reconstructed historic row or backcast cannot be treated as something published in the same form in a prior year. |
| **June 24, 2019** | Board staff changed daily Broad Index indexation from **January 2, 2006 = 100** to **January 2006 monthly average = 100**. | Current reindexed history does not establish the precise historical as-published vintage, and comparing pre/post releases requires controlled base/version lineage. |

The Board states that estimates of the revised methodology extend back to January 2006; a retrospective estimate is **not** proof that those numbers or definitions were published contemporaneously. Historical series keys, methods and first-publication versions must be kept separate. The source is the Board's dated 2019 Q&A (page last updated February 6, 2023), not a market observation.

**Unresolved:** reconcile the unit/base discrepancy between the Board's H.10 release and DDP preview metadata, actual as-published release vintages and the old goods-only alias, and the mechanics of a permitted immutable source snapshot. Do not fetch actual observations to resolve any of this without a separate authorization. The same-week Friday publication problem remains: Board H.10 typically releases previous-week daily information the following Monday.

### Research intake corrections — rights evidence is not permission

The latest Deep Research assessment should **not** become a configuration or publication authority. In particular:

- Reject `approved: true` for all four sources or the 14 permission fields under each source. CC0 in the Treasury Data.gov **catalog** and the Board/EIA general public-domain statements may be positive evidence; neither proves every series/transport/upstream right, commercial storage or public derivative permission.
- Reject the claim that **FRED** has no separate commercial/archival/AI restrictions. The [St. Louis Fed's FRED Services Terms](https://fred.stlouisfed.org/legal/terms/) contain distinct Services prohibitions: **(j) commercial use without prior written consent unless otherwise authorized; (p) AI/ML development/training; (q) storing/caching/archiving; (r) modification/distribution/derivative works**. API-specific rules independently address **(k) AI/ML** and **(l) storage/cache/archive**. The original series publisher and FRED delivery service are distinct rights layers. This is a policy reading, not a finding that every use would violate those clauses.
- Reject synthetic example release dates as contemporary evidence. Publisher schedules are guidelines, not first-seen receipts; the Board's [H.10 announcement](https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H10) documents a correction dated August 12, 2026, and Treasury's normal release can be at or after 18:00 Eastern.
- Reject live-provider tests, backtests, retroactive approval records, repeated synthetic Supabase evidence writes, a legacy Score source switch, or a new public index while the original Score and proposed independent study are both HOLD.

The existing [FRED clause crosswalk](../governance/fred-terms-clause-crosswalk-2026-10-29.json) and [source retention policy](source-retention-policy.md) should remain the governing FRED citation records; this addendum neither replaces them nor creates a new FRED transport fallback.

### Safe work still available

Offline tests and metadata-only source-definition reconciliation are permissible research preparation. The first future authorization requests should be (a) exact source-and-transport legal disposition for each of the four, including caches, backups, correction receipts and public derived histories; (b) independent **owner decision** on whether a genuinely distinct four-signal methodology is wanted; then, only after both, (c) a narrowly scoped real-source as-of/transport proof with its own explicit approval. EIA lease-stock/SPR definitions, Treasury candidate XML field mapping, and H.10 release-vintage recovery all remain unresolved.

**Release decision:** Existing Score rights `HOLD`; independent four-signal study `SYNTHETIC_ONLY_RESEARCH_HOLD`; all 56 permissions `false`; owner/legal receipts `null`. No change to the publication gate.
