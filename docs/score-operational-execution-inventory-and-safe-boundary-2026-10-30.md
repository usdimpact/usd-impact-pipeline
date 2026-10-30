# Score operational execution inventory and mandatory boundary design
**Reviewed:** October 30, 2026. **Status:** read-only operations assessment + offline CI regression, not authorization for provider access or Production.

## Executive decision
The canonical Score v1 publication gate remains `hold`. The eight known Score-operational GitHub Actions paths enforce that decision, and the supported manual launcher from [PR #324](https://github.com/usdimpact/usd-impact-pipeline/pull/324) refuses to spawn either frozen Score CLI while HOLD. This is **not** universal enforcement: the pre-holdout research lock pins the original `usd_impact_score_v2.py` and `scripts/build_score_repro_bundle.py` byte-for-byte, and arbitrary local Python processes can still invoke them directly. **No evidence that those direct invocations actually occurred after HOLD was found.** Absence of evidence in GitHub Actions/Cloudflare cannot prove no external jobs exist.

## Verified running / non-running evidence

| Surface | Latest independently verified evidence | Meaning / limitation |
| --- | --- | --- |
| GitHub protected main | `6d2bc9ca10095eef0e6d1b82ab9af31e58cb5258` at initial PR #324 assessment; **newer PR #325 at `2fd43f76ce04fced3753ddc18622c1169bc4db18`** (addendum below) | Quality/security green, **not** a data license |
| Original weekly Score GitHub Action | Scheduled run [#40044029286](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40044029286) on **October 24**, workflow completed successfully | This historical run was not interpreted as proof of authorized fresh market-data calculation; now source rights remain HOLD |
| Research and health schedules | Oct 24 research-validation and health succeeded; Oct 26 research-evidence health succeeded | Scheduled checks can run and record HOLD without ingesting new observations |
| Cloudflare Pages | Production branch `main`, public/ directory, `score.usd-impact.com` and `usd-impact-pipeline.pages.dev`; later research merge entries `idle`, no new successful Score build from PR #324 | No new publication as a result of the latest guards; prior public artifacts still need rights review |
| Cloudflare security monitor | Scheduled [Oct 28 failure](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40706972876) and [Oct 29 failure](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40893905425) previously expected a 200 response but received 403 and restrictive CSP | The checked-in monitor is now a **different** fixed-target policy that expects 403 for premium HTML and 410 for retired redemption. A fresh successful run of that current contract has not been verified; don't relax Pages security to force a 200 |
| Unrelated open PR | [#133](https://github.com/usdimpact/usd-impact-pipeline/pull/133) is a separate draft Weekly Score health classification | No implied merge/release |
| External local automation | GitHub/Cloudflare metadata cannot see local Task Scheduler, cron, third-party workers, notebooks or cloned repos | **Manual operator inventory required** if any such automation exists |

The scheduled-run status is a *snapshot* and not a guarantee of future GitHub Actions execution, operational availability or absence of unauthorized runs. Only metadata and explicitly public operational monitor logs were examined. No FRED, Yahoo, Treasury, H.15, EIA, paid provider or Score numerical observation endpoints were contacted.


## Post-merge addendum: connected Render and Pages execution evidence (2026-10-30)

**Purpose and scope:** Follow-up, read-only *metadata and deployed-code* attestation after PR #325. The initial inventory above is a historical snapshot. This addendum does not infer anything about another account/workspace, and it grants **no** access, execution, data-usage, retention, migration, or publication rights.

| Checked surface | Confirmed observation | Still unknown / not implied |
| --- | --- | --- |
| Protected pipeline main | PR #325 merged at `2fd43f76ce04fced3753ddc18622c1169bc4db18` | Green release checks do not grant provider usage rights |
| Connected Render workspace service inventory | Three **web services** and **no Render-managed cron-job service** returned; all three show auto-deploy off | No proof about in-process timers, external HTTP triggers, other workspaces/accounts, local schedulers or independent agents |
| Isolated Daily private runtime | Actual active Render deployment dates to Oct 7. The *deployed* server imports `createScheduledPreparation` and calls `.start()`; the deployed driver runs only when `USD_DAILY_PREPARATION_ENABLED === 'true'`, otherwise explicitly reports `DISABLED`. Its source is the isolated Daily shadow/runtime system, **not** the frozen Score engine | Current runtime flag, existing preparation activity, private mount contents and any external callers were **not verified**; a default-disabled implementation is not evidence of a disabled deployed flag |
| Isolated malware scanner | Actual active Render deployment dates to Oct 2. Its deployed startup script uses an internal six-hour ClamAV `freshclam` signature-maintenance loop | This internal maintenance schedule is **not** a Score invocation; no general statement about all runtime execution is justified |
| Isolated source-capture diagnostic | Actual active Render deployment dates to Sep 27. Its deployed configured entrypoint serves a static diagnostic response / health endpoint; a recent non-secret health log reported `HOLD`, zero model calls and `publicAllowed:false` | Only the deployed configured entrypoint and reported diagnostic state were inspected, not arbitrary external agents or a full process tree |
| Cloudflare Pages production-deployment records | PR #324 and #325 each have `idle`/skipped deployment records, not a newly successful Score production build | Pre-existing public Score artifacts and distribution-rights questions persist under Issue #155 |
| Scheduled Pages security monitor | Latest observed scheduled results on Oct 28 and 29 were **failures** under prior monitor behavior; checked-in main now specifies 403 for protected premium HTML, 410 for retired redemption, HEAD 200 for methodology metadata | A new successful execution of the **current** monitor contract has **not** been verified; do not alter protected-page access to force the old 200 response |

Source of private deployment attestation: connected Render service/deployment metadata, then GitHub file reads at each **actual deployed commit** (not merely branch HEAD). No secrets, source observations, provider responses, raw market values, private runtime logs or private repository commit hashes are reproduced here. The GitHub scheduled-run evidence is visible in [Oct 28](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40706972876) and [Oct 29](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40893905425), with the updated contract in [the checked-in workflow](../.github/workflows/pages-security-posture.yml) and [monitor code](../scripts/check_score_pages_security_posture.py).

### Smallest remaining operator-only checks

1. **Read only:** In the connected Render workspace, inspect the private Daily runtime's `USD_DAILY_PREPARATION_ENABLED` flag and last start/preparation event. Record only `enabled`, `disabled`, or `unverified`; never share values of credentials or unrelated environment variables. **Do not disable** the separate Daily publication workflow as a blanket Score containment measure.
2. Identify any Windows Task Scheduler, Linux cron, Vercel cron, Render service in another workspace, external automation/agent or cloned-repository job that calls the *original frozen Score* scripts directly. Record owner, environment, guarded launcher vs direct entrypoint and last-run metadata. Unknown means `UNVERIFIED`; an empty Render cron list is **not** a global negative attestation.
3. Review the **next** live execution of [Pages security posture](https://github.com/usdimpact/usd-impact-pipeline/actions/workflows/pages-security-posture.yml) against its current code. A run on an older SHA does not verify the updated monitor. Do not weaken the premium HTTP 403 boundary.
4. Before any mandatory broker or scheduler rewiring, perform a separately approved no-egress preview and confirm the daily runtime and scanner do not lose their independent functionality. Keep the original Score, independent Macro Context Panel, provider rights, archival changes and public release **HOLD**.

**Non-actions:** No Render/Cloudflare/GitHub Actions configuration changed; no dispatch, source fetch, source retention, repository-private evidence publication, public-path redaction, frozen-engine edit, paid resource, new build or Production activation performed. This documentation update must itself use the `[CF-Pages-Skip]` merge convention and exact-head protected checks.

## CI-only new regression control — no operational workflow edited

New [offline workflow execution registry test](../tests/test_score_operational_entrypoint_workflow_registry.py):

1. Dynamically enumerates all `.github/workflows/*.yml` files. The baseline contains **27 workflows**; an unrelated new CI workflow does not require changing a hard-coded count.
2. Recognizes direct original-Score Python CLI invocations, `python -m usd_impact_score_v2`, direct reproduction-builder Python modules, explicit provider helper calls, shell downloads from named provider graph endpoints and any `--live-refetch` flag.
3. Requires direct provider-execution signatures to be limited to `weekly.yml` and `repro-rehearsal.yml`, with explicit canonical rights-gate checks preceding those commands and exact `hold == 'false'` generation conditions. This test is deliberately stricter than the previous `python usd_impact_score_v2.py`-only registry; new command syntaxes or unreviewed workflows will fail the existing `unittest discover` protected quality check.
4. Verifies all eight previously reviewed Score rights-gated workflow definitions still contain the canonical rights-gate invocation; rejects new `USD_IMPACT_SCORE_ALLOW` bypass or `--live-refetch` in any workflow.
5. Includes invented adversarial command signatures and benign synthetic/metadata-only examples, so detector changes cannot silently weaken or falsely broaden the allowlist. It reads only static text; no code from checked workflows is executed.

**Limit:** Text matching does not prove arbitrary multi-line shell scripts, imports, Bash aliases, direct Python `exec`, composite actions, remote dependencies or external services are non-providering. It is a fail-closed review aid for known high-risk signatures, **not** a sandbox or universal provider/network deny.

## Next architectural controls — separate owner-approved design, not implemented here

### Gate A: operational inventory and ownership

Identify every *non-GitHub-Actions* execution environment that may invoke original Score modules: Windows Task Scheduler, Linux cron, Render cron/background workers, Vercel jobs, desktop scripts/notebooks, external webhook/agent and CI clones. For each, inventory **environment**, **executable/entrypoint**, **schedule**, **repo revision**, **operator**, **last execution evidence (metadata only)** and **HOLD acknowledgement**. Do not copy API tokens, provider payloads, logs containing numerical values or personal credentials into GitHub. Mark unknowns `UNVERIFIED`, not `NONE`.

### Gate B: mandatory operational broker

Because the original v3 pre-holdout engine and reproduction builder are immutable, do **not** edit their bytes, research lock hashes, methodology or saved model history. Any *supported operational* job should instead be reconfigured to use a new broker/launcher that:
- Checks the **canonical** rights and separate source-specific release contract **before** accessing source caches, original modules, source transport, logs, database or public artifacts.
- Explicitly denies all provider access under current v1, including a fabricated `allow` with GitHub receipt; no environment-based bypass.
- Runs in a constrained, least-privileged execution identity with outbound egress denied unless independently authorized, and protected branch/source provenance.
- Enforces a single verified task/job scheduler route; external jobs require migration/disable evidence rather than hoping the voluntary launcher is used.
- Distinguishes **synthetic** offline validation from unapproved *real* cached/provider processing; all rights and public release remain separate gates.
- Maintains the immutable frozen research engine **as a separate source artifact**, avoiding editing/rebaselining any v3 preregistration or its hash.

No network-deny firewall/worker change, workflow rewiring, scheduler mutation, new paid service or Production site change is authorized by this design.

### Gate C: post-migration verification, future approval only

Before allowing a future provider-enabled task, owner+technical reviewer must check non-production no-egress negative tests, immutable research lock, exact-head CI, absence of direct invocations across known jobs and legal source-by-source rights/retention approval. Any live-source request or public deployment then requires *separate* written owner authorization and a reviewable, rights-safe output schema. Old Git/Pages/Actions/backup handling remains under [Issue #282](https://github.com/usdimpact/usd-impact-pipeline/issues/282); public redistribution rights under [Issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155). The independent Macro Context Panel remains isolated under [Issue #313](https://github.com/usdimpact/usd-impact-pipeline/issues/313).

## Required manual steps and links

**Now, only for anyone with an external/local scheduler:** check whether it starts `usd_impact_score_v2.py`, `scripts.build_score_repro_bundle --live-refetch` or `fetch_all_inputs`/provider helpers without the guarded launcher. Disable those scheduled invocations under HOLD, retaining only non-sensitive execution/disable confirmation. Review [GitHub Actions](https://github.com/usdimpact/usd-impact-pipeline/actions) and [guarded launcher runbook](score-provider-entrypoint-hold-guard-2026-10-30.md). The central GitHub Actions Score paths are already gated; do **not** manually dispatch live-score or reproduction runs. If there are no independent jobs, no owner UI action is necessary for this engineering PR.

**Before attempting real data or reopening publication:** legal/source rights and public output in [#155](https://github.com/usdimpact/usd-impact-pipeline/issues/155); retention/disposal in [#282](https://github.com/usdimpact/usd-impact-pipeline/issues/282); separate operational-broker and rights-contract owner signoff, no budget for paid licenses. Do not modify Cloudflare Pages access/headers to resolve the old monitor's 403; that would weaken the premium perimeter.

## Acceptance and hold

Only one new offline test module plus this documentation should change. Do not change `public/`, `governance/`, workflows, frozen research, original Score source, Cloudflare, Supabase, Render, Vercel, pricing, entitlements or deployments. All proposed-source rights **56/56 denied** and legacy Score successor dimensions **128/128 denied** remain unchanged; original Score rights `hold` with null decision receipt. **No live provider requests and no production release.**
