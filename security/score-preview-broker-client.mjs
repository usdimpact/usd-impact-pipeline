// Cloudflare Pages Preview client for the Development-only Edge broker.
// No Supabase secret/service-role key is ever present in Cloudflare Pages.
export const SCORE_PREVIEW_BROKER_URL =
  'https://ycstrcvshdluovtuasjc.supabase.co/functions/v1/score-preview-broker';
const TOKEN = /^[A-Za-z0-9_-]{43}$/;
const SECRET = /^[A-Za-z0-9_-]{43,128}$/;
const PATHS = new Set(['/en/', '/es/', '/archive/en/', '/archive/es/']);
const JWT = /^[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{16,}$/;
const MACHINE_ISSUER = 'https://ycstrcvshdluovtuasjc.supabase.co/auth/v1';
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function decodeJwtPart(value) {
  const normalized = value.replace(/-/g,'+').replace(/_/g,'/');
  const padded = normalized + '='.repeat((4 - normalized.length % 4) % 4);
  return JSON.parse(atob(padded));
}
function isLeastPrivilegeMachineJwt(jwt) {
  if (!JWT.test(jwt || '')) return false;
  try {
    const payload = decodeJwtPart(jwt.split('.')[1]);
    return payload?.iss === MACHINE_ISSUER &&
      payload?.aud === 'authenticated' &&
      payload?.role === 'authenticated' &&
      payload?.is_anonymous === false &&
      UUID.test(payload?.sub || '') &&
      payload.sub === env?.SCORE_PREVIEW_MACHINE_SUB &&
      Number.isFinite(payload?.exp) &&
      payload.exp > Math.floor(Date.now()/1000) + 30;
  } catch {
    return false;
  }
}

async function invoke(action, token, env, fetchImpl) {
  if (env?.SCORE_DEV_BROKER_ENABLED !== 'true' ||
      !SECRET.test(env?.SCORE_EDGE_SHARED_SECRET || '') ||
      !isLeastPrivilegeMachineJwt(env?.SCORE_PREVIEW_MACHINE_JWT || '') ||
      !TOKEN.test(token || '')) throw new Error('Score Preview broker unavailable');
  const name = action === 'redeem' ? 'ticket' : action === 'validate' ? 'token' : null;
  if (!name) throw new Error('Unsupported broker operation');
  const result = await fetchImpl(SCORE_PREVIEW_BROKER_URL, {
    method: 'POST', redirect: 'error', cache: 'no-store',
    // Bound the entire Cloudflare-to-Development broker request, including response body.
    signal: AbortSignal.timeout(18_000),
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      'X-Score-Edge-Secret': env.SCORE_EDGE_SHARED_SECRET,
      Authorization: `Bearer ${env.SCORE_PREVIEW_MACHINE_JWT}`,
      'Cache-Control': 'no-store',
    },
    body: JSON.stringify({ action, [name]: token }),
  });
  if (result.status === 403) return null; // revoked/replayed or denied
  if (result.status !== 200) throw new Error('Score broker unavailable');
  return result.json();
}
export async function redeemScoreBrokerTicket(ticket, env, fetchImpl = fetch) {
  const payload = await invoke('redeem', ticket, env, fetchImpl);
  if (!payload || payload.allowed !== true ||
      !TOKEN.test(payload.token || '') ||
      !PATHS.has(payload.path) ||
      !Number.isFinite(payload.expiresAtMs)) return null;
  return payload;
}
export async function scoreBrokerSessionAllowed(token, env, fetchImpl = fetch) {
  const payload = await invoke('validate', token, env, fetchImpl);
  return payload?.allowed === true;
}
