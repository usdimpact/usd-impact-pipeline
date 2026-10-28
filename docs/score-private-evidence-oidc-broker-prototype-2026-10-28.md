# Score private evidence GitHub OIDC broker prototype — 2026-10-28

Status: **source-only review prototype / synthetic-only / no Supabase resource or deployment**.

Related: issue #155, merged HOLD #159, review-only #156–#158.

## Goal

Test the preferred short-lived authentication model for private Score evidence without creating a long-lived GitHub storage credential.

Proposed future trust chain:

`GitHub Actions OIDC`
→ exact GitHub identity/claim verification
→ narrow broker operation
→ fixed private Supabase Storage bucket/path
→ exact-byte receipt/readback

The prototype is deliberately **not deployable through any existing workflow**. It lives under `prototypes/`, not `supabase/functions/`, and no Supabase config, secret, bucket, function or GitHub OIDC workflow has been provisioned.

## Current-doc review

Current Supabase guidance was rechecked before writing this prototype.

Relevant current behavior:
- Edge Functions are Deno-compatible server-side TypeScript functions.
- functions normally perform Supabase JWT verification before user code.
- external GitHub OIDC tokens therefore require the future broker function to set `verify_jwt = false` and perform its own GitHub JWT verification in code.
- Supabase currently recommends `SUPABASE_SECRET_KEYS` for server-side privileged operations; the prototype intentionally has no legacy `SUPABASE_SERVICE_ROLE_KEY` fallback.
- private Storage objects do not have public URLs; this design does not create signed URLs.
- Supabase has announced removal of a small set of obsolete TLS 1.2 CBC ciphers no earlier than 2026-11-10. GitHub-hosted runners use modern TLS and the prototype does not depend on those legacy ciphers.

References:
- https://supabase.com/docs/guides/functions/function-configuration
- https://supabase.com/docs/guides/functions/auth
- https://supabase.com/docs/guides/functions/storage-caching
- https://supabase.com/docs/guides/storage/serving/downloads
- https://supabase.com/changelog/cbc-tls-ciphers-deprecated
- https://docs.github.com/en/actions/reference/security/oidc

## Prototype files

- `prototypes/score-private-evidence-broker/github-oidc.mjs`
  - RS256 signature verification using Web Crypto;
  - GitHub JWKS lookup;
  - issuer/audience/time verification;
  - immutable repository and owner ID checks;
  - exact branch, workflow, event and runner-environment checks.

- `prototypes/score-private-evidence-broker/broker-core.mjs`
  - separate read/write audiences;
  - separate exact read/write workflow identities;
  - synthetic-only week namespace;
  - fixed bucket/path derivation;
  - deterministic synthetic-bundle rejection rules;
  - SHA-256 helpers.

- `prototypes/score-private-evidence-broker/index.ts`
  - Supabase Edge Function-shaped wrapper;
  - POST only;
  - no query parameters;
  - no browser CORS;
  - create-only upload with `upsert: false`;
  - readback byte/hash verification;
  - exact-object read only;
  - no list/delete/signed-URL operation;
  - non-sensitive audit fields only.

- `security/score-private-evidence-broker.test.mjs`
  - locally generated RSA test keys;
  - valid signature path;
  - read/write token separation;
  - immutable repository-ID rejection;
  - workflow-ref rejection;
  - expiry rejection;
  - payload-tamper signature rejection;
  - synthetic-only namespace tests;
  - provider-marker rejection;
  - static no-list/no-delete/no-signed-URL/no-legacy-secret checks.

## Immutable GitHub trust boundary

The prototype pins:

- issuer: `https://token.actions.githubusercontent.com`;
- repository: `usdimpact/usd-impact-pipeline`;
- repository ID: `1207104487`;
- repository owner ID: `275107298`;
- ref: `refs/heads/main`;
- ref type: `branch`;
- runner environment: `github-hosted`;
- event: `workflow_dispatch` only;
- exact operation-specific workflow refs;
- operation-specific audiences;
- short token age/lifetime;
- signed commit/run/JTI claims.

It does not rely only on mutable repository names or the JWT subject.

### Write identity

Audience:
`urn:usd-impact:score-private-evidence:write:development`

Future exact workflow ref:
`usdimpact/usd-impact-pipeline/.github/workflows/score-private-evidence-write-rehearsal.yml@refs/heads/main`

### Read identity

Audience:
`urn:usd-impact:score-private-evidence:read:development`

Future exact workflow ref:
`usdimpact/usd-impact-pipeline/.github/workflows/score-private-evidence-read-rehearsal.yml@refs/heads/main`

Those workflows do not exist yet.

## Synthetic-only fail-closed mode

The prototype supports only:

`SCORE_BROKER_MODE=synthetic-only`

and defaults to that mode when unset.

It rejects:
- any week before 2099;
- non-Friday weeks;
- real pipeline SHA/hash values;
- missing `synthetic_rehearsal: true`;
- missing `do_not_publish: true`;
- unexpected component sets;
- provider/source/provenance markers;
- source URLs;
- bodies over 1 MiB.

This makes the first future Development rehearsal mechanically incapable of accepting a normal 2026 production Score bundle without a separate reviewed code change.

## Fixed Storage boundary

Future rehearsal target, if separately approved:

- project: `usd-impact-publication-guard-development`;
- bucket: `score-private-evidence`;
- bucket must be private;
- JSON only;
- 1 MiB maximum object size;
- no anonymous/authenticated Storage policies;
- no public/custom domain;
- no signed-URL delivery.

Object path is derived internally:

`rehearsal/score-v2/archive/<synthetic-Friday>/repro_bundle.json`

The caller cannot supply a bucket or arbitrary object path.

## Write contract

Request:
- POST;
- GitHub OIDC Bearer token;
- `x-score-operation: write`;
- synthetic Friday in `x-score-week`;
- lowercase SHA-256 in `x-score-content-sha256`;
- `application/json` body;
- <= 1 MiB.

Broker:
1. verifies GitHub signature and exact write identity;
2. validates synthetic bundle;
3. recomputes SHA-256;
4. uploads with `upsert: false`;
5. reads exact object back;
6. verifies byte hash;
7. returns non-sensitive receipt metadata.

A repeated create at the same object path is refused.

## Read contract

Request:
- POST with no body;
- GitHub OIDC Bearer token;
- `x-score-operation: read`;
- synthetic Friday in `x-score-week`.

Broker:
1. verifies GitHub signature and exact read identity;
2. derives exact object path;
3. downloads through privileged server-side Storage access;
4. hashes bytes;
5. streams bytes directly with `private, no-store`.

No signed/public bearer URL is created.

## Future Supabase function configuration

Only if a separate deployment decision is approved, the function configuration would need the equivalent of:

```toml
[functions.score-private-evidence-broker]
verify_jwt = false
```

That setting is safe only because the function itself rejects any request whose GitHub OIDC signature/claims fail. Do not deploy the function with `verify_jwt = false` before the claim-verifier tests and Development review pass.

## Residual risks

This prototype does not yet solve:

- OIDC bearer-token replay inside the token lifetime;
- production/non-synthetic evidence;
- storage object retention/deletion policy;
- provider/counsel rights;
- bucket provisioning;
- Supabase secret-key rotation;
- broker rate limiting;
- audit-log retention;
- current public artifact redaction;
- migration of historical research inputs.

Create-only write semantics make replayed writes non-destructive after the first successful create. Read-token replay remains a bounded residual risk and should be reviewed before any production design.

## Promotion gates

Do not provision or deploy until all are true:

1. issue #155 rights disposition allows internal retention;
2. owner approves the Development rehearsal;
3. draft broker exact-head CI/security checks pass;
4. publication-guard Development project is rechecked empty/healthy;
5. private bucket constraints are approved;
6. future read/write OIDC workflow files are separately reviewed;
7. a Development-only invocation proves signature/claim denial cases;
8. no real provider-derived bundle is used in the first rehearsal.

Production remains a separate later decision.

## No-action record

This prototype created only review-branch source/test/documentation files.

It did **not** create or modify:
- Supabase bucket/object;
- Edge Function;
- API/secret key;
- RLS/Storage policy;
- GitHub OIDC customization;
- GitHub Actions read/write workflow;
- Production resource;
- public Score artifact;
- existing research evidence.
