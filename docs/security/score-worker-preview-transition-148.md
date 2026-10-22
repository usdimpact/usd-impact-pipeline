# Score Research Membership — isolated Workers Preview transition

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
