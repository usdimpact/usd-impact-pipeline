// Development Supabase Edge broker: server-side fixed operation gateway only.
// Authentication is independent of the Supabase service-role API key.
import { redeemScoreDevTicket, scoreDevSessionAllowed } from './score-preview-dev-rpc.mjs';
const DEV_ORIGIN = 'https://ycstrcvshdluovtuasjc.supabase.co';
const DEV_HOST = 'ycstrcvshdluovtuasjc.supabase.co';
const EDGE_RUNTIME_HOST = 'edge-runtime.supabase.com';
const PUBLIC_BROKER_PATH = '/functions/v1/score-preview-broker';
const RUNTIME_BROKER_PATH = '/score-preview-broker';
const OPAQUE = /^[A-Za-z0-9_-]{43}$/;
const KEY = /^sb_secret_[A-Za-z0-9_-]{16,}$/;
const SHARED = /^[A-Za-z0-9_-]{43,128}$/;
const HEADERS = {
  'Cache-Control': 'private, no-store',
  'Content-Type': 'application/json; charset=utf-8',
  'Referrer-Policy': 'no-referrer',
  'X-Content-Type-Options': 'nosniff',
};
const json = (status, data, extra = {}) => Response.json(data, { status, headers: { ...HEADERS, ...extra } });
function diagnostic(config, stage, status = 403, extra = {}) {
  const enabled = config?.diagnostics === 'true';
  if (enabled) console.info('score-preview-broker-stage', stage);
  const stageHeaders = enabled ? { 'X-Score-Preview-Broker-Stage': stage } : {};
  const data = enabled ? { allowed: false, stage } : { allowed: false };
  return json(status, data, { ...extra, ...stageHeaders });
}
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
  try { url = new URL(request.url); } catch { return diagnostic(config, 'broker-url-parse'); }
  const publicUrl = url.origin === DEV_ORIGIN;
  const runtimeHost = request.headers.get('host');
  const forwardedHost = request.headers.get('x-forwarded-host');
  const gatewayUrl =
    (runtimeHost === EDGE_RUNTIME_HOST || forwardedHost === EDGE_RUNTIME_HOST) &&
    request.headers.get('x-forwarded-proto') === 'https';
  // Supabase Edge may rewrite request.url to an internal runtime origin after
  // the public gateway. Accept that form only when the platform-preserved Host
  // and forwarded protocol still identify this exact Development project.
  if (!publicUrl && !gatewayUrl) return diagnostic(config, 'broker-origin');
  const allowedPath =
    (publicUrl && (url.pathname === PUBLIC_BROKER_PATH || url.pathname === RUNTIME_BROKER_PATH)) ||
    (gatewayUrl && url.pathname === RUNTIME_BROKER_PATH);
  if (!allowedPath) return diagnostic(config, 'broker-path');
  if (url.search || url.hash) return diagnostic(config, 'broker-query');
  const supplied = request.headers.get('x-score-edge-secret');
  if (!SHARED.test(supplied || '') || !opaqueEqual(supplied, config.sharedSecret)) {
    return diagnostic(config, 'broker-shared-secret');
  }
  // Reject ambiguous media types and malformed lengths before parsing.
  // A missing length is permitted only because streamed bytes are capped below.
  const mediaType = (request.headers.get('content-type') || '').trim();
  if (!/^application\/json(?:\s*;\s*charset=utf-8)?$/i.test(mediaType)) {
    return diagnostic(config, 'broker-media-type', 415);
  }
  const announcedLength = request.headers.get('content-length');
  if (announcedLength !== null &&
      (!/^\d+$/.test(announcedLength) || Number(announcedLength) > 512)) {
    return diagnostic(config, 'broker-length', 400);
  }
  // Bound streamed bodies by actual UTF-8 bytes, even if Content-Length is
  // absent or incorrect. Never buffer an unbounded unauthenticated payload.
  let data;
  try {
    const reader = request.body?.getReader();
    if (!reader) return diagnostic(config, 'broker-body', 400);
    const decoder = new TextDecoder('utf-8', { fatal: true });
    let body = '';
    let byteCount = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      byteCount += value.byteLength;
      if (byteCount > 512) {
        await reader.cancel().catch(() => {});
        return diagnostic(config, 'broker-body', 400);
      }
      body += decoder.decode(value, { stream: true });
    }
    body += decoder.decode();
    data = JSON.parse(body);
  } catch { return diagnostic(config, 'broker-body', 400); }
  if (!data || typeof data !== 'object' || Array.isArray(data) ||
      !['redeem', 'validate'].includes(data.action) ||
      Object.keys(data).some(key => !['action', 'ticket', 'token'].includes(key))) {
    return diagnostic(config, 'broker-schema', 400);
  }
  // Requests from the public Supabase URL are authenticated and schema-checked
  // before touching the global service-role rate budget. Missing limiter fails
  // closed, including when the underlying Development database is unavailable.
  if (typeof config?.rateBudget !== 'function') return diagnostic(config, 'broker-budget-config', 503);
  try {
    const permitted = await config.rateBudget(data.action);
    if (permitted !== true) return diagnostic(config, 'broker-budget-limit', 429, { 'Retry-After': '60' });
  } catch {
    return diagnostic(config, 'broker-budget-error', 503);
  }
  const dbEnv = { SCORE_PREVIEW_SUPABASE_SECRET_KEY: config.supabaseSecretKey };
  try {
    if (data.action === 'redeem') {
      if (!OPAQUE.test(data.ticket || '') || data.token !== undefined) {
        return json(400, { allowed: false });
      }
      const granted = await redeemScoreDevTicket(data.ticket, dbEnv, fetchImpl);
      return granted ? json(200, granted) : diagnostic(config, 'broker-redeem-denied');
    }
    if (!OPAQUE.test(data.token || '') || data.ticket !== undefined) {
      return json(400, { allowed: false });
    }
    const allowed = await scoreDevSessionAllowed(data.token, dbEnv, fetchImpl);
    return allowed ? json(200, { allowed }) : diagnostic(config, 'broker-validate-denied');
  } catch {
    // No raw provider error, account ID, bearer token or key in responses.
    return diagnostic(config, 'broker-rpc-error', 503);
  }
}
