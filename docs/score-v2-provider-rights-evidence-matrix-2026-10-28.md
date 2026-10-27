# Score v2 provider-rights evidence matrix — 2026-10-28

Status: **counsel/provider review evidence only**.

Related:
- issue #155 — public Score v2 redistribution hold;
- PR #156 — containment design;
- PR #157 — aggregate-only/public-safe + private-evidence prototypes.

This matrix is not legal advice and does not determine whether a particular current use is permitted. It records current public provider terms and the concrete engineering questions that remain unresolved.

## Executive conclusion

The current Score v2 public surface should remain under review because:

- several production drivers are delivered through Yahoo Finance/yfinance;
- underlying data may be owned/licensed by third parties such as S&P Dow Jones Indices, Cboe and CME;
- current public Score artifacts expose provider-derived values and derived fields, not merely an aggregate score;
- public provider terms contain restrictions on commercial use, redistribution and/or derived data;
- sourcing data through a distributor does not necessarily remove underlying licensing obligations.

The safe engineering default is therefore:

> Preserve the Score calculation and aggregate Score/regime product, but do not expand public per-driver value/derivative exposure unless provider/counsel rights are documented.

## Current production drivers

| Score driver | Current transport | Current series/ticker | Underlying rights concern | Current engineering treatment |
|---|---|---|---|---|
| DXY | Yahoo Finance via yfinance | `DX-Y.NYB` | Yahoo terms + underlying ICE/index rights may apply | HOLD for public per-driver values/derivatives |
| WTI | Yahoo Finance via yfinance | `CL=F` | Yahoo terms + CME futures data rights may apply | HOLD for public per-driver values/derivatives |
| SPX | Yahoo Finance via yfinance | `^GSPC` | Yahoo terms + S&P Dow Jones Indices rights apply | HOLD for public per-driver values/derivatives |
| VIX | Yahoo Finance via yfinance | `^VIX` | Yahoo terms + Cboe index-data rights apply | HOLD for public per-driver values/derivatives |
| BTC | Yahoo Finance via yfinance | `BTC-USD` | Yahoo/service terms; underlying venue/provider chain still requires confirmation | HOLD for public per-driver values/derivatives |
| GOLD | Yahoo Finance via yfinance | `GC=F` | Yahoo terms + CME/COMEX futures data rights may apply | HOLD for public per-driver values/derivatives |
| UST 2Y | FRED | `DGS2` | Federal Reserve/Treasury public-source treatment differs from proprietary market-data inputs | review separately; not assumed to share Yahoo/market-data restrictions |
| UST 10Y | FRED | `DGS10` | Federal Reserve/Treasury public-source treatment differs from proprietary market-data inputs | review separately; not assumed to share Yahoo/market-data restrictions |

## Current public evidence reviewed

### Yahoo Developer Network

Source:
https://legal.yahoo.com/us/en/yahoo/guidelines/ydn/index.html

Current Yahoo guidance says commercial-use permissions differ by API/service and that some APIs/services are non-commercial only. Its published restrictions for non-commercial services include use in commercial/business websites, subscriber products and business productivity tools.

Engineering implication:
- the project must not infer commercial redistribution permission merely because a value can technically be retrieved through a Yahoo-facing endpoint;
- exact service/API rights and any upstream data-owner restrictions need confirmation.

Open decision:
- identify the legally applicable Yahoo service/API terms for each current Score transport;
- determine whether the current use, storage, transformation and redistribution are permitted.

### S&P Dow Jones Indices

Sources:
- https://www.spglobal.com/en/terms-of-use
- https://www.spglobal.com/spdji/en/disclaimers/
- https://www.spglobal.com/spdji/en/documents/legal/dow-jones-indexes-terms-conditions.pdf

Current S&P public terms state that SPDJI data is generally for non-commercial/personal use unless otherwise permitted and expressly restrict creation of derived data based on SPDJI data without written consent. Redistribution/reproduction is also restricted.

Relevant Score driver:
- `^GSPC` / S&P 500.

Engineering implication:
- publishing a long public history of S&P-derived z-scores or other derived component values should not be assumed safe without written rights analysis;
- aggregate Score/regime containment is the preferred conservative fallback.

Open decision:
- confirm whether the current Score use of S&P 500 values and derived public artifacts is licensed/permitted;
- if not, identify the minimum public output allowed while preserving internal calculation/auditability.

### Cboe

Sources:
- https://www.cboe.com/data/market-data-services/document-library
- https://cdn.cboe.com/resources/membership/Market_Data_Policies_july2026.pdf

Current Cboe policy materials state that usage depends on the selected data product and applicable policy/fees. The July 2026 policy states that delayed/end-of-day/historical subscribers who are exempt from a data agreement are not permitted to redistribute data externally other than to a named affiliate; index-data subscribers may require additional licensing depending on use/distribution.

Relevant Score driver:
- `^VIX`.

Engineering implication:
- public redistribution of VIX-derived component fields should remain on hold absent documented rights;
- the existing Three Dials decision to avoid public VIX numeric republication does not automatically resolve Score.

Open decision:
- determine whether the Score's current VIX use/derivatives qualify for an existing permitted category or require a Cboe agreement/license.

### CME Group

Sources:
- https://www.cmegroup.com/trading/market-data-explanation-disclaimer.html
- https://www.cmegroup.com/market-data/license-data/information-policies.html
- https://www.cmegroup.com/market-data/distributor/files/cme-group-data-licensing-policy-guidelines-and-non-display-licensing-faq.pdf
- https://www.cmegroup.com/market-data/files/cme-derived-data-license-agreement.pdf

Current CME public materials restrict redistribution and creation of derivative works without authorization and state that licensing obligations can depend on how information is used even when sourced through an authorized distributor. CME also maintains specific non-display and derived-data licensing frameworks.

Relevant Score drivers:
- `CL=F` (WTI futures);
- `GC=F` (Gold futures).

Engineering implication:
- Yahoo transport does not by itself establish the right to publish CME-derived values or transformations;
- public component histories, z-scores, normalization moments and contributions should remain under hold pending provider/counsel determination.

Open decision:
- determine whether the Score calculation is non-display, derived-data or another licensed use category;
- determine whether aggregate-only public Score output avoids the relevant redistribution/derived-data concerns or still needs a license.

## Important chain-of-rights limitation

A Yahoo-delivered ticker can carry rights from multiple layers:

1. transport/service terms;
2. underlying exchange/index owner rights;
3. display vs non-display rights;
4. storage/history rights;
5. derived-data rights;
6. external redistribution/publication rights.

Therefore:

- “retrievable from Yahoo” is not sufficient evidence of redistribution permission;
- “transformed into a z-score” is not sufficient evidence that underlying rights disappear;
- “the original value is not shown directly” is not sufficient evidence that a derived-data license is unnecessary.

Provider/counsel must make that determination.

## Engineering containment decision tree

### If written rights permit the current public component artifacts

Document:
- provider/license name;
- covered entity;
- covered project/use;
- covered source/ticker/data class;
- display/non-display scope;
- derived-data scope;
- redistribution scope;
- historical archive treatment;
- attribution requirements;
- effective/expiry dates.

Then keep or refine the current public schema under those documented terms.

### If rights are unclear or do not permit the current public component artifacts

Use the containment architecture in #156/#157:

Public:
- aggregate Score;
- regime;
- aggregate Score/regime history;
- methodology/weights/regime bands;
- approved non-value-bearing release fingerprints.

Non-public evidence:
- strict weekly levels;
- normalization moments;
- component z-scores/contributions;
- exact provider/ticker provenance;
- research inputs required by frozen Score v2/v3 protocols.

Do not remove historical public artifacts until archive treatment is explicitly decided.

## Questions counsel/provider should answer

1. Is KELA LEADS S.R.L. permitted to use the current Yahoo-delivered inputs for a commercial educational/subscription product?
2. Are the current per-driver z-scores, contributions and normalization moments considered derived data that require separate permission?
3. Does public historical publication of those derived values constitute redistribution?
4. Does publishing only the aggregate multi-input Score/regime materially change the licensing analysis?
5. Are internal/non-public research calculations and frozen evidence permitted under the relevant non-display/research terms?
6. Are historical public archives already published subject to removal, continued display, notice, or other remediation?
7. What attribution, disclaimer, audit and retention obligations apply?
8. What written evidence should be retained to demonstrate permission?

## Current engineering disposition

- No formula, weight, driver or Production change is authorized by this matrix.
- Do not expand public component data.
- Continue aggregate-only/public-safe and private-evidence prototypes in draft review only.
- Do not wire private evidence into research until the storage/access boundary is approved.
- Do not delete historical evidence.
- Keep issue #155 open until a provider/counsel rights decision or approved containment release is complete.
