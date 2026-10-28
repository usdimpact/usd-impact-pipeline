# Score rights combined containment integration — 2026-10-28

Status: **review-only / Draft / no provisioning / no public replacement / no Production change**.

Related:
- issue #155 — rights HOLD;
- merged #159 — fail-closed publication/research gate;
- Draft #162 — accepted current-main public-containment source candidate;
- Draft #161 — accepted current-main private-evidence source candidate.

## Purpose

Prove that the accepted public and private containment candidates can coexist on one current-main branch without weakening either boundary.

This integration is based on #162 exact head `bb8ed4937f315c91d665c244f14842a351ee6f4f` and carries #161's private-evidence files from exact head `047a26d52801b645612df2082121b8e98ac51bee`.

## Public side retained from #162

- machine-readable A–F public-rights surface classification;
- exact public allowlist/archive-pattern guard;
- HOLD / `production_change_authorized: false`;
- aggregate-only Score transformer;
- aggregate-only point-in-time, robustness and vintage research transformers;
- public-side rights/provider/consumer/historical-treatment documentation.

## Private side retained from #161

- provider-free synthetic fixture;
- strict staging/receipt/cleanup contract;
- GitHub OIDC RS256/JWKS verification;
- immutable repository/owner ID checks;
- exact workflow/ref/event/runner identity;
- request-bound read/write audiences;
- write audience bound to exact content SHA-256;
- fixed private Storage namespace;
- runtime bucket-policy guard;
- create-only write / readback SHA-256;
- no list/delete/signed-URL path;
- non-runnable workflow examples outside `.github/workflows`.

## Combined no-write rehearsal

`scripts/rehearse_score_combined_containment.py`:

1. requires both the publication gate and rights-surface manifest to remain HOLD;
2. requires Production authorization to remain false;
3. validates the A–F class set;
4. derives aggregate-only current Score output;
5. derives aggregate-only current research views;
6. rejects known provider/ticker/component-value markers;
7. builds provider-free synthetic private evidence only under a temporary directory;
8. verifies the synthetic latest SHA-256;
9. deletes the temporary directory automatically;
10. reports only aggregate values, counts and hashes.

No network, provider refetch, cloud storage action, public write or workflow mutation occurs.

## Active workflow boundary

The only active workflow change is to the existing quality workflow, which runs additional tests.

It does **not** add:
- `id-token: write`;
- schedule triggers;
- storage broker URL invocation;
- Supabase credentials;
- deploy steps;
- public artifact writes.

The OIDC workflow examples remain inert files under `prototypes/`.

## Next boundary after acceptance

If this source integration is green, the next step that changes external state is the separately authorized **Development-only synthetic provisioning rehearsal**:

- create a private Development Storage bucket;
- deploy a synthetic-only broker function;
- add manual-only OIDC rehearsal workflows;
- write/read only fixed synthetic week `2099-01-02`;
- verify exact receipt/hash/cleanup behavior;
- keep Production and real provider-derived evidence untouched.

That provisioning step is intentionally excluded from this Draft.
