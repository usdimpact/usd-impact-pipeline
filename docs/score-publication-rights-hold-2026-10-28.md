# Score public-publication rights hold — review candidate

Prepared: 2026-10-28  
Status: **DRAFT / UNMERGED / NO PRODUCTION CHANGE**

Related governance: issue #155, design #156, public-safe prototype #157, private-evidence prototype #158.

## Why this exists

The current Friday workflow creates and pushes a public Git branch containing newly generated
component-level Score artifacts before human review. The Saturday research workflow and the
post-attestation v2/v3 prospective research consumers can then create additional public/repository-
visible provider-derived evidence.

Because issue #155 is unresolved, leaving those automations unchanged would continue expanding the
rights-review surface even while engineering treats new component-level public exposure as HOLD.

This candidate provides a reversible fail-closed governance gate. **It is not merged by this
document.**

## Current HOLD effect

If merged with the policy still set to `hold`:

- Friday weekly Score preflight reads the policy and stops before Python dependency installation,
  provider retrieval, generated writes, branch push or publication PR;
- Saturday recovery does not dispatch the weekly workflow;
- scheduled/public research validation does not fetch live inputs or publish research branches;
- Score v3 shadow and Score v2 predictive downstream workflows stop before frozen research
  ingestion or PR writes;
- weekly freshness health does not open/close stale-publication incidents solely because the
  governance hold intentionally freezes the last published week;
- research-evidence health does not demand new prospective evidence while the rights hold is
  active.

Manual `workflow_dispatch` paths use the same gate. The policy does not provide a bypass input.

## What remains live

The hold does **not**:

- delete, redact or rewrite any currently public Score artifact;
- change the Score v2 formula, weights, drivers or current published values;
- change Cloudflare Pages/public routing;
- delete historical Git branches/PRs/research records;
- stop read-only security, methodology or Pages posture checks that do not publish new provider
  values;
- decide provider rights;
- create private storage;
- change billing, secrets or provider credentials.

The currently published Score remains the last verified public vintage until a separately approved
path resumes publication.

## Fail-closed policy

Policy file:

`governance/score-publication-rights-gate.json`

Malformed/missing/unknown policy evaluates to HOLD.

A future `allow` state requires both:

- a named approver; and
- an HTTPS GitHub decision receipt under `usdimpact/usd-impact-pipeline`.

Changing that policy is still a repository change requiring normal protected review. The gate does
not treat the existence of an approver/receipt as proof of legal sufficiency; the reviewer must
still verify the referenced decision against #155.

## Release decision required

Before merge, owner must explicitly decide whether to **freeze new Score public/repository-visible
provider-derived evidence** while #155 is unresolved.

If the hold is approved:
1. merge only after exact-head quality/security checks;
2. verify the Friday workflow no-ops before provider retrieval in a non-provider-consuming test or
   first scheduled run;
3. verify recovery/research/prospective workflows report HOLD without writes;
4. keep #155 open;
5. separately complete the aggregate-public/private-evidence migration or document provider rights.

If the hold is not approved, keep this PR draft/unmerged and document the decision in #155 before
the next Friday publication window.
