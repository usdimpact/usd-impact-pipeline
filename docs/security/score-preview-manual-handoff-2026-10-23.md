# 23 October 2026 — USD Impact Score Workers Preview manual handoff

**Operator goal:** Create or inspect exactly one isolated, **disabled** Cloudflare Workers Preview of Score PR #148 and record its actual hostname. **Do not enable membership or touch Production.**

**Preparation completed by ChatGPT on 22 October 2026:** The existing [Score PR #148](https://github.com/usdimpact/usd-impact-pipeline/pull/148) contains the source-only Worker candidate, short-lived ticket broker client, per-source hashed rate-limit keys, static asset default-deny security, and contract tests. Companion [Website PR #836](https://github.com/usdimpact/usd-impact-site/pull/836) remains draft, unmerged and unconnected to any new Worker URL. Supabase Development project \`ycstrcvshdluovtuasjc\` hosts broker version 2 with \`SCORE_PREVIEW_BROKER_ENABLED=false\`. Existing Pages Preview remains denied for premium HTML. No Production changes.

## Stop conditions before any provider action

- First check the latest source commit and [full Score quality workflow](https://github.com/usdimpact/usd-impact-pipeline/actions). Do not proceed if security tests are failing.
- Check the [bounded Wrangler packaging workflow](https://github.com/usdimpact/usd-impact-pipeline/actions/workflows/score-worker-preview-package-check.yml): a **PASS** means an actual Wrangler bundle was generated; a registry connectivity failure/timeout is **not** a PASS. [Static preflight](https://github.com/usdimpact/usd-impact-pipeline/actions/workflows/score-worker-preview-dryrun.yml) is a separate, lesser check.
- Verify the Cloudflare account/project is for \`usd-impact-pipeline\` and the dedicated worker is \`usd-impact-score-isolated-dev\`. **No Production deployment or existing Pages domain changes.**
- If the Cloudflare dashboard is unavailable, do not bypass verification or enter credentials into ChatGPT, GitHub PR comments, browser scripts or logs. Keep this work on HOLD.

## One manual dependency

Open the [Cloudflare dashboard](https://dash.cloudflare.com/) in your normal signed-in browser. The earlier headless TinyFish login was rejected, and Opera Browser Connector was not connected. You may enable **Allow AI connection** in Opera and sign in normally, or use Cloudflare's own UI/authorized cloud shell. No local installation is required if an authorized cloud development terminal is available. Do not share account passwords or API tokens in chat.

## Approved, minimal-change sequence for the session

1. Verify that [Worker Previews](https://developers.cloudflare.com/workers/previews/get-started/) is enabled/available in the correct Cloudflare account. Do **not** create a Worker production route, custom domain, Queue consumer, or Cron Trigger.
2. If *and only if* package verification is PASS, use a trusted authenticated cloud shell from the reviewed PR branch with installed **Wrangler 4.135.0 or later** and the checked \`workers/score-preview/wrangler.jsonc\`, then create the one isolated Preview using **\`wrangler preview --name pr-148 --config workers/score-preview/wrangler.jsonc\`**. The \`previews.vars\` switches are all \`false\`; use **preview**, never \`wrangler deploy\`. Cloudflare docs state no Production Worker deployment is required for the first Preview.
3. Record the **actual**, Cloudflare-returned Preview hostname; do not infer or fabricate a URL. Confirm it is a \`workers.dev\` Preview hostname. Inspect the asset binding \`ASSETS\` with \`run_worker_first:true\` and the **two separate Preview rate-limit bindings** \`SCORE_PREVIEW_REDEEM_LIMIT\` / \`SCORE_PREVIEW_VALIDATE_LIMIT\`. Their approximate limits are per location, not strict worldwide quotas.
4. With **all activation switches OFF**, test unauthenticated \`GET /en/\`, \`GET /archive/es/\`, \`GET /data/score_v2_methodology.json\` and synthetic \`POST /score-redeem\` on the **real Preview hostname**. An all-off Worker is expected to return 503 to **every** request, including public files, before any entitlement access is granted. Do not issue real tickets or create sessions.
5. Separately review [Preview-specific secret isolation](https://developers.cloudflare.com/workers/previews/configuration/). The Worker is not allowed to receive a full \`sb_secret_\` Supabase key. If preparing the shared broker authentication secret, provision an independent high-entropy value **only** to this Preview and the isolated Development Supabase broker through provider-managed secret interfaces; do not activate any flags, print it or put it in any Pages Preview environment. This must occur after confirming Preview bindings really are isolated.
6. Review inbound abuse controls **at Cloudflare and the direct Supabase Edge URL**. The Worker rate limiter does not prevent unauthenticated internet traffic from reaching the direct Supabase endpoint. Keep \`SCORE_PREVIEW_BROKER_ENABLED=false\` until the threat review is signed off.
7. Only after separate explicit Development acceptance planning: connect Website PR #836 to the **verified** Worker Preview URL and use the already authorized test membership account. Verify allowed/denied membership, one-time redemption, replay, expiry, revocation, direct URL bypass, iframe/cross-site-cookie behavior and normal/Incognito flows. Leave both PRs draft; never merge based solely on mocked or disabled-state CI.

## Rollback and evidence

- **Immediate fail-closed rollback:** leave or restore \`SCORE_WORKER_PREVIEW_ENABLED=false\`, \`SCORE_DEV_BROKER_ENABLED=false\`, \`SCORE_EDGE_GATE_ENABLED=false\`, \`SCORE_EDGE_REDEMPTION_ENABLED=false\` in Preview and \`SCORE_PREVIEW_BROKER_ENABLED=false\` in Supabase Development. Delete the isolated Preview through Cloudflare's supported UI if necessary; do not alter Production routing.
- Record a short evidence receipt in PR #148: timestamp, exact commit, genuine Preview URL, secure account/workspace name (never secret values), function state, denial status codes, bindings verified, and remaining failures. Mirror release decision (HOLD) to website PR #836.
- **Production release is out of scope.** No privileges, payments, customer entitlements, existing Pages domain, or Production project may be modified under this handoff.

**Primary documentation:** [Worker Previews](https://developers.cloudflare.com/workers/previews/), [configuration/secrets](https://developers.cloudflare.com/workers/previews/configuration/), [resource isolation](https://developers.cloudflare.com/workers/previews/resources/), [Rate Limiting](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/).
