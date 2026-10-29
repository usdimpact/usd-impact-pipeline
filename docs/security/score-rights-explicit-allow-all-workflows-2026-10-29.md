# Explicit allow-only rights gates (2026-10-29)

Status: **synthetic/test-only branch; public Score publication remains HOLD**.

## Threat model

GitHub Actions step outputs are strings. The legacy expression "hold != 'true'" permits a missing or unexpected value to pass the expression if a prior step happens to succeed without emitting the expected output. The current policy gate normally emits exactly "true" or "false" and fails closed for malformed policy data, but consumers must not rely on inverse checks.

## Proposed behavior

Every active rights-gated Score workflow must execute provider retrieval, research generation, recovery dispatch, or health-side effects **only when hold equals the explicit text false**. A missing, empty, misspelled, unexpected or non-boolean output is not authority.

The existing HOLD summary steps remain keyed to hold == true; they do not open any provider use. The gate script, policy schema and release approval requirements are unchanged.

Changes are limited to seven established workflows and their existing/test-only assertions, plus a new repository-wide regression test that checks every enumerated rights workflow.

## Constraints

- No provider fetch or direct-data comparison.
- No Score formula, weights, output schema, source, archive, entitlement or public endpoint changes.
- No credentials, Cloudflare Access, Pages Production, Supabase, Vercel, checkout or billing changes.
- No activation or publication authorization. Issue #155 remains HOLD.
- All changes must pass exact-head quality and security tests before review.
- Existing working scheduled/dispatch jobs should still record their HOLD summary; no processing is permitted without hold == false.
- This PR should remain draft until a separate review confirms the conditional syntax and tests against the current main SHA.

## Rollback

If an unexpected workflow behavior is found, revert this single bounded commit, keeping the controlling policy HOLD. Never relax the policy or route additional provider data to make a workflow pass.
