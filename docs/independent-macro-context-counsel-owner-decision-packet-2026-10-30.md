# Macro Context Panel — consolidated owner and counsel decision packet
**Prepared:** October 30, 2026  
**Status:** DECISION REQUEST ONLY · RIGHTS HOLD · NO NEW MARKET-DATA LICENSING BUDGET  
**Reference:** [machine-readable nonactivating decision queue](../governance/independent-macro-context-owner-counsel-decision-queue-2026-10-30.json)  
**Control:** [Independent candidate #313](https://github.com/usdimpact/usd-impact-pipeline/issues/313) · [Legacy Score rights #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155) · [FRED/Treasury history #282](https://github.com/usdimpact/usd-impact-pipeline/issues/282)

## Executive decision required

Request a **scope-specific legal/source-rights review** and **separate product-owner economic decision**, without presuming that accessible U.S. federal data can be commercially stored or publicly republished without conditions. **This packet is not a written rights grant, counsel opinion, production ticket, license purchase, or data-access authorization.** Private contracts/correspondence, personal contacts and legal opinions should not be copied into the public GitHub repository.

The current owner direction is to *design and test a no-budget fallback using invented, synthetic evidence*; this **does not** authorize live source use, a public name, public publishing, historical replay or a Production release. The original Score v2 remains a separate eight-driver product; its licensing, historical archives, calculated values and rights-release gate are unaffected by this packet.

**Existing technical baseline (already complete, do not redo):** [PR #312](https://github.com/usdimpact/usd-impact-pipeline/pull/312) merged a pure standard-library, year-2099-only synthetic prototype: H.10 nominal Broad Dollar UP/DOWN/UNCHANGED; EIA crude stocks excluding SPR BUILD/DRAW/UNCHANGED; Treasury 10Y–2Y curve POSITIVE/FLAT/INVERTED and STEEPENING/FLATTENING/UNCHANGED. The design has three dials / four descriptive labels, **no composite score, weights, signals or backtest**, and fail-closed missing/version/first-seen receipt checks. **Its methodology has not received an independent owner release decision.**

## A. Source-rights requests: four exact candidates, fourteen distinct use scopes

Source-specific evidence is documented in [exact-series matrix](../governance/score-four-source-exact-series-rights-matrix-2026-10-29.json), [Treasury/EIA XML and category review](score-treasury-eia-publisher-metadata-review-2026-10-30.md), [H.10 history review](score-four-source-exact-series-rights-review-2026-10-29.md) and the [draft synthetic product matrix](../governance/independent-macro-context-fallback-draft-2026-10-30.json). The rights matrix already contains **56 `false` permissions** (14 x 4); the decision queue separately tracks all **56 corresponding questions as `UNREVIEWED`**, never `ALLOW`. Merely completing a review checklist cannot unlock any underlying runtime flag.

| Exact candidate | Published evidence we can rely on | Unresolved legal/provenance questions | Mandatory technical blocker before future real-data proof |
| --- | --- | --- | --- |
| **Federal Reserve Board H.10 nominal Broad Dollar Index**, `H10/H10/JRXWTFB_N.B` | [Board disclaimer](https://www.federalreserve.gov/disclaimer.htm) generally recognizes Board-authored public-domain text with non-Board exceptions and attribution; [2019 technical Q&A](https://www.federalreserve.gov/releases/h10/h10_technical_qa.htm); [2026 DDP transition notice](https://www.federalreserve.gov/data/data-download-fred-information.htm) | Does any source input, index design or trade-weight material require separate permission? Is commercial label display, revision retention, backcast or direct automated access within permitted scope? | **2019-02-04** same-mnemonic change old goods-only to goods-and-services and **2019-06-24** daily base change; post-November-9 direct Board XML durability and actual first release/correction receipts |
| **EIA WPSR `WCESTUS1`**, U.S. weekly crude inventories **excluding SPR**, not WTI | [EIA copyright/reuse](https://www.eia.gov/about/copyrights_reuse.php) generally permits EIA-produced content with source/date acknowledgment but excludes protected contributed material; [retrieval policy](https://www.eia.gov/about/privacy_security_policy.php) restricts excessive bots | Is this exact statistical survey series fully government-produced? Are qualitative BUILD/DRAW outputs and persistent corrections/history permissible? Which rate limits and citation/date notices govern? | Reconcile [excl.-lease-stock](https://www.eia.gov/dnav/pet/PET_STOC_WSTK_A_EPC0_SAX_MBBL_W.htm) and [historical incl.-lease-stock](https://www.eia.gov/dnav/pet/pet_stoc_wstk_a_epc0_saxl_mbbl_w.htm) labels with the chosen WCESTUS1 version without assuming numerical/vintage parity; WPSR release-date/format staging |
| **U.S. Treasury direct 2Y nominal par CMT**, static `BC_2YEAR` XML example | [Treasury XML documentation](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed) identifies the sample field and `daily_treasury_yield_curve` transport; [Data.gov Treasury nominal yield curve CC0 catalog](https://catalog.data.gov/dataset/interest-rate-statistics-daily-treasury-yield-curve-rates) is positive dataset-level evidence | Is exact-curve commercial calculation, archive, historical qualitative curve-label publication and original FRBNY-originating indicative quote use covered? What retention/transport rules apply? | Publisher example tag does **not** prove current live field/native series ID, first-seen timing or permission to retrieve. Pair with 10Y from the **same exact curve revision** |
| **U.S. Treasury direct 10Y nominal par CMT**, static `BC_10YEAR` XML example | Same Treasury native XML documentation/CC0 catalog, **separate from H.15 and FRED DGS10** | Confirm 10Y-specific public slope/history permission, any upstream quotation rights, retained versions and disclaimers | Verify current live source, initial/version/first-seen as-of receipts and **same immutable 2Y/10Y snapshot** before any real observations may be processed |

**Primary-source rights boundaries:**

- The Board's 2019 retrospective methodology and daily base revisions create **two** historical comparability questions. Same series mnemonic ≠ unchanged economic definition, and latest backcast ≠ historically published version. H.10 usually releases the preceding business week's observations on **Monday around 16:15 ET**, or next business day after a holiday.
- EIA survey reuse rules do not authorize previously licensed **WTI/Brent spot quotes**. The chosen inventory observation is a stock level; a build/draw cannot be interpreted as a direct forecast of crude oil prices.
- Treasury 2Y/10Y values are published using Treasury methods and market indicative quotes, with normal **18:00 ET or later** availability; the observation date cannot substitute for the publication/vintage receipt. The illustrated BC tags prove historical documentation, **not live payload availability or native series IDs**.
- **No FRED fallback.** FRED is operated by the **Federal Reserve Bank of St. Louis**, not the Board or Treasury. The [FRED Services terms](https://fred.stlouisfed.org/legal/terms/) restrict certain commercial use, AI/ML, storage/caching/archiving and derivative/distribution activity (Services **(j), (p), (q), (r)**; API **(k), (l)**); any allowed future FRED delivery would require its *own* scoped rights evaluation and separate explicit authorization, not a convenience switch from Board/Treasury.
- A publisher's CC0 listing or U.S. government public-domain policy is **evidence**, not a provider-specific executed agreement, a resolution of third-party exceptions, authorization to scrape, or owner permission to release a product.

### Fourteen independent questions counsel/source owner must dispose for **each** source and transport

| Right/technical use scope | Required answer in a private, scoped determination |
| --- | --- |
| 1. Commercial internal ingestion | May USD Impact access exactly this publisher series through the named transport for an educational commercial website? |
| 2. Commercial non-display transformation | Is computation of a qualitative label / 10Y–2Y spread authorized without publishing component values? |
| 3. Transient processing | May temporary in-memory calculation occur; what data must be disposed after computation? |
| 4. Provider content retention | May original feed payload or observation(s) persist anywhere, even briefly? |
| 5. Observation archives | Are dated history or source/backcast archives permitted? Which periods and deletion obligations? |
| 6. Logs and caches | Can access logs, temporary caches, build logs or diagnostic traces contain values/metadata, and for how long? |
| 7. Backups and recovery | Are immutable/backed-up copies or disaster recovery mirrors allowed? What disposal plan applies? |
| 8. Revision vintage receipts | May first-release/version/first-seen evidence and hashes be stored privately, and must numerical values be omitted? |
| 9. Public aggregate distribution | Is a three-dial qualitative public page allowable, including historical labels? |
| 10. Public component distribution | May any underlying specific number, contribution or element be shown, including member views? |
| 11. Public history distribution | Does publishing a dated label sequence or charts require separate derived-data/historical rights? |
| 12. AI/ML processing | May any observations or related content be used in AI/ML systems; if not, prohibit completely? |
| 13. Downstream redistribution | Are screenshots, exports, copied feeds or syndicated results prohibited/limited? |
| 14. Live automated source retrieval | Does an official XML/API endpoint authorize this specific automated frequency, transport, user-agent and rate policy? |

**A valid later decision record** should specify: exact series identifier and original rightsholder, direct distributor/transport, exact commercial use and intended outputs (public versus member versus internal), each of the 14 rights above, exceptions, permitted retention/disposal, attribution/branding, effective period, written rationale or agreement evidence, reviewer's authority, and separate USD Impact owner approval. Store sensitive signed agreements **privately in an approved location**, referenced only by a redacted stable evidence pointer if lawful. **Never put secrets, staff names, billing identities, private provider emails or contractual text into a public PR.**

## B. Owner economic and educational decisions — separate from source permission

The existing invented-data prototype demonstrates engineering feasibility, **not** economic usefulness, performance or a trading signal. The owner still must decide explicitly:

1. Whether to continue, hold, or abandon this **genuinely different** no-cost product (separate from legacy Score v2).
2. Whether the four outputs in three dials are a useful **descriptive** educational view or need a different concept; **no automatically approved weights, thresholds, backtest or prediction claims**.
3. Whether to disallow a single composite numeric Score indefinitely, maintaining the distinct-product boundary.
4. The audience and access design: free public information vs member-only explanation; educational disclosures, attribution, language and limitations.
5. A **reporting schedule that does not claim Friday current-week completeness**: H.10 usually Monday, EIA usually Wednesday, Treasury around 18:00 ET or later. A fully known same-Friday four-signal panel is not possible under the described publisher release schedule. Each release must use actual as-of receipts for **two reference Fridays**, not projected calendars.
6. Whether missing, delayed, revised or unverified sources always suppress **all labels** (fail closed), and how to explain later corrections without implying foresight.
7. The final name, public description and separation from USD Impact Score, whose eight-driver schema and **617-week history** cannot be inherited, backfilled or spliced.
8. Any *later* real-data study, historical archive policy, source proof or public release — each requires an independent recorded authorization after the relevant rights/security gates.

The machine-readable queue registers **12 distinct owner decision prompts, all pending and non-authorizing**; it does not collect or fabricate a signature.

## C. Disposition order, evidence needed and no-go outcomes

| Gate | Responsible authority | Minimum *future* evidence | Until then |
| --- | --- | --- | --- |
| 1. Identify each original source/transport and non-Board/non-EIA/market-quote exceptions | Source-rights reviewer + counsel | Exact series, originator, delivery product and contributor caveats | **NO SOURCE DATA** |
| 2. Determine scoped commercial calculation, derivative display and redistribution rights | Authorized source owner or counsel | Private, dated, use-specific written determination for all fourteen dimensions per source | **NO COMPUTATION/OUTPUT** |
| 3. Set lawful value, first-seen receipt, cache/log, Git, archive and backup retention/disposal | Counsel + privacy/security | Written storage rules including corrections, vendor histories, backups and disaster-recovery fate | **NO REAL STORAGE** |
| 4. Sign off independent methodology, missing-data behavior, schedule, name and audience | Product owner + educational compliance | Explicit owner direction distinct from permission to design a synthetic prototype | **NO PUBLIC PRODUCT** |
| 5. Authorize a narrowly bounded **non-production** real-source transport proof | Owner + engineering security, *after* sources/rights/retention | Exact source route, allowed operations, first-seen receipt plan, rate limits, zero-cost scope and stop conditions | **NO DATA GET/HEAD** |
| 6. Test prospective point-in-time and revision handling | Engineering + rights reviewer | Legally retained first-published and first-seen versions for both Fridays and same-curve Treasury pairing | **NO HISTORIC INFERENCE/BACKTEST** |
| 7. Approve a versioned public schema, legal attribution, member/public consumer rules and preservation | Counsel, product owner, compliance/security | Reviewed outputs, public history policy, non-Production preview and rollback plan | **NO LIVE OR PUBLIC ARTIFACT** |
| 8. Issue distinct Production owner release | Owner; protected GitHub / deployment operators | Exact-head CI, independent signed release decision, protected safety and verified recovery | **PRODUCTION HOLD** |

**Permitted right now:** public/publisher *policy and static metadata* reading, clarification of legal questions, invented-data tests and documentation PRs only. **Not permitted:** provider observation GET/HEAD, active crawler, data history replay, SQL/Supabase evidence writes, commercial feed processing, paid licenses/subscriptions, vendor outreach, website/Cloudflare/Vercel/Render/Resend/Supabase modifications, FRED substitution, source switch, Score history rewrite, member changes or publicity.

## D. Legacy Score remains an independent legal and preservation case

The [existing eight-driver Score successor rights packet](score-v2-successor-rights-readiness-and-btc-source-2026-10-29.md) separately tracks **8 source/transport relationships and 16 denied rights dimensions each (128 false)**, including unresolved historical Yahoo-delivered BTC original OHLC ownership, S&P DJI, CME, ICE and Cboe rights, plus FRED. This packet **does not grant or replace any** of those rights, change original Score formula/weights, release 617 weeks of historical data or approve removing archived public assets. [Original provider/counsel packet](score-provider-counsel-rights-decision-package-2026-10-28.md) remains the correct legacy handoff.

S&P's previously recorded licensing discussions belong to the **existing** provider case. The independent no-budget panel is not an excuse to duplicate outreach or pay for an original Score license. Reviewers must separately decide how existing public archives, Git clones/forks, historical Cloudflare Pages deployments, analytics, Actions caches, off-platform backups and subscriber/research consumers may lawfully be preserved or remediated. Do not purge and do not migrate existing provider-derived values on this authorization.

## E. Decision outcome ledger (intentionally empty)

The current decision queue is *not an executable release receipt*. Every source review dimension is `UNREVIEWED`; all provider/counsel and project-owner signoff references are `null`; all execution switches are `false`; all owner methodology/name/publication choices are pending. No correspondence was sent and no legal authority was assumed.

**Next human inputs needed:** a role-authorized exact-source legal determination (preferably handling Board, EIA and Treasury original-source and transport/upstream scope), an owner decision on whether to continue the distinct *descriptive-only* design, and later a separate narrow transport proof approval if rights allow. **No response is presumed.**

**Final state:** Stage D rights and owner decision **HOLD**. All 56 four-source permissions remain **false** in both original governance records. Legacy eight-driver Score remains **HOLD** under Issue #155. Zero paid market-data budget unchanged. No real provider observation or Production publication is approved.
