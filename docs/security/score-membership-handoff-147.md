# Score Research Membership access — Vercel + Supabase contract (issue #147)

Status: **draft Preview implementation; Release HOLD.** Premium Score authorization has moved off Cloudflare. Cloudflare Pages is public delivery only. Premium Score HTML is stored privately in Supabase and is authorized and served by the USD Impact Vercel application.

## Implemented architecture

1. The user signs in to the existing USD Impact account on Vercel.
2. The protected route under `/score/member/*` uses the normal USD Impact Supabase session.
3. Vercel revalidates the current `research-membership` entitlement before returning premium Score bytes.
4. Premium Score HTML is read server-side from the private Supabase `public.score_member_assets` table with a server-only secret.
5. Responses are same-origin, `private, no-store`, `noindex, nofollow`, and do not use a second Score cookie, handoff ticket, cross-origin callback, iframe credential, or Cloudflare authorization decision.
6. Cloudflare Pages serves only explicitly allowlisted public methodology, research and reproduction assets. Premium HTML is denied there even if legacy cookies, flags or secrets are supplied.
7. The retired `/score-redeem` Cloudflare endpoint returns `410` and cannot reach an asset or backend.

## Security invariants

- Research Membership is independent from Library Pass and Guided Edition access.
- Identity comes only from the verified USD Impact Supabase account session.
- Vercel revalidates the Research entitlement on each protected Score request.
- The browser never receives a Supabase server secret.
- The browser cannot select an arbitrary private asset path; only bounded Score HTML paths are accepted.
- The Supabase member-asset table is private to privileged server access. Anonymous and authenticated database clients do not receive direct table access.
- Cloudflare must never become an entitlement authority or session verifier for Score.
- No premium HTML may be publicly reachable from Pages, pages.dev, a static bucket, or an object URL.
- Public methodology and permitted research/reproduction data stay public.
- Personalized/member responses must not be shared-cacheable.

## Private asset publication

`scripts/publish_score_member_assets.py` mirrors only premium HTML into Supabase after the Score release is generated and validated.

Development safeguards:

- Development writes are pinned to Supabase project `ycstrcvshdluovtuasjc`.
- The project URL must exactly match the selected project ref.
- Publishing is disabled unless `SCORE_MEMBER_ASSET_PUBLISH_ENABLED=true`.
- The source commit must be a full Git SHA.
- Only the approved current EN/ES dashboard roots and dated EN/ES archive HTML are accepted.
- HTML containing `<script` is rejected.
- CI validates this publisher in `--dry-run` mode with no remote-write secret.

Production safeguards:

- A Production publish is rejected unless the workflow runs from `refs/heads/main`.
- A Production publish additionally requires `SCORE_MEMBER_ASSET_PRODUCTION_APPROVED=true`.
- This document does **not** grant Production approval.

## Cloudflare Pages perimeter

`functions/_middleware.js` is deliberately public-only. It:

- allows only approved USD Impact Pages hosts;
- allows only explicit public Score paths;
- denies premium dashboard/archive HTML with HTTP 403;
- returns HTTP 410 for the retired redemption endpoint;
- blocks write methods;
- contains no entitlement, ticket, session, secret, or server-to-server authorization logic.

The perimeter contract is enforced by `security/score-pages-public-only.test.mjs`.

## Website contract

The companion website PR is `usdimpact/usd-impact-site#836`.

Its draft member route:

- serves `/score/member/:path*` from Vercel;
- uses the existing site Supabase session and Research Membership entitlement;
- reads premium HTML from private Supabase storage;
- does not issue or redeem Score handoff tickets;
- does not create a second Score session cookie;
- does not depend on Cloudflare for authorization.

## Required acceptance

| Case | Expected |
|---|---|
| Anonymous `/score/member/*` | 401, no premium bytes |
| Signed-in non-Research user | 403, no premium bytes |
| Active Research Membership | Member dashboard/archive served by Vercel |
| Revoked / expired / refunded Research Membership | Subsequent protected request denied |
| Invalid member path | 404, no private lookup |
| Unsupported method | 405 |
| Cloudflare Pages premium HTML path | 403 |
| Retired Cloudflare redemption path | 410 |
| Public methodology/research path | Continues to load without membership |
| Member response cache policy | `private, no-store` |
| Member response indexing policy | `noindex, nofollow` |
| Provenance | Response carries the source pipeline commit |

## Current Preview evidence

- Pipeline PR #148 exact head must be read from GitHub immediately before acceptance; do not rely on older handoff SHAs.
- Development `score_member_assets` is populated from the current reviewed pipeline source and records both source commit and source blob SHA.
- The website Preview performs the authorization decision; Cloudflare performs none.
- Anonymous member-route acceptance is expected to fail closed.
- An authenticated browser test must use an explicitly approved Development QA account/session; do not impersonate or mutate a customer account merely to complete QA.

## Release and rollback

- Both companion PRs stay draft/unmerged until a separate release decision.
- No Production domain, DNS, environment activation, database/customer mutation, Worker deployment, or promotion is authorized by this document.
- Rollback is fail-closed: disable the Vercel member gate and preserve the Cloudflare public-only perimeter.
- Historical ticket/session migrations may remain for migration-history consistency even though runtime authorization no longer uses them.

## Release state

**RELEASE: HOLD**
