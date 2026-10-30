# Score v2 public-schema and historical-retention decision packet — 2026-10-30

**Status: DRAFT / SYNTHETIC ONLY / ORIGINAL SCORE AND MACRO PANEL HOLD.** No provider permission, counsel decision, Production build, archive change, deletion, migration, new storage, or public Score release is authorized by this document or by passing its tests. This is a unified decision handoff for [Issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155) (public redistribution) and [Issue #282](https://github.com/usdimpact/usd-impact-pipeline/issues/282) (FRED delivery, downstream retention and disposal). The **independent Macro Context Panel** is a separate methodology, governed by [Issue #313](https://github.com/usdimpact/usd-impact-pipeline/issues/313), and remains HOLD.

## Why this packet exists, without duplicating prior engineering

A dormant aggregate-only prototype and versioned schema **already exist**:
- [Versioned JSON Schema](../schemas/score_public_safe.schema.json): \`score-public-v2-safe-1\`.
- [Non-production aggregate converter](../scripts/build_score_public_safe_artifact.py), with [synthetic-only adversarial tests](../tests/test_score_public_safe_contract_synthetic.py).
- [Synthetic schema hardening record](score-public-safe-synthetic-schema-hardening-2026-10-30.md) and [private research/public output migration map](score-public-safe-research-migration-map-2026-10-28.md).

These prove a **technical** narrow-payload transform, **not** legal clearance or a safe-live-publication contract. In particular, the existing S&P Dow Jones Indices correspondence states that the submitted commercial/aggregate use requires a paid license; no paid-data budget is approved. Keeping an aggregate Score rather than component values **does not remove that requirement**. No alternative source should silently replace the frozen eight-driver Score or its 617-week historical record.

This packet adds a **machine-readable decision-and-retention bridge**, [governance/score-v2-public-schema-retention-review-2026-10-30.json](../governance/score-v2-public-schema-retention-review-2026-10-30.json), instead of introducing a rival schema. New tests ensure that its candidate fields agree with the pre-existing versioned prototype and that all review/authority gates remain closed. The currently public Score data files are **not changed**, redacted or copied by this PR.

## Candidate public schema — fields are *proposed*, not approved

Version: \`score-public-v2-safe-1\`. This is a standalone draft JSON Schema, **not an active endpoint**. A future public route, filename/version compatibility strategy and rollback are **undecided**.

| Proposed object | Reviewed candidate fields | Open decision |
| --- | --- | --- |
| Root | \`schema_version\`, \`metadata\`, \`latest\`, \`history\`, \`release_evidence\` | Public API version and consumer contract |
| Metadata | \`pipeline\`, \`generated_at_utc\`, \`n_weeks\`, \`weights\` | Public methodology/attribution and aggregate-derived metadata |
| Latest | \`week_ending\`, \`score\`, \`regime\`, \`week_over_week_change\`, \`four_week_change\` | Public derived/aggregate outputs, date labels, revision interpretation |
| History row | \`date\`, \`score\`, \`regime\` | Rights to distribute historical aggregate sequences |
| Integrity | \`aggregate_history_sha256\` | Whether fingerprints are permitted and non-disclosing in this context |

Even published **weights**, aggregate labels, dates, calculated differences and fingerprints may require separate provenance/rights/consumer review. No field above is declared license-cleared. The prototype forbids provider source URLs/identifiers, component weekly levels, normalization moments, per-driver z-scores/contributions and revision diagnostics. These exclusions reduce technical exposure but **do not grant the right to publish the remainder**.

### Current schema is still dormant

There is no Production public URL chosen, no route switch, no Pages allowlist change and no new public JSON/CSV created. Passing the new tests must not be interpreted as a production-ready release, consent to use data already in Git, or permission to fetch fresh observations.

## Historical artifact decision inventory — metadata and known paths only

The authoritative current-tree path/count checkpoint is [the frozen exposure inventory](../governance/score-current-tree-exposure-inventory-2026-10-29.json), reconciled with [the Oct 30 source/retention delta](score-155-282-readonly-exposure-retention-delta-2026-10-30.md). **No component-value file bodies were read or copied to create this packet.**

| Class / carrier | Existing path family | Count in the verified current-tree snapshot | Disposition |
| --- | --- | ---: | --- |
| C — current machine-readable | \`public/data/usd_impact_score_v2.{json,csv}\`, \`public/data/weekly_input_latest.json\`, \`public/data/score_repro_bundle_latest.json\` | 4 | No change; provider-derived output rights unresolved |
| C — dated Score | \`public/archive/YYYY-MM-DD/score.json\` | 27 | No change; dated Git and Pages review needed |
| C — dated bridge | \`public/archive/YYYY-MM-DD/weekly_input.json\` | 14 | No change; per-driver values/provenance review |
| C — dated strict reproduction | \`public/archive/YYYY-MM-DD/repro_bundle.json\` | 9 | No change; levels/moments/receipts review |
| Git-only weekly bridges | \`data/weekly_input_*.json\` | 15 | Not protected merely because outside \`public/\`; repository is public |
| Dated HTML | \`public/archive/YYYY-MM-DD/{en,es}.html\` | 54 | Public Git objects; current Pages HTTP 403 does not revoke Git access |
| D/E/F research | Current public research point-in-time/robustness/vintage JSON, CSV and HTML | 1 / 1 / 3 | Aggregate and component-derived research require distinct rights review |

**Reconciliation:** 27 + 14 + 9 = **50 dated Class C**, plus 4 current = **54 Class C**. Counts concern **current-tree metadata**, not legal outcomes, all old commits, all deployments, clones or downloads. No claim of exhaustive historical distribution follows from them.

Other source/residue categories in the machine-readable draft have unknown or partial inventory status: old Git blobs/refs; past Cloudflare Pages deployments, previews and CDN caches; GitHub Actions logs, artifacts and caches; local \`_daily_cache.parquet\`, logs and runner-temporary matrices; external backups/clones; and any real-data private research evidence. These require **discovery and lawful treatment decisions**, not a speculative deletion or fresh backup.

The [source-retention policy](source-retention-policy.md) distinguishes originating Treasury/H.15 data from **FRED as the delivery service**. The 2026-10-29 FRED correspondence and public terms distinguish commercial use from **storage, caching, archival, distribution/derivative and AI/ML restrictions**. A public-domain series label is not permission to retain delivered records. Exact treatment of aggregate transformations, cryptographic receipts, Git history, old CDN copies, backups and historic logs remains pending legal/provider guidance. Historical removal also cannot be assumed to clear third-party copies.

## Explicit owner/counsel decisions still required

The new manifest holds each question at \`PENDING\` with a null receipt:

1. Exact originating owner, upstream series and transport rights for all eight inputs, including Yahoo/yfinance, ICE, CME, Cboe, S&P DJI and the Treasury/H.15–FRED distinction; separately determine permitted commercial computation, derivatives and redistribution.
2. Determine a lawful path for the **currently unfunded S&P license requirement** or explicitly scope a different *independent* methodology. Do not relabel a new study as the original Score or splice its history.
3. Decide whether any aggregate Score, regime, historical series, methodology/weight field, fingerprint or source-attribution statement may be publicly distributed.
4. Decide FRED Services/API retention, disposal, transient processing, hashes and derived-output treatment, including historic local runner files, logs and GitHub artifacts. Distinguish public-domain labels and separate H.15 publisher terms from FRED delivery conditions.
5. Decide preservation-versus-disposal and lawful rollback treatment for current Git, older commits, Pages deployments, CDN caches, inaccessible mirrors, backups and possible private evidence. **No copying or deletion first.**
6. Confirm Score v3/predictive research and member/site readers can function without component evidence in public paths, and correct any public replication claims that depend on data that would cease to be openly provided.
7. Approve an exact versioned public route, non-Production preview, protected CI, and later a separately signed Production release *only after* rights and retention approval.

Approvals are separate: **provider/transport license**, **historical retention and lawful disposal**, **field-level aggregate publication**, **private evidence boundary or permitted absence of retention**, **consumer migration**, **non-Production preview**, and **owner Production authorization**. A binary legal answer about FRED does not authorize use of unrelated S&P, Cboe or CME data. An approved research design does not authorize an external public launch.

## Future controlled sequence, *not* commands for this PR

1. Resolve provider/counsel question receipts and select lawful storage or disposal for old evidence. Do not infer permissions from engineer tests or an unverified source owner.
2. Review a final field list and versioned URL against allowed output rights and present/future consumers. A schema is only an engineering candidate until that review.
3. If permitted, build a private evidence migration with a no-copy option where retention is disallowed; preserve the frozen original engine/weights and preregistered research contracts.
4. Prove equivalence and public-path redaction on **synthetic/no-egress** data. Ensure old, allowed legacy paths and historical indexes cannot inadvertently republish the old Class C/E/F material.
5. After separate owner authorization, review a non-Production deployment with privacy/security checks, legal-safe rollback and exact-head CI. Production, CDN invalidation, Git history treatment, source-provider requests and any publication restart each require their own explicit gate.

## Draft PR acceptance and non-actions

This review changes only **one governance JSON, this documentation, and one offline stdlib test module**. It must pass exact-head [release quality](../.github/workflows/quality.yml) and applicable security checks. The Python tests read only the **existing versioned JSON Schema, policy/manifest text, and synthetic invented 2099 rows**. They never read real Score artifacts, parse restricted source observations, fetch providers, or write public files.

**No rights grant or activation:** keep \`governance/score-publication-rights-gate.json\` at \`hold\` with null receipt. No frozen engine/reproduction-builder code, original model/weights, provider adapter, public-path allowlist, scheduled workflow, real evidence, historical archive, service setting, entitlement, billing, Domain, or Production change is part of this draft.
