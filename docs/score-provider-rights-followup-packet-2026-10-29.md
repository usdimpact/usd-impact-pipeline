# USD Impact Score v2 — provider-rights follow-up and decision checklist

**Prepared:** 2026-10-29  
**Status:** RIGHTS HOLD, review-only, zero additional licensing budget, no outreach sent from this PR.  
**Control:** [Issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155) and [Issue #282](https://github.com/usdimpact/usd-impact-pipeline/issues/282). This is a factual **permission-request pack**, not legal advice, a license, or an authorization to fetch, retain, transform or publish new provider observations.

## 2026-10-30 provider-response addendum — supersedes the S&P sales-referral status below

**Material new evidence (private correspondence, not republished here):** On **2026-10-29**, S&P Dow Jones Indices replied in writing that the *described use case* requires a **paid license**. The submitted request covered commercial internal calculation using S&P 500 as one of the original eight Score inputs, combined with publication of only a non-reconstructible aggregate Score, regime, week-ending date and historical aggregate series, without component observations or normalization evidence. The answer did **not** separately enumerate every possible internal/non-public exception, historical-remediation step, license fee, or exact machine-readable publishing condition; do not invent them.

**Operational disposition under the existing $0 added-license budget:** the original eight-input Score is **NOT cleared for a no-cost release**. Aggregate-only technical containment is not a rights workaround. Do not schedule another S&P sales call, buy a license, open a duplicate case, switch the S&P 500 source, modify the frozen formula, fetch provider data, edit public Score artifacts, delete archives, or activate publication based on this correspondence. A funded/contracted route would require a new explicit owner and provider/counsel approval; otherwise advance the **separate** government-source Macro Context Panel through its own exact-source rights/retention review under [Issue #313](https://github.com/usdimpact/usd-impact-pipeline/issues/313). That panel is **not** the eight-input Score or a continuation of its historic series.

**Evidence hygiene:** [the dated S&P disposition manifest](../governance/score-spdji-provider-disposition-2026-10-30.json) stores only category-level confirmation and all-false permissions. The private original message remains in the owner's existing mailbox; no names, case identifiers, contact addresses, private quotations, or email bodies are reproduced in the repository. Other 2026-10-29 contact snapshots are retained as historical records and may contain earlier *pending referral* status for S&P. Treat **this dated addendum** as the newer status, **not** as a legal approval.

**Unchanged:** Issue #155 (Score redistribution) and Issue #282 (FRED retention/historical treatment) remain open on HOLD; FRED's conditional processing answer does not create storage rights. Cboe's no-cost answer remains unverified; CME/ICE/Yahoo source and transport licenses remain unresolved. The independent Macro Context Panel remains HOLD. No provider outreach or operational action is requested from this PR.

## Exactly what USD Impact proposes

USD Impact uses an eight-driver weekly educational Score (DXY, WTI, S&P 500, VIX, Bitcoin, Gold and two nominal Treasury yields). This review keeps the frozen Score method unchanged. We seek an individually documented answer for the **narrowest possible public output**: week-ending date, non-reversible **aggregate** Score, regime and aggregate score-history chart. Full source levels, individual driver z-scores, contributions, normalization means/std and revision diagnostics should **not** be presumed publishable. Existing public component-derived histories are separately on rights HOLD and need historical disposition.

Every source decision must cover **both**:
1. Commercial transient/internal calculation and, if needed, lawful retained historic evidence or required disposal; and
2. The separate use, attribution and machine-readable website distribution of non-reversible aggregates, components, diagnostics and old archive files.

Do not conflate the **transport** (Yahoo/yfinance, FRED) with the **original owner** (ICE, S&P DJI, Cboe, CME, Treasury); both may impose different conditions. Do not assume a consumer product, educational tone or publicly displayed price is an exemption.

## Current provider/correspondence checkpoints (not grants)

| Provider family | Last known checkpoint | Decision still missing | Next no-cost action |
|---|---|---|---|
| **FRED — DGS2/DGS10** | Oct 29 conditional answer for suitably tagged public-domain series, citation and disposal; no storage rights | Whether any existing independently calculated weekly aggregates, normalization statistics or hashes constitute restricted retained FRED Content and how to remediate already public histories | Counsel/owner interpretation first; do **not** repeat generic FRED use question |
| **Yahoo Finance/yfinance delivery** | No confirmed explicit commercial transport/retention rights | Exact API/vendor contract; individual Yahoo versus original-owner permission; aggregate rights | Establish licensed transport alternatives and applicable terms; no live fetch |
| **S&P Dow Jones Indices** | Oct 28 request referred to sales; no affirmative grant | Internal use of S&P 500 observations and public non-reversible aggregate | Await existing referral; no duplicate case |
| **Cboe / VIX** | Oct 28 sales qualification received; owner already replied asking whether zero-cost aggregate-only use is permitted | Written yes/no and any conditions for VIX-derived output | Await answer; avoid sharing personnel/KYC details via a public repository |
| **CME — WTI/Gold** | Oct 27 derived-data inquiry sent, no rights answer found | Internal use, derived-index rules and public aggregate/research/archive | Follow up on *existing* outreach only after reasonable elapsed time |
| **ICE / U.S. Dollar Index** | No independently verified ICE permission reply | USDX underlying index data rights, Yahoo-delivered input scope, public aggregate | Identify correct licensing route and no-cost exception without buying data |
| **U.S. Treasury / Board H.15** | Official feed documentation and synthetic-only parser reviewed | Direct retrieval, commercial retention, revision timing and H.15/FRED parity, third-party upstream quote exclusions | No real-source test until a source-level rights decision |

**Source links:** [FRED terms](https://fred.stlouisfed.org/legal/terms/), [Yahoo developer guidelines](https://legal.yahoo.com/us/en/yahoo/guidelines/ydn/index.html), [S&P terms](https://www.spglobal.com/en/terms-of-use), [Cboe July 2026 policies](https://cdn.cboe.com/resources/membership/Market_Data_Policies_july2026.pdf), [CME derived-data licensing](https://www.cmegroup.com/market-data/browse-data/derived-data.html), [ICE USDX rights statement](https://www.ice.com/products/194/US-Dollar-Index-Futures/), [Treasury XML](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed) and [Treasury developer notice](https://home.treasury.gov/developer-notice-xml-changes). Public terms are contextual evidence; provider-specific executed agreements or counsel disposition govern actual rights.

## Standard request matrix (each provider must answer for its own applicable data)

1. Identify the **exact instrument, original data owner, licensed delivery service, governing agreement and effective date**. Distinguish direct feed, delayed data and third-party aggregation.
2. Is USD Impact permitted to retrieve observations for **commercial internal, non-display, educational Score arithmetic**, without a paid data license? If yes, specify source path, attribution, rate limits and restrictions.
3. May we keep **daily or weekly values**, derived z-scores, normalized moments, rolling history, hashes/receipts, or reversible/reproducible derived statistics in an access-controlled private audit store? State time limit, backup/CI/cache/log copies, geographic and deletion rules. Explicitly answer **no** when prohibited.
4. May we publish only **date, a non-reversible aggregate eight-driver Score, regime and historical aggregate chart**, with no input levels, individual driver contributions or reconstructible component data? Is a derived-data license, declaration, form, fee, or audit required?
5. Are **machine-readable JSON/CSV**, HTML charts, screenshots, explanatory prose, emailed reports and public historical archives treated differently? Are old releases subject to removal/notification?
6. Which **provider/source trademark, attribution/citation, access date, subscriber status, confidentiality and use-case statements** are required or forbidden? Must the provider be named in the methodology?
7. If the above is not permitted **without cost**, please explicitly confirm the applicable restriction and the type of paid agreement required. USD Impact does not authorize a purchase or subscription in this research phase.

**Source-specific detail:**

- **FRED:** identify series copyright labels at the time of each observation and legal treatment of already retained/released transformed values, hashes and internal runner logs. Its response already clarifies **transient conditional commercial use with required citations and disposal, not storage**. Do not seek an implied exception from silence. Query counsel about the precise allowed lifespan of computation artifacts and derived independently calculated Score history.
- **Yahoo:** verify whether the actual data transport used by yfinance is an authorized interface for commercial use, and which original owners must also consent. Generic Yahoo developer guidelines do not automatically govern every Yahoo finance endpoint.
- **S&P DJI:** specify that the source is `^GSPC` as delivered by Yahoo and the aggregate is **not** an S&P-linked investable product, but ask whether public aggregates nonetheless require written derived-data permission. Respect the already open sales referral.
- **Cboe:** distinguish VIX-index observations from Cboe direct-feed entitlements. The seller's generic Derived Data section may not settle a VIX Global Indices Feed use case; require a product-specific answer. The no-cost question is already pending.
- **CME:** specify `CL=F` and `GC=F` Yahoo-delivered futures observations, a weekly aggregate Score, and whether CME considers any output a derived index, reference value or chargeable derived work.
- **ICE:** ask permission for an educational mixed-driver aggregate incorporating ICE-owned U.S. Dollar Index, including correct trademark/source naming and historical values. Do not assume Yahoo's availability licenses ICE index values.
- **Treasury/H.15:** ask separately for direct government-source commercial archiving/redistribution, H.15 republisher rights, revision/availability dates, XML pagination, and any rights in upstream dealer quotes; do not silently replace DGS2/DGS10.

## Short no-cost clarification template (use only in existing or owner-approved thread)

> USD Impact is evaluating a non-investable, educational weekly indicator comprising eight independently weighted market inputs. Our proposed external output is limited to a non-reversible aggregate Score, regime and aggregate history; no individual source observations, normalized component values or reconstruction statistics would be published. Could you confirm in writing whether (a) commercial internal calculation, (b) temporary processing and any retained research evidence, and (c) this restricted public aggregate are permitted without a paid agreement for the specific dataset you control? If not, please identify the required license and historical-output treatment. We will not implement changes or purchase a paid license while the rights review is open.

**Do not send or reuse this template automatically.** Tailor it to the existing provider correspondence; **do not reopen** the S&P or Cboe case simply to duplicate questions that are already pending. Never include passwords, internal tokens, personal financial/trading details, or actual market observations in the public GitHub record.

## How to record the reply without creating false rights

- Keep the machine-readable [follow-up queue](../governance/score-provider-rights-followup-queue-2026-10-29.json) in `RIGHTS_HOLD_RESEARCH_ONLY`; all source-level grants for retention/publication remain `unapproved`.
- For each provider, archive the underlying private rights response outside public GitHub, then create a **minimal non-sensitive** dated citation/authority and exact permitted scope in the [decision receipt template](../governance/score-rights-decision-receipt.template.json), leaving other providers pending.
- Counsel must independently decide the treatment of the existing public Class C/E/F histories, hash-only receipts and historical backups, and whether an aggregate-safe transformation is legally sufficient.
- A provider's statement allowing *internal processing* does **not** authorize private retention, historical backfill, public aggregates, redistribution or Production deployment.
- **No gate may change to ALLOW** until all required source classes are handled and a separately attested decision receipt, exact-head CI, consumer migration, backup/restore evidence and owner Production approval are recorded.

## Remaining independent decision gates

**Legal/provider:** permitted processing, retention, redistribution, trademarks/citations, archives and termination responses.  
**Engineering:** approved private real-data boundary, public-safe schema, member/research consumer compatibility, immutable evidence where lawful, tested legal-safe rollback.  
**Owner:** written approval of any real-source test, any paid service and any Production/commerce changes.  
**Current state:** all these remain **HOLD** except completed synthetic-only engineering rehearsal.

No mail was sent, no provider-data values were fetched/copied, and no stored data, public archive, source, Score formula, Supabase/Cloudflare/Vercel configuration or production gate was modified by this document.
