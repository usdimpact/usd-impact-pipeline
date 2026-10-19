// Edge-side authorization for Score resources. Does not expose an HTTP route.
// A deployed caller must provide an authoritative, fresh server-side membership
// checker and durable session lookup; missing dependencies deny access.
import { readScoreSessionCookie } from './score-session-cookie.mjs';

export async function authorizeScoreEdgeRequest(request, { sessions, membership, nowMs = Date.now() } = {}) {
  const token = readScoreSessionCookie(request?.headers?.get?.('cookie'));
  if (!token || typeof sessions?.lookup !== 'function' ||
      typeof membership?.isActive !== 'function') {
    return { allowed: false, code: 'AUTHENTICATION_REQUIRED' };
  }
  try {
    const session = await sessions.lookup(token);
    if (!session || !session.accountId || !Number.isFinite(session.expiresAtMs) ||
        session.expiresAtMs <= nowMs || session.expiresAtMs > nowMs + 15 * 60_000) {
      return { allowed: false, code: 'INVALID_SESSION' };
    }
    const active = await membership.isActive(session.accountId);
    if (active !== true) return { allowed: false, code: 'RESEARCH_MEMBERSHIP_REQUIRED' };
    return { allowed: true, accountId: session.accountId };
  } catch {
    return { allowed: false, code: 'AUTHORIZATION_UNAVAILABLE' };
  }
}
