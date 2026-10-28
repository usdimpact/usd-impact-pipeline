# Score strict-evidence consumer map — 2026-10-27

Status: **review-only migration evidence**.

Related: #155, #156, #157.

## Why this exists

Rights containment cannot be implemented by deleting public strict-bundle fields because multiple release/research contracts currently treat public reproduction bundles as authoritative evidence.

This map separates:

1. public release validation/attestation;
2. prospective research ingestion;
3. predictive research ingestion;
4. independent replication documentation.

## Direct strict-bundle consumers

### Production/release integrity

- `scripts/validate_weekly_release.py`
- `scripts/weekly_publication_preflight.py`
- `scripts/post_merge_repro_attestation.py`
- `scripts/rehearse_score_repro_acceptance.py`
- `.github/workflows/repro-attestation.yml`
- `.github/workflows/repro-rehearsal.yml`

These consumers validate as-published release integrity. A rights-safe migration must preserve equivalent immutable evidence, but it does not require that the evidence remain publicly web-served.

### Score v3 prospective research

- `scripts/score_v3_shadow_ingestion.py`
- `.github/workflows/score-v3-shadow.yml`

Current dependency:
- `public/data/score_repro_bundle_latest.json`;
- matching `public/archive/<week>/repro_bundle.json`;
- `components.<driver>.weekly_level` for all production drivers.

Research invariant:
- no provider refetch;
- no skipped week/backfill;
- exact immutable weekly levels;
- strict bundle hash bound into research records.

### Score v2 predictive research

- `scripts/score_v2_predictive_ingestion.py`
- `.github/workflows/score-v2-predictive.yml`
- `research/score_v2_predictive_implementation_contract.json`
- `research/score_v2_predictive_preregistration.json`

Current dependency:
- strict bundle published Score;
- `components.DXY.weekly_level`;
- byte-identical latest/archive bundle;
- successful post-merge attestation.

Research invariant:
- origin/outcome levels cannot be reconstructed after outcomes are visible;
- no later-provider recalculation;
- no outcome substitution;
- locked preregistration/contract SHAs remain unchanged.

### Independent replication/public documentation

- `docs/independent-replication-protocol.md`
- `public/data/research/independent_replication_protocol.json`
- related tests/reviewer packets.

Current claim assumes a public third party can reconstruct the as-published score from public strict artifacts. If component evidence becomes private, this claim must be narrowed to aggregate publication verification plus independent reconstruction using separately licensed provider inputs.

## Prototype migration boundary

`scripts/score_private_evidence_source.py` is deliberately **not wired** into any consumer.

It establishes only the future adapter contract:

- evidence root must be outside `public/`;
- latest/archive strict bundle must exist and be byte-identical;
- requested week must match;
- existing strict bundle verifier must pass;
- exact research weekly levels are returned without recalculation or provider refetch.

Storage, credentials, encryption, retention, access control, provider rights and workflow wiring remain unselected.

## Required migration order

1. Provider/counsel decision or approved conservative-redaction decision.
2. Select approved internal evidence storage/access boundary.
3. Wire release attestation to dual-write/verify internal evidence **without changing public output yet**.
4. Prove exact equality with current public strict bundle on frozen fixtures and one live non-Production rehearsal.
5. Migrate Score v3 shadow ingestion to the private evidence adapter; prove research output equivalence.
6. Migrate Score v2 predictive ingestion; preserve all locked preregistration semantics and hashes.
7. Update independent replication claims.
8. Only then remove/redact component evidence from public artifacts.
9. Separately decide historical public archive treatment.

No step may use provider refetching to reconstruct already-frozen predictive origins.
