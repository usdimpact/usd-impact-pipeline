# Score v2 provider/counsel rights decision package — 2026-10-28

Status: **decision requested / engineering HOLD remains active / no legal conclusion / no Production authorization**.

Related:
- issue #155;
- `governance/score-publication-rights-gate.json`;
- `governance/score-public-rights-surface.json`;
- `governance/score-private-research-migration-contract.json`;
- `governance/score-rights-decision-matrix.json`;
- `governance/score-rights-decision-receipt.schema.json`;
- `governance/score-rights-decision-receipt.template.json`.

## Dated operational follow-up (2026-10-29; supersedes only correspondence status)

The original 2026-10-28 packet below remains a **decision request**, not a grant. A new [provider follow-up packet](score-provider-rights-followup-packet-2026-10-29.md) and [fail-closed machine-readable queue](../governance/score-provider-rights-followup-queue-2026-10-29.json) now reconcile current source-specific questions and the zero-budget constraint.

- **FRED:** limited 2026-10-29 conditional commercial processing for public-domain-tagged series with citation and disposal. **No storage/retention permission**, no blanket approved derived output, and no AI/ML waiver. Counsel must separately assess historical weekly-derived values and receipts.
- **S&P DJI:** the existing 2026-10-28 index-data inquiry was referred to sales; **no license** granted. Wait on the existing case rather than opening duplicates.
- **Cboe VIX:** sales qualification requested; the owner has already asked whether a **no-cost aggregate-only** route is available. **No affirmative response** yet; do not disclose requested individual/background details in public GitHub.
- **CME WTI/Gold:** the existing derived-data inquiry has not yielded an affirmative clearance. Do not assume the futures history is licensed merely because it is Yahoo-delivered.
- **Yahoo/yfinance and ICE USDX:** delivery rights and underlying index rights are independent unresolved questions. Identify exact product/licensor and no-cost path before any provider change.
- **Treasury/H.15 direct source:** official XML feed and synthetic-only parser are research candidates; retain a NO-GO on real XML fetch, parity, commercial retention, public output and source switch.

**No provider outreach, payment, public-artifact transformation, Production release or decision receipt modification is authorized by this update.** Existing issue #155 HOLD and the separate synthetic-only Development research authorization continue to apply.

## Decision requested

USD Impact needs a written provider/counsel disposition for the public use of Score v2 data and derived outputs.

Engineering is **not** asking whether the Score calculation should change. The requested decision is limited to:
1. what provider-derived or transformed fields may remain public;
2. what fields must be private/internal;
3. what provider/source attribution may remain public;
4. whether aggregate non-reversible Score/regime outputs require any additional license or conditions;
5. whether component-derived research diagnostics may be published;
6. how historical public archives must be treated.

No legal conclusion is encoded in this package.

## Current public classes

### Class A — aggregate / operational

Examples:
- member-required and operational pages;
- robots/favicon;
- aggregate backtest results.

Proposed engineering treatment: **retain public**, subject to any separate counsel concern.

### Class B — methodology / source-contract transparency

Examples:
- Score methodology and data semantics;
- schemas;
- independent replication protocol.

Proposed engineering treatment: **retain public with reviewed wording**.

Decision required:
- whether exact provider names, source URLs and ticker mappings may remain public;
- how replication claims must be narrowed if strict evidence becomes private.

### Class C — direct component-derived release evidence

Examples:
- full Score CSV/JSON containing per-driver transformed histories;
- weekly input;
- strict reproduction bundle;
- dated Score/weekly-input/reproduction archives.

Proposed engineering treatment: **aggregate-safe public replacement after private evidence migration**.

Default aggregate-safe public fields already proven by code:
- date;
- aggregate Score;
- regime;
- aggregate history;
- methodology weights;
- non-value-bearing aggregate history hash.

Fields excluded by the review prototype:
- weekly provider-derived levels;
- component z-scores;
- component contributions;
- normalization means/std;
- source URLs and provider codes.

### Class D — aggregate research with provider provenance

Proposed engineering treatment: retain aggregate research results where approved, while removing or narrowing provider provenance if required.

### Classes E/F — component-derived diagnostics and revisions

Proposed engineering treatment: aggregate-safe transformation or private-only delivery unless provider/counsel expressly approves the transformed component outputs.

## Provider-specific questions

### Yahoo Finance / yfinance delivery path

Current Yahoo Developer Network guidance distinguishes APIs/services that may be available for commercial use from services designated non-commercial only. For non-commercial-only services, Yahoo says subscriber-only, SaaS, paid products and business productivity uses are not permitted.

Decision requested:
- identify the applicable Yahoo/upstream rights for each Score instrument delivered through the current yfinance path;
- confirm commercial internal use;
- confirm retention;
- confirm public redistribution;
- confirm publication of transformed/derived values;
- confirm whether aggregate non-reversible Score/regime values are permitted.

This package does not assume that one Yahoo page resolves the rights of every upstream dataset.

### S&P Dow Jones Indices / S&P 500

S&P Global's current public terms state that, absent an applicable agreement, SPDJI data may not be used to create derived data without express written consent and may not be redistributed externally.

Decision requested:
- whether the Score's aggregate output is treated as derived data requiring permission;
- whether transformed S&P component values may be public;
- what attribution/licensing language is required.

### Cboe Global Indices / VIX

Cboe's July 2026 market-data policy indicates that Cboe Global Indices delayed/end-of-day/historical distribution requires a data agreement, and notes that index-data subscribers may require additional licensing depending on planned use/distribution.

Decision requested:
- whether public transformed VIX-derived fields require redistribution/derived-data permission;
- whether aggregate non-reversible Score/regime output is permitted under the applicable license/terms.

### CME Group / WTI and Gold futures

CME publishes separate market-data and derived-data licensing rules. Current CME materials state that creation of derivative works may require express permission/separate licensing, while some limited graph/chart uses are treated differently under specified conditions.

Decision requested:
- whether the Score or its diagnostics constitute a CME-derived work;
- whether current WTI/Gold component transformations may be published;
- whether aggregate Score/regime outputs are permitted and under what conditions.

### FRED / DGS2 and DGS10

Treasury series are a distinct source path and must be reviewed separately from Yahoo-delivered observations.

Decision requested:
- confirm redistribution and attribution requirements for DGS2/DGS10;
- confirm whether transformed component values and aggregate Score outputs may remain public.

## Engineering evidence already completed

The rights decision does not require speculative engineering work. The replacement path has already been proven under synthetic/Development containment:

- private Development evidence boundary: proven;
- GitHub OIDC read path: proven;
- aggregate-safe Score transformer: proven;
- aggregate-safe research transformers: proven;
- broker-downloaded private bundle -> research adapter: proven;
- locked Score v2 predictive compatibility: proven;
- locked Score v3 compatibility: proven;
- full first-week locked-reader execution with `write=False`: proven;
- locked research sources/engine lock: unchanged;
- no Production migration performed.

## Recommended decision shape

The decision should explicitly disposition each public class A-F and each provider family rather than returning a single broad "approved" or "not approved" statement.

The repository template is intentionally fail-closed:
- every class starts `pending`;
- every provider starts `pending`;
- no decision authority is prefilled;
- no decision timestamp is prefilled;
- no public schema is pre-approved;
- Production authorization is always separate.

## Decision outcomes

### Outcome 1 — aggregate-only public approved

Expected engineering follow-up:
1. finalize and approve the aggregate-safe public schema;
2. migrate remaining real research dependencies to approved private evidence;
3. plan archive/consumer migration;
4. replace Classes C/E/F with approved aggregate-safe views;
5. update Class B wording/replication claims;
6. exact-head CI and non-Production release validation;
7. request a separate Production authorization.

### Outcome 2 — component publication expressly permitted

Record the exact provider, fields, products, time periods, attribution terms and agreement/reference. Do not infer permission for another provider or another class.

### Outcome 3 — unresolved / HOLD

No public replacement or real provider-evidence migration occurs. Existing HOLD remains active.

## Current public-source verification snapshot

Reviewed on 2026-10-28:
- Yahoo Developer Network Guidelines: https://legal.yahoo.com/us/en/yahoo/guidelines/ydn/index.html
- S&P Global Terms of Use: https://www.spglobal.com/en/terms-of-use
- Cboe Market Data Policies, effective July 1 2026: https://cdn.cboe.com/resources/membership/Market_Data_Policies_july2026.pdf
- CME derived-data fee/policy material: https://www.cmegroup.com/market-data/files/2026-derived-data-fees.pdf
- CME Market Data Explanation and Disclaimer: https://www.cmegroup.com/trading/market-data-explanation-disclaimer.html

These public materials support conservative review but do not substitute for the applicable contracts, provider confirmations, or legal advice.

## Release boundary

This decision package does **not** authorize:
- real/provider-derived evidence upload to the private boundary;
- migration of live research readers;
- public artifact replacement;
- archive redaction/removal;
- Score formula changes;
- Production deployment.

Issue #155 remains the controlling HOLD until a completed decision receipt is reviewed and a separate Production authorization is recorded.
