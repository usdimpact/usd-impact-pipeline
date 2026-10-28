# Score rights provider contact routing — 2026-10-28

Status: **outreach-ready / no contact sent / HOLD remains active**.

This document maps the unresolved Score v2 rights questions to official public contact channels. It does not authorize outreach, does not record any provider approval, and does not change the engineering or Production state.

## S&P Dow Jones Indices — S&P 500-derived use

Official public contact:
- index_services@spglobal.com
- S&P DJI contact page: https://www.spglobal.com/spdji/en/contact-us/

Suggested subject:
**USD Impact Score — request for data/derived-output licensing clarification**

Questions to ask:
1. Does commercial internal use of S&P 500 observations in the USD Impact Score require a specific license under the applicable S&P DJI terms?
2. Does publication of a non-reversible aggregate Score/regime derived partly from S&P 500 observations require derived-data permission?
3. May transformed component values such as normalized z-scores or contributions be published?
4. If permitted, what attribution, delayed/historical treatment, or redistribution conditions apply?
5. Does the answer differ for machine-readable public files versus human-readable charts/text?

Do not infer permission for any other provider from an S&P response.

## Cboe Global Indices — VIX-derived use

Official public contact:
- marketdata@cboe.com
- Cboe Global Indices Feed / licensing page: https://www.cboe.com/data/global-indices-feed/

Suggested subject:
**USD Impact Score — VIX-derived output and redistribution licensing clarification**

Questions to ask:
1. What agreement/license governs external use of VIX observations obtained through the current delivery path?
2. May a non-reversible aggregate Score/regime derived partly from VIX be published publicly?
3. May normalized VIX-derived values, z-scores, contributions or diagnostic statistics be published?
4. Are historical/public machine-readable derived outputs treated differently from charts or narrative analysis?
5. What attribution, reporting or distribution requirements apply?

## CME Group — WTI and Gold futures-derived use

Official public contact:
- CMEGroupDerivedData@CMEGroup.com
- CME derived-data information: https://www.cmegroup.com/market-data/derived-data.html
- CME derived-data fee material: https://www.cmegroup.com/market-data/files/2026-derived-data-fees.pdf

Suggested subject:
**USD Impact Score — derived-data licensing clarification for WTI and Gold inputs**

Questions to ask:
1. Does the USD Impact aggregate Score/regime constitute a derived work when it uses WTI and Gold futures observations as inputs?
2. Is public publication of the aggregate Score/regime permitted without a separate Derived Data License Agreement?
3. May normalized WTI/Gold component values, contributions, robustness diagnostics or revision statistics be published?
4. Do machine-readable public files require different licensing from non-machine-readable charts or narrative commentary?
5. What attribution, licensing or reporting conditions would apply?

## FRED — DGS2 / DGS10

Official public contact:
- stlsFRED@stls.frb.org
- FRED contact/legal pages:
  - https://fred.stlouisfed.org/help/about/contact-us/contact-us
  - https://fred.stlouisfed.org/legal/

Suggested subject:
**USD Impact Score — DGS2/DGS10 commercial and derived-output usage clarification**

Questions to ask:
1. Are DGS2 and DGS10 owned directly by the Federal Reserve Bank of St. Louis or by a third party for rights purposes?
2. What permissions/attribution apply to commercial internal use?
3. May transformed DGS2/DGS10-derived values be published publicly?
4. May a non-reversible aggregate Score/regime derived partly from those series be published?
5. Are there restrictions on machine-readable public history or archives?

FRED's public legal page states that third-party-owned series may carry separate restrictions, so series-level confirmation is required.

## Yahoo Finance / yfinance delivery path

No provider approval should be inferred from the yfinance package itself.

Current Yahoo Developer Network guidance states that commercial-use rules differ by API/service and that services designated non-commercial-only may not be incorporated into subscriber-only, SaaS, paid products or business productivity tools.

Required routing before outreach:
1. identify the exact Yahoo service/terms governing the delivery path actually used by yfinance for each instrument;
2. identify the upstream rights owner where relevant;
3. route the question to Yahoo and/or the upstream owner rather than treating yfinance documentation as a license.

Instrument mapping currently requiring confirmation:
- DX-Y.NYB — DXY;
- CL=F — WTI futures;
- ^GSPC — S&P 500;
- ^VIX — VIX;
- BTC-USD — Bitcoin;
- GC=F — Gold futures.

Questions to resolve:
- commercial internal use;
- retention;
- public redistribution;
- transformed/derived component publication;
- aggregate non-reversible Score/regime publication;
- archive treatment.

## Required context to include in every provider request

Keep the request narrow and factual:
- USD Impact is an educational/commercial web product;
- Score v2 combines eight weekly drivers using fixed published weights;
- the proposed conservative public target contains only date, aggregate Score, regime and aggregate history;
- provider-derived levels, z-scores, contributions and normalization moments can remain private;
- no raw provider response payloads are proposed for public redistribution;
- ask separately about component-derived diagnostics/revisions if those outputs are intended to remain public.

Do **not** describe the aggregate-safe target as already approved.

## Evidence to attach or reference

Engineering evidence is already available in-repository:
- issue #155;
- provider/counsel decision package;
- public rights inventory;
- aggregate-safe transformer definitions;
- private-evidence/OIDC rehearsal evidence;
- locked-reader compatibility and full `write=False` dry-run evidence.

Avoid sending private evidence bytes, credentials, tokens, internal secrets or provider-derived component values unless specifically authorized.

## Response recording

Any provider/counsel response must be recorded through the decision-receipt process. A provider email alone must not directly authorize Production.

Required recording:
- exact provider/authority;
- date;
- scope/products/fields covered;
- conditions/attribution;
- agreement or reference;
- public class dispositions A-F;
- approved public schema;
- archive treatment;
- replication wording;
- private evidence boundary;
- separate Production authorization remains required.

## Current boundary

No outreach has been sent by this work.

Issue #155 remains HOLD. Real provider evidence, public replacement and Production remain unauthorized.
