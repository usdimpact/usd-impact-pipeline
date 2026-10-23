// Private Development Supabase RPC adapter used exclusively inside the Edge broker.
// Deliberately uses Web Crypto only (Cloudflare Pages runtime, not Node).
// All RPCs are server-side and restricted to the existing service_role grants.
// Never copy its privileged key to Cloudflare Pages or Production.

export const SCORE_DIRECT_PREVIEW_HOST = 'fix-score-membership-handoff.usd-impact-pipeline.pages.dev';
export const SCORE_DIRECT_WEBSITE_ORIGIN = 'https://usd-impact-site-55p15tktn-usd-impact.vercel.app';
const DEV_SUPABASE_ORIGIN = 'https://ycstrcvshdluovtuasjc.supabase.co';
const KEY_RE = /^sb_secret_[A-Za-z0-9_-]{16,}$/;
const TICKET_RE = /^[A-Za-z0-9_-]{43}$/;
const DIGEST_RE = /^[a-f0-9]{64}$/;
const ACCOUNT_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const SCORE_PATHS = new Set(['/en/', '/es/', '/archive/en/', '/archive/es/']);
const RPC_NAMES = new Set([
  'score_preview_broker_claim_budget',
  'score_ticket_consume_atomic', 'score_membership_active',
  'score_session_create', 'score_session_lookup',
]);

export function scoreDevBrokerPreviewEnabled(request, env) {
  if (env?.SCORE_DEV_BROKER_ENABLED !== 'true') return false;
  try {
    const url = new URL(request.url);
    return url.protocol === 'https:' && url.hostname === SCORE_DIRECT_PREVIEW_HOST &&
      (url.port === '' || url.port === '443');
  } catch {
    return false;
  }
}

export async function scoreDigest(value) {
  if (typeof value !== 'string' || !TICKET_RE.test(value)) return null;
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return Array.from(new Uint8Array(bytes), (b) => b.toString(16).padStart(2, '0')).join('');
}

function newScoreSessionToken() {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-')
    .replace(/\//g, '_').replace(/=+$/g, '');
}

function privateRpc(env, fetchImpl) {
  // Hardcoded Development database; only the isolated Supabase Edge broker
  // passes a server-only secret key. Never expose the key in Pages Preview.
  const key = env?.SCORE_PREVIEW_SUPABASE_SECRET_KEY;
  if (typeof key !== 'string' || !KEY_RE.test(key)) {
    throw new Error('Score Development credential unavailable');
  }
  return async function rpc(name, payload) {
    if (!RPC_NAMES.has(name)) throw new Error('Unknown Score RPC');
    const response = await fetchImpl(`${DEV_SUPABASE_ORIGIN}/rest/v1/rpc/${name}`, {
      method: 'POST', redirect: 'error', cache: 'no-store',
      // Fail closed if a Development RPC hangs. Keep requests individually bounded.
      signal: AbortSignal.timeout(5000),
      headers: {
        apikey: key,
        'Content-Type': 'application/json',
        Accept: 'application/json',
        'Cache-Control': 'no-store',
      },
      body: JSON.stringify(payload),
    });
    // A non-2xx response indicates an inaccessible RPC, missing grant,
    // incorrect key or outage. Never return upstream details to the browser.
    if (!response.ok) throw new Error('Score Development RPC unavailable');
    return response.json();
  };
}

// Global Development budget, applied AFTER the broker's shared-secret check.
// It does not replace upstream pre-Edge-function denial-of-service controls.
export async function claimScoreDevBrokerBudget(action, env, fetchImpl = fetch) {
  if (action !== 'redeem' && action !== 'validate') return false;
  const rpc = privateRpc(env, fetchImpl);
  return (await rpc('score_preview_broker_claim_budget', {p_action: action})) === true;
}

export async function redeemScoreDevTicket(ticket, env, fetchImpl = fetch) {
  const digest = await scoreDigest(ticket);
  if (!digest) return null;
  const rpc = privateRpc(env, fetchImpl);
  const record = await rpc('score_ticket_consume_atomic', { p_digest: digest });
  if (!record || Array.isArray(record) ||
      record.digest !== digest ||
      record.audience !== 'score.usd-impact.com' ||
      !SCORE_PATHS.has(record.path) ||
      !ACCOUNT_RE.test(record.account_id || '')) return null;
  const expiresAt = Date.parse(record.expires_at);
  const now = Date.now();
  if (!Number.isFinite(expiresAt) || expiresAt <= now || expiresAt > now + 65_000) return null;
  const active = await rpc('score_membership_active', { p_account_id: record.account_id });
  if (active !== true) return null;
  const token = newScoreSessionToken();
  const sessionDigest = await scoreDigest(token);
  if (!DIGEST_RE.test(sessionDigest || '')) throw new Error('Score session unavailable');
  const sessionExpiresAtMs = Date.now() + 14 * 60_000;
  const created = await rpc('score_session_create', {
    p_digest: sessionDigest, p_account_id: record.account_id,
    p_expires_at: new Date(sessionExpiresAtMs).toISOString(),
  });
  if (created !== true) return null; // Includes atomic, current-membership recheck
  return { allowed: true, token, path: record.path, expiresAtMs: sessionExpiresAtMs };
}

export async function scoreDevSessionAllowed(token, env, fetchImpl = fetch) {
  const digest = await scoreDigest(token);
  if (!digest) return false;
  const rpc = privateRpc(env, fetchImpl);
  // This RPC also checks current Research Membership on EVERY lookup;
  // revoked, expired, disputed and non-Research entitlements cannot pass.
  const found = await rpc('score_session_lookup', { p_digest: digest });
  const expiry = Date.parse(found?.expires_at);
  return Boolean(found && !Array.isArray(found) &&
    ACCOUNT_RE.test(found.account_id || '') &&
    Number.isFinite(expiry) && expiry > Date.now() &&
    expiry <= Date.now() + 15 * 60_000);
}
