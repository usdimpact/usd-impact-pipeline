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
function unavailable() {
  return new Response('Score unavailable', {
    status: 503,
    headers: { 'Cache-Control': 'private, no-store', 'Referrer-Policy': 'no-referrer' },
  });
}
function productionWorkerRequest(request) {
  const source = new URL(request.url);
  const target = new URL(source.pathname + source.search, 'https://score.usd-impact.com');
  return new Request(target, request);
}
async function delegateToProductionWorker(request, env, rewriteOrigin = false) {
  if (!env?.SCORE_PRODUCTION_WORKER ||
      typeof env.SCORE_PRODUCTION_WORKER.fetch !== 'function') return unavailable();
  try {
    return await env.SCORE_PRODUCTION_WORKER.fetch(
      rewriteOrigin ? productionWorkerRequest(request) : request,
    );
  } catch {
    return unavailable();
  }
}
export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  if (!HOSTS.has(url.hostname) && !url.hostname.endsWith('.usd-impact-pipeline.pages.dev')) return deny();

  // Production custom-domain traffic is delegated to a private Worker through a
  // Pages Service binding. This avoids a Workers Route, which requires the apex
  // to be an active Cloudflare DNS zone. Missing/failed bindings fail closed.
  if (url.hostname === 'score.usd-impact.com') {
    return delegateToProductionWorker(request, env);
  }

  // Isolated Production-data QA may exercise the exact Production Worker from
  // one explicitly pinned Pages Preview. The Worker sees the canonical origin;
  // arbitrary Preview hosts cannot opt themselves into this path.
  if (env?.SCORE_PRODUCTION_SERVICE_PREVIEW_ENABLED === 'true') {
    const previewHost = env?.SCORE_PREVIEW_REDEMPTION_HOST;
    if (typeof previewHost !== 'string' ||
        !/^[a-z0-9-]+\.usd-impact-pipeline\.pages\.dev$/.test(previewHost) ||
        url.hostname !== previewHost) return deny();
    return delegateToProductionWorker(request, env, true);
  }

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
