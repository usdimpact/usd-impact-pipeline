// Cloudflare Pages ticket redemption. Browser navigates via POST form so the
// single-use ticket is not placed in URL, referrer or browser history.
// Development Edge broker mode remains disabled until isolated Preview acceptance.
import { scoreSessionCookie } from '../security/score-session-cookie.mjs';
import { scoreBackendEndpoint } from '../security/score-backend-endpoints.mjs';
import { SCORE_DIRECT_WEBSITE_ORIGIN, scoreDevBrokerPreviewEnabled } from '../security/score-preview-dev-rpc.mjs';
import { redeemScoreBrokerTicket } from '../security/score-preview-broker-client.mjs';

// A hostile client can omit or falsify Content-Length. Cap the streamed bytes
// before building a form body, rather than buffering an unbounded Request.text().
const MAX_HANDOFF_BYTES = 2048;
const OPAQUE_TICKET = /^[A-Za-z0-9_-]{43}$/;
async function parseBoundedTicket(request) {
  const media = (request.headers.get('content-type') || '').split(';', 1)[0].trim().toLowerCase();
  if (media !== 'application/x-www-form-urlencoded') return null;
  const advertised = request.headers.get('content-length');
  if (advertised !== null &&
      (!/^\\d+$/.test(advertised) || Number(advertised) > MAX_HANDOFF_BYTES)) return null;
  const reader = request.body?.getReader();
  if (!reader) return null;
  let bytes = 0;
  const chunks = [];
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > MAX_HANDOFF_BYTES) {
        await reader.cancel().catch(() => {});
        return null;
      }
      chunks.push(value);
    }
    const payload = new Uint8Array(bytes);
    let offset = 0;
    for (const chunk of chunks) {
      payload.set(chunk, offset);
      offset += chunk.byteLength;
    }
    const body = new TextDecoder('utf-8', { fatal: true }).decode(payload);
    const fields = new URLSearchParams(body);
    if ([...fields.keys()].length !== 1 || !fields.has('ticket')) return null;
    const ticket = fields.get('ticket');
    return OPAQUE_TICKET.test(ticket || '') ? ticket : null;
  } catch {
    return null;
  }
}

export async function onRequestPost({ request, env }) {
  const headers = { 'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer' };
  const useDevBroker = env?.SCORE_DEV_BROKER_ENABLED === 'true';
  if (env?.SCORE_EDGE_REDEMPTION_ENABLED !== 'true' ||
      (!useDevBroker && (!env?.SCORE_BACKEND_URL || !env?.SCORE_EDGE_SHARED_SECRET))) {
    return new Response('Score handoff unavailable', { status: 503, headers });
  }
  const origin = new URL(request.url);
  // Preview host must be explicitly pinned; never accept arbitrary Pages subdomains.
  const previewHost = env?.SCORE_PREVIEW_REDEMPTION_HOST;
  const previewAllowed = typeof previewHost === 'string' &&
    /^[a-z0-9-]+\.usd-impact-pipeline\.pages\.dev$/.test(previewHost) &&
    origin.hostname === previewHost;
  if (origin.hostname !== 'score.usd-impact.com' && !previewAllowed) {
    return new Response('Invalid Score host', { status: 403, headers });
  }
  const ticket = await parseBoundedTicket(request);
  if (!ticket) return new Response('Invalid handoff', { status: 400, headers });
  if (useDevBroker) {
    // Preview handoff is explicitly pinned to the Vercel Preview origin.
    // Cross-origin ticket injection (login CSRF) must fail closed.
    if (!scoreDevBrokerPreviewEnabled(request, env) ||
        request.headers.get('origin') !== SCORE_DIRECT_WEBSITE_ORIGIN) {
      return new Response('Invalid Preview handoff origin', { status: 403, headers });
    }
    try {
      const payload = await redeemScoreBrokerTicket(ticket, env);
      if (!payload) return new Response('Score membership required', { status: 403, headers });
      const cookie = scoreSessionCookie(payload.token, payload.expiresAtMs);
      return new Response(null, {
        status: 303,
        headers: { ...headers, Location: payload.path, 'Set-Cookie': cookie },
      });
    } catch {
      return new Response('Score handoff unavailable', { status: 503, headers });
    }
  }

  // Legacy server-to-server mode is retained disabled by default, not used by
  // the isolated Development Edge broker pathway.
  // Never forward the Cloudflare shared secret to arbitrary HTTPS endpoints.
  const backend = scoreBackendEndpoint(env.SCORE_BACKEND_URL, '/api/score-edge-redeem');
  if (!backend) {
    return new Response('Score handoff unavailable', { status: 503, headers });
  }
  try {
    const result = await fetch(backend, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json',
        'X-Score-Edge-Secret': env.SCORE_EDGE_SHARED_SECRET },
      body: JSON.stringify({ ticket }),
      redirect: 'manual',
    });
    if (!result.ok) return new Response('Score membership required', { status: 403, headers });
    const payload = await result.json();
    if (payload.allowed !== true ||
        !['/en/', '/es/', '/archive/en/', '/archive/es/'].includes(payload.path)) {
      return new Response('Score handoff unavailable', { status: 503, headers });
    }
    const cookie = scoreSessionCookie(payload.token, payload.expiresAtMs);
    return new Response(null, {
      status: 303,
      headers: { ...headers, Location: payload.path, 'Set-Cookie': cookie },
    });
  } catch {
    return new Response('Score handoff unavailable', { status: 503, headers });
  }
}
