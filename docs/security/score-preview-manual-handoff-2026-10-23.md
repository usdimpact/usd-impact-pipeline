## Cloudflare API execution evidence — 22 October 2026

- The dedicated **parent Worker** `usd-impact-score-isolated-dev` and one isolated **Preview** `pr-148` were created via the authorized Cloudflare API; the actual URL is **https://pr-148-usd-impact-score-isolated-dev.michael-w-d0b.workers.dev**.
- The reviewed **six JavaScript Worker modules** from Score draft commit `8e65a944a1afca03254f669de11687a6086cc163` have been deployed **only to the Preview**. The latest Cloudflare Preview deployment is `6c88746c-c376-437f-935b-883716d64dbd`.
- Two Preview-only, approximate rate-limit bindings are installed: `SCORE_PREVIEW_REDEEM_LIMIT` (namespace `817420621`, 30/60s per location) and `SCORE_PREVIEW_VALIDATE_LIMIT` (namespace `817420622`, 180/60s per location). The exact Preview origin binding is also installed. Four activation flags all remain **false**.
- **Production:** parent Worker subdomain disabled; no Production Worker code/deployment, custom domain, route or trigger. Existing Pages project unchanged.
- **Live denied-state:** Preview `GET /en/`, `GET /archive/es/`, and `GET /data/score_v2_methodology.json` each returned HTTP **503** while disabled. This is expected; public files are also disabled until explicitly allowed later.
- **Only remaining deployment artifact:** static files. The repository branch includes `public/` and `workers/score-preview/wrangler.jsonc`; no external attachment is required. The official Cloudflare API manifest upload session issued a token, but **the asset upload returned HTTP 401** through the OAuth API connector, including a trial with the temporary upload token. **No assets were uploaded or attached** and the `ASSETS` binding is absent. Do **not** copy temporary upload tokens to chat/PRs or change the Production Worker to work around it.
- **Browser-only fallback:** Open [Score PR #148 branch](https://github.com/usdimpact/usd-impact-pipeline/tree/fix/score-membership-handoff-147) → **Code → Codespaces → Create codespace on this branch**. In the cloud terminal, authenticate using `npx --yes wrangler@4.135.0 login`, verify the account with `npx --yes wrangler@4.135.0 whoami`, then run `npx --yes wrangler@4.135.0 preview --name pr-148 --config workers/score-preview/wrangler.jsonc --json`. This updates **only** the existing Preview, uploading the `public/` assets and runtime bindings; do **not** run `wrangler deploy`, merge PRs, enable any flag or add a Production route.
- The actual verified hostname is now included **only** in `previews.vars.SCORE_WORKER_PREVIEW_ORIGIN` in Wrangler config; source tests check this. This is public infrastructure metadata, not a secret.
- Next: after an authenticated Preview upload, inspect the actual `ASSETS` binding and (run_worker_first) setting, confirm live all-off HTTP 503, audit no Production deploy, then separately plan real Research Membership activation acceptance.

**Release HOLD:** source and safe Preview infrastructure are ready; the Worker is NOT ready to serve assets or real members.


# 23 October 2026 — USD Impact Score Workers Preview manual handoff

## 22 October 2026 — verified same-day checkpoint (supersedes earlier package blocker)

**Actual source commit:** `fcd223cfee232aba4398d91b2baedde851cfd792` on the existing draft Score PR #148. The broker client now has an 18-second abort deadline for its Development Edge HTTP request; new credential-isolation regression tests passed.

- [Full Score quality CI #39826795072](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/39826795072): **COMPLETED SUCCESS**, including live anonymous Development broker and Cloudflare Pages disabled-state POST checks.
- [Isolated Worker static preflight #39826795059](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/39826795059): **COMPLETED SUCCESS**.
- [Pinned Wrangler package verification #39826795079](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/39826795079): **COMPLETED SUCCESS** using genuine **Wrangler 4.135.0**, reading **156** static asset files and producing a 12.04 KiB (4.12 KiB gzip) Worker JS bundle via `wrangler deploy --dry-run`. Logs explicitly show `--dry-run: exiting now`, with **no Cloudflare deployment or credentials**. Earlier npm registry failures are resolved **for this GitHub Actions runner**.
- **Boundary:** This Wrangler dry-run validates the *top-level* bundle and assets. It does **not** create a Workers Preview, prove that `previews.ratelimits` bindings exist, set a Preview-only secret, establish a Preview URL, or run authenticated member browser tests.
- Independently verified Pages premium `/en/` and `/archive/es/` still return HTTP **403**; public methodology JSON remains accessible. The Development broker is hosted at version 2 but activation remains `SCORE_PREVIEW_BROKER_ENABLED=false`; Development ticket and session tables contain **zero** rows.
- **No login bypass:** Opera is still disconnected, and the headless Cloudflare login previously failed. The next provider action requires secure Cloudflare management access. Do not put credentials in a PR workflow or chat; the Dev Worker remains source-only. The existing Pages Preview and Production are unchanged.

**Release HOLD:** Both PRs must stay draft/unmerged. The next controlled step is one *disabled* isolated Workers Preview, its genuine provider URL, exact isolation and rate-limit verification, then separate entitlement, replay, revocation and iframe acceptance. No membership activation based on successful package build alone.


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
