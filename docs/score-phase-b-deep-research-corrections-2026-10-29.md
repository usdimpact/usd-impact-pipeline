# Phase B — Deep Research evidence corrections (2026-10-29)

**State:** DOCUMENTATION ONLY / SYNTHETIC RESEARCH HOLD. **Not a license decision or authority to ingest or publish data.** This note supplements [Phase B rights and as-of design](score-four-source-phase-b-rights-asof-design-2026-10-29.md) and its [fail-closed manifest](../governance/score-public-source-phase-b-design-2026-10-29.json). Governing issues: [#155](https://github.com/usdimpact/usd-impact-pipeline/issues/155) (existing eight-driver Score) and [#282](https://github.com/usdimpact/usd-impact-pipeline/issues/282) (Treasury/FRED retention).

## Evidence incorporated, without any rights grant

| Reference | What it supports | What remains unproved |
|---|---|---|
| [Data.gov Treasury daily yield curve dataset](https://catalog.data.gov/dataset/interest-rate-statistics-daily-treasury-yield-curve-rates) | The nominal daily yield-curve dataset (015-DO-020) catalog displays **CC0 1.0** (catalog metadata last modified 2025-02-11). This strengthens catalog-level licensing evidence for Treasury 2Y/10Y. | Exact-series and upstream indicative quotation rights, transport-specific terms, commercial storage/backup/retention, permitted calculations and public derived outputs; owner/counsel sign-off. A catalog license is **not** an approval toggle. |
| [Federal Reserve DDP transition notice](https://www.federalreserve.gov/data/data-download-fred-information.htm) and [H.10 package page](https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H10) | Board says historical XML downloads remain available on individual statistical-release pages when Build Your Package is retired in the week of **November 9, 2026**. | Continuity of specific machine clients and series, exact H.10 rights or revised first-published vintages; FRED may not silently become a replacement transport. |
| [Treasury FAQs](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/interest-rates-frequently-asked-questions), [methodology](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology) | Treasury generates its CMT par yields, using indicative market bids. The Board's H.15 republishes Treasury CMT; FRED is operated by the St. Louis Fed, not the Board. | Equality of a given source value, timestamp, correction or historical as-published vintage must be established by proof, not assumed. |
| [EIA reuse rules](https://www.eia.gov/about/copyrights_reuse.php), [WPSR](https://www.eia.gov/petroleum/supply/weekly/) | Government-produced WPSR crude-stock survey evidence has a plausible reuse basis, with third-party exceptions. | Exact inventory series/definition, rights in all fields and transports, correction history, durable retention and public derivative rights. **Do not transfer this permission to Refinitiv WTI/Brent spot prices.** |

## Rejected execution assumptions

1. **Unsafe `approved: true` examples:** Reject. All four `sources[].cleared` flags remain `false`; all Phase B `decision.approve_*` fields remain `false`; no supplier has granted final publication or retention authorization.
2. **Treasury 17:00 ET polling:** Reject. Treasury says daily nominal par data are usually available **by 18:00 Eastern, sometimes later**. That statement does not prove a particular first-publication time; use an actual publisher publication/version receipt and first-seen evidence. At 18:00 ET, UTC is 22:00 in daylight time and 23:00 in standard time.
3. **Treasury versus H.15:** Reject generic equal/not-equal assertions. Treasury's own curve and the Board's H.15 republication are related, but direct Treasury and FRED-delivered H.15 values **and vintages** are not yet compared and must be independently evidenced.
4. **Future approvals marked done:** Reject. Legal, source owner, methodology, four-signal product decision, live retrieval, retention, publication and Production remain pending.
5. **More Supabase synthetic writes:** Reject as redundant without a separately approved purpose. Existing offline synthetic validator and tests already cover revision, late release, as-of, timezone and same-curve Treasury receipts.
6. **One giant provider-rights gate:** Reject. ICE, S&P, Cboe, CME, Yahoo and FRED-related dependencies remain applicable to the *legacy eight-driver Score* where those inputs are used. A truly separate federal four-signal study has **its own** exact-series/source/transport gate; it does not inherit legacy licenses or approvals, and must not read legacy proprietary observations.
7. **Correction-free assumptions:** Reject. H.10 has a documented August 2026 correction, and EIA corrections cannot be ruled out without evidence. Preserve first-publication and revised source versions rather than using retrospective latest values as historically known.

## Product-specific decision ledger

| Product | Research status | What is explicitly NOT authorized |
|---|---|---|
| Existing eight-driver USD Impact Score v2 | #155 public rights/redistribution **HOLD**, separate from Phase B | New license assumptions, source substitution, change of weights or formula, alteration/purge of archives, Production release |
| Proposed four-signal federal macro study | **Synthetic-only design review**; independent model, not Score replacement | Real H.10/WPSR/Treasury downloads, FRED transport fallback, rights grants, historical backtest, storage/backup of real vintages, public aggregate or member output, methodology and weights, deployment |

## Next gated decisions (not yet approved)

- Review Treasury 2Y/10Y exact catalog-series mapping and publication-source transport, separating CC0 metadata from upstream indicative quotation and derivative/reuse restrictions.
- Determine the native H.10 series XML path and lifecycle *in documentation only*; do not download observations or infer future API uptime.
- Independently record for each of the four signals: exact owner, direct publisher transport, third-party conditions, commercial processing, log/cache/backup retention, public aggregate/history, corrections/versioning, and citation requirements. Default any missing decision to **DENY**.
- Obtain a distinct owner methodology decision if the alternative model is desired. Only after specific rights/retention sign-off request a *new* authorization for a minimal real-data timing and parity test.
- Preserve protected CI, no-lookahead synthetic checks and distinct Score rights gates. Verify before any later merge/publication.

**No work authorized by this correction:** provider data retrieval, outbound contact, paid agreements, Supabase writes or schema changes, Vercel/Render/Resend/Lovable/Cloudflare mutation, member or payment changes, public Score edits, or any Production deployment.
