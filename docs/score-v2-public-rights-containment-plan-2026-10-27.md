# Score v2 public-rights containment plan — 2026-10-27

Status: **REVIEW-ONLY DESIGN. NO PRODUCTION OR SCORE-METHODOLOGY CHANGE AUTHORIZED.**

Related governance issue: #155.

## Objective

Preserve the USD Impact Score v2 calculation, aggregate score history, regime history and public educational value while reducing the public redistribution surface for provider-derived market data until provider/counsel rights are confirmed.

This plan is deliberately separate from Three Dials v2. Three Dials has its own rights-safe primary-source contract and must not be used as implied approval for Score inputs.

## Current public-data inventory

### Public aggregate/product outputs

These are the intended public product outputs and should remain public unless separately changed:

- date;
- aggregate Score;
- regime;
- aggregate score history;
- methodology/version;
- fixed weights and regime bands;
- educational English/Spanish dashboards;
- non-value-bearing release/code/dependency fingerprints.

### Current provider-derived public outputs requiring rights review

1. `public/data/usd_impact_score_v2.csv`
   - full 617-week component z-score history for all eight drivers;
   - aggregate score and regime.

2. `public/data/usd_impact_score_v2.json`
   - full per-driver z-score history;
   - current source provenance, provider names, series/tickers and source URLs.

3. `public/data/weekly_input_latest.json`
   - latest per-driver z-score;
   - weight;
   - contribution;
   - provider/ticker provenance.

4. `public/data/score_repro_bundle_latest.json`
   - current weekly provider-derived level for each driver;
   - normalization sample mean/std;
   - unclipped/clipped z-score;
   - contribution;
   - exact provider/ticker provenance;
   - daily/weekly value-history hashes.

5. `public/archive/<week>/...`
   - historic copies of the above release artifacts.

6. Research/prospective material under public or repository-visible paths may also contain source weekly levels and must be inventoried before any claim that public exposure is limited to the primary Score files.

## Rights-risk boundary

This document does not determine legal rights.

Engineering should assume the public per-driver values/derivatives are **not cleared for external redistribution** until a provider/counsel record says otherwise.

Reasons for conservative treatment include:

- yfinance documentation says the Yahoo Finance API is intended for personal use and defers actual-data rights to Yahoo terms;
- S&P Dow Jones Indices public terms restrict redistribution and creation of derived data without express written consent;
- Cboe index-data materials describe redistribution/licensing requirements for index data;
- CME market-data policies contain separate redistribution and derived-work conditions.

The fact that a value is transformed into a z-score, contribution, normalization moment or derived research target does not by itself establish redistribution permission.

## Target architecture

### Public schema: `score-public-v2-safe`

A public release should contain only the minimum Score product fields:

```json
{
  "schema_version": "score-public-v2-safe-1",
  "latest": {
    "week_ending": "YYYY-MM-DD",
    "score": 0.0,
    "regime": "Neutral / transitional",
    "week_over_week_change": 0.0,
    "four_week_change": 0.0
  },
  "history": [
    {
      "date": "YYYY-MM-DD",
      "score": 0.0,
      "regime": "Neutral / transitional"
    }
  ],
  "methodology": {
    "version": "usd_impact_score_v2",
    "weights": {},
    "regime_bands": []
  },
  "release_evidence": {
    "pipeline_git_sha": "...",
    "requirements_lock_sha256": "...",
    "aggregate_history_sha256": "..."
  }
}
```

Public CSV should be reduced to:

```text
date,score,regime
```

No public-safe artifact should contain, absent documented rights:

- provider-derived weekly levels;
- per-driver z-scores;
- per-driver contributions;
- normalization means/std;
- exact Yahoo tickers/source URLs if provider/counsel requires a different attribution boundary;
- a field claiming that no provider-derived values are public when another section publishes such values.

### Internal/private release evidence

The current strict reproduction purpose still matters. Preserve it through a non-public evidence bundle containing:

- complete weekly input snapshot;
- current provider-derived weekly levels;
- normalization moments;
- per-driver z-scores/contributions;
- provider/ticker provenance;
- daily/weekly matrix fingerprints;
- pipeline/dependency hashes.

This evidence must not be placed under a public web root, public Pages artifact, public Git path, PR log or unrestricted repository artifact unless the relevant rights are confirmed.

The private storage/access/retention mechanism requires a separate design/approval. This document does not authorize a new paid storage service or secret.

## Critical dependency: research and predictive workflows

Current Score v3 shadow/predictive tooling references public strict reproduction bundles, including fields such as:

- `bundle.components.DXY.weekly_level`;
- other `components.*.weekly_level` values;
- strict bundle latest/archive paths.

Therefore public redaction cannot be implemented by simply deleting bundle fields.

Before public schema migration:

1. identify every research/predictive reader of public Score artifacts;
2. introduce a logically separate internal evidence input;
3. prove research output is byte/metric-equivalent for the same frozen fixture;
4. remove research dependence on public provider-derived fields;
5. only then reduce the public artifacts.

No predictive protocol, holdout definition or Score v3 frozen research rule may be silently changed as part of rights containment.

## Phased migration

### Phase 0 — hold and inventory

- [x] Create governance issue #155.
- [x] Inventory principal current public value surfaces.
- [x] Inventory repository-visible research/prospective exposure at the current main:
  - 8 `research/prospective/score_v3_shadow_*.json` records contain `source_weekly_levels` for all production drivers;
  - 8 `research/predictive/score_v2_predictive_week_*.json` records contain `dxy_weekly_level`;
  - dated public strict reproduction archives from the strict-release period expose provider/ticker/weekly-level evidence.
- [x] Record principal code dependencies on public per-driver fields:
  - Score v3 shadow ingestion and Score v2 predictive ingestion read strict reproduction bundles;
  - predictive implementation contracts explicitly name `bundle.components.DXY.weekly_level`;
  - weekly publication preflight, independent replication and post-merge attestation validate public strict bundles.
- [ ] Provider/counsel decision record for Yahoo-delivered DXY/WTI/SPX/VIX/BTC/GOLD and underlying data owners.

No Production change in Phase 0.

### Phase 1 — dual internal/public schema in Preview

Implement on an isolated branch:

- full internal release object remains available only to tests/private handoff;
- new public-safe JSON/CSV generated from the same calculation;
- dashboard renderer reads only aggregate Score/regime;
- public methodology page stops linking directly to uncleared per-driver artifacts;
- public path allowlist blocks internal evidence paths;
- tests fail if forbidden component/value fields enter public files.

No historical deletion in this phase.

### Phase 2 — research-reader migration

- switch Score v3/predictive readers from public strict bundle to approved internal evidence input;
- prove frozen-fixture equivalence;
- update schemas and replication documentation;
- preserve preregistration/holdout boundaries exactly.

### Phase 3 — historical public archive treatment

Choose only after provider/counsel decision:

A. retain historical per-driver artifacts if written rights cover them; or

B. replace public historic artifacts with versioned aggregate-only records while preserving private audit evidence; or

C. withdraw affected public data routes and publish a dated transparency notice.

Do not rewrite Git history or pretend removed public material never existed.

### Phase 4 — Production release

Require:

- exact-head CI/security tests;
- public-path scan proving no prohibited fields;
- Preview route inspection;
- documentation/replication consistency check;
- provider/counsel approval or approved conservative-redaction decision;
- explicit owner Production authorization;
- post-release crawl of current and dated archive paths.

## Acceptance tests for a rights-safe public schema

A release candidate should fail if any public Score path contains an uncleared field matching the protected component-value contract.

At minimum, tests should assert:

- public history rows contain only `date`, `score`, `regime`;
- public latest object contains only approved aggregate fields;
- no public file contains `weekly_level`, `z_unclipped`, `z_clipped`, per-driver `contribution`, or normalization mean/std;
- no public file claims `provider_derived_values_published: false` unless true for the entire scope that statement describes;
- public page rendering does not require component columns;
- private/internal evidence files cannot be served by the public-path router;
- Score formula, weights, regime bands and aggregate output remain unchanged for frozen fixtures.

## Independent replication after containment

Public reproduction claims must become narrower and accurate.

A public user should still be able to:

- inspect the methodology;
- inspect weights/regime bands;
- inspect the aggregate as-published Score/regime history;
- verify release/code/dependency hashes where exposed.

A full numerical reconstruction from provider inputs may require obtaining those inputs independently under the user's own data rights.

Do not claim that the public bundle alone can reproduce the provider-derived calculation if the necessary provider-derived values are intentionally private.

## Decision boundary

This plan does **not** authorize:

- changing the Score v2 formula;
- changing any driver or weight;
- changing Score v3 research rules;
- deleting historical Git evidence;
- deploying a redacted public schema;
- purchasing provider licenses;
- creating paid/private storage;
- making a legal determination.

Next engineering step after review: implement Phase 1 on an isolated branch and prove that aggregate Score/regime output is unchanged while uncleared per-driver value surfaces are absent from public paths.
