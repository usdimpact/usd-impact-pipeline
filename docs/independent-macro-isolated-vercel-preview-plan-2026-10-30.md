# Independent Macro Context — isolated authenticated mock-preview plan

**Date:** 2026-10-30 · **State:** PLANNING APPROVED ONLY / NO EXECUTION · **Owner decision scope:** planning a separate Vercel-authenticated mock-only Macro Context preview. No project creation, preview deployment, provider data access, or Production release is approved.

**Authority:** [Independent Macro Context Issue #313](https://github.com/usdimpact/usd-impact-pipeline/issues/313). This proposal is **not** an authority source: the [canonical independent rights matrix](../governance/independent-macro-context-fallback-draft-2026-10-30.json), original Score [#155](https://github.com/usdimpact/usd-impact-pipeline/issues/155), and FRED [#282](https://github.com/usdimpact/usd-impact-pipeline/issues/282) remain controlling. The [companion machine-readable planning manifest](../governance/independent-macro-isolated-vercel-preview-plan-2026-10-30.json) keeps **26 operational and release flags false**. Do not interpret owner permission to *plan* as authorization to create, invite, pay, deploy, merge, release, or delete.

## Recommendation: separate tiny source and separate project, no site import

The intended future review uses an **isolated Vercel project** tentatively named `usd-impact-macro-context-mock-review`, not the active `usd-impact-site`, `usdimpact-pt-isolated-review` or `siguiendo-el-dolar` projects. The project name is a proposal only: no project reservation or new resource has been made.

For any *later separately authorized* build, use a **standalone minimal local/static mock** (HTML/CSS and only reviewed local JavaScript where needed), rather than connecting the active USD Impact website Git repository, copying its environment, or importing the five-file website Draft into a deployment. **Do not link the main branch of the website to the new project**, which could trigger a Production build. Do not create a GitHub repo, connect Git, upload content or run a CLI deployment under this planning approval.

Keep the existing website [original one-file Draft PR #998](https://github.com/usdimpact/usd-impact-site/pull/998) and [five-file noindex/sitemap/HTTP 404 Draft PR #1013](https://github.com/usdimpact/usd-impact-site/pull/1013) **both Draft and unmerged**. The #1013 HTTP 404 is a quarantine, not private owner login. **Never relax its deny-all rule** merely to make the proposed preview visible. The mock preview is a different isolated artifact and future project.

## Vercel authentication boundary

Vercel currently reports three team projects; `usd-impact-site` is the public project, remains READY, and uses **Standard Protection / all_except_custom_domains**. **Do not modify its deployment protection or environment variables.** In particular, enabling **All Deployments** protection on that live project could prompt sign-in on its public domains.

For the **future isolated project only**, require **Vercel Authentication — All Deployments** before deploying any HTML, so every generated URL, preview alias and any accidental Production URL is protected. Restrict viewers to specifically approved Vercel accounts; create **no shareable links, automation bypass tokens, deployment protection exceptions, public domain alias, or custom DNS**. This is *authentication for the isolated project*, not a site membership entitlement.

Vercel's [September 9, 2026 announcement](https://vercel.com/changelog/protect-production-deployments-for-free-on-every-plan) says Vercel Authentication can protect All Deployments at no additional **protection** cost on every plan. This does **not** prove that new projects, builds, bandwidth, account seats or other usage have zero cost on this account. **Stop before any billable usage or plan change** until owner explicitly approves the expected spend (target additional market-data-licensing spend remains $0). See [Vercel Authentication](https://vercel.com/docs/deployment-protection/methods-to-protect-deployments/vercel-authentication) and [protection bypass risks](https://vercel.com/docs/deployment-protection/methods-to-bypass-deployment-protection).

## Review content contract

Only invented, educational display concepts. Every frame must visibly say **SYNTHETIC — NOT MARKET DATA — NOT PUBLISHED** and `SYNTHETIC_DO_NOT_PUBLISH`; any example reference dates must be **2099 or later**. Four categorical mock dials may be shown, but no actual numerical dollar index, EIA WCESTUS1, Treasury 2Y/10Y, DXY, WTI, Score or historical observations. The preview must not claim equivalence to the original eight-driver Weekly Score, confirmed source rights, owner methodology approval, a trading signal, or available live data.

**Forbidden imports:** private evidence, source-vintage archives, site Git history/assets containing provider data, Supabase configuration, Lemon Squeezy/entitlements, analytics, production service environment variables, user or reviewer personal data, secret keys, server functions that request providers, third-party fonts/scripts/images and provider URLs used for fetching observations. App network requests must be absent; Vercel's own login redirect is an expected authentication-system request and is not a provider-data fetch.

Prefer pure static content with a `robots.txt` disallow-all rule, HTML `noindex,nofollow`, no canonical, no sitemap and `Cache-Control: private, no-store`. **These headers do not replace Vercel Authentication.**

## Sequenced stop/go gates

| Gate | Required decision/evidence | Current state |
| --- | --- | --- |
| P0: Plan and separation | Scope reviewed; public site and existing PRs untouched; 26 authorization flags false | **PLAN ONLY** |
| P1: Create separate isolated project | Explicit **new owner approval**, team/project/cost and Git-auto-deploy boundaries checked; confirm no existing domain or shared secrets | **NOT APPROVED** |
| P2: Enable authentication | Configure **All Deployments** only on isolated project, verify named reviewer access and no bypass exceptions **before any artifact upload** | **NOT CONFIGURED** |
| P3: Build invented-only mock | Separate approved source, mock marker, pinned file inventory, offline static checks, zero app external network, exact-head QA | **NOT APPROVED** |
| P4: Preview deployment | Explicit separate owner approval for Preview only, verify project ID, no Production target/alias/branch; stop if setup tool would deploy Production | **NOT APPROVED** |
| P5: Auth and security QA | Anonymous and unapproved authenticated visitor denied; named reviewer can view; test alternate hostnames, redirects, asset paths, cache and SEO. Record safe proof without auth cookies or private data | **NOT RUN** |
| P6: Review closure | Owner reviews synthetic display. Reviewer access revocation/preview cleanup requires separate permission; no real data or public product release | **NOT RUN** |

**Fail closed immediately** on any anonymous HTML access, public/shareable exception, real provider observation, shared production environment, unapproved usage charge, unexpected Production build, new custom domain, inherited repository webhook or release gate change. Do not silently fix issues by weakening security or moving the preview to the live site.

## Acceptance tests for a separately authorized future preview

1. Verify exact isolated Vercel project name/ID and deployment target **before** any action. No code or env import from the public site; no auto-deploy from its Git `main`.
2. Review-only mock artifact contains **no actual source data** or outbound application requests; marker and invented 2099+ dates verified offline.
3. In an anonymous/incognito browser, deployment URL and direct static-asset URLs show Vercel sign-in, **not the HTML or assets**. Test the unique preview hostname, branch hostname and any generated alternate URL.
4. A Vercel account without granted access cannot see the page; a deliberately granted reviewer **can**, after login. Do not transmit personal tokens, cookies or invite links to public GitHub.
5. Ensure no shareable/automation bypass or deployment protection exception, no public DNS, no sitemap, no canonical, no indexable links, and no external request waterfall except Vercel authentication.
6. Confirm current `usd-impact-site` public domain, existing member auth, Daily publishing, Score rights gates, FRED storage and panel HOLDs are **unchanged** after any separately authorized preview.
7. Record minimal non-sensitive test results in #313. Treat a failed test as a **STOP**, not as release approval.

## Manual steps — only if another approval is given

**None are mandatory under the current planning authorization.** A later owner review can happen from [Issue #313](https://github.com/usdimpact/usd-impact-pipeline/issues/313) and this runbook. For any later **separately approved** setup:

- In [Vercel Dashboard](https://vercel.com/dashboard), verify the selected team and existing public project are **not** the destination. Prepare a separate project without importing the existing website repo, environment, Production branch or domain. If the project wizard requires immediately deploying or linking a Production branch, **stop** and return for a revised approval.
- Within **that new isolated project only**, open **Security → Deployment Protection** and enable **Vercel Authentication → All Deployments**, then confirm the setting was saved and review the user-access list. [Official instructions](https://vercel.com/docs/deployment-protection/methods-to-protect-deployments/vercel-authentication).
- Return to [Issue #313](https://github.com/usdimpact/usd-impact-pipeline/issues/313) with **non-sensitive** evidence that protection and budget boundaries are acceptable. Obtain separate explicit permission before mock upload/deployment or adding reviewer access. Never paste Vercel API tokens, bypass links, user emails or authentication cookies into GitHub.

## Status to carry forward

**Approved:** writing this isolated project plan and an offline review of applicable Vercel protection terms.

**Not approved:** creating or reusing a Vercel project, connecting Git, moving site code, installing integrations, changing SSO, granting access, deploying mock HTML, retrieving market data, buying provider services, enabling the Macro Context Panel or the original Weekly Score, modifying the live site, merging drafts, changing DNS, publishing, deleting artifacts, or reusing Production secrets.

**Next optimal task:** owner reviews this planning packet; if a visual mock is genuinely needed, separately authorize P1 **project creation only** after project/cost/auto-deploy safeguards are verified. No emergency or manual step is otherwise required.
