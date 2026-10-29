# Score private evidence — Development execution packet — 2026-10-28

Historical status at initial authoring (2026-10-28): **review-only / not yet provisioned / not merged / synthetic-only**. This historical status is superseded by the dated live checkpoint below.

## Superseding live checkpoint — 2026-10-29 (read-only verification)

**Development synthetic rehearsal status: PASS.** The originally planned bucket creation, broker deployment, and initial write/read have already been completed by earlier approved work; **do not provision a second bucket, redeploy a duplicate function, or rerun the create-only write**. This checkpoint is a new dated read-only inspection and does not backdate the original packet.

### Supabase current state

- Project `usd-impact-publication-guard-development` (`xakayexlzyrazuunqlxe`), region `eu-central-1`: **ACTIVE_HEALTHY**.
- Exactly one `storage.buckets` entry for `score-private-evidence`: `public=false`, 1 MiB (`1048576`) file limit, only `application/json` MIME allowed.
- Exactly one `storage.objects` entry in that bucket, `rehearsal/score-v2/archive/2099-01-02/repro_bundle.json`, recorded 2026-10-28 01:48 UTC, size **1,748 bytes** and MIME `application/json`. Only object metadata were queried; no private object bytes were exported.
- Public schema base tables: **zero**. Supabase security-advisor lints: **zero** at time checked.
- Edge Function `score-private-evidence-broker`: **ACTIVE, version 1**, with `verify_jwt=false`; the code itself verifies GitHub OIDC JWT signature and claims, so this Supabase setting is intentional rather than permission to bypass application authentication.
- The three deployed source files `index.ts`, `broker-core.mjs` and `github-oidc.mjs` were retrieved read-only and compared to `provisioning/score-private-evidence-development/function/` on current GitHub main. **All three exact content strings matched.** No function configuration or code was altered.

### GitHub Actions acceptance receipts (2026-10-28)

| Run | Verified outcome |
|---|---|
| [Synthetic write run #40617195348](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40617195348) | PASS: reviewed main checkout, HOLD checks, synthetic fixture, write-bound OIDC, create-only broker write and temporary cleanup |
| [Duplicate write attempt #40617289043](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40617289043) | **Expected rejection**: broker returned HTTP 409 instead of replacing the object; cleanup succeeded. Do not mistake this deliberate write-once failure for missing infrastructure |
| [Synthetic read run #40617383435](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40617383435) | PASS: week-bound OIDC, private read, fixture marker/hash validation and temporary cleanup |
| [Private research + locked reader compatibility run #40620133144](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40620133144) | PASS: private read, synthetic source/aggregate adapter, locked reader compatibility and temporary cleanup |

The successful read workflow validates the private bundle's synthetic marker, `do_not_publish`, exact week and zeroed synthetic provenance hashes. This audit did not pull down the object body. The clean-up steps delete runner-temporary inputs and tokens, **not** the already stored synthetic fixture.

### Active governance and stop conditions

`governance/score-private-research-migration-contract.json` currently records `development_synthetic_rehearsal_authorized=true`, while `production_change_authorized=false`, `real_provider_evidence_authorized=false`, and `public_replacement_authorized=false`. The separate Score gate `governance/score-publication-rights-gate.json` is still `state=hold` without a decision receipt.

**Therefore:**
1. Do not repeat the create-only write: the exact fixture path is occupied and correct behavior is HTTP 409.
2. Do not read, write or backfill real FRED, Yahoo or other provider-derived strict evidence into Development Storage based on this synthetic acceptance.
3. Do not activate private-backed production readers, change public root/archived Score artifacts, grant public bucket access, expose signed URLs, or delete the synthetic audit object.
4. Next permissible work without new rights clearance: **read-only** source/consumer dependency inventory, offline synthetic-only compatibility tests, and provider/counsel decision documentation.
5. Before any Development reader migration or Production public-schema change, require the respective governance approvals, explicit scope, backup/rollback plan, exact-head CI and independent verification.

The original planning sequence below is preserved as historical instructions/evidence. It is **not** a current deployment runbook.

---

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
