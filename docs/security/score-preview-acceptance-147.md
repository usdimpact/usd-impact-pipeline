# Score Research Membership — isolated Preview acceptance plan

## 22 October 2026 — verified same-day checkpoint (supersedes earlier package blocker)

**Actual source commit:** `fcd223cfee232aba4398d91b2baedde851cfd792` on the existing draft Score PR #148. The broker client now has an 18-second abort deadline for its Development Edge HTTP request; new credential-isolation regression tests passed.

- [Full Score quality CI #39826795072](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/39826795072): **COMPLETED SUCCESS**, including live anonymous Development broker and Cloudflare Pages disabled-state POST checks.
- [Isolated Worker static preflight #39826795059](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/39826795059): **COMPLETED SUCCESS**.
- [Pinned Wrangler package verification #39826795079](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/39826795079): **COMPLETED SUCCESS** using genuine **Wrangler 4.135.0**, reading **156** static asset files and producing a 12.04 KiB (4.12 KiB gzip) Worker JS bundle via `wrangler deploy --dry-run`. Logs explicitly show `--dry-run: exiting now`, with **no Cloudflare deployment or credentials**. Earlier npm registry failures are resolved **for this GitHub Actions runner**.
- **Boundary:** This Wrangler dry-run validates the *top-level* bundle and assets. It does **not** create a Workers Preview, prove that `previews.ratelimits` bindings exist, set a Preview-only secret, establish a Preview URL, or run authenticated member browser tests.
- Independently verified Pages premium `/en/` and `/archive/es/` still return HTTP **403**; public methodology JSON remains accessible. The Development broker is hosted at version 2 but activation remains `SCORE_PREVIEW_BROKER_ENABLED=false`; Development ticket and session tables contain **zero** rows.
- **No login bypass:** Opera is still disconnected, and the headless Cloudflare login previously failed. The next provider action requires secure Cloudflare management access. Do not put credentials in a PR workflow or chat; the Dev Worker remains source-only. The existing Pages Preview and Production are unchanged.

**Release HOLD:** Both PRs must stay draft/unmerged. The next controlled step is one *disabled* isolated Workers Preview, its genuine provider URL, exact isolation and rate-limit verification, then separate entitlement, replay, revocation and iframe acceptance. No membership activation based on successful package build alone.


## 2026-10-22 — Development broker v2 hardening checkpoint

**Implementation commit:** `6737d07621465fa2c7ec504f29ca726eaf48a76c` in draft Score PR #148. The full [source-commit CI](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/39711365461) passed. The broker now accepts only exactly `application/json` (optional UTF-8 charset), rejects invalid or oversized `Content-Length`, still limits streamed body data to 512 bytes, and caps each private Development RPC fetch at five seconds (fail closed on timeout).

**Deployed after the source-commit CI pass:** Supabase `usd-impact-development` (`ycstrcvshdluovtuasjc`) Edge Function `score-preview-broker` **version 2**, same isolated function ID `66136fed-7728-49be-94a5-a6568b787881`, bundle digest `d084d1b87a6ef9d451d123f09bbfe7cf2712fbf245eddd6d6fd5ab1530a878bf`. Re-fetched the deployed bundle and verified source files and default-off gate. JWT gateway setting remains `verify_jwt=false` specifically because the disabled server-to-server function uses its own shared-secret checks if authorized in the future.

**Post-deployment live acceptance:** A new latest-head draft quality run must complete successfully and demonstrate that the *deployed v2* broker returns HTTP `503` with `{"allowed":false}` to the credential-free POST; Cloudflare Preview redemption must continue returning HTTP `503` to synthetic POST. The earlier successful source-commit CI occurred before this v2 deployment and does not independently verify v2. Until the latest-head result is recorded, mark the v2 live denial as pending.

**Development data:** read-only query confirmed 0 ticket rows and 0 Score-session rows. No DB migration, entitlement update, key provisioning, Cloudflare setting, PR merge or Production change.

**Provider isolation decision:** Cloudflare *Pages* Preview settings are shared across preview branches; do not place any privileged Supabase key or shared broker credential there for activation without an independently reviewed security boundary. Cloudflare *Workers Previews* provides branch-specific secrets and bindings (see https://developers.cloudflare.com/workers/previews/), potentially supporting a separate isolated migration later; this has **not** been implemented or deployed. Owner's Cloudflare login was blocked in TinyFish; Opera Browser Connector was disconnected. Neither is needed for disabled-stage QA, but private provider configuration and actual Research Membership end-to-end acceptance remain blocked.

**Release remains HOLD:** pending isolated Preview credential topology, inbound request throttling, authorized live member/denied/replay/revocation testing, cross-site iframe/standalone browser behavior, and separate Production release signoff.


## 2026-10-22 — Development broker deployed and live disabled-state acceptance VERIFIED

**Actual Development deployment:** project `usd-impact-development` (`ycstrcvshdluovtuasjc`),
Supabase Edge Function `score-preview-broker`, version 1,
ID `66136fed-7728-49be-94a5-a6568b787881`.
The hosted bundle includes `index.ts`, `security/score-preview-broker-server.mjs` and
`security/score-preview-dev-rpc.mjs`. The function uses `verify_jwt=false` because it
performs explicit server-to-server shared-secret authentication; this does **not** mean
membership validation is enabled. The operator saved the Development-only
`SCORE_PREVIEW_BROKER_ENABLED` secret with the literal value `false`.

**Live, anonymous checks:**
- [GitHub Actions run 39706865346](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/39706865346)
  **PASS**, including one synthetic, credential-free JSON POST to the deployed
  Development function, which returned `503` and exactly `{"allowed":false}`.
  No real account, ticket, shared secret or API key was transmitted.
- Anonymous GET to broker returned `405` (method denied).
- Cloudflare branch Preview `GET /en/`, `/es/`, `/archive/en/`, `/archive/es/`,
  `/en/index.html`, `/archive/en/index.html`, and `/index.html` returned `403`.
- Public `/data/score_v2_methodology.json` and
  `/data/research/score_v2_point_in_time_latest.json` remained accessible.
- Protected Vercel branch Preview API still required Vercel login.
- Read-only Development database check: 0 ticket rows and 0 Score-session rows.

**What this does NOT prove:** authenticated one-use ticket redemption, simultaneous
replay resistance in the hosted environment, ongoing Research Membership revocation,
Browser normal/Incognito and iframe behavior, or per-client inbound rate limiting.
Supabase's published recursive/nested-function rate limit applies to outbound Edge-to-Edge
calls, **not inbound** calls; it is not an abuse-control substitute for this endpoint.
Cloudflare Pages Preview environment secrets are not branch-scoped: do **not** assume
the existing Cloudflare Preview shared secret is isolated to this PR.

**Remaining activation gates (HOLD):** provider-reviewed isolation or a separate
Preview-only Pages deployment/credential boundary; dedicated Development
shared-secret provisioned securely to both providers (never in chat, source or logs);
an independent inbound throttling/abuse-control solution; live authenticated
and denied entitlement fixtures; replay/expiry/revocation and direct-object bypass
evidence; standalone and embedded-browser acceptance. Neither draft PR may merge
or change Production until separately approved for release.

Historical design and staging checkpoints below predate this deployment.

## 2026-10-22 — SUPERCEDING IMPLEMENTATION: Development Edge broker staged, not deployed

**Preferred candidate after security correction.** No privileged `sb_secret_` key is to be provisioned in Cloudflare Pages Preview, which has environment-scoped secrets. The earlier direct-Cloudflare-to-Development-RPC approach is not an activation option. Its database RPC adapter is now imported only by the isolated Development Edge broker; Cloudflare imports a **broker client** that has no access to the database key.

**Reviewed code boundaries:**
- `security/score-preview-broker-server.mjs`: fixed `redeem` and `validate` operations only, no raw account-ID or arbitrary SQL/RPC parameters. Requires POST, exact Development Supabase hostname and Edge Function path, JSON under 512 bytes, short opaque bearer, high-entropy shared secret with constant-length comparison, and explicit `SCORE_PREVIEW_BROKER_ENABLED=true` flag. Any error is fail-closed and sanitized. Only the broker uses the Development Supabase project's automatic `SUPABASE_SECRET_KEYS.default` with `apikey` (no bearer key in a browser or Cloudflare).
- `supabase/functions/score-preview-broker/index.ts`: a **source-only** Edge Function entrypoint for Development. If and only if independently approved, deploy to Development `ycstrcvshdluovtuasjc` with `verify_jwt=false` plus verified high-entropy `SCORE_EDGE_SHARED_SECRET` environment secret and `SCORE_PREVIEW_BROKER_ENABLED` flag initially `false`. Do not deploy to `usd-impact-production`; do not deploy at all before reviewing auth, rate limit and provider configuration. The platform's automatic `SUPABASE_SECRET_KEYS` is expected to be present; failure is denied.
- `security/score-preview-broker-client.mjs`: Cloudflare sends a signed-secret-protected POST only to exact `https://ycstrcvshdluovtuasjc.supabase.co/functions/v1/score-preview-broker` using the existing encrypted `SCORE_EDGE_SHARED_SECRET`. It never holds, forwards or needs the full Development Supabase key. All other backend destinations and HTTP redirects are denied.
- `functions/_middleware.js` and `functions/score-redeem.js`: route through broker **only if** Cloudflare `SCORE_DEV_BROKER_ENABLED=true` on the exact isolated `fix-score-membership-handoff.usd-impact-pipeline.pages.dev` hostname. Independently require `SCORE_EDGE_GATE_ENABLED=true` for premium GET and `SCORE_EDGE_REDEMPTION_ENABLED=true` for one-time POST. Caller `Origin` for ticket redemption must exactly match the verified stable Vercel PR alias `https://usd-impact-site-git-feat-score-membership-han-fb189b-usd-impact.vercel.app`. All these switches remain OFF/unset. Old protected Vercel backend still exists as disabled fallback but is not part of the broker Preview test.
- Tests `security/score-preview-dev-rpc.test.mjs`, `score-preview-broker-server.test.mjs`, `score-preview-direct-flow.test.mjs` exercise modern key header, one-use digest, broker authentication, unsupported actions, revoked membership, malformed host/Origin, public methodology, and network outage. **Tests are simulated**. New code cannot be labeled live accepted from CI success.
- Development RPCs and private tables previously verified RLS/permissions (service_role only), no migrations. Website PR #836 modern-key adapters updated to `apikey` without `Authorization: Bearer sb_secret_`; exact-commit website CI passed 13/13.

**Next gates, without overlapping work:** (1) independent security review of new broker and its environment scope; (2) after approval, Development-only Edge deployment with auth flag false, no Production access; (3) provider-side Dev Edge `SCORE_EDGE_SHARED_SECRET` entered securely (do not paste into chat), initial `SCORE_PREVIEW_BROKER_ENABLED=false`; (4) non-credentialed remote 403/405 smoke test; (5) explicitly approved Preview-only three-flag activation and controlled active/denied membership E2E; (6) replay, direct static bypass, revocation, normal and Incognito standalone, iframe cookie acceptance and rollback tests; (7) separate Production approval. **No step is authorized by a source-code CI pass alone.**


## Security decision — 2026-10-22: do not provision privileged Supabase key in shared Cloudflare Pages Preview

**The direct Cloudflare -> Development Supabase RPC implementation is an INACTIVE EXPERIMENT ONLY, not an approved activation plan.** Its unit and integration-mock tests are useful for the ticket/session contract, but passing CI does not authorize provisioning `SCORE_PREVIEW_SUPABASE_SECRET_KEY` into the existing Cloudflare Pages Preview environment. Pages Preview variables and secrets are environment-scoped; no branch-specific binding isolation has been established for `fix-score-membership-handoff`. Any service-role-equivalent `sb_secret_` key bypasses all Development RLS, and storing it in a shared Preview environment could expose it to other preview branches. **Do not create/import that Cloudflare secret and do not set `SCORE_DIRECT_DEV_BACKEND_ENABLED=true`.**

**Preferred security architecture for a separate follow-on, still no new PR or Production change:**
1. Keep ticket issuance on the already protected Vercel website Preview using the existing Development Supabase RPCs. Keep `SCORE_HANDOFF_ISSUANCE_ENABLED=false` until full acceptance.
2. Author an isolated **Development Supabase Edge Function broker** with `verify_jwt=false` only when its own fail-closed server-to-server authentication is demonstrably verified. It must check a dedicated random `SCORE_EDGE_SHARED_SECRET` using constant-time comparison and reject every other request/action. No direct public membership lookup by account ID or arbitrary RPC proxy. The broker can use Supabase's own automatically injected Development `SUPABASE_SECRET_KEYS` server-side instead of copying a service-role key to Cloudflare.
3. Cloudflare Preview uses its existing encrypted `SCORE_EDGE_SHARED_SECRET` to call the exact allowlisted Development broker endpoint. Both initial redemption and every subsequent session validation must execute the existing Development RPCs inside the broker, enforcing atomic ticket use and current entitlement. Treat any DB or broker failure as 403/503 and never serve premium HTML.
4. Do not deploy or enable the broker until exact-host code tests, independent review of service-to-service authentication, rate limits, body-size bounds, log redaction and negative routes have passed. An additional **Development-only Edge Function secret** would need controlled provider entry; do not transmit it in GitHub or chat.
5. Retain Vercel Standard Deployment Protection and its existing Trusted Source entry unchanged; never add an unverified external OIDC issuer or project-wide bypass. Keep Cloudflare Preview edge flags `false` and Runtime Fail closed; no Production changes. Verify standalone and iframe separately, since `.vercel.app` / `.pages.dev` cookies are cross-site during Preview.
6. Once broker design passes review, supersede and remove the dormant direct-Database Preview experiment before merge; do not keep competing privileged credential paths in release code.

**Live status:** Score PR #148 mock CI passed; website PR #836 13/13 GitHub checks passed, latest Preview READY. No live authenticated POST ticket exchange, Production merge, direct database secret, broker Edge Function deployment or activation has occurred. **HOLD**.


## 2026-10-22 — narrower Development-only candidate: direct Cloudflare -> Development Supabase RPC

**Status: CODED AND UNIT/INTEGRATION-MOCKED; NOT ACTIVATED OR HOSTED-ACCEPTED.**
This route avoids the Cloudflare -> Vercel Preview service-to-service hop, which is blocked by Standard Protection. **Keep Vercel Authentication ON and do not change any Trusted Source**.

- New `security/score-preview-dev-rpc.mjs` uses Cloudflare Web Crypto (not Node) and the existing Development-only `ycstrcvshdluovtuasjc.supabase.co` REST RPC endpoint. The project ID is **hardcoded and reviewed**, never supplied by HTTP request or configurable Production secret. The only privileged credential is `SCORE_PREVIEW_SUPABASE_SECRET_KEY`, read server-side from a Cloudflare **Preview Secret**; it is never bundled into a page or response. REST requests use `apikey` with modern `sb_secret_` credentials and `redirect:error`, not `Authorization: Bearer sb_secret_`.
- **Three independent activation requirements**: (1) `SCORE_DIRECT_DEV_BACKEND_ENABLED=true` to select this adapter, (2) `SCORE_EDGE_REDEMPTION_ENABLED=true` for redeem route, and (3) `SCORE_EDGE_GATE_ENABLED=true` for premium HTML. All are **OFF/unset now**. The direct adapter independently refuses any hostname other than `fix-score-membership-handoff.usd-impact-pipeline.pages.dev`; Production `score.usd-impact.com` can never query the Development database through it.
- The browser handoff must come from exact Vercel **stable PR branch alias** `https://usd-impact-site-git-feat-score-membership-han-fb189b-usd-impact.vercel.app` with an exact `Origin` header and POST form body containing only an opaque 43-character ticket. No browser bearer ticket in URLs, query strings, localStorage, or referrers. The hostname was obtained from Vercel's live deployment alias API, not invented.
- On redeem: SHA-256(ticket), atomically consume the existing `score_ticket_consume_atomic` row, verify hash/audience/return path/expiry/account ID, call `score_membership_active`, mint an independent random 32-byte token, atomically `score_session_create` its SHA-256 digest after another current-entitlement check, set `__Host-score_session` Secure/HttpOnly/SameSite=Lax host-only cookie, and redirect only to allowlisted paths. Every protected GET/HEAD calls `score_session_lookup`, whose Development RPC checks that Research Membership remains active (revocation fail closed). Public approved methodology artifacts remain on the existing explicit public allowlist.
- **Read-only verified Development database contract:** `score_ticket_consume_atomic`, `score_membership_active`, `score_session_create`, and `score_session_lookup` are `SECURITY INVOKER`, executable by `service_role` only, not `anon` or `authenticated`; ticket and session tables have RLS ON and no anonymous/authenticated SELECT. No SQL migrations or account updates in this candidate.
- Two new `security/*.test.mjs` files exercise digest parity with Node's SHA-256, exact hostname and browser-origin pinning, atomic one-use redemption/replay refusal, encrypted-key-only backend requests, per-request membership revocation, anonymous/Library-only denial, missing-flag/invalid-key/outage failures, and public artifact isolation. These tests mock the Development REST API; they are not hosted/real-browser acceptance.
- Updated website PR #836 RPC adapters to authenticate modern Supabase REST using `apikey` only, no `Authorization: Bearer sb_secret_`; additional tests guard no cross-origin credential forwarding.
- **Manual configuration NOT YET AUTHORIZED OR DONE:** after independent review, create a *new, separately rotatable Development-only* `sb_secret_` key in Supabase (do not reuse the Vercel key or touch the Production project), store as Cloudflare Pages **Preview Secret** `SCORE_PREVIEW_SUPABASE_SECRET_KEY`. First add `SCORE_DIRECT_DEV_BACKEND_ENABLED=false`; keep both edge flags `false`. Never paste key into chat, GitHub, logs or screenshot. This is a powerful `service_role` key that bypasses RLS, so the extra provider trust boundary needs explicit independent review.
- **Required live acceptance before flag activation or merge**: exact-head CI on both PRs; published Cloudflare branch Preview contains new Worker code and secret; authorized reviewer confirms minimal Dev-only key handling; Vercel stable branch alias is authenticated; approved controlled QA member can issue and consume exactly one ticket; replay, revoked account, expired, Library-only, anonymous, direct-host bypass all deny; session cookie persistence works in standalone browsers, while cross-site `vercel.app`/ `pages.dev` iframe cookie behavior must be separately verified, not assumed; rollback disables three Preview flags, redeploys, and observes premium 403. **DO NOT claim Production equivalent iframe acceptance or unlock Production**.
- **No deployment protection change, new Vercel/Render project, Production secret, outbound email, commerce mutation, or new overlapping PR**. Legacy Vercel backend URLs and shared secret remain configured but unused when direct mode is explicitly enabled on the isolated Preview hostname.


## 2026-10-22 — Vercel Trusted Sources decision (no rule changed)

- Operator's authenticated Vercel dashboard screenshot confirms `usd-impact-site` uses **Vercel Authentication ON / Standard Protection**; Password Protection OFF. Under **Trusted Sources**, the single visible entry is `usd-impact-site (This project)`, granting its own matching-environment OIDC tokens and **development → preview**. This is Vercel-issued project identity, **not** Cloudflare Pages identity. Leave existing protection and self-source unchanged.
- Vercel documents that Trusted Sources can authorize external OIDC issuers if the caller actually sends a short-lived signed JWT in `x-vercel-trusted-oidc-idp-token` and the issuer, claims and target environment match a narrowly configured rule. Cloudflare Pages Functions do **not** automatically receive the existing Vercel project's OIDC token. No suitable *outbound Cloudflare workload OIDC issuer, token acquisition flow or signed claim set* is verified for this Preview. **Do not register a guessed issuer or trust Cloudflare hostname/origin headers as workload identity**.
- Read-only Vercel project connector confirms project `ssoProtection.enabled=true` with `deploymentType=all_except_custom_domains`; exact current Vercel deployment `dpl_AwvQzAyJobkAQo9oYfjZ4o1sieAQ` remains protected. The prior GET 405 via authenticated connector does not establish Cloudflare's unauthenticated ability to POST. Score member Preview `/en/` remains 403 to unauthenticated users.
- **Design gate**: before any Preview flag activation, select and review a secure server-to-server access architecture: (A) a verified external OIDC issuer with exact workload/Preview claims and short TTL; or (B) a wholly isolated Preview-only private API service that uses an independently audited shared-secret authorization boundary, without changing main-site Vercel protection. A GitHub Actions OIDC token can validate GitHub-to-Vercel CI, but cannot stand in for Cloudflare Pages at runtime. Never use a project-wide Vercel automation bypass or exempt the current Preview from deployment protection merely to pass this test.
- **Release decision: HOLD** until the selected service-to-service pattern passes independent security review, exact-host Preview POST handoff and revocation/replay browser acceptance. No new Trusted Source rule was added; no deployment protection, secret, entitlement, Production or Preview activation setting changed at this checkpoint.


## 2026-10-22 — operator Preview URL update observed (read-only)

- Authenticated Cloudflare Pages UI screenshot shows **Preview** selected, both `SCORE_BACKEND_URL` and `SCORE_VALIDATION_BACKEND_URL` changed to current Vercel Preview hostname `usd-impact-site-qjfsh5lm7-usd-impact.vercel.app`. The input boxes truncate the URL tails, so the required exact suffixes `/api/score-edge-redeem` and `/api/score-edge-validate` remain **manual visual confirmation pending**; screenshot also does not independently prove config save/redeployment.
- Encrypted Cloudflare `SCORE_EDGE_SHARED_SECRET` remains listed, `SCORE_EDGE_GATE_ENABLED=false`, `SCORE_EDGE_REDEMPTION_ENABLED=false`; previous Runtime **Fail closed** screenshot confirmed. Secrets must not be compared or displayed in screenshots. Verified Vercel Preview deployment `dpl_AwvQzAyJobkAQo9oYfjZ4o1sieAQ` remains READY on exact website commit `4163aadbd86093e25fc8e27f392c97a3df291c80`. Score pipeline quality passed prior PR commit; next doc-only CI is pending after this change.
- Read-only test: current Vercel Preview validation GET route returned **405** via authenticated Vercel tool; Cloudflare Preview member `/en/` remained **403** (correct anonymous denial), approved methodology remained publicly available. These are **NOT** authenticated cross-service POST tests or successful membership access.
- **RELEASE HOLD**: Cloudflare-to-Vercel call still cannot pass Vercel Preview Deployment Protection unauthenticated. Vercel Trusted Sources can accept approved short-lived external-service OIDC identities, but Cloudflare Pages must first have a verified trusted OIDC issuer/token acquisition path. Do not disable Vercel protection, deploy a project-wide bypass, or enable either gate. Require separate security approval for any access-control rule and Preview-only positive member tests.

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
