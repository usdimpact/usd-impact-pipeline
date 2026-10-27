# Score private evidence storage options — 2026-10-28

Status: **decision support only; no resource, credential, billing or Production change authorized**.

Related: #155, #156, #158.

## Required properties

Any future storage for strict Score reproduction evidence must provide:

- authenticated non-public reads/writes;
- durable retention across the 52-week frozen research studies;
- immutable/versioned historic weeks or equivalent object versioning;
- CI-readable access from the production research workflow;
- auditability;
- no public web route;
- clean separation from the public Score artifact tree;
- a credential/identity model suitable for a public GitHub repository;
- low operational complexity and small-data cost.

The stored material is small but rights-sensitive: provider-derived weekly levels, normalization moments, z-scores/contributions and provenance.

## Option 1 — Vercel Private Blob

Current official Vercel documentation states that private Blob stores require authenticated reads/writes and are GA on all plans.

Advantages:
- existing USD Impact Vercel team;
- purpose-built private object storage;
- no public URL access without authentication;
- straightforward object naming/versioning;
- small evidence volume.

Current account evidence:
- a fresh read-only project-environment metadata check on 2026-10-28 found no configured environment key matching Blob/R2/storage credentials on the USD Impact site project;
- no `BLOB_READ_WRITE_TOKEN` is configured on the inspected USD Impact Vercel project;
- no private Blob store was created or connected during this review.

GitHub Actions implication:
- the Score pipeline runs in GitHub Actions, not a Vercel Function;
- therefore the research workflow would still need an approved authentication path, likely a narrowly scoped Blob credential or a separately reviewed broker;
- do not create a long-lived token until the access/rotation model is approved.

Disposition: **viable candidate; no existing connection**.

## Option 2 — Cloudflare R2 private bucket

Cloudflare documentation states that R2 buckets are private by default and become public only after explicit public-access configuration.

Advantages:
- S3-compatible object storage;
- durable private bucket model;
- can avoid any public domain/r2.dev exposure;
- potentially consistent with other USD Impact Cloudflare operations.

Current account evidence:
- the connected Cloudflare identity has R2 read/write API scopes;
- a fresh read-only List Buckets call on 2026-10-28 again returned Cloudflare error 10042: **"Please enable R2 through the Cloudflare Dashboard."**
- the API explicitly reported that the existing connection already has the accepted R2 read/write permissions, so reconnecting will not fix this account-level refusal;
- no bucket was created or changed.

The known public-audio R2 context is therefore not available through the currently connected Cloudflare account/session and must not be assumed to be the same storage account.

Disposition: **viable architecture, current account boundary unresolved**.

## Option 3 — GitHub Actions artifacts

GitHub documentation states that workflow artifacts are downloadable by signed-in users with repository read access and expire according to artifact retention settings.

The Score pipeline repository is currently **public**.

Therefore plaintext Actions artifacts do not meet the private-evidence requirement.

An encrypted rolling artifact could technically hide values, but it would:
- distribute ciphertext through a public-repository artifact surface;
- add symmetric key lifecycle/rotation/recovery requirements;
- depend on artifact retention and weekly refresh;
- create unnecessary legal/security ambiguity when true private object stores exist.

Disposition: **not recommended for provider-derived plaintext; encrypted-artifact fallback only after explicit security/legal review**.

## Option 4 — new private GitHub repository

A private evidence-only repository could provide durable versioned storage, but it would:
- create a second repository and access-control boundary;
- require GitHub Actions credentials/cross-repo permissions;
- store data in Git objects, which is awkward for retention/deletion rules;
- risk accidental PR/log exposure if operational discipline slips.

Disposition: **possible, but inferior to object storage for this evidence class**.

## Preferred engineering direction

If provider/counsel chooses aggregate-only public containment, the lowest-complexity candidates are:

1. **Vercel Private Blob**, if a scoped GitHub-workflow authentication model is approved; or
2. **Cloudflare R2 private bucket**, after the correct account/R2 entitlement is resolved and a scoped API credential is approved.

Do not select between them on engineering convenience alone. The final choice should also consider:
- DPA/subprocessor posture;
- preferred data region;
- credential rotation;
- retention/deletion obligations;
- who owns operational recovery.

## Ephemeral runner contract

Whichever store is selected, the storage provider should feed the same reviewed temporary-worktree pattern from draft #158:

private store → runner temp → hash validation → ephemeral worktree legacy paths → unchanged frozen research engine → hash-guard cleanup → destroy worktree.

No provider-derived evidence should be copied into the public repository checkout or Pages/Vercel public output as part of that handoff.

## No-action record

This review performed only:
- official documentation checks;
- Vercel environment-key metadata inspection without decrypting values;
- a read-only Cloudflare R2 bucket-list attempt.

No storage, bucket, Blob store, token, secret, environment variable, billing setting or public route was created or changed.
