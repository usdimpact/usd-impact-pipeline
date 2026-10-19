# Score Research Membership — isolated Preview acceptance plan

Status: **PREPARED, NOT EXECUTED**. No Production configuration, database migrations, secrets, or feature flags are changed by this document.

## Boundaries and prerequisites

- Website draft PR #836 and Score draft PR #148 must remain unmerged. Confirm current Preview deployment IDs and CI success immediately before testing.
- Use a separate non-Production Supabase project or isolated test database with only the reviewed Score ticket/session migrations. Do not apply SQL to Production.
- Configure Preview-only server-to-server shared secret (minimum 32 characters), HTTPS Vercel backend endpoints, and Cloudflare Preview routing. Keep Production `SCORE_HANDOFF_ISSUANCE_ENABLED`, `SCORE_EDGE_REDEMPTION_ENABLED`, and `SCORE_EDGE_GATE_ENABLED` disabled.
- Use dedicated test identities: active Research Membership, Library Pass-only, expired/revoked membership, and anonymous. No real customer entitlement modifications.
- The Score redemption function accepts the Production hostname `score.usd-impact.com` and, only when `SCORE_PREVIEW_REDEMPTION_HOST` is explicitly configured, its exact matching `*.usd-impact-pipeline.pages.dev` Preview hostname. Confirm the pinned Preview hostname and isolated routing before browser redemption acceptance; do not use a broad wildcard or Production credentials.
- Validate that Preview routing uses the consolidated website account API actions. Current draft Score backend URL path checks refer to `/api/score-edge-redeem` and `/api/score-edge-validate`; verify they resolve via the website's Vercel rewrites before testing.

## Acceptance matrix (record actual status, not assumptions)

| Test | Expected | Result |
|---|---|---|
| Gate disabled, anonymous | 403 and no premium bytes | NOT RUN |
| Active member, valid single-use ticket | POST redemption sets secure HttpOnly cookie and 303 to allowlisted path | NOT RUN |
| Ticket replay or expired ticket | No session; 401/403 | NOT RUN |
| Wrong path, wrong audience, malformed ticket | No cookie, no redirect to attacker origin | NOT RUN |
| Active session, authorized backend | Dashboard and member archive load with private/no-store headers | NOT RUN |
| Library Pass only, anonymous, unverified | 401/403; no premium bytes | NOT RUN |
| Revoked/refunded membership after session issued | Next protected request denied | NOT RUN |
| Validation backend unavailable or wrong shared secret | Fail closed; no premium bytes | NOT RUN |
| Direct Cloudflare Pages custom and pages.dev hosts, assets, HTML | No premium bytes without authorization | NOT RUN |
| Standalone sign-in and embedded normal/incognito | No loops; iframe isolation enforced | NOT RUN |
| Public methodology and approved research data | Accessible per public policy | NOT RUN |
| Cookie, CSP, cache, logs, referrer | Secure attributes, no-store, no ticket or token leaks | NOT RUN |

## Execution sequence

1. Verify PR heads and successful checks. Record deployment IDs and the exact isolated test hostnames.
2. Review migrations, secret placement, Preview hostname validation, and backend rewrite paths. Stop if any route is inconsistent or would require a Production change.
3. Test fail-closed access on each Preview/direct origin before enabling any Preview-only gate.
4. With isolated Preview credentials and entitlement, test issuance, one-time redemption, cookie scope, and authorized protected content.
5. Test negative identities, replay, expiry, revocation, backend outage, direct-origin bypass, and public-resource preservation.
6. Test standalone and embedded browser flows; collect sanitized HTTP statuses, headers, timestamps, and deployment identifiers. Never log ticket/session values.
7. Reset Preview flags to disabled and remove disposable credentials; attach evidence to both PRs for a separate go/no-go decision.

**Stop condition:** Any protected HTML accessible without verified authorization, any cross-origin credential leak, or any request that reaches Production systems ends acceptance immediately. Release remains HOLD until all required rows pass.
