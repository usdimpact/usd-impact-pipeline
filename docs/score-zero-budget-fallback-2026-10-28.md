# Score zero-budget fallback matrix — original 2026-10-28 / reconciled 2026-11-07
## Operational update — 2026-11-07 (supersedes the historical October 28 recommendations)

**Decision: original eight-driver USD Impact Score v2 remains RIGHTS HOLD. No exact, no-fee publication path is authorized.** The 2026-10-29 written S&P DJI response requires a paid license for the described commercial eight-driver Score use, including the narrower non-reconstructible public aggregate. The project has USD 0 authorized additional market-data licensing. Source details and private correspondence stay in their established evidence locations; see the category-level disposition `governance/score-spdji-provider-disposition-2026-10-30.json` and Issue #155.

**Do not create a competing replacement Score from free-looking series.** The existing separate, synthetic-only Macro Context Panel under Issue #313 already explores three *descriptive* dials from four proposed original-publisher signals: H.10 nominal broad-dollar direction (not ICE DXY); EIA crude inventory build/draw (not WTI futures); and same-vintage direct Treasury nominal 10Y–2Y slope level/change (not real yields). It is not an eight-factor Score, has no comparable 617-week history, no weighting, no composite score, no approved public name, and no authority to fetch or publish real data. Source permission flags remain 56/56 denied; external authority gates remain 14/14 false.

**FRED is not the zero-budget retention fallback.** The 2026-10-29 FRED response and Issue #282 leave storage, caching, archives, logs and retained derivations unresolved. Direct Treasury/H.15 transport needs its own field-level, rights and revision decision; no silent FRED-to-Treasury switch.

**Time-sensitive transport constraint:** the Federal Reserve announced that the DDP 'Build Your Package' feature is planned for removal during the week of **November 9, 2026**. This is a design-review dependency only, not a reason to query live provider series or substitute FRED. Preserve the H.10 2019 methodology/base break, EIA survey/lease-stock distinctions, direct Treasury 2Y/10Y same-snapshot provenance, reference versus observed publication time and genuine first-seen receipts. See the existing Panel Issue #313 decision packet.

### Next safe transition gates — sequential, independent approvals

1. **Contain the existing product:** retain the Score engine, October 23 last committed Weekly input, canonical Score rights HOLD, public artifact/history inventories and prior archives unchanged. Do not trigger Score workflows, relabel existing history as current, purge evidence or change live endpoints.
2. **Review exact series and rights:** resolve all four proposed Panel source-owner/transport lineages, third-party exceptions, commercial calculations, retention/backups, derived descriptive labels, archives, attribution, automated access, AI use and permitted audience. Keep each unknown as DENY. No provider data GET/HEAD before an explicit source-level approval.
3. **Resolve economic and editorial identity:** obtain separate owner sign-off for three dials/four labels, latency and limitations; reject DXY/WTI-price/Score-v2 equivalence, implied backtest or retroactive continuity; decide the distinct public name and whether it should exist alongside the current Weekly Brief.
4. **Design a distinct versioned public contract:** explicitly limit fields and historical representation; prove non-leakage, fail-closed first-publication/version/first-seen/as-of selection, and separate protected research and evidence storage. Use invented year-2099-plus fixtures only in this stage.
5. **Prepare website disclosure separately:** propose an independent, scoped site Draft labeling legacy Score as historical/paused with last verified date; do not merge or change the currently working site in this review. Do not mislabel the separately source-verified Macro Weekly as a Score edition.
6. **Only after signed source/counsel and owner decisions:** separately authorize narrowly scoped real-data access, Development/non-Production review and public release; require exact-head protected CI, privacy/security/financial-language review, READY Preview, production approval, matched deploy and independently fetched live public proof.

**Non-actions in this Draft:** no source/network observation, no market-data purchase, no new model, no scoring/reweighting or data replay, no provider outreach, no workflows/Pages/Workers/Vercel/Supabase/Render edits, no live site UI change, no historical deletion, no gate activation or public publication. The updated fallback validator is a read-only assertion of the current HOLD, not a new release controller.

**Canonical references:** [Score rights #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155), [FRED retention #282](https://github.com/usdimpact/usd-impact-pipeline/issues/282), [independent panel #313](https://github.com/usdimpact/usd-impact-pipeline/issues/313), [UI-32 separate research #333](https://github.com/usdimpact/usd-impact-pipeline/issues/333), and [Federal Reserve DDP transition notice](https://www.federalreserve.gov/data/data-download-fred-information.htm).

---

## Historical 2026-10-28 fallback assessment (retained for audit; superseded where inconsistent)

Status: **review-only / zero-budget planning / issue #155 HOLD remains active**.

## Conclusion

There is currently **no confirmed zero-budget path that preserves Score v2 exactly**.

Some free official data exist, but they are not semantically equivalent to the current inputs:

- **DXY:** the Federal Reserve publishes a free broad dollar index, but it is not ICE DXY.
- **WTI:** EIA publishes free WTI Cushing spot prices, but spot is not the current futures continuation series.
- **SPX:** FRED carries S&P 500 data, but FRED explicitly marks the series copyrighted and pre-approval required. Access through FRED does not resolve USD Impact's commercial/derived-use rights.
- **VIX:** FRED carries VIX, but identifies Cboe copyright and reprint permission. FRED access does not independently grant USD Impact derived/public-use rights.
- **BTC:** no authoritative zero-cost source has yet been identified that both matches the historical Yahoo BTC-USD convention and has confirmed commercial/derived-use rights.
- **Gold:** no authoritative zero-cost source has yet been identified that preserves COMEX continuous/front-contract semantics with confirmed commercial/derived-use rights.
- **DGS2/DGS10:** retain the current FRED path if FRED confirms acceptable use.

## Engineering implication

Do **not** silently substitute free data into Score v2.

Any change such as:
- DXY -> Fed broad dollar index;
- CL futures -> EIA WTI spot;
- GC futures -> spot gold;
- VIX -> another volatility proxy;
- S&P 500 -> ETF/equity proxy;
- Yahoo BTC-USD -> a different crypto benchmark;

changes the economic meaning of at least one driver and therefore requires a separately reviewed methodology version.

## Zero-budget decision tree

1. Provider confirms no-cost permitted use for the current input:
   - keep candidate alive;
   - document scope;
   - request separate Development parity authorization.

2. Provider requires paid licensing:
   - mark candidate unavailable under the current project constraint;
   - do not enter procurement.

3. No exact free replacement exists:
   - preserve #155 HOLD;
   - prepare a v2.1 methodology option only;
   - do not deploy or change Production without explicit methodology/research approval.

## Current recommendation

Wait for S&P/Cboe/CME/FRED replies while keeping the Friday publication gate closed.

If paid licensing is required across the relevant proprietary inputs, the next rational project is not more licensing work; it is a controlled **Score v2.1 zero-budget methodology design** using free official inputs, with explicit backtest/research review before any Production consideration.

No methodology change, real-data rehearsal, public replacement, or Production authorization is granted by this document.
