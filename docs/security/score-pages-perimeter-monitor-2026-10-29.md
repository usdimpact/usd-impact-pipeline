# Pages security posture monitor — post-membership-migration contract (2026-10-29)

**Status:** Review-only branch. Issue [#155](https://github.com/usdimpact/usd-impact-pipeline/issues/155) remains **HOLD** for provider-data publication; this change is not part of a public Score artifact or Production rollout.

## Root cause

The previous scheduled `.github/workflows/pages-security-posture.yml` continued to expect Pages `/en/` to return HTTP 200 and the old dashboard/security-header policy. The [merged pipeline Score membership architecture #148](https://github.com/usdimpact/usd-impact-pipeline/pull/148) intentionally moved premium HTML authorization off Cloudflare Pages and onto the [merged website implementation #836](https://github.com/usdimpact/usd-impact-site/pull/836) at the Vercel/Supabase `/score/member/*` routes.

The Pages middleware now always returns **HTTP 403** to `/en/`, with a no-store "Research Membership required" response and restrictive CSP. The retired `/score-redeem` endpoint returns **HTTP 410**. Only explicitly allowlisted public paths may serve on Pages.

- Scheduled [2026-10-27 run #40513815094](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40513815094): **success**, before the switch.
- Scheduled [2026-10-28 run #40706972876](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40706972876): **failure**; log's last response HTTP 403 and strict CSP.
- Scheduled [2026-10-29 run #40893905425](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40893905425): **failure**; same HTTP 403 and strict CSP after 30 attempts.

These observations strongly support a **stale monitor expectation**, not an access-bypass finding. If unrelated outages occur, they remain separately actionable.

## Scope of draft fix

- Keep the existing monitor's **daily schedule**, `main` push trigger, `workflow_dispatch`, and read-only GitHub permissions.
- Replace its obsolete 30-attempt HTTP 200/embedded-dashboard assertion with `scripts/check_score_pages_security_posture.py`.
- Check exactly **two** known Pages root origins: `usd-impact-pipeline.pages.dev` and `score.usd-impact.com`.
- Check **three** operational paths on each root:
  1. `GET /en/` -> **403**, no-store, nosniff, noindex, restrictive CSP and membership referral.
  2. `GET /score-redeem` -> **410**, same security header contract, tombstone.
  3. `HEAD /data/score_v2_methodology.json` -> **200**; **never read its body**.
- Request no strict reproduction bundle, weekly bridge, component history, private asset, protected account page, FRED, Treasury, Yahoo or other market-data feed.
- Fail if the perimeter widens to allow premium HTML, the retired endpoint reactivates, or a previously public methodology metadata path is unexpectedly denied.
- Use Python stdlib only; no API token, credential, entitlement, Cloudflare configuration write or external provider license.
- Run offline synthetic Python unit tests under the existing `Weekly score quality` workflow on PR review. Actual live perimeter checks run only on `main` after separately approved merge, scheduled invocation, or manual dispatch.

## Distinct security layers

- **Cloudflare Access preview gate**: independent external policy on `*.usd-impact-pipeline.pages.dev`. Verify anonymous preview denial separately. This monitor intentionally does **not** fetch previews or simulate identity.
- **Pages public-only middleware**: denies premium HTML on both root origins, irrespective of Cloudflare Access cookies.
- **Vercel/Supabase Research Membership**: website `/score/member/*` checks site account session and research entitlement. The older Pages 403 text cannot prove a particular user's entitlement state.
- **Provider redistribution rights**: Class C/E/F public machine-readable artifacts remain anonymously accessible on root origins while Issue #155 HOLD prevents new publication. This monitor's passing result does **not** clear their licensing/retention status.

## Acceptance and rollback

1. Verify exact draft PR head: CI Python quality and security checks complete successfully. The Python security test must not create external writes.
2. Before merge, recheck `functions/_middleware.js` and `security/score-public-paths.mjs` have the expected public-only architecture.
3. After a separate owner-reviewed merge, run the existing security-posture workflow once manually; verify six root URL outcomes and log only expected statuses, not any data file body.
4. If it fails, inspect current HTTP statuses and headers **before** changing any access rule. Do not "fix" a 403 by opening premium HTML.
5. Rollback is to revert the monitor script/workflow commit or disable its scheduled job if an approved incident action requires it. Preserve the secure Pages middleware, Cloudflare Access preview policy and rights HOLD.

**Non-goals:** no public data migration; no history purge; no Cloudflare Access or Production changes; no member entitlement mutation; no new Score release; no license approval.
