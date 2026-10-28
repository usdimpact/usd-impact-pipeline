# Score private evidence source-only integration rehearsal — 2026-10-28

Status: **review-only / no network storage / no deployment / synthetic-only**.

Related: issue #155, merged HOLD #159, draft #158 and draft #160.

## Purpose

Prove that the two accepted review layers are mechanically compatible on current HOLD-enabled main:

1. #158 runner-side synthetic fixture + strict staging/receipt/cleanup contract;
2. #160 short-lived GitHub OIDC private-evidence broker contract.

This branch does not replace or rewrite either historical review head.

## Exact source ancestry

Base:
- current HOLD-enabled main after #159.

Broker layer:
- inherited from #160 accepted head `4f1151986119c17da1890e30561f11758f61c227`.

Handoff layer:
- the five #158 files were copied byte-for-byte from accepted head `15adcdb7b722e17699601ce4c1349168e60b29fb`.

Copied #158 files:
- `scripts/build_synthetic_private_score_evidence.py`;
- `scripts/materialize_private_score_evidence.py`;
- `schemas/score_private_evidence_receipt.schema.json`;
- `tests/test_private_score_evidence_handoff.py`;
- `docs/score-private-evidence-handoff-prototype-2026-10-27.md`.

## New cross-layer proof

`security/score-private-evidence-integration.test.mjs`:

1. creates a temporary directory outside the repository;
2. invokes the reviewed Python synthetic fixture builder;
3. confirms the builder reports provider-free / do-not-publish state;
4. reads both fixed synthetic archive weeks;
5. passes the exact Python-produced bytes through the JavaScript broker validator;
6. verifies the broker derives the expected fixed rehearsal object paths;
7. verifies SHA-256 determinism;
8. proves latest bytes equal the latest archive bytes;
9. removes the temporary directory.

There is no provider retrieval and no cloud/network storage access.

## Request-bound OIDC hardening

The integration review tightens #160's source-only broker policy without changing #160's historical accepted head:

- read OIDC audience is bound to the exact synthetic week;
- write OIDC audience is bound to the exact synthetic week **and** the exact body SHA-256;
- the broker derives the expected audience from validated request headers before accepting the GitHub token;
- tests prove a valid token for one week cannot be reused for another week;
- tests prove a valid write token cannot be reused for different bytes.

This reduces short-lived bearer-token replay scope before any Development deployment exists.

## Deliberate non-execution boundary

The example read/write workflow files remain outside `.github/workflows`.

Therefore this branch cannot:
- request a live GitHub OIDC token through a repository workflow;
- invoke a Supabase Edge Function;
- upload/download Storage objects;
- create a bucket;
- provision a secret;
- change Production.

## What a green result means

A green exact-head quality run proves only:

- the accepted #158 Python synthetic fixture contract still works on current main;
- the accepted #160 OIDC broker validation layer accepts those exact synthetic bytes;
- the combined source/test layers do not break the frozen Score research/release quality suite.

It does **not** prove:
- deployed Edge Function behavior;
- live GitHub OIDC claim values;
- live Supabase Storage permissions;
- bucket policy enforcement in a real project;
- provider rights;
- Production readiness.

Those require a separately authorized Development rehearsal.

## No-action record

No Supabase bucket, object, Edge Function, policy, secret, GitHub environment, runnable OIDC workflow, public Score artifact, research record or Production resource was created or changed by this integration rehearsal.
