# Score v2.1F / WPU0561: v14 page-count forensics and methodology review

**State: OWNER-APPROVED DESIGN ONLY / HOLD.** Dated 2026-10-29. No new BLS PDF request, parser retrieval, original-release proof, source substitution, page-limit change, numerical observation, reconstruction, public output or Production deployment.

Research: https://github.com/usdimpact/usd-impact-pipeline/issues/258  
Independent rights HOLD: https://github.com/usdimpact/usd-impact-pipeline/issues/155  
Consumed one-off run: https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40924080468  
Original sanitized evidence: https://github.com/usdimpact/usd-impact-pipeline/issues/258#issuecomment-6504080848  
v13 terminal cleanup: https://github.com/usdimpact/usd-impact-pipeline/pull/292  
Pre-v14 recovery pin: backup/score-v2-1f-v13-consumed-2026-10-29 at 1ed8934b5e99e493606a0d23dd4206a6f5f9fe76.

## 1. Evidence: what the v13 result means

The reviewed v13 activation and dispatch acquired the exclusive pre-HTTP Git claim. Its PDF structural parser subsequently failed closed with reason **invalid_page_count**. The preflight authorization was consumed even on failure. Cleanup removed the active receipt/dispatch, disabled the workflow, and preserved the claim tag. The retained issue audit reports zero numeric identifier/economic values retained and no Score, research-ledger, public or Production changes.

The source at scripts/score_v2_1f_wpu0561_pdf_v13_parser.py checks the following after PdfReader initialization:

    count = len(pdf.pages)
    if count < 1 or count > MAX_PAGES:
        return result({"invalid_page_count"})

The historical MAX_PAGES ceiling is 200. The outcome is therefore compatible with **two alternative conditions**: the parser reported fewer than one page, OR more than 200 pages. No actual number or bound-specific reason was retained. Reader construction/count exceptions would have emitted a *different* reason, pdf_load_failed.

| Invented page-count case | Existing v13 behavior | Inference about actual BLS PDF |
| --- | --- | --- |
| 0 fake pages | invalid_page_count, no page scan | None; compatible with the observed failure |
| 1 fake page | Count passes; missing-schema HOLD on blank mock | None |
| 200 fake pages | Count passes; missing-schema HOLD on blank mocks | None |
| 201 fake pages | invalid_page_count, no page scan | None; also compatible with the observed failure |
| Simulated reader exception | pdf_load_failed | Separates parser exception from the observed page-count code |

**Result:** this is evidence the page-count guard operated, not evidence that the actual BLS report had more than 200 pages or has an invalid WPU0561 source series. The prior PDF content and original-release vintage remain unverified for the required Table 9 observation.

The official pypdf documentation describes PdfReader.pages as a sequence supporting length, and says page text extraction parses the whole page content stream with possible substantial memory amplification. A future cap review needs a separate parser/cgroup/byte-security review; merely increasing 200 would not be an acceptable remedy.

Sources: https://pypdf.readthedocs.io/en/stable/modules/PdfReader.html and https://pypdf.readthedocs.io/en/stable/user/extract-text.html

## 2. Additional parser risks, not explanations of the v13 failure

1. **Repeated Table 9 headings:** the existing parser counts a Table 9 heading on every page where it reappears. A valid table that continues over pages can repeat its title. The parser currently fails closed on repetition; any change to table-continuation semantics needs separate, deterministic tests and approval.
2. **Lexical rather than series identity:** crude-petroleum phrase detection is not an exact row-code/series identity proof. Numeric identifier inspection was excluded by the prior authorization; an apparently matching text phrase cannot establish the proper WPU0561 concept or resolve the *Crude Petroleum (Domestic Production)* naming ambiguity.
3. **Field/period linkage:** the Table 9 title, an unadjusted-index phrase and a crude label anywhere within a scanned section are not sufficient to establish one governing header and unique correct observation cell for April 2026.
4. **Historical edition:** an archive link and dated May 2026 news release do not prove the currently hosted PDF remains the unchanged original-release vintage. Check revisions, corrections and basis separately.
5. **Public rights:** source feasibility never overrides Issue #155 HOLD or grants redistribution rights.

The actual v13 run stopped at page count, before any successful Table 9 schema or row validation. These are *future-stage risks*, not observed failures.

## 3. v14 offline testing and protections

New source: governance/score-v2-1f-wpu0561-v14-pagecount-forensic-design.json and scripts/score_v2_1f_wpu0561_pdf_v14_offline_diagnostics.py. The latter reads only committed governance files and runs invented integer boundary cases.

New tests: tests/test_score_v2_1f_wpu0561_pdf_v14.py. Dependency-free cases verify claim consumption, zero request budget, absent v8/v13 receipts/dispatch, inert v13 workflow, rights HOLD and no inferred page count. The isolated pinned-pypdf CI job additionally uses fake PdfReader page trees of 0, 1, 200 and 201 pages and an exception case to demonstrate the actual existing v13 parser branches. All inputs are invented. **No BLS PDF URL, file, byte stream or economic value is used for these mock cases.**

A passing mock test is NOT a real PDF structural observation, nor authorization to adopt a source or modify any Score.

## 4. Methodology decision alternatives

**A. Keep v9's existing fixed-resource infeasibility.** The selected April 2026 XLSX container has no eligible index-level field. Exclude WPU0561 from v2.1F under this fixed boundary; retain the earlier Crude petroleum to 0561 identifier proof without mistaking it for value feasibility. This is already consistent with the governance and needs no new BLS request.

**B. Prepare a new v15 methodology gate, not a retry.** Only if preserving WPU0561 is necessary, first review whether a minimal official provenance or page-status observation can distinguish the 0-versus-over-200 hypotheses without new economic-value reads. Specify why the existing 200-page cap is scientifically inapplicable before proposing any change. Preserve the single official primary-source path, independent first-release proof, parser security and memory bounds, concept identity and series basis. A new one-off live request would require a NEW explicit owner approval, activation receipt, dispatch, non-reusable claim and terminal cleanup. The v8/v13 approvals and claims remain consumed.

**C. Continue HOLD.** If original-release provenance, exact series/field identity, safe parser method or rights cannot be established, do not retry, broaden the source, reconstruct values or change public Score outputs.

**Recommended next decision:** formally review A versus B on v14's offline evidence. Do not turn the approval for v14 *design research* into a new PDF retrieval, a higher page bound, a source substitution, or a right to read economic values.

## 5. Recovery and release boundary

- Preserve the GitHub tag associated with v13 consumption and its linked audit. Never delete, move, or reuse it.
- Preserve the known-good v13 cleanup SHA and pinned v9–v13 recovery branches; v14 changes remain separately reviewable.
- A failing design PR should be corrected/reverted on a review branch via normal protected GitHub PR, not forced into main.
- A future live v15 request must have an independent one-use authorization. Git rollback cannot undo already executed external HTTP requests.
- The Git recovery references are NOT offsite repository archives or independent Supabase, Vercel, Cloudflare, Resend, Render and provider backups. None have been restored under v14.

**Release result: design-only, no new BLS request, zero request budget, Issue #258 and Issue #155 HOLD, and no Score or Production change.**
