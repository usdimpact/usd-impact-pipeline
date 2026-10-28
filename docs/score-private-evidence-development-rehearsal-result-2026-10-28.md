# Score private evidence — Development synthetic rehearsal result — 2026-10-28

Status: **COMPLETED / DEVELOPMENT-ONLY / SYNTHETIC-ONLY / SCORE RIGHTS HOLD UNCHANGED**.

Related:
- issue #155 — Score rights / redistribution HOLD;
- merged #164 — combined public/private containment;
- merged #165 — Development synthetic execution packet;
- merged #166 — module-safe synthetic builder invocation;
- merged #167 — pinned Python runtime repair;
- merged #168 — shell-safe summary logging repair.

## Authorization boundary

The owner explicitly authorized:

`APPROVE DEVELOPMENT SYNTHETIC REHEARSAL`

That authorization covered only:
- Supabase Development project `xakayexlzyrazuunqlxe`;
- one private bucket `score-private-evidence`;
- one synthetic-only broker `score-private-evidence-broker`;
- manual write/read rehearsal workflows;
- synthetic week `2099-01-02`;
- no Production;
- no real/provider-derived Score evidence.

This result does not expand that authorization.

## Final Development state

Supabase project:
- name: `usd-impact-publication-guard-development`;
- ref: `xakayexlzyrazuunqlxe`;
- status at verification: healthy.

Private Storage bucket:
- id/name: `score-private-evidence`;
- public: `false`;
- file size limit: `1048576` bytes;
- allowed MIME type: `application/json`;
- final object count: exactly `1`.

Stored rehearsal object:
- path: `rehearsal/score-v2/archive/2099-01-02/repro_bundle.json`;
- size: `1748` bytes;
- MIME type: `application/json`;
- created at: `2026-10-28T01:48:40.712473Z`;
- updated at: same timestamp, proving no overwrite occurred.

Edge Function:
- slug: `score-private-evidence-broker`;
- status: `ACTIVE`;
- live files are byte-identical to the reviewed provisioning source on `main`;
- `verify_jwt=false` at the Supabase platform layer is intentional because the function performs GitHub OIDC signature and claim verification itself.

Supabase security advisors at verification:
- security findings: `0`.

## Successful write rehearsal

Workflow:
`Score private evidence synthetic write rehearsal`

Successful run:
https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40617195348

Exact run head:
`54942cf0958c514c453e8577d532ebc715397de0`

Synthetic week:
`2099-01-02`

Exact content SHA-256:
`74bf55400a10e59173a516c46538a1fe4c04d03056aea85c1e1e246b6c33f8be`

The successful write proved:
- Score publication gate remained `hold`;
- public rights surface remained `hold`;
- `production_change_authorized=false`;
- provider-free synthetic evidence generation completed;
- GitHub OIDC write token issuance completed;
- the write audience was bound to exact week + exact content SHA-256;
- the broker accepted the request;
- Storage created the object once;
- broker readback hash matched the written bytes;
- no Production resource was touched.

## Duplicate-write fail-closed evidence

A later duplicate write run:
https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40617289043

used the same current-main rehearsal path after the object already existed.

Result:
- HTTP `409`;
- overwrite refused;
- object count remained `1`;
- stored object `updated_at` remained identical to `created_at`.

This is expected fail-closed behavior from `upsert:false`, not a data-loss incident.

## Successful read rehearsal

Workflow:
`Score private evidence synthetic read rehearsal`

Successful run:
https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40617383435

Exact run head:
`54942cf0958c514c453e8577d532ebc715397de0`

The read rehearsal passed:
- Score HOLD verification;
- exact week-bound GitHub OIDC token issuance;
- broker read authorization;
- exact object retrieval;
- returned SHA-256 verification;
- synthetic rehearsal marker verification;
- `do_not_publish=true` verification;
- zeroed pipeline SHA verification;
- zeroed requirements hash verification;
- runner-temporary token/evidence cleanup.

## Logging-only repair after successful rehearsal

The successful write/read validations were already complete before merged #168.

#168 only removed Markdown backticks from shell `echo` step-summary lines to prevent command-substitution noise and added a regression assertion.

It did not change:
- broker logic;
- OIDC policy;
- Storage bucket;
- stored object;
- rights/HOLD controls;
- public artifacts;
- Production.

No write/read storage workflow rerun is required for #168.

## Security / rights conclusions

The Development rehearsal proves the reviewed private-evidence transport can:
- accept only the fixed synthetic namespace;
- bind GitHub OIDC to repository/ref/workflow/event/runner identity;
- bind writes to exact week + exact SHA-256;
- reject duplicate overwrite;
- read back and verify exact stored bytes;
- keep the bucket private;
- operate without exposing provider-derived evidence.

It does **not** prove or authorize:
- rights to redistribute current Score provider-derived evidence;
- Production storage;
- Production broker deployment;
- migration of real Score evidence;
- public Score schema release;
- research publication;
- publication workflow unfreezing.

## Retention decision

Per the reviewed execution packet, the single synthetic Development object is intentionally retained as rehearsal evidence.

Do not delete it unless a separate cleanup decision is approved.

## Continuing HOLD

Issue #155 remains open.

The Score publication gate and public-rights surface remain HOLD-bound.

No Production or public-release action is authorized by this rehearsal result.
