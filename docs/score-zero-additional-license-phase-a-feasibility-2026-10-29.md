# Phase A — Eight-driver zero-additional-license source feasibility

**Research date:** 2026-10-29  
**Scope:** public primary-source documentation and read-only existing repository code. **No real financial observations were fetched for this study, no providers contacted, no model calculation performed.**  
**Decision status:** **NO-GO for silently replacing the existing USD Impact Score v2**. Synthetic research on a separately defined indicator may continue; provider and counsel decisions remain outstanding.  
**Controlling:** [Rights HOLD #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155), [FRED retention audit #282](https://github.com/usdimpact/usd-impact-pipeline/issues/282). Public archive, private evidence, source-switch and Production grants stay false.

## Executive decision

The live legacy method, frozen at [the production source file](../usd_impact_score_v2.py), is a weekly, eight-driver, equal-magnitude weighted composite: **ICE DXY (+), CME WTI front futures (−), S&P 500 (−), Cboe VIX (+), BTC/USD market spot (−), CME Gold futures (−), 2Y U.S. Treasury yield (+), and 10Y yield (+)**; each magnitude **0.125**. Current delivery is Yahoo/yfinance for six and FRED DGS2/DGS10 for two. It targets the completed **Friday** week and has a publicly distributed legacy derived-history surface. A free webpage, free API key, publicly available download or government-published *third-party market quote* does not establish commercial rights to store, recompute, backfill, expose per-driver contributions, or publish non-reversible aggregates.

**Research result:** Of the original eight, **two nominal-yield input concepts** have direct Treasury official-source counterparts requiring rights/timing/parity review; **one broad-dollar and one government petroleum-inventory** family could support a newly named *different* macro indicator; the other original market-price/index drivers do not have a verified zero-fee, commercially cleared, weekly, like-for-like alternative. The 4-signal research design is **not** an eight-driver Score, has no assigned weights and is not approved for production/publication. The original 617-week history cannot be represented as continuous, methodologically comparable history without separate source and model approval.

The one-line recommendation is **keep the eight-driver Score on HOLD; research a distinctly named, smaller federal-source macro regime product only if the owner later approves a different methodology and counsel clears each feed and use.**

## 1. Candidate decision matrix — all eight legacy inputs

| Legacy driver, source and sign | Zero-fee/official candidate(s) | Frequency and availability | Licensing and semantic conclusion | Phase A disposition |
|---|---|---|---|---|
| **DXY (+)** — ICE U.S. Dollar Index, Yahoo `DX-Y.NYB` | Federal Reserve Board nominal **Broad** or Advanced Foreign Economies USD index, H.10 | Daily observations; **previous week published Monday ~4:15 p.m. ET** | Board generally permits copying/public distribution of its own website information with citation, except third-party materials. Different country/currency composition and trade weights; not the six-currency ICE DXY. | **Research new model only.** No ICE DXY parity or current-week Friday availability |
| **WTI (−)** — CME rolling front futures, Yahoo `CL=F` | EIA Cushing **spot**; or EIA **commercial crude stocks** from survey WPSR | Spot assessed daily and published with lag; stocks **weekly Friday reference, published next Wednesday** | **Material trap:** EIA says historical WTI spot prices were **purchased from Refinitiv** and republished with permission. General EIA public-domain language expressly excepts private content. Official survey inventories appear more promising, but are physical quantity—not futures prices. | Spot **BLOCKED pending Refinitiv downstream rights**; inventories **new model only** |
| **SPX (−)** — S&P 500 index, Yahoo `^GSPC` | BEA quarterly U.S. corporate profits | Quarterly, delayed and revised | No equivalent daily/weekly licensed-free market cap index established. BEA profits measure company earnings rather than S&P 500 valuations. [S&P terms](https://www.spglobal.com/en/terms-of-use) require express written consent for derived data and historical indices. | **No weekly like-for-like candidate** |
| **VIX (+)** — Cboe VIX, Yahoo `^VIX` | OFR FSI, Chicago Fed NFCI, or Treasury-based realized interest-rate volatility | OFR daily with ~2-day lag; NFCI weekly next Wednesday; rate-vol research only | OFR [component list](https://dmtenrspjuuhr.cloudfront.net/financial-stress-index/files/indicators/index.html) explicitly includes **VIX and ICE DXY**, and uses **Refinitiv** inputs. Chicago Fed NFCI has proprietary/third-party-source ambiguity and [FRED labels it copyrighted](https://fred.stlouisfed.org/series/NFCI). Treasury *realized rate* volatility is not equity *implied option* volatility. | OFR/NFCI **not cleared**; synthetic rate-vol is **new model only** |
| **BTC (−)** — Bitcoin/USD Yahoo composite | CoinGecko Demo; Coin Metrics Community; native Bitcoin blockchain activity | API plan/history limits; chain-native stats possible at network level | [CoinGecko explicitly denies commercial rights on free/demo/keyless](https://support.coingecko.com/articles/1043089972-what-are-the-differences-between-commercial-and-custom-licenses); [Coin Metrics Community docs state free non-commercial](https://github.com/coinmetrics/docs-website/blob/master/api.md). On-chain difficulty/transaction activity is not the BTC/USD price. | **No cleared BTC/USD replacement; block free/demo APIs for commercial use** |
| **GOLD (−)** — CME continuous front gold futures, Yahoo `GC=F` | USGS annual gold data (CC0 data release); World Bank Pink Sheet monthly gold price | USGS **annual**; World Bank **monthly** | [USGS 2026 release](https://www.usgs.gov/data/mineral-commodity-summaries-2026-data-release) is explicitly **CC0**, but not weekly gold futures. [World Bank general CC BY 4.0](https://datacatalog.worldbank.org/public-licenses) depends on dataset/third-party license; London-fixing benchmark rights and monthly lag are unresolved. | **Neither is an equivalent weekly gold-futures source** |
| **UST 2Y (+)** — FRED DGS2 | Treasury nominal par curve `BC_2YEAR` via Treasury XML | Daily; typically by **6 p.m. ET**, may be delayed | Original U.S. Treasury publishes par yields; its 2025 methodology uses indicative bid quotes and monotone-convex interpolation. Still need transport/license, as-of availability, historical revision/parity, commercial retention and derivative permission. Existing parser **synthetic only**. | **Most promising near-subject candidate, NOT authorized** |
| **UST 10Y (+)** — FRED DGS10 | Treasury nominal par curve `BC_10YEAR` via Treasury XML | Same daily timing/conditions | Same terms, revision and parity questions. Do not assume identical historical FRED as-of vintages from matched tenor labels. | **Most promising near-subject candidate, NOT authorized** |

**A candidate is not a permission grant.** The [machine-readable source study](../governance/score-zero-license-phase-a-feasibility-2026-10-29.json) records **15** assessed alternatives/approaches across these eight drivers. Every single candidate's `source_rights_granted`, `full_series_parity_verified`, `public_derived_output_granted` and `real_source_retrieval_authorized` fields are **false**. The existing Score's weights, signals, official source maps, public archive and entitlements are untouched.

## 2. Key primary-source evidence and unusual risks

### A. ICE DXY versus the Federal Reserve trade-weighted dollar

The Board [H.10 release](https://www.federalreserve.gov/releases/h10/) and [trade-weighted methodology](https://www.federalreserve.gov/econres/notes/feds-notes/revisions-to-the-federal-reserve-dollar-indexes-20190115.html) document an index based on **U.S. trading-partner currencies and bilateral goods/services trade**, with changing weights. That index represents a distinct macroeconomic dollar concept from ICE's U.S. Dollar Index. No scale conversion makes the two identical; historical performance and normalization would change.

The Board [disclaimer](https://www.federalreserve.gov/disclaimer.htm) says its own website information is generally public-domain and distributable with attribution unless indicated otherwise, with an exception for privately sourced copyrighted material. A Board-hosted index still needs exact-series and transport terms checked.

**Timing failure:** H.10 releases last week's daily FX/index values **Monday around 16:15 ET**. Existing Score wants the week ending Friday and its Friday-night release. Same-Friday broad-dollar data would not yet have been officially published. A revised as-of contract would be mandatory.

**Infrastructure continuity:** Board H.10 notices state its DDP **Build Your Package** feature is scheduled for removal in the week of November 9, 2026 as DDP retires. Do not write a future pipeline assuming the historic DDP UI remains a stable source. A switch from Board's own publication to FRED would reintroduce separate FRED transport/storage terms.

### B. EIA crude spot prices have a documented third-party provenance exception

EIA's [Copyrights and Reuse](https://www.eia.gov/about/copyrights_reuse.php) allows reuse of government-generated products with acknowledgment and expressly cautions that private third-party material may be protected. The official EIA [STEO crude-price modeling handbook](https://www.eia.gov/analysis/handbook/pdf/STEO_Crude_Oil_Price.pdf), §2, **states that EIA purchases historical WTI/Brent spot-price time series from Refinitiv/Thomson Reuters and republishes them with permission**. This is an official source-provenance warning, **not** proof of permission for downstream commercial products. Confirm current rights with EIA and/or the underlying vendor before considering internal archives, computed histories or publication. No real source series was downloaded.

The original Score's `CL=F` represents a rolling CME futures contract; EIA Cushing `RWTC` represents physical spot. Even if rights were granted, **basis, contract-roll behavior, settlement times and weekend conventions would differ**.

A safer *macro-redesign* research option is **EIA's independently collected weekly U.S. commercial crude inventory** series, [WPSR stocks table](https://www.eia.gov/dnav/pet/PET_STOC_WSTK_A_EPC0_SAX_MBBL_W.htm). The WPSR is normally released **Wednesday 10:30 ET for the prior Friday's reference week**, as shown in [the EIA schedule](https://www.eia.gov/petroleum/supply/weekly/schedule.php). This is **not an oil price** and would need a new sign, normalization, handling of inventories' level/trend and economic rationale. Check for any upstream/third-party exclusions, even though the aggregate is presented in EIA's own survey report.

### C. Equity and VIX cannot be relabeled with government proxies

[S&P's terms](https://www.spglobal.com/en/terms-of-use) explicitly address derived data, index construction, historical databases and redistribution. Merely calling a derived eight-driver output **non-reversible** does not settle whether it is an unlicensed SPDJI-derived product.

[BEA corporate profits](https://www.bea.gov/data/income-saving/corporate-profits) are official quarterly accounting estimates, not a weekly equity valuation measure. They cannot substitute for `^GSPC` in the original weekly transmission framework without a substantial economic/methodology redesign.

The [OFR Financial Stress Index](https://www.financialresearch.gov/financial-stress-index/) is useful educational context, but [its inputs](https://dmtenrspjuuhr.cloudfront.net/financial-stress-index/files/indicators/index.html) include **Cboe VIX**, **ICE DXY** and Refinitiv-sourced data. Treating government publication as automatically erasing these underlying rights would be unjustified. The [Chicago Fed NFCI](https://www.chicagofed.org/research/data/nfci/current-data) is released Wednesday for the previous Friday and is regularly revised; [FRED's NFCI page](https://fred.stlouisfed.org/series/NFCI) displays a copyright warning. Neither stress index is VIX, and neither is established as a commercial-redistribution license-free substitute.

One could research **realized Treasury yield volatility** using independently permitted nominal yields. It would measure past *interest-rate* variation, not the *forward 30-day S&P options-implied volatility* represented by VIX. This would also overlap the two Treasury-level signals in a model.

### D. Free crypto APIs do not solve the BTC license

[CoinGecko's commercial-license support answer](https://support.coingecko.com/articles/1043089972-what-are-the-differences-between-commercial-and-custom-licenses) clearly says its **free Demo/keyless** plan **does not include commercial rights**. Paid commercial display and custom redistribution are different licensing levels.

[Coin Metrics official documentation](https://github.com/coinmetrics/docs-website/blob/master/api.md) describes the free Community API as **non-commercial**; [product docs](https://gitbook-docs.coinmetrics.io/packages/coin-metrics-community-data) also identify community reference-rate **history limits**. Neither is a cleared commercial backfill for BTC/USD. Public-chain observables (blocks, transactions, mining difficulty) might support a separate independently researched network-activity signal, but they are **not a USD exchange rate** and do not preserve the old Score meaning.

### E. Gold: annual CC0 does not imply weekly CME futures

The [USGS 2026 Mineral Commodity Summaries release](https://www.usgs.gov/data/mineral-commodity-summaries-2026-data-release) is explicitly **CC0** for its released statistics. Those **annual** mineral/price/production summaries are useful for an educational gold-structure page, not a Friday mark of `GC=F` gold futures.

The World Bank [Pink Sheet](https://www.worldbank.org/en/research/commodity-markets) provides **monthly and annual** commodity prices; its [general data licensing](https://datacatalog.worldbank.org/public-licenses) commonly uses **CC BY 4.0**, but specifically sourced gold quotations may carry underlying rights not addressed by a blanket license assumption. The month-end publication lag and difference between London benchmark quotations and front-month CME futures independently disqualify weekly parity.

### F. Direct Treasury 2Y/10Y: promising but release and vintage checks matter

Treasury's [daily par-yield XML guide](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed) supports year/month selection and all-history pagination. Its [developer notice](https://home.treasury.gov/developer-notice-xml-changes) requires page increments until an empty feed for `all` queries; the existing [synthetic-only parser](../scripts/treasury_par_yield_xml_candidate.py) correctly rejects all-history requests and explicitly requires a year/month selection.

Treasury's [2025 official methodology](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology) explains that par yields are interpolated from indicative NY Fed market quotes, and rates are **usually published by 6:00 p.m. Eastern time each trading day**, sometimes later. This matters because the existing Score's Friday ~22:00 UTC cutoff is **approximately the same local clock time during U.S. daylight saving**, leaving no assured Friday final observation even if direct Treasury transport is approved. The indicative underlying market quotes also deserve an explicit source-rights/republisher review.

The [Treasury FAQ](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/interest-rates-frequently-asked-questions) describes Treasury CMTs as fixed-maturity points derived from the par curve and identifies H.15 as a separate publication route. Exact FRED DGS2/DGS10 historical equivalence, **release-as-of vintages, 2021 methodology transitions, missing days, revisions, holidays and week selection** remain untested.

## 3. A distinctly named 4-signal public-source research alternative


**Working title only:** Federal Public-Source Regime Study. It is **NOT** the original USD Impact Score, is not commercially/publicly approved, and has no final signal normalization, sign, weight, threshold or backtest.


| Proposed research signal | Official publisher | Economic meaning | Why it cannot inherit the old weight/sign |
|---|---|---|---|
| Broad dollar | Federal Reserve Board H.10 | U.S. trade-weighted FX strength | Different basket/weighting and a Monday release lag |
| Weekly commercial crude inventories | EIA WPSR | Physical oil balance/inventory pressure | Not WTI futures; price and inventories may move in opposite or same directions across regimes |
| Nominal Treasury 2Y par yield | U.S. Treasury | Shorter policy-sensitive nominal rates | As-of release and direct source parity not yet confirmed |
| Nominal Treasury 10Y par yield | U.S. Treasury | Long-term nominal rates | Highly correlated with 2Y; weights/risk of double-counting require new analysis |

This is a **candidate research design**, not a final recommendation to launch. The required technical design needs **first-publication timestamps, historical as-of snapshots only where legally permitted, holiday schedules, revision handling, causal/non-look-ahead cross-asset definitions, a newly approved score scale and name, and distinct educational/compliance disclosures**. Never label it an eight-driver Score or extend the legacy 617-week chart by splicing rewritten sources.

A minimal publication cadence may need to be **after Wednesday** to incorporate the prior Friday's EIA stock data, while H.10 from Monday becomes available earlier in the same following week. This would be a **different weekly Score release schedule** and must be separately approved.

## 4. Evidence classification by use

| Requested operation | Why separate permission is needed | Current state |
|---|---|---|
| Read source observations internally | Transport API/data licensor terms versus originator terms | **HOLD** |
| In-memory transient computation | Provider and source copyright/publication scope, possible required citation | **HOLD**, aside from previously documented conditional FRED use under terms/disposal |
| Keep historic original observations | Storage, archive, metadata, source contract and duration | **HOLD** |
| Keep derived z-scores/normalization moments | Commercial derived product and possible reconstructibility | **HOLD** |
| Keep hashes, code versions, source metadata | Even hash-only receipts need provenance and counsel classification | **HOLD for real provider evidence** |
| Publish date + aggregate + regime | Could still qualify as derived-data distribution | **HOLD** |
| Publish machine-readable components/history or resale | Higher redistribution risk | **HOLD** |
| Remove current files or purge old archives/caches | Preservation, old Git objects, distributor copies, user research consumers and legal-safe rollback | **HOLD pending rights/preservation decision** |

**Licensing analysis is not a substitute for a legal opinion.** The project has no new paid data-license budget and must not purchase a contract or initiate a provider request automatically. S&P existing case #01036004 and the Cboe no-fee request are pending; do not reopen either.

## 5. Next executable phase without market-data retrieval

1. **Counsel/source rights worksheet:** for each candidate, record source owner, versioned terms, whether third-party prices are embedded, exact allowed internal/public/retention operations, attribution, automated access and revocation, and scope of any source-permitted historical preservation. Obtain affirmative written interpretation where needed.
2. **Synthetic-first availability validator:** model Friday reference date versus Monday H.10, Wednesday EIA and Treasury ~18:00 ET availability, including holiday delays; use invented 2099 dates and deny availability if actual first-seen time is absent. No real data access.
3. **Alternative methodology design approval:** evaluate separate 4-signal weighting/sign/threshold, lead-lag, stress sensitivity and how the site would distinguish a public macro research index from the locked eight-driver Score. Do **not** reuse old weights or historical chart.
4. **New-source access and data-parity approval:** only after source rights are clear, separately authorize any real Board/EIA/Treasury fetch; then test data availability, revisions, H.15 parity, cadence and backtest stability in a legally permitted environment. A synthetic pass is not a license.
5. **Historical remediation:** counsel-approved preservation of old Git/Pages/CI/CDN and archive provenance, consumer map, public/private boundary and legally safe rollback before any deletion or source-based restart.
6. **Protected release:** exact-head CI, member auth, anonymous endpoint testing, post-release no-leak monitoring, and separate owner Production approval. Until then `governance/score-publication-rights-gate.json` remains **hold**.

## 6. Risk register and hard NO-GO criteria

| Risk | Severity | No-go trigger |
|---|---|---|
| Paid index/derivative licensing (ICE/S&P/Cboe/CME) | Critical | Any original driver, internal calculation or aggregate publication not affirmatively licensed |
| Third-party price data through government republisher (EIA Refinitiv) | Critical | Relying on general EIA public-domain words as sublicense for privately acquired WTI spot quotations |
| Free crypto API commercial-rights confusion | High | Selecting CoinGecko Demo or Coin Metrics Community for a paid/commercial product |
| Government stress index embedded VIX/DXY/Refinitiv data | High | Calling OFR FSI or NFCI clear without underlying-source review |
| Misleading Score continuity and legacy history | Critical | Claiming unchanged Score/617-week performance while replacing futures/indices with government macro inputs |
| Forward-looking data leak or false historical as-of | Critical | Using Monday/Wednesday published values for earlier Friday without explicit lag/revision model |
| Source retirement and transport drift | High | Depending on Board DDP retired UI or scraping without approved access, monitoring and contract |
| Unlawful retention or destructive cleanup | Critical | Creating new real-data backup without retention rights, or purging Git/Pages before lawful preservation |
| Site member entitlements and source-gate bypass | High | Any unreviewed public root URLs, stale previews, workflow/manual triggers or consumer incompatibilities |
| Unauthorized spend or provider outreach | High | Paid plan, subscription or duplicate supplier case without owner approval |

**Decision today: the old 8-driver pipeline is a NO-GO; a 4-signal government-source study is a conditional research direction, not an approved implementation.**

## 7. Primary evidence checklist

All the cited links above are **publisher-owned documentation, original government policies, or the named vendor's own licensing pages**, except Coin Metrics' official documentation repository (maintained by Coin Metrics). No market observation, licensed history or provider-delivered CSV/JSON value is reproduced in this research artifact. Source pages can change; recheck dated terms and permissions before any new real-data or Production authorization.

- [Federal Reserve Board H.10](https://www.federalreserve.gov/releases/h10/), [Board website rights](https://www.federalreserve.gov/disclaimer.htm), [trade-weighted methodology](https://www.federalreserve.gov/econres/notes/feds-notes/revisions-to-the-federal-reserve-dollar-indexes-20190115.html)
- [EIA general reuse](https://www.eia.gov/about/copyrights_reuse.php), [Refinitiv-origin historical oil-price assessment](https://www.eia.gov/analysis/handbook/pdf/STEO_Crude_Oil_Price.pdf), [WPSR stocks](https://www.eia.gov/dnav/pet/PET_STOC_WSTK_A_EPC0_SAX_MBBL_W.htm) and [schedule](https://www.eia.gov/petroleum/supply/weekly/schedule.php)
- [Treasury XML](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed), [developer paging notice](https://home.treasury.gov/developer-notice-xml-changes), [2025 yield methodology](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology)
- [S&P terms](https://www.spglobal.com/en/terms-of-use), [CME licensing](https://www.cmegroup.com/market-data/license-data.html), [FRED terms](https://fred.stlouisfed.org/legal/terms/)
- [OFR stress index](https://www.financialresearch.gov/financial-stress-index/), [OFR underlying indicators](https://dmtenrspjuuhr.cloudfront.net/financial-stress-index/files/indicators/index.html), [Chicago NFCI](https://www.chicagofed.org/research/data/nfci/current-data)
- [CoinGecko free vs commercial licensing](https://support.coingecko.com/articles/1043089972-what-are-the-differences-between-commercial-and-custom-licenses), [Coin Metrics official community documentation](https://github.com/coinmetrics/docs-website/blob/master/api.md)
- [USGS CC0 minerals release](https://www.usgs.gov/data/mineral-commodity-summaries-2026-data-release), [World Bank Pink Sheet](https://www.worldbank.org/en/research/commodity-markets), [World Bank data licensing](https://datacatalog.worldbank.org/public-licenses), [BEA corporate profits](https://www.bea.gov/data/income-saving/corporate-profits)

**No publication, source switch, raw observations, user data, new credentials, subscriptions, public historical artifacts or Production infrastructure were created or changed by this Phase A research.**
