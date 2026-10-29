# USD Impact — research applicability and FRED clause-reference correction (2026-10-29)

**Decision:** Apply the citation corrections and evidence-priority controls below. **Do not** release the Score, store real source data, switch sources, purge history or authorize paid licenses. This is an engineering/governance desk review, not provider approval or legal advice.

## Research report: useful versus already implemented

The completed Deep Research output was an **email-access and provider-status review**, not the fully scoped independent eight-source license/alternative-data research originally requested. Its broad conclusion to keep publication on HOLD is consistent with [Issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155). Its provider follow-up matrix largely duplicates [merged PR #298](https://github.com/usdimpact/usd-impact-pipeline/pull/298), the corrected retention policy [PR #295](https://github.com/usdimpact/usd-impact-pipeline/pull/295), and the archive/preservation plan [PR #294](https://github.com/usdimpact/usd-impact-pipeline/pull/294). Do **not** copy duplicate email scripts or initiate a second licensing case just because the research output proposed another message.

The report claimed no Gmail connector was available **to that research run**. Independently, the project-owner-authorized Gmail connector **was** accessible to the assistant: an October 28–29 scoped review located a FRED response, S&P support/sales referrals and Cboe sales inquiries, **five relevant inbound provider messages** in total, **zero attachments in those retrieved messages**, and no new signed permission or affirmative CME/Yahoo/ICE reply in the scoped searches. This is a bounded search result, **not** a full forensic account-wide message/attachment clearance. Private provider email bodies, participant names, message IDs, addresses and quoted staff wording are deliberately excluded from this public repo.

## Public primary-source terms independently rechecked

| Source/transport | Public source observation | Decision for USD Impact |
|---|---|---|
| **FRED Services** | [FRED terms](https://fred.stlouisfed.org/legal/terms/): **(p) AI/ML** use, **(q) storage/cache/archive**, **(r) modification/distribution/derivatives**. The existing repo inverted the Services (p)/(q) labels. | Correct the clause crosswalk; FRED's conditional public-domain commercial processing and required citation/disposal **does not grant** retention/public-derived redistribution |
| **FRED API** | Same [published terms](https://fred.stlouisfed.org/legal/terms/): **(k) AI/ML**, **(l) API-related storage/cache/archive**. The API section also imposes a non-endorsement notice on applicable applications. | Treat API obligations separately; leave publication HOLD |
| **S&P DJI — S&P 500** | [S&P Global terms §4.2](https://www.spglobal.com/en/terms-of-use) restrict SPDJI data to non-commercial personal use unless otherwise permitted; creating indices/historical databases and derived data requires express written consent. | The eight-driver aggregate's lack of an investable product or reversible components is **not** a license exemption. Await existing case #01036004 |
| **CME — WTI/Gold futures** | [CME's licensing page](https://www.cmegroup.com/market-data/license-data.html) lists separate internal **non-display research/calculation** and **derived-data/new-product** licenses; its [derived-data page](https://www.cmegroup.com/market-data/browse-data/derived-data.html) includes indices and reference values. | Explicit permission needed for the actual commercial use. A free web quote or an internally calculated Score is not a confirmed no-cost license. Await the existing inquiry |
| **ICE — USDX/DXY** | [ICE data distribution terms](https://www.ice.com/fixed-income-data-services/data-and-analytics/quote-data-distribution) say derived objects, including those **not** reverse-engineerable, require case-by-case consideration; public delayed display also requires approval. | Do not infer an exception from a non-reversible aggregate; identify the exact USDX/index rightsholder and authorized transport |
| **Cboe — VIX** | Existing Cboe sales correspondence has not produced a no-fee VIX derived-data grant; the report cites the July 2026 policy but did not provide an executed contract. | Keep PENDING, await reply in existing zero-cost thread; do not copy any private qualification details into GitHub |
| **Yahoo/yfinance** | Generic [Yahoo API/developer terms](https://legal.yahoo.com/us/en/yahoo/guidelines/ydn/index.html) alone do **not** establish commercial rights in the specific Yahoo Finance market feed or underlying exchange/index series. | Confirm transport + owner rights separately; no fetch or source switch |
| **Treasury / Board H.15** | [Treasury XML feed](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed) and [Treasury 2022 pagination notice](https://home.treasury.gov/developer-notice-xml-changes) support synthetic integration design, **not** production data/source/retention/parity authorization. | Retain standalone offline-only parser; no real-data collection or replacement |

**Legal distinction:** A source's copyright status and its publisher/distributor's enforceable terms are different questions. The above is a record of published positions and the current engineering HOLD, not a finding of infringement, a binding legal interpretation or a signed provider grant.

## Exactly what this assessment changes

1. Correct Services clause labels in the authoritative current policy and Issue #282 audit; preserve all historical contents and dates. API clause **(l)** and API **(k)** remain correctly classified.
2. Add a machine-readable [FRED clause crosswalk](../governance/fred-terms-clause-crosswalk-2026-10-29.json) and an **offline test** to prevent the old inversion from silently returning.
3. Clarify that the Deep Research mailbox-access limitation is *specific to that research run*, not proof that the actual account or all email was inaccessible.
4. Treat S&P internal use, CME non-display calculation and derived distribution, and ICE non-reversible derived products as separate licensing questions requiring provider/counsel decisions.
5. Keep a provider-scope and legal-safe history decision **before** any real evidence replication, URL removal, Cloudflare cache purge, rewritten Git history or source change.

## Execution readiness matrix

| Gate | What has been verified | Still required before execution |
|---|---|---|
| Eight Score workflow fail-closed protections | Merged #285/#291 and live HOLD-path CI | Inventory manual/external provider entrypoints before source resumption |
| Development private synthetic evidence | Prior OIDC write/read and immutable fixture checks | Rights-cleared real evidence retention before new real storage |
| Public file and deployment metadata | Current Git tree + 1,921 Pages deployment records inventoried | Counsel disposition on current/historical Git, caches, preview hashes, Actions logs and off-platform backups |
| Offline Treasury adapter | Merged #287/#296 synthetic tests and explicit no-partial-page scope | Direct source commercial rights, complete periods, availability/revisions and exact parity before any real-data comparison |
| Provider replies | Gmail review of scoped FRED/S&P/Cboe messages, with no signed grants | S&P sales, Cboe no-fee, CME, Yahoo, ICE, Treasury/H.15 and counsel, each by right and product |
| Score public aggregate-only schema | Concept and technical plans exist | Provider permission for public aggregate/history, verified non-reversibility, all site/research consumers, member auth and legal-safe rollback |
| Publication/Production | Rights gate is HOLD and Cloudflare canonical Production previously unchanged | Signed rights receipt and independent owner-approved release gate |

### No-go criteria

**Do not execute real-provider ingestion, new retention, public Score publication, source substitution, historic purge or Production replacement** if any relevant provider's rights remain pending, the signed decision receipt is missing, a source's original owner/transport contract is unresolved, the consumer migration or rollback would re-expose component histories, or CI/preview cannot demonstrate the intended fail-closed path. A green static test alone is not a provider license.

**Next review:** obtain targeted source/rights decisions (not duplicated outreach), conduct a separately scoped public-source legal/technical research on truly reusable alternate datasets if no-cost permissions prove unavailable, and let counsel decide historical preservation before preparing an explicitly bounded Production PR. No automatic outgoing email, paid subscription, provider-data fetch, archive mutation or Production change occurs from this memo.
