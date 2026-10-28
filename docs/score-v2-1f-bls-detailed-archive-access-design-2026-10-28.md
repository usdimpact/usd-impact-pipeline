# Score v2.1F — BLS Detailed Report archive alternative (offline design only)

**Date:** 2026-10-28  
**Status:** DESIGN ONLY / NO LIVE RESEARCH / RIGHTS & PRODUCTION HOLD.  
**Controls:** [Pipeline #228](https://github.com/usdimpact/usd-impact-pipeline/issues/228) (BLS archive HTTP 403), [#155](https://github.com/usdimpact/usd-impact-pipeline/issues/155) (public/paid redistribution), [consumed Stage 1 approval](https://github.com/usdimpact/usd-impact-pipeline/blob/56aa8b97922266be88c2f74ebf2659a48a8abede/governance/score-v2-1f-live-vintage-preflight-consumption-2026-10-28.json).

## What the authorized preflight established

The original fixed [BLS archived-news index](https://www.bls.gov/bls/news-release/ppi.htm) returned HTTP **403 to the authorized GitHub Actions runner**. The preflight stopped before computing any v2.1F Score or persisting component values. The one-off approval and dispatch have since been consumed and removed. Their owner authorization **must not be reused**.

The Federal Reserve H.10/H.8/H.4.1 sampled archive phase completed before that error; this does not prove full 2013–2026 historical coverage or BLS PPI feasibility.

## A different, documented BLS archive family worth investigating

BLS separately documents its [Producer Price Index Detailed Report archive](https://www.bls.gov/ppi/detailed-report/), described as **2005 onward**, with monthly historical reports and **tables of all PPIs released in each month**. Its [PPI FAQ](https://www.bls.gov/ppi/faqs/questions-and-answers.htm) describes the Detailed Report as the most comprehensive monthly PPI publication, issued at the same time as the news release. This makes it an *official-source documentary candidate* for reconstructing the WPU0561 release-time record.

This evidence **does not prove** that the exact WPU0561 row is present and machine-parseable for each required month, that a PDF/XLSX historical report is a complete vintage for the requested series, that the document's original release timestamp can be recovered, or that the GitHub Actions runner can retrieve either the index or report assets. The archived index also describes PPI revisions for four months, seasonal-factor revisions and recoding, so **latest revised BLS history is not a valid substitute**.

As a documented exception, the Detailed Report archive marks **October 2025 as not available**. Under the frozen v2.1F Friday cutoff and 45-day BLS release-staleness rule, a missing or delayed release must be classified according to the preregistration. No invented release date, proxy or carry-forward may be introduced to rescue a failing window.

The direct official **PPI archive news release** remains a separate candidate family, but it is the original blocked index and should not be retried without fresh approval. There is no evidence here that changing a User-Agent, retrying 403s, adding credentials, using a mirror, or requesting a different host would be legitimate.

## Synthetic-only deliverable

`scripts/rehearse_score_v2_1f_bls_detailed_archive_design.py` contains a **pure offline HTML link inspector**. It accepts caller-provided fabricated HTML and fabricated HTTP status codes; it cannot open URLs or read external files. It rejects non-HTTPS, non-BLS hosts, userinfo/queries, encoded or traversal paths, unsupported file types, duplicates, and all simulated non-200 HTTP statuses. Synthetic PDF/XLSX link output is labelled **DESIGN_CANDIDATES_ONLY**, never "historically verified" or "source approved".

The companion `tests/test_score_v2_1f_bls_detailed_archive_design.py` exercises the official-host boundary, the original 403 fail-closed response, missing month, duplicate/unsafe links, non-network imports and all negative authorizations. **The fabricated URLs are deliberately non-existent; tests never access any BLS record or source value.**

The machine-readable governance metadata is at `governance/score-v2-1f-bls-detailed-archive-design-2026-10-28.json`. It preserves all approval flags as false. This is an optional design aid, not an extension of the frozen v2.1F preregistration or of its consumed source authorization.

## Required decisions before any live feasibility request

1. **Owner/source authorization:** record a *new* narrow authorization listing the exact official BLS Detailed Report index/asset path, allowable redirects (conservatively none), historical window, and ephemeral source policy. Issue #224's prior consumed receipt does not apply.
2. **Transport test:** in an authorized isolated run, first verify whether the alternate BLS index and sample PDF/XLSX assets are reachable from the actual runner. A 401/403/redirect remains a hard stop, not a reason to evade.
3. **Vintage evidence:** verify exact release timestamp of each candidate document, WPU0561 row/code lineage, initial and four-month revised vintages, recoding/errors, and Friday 23:59:59 America/New_York eligibility. Index month labels alone are insufficient.
4. **Acceptance:** apply the already frozen coverage/recency/missing-week thresholds and preserve non-value-bearing aggregate evidence only. Do not use unapproved FRED, ALFRED, Treasury, current revised BLS or H.15 proxies.
5. **Subsequent study:** even if feasibility passes, a *second independent owner approval* is required before candidate Score computation. Data-distribution rights under #155 and separate Production release approval are different decisions.

**Nothing in this Draft retrieves live data, changes the v2.1F design, enables a workflow, modifies a Score, touches public/provider-derived artifacts, alters subscriptions or entitlements, or deploys Production.**
