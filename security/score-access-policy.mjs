// Pure authorization decision only. Not a route, session validator, or deployed gateway.
// The caller MUST first verify user identity, profile and entitlement from a trusted server.
export const SCORE_PRODUCT_ID = 'research-membership';

export function scoreAccessDecision({ verifiedUser, profile, entitlement, nowMs = Date.now() } = {}) {
  if (!verifiedUser?.id || !verifiedUser.emailConfirmedAt) return { allowed: false, reason: 'unauthenticated' };
  if (!profile || profile.accountId !== verifiedUser.id || profile.status !== 'active') {
    return { allowed: false, reason: 'inactive-account' };
  }
  if (!entitlement || entitlement.accountId !== verifiedUser.id ||
      entitlement.productId !== SCORE_PRODUCT_ID) {
    return { allowed: false, reason: 'missing-membership' };
  }
  if (entitlement.state !== 'active') return { allowed: false, reason: 'inactive-membership' };
  const startsAt = Date.parse(entitlement.startsAt);
  if (!Number.isFinite(startsAt) || startsAt > nowMs) return { allowed: false, reason: 'not-started' };
  if (entitlement.endsAt !== null && entitlement.endsAt !== undefined) {
    const endsAt = Date.parse(entitlement.endsAt);
    if (!Number.isFinite(endsAt) || endsAt <= nowMs) return { allowed: false, reason: 'expired' };
  }
  return { allowed: true, reason: 'active' };
}

const ALLOWED_SCORE_PATHS = new Set(['/en/', '/es/', '/archive/en/', '/archive/es/']);
export function safeScoreReturnPath(value) {
  if (typeof value !== 'string' || !ALLOWED_SCORE_PATHS.has(value)) return null;
  return value;
}
