# Score rights-safe private research migration packet — 2026-10-28

Status: **review-only / HOLD-bound / Development synthetic only / no Production change**.

Related:
- issue #155 — Score v2 public redistribution HOLD;
- successful Development synthetic private-evidence rehearsal on 2026-10-28;
- `governance/score-private-research-migration-contract.json`;
- `scripts/score_private_evidence_research_adapter.py`;
- `scripts/rehearse_score_private_research_migration.py`.

## Purpose

Define and test the next engineering boundary after the private Storage/OIDC rehearsal:

1. preserve the current Score v2 calculation;
2. move future research-only component evidence behind the approved private boundary;
3. keep public publication limited to aggregate-safe views;
4. migrate research readers before any public component redaction;
5. keep real/provider-derived evidence and Production changes separately gated.

This packet does **not** move real provider-derived evidence, modify active research readers, replace public artifacts, alter website routes, or authorize Production.

## Current dependency that must be removed before public narrowing

### Score v2 predictive

`scripts/score_v2_predictive_ingestion.py` currently reads:
- `public/data/score_repro_bundle_latest.json`;
- the byte-identical dated public archive bundle;
- aggregate published Score;
- `components.DXY.weekly_level`.

The future private-reader contract therefore needs only:
- attested private bundle bytes/hash;
- expected week;
- aggregate published Score;
- DXY weekly level.

### Score v3 shadow

`scripts/score_v3_shadow_ingestion.py` and `scripts/score_v3_metrics.py` reconstruct prospective histories using `source_weekly_levels` for all production drivers.

The future private-reader contract therefore needs:
- attested private bundle bytes/hash;
- expected week;
- the exact production driver set;
- one finite positive weekly level per driver.

### Research validation / vintage

The full robustness, point-in-time and vintage research paths still depend on component-level history and historical as-published evidence. They must be migrated only after the two smaller reader contracts are proven.

## New review-only adapter

`scripts/score_private_evidence_research_adapter.py` defines a narrow local interface:

- `load_private_bundle(...)`:
  - validates the strict reproduction-bundle contract;
  - checks the expected week;
  - in the current rehearsal requires synthetic/do-not-publish markers;
  - returns the bundle plus exact SHA-256.

- `predictive_observation(...)`:
  - returns only `score` and `dxy_weekly_level`.

- `v3_source_levels(...)`:
  - returns exactly one weekly level for each current production driver.

It has no network access and no write path. It is not imported by the active research workflows.

## Synthetic end-to-end rehearsal

`scripts/rehearse_score_private_research_migration.py` performs only local temporary work:

1. loads the migration contract and requires all release boundaries closed;
2. builds provider-free synthetic strict evidence outside the repository;
3. loads that evidence through the new private-reader adapter;
4. extracts the exact Score v2 predictive and Score v3 source-level inputs;
5. constructs a synthetic aggregate Score history;
6. runs the existing aggregate-safe public Score transformer;
7. proves aggregate Score equality across private research and public-safe views;
8. rejects public output containing component/private markers;
9. destroys all temporary evidence automatically.

The rehearsal performs:
- no network access;
- no provider retrieval;
- no Supabase action;
- no public write;
- no workflow dispatch;
- no Production mutation.

## Migration order

### Phase 1 — accepted in this packet

- define machine-readable migration gates;
- define private research reader interface;
- prove synthetic private bundle -> research inputs;
- prove synthetic aggregate-safe public output;
- keep active readers untouched.

### Phase 2 — future Development-only reader migration

Only after this packet is green:

1. add a Development-only private-evidence materialization step for synthetic evidence;
2. run Score v2 predictive ingestion against the private adapter instead of public strict-bundle paths;
3. compare the generated predictive record byte-for-byte or field-for-field with the current reader for the same synthetic fixture;
4. run Score v3 shadow ingestion against the private adapter;
5. compare driver-level input matrices and resulting synthetic research outputs;
6. keep public component paths unchanged during this comparison phase.

No real provider-derived evidence is permitted in Phase 2 without a new authorization satisfying the migration contract.

### Phase 3 — Development research-generation split

After both smaller readers match:

1. generate full research results only in runner-private temporary storage;
2. validate the existing full research contract there;
3. persist full evidence only to the approved private Development boundary;
4. transform only aggregate-safe research views for a temporary publication directory;
5. run exact public leakage/allowlist checks;
6. do not deploy or replace Production.

### Phase 4 — rights decision

Prepare a provider/counsel disposition against the actual proposed end state:
- public aggregate Score/regime;
- approved methodology;
- approved provenance wording;
- private component evidence and research inputs.

A legal/provider decision is still required before the HOLD can be resolved.

### Phase 5 — separate Production candidate

Production may be prepared only after all of these are true:
- research readers no longer depend on public component values;
- public-safe schema is approved;
- consumer/archive migration is verified;
- provider/counsel disposition is recorded;
- exact-head CI is green;
- a separate explicit Production authorization is given.

## Rollback rules

Before any public redaction, the active Production system remains the rollback baseline.

If a Development reader migration differs from the existing public reader:
- stop;
- preserve the mismatch evidence;
- revert the Development reader to the current public strict-bundle path;
- do not change public artifacts.

If future aggregate-safe publication validation fails:
- do not publish;
- retain the current Production public surface;
- keep issue #155 on HOLD.

## Current external state

The successful Development Storage/OIDC rehearsal remains evidence only:
- exactly one synthetic object may remain preserved in the Development private bucket;
- no real/provider-derived object is authorized;
- no Production bucket/broker is authorized;
- no public replacement is authorized.

## Acceptance criteria for this packet

This packet is acceptable when exact-head CI proves:
- the machine-readable contract keeps all release gates closed;
- the new adapter accepts the provider-free synthetic strict bundle;
- predictive input is limited to Score + DXY level;
- V3 input contains exactly the production driver set;
- aggregate-safe output matches the private aggregate Score;
- no component/private markers leak into the public-safe output;
- the full existing repository test/release/security suite remains green.

Acceptance of this packet authorizes **no external state change**.
