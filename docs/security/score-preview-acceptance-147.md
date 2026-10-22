# Score Research Membership — isolated Preview acceptance plan

## 2026-10-22 — Cloudflare Preview secret checkpoint and remaining provider-auth gate

- User's authenticated Cloudflare Pages UI screenshot confirms the **Preview** environment, `SCORE_EDGE_SHARED_SECRET` displayed as encrypted Secret, `SCORE_EDGE_GATE_ENABLED=false`, `SCORE_EDGE_REDEMPTION_ENABLED=false`, and preview host pin. Prior Preview Runtime screenshot independently showed **Fail closed**. **Matching secret bytes to Vercel have not been verified**; screenshots of encrypted secrets cannot establish equality.
- Cloudflare Preview `SCORE_BACKEND_URL` and `SCORE_VALIDATION_BACKEND_URL` still visibly refer to older Vercel Preview deployment `usd-impact-site-8lvzao44t-usd-impact.vercel.app`. Correct reviewed current exact deployment is `dpl_AwvQzAyJobkAQo9oYfjZ4o1sieAQ`, commit `4163aadbd86093e25fc8e27f392c97a3df291c80`, host `usd-impact-site-qjfsh5lm7-usd-impact.vercel.app`; **manually update only the two Preview backend URLs** to exact `/api/score-edge-redeem` and `/api/score-edge-validate`, respectively, keep flags OFF. New Cloudflare Preview deployment required after environment changes.
- Latest website PR #836 exact-head CI: **13/13 PASS**. Score pipeline PR #148 exact-head weekly Score quality: **PASS** at [run 39695029466](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/39695029466).
- Read-only external request to the exact current Vercel Preview API reported **login_required** from Vercel Deployment Protection. Authorized Vercel connector GET against the same private API reached application and returned **405** as expected for POST-only endpoint. Therefore Cloudflare-to-Vercel *server-to-server* authorization is **not proven** and will not succeed unauthenticated: establish an independently reviewed, narrow Trusted Sources/OIDC or equivalent approved provider access pattern before activating either Score gate. Do **not** disable deployment protection, create a project-wide bypass, expose keys in logs, or change Production as a shortcut.
- Cloudflare Preview anonymous `/en/` remained **403**; public `/data/score_v2_methodology.json` remained available. All active-member redemption, membership revocation, replay, and standalone/iframe live browser scenarios remain **NOT RUN**. Release remains HOLD.


Status: **PARTIAL ACCEPTANCE EVIDENCE — REAL AUTHENTICATED PREVIEW HANDOFF STILL NOT RUN**. No Production configuration, database migrations, secrets, or feature flags are changed by this document.

## Alternative verification checkpoint — 2026-10-22

| Evidence | Result and boundary |
|---|---|
| Website PR #836 at `2fdf0df46b160164f0118dc10faa5cc19e2e9e31` | 13 GitHub workflow checks successful; Vercel Preview READY at `dpl_3fZhsh7asKf7sXwkxJ3YSeX4zUVW`; browser requires Vercel Preview authentication |
| Score PR #148 at `63409bcf199b7be647607aab0172ce2acc3addb6` | Score quality CI success: https://github.com/usdimpact/usd-impact-pipeline/actions/runs/39691657705 |
| Cloudflare Score Preview (TinyFish, unauthenticated) | `/en/` blocked with no premium dashboard content; approved `/data/score_v2_methodology.json` readable |
| Development Supabase transactional authorization test | Existing active Research Membership authorized; unknown account denied; ticket issue, duplicate refusal, atomic consume, replay denial, invalid audience/path/expired refusal, session create/lookup/duplicate refusal PASS. Explicit ROLLBACK; confirmed 0 tickets, 0 sessions and 3 unchanged active Research entitlements |
| New isolated contract integration `security/score-preview-flow-contract.test.mjs` | Cloudflare middleware and redemption handler joined through a **mock** private backend: one-time POST -> 303 secure cookie -> protected GET -> membership recheck -> post-revocation denial; replay, disabled flags, unapproved host and outage fail closed. Test PASS in CI, **NOT a real authenticated hosted Preview test** |
| Member-required recovery path | Draft PR updates the plain denial response with an HTTP 403 safe return link to the first-party `/score/` entry. Preview static `/member-required.html` link verified by TinyFish; fully hosted current 403 HTML and authenticated redirect chain still need browser recheck |
| Cloudflare administration | TinyFish profile setup attempted; Cloudflare's verification challenge failed in the hosted setup browser. Do not bypass bot verification or assume credentials are captured. Use ordinary authenticated Cloudflare dashboard access if needed |

**Remaining HOLD gates:** secure Cloudflare Preview variables and exact host pinning; shared-secret pairing with the *Preview-only* Vercel environment; positive authenticated live ticket/session flow and revoke-after-issue; authorized direct Cloudflare origin/asset regression; private/normal browser tests; independent security review. No Production release.

**Preview cookie caveat:** Vercel `.vercel.app` and Cloudflare `.pages.dev` are different browser sites. A `SameSite=Lax` session cookie is not suitable as proof that the embedded iframe works across these Preview sites. Check standalone first and use an independently reviewed same-site or same-origin delivery path for iframe acceptance; do not weaken cookie settings or claim Production-equivalent browser acceptance from this cross-site Preview.


## Additional cross-service Preview checkpoint — 2026-10-22

- Website [PR #836](https://github.com/usdimpact/usd-impact-site/pull/836) commit `3a614f74fac0e4b681728cca96536455394a45dd` passed **all 13 exact-commit GitHub checks**, including Web quality, Dependency Review and CodeQL. Vercel Preview deployment `dpl_5kVy9EjEssqw7RTCrpKtZX6w8KHd` is **READY**, pointing to the exact `fix-score-membership-handoff.usd-impact-pipeline.pages.dev` branch Preview origin. Preview builds initially rejected this hostname in the CSP post-build validator; the validator now uses the same strict pinned Preview origin and `VERCEL_ENV` as Astro's CSP. **No Production build/config change.**
- The isolated Vercel PR branch now has `SUPABASE_URL=https://ycstrcvshdluovtuasjc.supabase.co` and a Development **publishable** key, both scoped to Preview on `feat/score-membership-handoff-147`. The three Vercel Score activation flags were explicitly set to `false` on that branch. A new 64-character cryptographic edge shared secret is installed as an **encrypted branch-specific Preview** variable; Cloudflare's matching encrypted Preview copy is **not yet verified**.
- Protected Vercel deployment route tests via Vercel's own authenticated fetch confirmed `GET /api/score-handoff`, `GET /api/score-edge-redeem` and `GET /api/score-edge-validate` all return **405 Method Not Allowed**, proving the expected rewrite routes are present. The served CSP includes the pinned Cloudflare Preview in both `frame-src` and `form-action`. The Score page itself redirected to USD Impact sign-in without an authenticated Research Membership session. **No successful live POST redemption is claimed.**
- Read-only Cloudflare Preview fetch confirmed `GET /en/` returns **403** and approved `GET /data/score_v2_methodology.json` remains available. The user independently verified the Cloudflare Preview environment is selected with Runtime **Fail closed**; edge gate and redemption activation flags are still `false`.
- **Outstanding blocking prerequisites**: (1) configure Cloudflare's corresponding `SCORE_EDGE_SHARED_SECRET` as an encrypted **Preview-only** secret; (2) scope a Development-only `SUPABASE_SECRET_KEY` to the exact Vercel Preview branch using private Supabase dashboard, without sharing its value; (3) resolve server-to-server access through Vercel Authentication with a separately approved narrow mechanism; (4) obtain a fresh Vercel Preview deployment after adding secrets and pin its exact backend HTTPS origin on Cloudflare Preview; (5) verify positive active-member flow, replay/revocation and no cross-site iframe cookie regressions. Do not disable Vercel Preview protection or create a project-wide automation bypass merely for convenience.
- Vercel Production was read-only verified **unchanged** at `0be0809caa61f0de2315765b40cf57961420bdc6` (`dpl_8TXfGqeWfAVg1NWRFoxsVc8Vofzy`). No merge, entitlement, payments, or Production changes occurred. **RELEASE HOLD.**

## Boundaries and prerequisites

- Website draft PR #836 and Score draft PR #148 must remain unmerged. Confirm current Preview deployment IDs and CI success immediately before testing.
- Use a separate non-Production Supabase project or isolated test database with only the reviewed Score ticket/session migrations. Do not apply SQL to Production.
- Configure Preview-only server-to-server shared secret (minimum 32 characters), HTTPS Vercel backend endpoints, and Cloudflare Preview routing. Keep Production `SCORE_HANDOFF_ISSUANCE_ENABLED`, `SCORE_EDGE_REDEMPTION_ENABLED`, and `SCORE_EDGE_GATE_ENABLED` disabled.
- Use dedicated test identities: active Research Membership, Library Pass-only, expired/revoked membership, and anonymous. No real customer entitlement modifications.
- The Score redemption function accepts the Production hostname `score.usd-impact.com` and, only when `SCORE_PREVIEW_REDEMPTION_HOST` is explicitly configured, its exact matching `*.usd-impact-pipeline.pages.dev` Preview hostname. Confirm the pinned Preview hostname and isolated routing before browser redemption acceptance; do not use a broad wildcard or Production credentials.
- Validate that Preview routing uses the consolidated website account API actions. Current draft Score backend URL path checks refer to `/api/score-edge-redeem` and `/api/score-edge-validate`; verify they resolve via the website's Vercel rewrites before testing.

## Development database checkpoint (2026-10-19)

**Development only:** The `usd-impact-development` Supabase project now has three applied migrations:

| Supabase migration version | Source migration | Verification |
|---|---|---|
| `20261019170710` | `20261019010000_score_handoff_tickets.sql` | Table exists, empty, RLS enabled, digest/expiry/audience/path constraints |
| `20261019170741` | `20261019020000_score_member_sessions.sql` | Table exists, empty, RLS enabled, digest/session-expiry constraints |
| `20261019170935` | `20261019030000_score_handoff_account_indexes.sql` | Both account-ID foreign-key index advisories cleared |

The security advisor reports `rls_enabled_no_policy` as an informational result for both intentionally server-only tables. Its warning about the existing `request_account_deletion()` SECURITY DEFINER function is unrelated to this handoff. The account-ID index advisory for pre-existing `subscription_events` is also unrelated.

**Not yet verified:** direct RPC privilege/role execution tests, real ticket issue/consume/replay, Research Membership test identities, private backend connectivity, isolated shared secrets, same-origin embedding, and the 12 live browser/security scenarios below. No Score ticket or session rows were created, and no Production database migration was applied.

Website Vercel Preview flags `SCORE_HANDOFF_ISSUANCE_ENABLED`, `SCORE_EDGE_REDEMPTION_ENABLED` and `SCORE_EDGE_VALIDATION_ENABLED` were each verified as `false` on the handoff branch. Score Preview is available at `https://fix-score-membership-handoff.usd-impact-pipeline.pages.dev`; its private member paths remained denied and approved public research routes were observed accessible. **All acceptance rows below remain NOT RUN pending controlled credential wiring.**

## Acceptance matrix (record actual status, not assumptions)

| Test | Expected | Result |
|---|---|---|
| Gate disabled, anonymous | 403 and no premium bytes | NOT RUN |
| Active member, valid single-use ticket | POST redemption sets secure HttpOnly cookie and 303 to allowlisted path | NOT RUN |
| Ticket replay or expired ticket | No session; 401/403 | NOT RUN |
| Wrong path, wrong audience, malformed ticket | No cookie, no redirect to attacker origin | NOT RUN |
| Active session, authorized backend | Dashboard and member archive load with private/no-store headers | NOT RUN |
| Library Pass only, anonymous, unverified | 401/403; no premium bytes | NOT RUN |
| Revoked/refunded membership after session issued | Next protected request denied | NOT RUN |
| Validation backend unavailable or wrong shared secret | Fail closed; no premium bytes | NOT RUN |
| Direct Cloudflare Pages custom and pages.dev hosts, assets, HTML | No premium bytes without authorization | NOT RUN |
| Standalone sign-in and embedded normal/incognito | No loops; iframe isolation enforced | NOT RUN |
| Public methodology and approved research data | Accessible per public policy | NOT RUN |
| Cookie, CSP, cache, logs, referrer | Secure attributes, no-store, no ticket or token leaks | NOT RUN |

## Execution sequence

1. Verify PR heads and successful checks. Record deployment IDs and the exact isolated test hostnames.
2. Review migrations, secret placement, Preview hostname validation, and backend rewrite paths. Stop if any route is inconsistent or would require a Production change.
3. Test fail-closed access on each Preview/direct origin before enabling any Preview-only gate.
4. With isolated Preview credentials and entitlement, test issuance, one-time redemption, cookie scope, and authorized protected content.
5. Test negative identities, replay, expiry, revocation, backend outage, direct-origin bypass, and public-resource preservation.
6. Test standalone and embedded browser flows; collect sanitized HTTP statuses, headers, timestamps, and deployment identifiers. Never log ticket/session values.
7. Reset Preview flags to disabled and remove disposable credentials; attach evidence to both PRs for a separate go/no-go decision.

**Stop condition:** Any protected HTML accessible without verified authorization, any cross-origin credential leak, or any request that reaches Production systems ends acceptance immediately. Release remains HOLD until all required rows pass.
