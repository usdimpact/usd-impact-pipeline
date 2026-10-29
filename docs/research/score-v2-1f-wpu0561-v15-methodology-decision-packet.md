# WPU0561 / Score v2.1F — v15 methodology decision packet

**State: DESIGN-ONLY HOLD. No option has been selected by the owner.**  
Date: 2026-10-29. Research [Issue #258](https://github.com/usdimpact/usd-impact-pipeline/issues/258). Independent rights [Issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155).

## 1. Preserve authoritative evidence

The v9 fixed-resource method demonstrated Crude petroleum -> identifier 0561, but the selected April 2026 direct-commodity XLSX container contained percent-change fields and **no eligible index-level field**. It could not supply the original-release 2013/2026 index-level representative pair.

The separate v13 PDF inspection acquired its exclusive claim and failed closed with reason **invalid_page_count**. The original frozen parser emits the same reason when a PDF page tree has **fewer than one page** OR **more than the original 200-page maximum**. The retained output did **not** identify the exact page count or which branch failed. The PDF's release vintage, Table 9 field, governing WPU0561 row and index basis were not established. The v13 permission is consumed, receipt/dispatch removed, workflow inert, and the claim remains preserved.

The v14 synthetic regression reproduced both possible page-count branches; it did NOT produce a new actual BLS PDF observation. A claim that the April PDF is over 200 pages would be speculation.

Evidence: [one-off run 40924080468](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40924080468), [sanitized original evidence](https://github.com/usdimpact/usd-impact-pipeline/issues/258#issuecomment-6504080848), and [merged v14 review PR #297](https://github.com/usdimpact/usd-impact-pipeline/pull/297).

## 2. Why pagination and series feasibility must be separate

An HTTP HEAD response ordinarily supplies HTTP metadata, **not a verified PDF page-tree count**. A byte-range request is also a provider request and may expose source bytes; it may be insufficient for page count without further ranges. Neither is preapproved. The 10 MiB wire cap is not a complete defense against inflated PDF page objects and decompression memory.

pypdf reads cross-reference tables on reader initialization, while page count comes from the parsed page sequence. Page text extraction is a separate, potentially memory-intensive operation. Source documentation reviewed WITHOUT retrieving the BLS PDF:
- https://pypdf.readthedocs.io/en/stable/modules/PdfReader.html
- https://pypdf.readthedocs.io/en/stable/user/extract-text.html
- https://pypdf.readthedocs.io/en/stable/user/streaming-data.html

**No live request of any method was made in v15.** For a hypothetical future separately authorized diagnostic, classify only: below minimum; above existing cap; within existing cap; or parser failure. Do not return raw PDF text, exact source values, governing row identifiers or an unapproved exact count. Even a within-cap classification would prove only one structural prerequisite, not first-edition provenance or WPU0561.

## 3. Staged methodological gates

| Stage | Independent requirement | Failure response |
| --- | --- | --- |
| D0 — retained historical evidence | Pinned v9-v14 code, consumed claim, exact audit | No additional request; stop |
| D1 — original-release provenance | Primary-source release/edition and corrections evidence proving the exact intended original vintage | HOLD; a URL, timestamp or PDF metadata alone is not proof |
| D2 — pagination and parser isolation | Newly reviewed minimal source-byte budget, cgroup/resource limits and one-use owner approval | Fail closed on zero, >200, error or ambiguity; no automatic limit increase |
| D3 — Table 9 identity | Unique governing unadjusted **index level** header, April 2026 period, direct commodity code/row; reject domestic/stage/extraction aliases | HOLD without values |
| D4 — 2013 versus 2026 comparability | Release vintage, rebasing and index basis reviewed | HOLD without reconstruction |
| D5 — redistribution | Separate legal/licensing/retention decision in Issue #155 | Public Score HOLD |
| D6 — implementation | Independent score-method/security and release approval | No z-score, source replacement, publication or Production |

D0 is complete using retained internal evidence. The other stages are unverified or not authorized. These are **design gates**, not new executable capabilities.

## 4. Owner decision options — not yet selected

**A. Freeze the fixed-resource infeasibility (recommended operational default).** Keep WPU0561 historical-vintage representative index levels unavailable for v2.1F under the original selected April 2026 XLSX. Preserve the identifier proof separately. Do not change any live/public Score component merely by documenting the finding. This path requires no source request and avoids methodological drift.

**B. Pursue a separately approved BLS-first-release research source.** Retain WPU0561 as a candidate only. First document release-vintage immutability, exact row and column semantics, pagination security, deterministic source identity and licensing. Any eventual source request needs a **new explicit owner decision, one-use claim, receipt, reviewed dispatch and cleanup**. Reusing the v8/v13 authorizations, increasing the 200-page limit or broadening BLS searches is forbidden by the current packet.

**C. Continue HOLD.** If source provenance, method or rights cannot be established, retain the research question without Score/public/Production changes.

**Current owner choice:** none. **Nonbinding design preference:** A for the present fixed-resource method, leaving B open only as a separate future investigation.

## 5. Implemented offline governance

- governance/score-v2-1f-wpu0561-v15-methodology-decision.json: precise D0-D6 gates, A/B/C options, false permissions and fixed evidence.
- scripts/score_v2_1f_wpu0561_v15_methodology_guard.py: no-network validator of consumed v13, accepted v14 evidence, unselected owner choice, rights HOLD and absent v15 live files.
- tests/test_score_v2_1f_wpu0561_v15_methodology.py: 32 negative and finite-case tests. Synthetic scenario names are not valid PDF filenames, provider URLs or actual economic values.
- Existing offline recovery CI gains the v15 validation. No extra parser dependency, fetch job, action token or Production workflow is introduced.

Tests explicitly refuse: HTTP GET/HEAD/range, alternate resource, widened page bound, invented original vintage or page count, new economic/identifier field access, a reused claim, owner choice inferred without instruction, and public/Production changes.

## 6. Recovery and boundaries

The pre-v15 recovery ref backup/score-v2-1f-v14-offline-2026-10-29 is pinned to 2e028a553132c94db64ed9ba88927957374c2b1f. Preserve the original v13 consumed claim and earlier v9-v13 Git recovery branches.

The new work begins after protected main acquired separate Treasury and Score rights/retention changes; do not overwrite those updates. If any v15 tests fail, fix or revert **only v15 design, test and CI scope** through a reviewed corrective PR, preserving protected main and source governance. Git recovery references do not constitute offsite or provider-native backups.

No BLS PDF, exact page count, economic or numeric identifier values, historical reconstruction, Score computation, research-ledger mutation, public artifact replacement, provider restoration or Production deployment was performed or authorized under v15.

**Final methodology status: HOLD pending a separately expressed owner choice.**
