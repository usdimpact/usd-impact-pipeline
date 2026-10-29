# Score v2.1F / WPU0561 — 2026 BLS source-boundary review (v10 proposal)

**State: DESIGN-ONLY PROPOSAL / HOLD — NOT AN OWNER METHODOLOGY DECISION.**

**Issue:** https://github.com/usdimpact/usd-impact-pipeline/issues/258  
**Rights hold:** https://github.com/usdimpact/usd-impact-pipeline/issues/155  
**Baseline protected main:** 0c420f495e6196d34d195d441edf7b707da4f35a (v9)  
**Scope:** identify one candidate original BLS April 2026 primary document for a future *separately authorized* structural-feasibility review. No source replacement, runtime activation, score calculation, rights clearance or release.

## 1. Existing evidence is frozen

The completed, consumed v8 preflight (https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40901086765) retained structural data only, with exactly two fixed-resource requests; no identifier values or economic values retained.

- May 2013 archived PPI HTML, selected table 4: target identity and an index-level header are structurally compatible; index-level value read remains unauthorized.
- April 2026 PPI Detailed Report XLSX, selected xl/worksheets/sheet3.xml under the exact-label/direct-commodity rule: identifier and percent-change headers were observed, but no index-level field was observed in the verified selected-container header band.
- Under these **unchanged fixed resources**, a representative index-level pair is not feasible. The previously proven Crude petroleum -> WPU0561 identity is not reversed.
- v9 forbids switching to domestic-production, extraction, pipeline, stage-demand or unrelated rows/containers merely to find an index column. This proposal does not relax that rule.

## 2. One external-document candidate, NOT an adopted source

**Candidate C1: BLS archived April 2026 PPI Detailed Report — PDF edition, potentially Table 9.**

Primary metadata-only evidence:

1. BLS official archived monthly reports index explicitly lists an **April 2026 PDF** alongside the April 2026 XLSX: https://www.bls.gov/ppi/detailed-report/
2. BLS official PPI tables directory describes **Table 9** as producer price indexes for commodity and service groupings and individual items: https://www.bls.gov/ppi/tables/home.htm
3. BLS archived **April 2026 PPI news release** identifies the first release date as **May 13, 2026**: https://www.bls.gov/news.release/archives/ppi_05132026.htm

The two sources in (1) and (2) establish only publication and table purpose, NOT that an April 2026 original-release WPU0561 index-level row is present in the PDF. The archived release in (3) is dating/provenance context only, NOT an automatic data fallback.

**Exact PDF resource URL:** unresolved and not preregistered. The official archived index entry is a human-readable locator, not authorization to download. Do not infer a URL from the XLSX filename or another month's PDF.

**Candidate document fetched/parsed during this proposal:** NO.  
**PDF field/header observed:** NO.  
**Exact WPU0561 row present in PDF:** UNKNOWN.  
**Unadjusted index-level field present for that row:** UNKNOWN.  
**Original-publication vintage independently proven:** NO.

Do not silently widen to a different report, supplemental file, current database, API, FRASER-held copy, or another month if C1 fails.

## 3. Publication-vintage risk

BLS explicitly cautions on its archive index that PPI indexes are subject to revisions up to four months after original publication; seasonally adjusted series can also be revised on a different timetable. Archive membership alone does NOT prove that a currently hosted document is the immutable May 13, 2026 first-release edition.

A future methodology review must establish whether C1 is the original-release April 2026 edition, including applicable publication date, revision state and any correction/replacement notices. A third-party archive may support provenance investigation but may not be substituted as the data source under this proposal.

No current-vintage BLS database observation or back-calculated level may stand in for an original-release observation.

## 4. Preconditions before accepting C1 as a methodologically eligible source

All conditions must pass independently; any unknown, absence, ambiguity or conflict means HOLD:

1. **Authentic URL:** owner reviews a single exact official BLS PDF resource path and its provenance; no pattern-guessing or dynamic fallback.
2. **Correct edition:** reference month April 2026, publication provenance consistent with first release on May 13, 2026, and no unresolved corrections/replacements.
3. **Correct table:** independently establish Table 9's governing header, page/section identity and original layout. Do not infer fields from another table.
4. **Correct series:** exactly one direct commodity concept matching previously proven Crude petroleum / WPU0561. Exclude derivative, domestic-production, stage-demand, extraction and transport variants; no concept substitution.
5. **Correct field:** unadjusted **index level**, not percentage change, seasonally adjusted index, relative importance, percent contribution or another numeric field.
6. **Vintage equivalence:** 2013 and 2026 observations must have clearly comparable release-vintage definitions, series identity, index basis, preliminary/revised status, unit conventions and time-period anchoring. If a rebase or definition break is needed, stop for a separate decision instead of silently adjusting.
7. **Structural-only preflight first:** a separately preregistered PDF-safe parser and structural-inventory contract must be approved before any network access or content processing. No economic field, numeric identifier value, or full document text retained at this stage.
8. **Legal/rights separation:** Issue #155 remains a HOLD. Source feasibility does not convey redistribution or public-publication authorization.

## 5. If the owner separately approves the methodology *design*

First record the exact official PDF path, provenance and format; propose a **new**, versioned, finite, audit-ready contract. It must specify:

- Exactly which primary resources (and host) may be contacted, whether the original 2013 HTML remains unchanged, and a fixed total request budget. Prior v8 authorization is consumed and cannot be reused.
- An approved PDF parsing dependency/environment and bounded pages/regions/cell counts. The historic Python-standard-library HTML/XLSX contract cannot be silently repurposed for PDF.
- A deterministic exact-target and governing-header algorithm that fails closed on zero/multiple matches, schema gaps, correction ambiguity, or vintage mismatch; never use candidate row/page numbers as selectors.
- Only sanitized non-economic structural evidence, bounded output, no response body/document persistence, no identifiers or economic values at the first gate.
- Two protected GitHub Actions audit writes before dispatch, explicit separate owner authorization for a one-off live structural preflight, zero retries, serialized requests, redirects rejected, 401/403/429/challenge global stop, and mandatory receipt/dispatch consumption after success or failure.
- New, independent owner decisions for **identifier-value read**, **economic-value read**, **historical reconstruction**, **Score calculation**, **research-ledger write**, **public artifact replacement**, and **Production**. No action in one stage authorizes the next.

This document does NOT supply an executable contract, authorization receipt, workflow dispatch marker or any authorization.

## 6. Decision gate

**Proposed choice for owner review:** permit drafting a new source-boundary methodology around *only* C1's original-release official BLS PDF, subject to the unresolved validations above.

The current v9 design and execution contract remain authoritative until a distinct owner methodology decision is recorded and reviewed. A draft proposal must not be interpreted as such a decision.

**Currently forbidden and unchanged:** further live BLS requests; numeric identifier/economic value reads; whole-history reconstruction; Score/z-score/contribution computation; source substitution; research-ledger mutation; public replacement; deployments, emails, payments, Supabase/Cloudflare/Resend/Render changes; Production release. Issue #155 stays HOLD.
