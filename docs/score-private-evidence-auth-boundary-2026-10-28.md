# Score private evidence authentication boundary — 2026-10-28

Status: **design only / no credential, bucket, policy, function, workflow or Production change authorized**.

Related: issue #155, PRs #156, #158, #159.

## Decision target

Define an implementation-ready authentication boundary for strict provider-derived Score reproduction evidence without placing a long-lived broad cloud credential in the public `usd-impact-pipeline` repository workflow unless explicitly approved.

This document does not select a provider and does not authorize provisioning.

## Current constraints

- `usdimpact/usd-impact-pipeline` is public.
- The weekly Score workflow currently runs on schedule and `workflow_dispatch`.
- Research consumers run from current `main` after successful upstream evidence/attestation.
- issue #155 remains HOLD.
- draft #158 provides the accepted local ephemeral-worktree staging/cleanup contract.
- existing Supabase Library buckets are private but intentionally constrained to audio/PDF and must not be repurposed.
- the separate Supabase publication-guard development and production projects are ACTIVE_HEALTHY, EU-hosted, and currently empty: no Storage buckets, public tables or Edge Functions.
- Vercel has no reviewed Blob credential/store connected to the inspected project.
- the connected Cloudflare account still refuses R2 List Buckets with error 10042.

## Non-negotiable properties

Any future authentication design must:

1. keep provider-derived evidence outside the public repository and public deployment trees;
2. authorize only the exact workflow/repository/branch context needed;
3. separate write authority from read authority when practical;
4. make weekly archive writes create-once / non-overwriting;
5. avoid workflow delete authority;
6. keep credentials/tokens out of logs and committed files;
7. preserve a non-sensitive audit receipt: week, object path, SHA-256, workflow run ID/URL, timestamp and operation;
8. fail closed on missing/invalid identity, unexpected event, unexpected ref, path mismatch, existing archive object or hash mismatch;
9. feed the unchanged #158 ephemeral-worktree contract after download;
10. require separate Production authorization after rights approval.

## Candidate A — dedicated Supabase S3 credential

Supabase Storage exposes an S3-compatible API. Official documentation states that generated S3 access keys are intended for server-side use and provide full Storage access across all buckets in that project, bypassing RLS.

Reference:
- https://supabase.com/docs/guides/storage/s3/authentication

### Development rehearsal shape

If explicitly approved later:

- use **`usd-impact-publication-guard-development`**, not the live Library project;
- create one new **private** bucket dedicated to Score evidence;
- allow only `application/json`;
- set a small file-size ceiling appropriate to the strict bundle;
- create no `anon` or `authenticated` Storage access policy;
- issue a development-only S3 credential;
- store it as a GitHub **environment secret**, not in repository files;
- bind the rehearsal job to a dedicated environment and `refs/heads/main`;
- use `workflow_dispatch` only for the first rehearsal;
- use upload-without-upsert semantics and reject an already-existing week object;
- give the workflow no delete step.

GitHub documents that Actions secrets are not passed to workflows triggered from forks. Environment secrets can further limit which jobs receive the credential.

References:
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets
- https://docs.github.com/en/code-security/reference/secret-security/secret-types

### Residual risk

The S3 credential is long-lived and broad across Storage in its dedicated Supabase project. Project isolation limits blast radius, but compromise of that key would still permit all Storage operations in that project until rotation/revocation.

Disposition: **lowest-complexity rehearsal path; not preferred as the final credential model without explicit risk acceptance**.

## Candidate B — GitHub OIDC → narrow broker

GitHub Actions can mint a short-lived OIDC JWT per workflow job when `id-token: write` is granted. GitHub's current OIDC tokens include claims such as issuer, audience, repository identity, repository owner identity, ref, SHA, event, run ID and workflow identity.

References:
- https://docs.github.com/en/actions/concepts/security/openid-connect
- https://docs.github.com/en/actions/reference/security/oidc

A future broker can verify the GitHub OIDC token and perform only the exact storage operation requested. The broker would hold the underlying storage credential server-side; GitHub would hold no long-lived cloud-storage secret.

### Trust conditions

A production trust policy should pin, at minimum:

- issuer: `https://token.actions.githubusercontent.com`;
- a custom audience dedicated to Score private evidence;
- immutable GitHub repository ID: `1207104487`;
- immutable GitHub owner ID: `275107298`;
- repository: `usdimpact/usd-impact-pipeline` as an additional human-readable guard;
- ref: `refs/heads/main`;
- only explicitly accepted events;
- exact approved workflow identity;
- token expiry / not-before;
- one request per accepted operation.

Do not rely only on mutable repository/owner names.

GitHub changed default OIDC subject formatting for repositories created after 2026-07-15 and supports immutable subject claims. The current repository's subject-template state has not been verified in this review. Therefore the final trust implementation must inspect the actual token/template state rather than assuming a subject format.

### Prefer a reusable storage workflow

For the strongest workflow identity boundary, future implementation should consider a single reviewed reusable workflow for private-evidence storage access and bind OIDC trust to its `job_workflow_ref` / equivalent exact workflow identity claim.

Do not authorize arbitrary workflows in the repository merely because they run on `main`.

### Broker operations

The broker API should be deliberately small:

**Writer**
- `PUT /score-v2/archive/YYYY-MM-DD/repro_bundle.json`
- create only;
- reject overwrite;
- verify the strict bundle contract and declared week;
- compute/return SHA-256;
- no delete/list operation.

**Reader**
- fetch an exact dated archive object;
- fetch a non-sensitive latest pointer/manifest if one is maintained;
- no write/delete authority.

A non-sensitive latest pointer can contain only:
- latest week;
- archive object path;
- SHA-256;
- schema version.

It should contain no provider-derived component values.

### Avoid signed URLs for strict evidence

Supabase documentation notes that private assets can be accessed with authenticated downloads or signed URLs, and that signed URLs use a dedicated internal signing key. Current CDN documentation also warns that cached signed-URL responses can remain available according to cache TTL even after token expiry.

For this rights-sensitive evidence class, the preferred broker behavior is therefore:
- authenticate GitHub OIDC;
- broker performs the private Storage read server-side;
- stream the bytes directly to the GitHub runner;
- do **not** hand out reusable public bearer URLs.

References:
- https://supabase.com/docs/guides/storage/serving/downloads
- https://supabase.com/docs/guides/storage/cdn/smart-cdn

### Audit record

Broker logs/receipts should include only:
- GitHub repository ID;
- workflow/run ID;
- event/ref;
- operation;
- week/object path;
- SHA-256;
- result;
- timestamp.

Do not log:
- provider-derived component values;
- object body;
- authorization headers;
- OIDC JWT;
- underlying service/S3 credential.

Disposition: **preferred final security model if implementation complexity is accepted**.

## Supabase publication-guard shape

If Supabase is selected later, keep the private evidence boundary out of `usd-impact-production` and `usd-impact-development`.

Proposed progression:

1. publication-guard **development** project — manually approved rehearsal only;
2. verify private bucket metadata, MIME/size constraints, create-once behavior and #158 byte equivalence;
3. verify security advisors remain clean;
4. verify no public URL / no anonymous policy / no signed-URL dependency;
5. verify cleanup leaves no strict evidence in repository checkout/worktree after the research process;
6. only after rights + security + owner acceptance, separately design publication-guard **production** equivalent.

No development rehearsal authorizes the production equivalent.

## Workflow permission tightening

A future private-evidence workflow should start from least privilege:

- `contents: read`;
- `id-token: write` only when using OIDC;
- no `actions: write`;
- no `pull-requests: write`;
- no `issues: write`;
- no repository content write unless a separate reviewed job explicitly needs it.

Storage access should live in a distinct job/workflow from public publication.

## Reader/writer separation

Preferred final model:

`weekly calculation`
→ strict evidence in runner temp
→ authenticated **create-only writer**
→ private immutable archive

`research consumer`
→ authenticated **read-only reader**
→ runner temp
→ #158 strict validation
→ ephemeral worktree
→ unchanged frozen research engine
→ hash-guard cleanup
→ destroy worktree

The public aggregate artifact path remains separate.

## Fail-closed rules

Do not perform a private-evidence write if:

- issue #155 is HOLD for a path that would still violate the rights disposition;
- storage candidate is not approved;
- identity claims are incomplete/mismatched;
- ref is not exact `main`;
- event/workflow identity is unexpected;
- week is invalid;
- archive object already exists;
- strict bundle validation fails;
- object hash differs after write/readback;
- audit receipt cannot be recorded safely.

Do not fall back from private storage to:
- public GitHub artifacts;
- repository commits;
- public Vercel/Pages assets;
- email attachments;
- public/signed URLs;
- logs.

## Current recommendation

Engineering preference, without provisioning:

1. keep #159 HOLD unchanged;
2. retain #158 as the local handoff contract;
3. treat Supabase publication-guard **development** as the leading rehearsal surface because it is isolated, EU-hosted and currently empty;
4. use a development-only long-lived S3 key only if the owner explicitly approves a bounded rehearsal;
5. prefer GitHub OIDC → broker for a later production design so the public repository does not depend on a long-lived storage credential;
6. do not create any resource until the rights disposition and owner authorization make the rehearsal necessary.

## No-action record

This design was produced from read-only GitHub, Supabase, Vercel and Cloudflare evidence plus current official documentation.

No bucket, object, table, policy, Edge Function, credential, secret, GitHub environment, OIDC configuration, workflow permission, provider setting or Production resource was created or changed.
