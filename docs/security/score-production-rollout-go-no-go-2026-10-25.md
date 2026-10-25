# USD Impact Score — Production Rollout / Go-No-Go Package

Date: 2026-10-25  
Status: RELEASE HOLD — preparation only; no Production activation authorized  
Primary implementation PR: usdimpact/usd-impact-pipeline#148  
Companion website PR: usdimpact/usd-impact-site#836

## STATUS

- Scope: Production architecture, secrets/bindings inventory, routing, security controls, acceptance gates, rollback, and release order for the protected USD Impact Score.
- Current decision: NO-GO for Production activation. Development/Preview acceptance passed, but Production prerequisites are intentionally incomplete.
- Production changes performed by this package: none.
- Main/DNS/Production DB mutations: none.
- Conflicts: none with current release-hold policy. Production Supabase live inventory is an explicit evidence gap because the current connector cannot read that project.
- Next action after this document: implement the Production-only server bridge and Worker configuration on draft branches, then run staged Production acceptance without assigning the public domain.

## 1. Hard constraints

1. main is Production. No merge to main is implied by this document.
2. No Production deploy, promotion, env mutation, DNS/domain change, database migration, entitlement mutation, sending, or billing action is authorized here.
3. Production must remain fail-closed until every GO item below is independently verified.
4. Secrets must never be committed, printed in CI, included in PR comments, or copied through chat.
5. Preview machine-auth credentials are Development-only and must not be copied into Production.
6. Production must use the current Research Membership state on every protected Score request, not only at initial sign-in.
7. Browser/email state alone is never sufficient. Access requires a verified account plus active Research Membership entitlement.

## 2. Accepted Development/Preview evidence

The accepted Preview path was:

stable Vercel PR #836 website alias -> one-time handoff ticket -> pr-148 Worker -> machine3 JWT -> Supabase verify_jwt -> Development broker -> atomic ticket consume -> current Research Membership recheck -> short-lived Score session -> protected dashboard.

Acceptance completed successfully on 2026-10-25.

Observed PASS evidence:

- QA website authentication recognized the account as active.
- Score-specific membership endpoint returned allowed=true and productId=research-membership.
- Website issued one one-time /en/ handoff ticket.
- Worker redeemed the ticket successfully after synchronizing SCORE_EDGE_SHARED_SECRET.
- Supabase gateway accepted the dedicated machine JWT with verify_jwt=true.
- Browser landed on the isolated Worker /en/ dashboard.
- Protected dashboard rendered correctly.
- Successful handoff left 0 live handoff tickets and 1 short-lived Score session.
- Existing backend contract tests separately proved immediate ticket replay denial and ticket-expiry denial.
- Live revocation was tested against the already-issued session: changing the QA Research entitlement to revoked caused immediate denial.
- Restoring the exact entitlement state caused the same existing Score session to become valid again without a new ticket.
- Test session was deleted afterward.
- Final state: 0 live tickets, 0 live sessions, QA entitlement active.
- Worker /en/ and /score-redeem returned 503 after all activation flags were restored OFF.
- Development broker restored to its normal env-controlled source with verify_jwt=true.
- Post-cleanup validate-release completed successfully.

This is not Production approval. It proves the access-control design under Development/Preview conditions.

## 3. Live Production baseline before any Score gating change

### 3.1 Website — Vercel

Project:
- Vercel project: usd-impact-site
- Project ID: prj_ZoLLM35ksI6wk17PcfS2xYknaVl7
- Public domains include www.usd-impact.com and usd-impact.com.
- Production custom domains are not protected by Vercel SSO; Vercel-owned deployment URLs remain protected according to project settings.

Current Production deployment observed while preparing this package:
- Deployment ID: dpl_C3YDDfpVLNvdvSzvH7MEUuU6ZBvB
- Deployment URL: usd-impact-site-19u3kcomr-usd-impact.vercel.app
- Git branch: main
- Git commit: b980b8fbcc5a297731a74228409d5282e5422768
- State: READY

Provider link:
https://vercel.com/usd-impact/usd-impact-site/C3YDDfpVLNvdvSzvH7MEUuU6ZBvB

Important env finding: the project env inventory returned no project-scoped Production variables whose names begin with SCORE, PUBLIC_SCORE, or SUPABASE. Current Score variables observed in this workstream are branch-specific Preview variables only. Shared/inherited environment variables may exist outside this project-scoped list and therefore remain a mandatory pre-GO verification item.

### 3.2 Score static origin — Cloudflare Pages

Project:
- Pages project: usd-impact-pipeline
- Production branch: main
- Public custom domain: score.usd-impact.com

Current Production Pages deployment observed while preparing this package:
- Deployment ID: 163e75ac-7a39-4ead-a0b5-452ca5d4e654
- URL: https://163e75ac.usd-impact-pipeline.pages.dev
- Branch: main
- Commit: 1bdd9a47796876e794bb6a24248ced8823f8b719
- Alias: https://score.usd-impact.com
- State: successful

This is the rollback origin of record until immediately before an authorized Production release. Re-record the then-current Pages deployment ID/commit immediately before GO because weekly Score publication may advance main.

### 3.3 Cloudflare Worker baseline

Current gated Worker:
- Worker: usd-impact-score-isolated-dev
- Tags: usd-impact, development-only
- Production workers.dev subdomain: disabled
- Preview URLs: enabled
- Activation flags: OFF
- SCORE_EDGE_SHARED_SECRET: encrypted secret_text
- Machine password: encrypted secret_text
- Native ASSETS binding present on accepted Wrangler Preview builds
- Worker observability/logs/traces: disabled

An obsolete temporary probe Worker, score-preview-stage-probe-temp-20261024, was verified unreferenced and deleted during preparation of this package.

### 3.4 Production Supabase evidence gap — blocking

Production project reference of record:
- zyhjtbjbmeeyhqunwvzr

The current connector is not authorized to read this Production project. Therefore this document does not claim that the required Score tables/RPCs already exist in Production.

GO is blocked until an owner-authenticated read-only inventory verifies the exact Production objects and grants listed in section 6.

## 4. Production architecture decision

### 4.1 Do not copy the Development broker architecture into Production

The Development path uses a dedicated Supabase Auth machine user and a public Supabase Edge Function broker so Cloudflare can reach privileged Development RPCs without carrying a Supabase secret key.

That was appropriate for isolated Preview acceptance, but Production should use a tighter first-party boundary:

browser -> www.usd-impact.com -> one-time ticket -> score.usd-impact.com Worker -> first-party Vercel server endpoint -> Production Supabase RPCs

### 4.2 Recommended Production trust boundary

Create a Production-only first-party server bridge inside usd-impact-site. The implemented draft reuses the existing account serverless function to stay within the enforced 12-function Vercel limit:

POST /api/account?action=score-edge

The fixed action query is a route selector only. Authentication material remains exclusively in the X-Score-Edge-Secret header; extra query parameters are rejected.

Allowed actions:
- redeem
- validate

The endpoint must:
1. accept POST only;
2. require exact JSON media type;
3. reject query strings/fragments;
4. cap request body bytes before JSON parsing;
5. authenticate the Worker with a high-entropy shared secret;
6. perform constant-time comparison;
7. never return Supabase provider errors, account IDs, keys, ticket digests, or session digests;
8. use existing server-only SUPABASE_SECRET_KEY to call a fixed RPC allowlist;
9. re-check active Research Membership during ticket redemption and every session validation;
10. emit generic fail-closed responses only.

Production Cloudflare must not receive:
- SUPABASE_SECRET_KEY
- any service-role/secret API key
- SCORE_PREVIEW_MACHINE_PASSWORD
- SCORE_PREVIEW_MACHINE_SUB
- a Production Supabase user password
- a Supabase Auth refresh token

This removes the public Supabase Edge broker from the eventual Production ingress and eliminates the machine-password boundary from Production.

## 5. Required Production secrets and bindings

No values are recorded here.

### 5.1 Vercel Production — website/server

Required effective variables for the Production deployment:

| Name | Type | Initial state / purpose |
| --- | --- | --- |
| SUPABASE_URL | plain config | Exact Production Supabase origin; verify effective value before GO |
| SUPABASE_PUBLISHABLE_KEY | encrypted/config | Existing public client key if required by current auth runtime |
| SUPABASE_SECRET_KEY | sensitive secret | Existing server-only Production key; never sent to browser/Cloudflare |
| SCORE_EDGE_SHARED_SECRET | sensitive secret | Same newly generated Production value as Cloudflare Worker |
| SCORE_HANDOFF_ISSUANCE_ENABLED | config | false until final website activation gate |
| PUBLIC_SCORE_PIPELINE_ORIGIN | plain config | https://score.usd-impact.com |
| SCORE_EDGE_BRIDGE_ENABLED | config | false until staged acceptance authorizes bridge calls |

If implementation uses a different exact flag name, code and this runbook must be updated together before review. No implicit fallback from Preview flags is allowed.

### 5.2 Cloudflare Production Worker

Use a separate Production Worker identity, not the Development-only Worker name.

Recommended name:
- usd-impact-score-production

Required bindings:

| Name | Type | Initial state / purpose |
| --- | --- | --- |
| ASSETS | assets binding | Exact reviewed Score static bundle |
| SCORE_WORKER_ENABLED | plain config | false until final staged acceptance |
| SCORE_EDGE_GATE_ENABLED | plain config | false until final staged acceptance |
| SCORE_EDGE_REDEMPTION_ENABLED | plain config | false until final staged acceptance |
| SCORE_EDGE_SHARED_SECRET | encrypted secret | Same Production value as Vercel |
| SCORE_EDGE_BRIDGE_ORIGIN | plain config | Exact first-party Vercel origin, normally https://www.usd-impact.com |
| SCORE_REDEEM_LIMIT | rate-limit binding | 30 requests / 60 seconds |
| SCORE_VALIDATE_LIMIT | rate-limit binding | 180 requests / 60 seconds |

Do not create Production equivalents of the Preview machine password/subject bindings.

### 5.3 Supabase Production

No Score-specific Edge Function secret is required by the recommended Production architecture because the privileged bridge remains on Vercel.

The Production database must contain only the reviewed tables/RPCs/grants needed for one-time tickets and short-lived Score sessions.

## 6. Mandatory Production Supabase read-only inventory — GO blocker

Before any migration or Production release, verify all of the following with an owner-authenticated read-only session.

Required tables:
- public.entitlements
- public.score_handoff_tickets
- public.score_member_sessions

Required RPCs:
- public.score_ticket_issue_atomic
- public.score_ticket_consume_atomic
- public.score_membership_active
- public.score_session_create
- public.score_session_lookup

If a Production global broker budget is retained, its function must have a Production-specific name and contract; do not copy the Preview-only budget function blindly.

Required authorization review:
- no direct browser client access;
- no broad anon/authenticated table grants;
- RLS state explicitly verified;
- any SECURITY DEFINER function has EXECUTE revoked from PUBLIC, anon, and authenticated unless a specific reviewed exception exists;
- fixed search_path where applicable;
- RPC parameters are bounded and validated;
- membership-active check cannot be bypassed by stale JWT metadata;
- no authorization decision depends on user-editable user_metadata.

NO-GO if this inventory cannot be proved.

## 7. Origin and request contract

### Website -> Worker

Production browser origin:
- https://www.usd-impact.com

Worker redeem endpoint:
- POST https://score.usd-impact.com/score-redeem

Required checks:
- exact HTTPS origin;
- no alternate Vercel deployment origin accepted in Production;
- no wildcard origins;
- form body contains only the bounded one-time ticket;
- one-time ticket lifetime remains approximately one minute;
- successful redeem returns a relative protected Score path only.

### Worker -> Vercel bridge

Implemented draft endpoint:
- POST https://www.usd-impact.com/api/account?action=score-edge

Required headers:
- Content-Type: application/json
- X-Score-Edge-Secret: secret

Required request body:
- redeem action with ticket
- validate action with token

No query-string authentication. The only accepted query component is the exact fixed route selector action=score-edge; no secret, ticket, token, account identifier, or other authentication material may appear in the query string.

### Score session cookie

Production cookie contract:
- name: __Host-score_session
- Secure
- HttpOnly
- SameSite=Lax
- Path=/
- no Domain attribute
- opaque value only
- ticket value never copied into the cookie
- short TTL; Preview acceptance used approximately 14 minutes

Every protected request must revalidate current membership server-side.

## 8. Public vs protected paths

Public methodology/transparency resources remain readable without Research Membership.

Protected content includes the premium Score dashboard and archive paths.

The implementation must preserve an explicit allowlist. It must never infer public access from file extension alone.

Acceptance must prove:
- anonymous premium HTML denied;
- active-member premium HTML allowed;
- public methodology/reproducibility resources readable;
- direct static-asset URLs cannot bypass the protected HTML/session gate where the asset itself is premium;
- archive language variants obey the same gate.

## 9. Rate limiting and abuse controls

Minimum Worker limits, matching the accepted Preview contract:
- ticket redemption: 30 / 60 seconds
- session validation: 180 / 60 seconds

These are application-layer fail-closed limits, not a replacement for zone-level controls.

Preferred Production routing uses a Cloudflare Worker Route in front of the existing score.usd-impact.com Pages origin. Cloudflare documents Routes as an interception layer on an existing proxied hostname. This is preferred because removing the route restores the pre-release Pages origin without moving the custom domain.

Provider reference:
https://developers.cloudflare.com/workers/configuration/routing/routes/

Before GO, verify zone-level access and whether a WAF rate-limit rule is available for this hostname. If available, add a second independent layer for POST /score-redeem. Do not make WAF availability the only rate-control mechanism.

## 10. Logging and privacy exclusions

### Cloudflare Worker

Preferred Production baseline:
- Worker observability OFF initially, matching the accepted Preview baseline.

If observability is later enabled:
- redact query strings;
- never log request bodies;
- never log Cookie;
- never log Set-Cookie;
- never log Authorization;
- never log X-Score-Edge-Secret;
- never log raw ticket/session values;
- never log Supabase keys;
- no persistent tail consumer until independently reviewed.

Allowed telemetry:
- coarse result code;
- route name;
- response status;
- rate-limit outcome;
- duration;
- deployment/version identifier.

### Vercel

The Score bridge must not log:
- raw request object;
- request headers;
- body;
- ticket;
- session token;
- account ID;
- email;
- shared secret;
- Supabase key;
- provider response payload containing user identifiers.

Allowed structured fields:
- generic stage/reason code;
- HTTP status;
- server request ID;
- duration.

### Supabase

RPC failures must be mapped to generic server errors at the Vercel boundary. Raw provider errors must not be returned to the Worker/browser.

## 11. Staged Production acceptance — no public cutover yet

All stages require explicit separate authorization.

### Stage A — exact-head code review

- Production Worker implementation contains no Development project reference.
- Website bridge contains no Preview Worker URL.
- No Preview machine credential names exist in Production config.
- All tests and security checks pass at exact reviewed heads.
- Dependency/security review green.
- Release-control status remains HOLD.

### Stage B — Production database inventory/migration

- Complete section 6 read-only inventory.
- If objects are missing, prepare a reviewed migration.
- Apply only after explicit database authorization.
- Verify grants/RLS after migration.
- Create a dedicated Production QA entitlement only if separately approved.

### Stage C — Vercel staged Production build

Use a staged Production deployment without assigning domains:
- build with Production environment;
- deploy with Production target but skip domain assignment;
- verify exact commit and effective env-name inventory;
- SCORE_HANDOFF_ISSUANCE_ENABLED=false;
- SCORE_EDGE_BRIDGE_ENABLED=false.

Do not promote yet.

### Stage D — Cloudflare Production Worker candidate

- separate Worker identity;
- Production secret generated independently from Development;
- assets from exact reviewed commit;
- no workers.dev public subdomain for the final Production Worker;
- all activation flags OFF initially;
- stage via a non-public Preview URL where possible.

### Stage E — isolated Production-data QA

After explicit authorization:
- enable only the Vercel bridge and Worker candidate in an isolated candidate path;
- eligible Production QA account only;
- no real customer entitlement mutation;
- repeat the full matrix:
  - anonymous denial;
  - active membership acceptance;
  - one-time ticket consumption;
  - replay denial;
  - expiry denial;
  - secure cookie attributes;
  - protected archive access;
  - public methodology access;
  - live entitlement revocation;
  - restoration;
  - cleanup.

### Stage F — cutover

Only after an explicit GO decision.

Preferred sequence:
1. record the current Vercel Production deployment ID and current Cloudflare Pages Production deployment ID/commit;
2. ensure website Production code is present with handoff issuance still OFF;
3. ensure Production Worker is fully configured and acceptance-tested;
4. enable Worker internal gate/redemption/session validation;
5. add the Worker Route in front of score.usd-impact.com/*;
6. smoke-test anonymous/public/protected behavior;
7. enable website handoff issuance;
8. perform one eligible QA browser handoff;
9. check errors/latency/denials;
10. keep a live rollback operator ready until the acceptance window closes.

## 12. Rollback contract

Rollback must not depend on writing database fixes under pressure.

Immediate rollback order:
1. disable website SCORE_HANDOFF_ISSUANCE_ENABLED;
2. remove the Cloudflare Worker Route from score.usd-impact.com/*;
3. confirm traffic falls back to the pre-recorded Cloudflare Pages Production deployment;
4. set Worker activation/gate/redemption flags OFF;
5. if website code itself regressed, roll Vercel back to the exact pre-release Production deployment;
6. leave existing sessions/tickets to expire naturally unless a reviewed emergency cleanup is required;
7. do not delete entitlements as part of rollback.

Current baseline references at document creation:

Vercel:
- dpl_C3YDDfpVLNvdvSzvH7MEUuU6ZBvB
- commit b980b8fbcc5a297731a74228409d5282e5422768

Cloudflare Pages:
- 163e75ac-7a39-4ead-a0b5-452ca5d4e654
- commit 1bdd9a47796876e794bb6a24248ced8823f8b719

These are historical baselines, not permanent rollback IDs. Refresh them immediately before an authorized cutover.

## 13. GO / NO-GO matrix

GO requires every item:

- [ ] Production Supabase schema/RPC/grant inventory independently verified.
- [ ] Production implementation contains no Development project IDs or Preview machine credentials.
- [ ] Vercel effective Production env inventory reviewed without exposing values.
- [ ] Production shared secret exists only in Vercel + Cloudflare secret stores.
- [ ] Website issuance flag defaults OFF.
- [ ] Worker gate/redemption flags default OFF.
- [ ] Production Worker has native assets from exact reviewed commit.
- [ ] Exact website origin allowlist reviewed.
- [ ] Exact Worker/bridge origin reviewed.
- [ ] Worker rate-limit bindings present.
- [ ] Logging/privacy exclusions verified.
- [ ] Public methodology allowlist tests pass.
- [ ] Anonymous premium denial tests pass.
- [ ] Eligible member handoff passes.
- [ ] Ticket replay denial passes.
- [ ] Ticket expiry denial passes.
- [ ] Session cookie attributes pass.
- [ ] Live entitlement revocation denies an existing session.
- [ ] Entitlement restoration behaves as designed.
- [ ] Direct asset bypass tests pass.
- [ ] QA residue cleaned.
- [ ] Exact-head CI/security checks green.
- [ ] Current pre-release Vercel and Pages rollback IDs recorded.
- [ ] Cloudflare zone Route permission and rollback path verified.
- [ ] Explicit owner GO recorded for merge/deploy/domain steps.

Automatic NO-GO:

- Production Supabase inventory cannot be read/verified.
- Any secret is visible in source, logs, PR comments, screenshots, or artifacts.
- Production Worker requires a user password or Supabase secret key.
- Any Preview/Development project reference remains in Production code/config.
- Any protected asset is directly reachable without session validation.
- Membership revocation does not affect an existing Score session immediately.
- Worker route rollback cannot be proven.
- Exact-head tests are not green.
- Production env values are ambiguous or inherited without verification.
- Public domain/routing ownership is unclear.
- Release hold has not been explicitly lifted.

## 14. Merge/deployment order — future authorized release only

This section is a sequence, not authorization.

1. Review and approve Production database migration, if required.
2. Apply and verify Production DB migration.
3. Merge Production server bridge implementation into the website release branch.
4. Merge Production Worker/runtime implementation into the pipeline release branch.
5. Stage Vercel Production deployment without domain assignment.
6. Stage Cloudflare Production Worker candidate without public cutover.
7. Run Production-data QA acceptance.
8. Record fresh rollback IDs.
9. Merge/promote website code with issuance OFF.
10. Deploy Worker with all internals ready but no public route.
11. Add score.usd-impact.com/* Worker Route.
12. Smoke test.
13. Enable website handoff issuance through a reviewed Production deployment.
14. Run one final eligible QA handoff.
15. Monitor the bounded release window.
16. Record PASS evidence and close HOLD only after all acceptance checks remain green.

## 15. Current decision

NO-GO.

Reason:
- Preview acceptance is complete and clean.
- The Production architecture and rollback strategy are defined.
- The live Production Supabase schema/functions/grants have not yet been independently verified.
- Draft Production implementation now exists and is CI-green: website bridge head 94680a060896b684d2b6947b6299065ba85888f0 and pipeline Worker/security head 8e3ffc3433cf508aff824893904d8915558c948a.
- The implementation remains draft/unmerged and has not been staged with Production environment values, Worker secrets, routes, domains, or Production database access.
- Production Supabase live schema/RPC/grant inventory remains unverified and is still a blocking NO-GO item.

The next safe engineering task is read-only Production Supabase schema/RPC/grant verification plus effective Production Vercel environment-name verification. Until those inventories are proven, do not stage Production secrets, deploy the Production Worker candidate, add a Worker Route, or enable any Production Score flag.
