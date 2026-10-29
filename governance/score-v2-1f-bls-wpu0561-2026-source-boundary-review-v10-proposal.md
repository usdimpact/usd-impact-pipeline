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

**Exact PDF href in the archive listing (metadata-only):** https://www.bls.gov/ppi/detailed-report/ppi-detailed-report-april-2026.pdf. The href was extracted from the *official April 2026 PDF anchor* in the BLS HTML archive listing without following the PDF link. This verifies link metadata only, not HTTP availability, contents, a cryptographic digest, or original-release vintage. The PDF has **not** been downloaded or parsed and remains unauthorized as a data source.

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

## 7. Evidence-ledger addendum (metadata-only, no candidate PDF ingestion)

The companion machine-readable register is:
[score-v2-1f-bls-wpu0561-2026-source-boundary-review-v10-evidence.json](score-v2-1f-bls-wpu0561-2026-source-boundary-review-v10-evidence.json).

This register has 10 independent gates (unknown/HOLD/not authorized), 18 adversarial rejection cases, explicit no-network/no-value authorizations, and an unresolved exact PDF URL. It is inert data: it must not be treated as a new source selector or a runnable workflow.

Metadata evidence distinctions:

| Question | Established in existing official publication metadata? | May it be used for an April 2026 index-level value? |
| --- | --- | --- |
| BLS lists an April 2026 Detailed Report PDF | Yes, archive listing only | No |
| BLS April 2026 PPI release was dated May 13, 2026 | Yes, archived news release | No |
| BLS defines Table 9 as a detailed commodity/service index table | Yes, table directory | No |
| An **earlier March 2026 PDF** Table 9 exposes unadjusted index columns | Search-indexed example only: https://www.bls.gov/ppi/detailed-report/ppi-detailed-report-march-2026.pdf | No — other month |
| Exact April 2026 PDF href / first-release immutability | BLS HTML href now established; original-release immutability NOT established | No |
| The specific April Table 9 WPU0561 direct-commodity row exists | Not established | No |
| Matching historical-vintage unadjusted level exists and is comparable to 2013 | Not established | No |

**Series-label discrepancy requiring an explicit owner adjudication.** The BLS/FRED-hosted series metadata page https://fred.stlouisfed.org/series/WPU0561 calls WPU0561 "Crude Petroleum (Domestic Production)." The consumed v9 candidate is the exact shorter string "Crude petroleum," and its no-broadening rule explicitly prohibits *switching to a domestic-production variant* merely to discover an index-level field. Matching digits or a FRED label does not settle semantic identity or authorize a label substitution. The earlier proven 0561 identifier remains proven as originally scoped; its equivalence to a differently titled PDF row is a separate unresolved question. FRED may be referenced as a **warning about metadata naming**, never as a price source or a way to recover values.

**Do not assume Table 9 resolves the issue.** The indexed March PDF shows a *type* of layout but provides no proof that the exact April PDF has the target series or that the archived PDF is a date-frozen original copy. The official BLS archive also warns that reported indexes may differ from later revised releases. If those questions cannot be settled with bounded evidence, retain v9 infeasibility.

## 8. Pre-registration of negative outcomes (review-only)

The following scenarios must fail closed rather than trigger wider or repeated searching:

- Unverified or patterned PDF URL; link redirects to current/latest report; wrong or corrected edition.
- Target appears only as a footnote, different commodity label, domestic-production concept without adjudication, extraction, transportation, pipeline, or stage-demand classification.
- Missing governing Table 9 header; only a percentage-change, relative-importance or seasonally adjusted field; ambiguous OCR or split columns.
- Multiple plausible target rows, missing code, incompatible code components, conflicting or unattributed revision markers.
- Different 2013 vs 2026 index base/definition without separately approved comparability plan.
- Need to parse or retain economic tokens merely to conduct a structural-only preflight, when no such read has been authorized.
- Inability to prove the exact original-release vintage, including BLS corrections or replaced PDFs.
- Rights gate #155 unresolved or any attempt to use BLS availability as implicit publication rights.
- Any temptation to use current BLS series, FRED, a third-party mirror or a later release as a backfill or substitute.

The numbered adversarial cases and their required HOLD outcomes are maintained in the companion evidence register; this Markdown summary is explanatory, not executable.

## 9. Proposed stages and explicit decisions

| Stage | Intended work | Current state | New separate approval required? |
| --- | --- | --- | --- |
| S0 | Record published metadata and design candidate without fetching PDF | Completed as proposal | No live access |
| S1 | Owner permits candidate-specific PDF methodology DESIGN, not adoption or retrieval | **DESIGN-ONLY APPROVED 2026-10-29** | No live request or source-adoption approval |
| S2 | Validate the archive-linked PDF provenance, original-release identity and parser bounds; preregister any new execution contract | **HOLD** | Yes — separately reviewed contract and exact-resource gate |
| S3 | Run one bounded structural-only preflight under explicit activation/dispatch/consumption lifecycle | **NOT AUTHORIZED** | Yes — one-off live preflight |
| S4 | Verify source-code/series identity and later any economic level | **NOT AUTHORIZED** | Yes — independently for each category of read |
| S5 | Evaluate historical reconstruction, normalization or Score v2.1F | **NOT AUTHORIZED** | Yes — separate methodology/computation review |
| S6 | Modify research ledger, public artifacts or Production | **NOT AUTHORIZED** | Yes — independent rights and release gates |

The old v8 network allowance was already consumed. None of S1–S6 is approved by opening a draft PR or saying to continue design work. No new workflow, auth receipt, dispatch marker or BLS request has been created.

## 10. Owner decision alternatives

**A. Retain the v9 fixed-resource boundary:** original XLSX selected target has no index-level schema; freeze WPU0561 feasibility as failed closed in this design.

**B. Authorize only a *new design phase* about the exact official BLS April 2026 Detailed Report PDF:** this permits planning further checks, but not selecting/reading the source, requesting the PDF, reading any series/value, updating Score, or releasing anything.

**C. Defer the source-boundary decision:** retain v9 and PR #286 as draft; do not schedule or dispatch any preflight.

The owner approved **B only for design-phase continuation on 2026-10-29**. This is not adoption of C1, not authorization to fetch the PDF or read numbers, and not authorization to merge/release. Operational execution remains **HOLD**. Issue #155 remains HOLD independently.

## 11. Approved design-only metadata follow-up and audited recovery points

**Approval boundary (2026-10-29):** candidate-specific design research, archive link metadata and offline recovery preparation only. It does not authorize any PDF GET, BLS identifier/economic read, scoring, source substitution, rights clearance or Production change.

**Exact BLS archive href now identified:** https://www.bls.gov/ppi/detailed-report/ppi-detailed-report-april-2026.pdf. Obtained from the archive page's HTML outgoing links without accessing the PDF. The document content, hash, date-frozen provenance, corrections and Table 9 row/schema remain **unverified**. An exact URL is not itself an eligible source.

**Two Git recovery anchors created and compare-verified to be identical to their pinned commits:**

- Protected v9 HOLD tree: 0c420f495e6196d34d195d441edf7b707da4f35a; branch backup/score-v2-1f-v9-hold-2026-10-29.
- Original v10 draft tree: 698fb0c0d069c598909cc10e875a28cb711d1ea5; branch backup/score-v2-1f-v10-review-2026-10-29.

**Offline recovery controls drafted (not a live rollback):** governance/score-v2-1f-wpu0561-v10-recovery-manifest.json pins six frozen governance blob hashes; scripts/validate_score_v2_1f_wpu0561_recovery.py checks that rights/authorization/workflow guards remain HOLD; tests/test_score_v2_1f_wpu0561_recovery.py exercises synthetic failure cases; .github/workflows/score-v2-1f-wpu0561-recovery-drill.yml runs an unprivileged PR-time synthetic restore rehearsal. docs/recovery/score-v2-1f-wpu0561-v10-backup-and-restore.md documents PR-only recovery and independently authorized provider-specific rollbacks.

Git branches are mutable pointers, not independent offsite backups. The new workflow cannot restore Production or a provider database and requires its own default-branch merge before manual workflow_dispatch is available. All actual restores require separate incident review.

**Current gate:** review PDF first-release identity, exact Table 9 semantics and potential Crude Petroleum (Domestic Production) naming mismatch in a future *independently authorized* bounded source assessment. No further BLS fetch is allowed under this design-only approval.

## 12. Proposed v11 PDF structural-preflight contract (2026-10-29 continuation)

**Status: PREREGISTERED DRAFT / HOLD; not an executable workflow and not a live request.**

The next design file is governance/score-v2-1f-bls-wpu0561-pdf-structural-preflight-v11-design.json. It does **not** modify the authoritative v9 methodology contract or the consumed v8 lifecycle.

### Fixed candidate and limits (proposal only)

- One exact potential official BLS path: https://www.bls.gov/ppi/detailed-report/ppi-detailed-report-april-2026.pdf
- Source selection remains **unapproved**, despite the HTML archive href being established.
- If a later owner authorizes a future live preflight: proposed maximum **one GET**, one request at a time, **zero retries**, **no redirect**, explicit stop on non-200/401/403/429/challenge.
- Proposed hard stop if PDF is over **10 MiB**, exceeds **200 pages**, or expected structure cannot be located without ambiguous broadening. These are design ceilings, not evidence that the PDF meets them. The exact file has not been inspected.
- Proposed retained *sanitized structural metadata* caps: 12 table titles, 96 header tokens, four candidate labels, **zero numeric identifier values** and **zero economic values**. No PDF or raw text body persistence.
- No PDF/OCR parser or execution image has been selected or approved. No executable PDF fetch function, authorization receipt, dispatch marker, or newly enabled network workflow is part of this PR.

### Important exposure distinction

The original no-economic-value-read policy cannot be assumed compatible with simply downloading and text-extracting a PDF that contains economic values. A parser will process bytes and may materialize text representing numeric values even if it does not persist them. The v11 proposal therefore **does not authorize PDF download or parsing**. A separate owner/security/rights decision must define whether bounded ephemeral raw-byte handling is acceptable, and, if so, how any numeric semantic access is excluded and proven with adversarial tests. If that cannot be established, **stop**. Do not reinterpret 'no retained values' as 'no value access.'

### Independently blocking scientific questions

1. Is this exact PDF the first-published May 13, 2026 edition rather than a corrected/replaced copy?
2. Does April Table 9 expose an unadjusted index-level column governed by a compatible period header?
3. Is its direct-commodity row semantically the same WPU0561 as the frozen 2013 identity, without reclassifying domestic-production or stage-demand variants to make the data fit?
4. Is the April 2026 observation index base/definition comparable with the selected May 2013 observation, including rebase and revision handling?
5. Can the document be parsed inside a separately reviewed pinned dependency/runtime without unauthorized numeric access, logging, OCR or disk persistence?
6. Does any future retention or public use satisfy independent data-rights gates (Issue #155)?

The May 13, 2026 date comes from the official BLS archived April 2026 PPI *news release*. It is not independent proof of the PDF's own immutable publication timestamp. Official BLS PPI methodology notes that revisions can occur after first publication, so vintage equivalence must be explicitly demonstrated.

### Synthetic-only test coverage

The draft adds scripts/validate_score_v2_1f_wpu0561_pdf_v11.py and tests/test_score_v2_1f_wpu0561_pdf_v11.py. They accept only invented metadata facts, with exact Table 9 title, direct-commodity label, unadjusted index-level role and unique April 2026 observation-column assertions. Any extra economic field, raw code value, domestic-production substitution, unknown vintage, duplicate row, percent-only header, wrong URL/month, or other nonconforming input fails closed.

Even a nominal synthetic fixture yields only synthetic_layout_compatible_not_authorized; it cannot certify the real PDF, release vintage, source rights, WPU0561 identity, or Score calculation. This separate test step is wired into the unprivileged PR recovery workflow; it uses **no network, PDF or OCR library**.

### Next owner gate, explicitly not delegated

The only current authorization is **design-only preregistration and synthetic testing**. To go further, the owner would separately need to decide that the exact PDF is an admissible *candidate for a bounded preflight*, approve the actual parser/runtime and transient-byte exposure policy, and then issue a fresh one-off preflight authorization with protected activation/dispatch/consumption. No current PR or comment does those steps.

**Fail closed with no workflow activation, no further BLS request, no change to v9 feasibility, no Score/reconstruction, no public/Production changes, and no amendment of Issue #155 rights HOLD.**

## 13. Owner-approved v12 parser/security design — synthetic-only execution

**Owner's new approval:** advance the precise April 2026 BLS PDF candidate-source boundary and parser/security contract. This permits reviewing metadata and building a **synthetic-only offline prototype**, not fetching the real PDF or reading its numeric contents. The v9 methodology/rights gate and v11 HOLD remain authoritative for any live activity.

The v12 contract is governance/score-v2-1f-bls-wpu0561-pdf-parser-security-v12-design.json. It selects the official archive-linked April 2026 PDF URL as the sole *candidate* for a future separately authorized preflight, with zero requests authorized now. The source cannot be used to produce index-level values until exact release-vintage evidence, Table 9 governing headers, WPU0561 commodity identity, index-basis comparability and redistribution rights are separately established.

The parser candidate is **pypdf 6.21.4** (BSD-3-Clause, published 2026-10-28) with the exact PyPI wheel hash pinned in governance/score-v2-1f-wpu0561-pdf-v12-parser.lock. No production/frozen-research dependency lock changes are included. The pypdf parser is approved only for PDFs invented and generated **within the synthetic test process**. It has no source URL/file argument or real-data execution workflow.

The PR CI installs the hash-verified wheel in a standalone unprivileged fixture environment, then runs scripts/score_v2_1f_wpu0561_pdf_v12_synthetic.py through tests/test_score_v2_1f_wpu0561_pdf_v12.py inside a pinned Python container with network **none**, no secrets, non-root UID, read-only repo/package mounts, capability drops and memory/CPU/PID limits. No BLS PDF data or actual observation is used. A successful fixture is explicitly "synthetic_format_compatible_not_live", never evidence of the actual April PDF's structure.

**Crucial caveat:** pypdf warns that text extraction processes entire page content streams, which may expand far beyond compressed input size. A post-decompression length check is not a protective cap on decompression for real documents. The v12 design requires a separate secure streaming/byte broker, parser isolation, explicit authorization for transient access to economic bytes, security review and rights clearance *before* any real PDF request. The proposed 10-MiB response-byte limit does not resolve that issue.

Rollback is documented in docs/recovery/score-v2-1f-wpu0561-v10-backup-and-restore.md. The original v9, initial v10 and v11 design-only pinned recovery points remain available; real recovery must be via a separately reviewed corrective PR, not a force push. GitHub branches are not offsite/provider backups.

**Still forbidden:** live BLS requests, PDF file ingestion, value extraction, identifier reads, source substitution, reconstruction, Score computation, research-ledger writes, public artifact replacement, Production deployments, and rights-gate release under Issue #155. A new one-off live authorization will be a distinct owner decision.
