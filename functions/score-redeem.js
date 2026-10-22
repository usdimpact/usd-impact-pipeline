// Cloudflare Pages ticket redemption. Browser navigates via POST form so the
// single-use ticket is not placed in URL, referrer or browser history.
// Disabled until private Vercel endpoint and database migrations are verified.
import { scoreSessionCookie } from '../security/score-session-cookie.mjs';
import { scoreBackendEndpoint } from '../security/score-backend-endpoints.mjs';

export async function onRequestPost({ request, env }) {
  const headers = { 'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer' };
  if (env?.SCORE_EDGE_REDEMPTION_ENABLED !== 'true' ||
      !env?.SCORE_BACKEND_URL || !env?.SCORE_EDGE_SHARED_SECRET) {
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
  const contentType = request.headers.get('content-type') || '';
  if (!contentType.startsWith('application/x-www-form-urlencoded') ||
      Number(request.headers.get('content-length') || 0) > 2048) {
    return new Response('Invalid handoff', { status: 400, headers });
  }
  let ticket;
  try {
    const body = await request.text();
    if (body.length > 2048) return new Response('Invalid handoff', { status: 400, headers });
    ticket = new URLSearchParams(body).get('ticket');
  } catch {
    return new Response('Invalid handoff', { status: 400, headers });
  }
  if (!/^[A-Za-z0-9_-]{43}$/.test(ticket || '')) {
    return new Response('Invalid ticket', { status: 400, headers });
  }
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
