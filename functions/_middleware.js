// Cloudflare Pages Functions Score perimeter. Private validation is required
// on EVERY premium request. No client-controlled identity or access claims.
import { readScoreSessionCookie } from '../security/score-session-cookie.mjs';

const PUBLIC_PATHS = new Set(['/member-required.html', '/robots.txt', '/favicon.ico']);
const HOSTS = new Set(['score.usd-impact.com', 'usd-impact-pipeline.pages.dev']);

function deny() {
  return new Response('Research Membership required', {
    status: 403,
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'private, no-store',
      'X-Content-Type-Options': 'nosniff',
      'X-Robots-Tag': 'noindex, nofollow',
    },
  });
}
function backendUrl(value) {
  try {
    const url = new URL(value);
    if (url.protocol !== 'https:' || url.username || url.password ||
        url.search || url.hash || url.pathname !== '/api/score-edge-validate') return null;
    return url.href;
  } catch { return null; }
}
export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  if (!HOSTS.has(url.hostname) && !url.hostname.endsWith('.usd-impact-pipeline.pages.dev')) return deny();
  if (url.pathname === '/score-redeem' && request.method === 'POST') return context.next();
  if (!['GET', 'HEAD'].includes(request.method)) {
    return new Response('Method Not Allowed', { status: 405, headers: { Allow: 'GET, HEAD' } });
  }
  if (PUBLIC_PATHS.has(url.pathname)) return context.next();

  if (env?.SCORE_EDGE_GATE_ENABLED !== 'true') return deny();
  const token = readScoreSessionCookie(request.headers.get('cookie'));
  const endpoint = backendUrl(env?.SCORE_VALIDATION_BACKEND_URL);
  if (!token || !endpoint || typeof env?.SCORE_EDGE_SHARED_SECRET !== 'string' ||
      env.SCORE_EDGE_SHARED_SECRET.length < 32) return deny();
  try {
    const result = await fetch(endpoint, {
      method: 'POST', redirect: 'manual',
      headers: { 'Content-Type': 'application/json',
        'X-Score-Edge-Secret': env.SCORE_EDGE_SHARED_SECRET },
      body: JSON.stringify({ token }),
    });
    if (result.status !== 200) return deny();
    const data = await result.json();
    if (data?.allowed !== true) return deny();
  } catch { return deny(); }

  const response = await context.next();
  const headers = new Headers(response.headers);
  headers.set('Cache-Control', 'private, no-store');
  headers.set('X-Robots-Tag', 'noindex, nofollow');
  return new Response(response.body, {
    status: response.status, statusText: response.statusText, headers,
  });
}
