# Score v2 aggregate-public prototype — synthetic contract hardening (2026-10-30)

**Status: OFFLINE / NON-PRODUCTION / RIGHTS HOLD.** This work changes the dormant aggregate-only converter, its JSON Schema, and synthetic tests. It does not change Score v2 mathematics, weights, source transport, real historical provider values, any Cloudflare Pages/public routes, frozen research engines, private real-evidence retention policy, or the binding publication gate. The prototype MUST NOT be used to publish Score data without separate written rights and explicit owner Production authorization.

## Why now

Review of the [older aggregate-safe prototype](score-public-safe-prototype-2026-10-27.md) found that the previous assertion blocked known provider-specific field names and checked history-row field sets. It did **not** reject:
- unreviewed root/metadata/latest fields;
- NaN or Infinity in weekly Scores or methodology weights (Python's default JSON writer can serialize non-standard NaN);
- forged aggregate history hashes, latest weekly changes or metadata row counts;
- malformed/non-Friday/duplicate/reordered week-ending dates;
- changed methodology weights, pipeline ID or inconsistent regime labels;
- CSV-injectable text in a free-form regime field.

The previous JSON Schema also permitted arbitrary numeric weight names even though the frozen methodology has **eight exact signed weights**. The prototype schema now specifies exactly those weights and the five frozen regime labels.

## Fail-closed prototype validation

The inactive converter still selects **only** aggregate date, Score and regime from supplied inputs, with no component numbers. The strengthened aggregate assertion now:
1. Requires exact top-level, metadata, latest, evidence, weights and history-row keys and reviewed schema version;
2. Rejects non-finite/boolean scores and weights, and extremely large non-convertible integers;
3. Validates Friday calendar dates, strictly increasing weekly order, frozen weights and exact regime bands;
4. Recalculates latest date/Score/regime, one-week and four-week change against the aggregate history;
5. Verifies SHA-256 of canonical aggregate history;
6. Checks UTC timestamp or null for review-only synthetic metadata;
7. Checks payload **before creating output directories**; JSON output uses strict finite serialization.

This is **technical exposure and format assurance only**. It does not prove an aggregate is non-invertible or license-cleared, and does not make the original Score or its derivatives legally distributable.

## Synthetic-only acceptance

The new adversarial tests use fictional 2099 dates and invented Score/regime rows only; they read no live provider source, historical Score JSON, private data, or online service. Existing repository-wide legacy tests may read already committed Score files; no new observations are fetched.

Tests cover positive format/CSV parity, forbidden fields, NaN/Infinity, giant integers, boolean scores, invalid/non-Friday/non-increasing dates, fake formula strings, false regime labels, schema and hash tampering, changed weights/pipeline, wrong UTC metadata, invalid latest changes, output-before-validation, and no provider imports.

## S&P no-budget outcome

In existing S&P Dow Jones Indices case **#01036004**, a commercial representative replied in writing on 2026-10-29 that USD Impact's submitted commercial/aggregate use case **requires a paid license**. USD Impact has confirmed **no budget**. This blocks the frozen **S&P 500-derived component and proposed aggregate product** under the current budget. It does not establish that every independent new model requires an S&P license or that historical uses were unlawful.

Consequently:
- Do **not** deploy or market the dormant aggregate-only Score v2 output, even after engineering tests pass.
- Do **not** book a paid-license sales call, purchase, change original sources, or substitute the separate four-government-signal study into the 617-week historical Score.
- Keep Issue #155 OPEN, the v1 publication gate HOLD, and Yahoo/ICE/CME/Cboe/FRED/Treasury/BTC provenance and archive rights independently unresolved.
- A separately named new methodology may be explored in synthetic-only mode pending explicit source rights and owner approval.

No private email bodies, sender contact details, credentials, quotes or provider-market observations appear in this document.

## Scope and acceptance

Exactly four files change:
- scripts/build_score_public_safe_artifact.py
- schemas/score_public_safe.schema.json
- tests/test_score_public_safe_contract_synthetic.py
- this document.

Require exact-head protected quality, frozen-research checks, CodeQL and dependency audit before merge; skip Pages deployment; verify merged status and Git recovery references; record Issue #155 non-approval evidence.

**Authority boundary:** This document does not grant legal or publication permission. No live workflow uses it as authorization.
