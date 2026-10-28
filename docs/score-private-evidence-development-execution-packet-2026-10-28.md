# Score private evidence — Development execution packet — 2026-10-28

Status: **review-only / not yet provisioned / not merged / synthetic-only**.

Related:
- issue #155 — Score rights HOLD;
- merged #159 — fail-closed publication/research gate;
- accepted Draft #164 — combined public/private source containment.

## Objective

Prepare the exact Development-only actions required to prove the private-evidence path end to end using **provider-free synthetic evidence only**.

This packet intentionally stops before external state changes.

## Development target

Supabase project:
- name: `usd-impact-publication-guard-development`
- project ref: `xakayexlzyrazuunqlxe`
- region: `eu-central-1`
- expected current state before provisioning:
  - Storage buckets: 0
  - public tables: 0
  - Edge Functions: 0
  - security-advisor findings: 0

Direct links:
- Project: https://supabase.com/dashboard/project/xakayexlzyrazuunqlxe
- Storage: https://supabase.com/dashboard/project/xakayexlzyrazuunqlxe/storage/buckets
- Edge Functions: https://supabase.com/dashboard/project/xakayexlzyrazuunqlxe/functions

GitHub:
- Repository: https://github.com/usdimpact/usd-impact-pipeline
- Rights issue: https://github.com/usdimpact/usd-impact-pipeline/issues/155
- Accepted source candidate: https://github.com/usdimpact/usd-impact-pipeline/pull/164

## Prepared source

### Private bucket SQL

`provisioning/score-private-evidence-development/create_bucket.sql`

Creates exactly one bucket:
- id/name: `score-private-evidence`
- public: `false`
- maximum file size: 1 MiB
- allowed MIME type: `application/json`

The SQL has no conflict/update path. If a bucket already exists, provisioning fails instead of silently mutating it.

`provisioning/score-private-evidence-development/verify_bucket.sql` is read-only and reports:
- bucket metadata;
- object count.

### Edge Function package

`provisioning/score-private-evidence-development/function/`

Files are byte-identical to the accepted broker prototype:
- `index.ts`
- `broker-core.mjs`
- `github-oidc.mjs`

Future deployment settings:
- function name: `score-private-evidence-broker`
- project: `xakayexlzyrazuunqlxe`
- `verify_jwt: false`

`verify_jwt: false` is required only because the function verifies the external GitHub OIDC JWT itself. The broker fails closed on invalid signature/claims.

No user-created Supabase secret is required. The broker uses Supabase's server-side default `SUPABASE_SECRET_KEYS` environment variable.

### GitHub write rehearsal

`.github/workflows/score-private-evidence-write-rehearsal.yml`

Properties:
- `workflow_dispatch` only;
- main branch only;
- `contents: read`;
- `id-token: write`;
- fixed synthetic week `2099-01-02`;
- requires both rights manifests to remain HOLD;
- builds only the reviewed provider-free synthetic fixture;
- GitHub OIDC audience is bound to exact week + exact fixture SHA-256;
- writes through the broker;
- validates the broker receipt;
- removes all runner-temporary evidence/token files.

After merge, workflow page:
https://github.com/usdimpact/usd-impact-pipeline/actions/workflows/score-private-evidence-write-rehearsal.yml

### GitHub read rehearsal

`.github/workflows/score-private-evidence-read-rehearsal.yml`

Properties:
- `workflow_dispatch` only;
- main branch only;
- `contents: read`;
- `id-token: write`;
- fixed synthetic week `2099-01-02`;
- requires both rights manifests to remain HOLD;
- OIDC audience is bound to the exact week;
- reads the exact object only;
- verifies returned SHA-256;
- revalidates synthetic/do-not-publish/zeroed-hash markers;
- removes runner-temporary token/evidence files.

After merge, workflow page:
https://github.com/usdimpact/usd-impact-pipeline/actions/workflows/score-private-evidence-read-rehearsal.yml

## Exact execution order after authorization

1. Recheck #155 remains OPEN/HOLD.
2. Recheck Development Supabase project is healthy and still has no conflicting bucket/function.
3. Execute `create_bucket.sql`.
4. Re-read bucket metadata and confirm:
   - private;
   - JSON-only;
   - exactly 1 MiB;
   - object count 0.
5. Deploy `score-private-evidence-broker` with `verify_jwt=false`.
6. Verify function metadata/logs and perform unauthenticated rejection checks.
7. Merge only the reviewed execution workflow package to `main`.
8. Run the **write** workflow once.
9. Verify:
   - object count becomes 1;
   - path is exactly `rehearsal/score-v2/archive/2099-01-02/repro_bundle.json`;
   - bucket remains private;
   - receipt SHA matches stored object.
10. Run the **read** workflow once.
11. Verify:
   - read SHA equals write receipt SHA;
   - stored JSON remains synthetic/do-not-publish;
   - no public/signed URL exists.
12. Review Edge Function + GitHub Actions logs for auth/storage anomalies.
13. Leave the synthetic Development object in place as rehearsal evidence unless a separate cleanup decision is made.
14. Keep Score publication HOLD active. Do not use real provider-derived evidence.

## Failure rules

Stop immediately if any of these occur:
- #155 is closed or HOLD state changes unexpectedly;
- `production_change_authorized` becomes true without a separate reviewed decision;
- Development bucket/function already exists unexpectedly;
- bucket is public;
- file-size/MIME constraints differ;
- unauthenticated broker request succeeds;
- write token can be used for a different week/hash;
- read token can read a different week;
- object path differs from the fixed synthetic namespace;
- broker returns or creates a signed/public URL;
- any real/current Score week is accepted;
- any provider-derived marker appears in rehearsal bytes.

Do not retry by weakening checks.

## Rollback boundary

Before the write rehearsal:
- bucket/function can be removed because no evidence object exists.

After the write rehearsal:
- preserve the synthetic object until the rehearsal result is documented;
- do not delete Storage rows directly from Postgres;
- if cleanup is later approved, use the Storage API/Dashboard to delete the synthetic object first, then remove the bucket/function.

No rollback action affects Production because this packet targets only `usd-impact-publication-guard-development`.

## Manual action requirement

At the current stage, **no manual dashboard click is technically required**. The connected tools can:
- execute the bucket SQL;
- deploy the Edge Function;
- create/merge GitHub workflow source;
- inspect Supabase metadata/logs;
- inspect GitHub Actions runs.

What **is** required is explicit owner authorization before those state-changing Development actions.

A sufficient authorization is:

`APPROVE DEVELOPMENT SYNTHETIC REHEARSAL`

That authorization covers only:
- the Development project above;
- one private bucket;
- one synthetic-only broker;
- the two manual-only synthetic workflows;
- synthetic week `2099-01-02`;
- no Production;
- no real/provider-derived Score evidence.

Anything beyond that requires a separate authorization.
