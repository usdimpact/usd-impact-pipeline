// Development Supabase Edge broker: server-side fixed operation gateway only.
// Authentication is independent of the Supabase service-role API key.
import { redeemScoreDevTicket, scoreDevSessionAllowed } from './score-preview-dev-rpc.mjs';
const DEV_ORIGIN = 'https://ycstrcvshdluovtuasjc.supabase.co';
const BROKER_PATH = '/functions/v1/score-preview-broker';
const OPAQUE = /^[A-Za-z0-9_-]{43}$/;
const KEY = /^sb_secret_[A-Za-z0-9_-]{16,}$/;
const SHARED = /^[A-Za-z0-9_-]{43,128}$/;
const HEADERS = {
  'Cache-Control': 'private, no-store',
  'Content-Type': 'application/json; charset=utf-8',
  'Referrer-Policy': 'no-referrer',
  'X-Content-Type-Options': 'nosniff',
};
const json = (status, data) => Response.json(data, { status, headers: HEADERS });
function opaqueEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' ||
      a.length > 128 || b.length > 128) return false;
  const enc = new TextEncoder();
  const aa = enc.encode(a), bb = enc.encode(b);
  let diff = aa.length ^ bb.length;
  for (let i = 0; i < Math.max(aa.length, bb.length); i++) diff |= (aa[i] ?? 0) ^ (bb[i] ?? 0);
  return diff === 0;
}
export async function handleScorePreviewBroker(request, config, fetchImpl = fetch) {
  if (request?.method !== 'POST') return json(405, { allowed: false });
  if (config?.enabled !== 'true' || config?.supabaseUrl !== DEV_ORIGIN ||
      !KEY.test(config?.supabaseSecretKey || '') ||
      !SHARED.test(config?.sharedSecret || '')) return json(503, { allowed: false });
  let url;
  try { url = new URL(request.url); } catch { return json(403, { allowed: false }); }
  if (url.origin !== DEV_ORIGIN || url.pathname !== BROKER_PATH ||
      url.search || url.hash) return json(403, { allowed: false });
  const supplied = request.headers.get('x-score-edge-secret');
  if (!SHARED.test(supplied || '') || !opaqueEqual(supplied, config.sharedSecret)) {
    return json(403, { allowed: false });
  }
  if (!(request.headers.get('content-type') || '').startsWith('application/json') ||
      Number(request.headers.get('content-length') || 0) > 512) return json(415, { allowed: false });
  // Bound streamed bodies by actual UTF-8 bytes, even if Content-Length is
  // absent or incorrect. Never buffer an unbounded unauthenticated payload.
  let data;
  try {
    const reader = request.body?.getReader();
    if (!reader) return json(400, { allowed: false });
    const decoder = new TextDecoder('utf-8', { fatal: true });
    let body = '';
    let byteCount = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      byteCount += value.byteLength;
      if (byteCount > 512) {
        await reader.cancel().catch(() => {});
        return json(400, { allowed: false });
      }
      body += decoder.decode(value, { stream: true });
    }
    body += decoder.decode();
    data = JSON.parse(body);
  } catch { return json(400, { allowed: false }); }
  if (!data || typeof data !== 'object' || Array.isArray(data) ||
      !['redeem', 'validate'].includes(data.action) ||
      Object.keys(data).some(key => !['action', 'ticket', 'token'].includes(key))) {
    return json(400, { allowed: false });
  }
  const dbEnv = { SCORE_PREVIEW_SUPABASE_SECRET_KEY: config.supabaseSecretKey };
  try {
    if (data.action === 'redeem') {
      if (!OPAQUE.test(data.ticket || '') || data.token !== undefined) {
        return json(400, { allowed: false });
      }
      const granted = await redeemScoreDevTicket(data.ticket, dbEnv, fetchImpl);
      return granted ? json(200, granted) : json(403, { allowed: false });
    }
    if (!OPAQUE.test(data.token || '') || data.ticket !== undefined) {
      return json(400, { allowed: false });
    }
    const allowed = await scoreDevSessionAllowed(data.token, dbEnv, fetchImpl);
    return json(allowed ? 200 : 403, { allowed });
  } catch {
    // No raw provider error, account ID, bearer token or key in responses.
    return json(503, { allowed: false });
  }
}
