# Score Preview machine JWT boundary — 2026-10-23

Status: SOURCE/REVIEW ONLY. RELEASE HOLD.

## Purpose

Protect the Development `score-preview-broker` before Edge Function handler execution without placing a privileged Supabase database credential in the isolated Cloudflare Worker Preview.

The request must pass two independent controls:

1. Supabase platform `verify_jwt=true` with a valid Development Auth access JWT.
2. Existing handler-level `X-Score-Edge-Secret` verification.

Neither control replaces the other.

## Required machine identity

Create one dedicated **Development-only Supabase Auth user** for Score Preview broker ingress.

Required properties:

- ordinary `authenticated` role only;
- non-anonymous;
- no Research Membership, Library Pass, subscription, or commercial entitlement;
- no direct grants on Score tables or RPCs;
- signed `app_metadata.score_preview_machine=true`;
- no user-editable metadata is used for authorization;
- identity exists only in the Development project.

The Worker additionally rejects JWTs unless the payload has:

- issuer exactly `https://ycstrcvshdluovtuasjc.supabase.co/auth/v1`;
- audience exactly `authenticated`;
- role exactly `authenticated`;
- `is_anonymous=false`;
- UUID subject;
- `app_metadata.score_preview_machine=true`;
- expiry more than 30 seconds in the future.

The Worker-side claim check is only a fail-closed policy guard. Supabase remains responsible for cryptographic JWT verification before handler execution.

## Explicitly forbidden credentials

Do not use any of the following as the Worker bearer credential:

- `service_role` JWT;
- `sb_secret_...` API key;
- legacy service-role API key;
- Production Auth JWT;
- customer/member JWT;
- the QA Research Membership account;
- a JWT signing private key or project JWT signing secret.

Current Supabase documentation confirms opaque publishable/secret API keys are not accepted by the Edge Function `verify_jwt` platform check.

## Preview secret handling

For controlled Development acceptance:

- place only a **short-lived access JWT** in the isolated Worker Preview secret `SCORE_PREVIEW_MACHINE_JWT`;
- keep `SCORE_EDGE_SHARED_SECRET` as a separate Preview secret;
- do not persist the machine user's password or refresh token in Cloudflare;
- do not commit either credential;
- do not expose either credential through Pages, Vercel, browser JavaScript, logs, URLs, or CI output;
- leave all access flags OFF while secrets are installed and verified.

For the initial acceptance cycle, mint a fresh short-lived access JWT immediately before testing and replace/remove it after the test window. Automated refresh is out of scope until a separate least-privilege token broker design is approved.

## Database boundary

The dedicated Auth user must not gain database access merely because it can pass `verify_jwt`.

Before staging:

- `score_handoff_tickets`: RLS ON; no `authenticated` SELECT/INSERT/UPDATE;
- `score_member_sessions`: RLS ON; no `authenticated` SELECT/INSERT/UPDATE;
- `score_preview_broker_budget`: RLS ON; no `authenticated` SELECT/INSERT/UPDATE;
- privileged Score RPCs remain unavailable to `authenticated`.

The broker continues using its own server-side Development database credential after both ingress checks pass.

## Rotation and revocation

Initial controlled acceptance:

1. Mint a fresh Development access JWT for the dedicated machine user.
2. Install it only in the isolated Worker Preview secret.
3. Run anonymous denial before enabling any broker/application flag.
4. Enable only the minimum Development flags required for the controlled test.
5. Complete ticket/replay/expiry/revocation/direct-bypass tests.
6. Disable flags again.
7. Remove/replace the Preview JWT after the acceptance window.
8. Revoke the machine Auth session if any credential handling anomaly occurs.

A long-lived refresh token must not be installed in the Worker during this phase.

## Runtime staging gate

Do not redeploy `score-preview-broker` with `verify_jwt=true` until all are true:

- exact-head CI/package/static checks pass;
- dedicated Development machine identity exists with the required signed app metadata;
- read-only database privilege audit still passes;
- isolated Worker Preview secret boundary is verified;
- anonymous request test is defined to prove rejection happens before handler execution;
- rollback procedure is recorded;
- Production remains untouched.

## Rollback

If the staged Development broker rejects legitimate Preview traffic or the machine identity cannot be verified:

- keep/restore all access flags OFF;
- remove the Preview machine JWT;
- redeploy the last reviewed disabled broker source only if necessary;
- do not weaken `verify_jwt`, add public table/RPC grants, or substitute `service_role`;
- preserve ticket/session tables for audit unless an independently approved cleanup is required.

Production is never part of this rollback path.
