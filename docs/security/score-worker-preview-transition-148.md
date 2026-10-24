## Current live infrastructure checkpoint — 22 October 2026: Preview assets attached, access OFF

**Provider-verified after GitHub Codespaces authenticated Wrangler Preview upload:** isolated Cloudflare Worker `usd-impact-score-isolated-dev`, Preview `pr-148`, at [actual provider-issued URL](https://pr-148-usd-impact-score-isolated-dev.michael-w-d0b.workers.dev). Latest Preview deployment **`d39e2b76-785d-4674-bb6c-83c372b2bac8`** created at **2026-10-22T19:01:59Z**. The Cloudflare deployment API returns the **`ASSETS` binding** plus `assets.config.run_worker_first=true`, `not_found_handling=none`, `base_path="/"`, `html_handling=auto-trailing-slash`. The Wrangler command completed and returned configured assets metadata. **Per-file content checks are not yet possible while access stays disabled**; do not claim all asset bytes individually verified.

The same live Preview deployment has **four activation flags exactly `false`** (`SCORE_WORKER_PREVIEW_ENABLED`, `SCORE_DEV_BROKER_ENABLED`, `SCORE_EDGE_GATE_ENABLED`, `SCORE_EDGE_REDEMPTION_ENABLED`), a verified exact `SCORE_WORKER_PREVIEW_ORIGIN`, and two `ratelimit` bindings `SCORE_PREVIEW_REDEEM_LIMIT` (30/60s, namespace `817420621`) and `SCORE_PREVIEW_VALIDATE_LIMIT` (180/60s, namespace `817420622`). Limits are Cloudflare approximate, per location, not global distributed quotas. Worker Production subdomain is **disabled**, Production Worker version/deployment counts are **zero**; existing Pages Production was untouched.

**Independent public HTTP check:** anonymous `GET /en/`, `GET /archive/es/`, `GET /data/score_v2_methodology.json` and `GET /data/research/score_v2_point_in_time_latest.json` all return **HTTP 503** on the isolated Worker Preview while disabled (via an external browser-accessible HTTP source). No premium/private assets were returned. The development Supabase tables `score_handoff_tickets` and `score_member_sessions` still hold **0** rows each. A GitHub Actions branch-scoped synthetic `POST /score-redeem` and repeatable GET denial check were added to `.github/workflows/quality.yml`, without credentials; their exact-head CI result must be checked separately.

**Supersedes stale source-only/asset-pending statements below** (retained as historical progression, not today's deployment state). The user does **not** need to upload files again. No entitlement, ticket, active membership session, Preview broker shared secret, or production route was created. Remaining activation gates: isolated per-Preview shared secret matching the Development Supabase broker via secure provider controls, direct inbound abuse control for Supabase URL, authenticated positive/negative member E2E, expiry/replay/revocation, direct URL bypass, cookies and normal/Incognito cross-origin iframe tests. Do not enable any Preview or Development broker flag until all conditions are independently reviewed.

**RELEASE HOLD:** Keep both PRs draft and unmerged, Preview activation OFF, Development Supabase broker OFF, and Production unchanged.


# Score Research Membership — isolated Workers Preview transition

## 22 October 2026 — verified same-day checkpoint (supersedes earlier package blocker)

**Actual source commit:** `fcd223cfee232aba4398d91b2baedde851cfd792` on the existing draft Score PR #148. The broker client now has an 18-second abort deadline for its Development Edge HTTP request; new credential-isolation regression tests passed.

- [Full Score quality CI #39826795072](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/39826795072): **COMPLETED SUCCESS**, including live anonymous Development broker and Cloudflare Pages disabled-state POST checks.
- [Isolated Worker static preflight #39826795059](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/39826795059): **COMPLETED SUCCESS**.
- [Pinned Wrangler package verification #39826795079](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/39826795079): **COMPLETED SUCCESS** using genuine **Wrangler 4.135.0**, reading **156** static asset files and producing a 12.04 KiB (4.12 KiB gzip) Worker JS bundle via `wrangler deploy --dry-run`. Logs explicitly show `--dry-run: exiting now`, with **no Cloudflare deployment or credentials**. Earlier npm registry failures are resolved **for this GitHub Actions runner**.
- **Boundary:** This Wrangler dry-run validates the *top-level* bundle and assets. It does **not** create a Workers Preview, prove that `previews.ratelimits` bindings exist, set a Preview-only secret, establish a Preview URL, or run authenticated member browser tests.
- Independently verified Pages premium `/en/` and `/archive/es/` still return HTTP **403**; public methodology JSON remains accessible. The Development broker is hosted at version 2 but activation remains `SCORE_PREVIEW_BROKER_ENABLED=false`; Development ticket and session tables contain **zero** rows.
- **No login bypass:** Opera is still disconnected, and the headless Cloudflare login previously failed. The next provider action requires secure Cloudflare management access. Do not put credentials in a PR workflow or chat; the Dev Worker remains source-only. The existing Pages Preview and Production are unchanged.

**Release HOLD:** Both PRs must stay draft/unmerged. The next controlled step is one *disabled* isolated Workers Preview, its genuine provider URL, exact isolation and rate-limit verification, then separate entitlement, replay, revocation and iframe acceptance. No membership activation based on successful package build alone.


**Status: SOURCE-ONLY CANDIDATE, NOT HOSTED. Release HOLD.** This document and code belong exclusively to the draft [Score PR #148](https://github.com/usdimpact/usd-impact-pipeline/pull/148). The existing Cloudflare **Pages** Preview remains disabled and intact. The Supabase Development broker v2 remains deployed **with its activation flag set to false**. No new Cloudflare Worker, Preview, routes, aliases, secrets, or production environment has been deployed or configured.

## Why migrate

Cloudflare Pages Preview environment settings are shared across preview branches. They do not provide the credential isolation required to put a reusable shared broker secret on a branch where unrelated PR code can execute. Cloudflare **Workers Previews** (introduced September 2026) provide separate per-Preview secrets, variables, bindings and URLs. This project must **not** use Workers Version URLs for authentication tests: those use production resources.

Primary sources:
- https://developers.cloudflare.com/workers/previews/
- https://developers.cloudflare.com/workers/previews/configuration/
- https://developers.cloudflare.com/workers/previews/resources/
- https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/
- https://developers.cloudflare.com/workers/static-assets/binding/

## Prepared source

- `workers/score-preview/index.mjs`: isolated Workers Preview-only gateway. Every request first passes exact Preview origin and activation checks, prior to static asset access. Strict Research Membership redemption and per-request revalidation call the existing Development-only Supabase broker client. Session cookies are opaque, Secure, HttpOnly and host-only. No service-role key is imported into this Worker.
- `workers/score-preview/wrangler.jsonc`: dedicated Worker name `usd-impact-score-isolated-dev`, top-level and Preview flags all `false`; `workers_dev:false`, `preview_urls:true`, no production routes, and `assets.run_worker_first:true`. Only Previews have rate-limiting bindings. **Never run `wrangler deploy` as part of this acceptance; use only `wrangler preview` after independent readiness review.**
- `security/score-public-paths.mjs` and `security/score-ticket-form.mjs`: shared, audited allowlist and bounded form parser used by existing Pages and the candidate Worker. Future changes must pass security contract tests.
- `public/.assetsignore`: exclude Pages-specific `_headers`, `_redirects`, and `_worker.js` from Workers static asset uploads. The Worker applies explicit security headers to served assets instead.
- `security/score-preview-worker.test.mjs`: checks default OFF, exact Preview origin, public-vs-premium gate, branch-isolated secret requirement, rate-limit denial, mocked redemption/validation/revocation, asset gate, and key-free dependency graph.
- `.github/workflows/score-worker-preview-dryrun.yml`: credential-free, npm-free **static preflight** only (Node source, Wrangler JSON config, security tests). **Wrangler packaging verification is outstanding.** The earlier `npx wrangler@4.135.0 deploy --dry-run` attempt stalled during npm execution and was cancelled by GitHub after the job timeout, with no bundle result. Do not confuse the static preflight with a compiled or hosted Worker.

## Trust boundaries

1. This is **not** a Cloudflare Pages Preview upgrade in place. It is a separate Worker, whose Production settings are inert; no Production deployment is necessary to create a Worker Preview according to Cloudflare documentation.
2. Only the exact `SCORE_WORKER_PREVIEW_ORIGIN` URL (a `workers.dev` Preview URL) is accepted. Its value must be verified from the actual provider deployment; never invent the hostname.
3. Workers Preview runtime must have a separately generated **per-Preview** `SCORE_EDGE_SHARED_SECRET`, independently paired with Development Supabase Edge. Do not install any privileged `sb_secret_` key in Cloudflare, Pages, Vercel browser assets, GitHub pull-request workflows, logs or chat.
4. Current source flags `SCORE_WORKER_PREVIEW_ENABLED`, `SCORE_DEV_BROKER_ENABLED`, `SCORE_EDGE_GATE_ENABLED`, and `SCORE_EDGE_REDEMPTION_ENABLED` are all `false`. They are independent; activation requires new explicitly reviewed Preview-specific config and a new test plan.
5. Two preview-only Rate Limiting bindings are configured: redemption 30/minute and validation 180/minute per limiter key/Cloudflare location. Missing/failed bindings fail **closed**. Cloudflare calls these limits **approximate, per-location**, not strict distributed quotas. An untrusted request may reach the *direct* Supabase endpoint independently, but it still cannot authorize without a valid shared secret; separate provider abuse controls remain a release gate.
6. Binding namespace IDs are reserved for **this one candidate Preview**. Rate Limiting namespace IDs can share counters across Workers/Previews if reused. A future additional Preview must be reviewed and assigned its own unique namespace IDs.
7. The asset binding uses `run_worker_first:true` for **every** static request; a missing or broken `ASSETS` binding fails closed, rather than serving premium files directly.
8. The current website's handoff destination and iframe behavior were designed around the existing Pages Preview. A Worker Preview URL and updated ticket form destination must be verified **on the website draft only** before live member testing. `SameSite=Lax` cookies may be blocked in cross-site iframes; do not assume they work.

## Next acceptance sequence — no automatic activation

1. Complete source tests and Wrangler dry-run without credentials. Keep source PR **draft**, existing Pages Preview disabled, broker disabled, Production unchanged.
2. Obtain secure Cloudflare Workers management connectivity (never a token in chat). Verify dedicated Worker name, plan, Preview limits, and safe per-Preview secret capacity. Ensure the account permits Workers Previews with Wrangler >=4.135.0.
3. Create only **one** isolated Preview using the checked draft commit and `wrangler preview --name pr-148 --config workers/score-preview/wrangler.jsonc` through a secure, reviewed workflow. Do not run `wrangler deploy`; do not attach a production hostname.
4. Confirm initial Preview requests are disabled. Verify matching *Preview-specific* origin and rate-limit binding identifiers. Configure a distinct per-Preview shared secret directly in the provider and Development Supabase, leaving all activation flags OFF.
5. After independent abuse/isolation review, enable one gated Preview path at a time, only on the isolated branch. Require protected Vercel ticket issuance, positive and negative Research Membership tests, replay and expiry, revocation, direct-bypass denial, normal/Incognito, standalone and iframe tests.
6. Disable all flags as rollback; verify unauthorized POST and premium GET remain denied. Separate Production go/no-go only after acceptance. No implied release authorization from source CI alone.

This document intentionally contains **no credentials** and authorizes **no deployment or Production change**.
