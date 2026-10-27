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
- no user-editable metadata is used for authorization;
- identity exists only in the Development project.

The Worker additionally rejects JWTs unless the payload has:

- issuer exactly `https://ycstrcvshdluovtuasjc.supabase.co/auth/v1`;
- audience exactly `authenticated`;
- role exactly `authenticated`;
- `is_anonymous=false`;
- UUID subject;
- subject exactly matches the pinned Development machine user UUID from `SCORE_PREVIEW_MACHINE_SUB`;
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

The isolated Worker now mints the short-lived Development Auth access JWT internally on demand. It never returns, logs, commits, or persists the access token or refresh token.

Required encrypted Worker Preview secrets:

- `SCORE_PREVIEW_MACHINE_PASSWORD` — dedicated Development machine user's password;
- `SCORE_EDGE_SHARED_SECRET` — independent broker application secret.

Required non-secret Preview configuration:

- `SCORE_PREVIEW_SUPABASE_PUBLISHABLE_KEY` — Development publishable key;
- `SCORE_PREVIEW_MACHINE_SUB` — exact dedicated machine Auth user UUID.

The Worker POSTs the machine email/password to the fixed Development Auth password-grant endpoint, validates the returned access JWT claims locally, immediately uses that JWT only in the broker Authorization header, and ignores any refresh token returned by Auth.

Do not commit the password/shared secret, expose either to browser JavaScript, logs, URLs, CI output, Pages, Vercel, or Production. Leave all Score access flags OFF while secrets are installed and verified.

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

1. Install the machine password and independent broker secret only as encrypted isolated Worker Preview secrets.
2. Keep the publishable key and pinned machine UUID as non-secret Preview configuration.
3. Run anonymous denial before enabling any broker/application flag.
4. Verify a disabled authenticated broker request reaches the handler only after a freshly minted machine JWT passes the Supabase gateway.
5. Enable only the minimum Development flags required for the controlled positive test.
6. Complete ticket/replay/expiry/revocation/direct-bypass tests.
7. Disable flags again.
8. Rotate the machine password and broker shared secret if any credential-handling anomaly occurs.

No refresh token is stored or used by the Worker.

## Runtime staging gate

Do not redeploy `score-preview-broker` with `verify_jwt=true` until all are true:

- exact-head CI/package/static checks pass;
- dedicated Development machine identity exists and its exact UUID is pinned in Worker Preview configuration;
- read-only database privilege audit still passes;
- isolated Worker Preview encrypted-secret boundary is verified;
- internal password-to-access-JWT mint path is source/test verified;
- anonymous request test proves rejection happens before handler execution;
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
