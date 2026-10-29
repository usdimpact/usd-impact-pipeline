# Issue #282 — FRED DGS2/DGS10 retention and publication inventory (2026-10-29)

**Status:** preliminary read-only source audit / review-only. **No permission, no Production change and no authority to delete history.**

## Evidence and scope

- FRED support reply dated 2026-10-29 to the USD Impact DGS2/DGS10 commercial/derived-use inquiry: permitted commercial use for appropriately labelled Public Domain datasets, with citation and disposal; states FRED terms do not permit retention/storage.
- [FRED legal terms, general prohibitions (p) and (q)](https://fred.stlouisfed.org/legal/terms/) distinguish **(p) storing/caching/archiving or incorporating FRED Content in a database** from **(q) derivative works or modification of FRED Services**; the separate FRED API prohibitions **(k) AI/model development and (l) storage/caching/archiving** also apply where relevant. The public-domain series label is not a blanket waiver of service terms. This is a terms quotation/classification, not counsel's conclusion about a specific derivative.
- Existing [source-retention-policy.md](source-retention-policy.md) is last reviewed 2026-08-24. It prohibits raw response retention but describes provider-derived weekly evidence and public component artifacts. The Oct 29 support reply requires a more granular lineage and retention review.
- Existing [Score provider rights matrix](score-v2-provider-rights-evidence-matrix-2026-10-28.md), [containment plan](score-v2-public-rights-containment-plan-2026-10-27.md), [zero-budget fallback](score-zero-budget-fallback-2026-10-28.md), and [issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155) remain controlling research/hold references.

## Confirmed paths from read-only inspection of default branch

| Phase | Path / function | Evidence | Disposition |
|---|---|---|---|
| Source configuration | `usd_impact_score_v2.py`, `TICKERS` | UST_2Y=DGS2 and UST_10Y=DGS10, FRED transport | Confirmed FRED dependency; do not substitute silently |
| Fetch | `usd_impact_score_v2.py:fetch_fred()` | `https://fred.stlouisfed.org/graph/fredgraph.csv?id=...`, parsed into a daily pandas DataFrame | Confirmed source; check transient and persistent lifecycle |
| Merge | `usd_impact_score_v2.py`, `fetch_all_inputs()` | FRED and Yahoo frames joined into one daily matrix | Derived/in-memory mixing; characterize subsequent writes |
| Local exports | `usd_impact_score_v2.py:export_csv()`, `export_json()`, `_daily_cache.parquet` and output directories | Code contains disk-writing paths | Potential exposure; actual execution/retention not verified |
| Committed weekly input | `data/weekly_input_2026-10-23.json` | DGS2/DGS10 source and observation metadata under weekly driver entries | Confirmed committed persistence; weekly schema contains per-driver derived z-scores/contributions; source-specific rights unresolved |
| Public latest input | `public/data/weekly_input_latest.json` | Public driver entries with FRED source metadata | Confirmed public path; file contains UST_2Y/UST_10Y per-driver z-scores and contributions as well as source metadata; terms treatment unresolved |
| Historical public input | `public/archive/2026-10-23/weekly_input.json` and other dated archives | DGS2/DGS10 are present in dated public archive files | Confirmed archived persistence; enumerate full set |
| Public component histories | `public/data/usd_impact_score_v2.csv`, `public/data/usd_impact_score_v2.json`, `public/data/score_repro_bundle_latest.json` | Existing containment plan describes multiweek component values and weekly provider-derived values | Repo-document evidence; inspect exact current file schemas and deployment before remediation |
| Independent validation | `scripts/validate_weekly_release.py`, `public/data/score_v2_methodology.json` | DGS2/DGS10 embedded in source/provenance and release contracts | Metadata alone is not evidence of stored observations |

## Runtime production / persistence trace (source-level verified)

| Stage | Writer / carrier | Confirmed behavior | Rights-audit significance |
|---|---|---|---|
| Friday preflight | `.github/workflows/weekly.yml` | Scheduled Friday 22:00 UTC and manual dispatch both call `scripts.score_publication_rights_gate` **before** provider fetch | `governance/score-publication-rights-gate.json` is `hold` dated 2026-10-28. The `run-pipeline` job is gated on `rights_hold != 'true'`. No scheduled new-week publication generation is currently authorized |
| Read/merge | `usd_impact_score_v2.py:fetch_fred`, `fetch_all_inputs` | Downloads FRED CSV, aligns FRED 2Y/10Y with Yahoo drivers, normalizes and computes Score | Unapproved direct reruns can still process mixed data; entrypoints must be inventoried individually |
| CI runner-local | `usd_impact_score_v2.py` + `.github/workflows/weekly.yml` | Writes full weekly level matrix as CSV and daily fingerprint receipt in `$RUNNER_TEMP` for same-run strict reproduction | Ephemeral by design; exact runner retention, logs, workflow artifacts and failure-path cleanup need verification |
| Local `--test` mode | `usd_impact_score_v2.py:main` | Non-web mode may write the combined daily matrix to `_daily_cache.parquet`; `--web` does **not** write that parquet cache. `.gitignore` ignores cache/log paths | Distinguish local/development retention from current CI. Git ignore is not a storage permission or deletion mechanism |
| Logs | `setup_logging`, `compute_zscores` | Writes local `logs/usd_impact_score_v2.log` in web mode, streams to stdout; debug logging emits per-driver mean and standard deviation | GitHub Actions logs may contain derived normalization statistics even if Git never commits the local log. Determine retention/access and whether old logs exist |
| Public output generation | `export_csv`, `export_json` | Writes full Score history (617 weekly observations in 2026-10-23 committed JSON) including UST_2Y/UST_10Y component z-scores | Machine-readable derivative history under rights review |
| Commentary/bridge | `scripts/generate_weekly_commentary.py` | Writes `data/weekly_input_YYYY-MM-DD.json` and `public/data/weekly_input_latest.json`, including driver z-scores/contributions | Both Git-persistent and public latest outputs. Non-public directory naming alone does not prevent exposure in a public repository |
| Strict reproduction | `scripts/build_runtime_score_repro_bundle.py`, `scripts/build_score_repro_bundle.py` | Serializes per-driver weekly level, normalization mean/std, contribution and provider fingerprints to `public/data/score_repro_bundle_latest.json` | Highest concern because the public artifact includes levels and normalization moments, not just aggregate Score |
| Archive | `.github/workflows/weekly.yml` | Copies latest Score, bridge and reproduction bundle to `public/archive/<week>/...` | Dated persistence and Git history; future file deletion alone does not erase past Git objects or edge caches |
| Git publication candidate | `.github/workflows/weekly.yml` | Stages `git add public commentary data`, pushes branch and opens PR; human review/merge is separate | Committed derived output can enter public repository and later Pages deployment. No such new publication should proceed while HOLD |
| Cloudflare Pages delivery | `functions/_middleware.js`, `security/score-public-paths.mjs` | Dashboard HTML is restricted; precise data JSON/CSV paths and dated score/weekly_input/repro_bundle archives are explicitly public | Membership protection does **not** protect these allowlisted data paths. `governance/score-public-rights-surface.json` identifies Class C |
| Other paths | `.github/workflows/research-validation.yml`, `score-v3-shadow.yml`, `score-v2-predictive.yml` | Explicit rights-gate checks stop scheduled derived-data research ingestion/publication while HOLD | No evidence from source review of unauthorized new scheduled ingestion on these workflows |
| Ungated reproduction | `.github/workflows/repro-rehearsal.yml` on `main` at time of audit | Manual/selected PR rehearsal had no rights check despite a live `usd_impact_score_v2.py` call | Follow-up [draft PR #285](https://github.com/usdimpact/usd-impact-pipeline/pull/285) adds fail-closed gate. Its PR Actions rehearsal confirmed fetch step **skipped**, but it is not merged to `main` |
| Read-only attestation | `.github/workflows/repro-attestation.yml` | Reads already committed bundles; does not itself fetch live market data | Distinguish read-only verifier from reproduction rehearsal |

## Deployed endpoint verification (2026-10-29; read-only)

An independent browser fetch returned machine-readable content on each of these current URLs; no values were reproduced in this record:

- `https://score.usd-impact.com/data/weekly_input_latest.json` — current bridge values and source metadata were served.
- `https://score.usd-impact.com/data/score_repro_bundle_latest.json` — strict reproduction bundle with component evidence was served.
- `https://score.usd-impact.com/archive/2026-10-23/repro_bundle.json` — dated bundle served.
- `https://usd-impact-pipeline.pages.dev/data/weekly_input_latest.json` — legacy Pages endpoint served bridge data.
- `https://score.usd-impact.com/en/` — returned HTTP 403 (dashboard HTML protected).

These tests prove the stated endpoints were reachable/denied during inspection; they do not enumerate all cache nodes, older branches, domain variants or historic revisions. Do not equate HTTP 403 on HTML with protection for data endpoints. The public GitHub repository provides a separate distribution channel irrespective of Pages routing.

## Source-specific legal guardrails (not a legal conclusion)

- The current [FRED Terms of Use](https://fred.stlouisfed.org/legal/terms/) prohibit storing/caching/archiving in the general FRED Services prohibitions **(p)** and API prohibitions **(l)**; general prohibitions **(q)** separately address modifying/copying/creating derivative works of FRED Services. The API's **(k)** expressly addresses AI/model development or training. Do not treat different clauses as interchangeable, nor use provider-derived observations for AI training without explicit authorization.
- FRED staff's 2026-10-29 email permits the described commercial use of properly tagged Public Domain datasets **subject to the full terms, source citations and disposal**. It is not permission for all series or all public derivatives.
- [Federal Reserve Board DDP transition notice](https://www.federalreserve.gov/data/data-download-fred-information.htm) confirms removal of custom **Build Your Package** the week of Nov 9, 2026, with preformatted packages to be retired subsequently; historical release XML remains a possible direct-source candidate. Ownership, exact automated-access license, retention, parity and continuity are **not approved**.

## Historical execution evidence and preview exposures (2026-10-29, read-only)

The following are sampled, **not a complete historical enumeration**:

| Source / run | Observation | Limit |
|---|---|---|
| [Friday release run #40044029286](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40044029286) (2026-10-24 UTC) | Pipeline succeeded; job logs confirm a FRED DGS2/DGS10 retrieval and a Yahoo retrieval, temporary same-run 617-week matrix, fingerprint receipt and calculation normalization output | Runner-local artifact TTL and downstream cached copies not proved by log access |
| [Friday release run #38984976938](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/38984976938) (2026-10-17 UTC) | Equivalent pre-HOLD provider fetch, temporary weekly input matrix and normalization/log statements | Does not establish all older versions or all historical CI runs |
| [Rights-gated PR rehearsal run #40905286366](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40905286366) (2026-10-29 UTC) | Rights gate succeeded; provider fetch, Python setup, dependency installation and rehearsal output steps were **skipped** | Validates draft PR #285 behavior at its branch only, not main |
| GitHub Actions artifact listing for the above three runs | Returned zero GitHub-uploaded artifacts in each sampled run | Not evidence of cache absence, logfile deletion, runner deletion, Git history removal or third-party replicas |

The October 17 and October 24 logs were retrievable on October 29 and contain numeric-derived calculation statements. No such values were copied into this audit document. The CI pipeline uses `actions/setup-python` pip dependency cache; **package cache** should not be conflated with provider-data retention without inspecting its actual contents and any custom cache paths. The connector did not expose the GitHub Actions cache-list API, so cache contents and retention are currently **unverified**.

The linked Cloudflare account's Pages project `usd-impact-pipeline` has Production branch `main` and the domains `score.usd-impact.com` and `usd-impact-pipeline.pages.dev`; the provider returned a project-level lifetime listing of **1,803** Pages deployments. **That is a count of deployment records, not a count of proven accessible or data-exposing deployments.**

Independent URL reads confirmed two development **preview** deployments also serve pre-existing provider-derived JSON without authentication:

- `https://ca9ec248.usd-impact-pipeline.pages.dev/data/score_repro_bundle_latest.json` (audit-docs PR #284 preview) — reproduction bundle served.
- `https://c7a03949.usd-impact-pipeline.pages.dev/data/weekly_input_latest.json` (rehearsal-safeguard PR #285 preview) — bridge JSON served.
- `https://ca9ec248.usd-impact-pipeline.pages.dev/en/` — HTTP 403, dashboard HTML protected.

Preview deployment copies therefore remain a separate public dissemination surface even when a PR edits documentation or CI only. The Cloudflare account exposed Pages project/deployment metadata but **no zone records** for this domain; actual CDN cache rules, per-object cache lifetimes, and purge coverage were not accessible. A separate container-based HTTP header check failed at DNS resolution and cannot be treated as evidence about live Cache-Control headers.

**Containment requirement:** before any cleanup, verify both deployment classes, explicit public-path allowlist, preview-build strategy, Git source history, retained logs/artifacts, private stores, edge caches and backups. Do not delete historical evidence, alter Pages deployment/protection, or purge CDN without documented rights, preservation and deployment approvals. For draft-only documentation commits, use the existing `[CF-Pages-Skip]` convention to reduce additional preview builds, but do not assume a skipped build revokes previous preview URLs.

## Cloudflare Pages Access containment decision — evidence verified 2026-10-29

**Read-only account inspection** of `usd-impact-pipeline` confirmed:

- Pages project: `usd-impact-pipeline`, Github source, Production branch `main`, `build_config.destination_dir = public`.
- `source.config.preview_deployment_setting = "all"`, `preview_branch_includes = ["*"]`, `preview_branch_excludes = []`, `path_includes = ["*"]`, `path_excludes = []`. Any non-main audit/research commit can therefore generate a preview exposing the committed `public/` tree, even if the commit itself edits no data files.
- Cloudflare account `GET /accounts/{account_id}/access/apps` and reusable-policies GET both returned HTTP 403 `access.api.error.not_enabled`: **Cloudflare Access is not enabled**. This independently explains the lack of Access authentication on the sampled preview URLs.
- Latest successful Production deployment is a separate canonical Pages record; the latest preview does **not** mean Production has changed. The GitHub `main` rights gate remains HOLD.

Cloudflare's [official Pages preview documentation](https://developers.cloudflare.com/pages/configuration/preview-deployments/) states previews are public by default and describes **Workers & Pages > select project > Settings > General > Enable access policy** to protect *preview deployment subdomains*, including random per-commit preview URLs. The doc expressly distinguishes these from the project's own `*.pages.dev` root and custom domain: **preview Access is not a fix for the existing Production/legacy root public data endpoints**.

**Recommended staged remediation subject to owner approval and a cost/identity check:**

1. Verify Cloudflare Access/Zero Trust plan and authentication configuration before activation; do not assume it is free, and do not enable account services from a documentation review.
2. Prefer a project preview Access rule allowing only an explicitly named QA/editorial team, with a reversible change record and pre/post HTTP checks for anonymous preview data and dashboard routes. Check current reviewers' sign-in ability before enforcing. If activated, test *old* and new preview hashes independently rather than assuming historical versions are covered.
3. Separately plan a future reduction of preview build triggers (e.g. audit/research branch exclusions or `[CF-Pages-Skip]`), after accounting for existing QA flows. **Disabling future previews cannot revoke existing preview URLs.**
4. Treat the main `score.usd-impact.com` and legacy `usd-impact-pipeline.pages.dev` machine-readable allowlist as a **different remediation gate**. Review the existing private-reproduction and public-safe aggregate prototypes and preservation/rights decisions before any new public schema.
5. Inventory GitHub history, workflow logs, runner caches, third-party mirrors and Cloudflare retention under a single evidence-preservation plan. No purge, deletion or changed access-control setting is authorized in this PR.

This is a **security decision packet**, not Cloudflare Access activation or permission to modify Production.

## Verified Cloudflare preview Access activation — 2026-10-29

**Owner action:** The project owner enabled the dashboard control **Settings > General > Preview access > Restrict previews**. The subsequent dashboard screenshot displays: "Preview deployments are restricted by a Cloudflare Access policy." This is a recorded owner action, not an API mutation by the audit.

**Independent read-only configuration verification:**

- Cloudflare Access app name: `usd-impact-pipeline - Cloudflare Pages`; self-hosted domain pattern `*.usd-impact-pipeline.pages.dev`; **24-hour** session duration.
- Policy: `Allow Members - Cloudflare Pages`, decision `allow`; **one specific-email include rule**, zero excludes, zero additional requirements. Identity/address intentionally not copied into the repository. No "Everyone" rule was observed in the inspected application policy.
- Pages project still has Production branch `main` and its two root domains. No Score/source/deployment settings or public endpoint routes were changed by this audit.

**Independent anonymous URL verification, immediately after activation:**

| Previously tested surface | Post-activation result |
|---|---|
| `https://ca9ec248.usd-impact-pipeline.pages.dev/data/score_repro_bundle_latest.json` | `login_required`, no provider data returned |
| `https://c7a03949.usd-impact-pipeline.pages.dev/data/weekly_input_latest.json` | `login_required`, no provider data returned |
| `https://score.usd-impact.com/data/weekly_input_latest.json` | JSON still anonymously readable |
| `https://usd-impact-pipeline.pages.dev/data/weekly_input_latest.json` | JSON still anonymously readable |

The two old preview URL tests demonstrate protection beyond only future previews, **for these sampled URLs**. They do not prove every historical URL, third-party mirror, cache, local runner artifact or Git history has been remediated. `*.usd-impact-pipeline.pages.dev` Access policy scope explicitly excludes the root `usd-impact-pipeline.pages.dev` host and `score.usd-impact.com`.

**Operational follow-up:** Confirm the owner's intended account can complete login (without sharing passcodes), verify any additional QA reviewers are separately allowed, and establish an Access policy change/rollback procedure. A sign-in requirement can block legitimate previews until reviewer permissions are correct. Keep the root-domain/Production data rights decision separate, coordinated with Issue #155 and approved private-evidence/public-safe schema work.

**Status:** preview protection **verified on sampled old URLs**; Production/root public data exposure **unresolved**. No additional Cloudflare settings were changed, no data deleted, and no rights/publication decision inferred.

## Follow-up independent TinyFish anonymous-origin recheck (2026-10-29)

The owner explicitly requested TinyFish to continue the audit. A fresh TinyFish fetch with no authentication and no market data excerpts in the audit output independently rechecked the security boundary.

| Anonymous URL (hostname and path only) | Result | Classification |
|---|---|---|
| `ca9ec248.usd-impact-pipeline.pages.dev/en/` | `login_required` | Protected preview HTML |
| `ca9ec248.usd-impact-pipeline.pages.dev/data/score_repro_bundle_latest.json` | `login_required` | Protected preview strict evidence |
| `c7a03949.usd-impact-pipeline.pages.dev/data/weekly_input_latest.json` | `login_required` | Protected preview weekly bridge |
| `score.usd-impact.com/data/weekly_input_latest.json` | anonymous JSON served | Unresolved custom-domain Class C |
| `score.usd-impact.com/data/score_repro_bundle_latest.json` | anonymous JSON served | Unresolved custom-domain Class C |
| `usd-impact-pipeline.pages.dev/data/weekly_input_latest.json` | anonymous JSON served | Unresolved root-domain Class C |
| `usd-impact-pipeline.pages.dev/archive/2026-10-23/repro_bundle.json` | anonymous JSON served | Unresolved root-domain dated Class C |

No provider numeric values are copied to the issue, PR, or this document. This is a **sample of specific known URLs**, not a full historical URL or cache inventory. It confirms preview protection persisted after the owner's activation and is not just a screenshot-based assertion. Historical Cloudflare deployment records, public Git history, root-domain endpoints, CI logs and cached clones remain distinct exposures.

**Authenticated user journey not yet tested in TinyFish:** no TinyFish browser context profile reported an existing signed-in Cloudflare/Access session. Do not guess a reviewer identity, attempt to bypass login or request a one-time code in chat. If the owner authorizes a TinyFish authenticated browser QA session, use a newly verified, user-signed-in profile; otherwise ask owner to test login in an incognito browser using the policy-allowed email.

**Decision gates remain unchanged:** source-level rights approval, approved private evidence retention boundary, aggregate-safe publication schema, full historical treatment/backup plan and separate Production authorization. Do not put Cloudflare Access in front of the customer Production domain in lieu of a rights decision, do not purge without preservation, and do not claim private preview URLs have cleared the ongoing redistribution risk on public root domains.

## Two-layer Score access control and current merged implementation — 2026-10-29

**Security assessment correction:** A previous TinyFish browser test accessed a preview reproduction JSON URL but saw "Research Membership required" at the same preview's `/en/` HTML route. **This does not establish a missing Research Membership entitlement.** The current `functions/_middleware.js` on Pages deliberately denies **every premium HTML path** with HTTP 403 and that message, for all cookies and all sessions. Its `security/score-pages-public-only.test.mjs` explicitly verifies the invariant even when legacy enable flags, cookies and secrets are present. Cloudflare Access and the USD Impact membership authorization are independent gates.

**Current code and external status:**

1. [Pipeline membership design PR #148](https://github.com/usdimpact/usd-impact-pipeline/pull/148) is **merged**, although older documentation still describes its initial draft status. The Pages perimeter remains public-only for specifically allowlisted paths, with no member authorization logic.
2. [USD Impact website PR #836](https://github.com/usdimpact/usd-impact-site/pull/836) is **merged**. The current website `apps/web/src/pages/score.astro` sends members to its same-origin `/score/member/en/` and `/score/member/archive/en/` routes, not to Pages HTML.
3. Website `apps/web/vercel.json` routes those member paths to `/api/account?action=score-member-content&path=:path*`. Website `apps/web/src/lib/score-member-handler.js` verifies the current Supabase site session and `research-membership` entitlement before reading the private Score HTML asset. The handler returns 401 for anonymous, 403 for non-entitled, 404 for missing/invalid asset and 200 for verified active member; member responses are `private, no-store`.
4. Website unit tests in `apps/web/src/lib/score-member-handler.test.js` check 401, 403, 200, HEAD, 404 and 405. These are code test expectations, **not proof of the current user's entitlement**. The older Development acceptance report documents a positive QA member test as of 2026-10-27, which does not substitute for a fresh user-specific end-to-end test.
5. Fresh TinyFish anonymous checks on 2026-10-29 confirmed `https://www.usd-impact.com/score/` loads publicly, while `https://www.usd-impact.com/score/member/en/` and `https://www.usd-impact.com/score/member/archive/en/` both returned HTTP **401**. This is the intended negative production-side authorization result.
6. TinyFish's saved `cloudflare-usd-impact` browser profile visited historical preview `/en/` and the preview reproduction JSON. It saw the expected Pages 403 membership text on `/en/` and the allowlisted JSON loaded **in that browser context**. Separate **unauthenticated** TinyFish fetches of the identical preview JSON returned `login_required`. Together these results are consistent with Cloudflare Access working for the saved browser context, but do **not** reveal its specific Access identity, prove membership status, or establish authorization to republish provider-derived data.
7. The TinyFish profile metadata did not list a recorded Cloudflare sign-in at inspection, so its session identity should be treated as **not independently attested**. If explicit identity evidence is needed, use Cloudflare Access's own safe audit method with owner-approved scope, not a cookie/OTP dump.

**Pass/fail acceptance matrix:**

| Layer / test | Current evidence | Result |
|---|---|---|
| Anonymous visitor to preview allowlisted JSON | TinyFish `login_required` | PASS — denied |
| Saved TinyFish context to preview allowlisted JSON | JSON page reachable in browser; identity endpoint reports NONE | OBSERVED — browser access, named Access identity NOT VERIFIED |
| Any visitor to preview premium `/en/` | Pages code and browser return 403 | PASS — HTML deliberately not served on Pages |
| Anonymous visitor to website `/score/member/en/` | TinyFish HTTP 401 | PASS — denied |
| Anonymous visitor to website archive member route | TinyFish HTTP 401 | PASS — denied |
| Website active member to private dashboard | Prior 2026-10-27 QA report, site code/tests | CURRENT POSITIVE E2E NOT REPEATED |
| Anonymous visitor to custom/root Class C JSON | TinyFish returns detailed JSON | OPEN — redistribution/retention rights HOLD |

**No attempted remediation by making Pages serve premium HTML.** This is a deliberately different trust boundary; modifying the Pages middleware to "fix" a 403 would be a security regression. No change to account, entitlement, Cloudflare Access policy, site router, Score source, publication rights gate or Production was made.

Existing integrated rights-safe public/private containment source ([merged #164](https://github.com/usdimpact/usd-impact-pipeline/pull/164)) already exists as **non-activated prototype**. Do not duplicate or activate it while Issue #155 holds. Future root-domain Class C containment must follow the approved private evidence migration, provider/counsel disposition, public consumer migration and separate Production authorization.

## TinyFish same-session Access discrepancy and stale Pages health monitor — 2026-10-29

### Preview authentication — distinguish access from user identity

Cloudflare's documented `/cdn-cgi/access/get-identity` endpoint was queried **read-only** with the user's saved TinyFish `cloudflare-usd-impact` browser context. It returned `auth_status: NONE`; profile metadata also did not list a recorded signed-in Cloudflare site. **Do not claim that the named Cloudflare Access identity is authenticated based only on that saved profile.**

A subsequent [same-session TinyFish check](https://agent.tinyfish.ai/runs/41c7def8-04b8-4fc3-9594-3174d7dff9d6) observed that the **harmless methodology metadata JSON** rendered in the saved browser, while the identity endpoint still reported NONE. This is a **discrepancy**, not a verified login or an established Access bypass.

A separate [fresh browser with no saved profile](https://agent.tinyfish.ai/runs/9168f5b5-9094-4ad5-a1e1-dfad6dd2e80f) attempted the **same methodology URL** and received the Cloudflare Access login challenge before any JSON was served. Prior unauthenticated TinyFish fetches of preview weekly/reproduction URLs also reported `login_required`. Thus a straightforward anonymous bypass is **not demonstrated** on the tested paths. The observed difference between saved-profile and clean-context access warrants a future owner-authorized session audit; do not use or reveal tokens, cookies, OTPs or personal identity fields.

The separate Vercel/Supabase website member route continued to return 401 for anonymous calls. It must not be conflated with Pages' always-403 premium HTML denial.

### Daily Cloudflare Pages security workflow — outdated expected status

A distinct **operations/alerting mismatch** was discovered in the active `.github/workflows/pages-security-posture.yml`. It still expects `GET /en/` to return **200** with the old embedded-dashboard/CSP contract. The newer public-only Pages middleware intentionally serves **403** and a strict no-store denial response.

Actual [2026-10-28 run #40706972876](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40706972876) and [2026-10-29 run #40893905425](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40893905425) failed after repeated attempts and logged status **403** with restrictive CSP. The preceding [2026-10-27 run #40513815094](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40513815094) passed under the previous contract.

[Draft PR #288](https://github.com/usdimpact/usd-impact-pipeline/pull/288) proposes a read-only correction. It checks both Pages root origins with **403 premium HTML denial**, **410 retired redemption**, and **200 HEAD-only public methodology metadata**. It includes offline tests. It does **not** modify Cloudflare Access, the website, Production, membership, public Score artifacts or Issue #155 HOLD. Until independently reviewed/merged, the old daily monitor remains on `main`, and the known false-positive status remains outstanding.

## Scope not yet verified

- Complete historic GitHub Actions run logs, artifacts, cache inventories, runner-local retention and cleanup proofs; Cloudflare cache coverage/TTL and alternate domain variants; Vercel/Supabase downstream copies; object storage/backups; old Git history/reflogs and third-party mirrors. The workflow commands and selected live Pages endpoints were verified above.
- Whether hashes, normalization moments, mixed-source aggregates, and independently computed non-reversible aggregate history qualify as FRED Content or prohibited derived works. **Do not assume either permission or prohibition; obtain written interpretation.**
- Whether the same H.15 observations can be sourced directly from the Federal Reserve Board, whether its license/terms permit the required retention/commercial use, and whether source and calendar parity can be demonstrated without changing Score methodology.
- Current workflow configuration is scheduled and rights-gated, but actual upcoming trigger outcomes and all external runners cannot be guaranteed merely from source inspection. The non-publishing live reproduction rehearsal gap is now closed on protected `main` by [merged PR #285](https://github.com/usdimpact/usd-impact-pipeline/pull/285). Its live steps require `hold == 'false'`. Additional rights-gated workflow hardening was merged via [PR #291](https://github.com/usdimpact/usd-impact-pipeline/pull/291). This does not prove every manual/external entry point is gated.


## Direct Federal Reserve Board H.15 candidate (public-source desk review)

- Official [H.15 Download Program](https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H15) offers a preformatted **Treasury Constant Maturities** CSV package and a complete release XML package.
- The [official package series listing](https://www.federalreserve.gov/datadownload/Review.aspx?filetype=csv&from=&label=include&lastObs=&layout=seriescolumn&rel=H15&series=bf17364827e38702b42a58cf8eaa3f78&to=&type=package) lists two-year `H15/H15/RIFLGFCY02_N.B` and ten-year `H15/H15/RIFLGFCY10_N.B` daily market yield observations. **Candidate mapping only**; no real-data parity assessment has been run.
- Federal Reserve Board's July 16, 2026 notice states that the DDP **Build Your Package** option will be removed during the week of **November 9, 2026** ahead of eventual DDP retirement. Do not design a new integration to depend on that UI path. Investigate release XML and enduring machine-readable Board alternatives, including deprecation support and allowed access/retention, before implementation.
- The Board is the **H.15 release publisher**, but the [H.15 release footnote 9](https://www.federalreserve.gov/releases/h15/) explicitly credits the **U.S. Treasury as the source** of nominal Treasury constant-maturity yields. Distinguish data-originator, H.15 republisher, and FRED transport; do not claim that the Board is the original Treasury-rate data owner.
- The [Board website disclaimer](https://www.federalreserve.gov/disclaimer.htm) provides a public-domain default for information on its own site and requests Board attribution, **unless otherwise indicated**, with explicit carveouts for material associated with non-Board rights. This is useful evidence but does not waive Treasury-origin questions or independently establish retention/commercial reuse permission for each Board H.15 downloadable format.
- The [U.S. Treasury official XML-feed documentation](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed) describes its continuing `/resource-center/data-chart-center/interest-rates/pages/xml` endpoint, with `data=daily_treasury_yield_curve` and year/month/all-pagination parameters. The [official interest-rate CSV archive](https://home.treasury.gov/interest-rates-data-csv-archive/) provides historical CSV files. This is a **third, more direct Treasury-origin candidate** for the same 2Y/10Y constant-maturity measures, with full-period historical availability advertised from 1990.
- The [Treasury XML developer change notice](https://home.treasury.gov/developer-notice-xml-changes) notes that this is an API feed rather than a browser-rendered page and details feed pagination and URL changes made in 2022. Treat endpoint version/change monitoring, schema and year coverage as specific acceptance tests.
- **No live Treasury/Board/FRED provider-data retrieval or parity computation has been performed in this audit.** Before proposing any replacement, verify exact data-series equivalence (value, as-of calendar, observation/availability date, vintages/revisions, gaps, units), copyright/service terms including commercial archival and redistribution rights, attribution, rate limits and continuity. Keep unknowns as HOLD.
- Future synthetic tests should validate daily date alignment, missing days, holiday handling, release timestamps, unit conventions, revision/vintage expectations, and strict fail-closed response parsing. **No live retrieval or activation in this PR.**

## Post-merge safeguard and licensing reconciliation (2026-10-29)

**Review-only dated audit addendum.** This section updates the historical "draft" descriptions above without deleting the original investigation sequence. Rights and private-evidence decisions still require their own approvals.

| Change / evidence | Verified result | Important limit |
|---|---|---|
| [PR #288](https://github.com/usdimpact/usd-impact-pipeline/pull/288) | Merged at `662e8dfd80d1aae3be6365562f145a6adaef939d`; [Pages monitor push run 40921274786](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40921274786) passed | Checks operational 403 premium denial, 410 retired redemption, 200 HEAD methodology on two Pages root domains; does not remove provider-derived JSON |
| [PR #285](https://github.com/usdimpact/usd-impact-pipeline/pull/285) | Merged at `9cef78c307057ca6872a5705f1ca8f646a88dd96`; only explicit `hold == 'false'` permits live reproduction | Rehearsal under current HOLD records no-op; no provider download or temporary reproduction evidence |
| [PR #291](https://github.com/usdimpact/usd-impact-pipeline/pull/291) | Merged at `ca0879ad994ed93c3d0d5b9ff34aafd4d4c38801` after fresh protected-base validation | Tightens seven additional existing workflows; do not generalize to unrelated manual/third-party entrypoints |
| [Post-merge Weekly Score quality](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40925618640) | Completed success on PR #291 merge commit | Unit and synthetic QA, not a rights decision |
| [Post-merge Python security](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40925618499) | Completed success on PR #291 merge commit | CodeQL/dependency workflows, not a market-data license |
| [Post-merge research validation](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40925618462) | Completed success; rights HOLD step ran and provider-research generation, validation, publication PR steps skipped | No live data processed |
| Cloudflare Pages project readback | Canonical successful Production deployment remained `c5e8e9a9-3a7e-418e-99bd-109128cf973d`, source SHA `7770bd0cc64438b4cb03353ec8f486d84de62948`; new skip-tagged deployment records idle | GitHub `main` changed for CI safeguards but no verified new Pages Production release |
| [Draft PR #287](https://github.com/usdimpact/usd-impact-pipeline/pull/287) | Synthetic-only direct Treasury XML candidate parser and tests remain draft | No real-source comparison, download, license conclusion, or Score source switch |
| [Draft PR #284](https://github.com/usdimpact/usd-impact-pipeline/pull/284) | This audit remains an unmerged reference document | No production, data-deletion, publication or provider-side mutation |

**Read-only source-rights correspondence reconciliation:** A 2026-10-29 FRED staff reply permits the specifically described commercial use of series tagged public domain **subject to FRED legal terms, citation to FRED and the originating source, and disposal after use**, while confirming **no storage or retention permission**. This is not a blanket authorization to retain, archive, publish detailed derived histories or use copyrighted series. The existing 2026-10-28 S&P DJI (case 01036004) and Cboe replies route toward sales/permissions rather than grant usage rights; a fresh relevant-mail search located no later signed clearance for S&P, Cboe, CME, Yahoo or ICE. Do not reproduce private staff correspondence verbatim or identifying personal details in repository records.

**Official public-source verification:** [FRED current terms](https://fred.stlouisfed.org/legal/terms/) distinguish General Services prohibition (p) for storage/caching/archive from (q) for derivative works, and API restriction (l) separately addresses storage. [U.S. Treasury XML documentation](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed) describes an official yield-curve feed with 1990+ coverage, but no authorized real-data/rights/parity review has been completed. Do not substitute Treasury feeds silently for the current frozen Score methodology.

**Residual HOLD boundaries:** Public Class C/E/F component-derived release files remain anonymously accessible on the root Pages and custom Production domains; historical Git objects and prior releases, Action logs, CDN caches, downstream backups and public copies require separate preservation/retention planning. The main Score rights gate still has `state=hold`, `decision_receipt=null`, `approved_by=null`. Legal/provider decisions, a public-safe output schema, private evidence rights/storage, archive/consumer compatibility and **separate** Production authorization remain required. Neither a successful CI check nor an owner's approval of workflow hardening is approval to commercialize, migrate or delete these artifacts.

## Development private-evidence current-state cross-check (2026-10-29, read-only)

The old 2026-10-28 [Development private-evidence execution packet](docs/score-private-evidence-development-execution-packet-2026-10-28.md) is **historically stale** where it says not yet provisioned. A new [draft documentation correction PR #293](https://github.com/usdimpact/usd-impact-pipeline/pull/293) preserves the original packet while adding a dated superseding checkpoint. This work **did not provision or modify Supabase**.

**Provider readback, strictly Development:** Project `xakayexlzyrazuunqlxe` is ACTIVE_HEALTHY. It has one `score-private-evidence` Storage bucket (`public=false`, 1 MiB limit, JSON-only), one existing synthetic `2099-01-02` object at `rehearsal/score-v2/archive/2099-01-02/repro_bundle.json` (1,748 bytes by metadata), zero public-schema tables, and no Supabase security-advisor notices. The function `score-private-evidence-broker` is ACTIVE version 1. Its three deployed module source strings **exactly match** the GitHub-reviewed files; the `verify_jwt=false` provider setting is deliberately paired with the broker's own GitHub OIDC signature/claim verification.

**Historical GitHub Actions receipts:**

- [2026-10-28 synthetic write #40617195348](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40617195348): **success**, OIDC audience bound to fixed week + fixture hash; created object and cleaned runner temporaries.
- [2026-10-28 repeat write #40617289043](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40617289043): **expected HTTP 409** from create-only archive; no overwrite; cleanup ran.
- [2026-10-28 synthetic read #40617383435](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40617383435): **success**, week-bound OIDC, read and synthetic/hash checks.
- [2026-10-28 private research adapter + locked reader #40620133144](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40620133144): **success**, aggregate-safe synthetic reader compatibility and temporary cleanup.

**Governance:** `governance/score-private-research-migration-contract.json` records `development_synthetic_rehearsal_authorized=true`, but `real_provider_evidence_authorized=false`, `public_replacement_authorized=false` and `production_change_authorized=false`. Do not write current/real FRED or Yahoo evidence into the synthetic private store or rely on a synthetic pass as a source-rights decision. Preserve its one fixed fixture as audit evidence; **do not rerun the create-only write**. The outstanding work is source/retention approval, read-path migration of real evidence after approval, historical public-archive treatment, and a separate Production decision.

## Risk gates and next executable checks

1. **No additional live FRED fetch for this audit.** Use repository metadata and synthetic fixtures; never include actual provider-derived numeric values in issues, logs or PR descriptions.
2. Inventory all FRED-sourced disk writes, producer/consumer graphs, and persistence durations, including CI outputs and historical releases, with links and evidence classifications.
3. Record six distinct rights per source/transport: commercial access, internal use, transient processing, storage/retention, derived output, public dissemination. Unknown = HOLD. Include separately prohibited AI/model development use.
4. Research direct H.15 source at the Board under its actual terms and supply a synthetic-only adapter acceptance plan with observation calendar and parity tests; do not replace FRED or alter Score v2.
5. Seek written provider/counsel interpretation for aggregate-only derived Score/history, intermediate matrices, hashes and retention of old releases, without asserting that no-cost access implies rights.
6. Before any public artifact cleanup, obtain approved reversible migration, external cache/backup plan, privacy/legal review, reproducibility preservation and explicit release authorization.

## Acceptance checklist

- [x] Confirmed source code linkage to FRED DGS2 and DGS10.
- [x] Confirmed committed weekly and public archive data-file pathways.
- [x] Established material difference between public-domain series status and FRED delivery/retention terms.
- [x] Mapped current source-level Friday, archive, Git publication, Pages allowlist and rehearsal flow; confirmed public endpoint reachability.
- [x] Sampled pre-HOLD live jobs and retrievable job logs; checked artifact listings and sampled Pages preview endpoints.
- [ ] Completed all historical job-log/backup/CDN/cache, historical preview and downstream persistence inventory.
- [x] Independently verified existing Development synthetic private bucket, broker source parity, immutable write, read and locked-reader acceptance; no new provisioning required.
- [ ] Approved use/retention of **real** provider-derived evidence in the private system and completed real-reader production migration.
- [ ] Confirmed retained value classes and rights interpretation.
- [x] Identified Treasury-origin XML candidate and public Board disclaimer with original Treasury provenance.
- [ ] Confirmed direct Board/Treasury rights and exact-source parity feasibility.
- [x] Merged PR #285 after protected branch update and exact-head checks; confirmed reproduction rehearsal live provider steps are skipped under rights HOLD.
- [x] Merged PR #288; verified first post-merge daily Cloudflare Pages security monitor passed against current 403/410/200 public-only contract.
- [x] Merged PR #291 after protected branch update and exact-head checks; all eight inventoried rights-gated Score workflows require explicit `hold == 'false'` to process.
- [x] Post-merge PR #291 CI: Weekly Score quality, Python security and research validation all succeeded; research provider generation, validation and publication were skipped under HOLD.
- [ ] Completed executable/manual/external entry-point inventory beyond these eight workflows and demonstrated no unauthorized provider retrieval paths.
- [ ] Obtained explicit legal/provider and release approvals.

This is a **review artifact only**. Issue #155 HOLD remains active. No existing data, workflows, public artifacts, method, credentials, entitlements, or production config are changed by this document.
