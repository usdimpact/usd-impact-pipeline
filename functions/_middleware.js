// Cloudflare Pages Functions Score perimeter. Private validation is required
// on EVERY premium request. No client-controlled identity or access claims.
import { readScoreSessionCookie } from '../security/score-session-cookie.mjs';
import { scoreBackendEndpoint } from '../security/score-backend-endpoints.mjs';
import { scoreDevBrokerPreviewEnabled } from '../security/score-preview-host-policy.mjs';
import { scoreBrokerSessionAllowed } from '../security/score-preview-broker-client.mjs';
import { isPublicScorePath } from '../security/score-public-paths.mjs';

const HOSTS = new Set(['score.usd-impact.com', 'usd-impact-pipeline.pages.dev']);

// Deliberately static denial page: no account IDs, tokens, query parameters,
// request-derived HTML, JavaScript, or redirects. A denied request remains 403.
const DENIAL_PAGE = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow">
<title>Research Membership required | USD Impact</title></head>
<body><main><h1>Research Membership required</h1>
<p>The Weekly Score dashboard requires an active Research Membership.</p>
<p><a href="https://www.usd-impact.com/score/">Continue at USD Impact to verify membership</a></p>
</main></body></html>`;

function deny() {
  return new Response(DENIAL_PAGE, {
    status: 403,
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'private, no-store',
      'X-Content-Type-Options': 'nosniff',
      'X-Robots-Tag': 'noindex, nofollow',
      'Referrer-Policy': 'no-referrer',
      'Content-Security-Policy': "default-src 'none'; base-uri 'none'; object-src 'none'; form-action 'none'",
    },
  });
}
export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  if (!HOSTS.has(url.hostname) && !url.hostname.endsWith('.usd-impact-pipeline.pages.dev')) return deny();
  if (url.pathname === '/score-redeem' && request.method === 'POST') return context.next();
  if (!['GET', 'HEAD'].includes(request.method)) {
    return new Response('Method Not Allowed', { status: 405, headers: { Allow: 'GET, HEAD' } });
  }
  if (isPublicScorePath(url.pathname)) return context.next();

  if (env?.SCORE_EDGE_GATE_ENABLED !== 'true') return deny();
  const token = readScoreSessionCookie(request.headers.get('cookie'));
  if (!token) return deny();
  if (env?.SCORE_DEV_BROKER_ENABLED === 'true') {
    // This route can be activated only on the exact isolated Pages Preview.
    // An isolated Development Edge broker avoids Vercel Deployment Protection
    // without weakening or bypassing it.
    if (!scoreDevBrokerPreviewEnabled(request, env)) return deny();
    try {
      if (await scoreBrokerSessionAllowed(token, env) !== true) return deny();
    } catch { return deny(); }
  } else {
    const endpoint = scoreBackendEndpoint(env?.SCORE_VALIDATION_BACKEND_URL, '/api/score-edge-validate');
    if (!endpoint || typeof env?.SCORE_EDGE_SHARED_SECRET !== 'string' ||
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
  }

  const response = await context.next();
  const headers = new Headers(response.headers);
  headers.set('Cache-Control', 'private, no-store');
  headers.set('X-Robots-Tag', 'noindex, nofollow');
  return new Response(response.body, {
    status: response.status, statusText: response.statusText, headers,
  });
}
