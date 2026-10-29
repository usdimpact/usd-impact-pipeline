# Score v2 — successor release readiness and historical BTC provenance blocker

**Recorded:** October 29, 2026. **Status:** DRAFT ONLY / NO RUNTIME / NO RELEASE.  
**Control:** [Issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155), [Issue #282](https://github.com/usdimpact/usd-impact-pipeline/issues/282).  
**Source of truth for the inactive successor packet:** [JSON readiness matrix](../governance/score-v2-successor-rights-readiness-2026-10-29.json).

This document is a technical and documentary decision checklist, not provider permission, legal advice, evidence that earlier publication was unlawful, an executable license, a production unlock, a provider-fetch authorization or an instruction to delete any historical data. The binding legacy v1 policy remains on HOLD; the [merged v1 lock](../scripts/score_publication_rights_gate.py) refuses a superficially approved v1 policy.

## 1. Current Score, source and permission requirements are separate

The actual 8-input production mapping was checked by reading *source-code constants* (no module import, observation access or numeric provider history). It must not change as a side effect of governance research:

| Frozen Score driver | Current retrieval | Original publisher/source right to resolve | Frozen model intent |
|---|---|---|---|
| DXY | Yahoo/yfinance DX-Y.NYB | ICE USDX and licensed Yahoo route | ICE dollar index, not Board H.10 broad dollar |
| WTI | Yahoo/yfinance CL=F | CME contracts and Yahoo delivery | Futures, not EIA spot or surveyed inventory |
| SPX | Yahoo/yfinance ^GSPC | S&P DJI and Yahoo delivery | S&P 500, not quarterly BEA profits |
| VIX | Yahoo/yfinance ^VIX | Cboe and Yahoo delivery | VIX, not a government stress proxy |
| BTC | Yahoo/yfinance BTC-USD | **Original historical OHLC provider not independently proved**; Yahoo delivery conditions still apply | Bitcoin/USD historical observed price |
| GOLD | Yahoo/yfinance GC=F | CME contracts and Yahoo delivery | Gold futures, not annual USGS output |
| UST_2Y | FRED DGS2 | FRED transport; underlying U.S. Treasury/Board H.15 published-yield provenance | Two-year Treasury constant maturity |
| UST_10Y | FRED DGS10 | FRED transport; underlying U.S. Treasury/Board H.15 published-yield provenance | Ten-year Treasury constant maturity |

The seven previously tracked vendor/source relationships were a useful initial inventory, not proof of full originator coverage. This draft explicitly adds an **eighth unresolved rights-analysis relationship** for the original Yahoo BTC-USD historical price observations. It does **not** assert that BTC has an eighth newly identified or contracted supplier, nor does it equate the proposal to eight independent direct providers. Treasury/H.15 appears as **underlying lineage**, not a claim that the Score currently fetches a direct Treasury feed. Each relationship is tracked with 16 separate **false** permission gates (8 x 16 = 128 currently denied).

## 2. New primary-source BTC evidence — narrow applicability

Read-only public-source terms review (no BTC prices or market histories fetched):
- [Yahoo Finance help — exchanges and data providers](https://help.yahoo.com/kb/SLN2310.html) says Yahoo Finance information must not be redistributed and lists market/exchange delivery relationships. Yahoo market access is NOT an implicit downstream license.
- [CoinMarketCap's Yahoo Finance integration case study](https://coinmarketcap.com/academy/article/how-yahoo-finance-powers-its-crypto-data-with-coinmarketcap-api) documents a Yahoo/CoinMarketCap integration that has included crypto market information since the 2019 partnership. This is useful evidence of an **upstream relationship**, but is NOT proof that the historical OHLC values retrieved by yfinance for BTC-USD and used by the frozen Score pipeline came from CoinMarketCap for every requested date.
- [CoinMarketCap general Terms](https://coinmarketcap.com/terms/) contain personal-use, noncommercial and data extraction/derivative/redistribution restrictions for the general site service.
- CoinMarketCap's [API plan descriptions](https://coinmarketcap.com/api/pricing/) and [Commercial API Agreement](https://pro.coinmarketcap.com/user-agreement-commercial/) separately describe commercial-API permissions and limits, including redistribution restrictions. The existence of a commercial Basic plan **does not license the current Yahoo historical OHLC ingestion**, does not establish exact-series historical parity, and does not automatically cover a commercial educational membership or downloadable public research archives.

**Unanswered BTC decision:** identify the original provider(s) and specific historical close/adjustment/venue/aggregation methodology actually delivered by Yahoo for BTC-USD, trace which license controls commercial internal computation, historical retention and external aggregate publication, and document authorized delivery/API terms. If the upstream supplier cannot be proved, the source-specific rights decision remains unresolved and no legacy Score release may be authorized.

This is an important new research target, **not** an authorization to contact CoinMarketCap, change the price feed, create a CMC account, pay fees or replay historical Yahoo observations.

## 3. Provider follow-up now requires an owner scheduling action

The October 29 read-only existing-mailbox review found that **S&P Dow Jones Indices' regional client-coverage team asked for availability next week**, after the earlier case escalation. That is a *commercial discussion request*, not a license, price quote, approved aggregate output or counsel opinion. The case exists; **do not open a duplicate request**.

The meeting requires owner participation or explicit scheduling approval. Do not put private correspondence, contact details or billing-person identities into this public GitHub document. The owner can offer a small number of time slots in the same CET timezone as Frankfurt in early November. Before committing to any fees, contracts or private identity disclosure, separately obtain owner approval.

Suggested short call agenda, with written follow-up requested afterward:
1. Confirm the exact contract/licensor for commercial non-display **S&P 500 index level** ingestion via current Yahoo/yfinance delivery; does a direct licensed feed change the answer?
2. Is a **multi-driver, non-reconstructible educational weekly Score/regime**, with dates and aggregate history but no component S&P inputs, a licensed derived-data product? Are machine-readable JSON/CSV, web chart and subscriber output treated differently?
3. What internal historical source values, normalizing moments, validation logs, hashes, backups, audit receipts and vintage histories may legally be retained, and for how long?
4. What rights and remediations apply to prior component-derived public artifacts and dated archive copies? What licensing/attribution, restrictions, disclosure terms or fees would govern?
5. Is there a **no-additional-license or no-fee** permitted scope for the exact proposed narrow use? If not, please provide the written licensing requirements rather than assuming permission.
6. Can the provider reply in writing by specific input, output and intended commercial channel? Record the written terms in a private appropriate evidence store only after permission for that storage is reviewed.

This dossier records only **provider_requested_call**, no user-confirmed slot, no reply sent, no calendar event created and no affirmative rights grant.

## 4. Public artifacts and historical persistence are independent approval tracks

The dated [current-tree exposure inventory](../governance/score-current-tree-exposure-inventory-2026-10-29.json) has **54 current-tree Class C files** and **27 dated archive directories**. These are static Git path counts, not 54 verified reachable endpoints or 54 infringements. Other public research artifacts are in A, B, D, E and F classes; treating only raw HTTP payloads as protected misses provider-derived levels, normalization moments, z-scores, contributions and revision diagnostics.

A separate prior metadata study recorded 1,921 Cloudflare Pages **deployment records**, not 1,921 proven live exposures. Prior revisions, preview Access, production Pages hosts, CDN/edge caches, Git forks/clones, Actions artifacts/caches/logs, external backups and third-party research consumers need independent *lawful preservation and access* decisions. A Git branch is not an offsite archival solution.

Never delete or rewrite historical Git/Pages data or copy real provider records into the already demonstrated synthetic-only Development storage bucket merely because the aggregate-safe transformer passes offline tests. A public aggregate-only schema is *technically narrower*, not automatically license-safe.

## 5. Private calculation and public publication consumer separation

Before any future rights-authorized public file replacement:
1. Keep full component-derived calculation and research validation outside the public worktree **only after** confirming lawful access, retention/disposal and private evidence storage rules.
2. Validate existing strict calculation evidence privately, where approved.
3. Generate versioned aggregate-safe Score and research views and prove absence of per-driver level/z/contribution/provenance fields.
4. Migrate predictive, v3 shadow, vintage/robustness, independent reproduction, weekly health, methodology public links, archive URL helpers and authenticated member readers to correctly scoped public/private contracts.
5. Reword replication claims accurately; an aggregate-only public output does not provide full independent per-driver reproduction.
6. Preserve current artifact provenance under counsel's lawful historical treatment plan, not destructive Git/CDN purge.
7. Run exact-head CI, non-production public and member boundary tests, Cloudflare route/preview sampling, then obtain distinct explicit owner Production approval.

The accompanying packet contains seven preservation surfaces, seven consumer migrations, A–F classes, 12 separate external authority gates and 13 high-risk action flags. **Every grant is false.** The 128 per-source permission flags are also false.

## 6. How the validator can and cannot be used

Run as local/offline PR-quality guard:

    python -m scripts.validate_score_v2_successor_rights_readiness
    python -m unittest tests.test_score_v2_successor_rights_readiness -v

The validator checks local JSON/governance documents and frozen Score source constants through AST only. The tests mutate temporary fabricated copies to demonstrate hard failures for missing BTC origin, fake CMC/S&P rights, premature public aggregation, historical cleanup, input drift, source substitution, missing consumers and S&P meeting-as-license confusion.

It will deliberately **reject** any positive rights/production flags. Therefore it is NOT a future v2 release engine or provider-rights approval mechanism; that requires a separate versioned, protected, reviewed technical/legal design and explicit owner authorization. The current v1 runtime gate and all live workflows remain untouched by this packet.

## Completion boundary and next decisions

**Completed without external approval:** preserve historical/source context, identify and block BTC provenance ambiguity, classify fields, pin the frozen inputs, build the inactive successor packet and test fail-closed behavior.

**Owner/provider/counsel needed next:** S&P meeting slot, authoritative source/delivery rights (including BTC OHLC), permitted retention or disposal and old archives, approved A–F public schema, private evidence policy, consumer migration, and a separate Production release decision. No automated outreach, paid license, market observation retrieval, public change or production deployment is permitted by this research PR.
