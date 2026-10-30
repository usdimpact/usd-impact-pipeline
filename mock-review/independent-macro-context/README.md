# Independent Macro Context — P3 static mock source (DRAFT / NOT DEPLOYED)

**Date:** October 30, 2026. **Purpose:** visually review a **self-contained, fictional** layout for an independent educational macro context concept. This directory is a portable static *source folder*, not a live application or an approved market-data product.

**Source-review location:** pipeline repository Draft PR only. **Future isolated deployment destination, if separately approved:** Vercel project `usd-impact-macro-context-mock-review` (ID `prj_oQ3dGEvHmWRBMYAnQaRYIsY6URu1`). The existing public website project `usd-impact-site` is **not** a destination. The isolated project was created under P1 with `ssoProtection.deploymentType = all`, no Git connection and **zero** deployments as of preparation.

## Inventory

| File | Purpose |
| --- | --- |
| `index.html` | Single-page, script-free, responsive educational layout with **invented** 2099-06-05 and 2099-06-12 Friday dates, four fictional categorical dial labels and visible `SYNTHETIC_DO_NOT_PUBLISH` / no-market-data warnings |
| `robots.txt` | Deny robots across every path |
| `vercel.json` | Static noindex/no-store and strict Content Security Policy headers **for a separately authorized future Preview only** |
| `README.md` | Scope, evidence, security gates and no-deploy rule |

**No runtime packages. No JavaScript. No remote fonts, images, scripts, fetch/XHR, analytics, cookies, market-data feeds, source-provider URLs, auth bypass tokens or service environment variables.** This directory does not use any files from existing site Production, original Score archives or FRED source transports. There is no `package.json`, Git integration, deployment script, Vercel project association file or generated output.

## Fixed fictional labels, never real source readings

- `dollar_breadth = UP` (invented; no broad USD series retrieved)
- `crude_inventory = DRAW` (invented; no oil/inventory observation retrieved)
- `treasury_curve_level = POSITIVE` (invented; no yields retrieved)
- `treasury_curve_direction = FLATTENING` (invented; no curve history retrieved)

All four are vocabulary-compatible with the [existing synthetic-only result schema](../../schemas/independent_macro_context_synthetic_preview.schema.json). These are intentionally **static HTML labels**, not an evaluator result object, source evidence, trading recommendation or economic claim. The dates are only 2099+ invented mock period metadata and convey no real-world prediction.

## Non-Production security model

1. **Primary control for any later preview:** Vercel Authentication **All Deployments on the separate isolated project only**. It is already configured in project settings but **not tested end-to-end**, since no mock has been deployed.
2. **Secondary, not access control:** HTML robots meta, `robots.txt`, no canonical/sitemap, and `vercel.json` noindex/no-store/CSP headers. These do **not** secure the HTML without Vercel Authentication.
3. **No bypass:** do not create shareable links, automation-bypass tokens, public project exceptions, custom domains, DNS aliases, or reviewer invitations without separately authorized review.
4. **No Production changes:** Do not merge website [Draft #998](https://github.com/usdimpact/usd-impact-site/pull/998) or [Draft #1013](https://github.com/usdimpact/usd-impact-site/pull/1013). Preserve #1013's 404 quarantine of its unrelated concept path. Do not import the existing website Git repository or environment into the isolated project.
5. **No real data:** all 56 proposed exact-source rights and all 14 release-authority gates remain false. No real H.10, EIA, Treasury, S&P, FRED, WTI, DXY or historical source data may be added.

## Offline review and non-deploy acceptance

The repository's **standard-library-only** `tests/test_independent_macro_static_mock_review.py` checks the exact file inventory, safe HTML elements/attributes, invented dates and Friday adjacency, closed dial name/value pairing, visible warnings, absence of external network dependencies, robots/canonical exclusions, strict security headers, no authorization drift, and the separate preview project identity.

The page can be rendered by an offline browser opening the single HTML file (no installs, data, or internet required), but **a local preview is not a Vercel access-control test**. A GitHub review of the markup and tests is sufficient for P3.

## Stop/go boundary for P4 — not authorized by this package

**Do not** run a Vercel CLI deployment, link a repository, upload static files, grant a reviewer account, remove deployment protection, connect a domain, or introduce any credentials as part of this P3 Draft PR.

A *separate explicit P4 Preview-only approval* would require:
- confirm target project ID exactly `prj_oQ3dGEvHmWRBMYAnQaRYIsY6URu1`, existing protection `all`, absence of Git/production links and the current zero-deployment state;
- confirm this exact reviewed source revision, static offline tests green, no external app request, and no unapproved build/usage charge;
- use a supported non-Production Preview-target deployment path and stop if the tool would create a Production deployment or bypass authentication;
- verify anonymously that **the HTML and each direct static asset are inaccessible** before granting named reviewer access; then check unauthorized/authorized Vercel accounts under separate reviewer approval; record safe evidence without exposing login cookies or bypass links;
- re-check existing `usd-impact-site` remains public and READY and that independent panel, original Score, historical retention and publication gates remain HOLD.

**Current stage:** P3 **code review only**. P4 and P5 are **NOT STARTED**. The existence of this folder, CI success, and Vercel Authentication settings must never be construed as an authorization to publish, deploy or use real data.

Controlling records: [Issue #313](https://github.com/usdimpact/usd-impact-pipeline/issues/313), [P1 project setup receipt](https://github.com/usdimpact/usd-impact-pipeline/issues/313#issuecomment-6527572526), [Draft planning PR #331](https://github.com/usdimpact/usd-impact-pipeline/pull/331), [Score rights Issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155) and [FRED retention Issue #282](https://github.com/usdimpact/usd-impact-pipeline/issues/282).
