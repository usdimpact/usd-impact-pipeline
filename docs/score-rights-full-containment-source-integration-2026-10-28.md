# Score rights full-containment source integration — 2026-10-28

Status: **review-only / Draft / no cloud provisioning / no public replacement / no Production change**.

Related:
- issue #155 — rights/redistribution HOLD;
- merged #159 — fail-closed publication/research gate;
- accepted #161 — private-evidence/OIDC source integration;
- historical #156 — rights/design package;
- historical #157 — aggregate-only public-output prototype.

## Purpose

Bring the accepted Score rights-containment layers onto one current-main review branch without rewriting any historical accepted head.

The integrated source model now contains:

1. active fail-closed HOLD from current `main`;
2. rights/public-surface/provider evidence package from #156;
3. aggregate-only Score and research transformers from #157;
4. private evidence handoff + receipt/cleanup contract from #161;
5. short-lived, request-bound GitHub OIDC broker source from #161;
6. a consolidated no-write rehearsal that proves the layers remain compatible.

## Historical source integrity

The #156 and #157 files are carried from their exact accepted heads, not regenerated from memory.

Historical heads remain preserved:
- #156: `596043c89efb3154a4db017fc3092bc3f8ccf9f4`;
- #157: `d209b6feeda697acfb65de575af550122061bf41`;
- #161 base layer: `047a26d52801b645612df2082121b8e98ac51bee`.

No old branch is rebased or force-updated.

## Consolidated rehearsal

`scripts/rehearse_score_full_containment.py` performs a local/no-write review:

1. reads `governance/score-publication-rights-gate.json`;
2. requires `state: hold` and no approval receipt;
3. transforms the current Score JSON into the aggregate-only public-safe Score payload;
4. transforms current point-in-time, robustness and vintage research into aggregate-only public-safe views;
5. scans transformed outputs for known provider/ticker/component-value markers;
6. runs the existing strict-evidence ↔ aggregate Score/regime parity rehearsal in a temporary private directory;
7. builds the accepted provider-free synthetic private-evidence fixture in a temporary directory;
8. verifies synthetic do-not-publish/provider-free markers and SHA-256;
9. deletes all temporary evidence automatically;
10. returns only hashes/counts/aggregate values.

It does **not**:
- make a network request;
- fetch provider data;
- create a Supabase object;
- write a repository/public artifact;
- modify a workflow;
- deploy anything.

## Integrated public-safe target

### Main Score artifact

Public candidate retains:
- aggregate Score history;
- regime history;
- latest aggregate Score/regime;
- aggregate WoW / four-week change;
- methodology weights;
- aggregate-history hash.

It removes:
- provider weekly levels;
- z-scores;
- contributions;
- normalization moments;
- provider/source provenance.

### Research artifacts

Point-in-time candidate retains aggregate study results and removes provider provenance.

Robustness candidate retains aggregate normalization/regime/distribution/duration/subperiod diagnostics and removes component-specific sensitivity/correlation/contribution outputs.

Vintage candidate retains aggregate Score/regime revision evidence and removes per-driver revision structures.

## Integrated private-evidence target

The private side retains strict evidence required by frozen research/audit contracts.

Current source-only security properties include:
- synthetic-only Development rehearsal;
- non-public path enforcement;
- exact latest/archive byte identity;
- strict bundle verification;
- closed receipt/cleanup contract;
- GitHub OIDC RS256/JWKS verification;
- immutable repository/owner ID checks;
- exact branch/workflow identity;
- operation-specific audiences;
- read token bound to exact week;
- write token bound to exact week and exact content SHA-256;
- fixed private bucket/object namespace;
- private/JSON-only/1 MiB bucket metadata guard;
- create-only writes;
- readback SHA-256 verification;
- no list/delete/signed-URL path.

## What remains intentionally unimplemented

This branch does not yet:
- provision a Supabase bucket;
- deploy an Edge Function;
- create a secret;
- create runnable read/write OIDC workflows;
- move existing strict evidence out of public/repository-visible locations;
- replace existing public files;
- update website links;
- delete/redact historical public artifacts;
- resume Score publication;
- resolve provider rights;
- authorize Production.

## Future Development rehearsal boundary

After source review is accepted, a separate explicit Development-only step may provision:

- private bucket `score-private-evidence`;
- JSON-only, 1 MiB object limit;
- synthetic-only broker function;
- no anonymous/authenticated Storage policy;
- manual-only write/read OIDC workflows;
- fixed week `2099-01-02`;
- provider-free synthetic bytes only.

That step is intentionally not included here.

## No-action record

No Supabase bucket/object/function/policy/secret, GitHub runnable OIDC workflow, provider request, public Score artifact, public research artifact, website route, billing setting or Production resource was created or changed by this source integration.
