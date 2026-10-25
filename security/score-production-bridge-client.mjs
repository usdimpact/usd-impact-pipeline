// Production Cloudflare Worker client for the first-party Vercel Score bridge.
// No Supabase credential, user password, refresh token, or account identity belongs here.
export const SCORE_PRODUCTION_BRIDGE_ORIGIN = 'https://www.usd-impact.com';
export const SCORE_PRODUCTION_BRIDGE_URL =
  SCORE_PRODUCTION_BRIDGE_ORIGIN + '/api/account?action=score-edge';

const TOKEN = /^[A-Za-z0-9_-]{43}$/;
const SECRET = /^[A-Za-z0-9_-]{43,128}$/;
const PATHS = new Set(['/en/', '/es/', '/archive/en/', '/archive/es/']);
const MAX_RESPONSE_BYTES = 2048;

function fail() {
  throw new Error('Score edge unavailable');
}

async function boundedJson(response) {
  const announced = response.headers.get('content-length');
  if (announced !== null && (!/^\d+$/.test(announced) || Number(announced) > MAX_RESPONSE_BYTES)) fail();
  const reader = response.body?.getReader();
  if (!reader) fail();
  const chunks = [];
  let bytes = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    bytes += value.byteLength;
    if (bytes > MAX_RESPONSE_BYTES) {
      await reader.cancel().catch(() => {});
      fail();
    }
    chunks.push(value);
  }
  const joined = new Uint8Array(bytes);
  let offset = 0;
  for (const chunk of chunks) {
    joined.set(chunk, offset);
    offset += chunk.byteLength;
  }
  try {
    return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(joined));
  } catch {
    fail();
  }
}

async function invoke(action, credential, env, fetchImpl) {
  if (env?.SCORE_EDGE_BRIDGE_ORIGIN !== SCORE_PRODUCTION_BRIDGE_ORIGIN ||
      !SECRET.test(env?.SCORE_EDGE_SHARED_SECRET || '') ||
      !TOKEN.test(credential || '')) fail();
  const name = action === 'redeem' ? 'ticket' : action === 'validate' ? 'token' : null;
  if (!name) fail();

  const result = await fetchImpl(SCORE_PRODUCTION_BRIDGE_URL, {
    method: 'POST',
    redirect: 'error',
    cache: 'no-store',
    signal: AbortSignal.timeout(10_000),
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      'X-Score-Edge-Secret': env.SCORE_EDGE_SHARED_SECRET,
      'Cache-Control': 'no-store',
    },
    body: JSON.stringify({ action, [name]: credential }),
  });
  if (result.status === 403) return null;
  if (result.status !== 200) fail();
  return boundedJson(result);
}

export async function redeemScoreEdgeTicket(ticket, env, fetchImpl = fetch) {
  const payload = await invoke('redeem', ticket, env, fetchImpl);
  if (!payload || payload.allowed !== true ||
      !TOKEN.test(payload.token || '') ||
      !PATHS.has(payload.path) ||
      typeof payload.expiresAt !== 'string') return null;
  const expiresAtMs = Date.parse(payload.expiresAt);
  if (!Number.isFinite(expiresAtMs) ||
      expiresAtMs <= Date.now() ||
      expiresAtMs > Date.now() + 15 * 60_000) return null;
  return { token: payload.token, path: payload.path, expiresAtMs };
}

export async function scoreEdgeSessionAllowed(token, env, fetchImpl = fetch) {
  const payload = await invoke('validate', token, env, fetchImpl);
  return payload?.allowed === true;
}
