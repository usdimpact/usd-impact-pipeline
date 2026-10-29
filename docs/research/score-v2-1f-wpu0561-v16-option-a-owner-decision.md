# Score v2.1F / WPU0561 — Owner-approved Option A

**Decision dated October 29, 2026. Scope: original fixed-resource historical-vintage index-level pair only.**  
**State: fixed-resource methodology concluded infeasible; no new source, economic value, Score, public, or Production work.**

Research governance: [Issue #258](https://github.com/usdimpact/usd-impact-pipeline/issues/258). Separate public data rights: [Issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155). Prior non-executable methodology packet: [PR #299](https://github.com/usdimpact/usd-impact-pipeline/pull/299).

## 1. Date and decision provenance

The v15 packet was merged while the choice among options A/B/C was still pending. Following that publication, the owner explicitly replied **"approved, please continue"** to the immediately preceding recommendation of **Option A** — retaining the original fixed-resource infeasibility, with WPU0561 excluded **only from the proposed unverified representative historical-vintage index-level pair**, while leaving the live Score unchanged. This new successor document records that 2026-10-29 decision. It does **not** rewrite v15's historically correct "no choice selected" record, backdate an earlier review, grant rights approval, or authorize further BLS requests.

The selected option is A. Option B was *not* approved and remains available only as a separately scoped, separately authorized future methodology review. Option C was not selected.

## 2. Precisely what is infeasible

Under the **original, preregistered two-resource boundary**, the fixed 2013 BLS HTML source structurally contains an unadjusted index-level role. The fixed April 2026 XLSX direct-commodity container was correctly selected at `xl/worksheets/sheet3.xml`. The eligible 2026 header band shows commodity identifiers and **percent-change** roles but **no unadjusted index-level field**. The fixed resources therefore cannot supply the required representative 2013/2026 index-level WPU0561 pair.

This finding is limited and does not mean:
- BLS lacks any WPU0561 historical series elsewhere;
- the separate hardened **Crude petroleum → 0561** identifier mapping was wrong;
- existing public WTI or other Score drivers must be removed or replaced;
- a different BLS source is automatically admissible or licensed.

A new source boundary would require a fresh methodological design and explicit owner authorization. The current result should not be "repaired" by trying wider sheets, domestic-production aliases, crude extraction/pipeline variants, or an unrelated candidate whose schema looks more convenient.

## 3. Why the v13 PDF does not overrule the XLSX boundary

The one-off official April 2026 BLS PDF structural inspection was consumed in [run 40924080468](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40924080468) and returned **fail_closed / invalid_page_count**. The frozen parser maps **count <1** or **count >200** to that same code. The actual PDF page count is unknown. No admissible original-release Table 9/WPU0561 unadjusted index-level row, correct period, series variant, historical index basis, or first-edition provenance was proven.

The [v14 offline investigation](https://github.com/usdimpact/usd-impact-pipeline/pull/297) and [v15 methodology packet](https://github.com/usdimpact/usd-impact-pipeline/pull/299) added synthetic tests and options, not new actual PDF observations or economic values. The original v13 claim remains permanently consumed and must not be removed or reused.

**This owner decision does not assert that the PDF source is invalid or that its page count exceeds 200.** It freezes the original fixed-resource methodology, which already lacks the required 2026 index field.

## 4. Approved consequence versus prohibited consequences

| Item | Owner-approved consequence |
| --- | --- |
| Proposed WPU0561 historical-vintage representative pair for v2.1F | **Not admissible** under the original selected 2013 HTML + April 2026 XLSX resources |
| Existing identifier proof for 0561 | Preserved, separate from economic value feasibility |
| v13 PDF and original release comparison | Unresolved; authorization permanently consumed |
| Reconstructed historical values | **None** |
| Research ledger and existing Score formulas | **No modification** |
| Existing public Score CSV/JSON/archives | **No modification** |
| External providers and Production | **No modification** |
| New BLS GET/HEAD/Range, PDF read, alternate source | **Not authorized**; request budget 0 |
| Issue #155 public redistribution | Independent HOLD (not legal clearance) |
| Future Option B research | New owner-approved methodology and one-off request cycle required |

No code should use this document to fabricate an absent observation, remove a live Score driver, replace a published weekly release, or infer licensing from an engineering outcome.

## 5. Governance, issue disposition and future reopening

**Issue #258:** the specific ambiguity-diagnostics lifecycle has reached a documented owner methodological decision. After the protected v16 decision PR merges and all validation gates pass, the issue may be closed **as completed for its fixed-resource research objective**. Closing #258 is **not** evidence of BLS source adoption or rights clearance. Any new BLS source experiment would require a distinct issue, scoped data/provenance method, explicit owner consent, bounded one-use request and independent post-run cleanup.

**Issue #155:** leave open/HOLD. Its broader current-public-Score, provider-derived transformed-value and redistribution analysis remains independent and is not answered by WPU0561 exclusion from the proposed unverified historical pair.

## 6. Rollback and recovery

- Pre-v16 protected-main snapshot: `1c66580dbff811d2ba033254de9df483f62620c9` (which includes unrelated rights-research PR #300). Do not discard newer protected-main work.
- Retain v15 known-good recovery: `backup/score-v2-1f-v15-methodology-2026-10-29` pinned to `381db57df68db8624cc3b03e83ac5a1febd06611`.
- Retain v13 consumed claim `refs/tags/score-v2-1f-wpu0561-pdf-v13-oneoff-2026-10-29` pointing to `82adf0b250871887e82123ed56f641d09fa14ba0`.
- A v16 issue or test failure is repaired with a **new corrective protected PR affecting only v16 governance, guard, tests and associated recovery metadata**. Do not force-push main, delete the original claim, rewrite v15, trigger BLS, or roll back unrelated PRs.
- Git branches are repository-level version references, **not offsite archives, database snapshots or provider-native restoration mechanisms**. This decision does not create or exercise independent provider backups.

## 7. Release acceptance gates

The v16 governance package must pass exact-head release validation, CodeQL, dependency/frozen research checks, and the no-network recovery drill (including the earlier v13-v15 baseline and v16 negative cases) before merge. Then verify protected main, unchanged claim, absent live receipts/dispatch, inert BLS workflow, zero requests, and independent rights HOLD.

**Outcome:** the owner-approved Option A research method is closed under its fixed sources; existing Score, publication rights and Production are unchanged. Any alternative WPU0561 source is a new, separately governed future investigation.
