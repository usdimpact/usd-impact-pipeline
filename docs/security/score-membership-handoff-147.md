# Score Research Membership access — implementation contract (issue #147)

Status: design and test plan only; **not a deployed authorization implementation**. Keep current deny-all HTML redirects until a server-side gate has been deployed and verified.

## Confirmed failure

`public/_redirects` redirects the dashboard and archive HTML paths to `/member-required.html` unconditionally. The CTA links to `https://www.usd-impact.com/account/?returnTo=%2Fscore%2F` but does not establish a session on `score.usd-impact.com`. A user with an active Research Membership therefore still receives the gate.

## Threat model and invariants

- Score HTML and member history are premium content. **No static origin or direct object URL may serve them without server authorization.**
- Public methodology, permitted JSON/CSV research artifacts, and existing published provenance remain publicly readable, unchanged.
- The Research Membership entitlement is independent of the legacy Guided Edition and Library Pass; neither alone authorizes Score.
- Account identity must come from the verified Supabase auth session, not from email or an account ID supplied by the browser.
- Revalidate membership on each privileged request or with a very short bounded cache and explicit invalidation on revocation/refund.
- Reject unrecognized hosts, redirect targets, cross-origin callbacks, missing/expired/replayed tickets and wrong-account sessions.
- Never place a long-lived bearer credential in an iframe URL, logs, analytics, or referrer.
- Deny access at the **origin**: do not rely on a JavaScript overlay or Cloudflare Pages `_redirects` as the only gate.

## Proposed handoff

1. Browser on `www.usd-impact.com` signs in using the existing verified session.
2. An authenticated, same-origin `POST /api/score/handoff` validates the current user, active profile and active, unexpired `research-membership` entitlement. Require CSRF/Origin validation and no-store response.
3. Issue a cryptographically random opaque **single-use** ticket, TTL <= 60 seconds, persisted as a digest in a server-side store with `account_id`, exact audience `score.usd-impact.com`, a strict allowlisted destination path, expiry and consumed flag. Do not accept arbitrary `returnTo` URLs.
4. Transfer to an HTTPS callback on the Score origin. Redeem the ticket atomically, server-to-server; bind it to a new server-managed Score session with `Secure; HttpOnly; SameSite=Lax; Path=/` cookie and explicit short expiration. Never put the Supabase access/refresh token in the URL.
5. For embedding, initiate the top-level handoff first and only then render the iframe. Where third-party-cookie restrictions apply, use a same-origin reverse-proxy route under `www.usd-impact.com` for the embedded Score content, with **server-side authorization on every protected request**. Do not loosen cookie policy or allow cross-origin token exchange via wildcard postMessage.
6. A trusted edge/server gate checks the session **before** serving `/en/`, `/es/`, `/archive/en/`, `/archive/es/` and all protected member HTML/assets. Denied requests return a non-cacheable 401/403 or a safe sign-in entry point.
7. Direct access to the Cloudflare Pages static bucket and legacy `usd-impact-pipeline.pages.dev` must be blocked for protected HTML (or those objects must no longer exist at publicly addressable paths). Preserve public machine-readable files and methodology.
8. Logout and membership revocation invalidate the server session. Set `Cache-Control: private, no-store` on personalized responses; never cache authorized HTML in a shared CDN cache.

## Routing / deployment decision

Before editing `public/_redirects`, select an enforcement deployment capable of verifying sessions **before static assets are returned** (Cloudflare Worker/Pages Functions or same-origin protected proxy). The static Pages site alone cannot implement this requirement. Keep the fail-closed redirect until the gate, ticket store, secrets, and revocation path have passed Preview tests.

## Tests required

| Case | Expected |
|---|---|
| Active Research Membership | Dashboard and member archive load after secure handoff |
| Active Library Pass only | 403, no member bytes |
| Revoked / expired / refunded Research Membership | 403, invalidated existing session |
| Anonymous / deleted / unverified account | 401/403 |
| Expired or replayed ticket | 401/403, no session |
| Altered return path / wrong audience | 400/403, no open redirect |
| Direct Pages / pages.dev / static object request | No premium HTML without authorization |
| Signed-in standalone desktop | Loads without loop |
| Embedded normal / Incognito | Works through approved same-origin delivery path |
| Public methodology and research data | Continue to load without login |
| No-store and CSP / frame-ancestors | Pass response-header checks |
| Revocation while session exists | Subsequent protected request denied |

## Release and rollback

- Preview only until all security, access, browser and direct-origin bypass tests pass.
- No changes to Score calculations, vintages, publication pipeline, data semantics, existing QA entitlements, or billing.
- Rollback means returning to the current **fail-closed** membership-required gate; never revert to public premium HTML.
- Document deployment IDs, CI checks, direct-origin tests, and QA evidence in PR before Production approval.

## Work decomposition

1. Implement the authenticated handoff issuer in `usd-impact-site` (separate bounded PR).
2. Implement the ticket store and verifier plus protected HTML origin in `usd-impact-pipeline`.
3. Wire main-site iframe to the protected same-origin path and add integration tests.
4. Remove static unconditional redirects only after the protected origin is proven.
5. Run Preview QA; submit separate Production go/no-go review.
