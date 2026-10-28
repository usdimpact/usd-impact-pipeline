# Score v2 provider-rights question pack — 2026-10-28

Status: **NO-SEND REVIEW TEMPLATE**.

Purpose: obtain written, use-case-specific answers without overstating the current product or asking providers to opine on another provider's rights.

Entity/product context to provide in outreach:

- operator: KELA LEADS S.R.L. / USD Impact;
- product: educational USD regime indicator;
- cadence: weekly, non-real-time;
- no order routing, execution or market-data terminal;
- public methodology plus public and/or member educational pages;
- current pipeline uses weekly last-available market levels to compute standardized component values and one aggregate Score/regime;
- engineering is willing to suppress component values publicly if provider rights do not cover them.

Do not claim permission based on Yahoo/yfinance access, delayed data, transformation, attribution or member gating.

## Common questions for every relevant data owner

Ask for written confirmation of which of the following are permitted and under what license/fees:

1. storing the provider-derived observation internally for calculation/audit;
2. showing the latest weekly source level on a public educational website;
3. showing the latest weekly source level only to authenticated paying members;
4. publishing a standardized transformation of the level (for example a z-score);
5. publishing a weighted contribution derived from that z-score;
6. publishing historical transformed values without the underlying raw daily history;
7. publishing only an aggregate multi-asset Score/regime while withholding the provider-specific level and transformation;
8. keeping private reproduction/audit records accessible only to authorized operators/CI;
9. required attribution, trademark language, delayed-data notices or disclaimers;
10. whether public vs member-only delivery changes the applicable license;
11. whether a separate derived-data/index license is required;
12. whether the provider can give a written no-fee educational permission for this narrow weekly use.

Ask the provider to identify the exact agreement/product name that would govern the permitted use.

## ICE — DXY / U.S. Dollar Index

Current Score transport uses Yahoo ticker `DX-Y.NYB`, but the underlying dollar index is an ICE-controlled index product.

Existing USD Impact inquiry history exists for ICE index licensing, but no reply was found in connected Gmail.

Specific questions:

- Does ICE permit a weekly educational display of the U.S. Dollar Index level obtained through an authorized downstream source?
- Is a z-score or weighted contribution calculated from DXY considered "derived data", an index-based derived work, or redistribution requiring an ICE license?
- May an aggregate multi-asset Score be published if DXY's level/z-score/contribution are withheld?
- What attribution/trademark notice is required when naming DXY in methodology?
- Does member-only access alter the license class?

Existing inquiry address on record: `ICEIndices@ice.com`.

## Cboe — VIX

Current Score transport uses Yahoo ticker `^VIX`; underlying index rights are Cboe's.

USD Impact previously closed the paid-license inquiry because there was no current budget and stated it would not republish restricted data without permission.

Specific questions:

- Is a once-weekly VIX level public display covered by any existing public-data allowance, or does external redistribution require a Cboe agreement?
- Are standardized z-scores/contributions based on VIX treated as derived index data requiring a license?
- Can an aggregate Score be published when no VIX-specific numeric value is exposed?
- What attribution/trademark requirements apply to methodology references to VIX?

Official index-data contact currently identified: `marketdata@cboe.com`.

## S&P Dow Jones Indices — S&P 500

Current Score transport uses Yahoo ticker `^GSPC`.

Specific questions:

- Does publication of a weekly S&P 500 index level require an S&P DJI redistribution/display license?
- Are z-scores, weighted contributions or historical transformed values "derived data" under S&P DJI terms?
- Is an aggregate multi-asset Score permissible without exposing S&P 500-specific numeric values?
- What attribution/trademark wording is required for public methodology?
- Is member-only educational delivery treated differently?

Official index-services contact currently identified: `index_services@spglobal.com`.

## CME Group — WTI and Gold futures

Current Score transport uses Yahoo tickers `CL=F` and `GC=F`, corresponding to CME Group markets.

Do not characterize the Yahoo value as a settlement unless the source contract explicitly establishes that field.

Specific questions:

- What license applies to a weekly last-available WTI/Gold futures reference level sourced via an authorized downstream distributor?
- Do normalized transformations/z-scores or weighted contributions count as derived data under CME market-data policy?
- Is publishing only an aggregate Score/regime permissible without exposing contract-specific numeric values?
- Are there different requirements for public vs authenticated/member educational use?
- What market/source attribution is required?

Official contacts currently identified:
- `marketdataemea@cmegroup.com`
- `CMEDataSales@cmegroup.com`

## Yahoo / Yahoo Finance transport

Yahoo/yfinance is a transport/source layer for several current Score observations; it does not resolve underlying index/exchange rights.

Specific questions:

- Is KELA LEADS S.R.L. permitted to use Yahoo Finance historical data programmatically for a commercial educational/subscription service?
- If permitted, may weekly observations or transformations be redistributed publicly or to members?
- Does Yahoo offer a commercial license/API or approved data partner for this use?
- Which upstream data-owner permissions remain the customer's responsibility?
- Is internal calculation with public output limited to an aggregate derived Score permitted under Yahoo terms?

Do not treat an answer from Yahoo as permission from ICE, Cboe, S&P DJI or CME unless the answer explicitly grants/sublicenses those rights.

## Bitcoin / BTC-USD

Current Score uses Yahoo `BTC-USD`.

Ask Yahoo which underlying source supplies this series and what commercial redistribution/derived-use rights apply. If Yahoo cannot sublicense those rights, identify the actual data owner/venue before public component display.

## Counsel decision format

For each component, counsel/provider review should record:

- source/underlying owner;
- transport provider;
- exact permitted public fields;
- exact permitted member-only fields;
- permitted internal/private evidence fields;
- derived-data treatment;
- attribution/trademark requirements;
- retention restrictions;
- license/agreement name and date;
- fee/tier if applicable;
- written evidence link/file;
- final disposition: `PUBLIC_OK`, `MEMBER_ONLY`, `AGGREGATE_ONLY`, or `HOLD`.

Until a component has an evidence-backed disposition, engineering should default to `AGGREGATE_ONLY` for public redesign planning and `HOLD` for any expansion of component-level public data.
