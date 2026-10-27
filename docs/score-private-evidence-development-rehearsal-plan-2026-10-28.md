# Score private evidence development rehearsal plan — 2026-10-28

Status: **plan only / not authorized for execution**.

Related: issue #155, PRs #156 and #158.

## Purpose

Provide a bounded, reversible development rehearsal for the future private Score evidence boundary without using real provider-derived evidence and without touching Production.

The rehearsal is only needed after the owner explicitly authorizes resource creation. Until then this document is a checklist, not an instruction to execute.

## Why synthetic evidence only

Issue #155 is still unresolved. A storage-mechanics rehearsal does not need genuine ICE/Cboe/S&P/CME/Yahoo-derived values.

Therefore the first rehearsal must use a deterministic **synthetic strict bundle** that:
- matches the strict reproduction schema and driver set;
- contains obviously fake component levels and provenance;
- passes the same structural/hash validation used by #158;
- cannot be mistaken for a publishable Score week;
- never enters the public repository as a generated release.

No current or historical production reproduction bundle should be copied into the rehearsal store while the rights HOLD remains unresolved.

## Candidate rehearsal surface

Preferred development target if explicitly approved:

- Supabase project: `usd-impact-publication-guard-development`;
- region: existing `eu-central-1`;
- new dedicated private Storage bucket only;
- no use of `usd-impact-production`;
- no use of `usd-impact-development`;
- no changes to existing `library-pass-assets` or `library-pass-books` buckets.

Current read-only evidence shows the publication-guard development project has:
- no Storage buckets;
- no public tables;
- no Edge Functions;
- no current Supabase security-advisor findings.

## Proposed bucket constraints

For a future approved rehearsal:

- access: **private**;
- MIME allowlist: `application/json` only;
- file-size ceiling: **1 MiB**;
- no public bucket setting;
- no `anon` or `authenticated` object policies;
- no custom/public domain;
- no signed-URL delivery path;
- no browser/client credential.

The current strict bundle on repository `main` is roughly 13k characters, so a 1 MiB ceiling leaves substantial schema-growth room while preventing accidental large-object use.

## Object namespace

Development rehearsal objects should be isolated under a non-production namespace, for example:

`rehearsal/score-v2/archive/<synthetic-week>/repro_bundle.json`

Do not use the eventual production namespace during the first rehearsal.

The rehearsal adapter may materialize the downloaded bytes into #158's expected local paths only inside runner temporary directories and the explicitly marked ephemeral worktree.

## Credential model for the first rehearsal

If explicitly approved, the simplest development-only test may use one dedicated Supabase S3 credential because the publication-guard project is otherwise empty.

Constraints:

- server-side credential only;
- GitHub **environment secret**, not a committed value;
- environment restricted to the approved repository/main context;
- first run manual `workflow_dispatch` only;
- no pull-request trigger;
- no `pull_request_target`;
- no schedule;
- no reusable exposure to arbitrary workflows;
- no output/echo of the credential;
- no Production credential;
- revoke/rotate after the rehearsal if the design does not proceed.

A later Production design should prefer the OIDC-broker model from `score-private-evidence-auth-boundary-2026-10-28.md` if the additional implementation complexity is accepted.

## Workflow permissions

The rehearsal job should need only:

- `contents: read`.

It should not need:
- `contents: write`;
- `actions: write`;
- `pull-requests: write`;
- `issues: write`;
- `id-token: write` when using the temporary S3-key rehearsal model.

If an OIDC broker is rehearsed later, add `id-token: write` only to the isolated broker-access job.

## Acceptance sequence

### A. Storage isolation

1. Confirm the exact project ID is the publication-guard **development** project.
2. Confirm the bucket is private.
3. Confirm MIME limit is JSON-only.
4. Confirm size cap is 1 MiB.
5. Confirm there is no public/custom domain.
6. Confirm there are no anonymous/authenticated Storage policies.
7. Confirm Supabase security advisors remain clean.

### B. Synthetic write

1. Generate the synthetic strict bundle in `$RUNNER_TEMP`.
2. Validate it locally before upload.
3. Upload to one exact rehearsal object path.
4. Do not use upsert/overwrite behavior.
5. Read the exact object back through authenticated server-side access.
6. Compare byte-for-byte and SHA-256.
7. Record only non-sensitive receipt metadata.

### C. Immutability check

Attempt a second create at the same synthetic-week path using the reviewed adapter logic.

Expected result: **refused before overwrite**.

The rehearsal is a failure if existing evidence bytes can be silently replaced.

### D. Public-access negative checks

Verify:

- unauthenticated object retrieval fails;
- there is no public URL path;
- no signed URL is generated;
- no browser-access credential is used;
- no object bytes appear in logs or Actions artifacts.

### E. #158 handoff equivalence

1. Download the synthetic object into a runner-temporary private evidence root.
2. Create the synthetic latest/archive pair expected by #158.
3. Run #158 strict validation.
4. Stage exact bytes into the marked ephemeral worktree.
5. Run the non-provider synthetic consumer/check.
6. Run hash-guard cleanup.
7. Verify all receipted strict evidence files are gone from the worktree.
8. Destroy the worktree.
9. Verify no strict bundle was committed or added to an artifact.

### F. Credential/log audit

Verify:
- no secret in workflow output;
- no auth header/JWT/access key in logs;
- no provider values in receipt;
- no provider values in job summary;
- only synthetic hashes/path/week metadata retained.

## Abort conditions

Stop immediately if:

- project identity is ambiguous;
- the bucket is accidentally public;
- any existing Library bucket would be modified;
- any real provider-derived bundle is selected;
- credential scope cannot be isolated to the rehearsal;
- overwrite semantics are unclear;
- unauthenticated access succeeds;
- logs expose object content or credentials;
- #158 byte/hash validation fails;
- cleanup leaves strict evidence in the worktree;
- any step requires Production.

Do not weaken a control merely to complete the rehearsal.

## Reversal plan

If a future approved rehearsal completes or aborts:

1. preserve only the non-sensitive acceptance report;
2. revoke/rotate the development rehearsal credential;
3. delete synthetic rehearsal objects;
4. remove the rehearsal bucket if no longer needed;
5. remove the GitHub development environment secret;
6. run Supabase security advisors again;
7. verify no Production project/resource changed.

These reversal mutations require the same explicit execution authorization as the initial rehearsal.

## Promotion gate

A successful synthetic development rehearsal proves only storage mechanics.

It does **not** approve:
- real provider-derived uploads;
- provider rights;
- the final cloud provider;
- Production bucket creation;
- Production credentials;
- a scheduled workflow;
- public Score schema changes;
- removal of issue #155 HOLD.

Promotion requires separate evidence for:
1. provider/counsel rights disposition;
2. selected storage architecture;
3. credential/identity model;
4. retention/deletion policy;
5. exact-head CI/security review;
6. separate Production authorization.

## No-action record

No bucket, object, credential, policy, table, Edge Function, environment secret, workflow, provider value or Production resource was created or changed while preparing this plan.
