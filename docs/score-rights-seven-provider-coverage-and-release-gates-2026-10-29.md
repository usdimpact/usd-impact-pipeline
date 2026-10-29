# USD Impact Score v2 — Seven-provider decision coverage and release blockers

**Recorded 2026-10-29. Issue #155 remains OPEN / HOLD.** This is a technical decision-coverage audit, not a counsel opinion, new license, source switch, public schema approval, or deployment authorization. No real market observations or current/historical Score data bodies were downloaded for this work.

Research tracking: https://github.com/usdimpact/usd-impact-pipeline/issues/155

## 1. A missing decision relationship in the older approval draft

The original governance/score-rights-decision-receipt.template.json lists **five** provider dispositions: Yahoo/yfinance transport, S&P Dow Jones Indices, Cboe, CME and FRED.

The newer October 29 source rights queue records **seven** distinct source/transport relationships, adding:
- **ICE / USDX (DXY)** as the owner of the named dollar index, separate from Yahoo delivery;
- **Direct U.S. Treasury / Federal Reserve H.15 outputs** as potential upstream government-publisher/republication sources, separate from FRED transport-specific terms.

These are not two newly approved providers; they are **two source relationships that a future approval review must not omit**. Seven is the current documented inventory, not proof every upstream contributor or BTC exchange-data owner has been identified. Exact instrument, source owner, route and agreement remain open counsel/provider questions.

The legacy five-row decision template is frozen at its current Git blob, retains HOLD, and cannot constitute a complete release receipt. It should not be silently edited to imply an earlier approval. A future successor receipt must be separately versioned and independently reviewed for all seven relationships and each use dimension: commercial retrieval, transient calculation, private retention/backup/disposal, public aggregate, public components, historical archive treatment, attribution and automated access.

The canonical review state is governance/score-rights-seven-provider-coverage-2026-10-29.json. It pins all seven relationships and eight field-level dimensions, every field UNAPPROVED. FRED's existing conditional answer is classified as limited transient processing for suitably tagged public-domain datasets with citation and disposal, NOT approval for storage, aggregate publication or the whole pipeline.

## 2. Public artifact footprint and historical preservation

A prior metadata-only Git tree inventory identified **54 current-tree Class C files**: 50 dated and four current, across 27 dated directories. E and F include diagnostics and revision research; B/D involve methodology and aggregate provenance; A contains aggregate or operational paths. None is a new approved treatment.

Those 54 and 27 counts are date-stamped repository metadata, NOT proof that all routes are currently reachable, that each is a legal violation, or that prior Git versions, caches or external backups are clean. The separate Pages audit identified 1,921 deployment records, NOT 1,921 established disclosures. See https://github.com/usdimpact/usd-impact-pipeline/blob/main/docs/score-public-archive-metadata-preservation-2026-10-29.md .

Do not redact files, delete old archives, purge Pages/CDN caches, migrate real provider data into the synthetic-only Development storage bucket, rewrite Git history, or change research consumers until preservation rights, retention and a reviewed release/restore plan are approved. Git source snapshots are not independent offsite or provider backups.

## 3. The latest no-added-license study is not an eight-driver substitute

PR #302 (https://github.com/usdimpact/usd-impact-pipeline/pull/302) merged on 2026-10-29 at commit 8402573f57413aa8ba84dbd15c85e57e0e5f965b. It found **no verified zero-additional-cost, commercial-license-cleared, equivalent eight-driver replacement**. Direct Treasury government outputs may be promising but source parity, as-of availability and rights remain unverified. Federal Reserve H.10 dollar and EIA crude inventories are not ICE DXY and CME WTI futures; their publication lags would invalidate unchanged Friday-as-of semantics.

EIA spot histories may include data acquired from Refinitiv with publication permission, not downstream sublicensing. Free crypto/public research APIs do not imply rights for commercial derived outputs. A four-government-signal study is a **separate model research direction**, NOT a live Score v2 source switch and not approval to recalculate or splice its historical 617-week series.

## 4. Correspondence status and no-duplicate-contact control

A targeted read-only October 29 Gmail search found the earlier conditional FRED response, the S&P sales referral and Cboe sales/no-fee clarification conversation. It did NOT establish a new affirmative signed commercial/public-derived rights grant. This work did not send email, reopen vendor cases, request confidential identity details, purchase services or publish private correspondence. A sales referral does not create a rights license. Keep the existing follow-up queue and avoid duplicate cases.

## 5. Fail-closed approval requirements

1. Seven documented upstream source and transport determinations, scoped per instrument, with any subsequently discovered original owners added by separate review.
2. Written disposition for internal use, retention/deletion, public aggregate, component transformations, historical archives, public metadata and attribution, including treatment of old distributed copies.
3. FRED conditional use clarified without inferring retention rights.
4. Owner/counsel-approved A–F public schema and legally accurate replication wording. An aggregate-only prototype is not automatically publishable.
5. Lawful access-controlled real evidence retention route, or explicit decision that retention is prohibited and a compatible audit/remediation plan.
6. Private consumer migration for Score v2 predictive, v3 shadow, vintage/robustness research and weekly reproducibility before any public component reduction; validate member and public website readers.
7. Historical Git/Pages/CDN/backup retention and if instructed lawful redaction with a rollback that will not republish restricted fields.
8. Exact-head CI, non-Production preview, anonymous/authenticated endpoint testing and distinct owner Production authorization.

If any is incomplete, Issue #155 remains HOLD. A passing synthetic test or a provider sales referral is not a positive publication decision.

## 6. Offline protection added

The new scripts/validate_score_rights_seven_provider_coverage.py inspects **only local committed governance and review JSON**. It does not read public market-value files, PDFs, Gmail, storage or provider services. It verifies the old template's unchanged five-row HOLD blob, seven exact relationships including ICE and direct Treasury, non-approved field and A–F classes, public/private/Production gates, zero-license study, historical metadata-only inventory and no live actions.

The new tests/test_score_rights_seven_provider_coverage.py runs negative tests on invented local copies, rejecting missing relationships, FRED over-generalization, false provider grants, historic archive deletion permission, template rewriting and Production activation. The existing unprivileged Weekly score quality workflow discovers these Python tests; no new live workflow or credential is introduced.

**Next authority boundary:** obtain a written seven-source/field class and historical preservation decision, then draft a separately reviewed successor decision receipt, consumer/schema migration and release plan. Nothing here grants source rights or authorizes an actual public replacement.
