// Cloudflare Pages Functions Score perimeter. Private validation is required
// on EVERY premium request. No client-controlled identity or access claims.
import { readScoreSessionCookie } from '../security/score-session-cookie.mjs';

// Only artifacts already published as public methodology/reproducibility data
// bypass the membership gate. Never open a directory prefix: archive HTML,
// dashboard pages and future unpublished files must still require a session.
const PUBLIC_PATHS = new Set([
  '/member-required', '/member-required.html', '/robots.txt', '/favicon.ico',
  '/data/backtest_results.json',
  '/data/score_repro_bundle_latest.json',
  '/data/score_v2_data_semantics.json',
  '/data/score_v2_data_semantics.schema.json',
  '/data/score_v2_methodology.json',
  '/data/score_v2_methodology.schema.json',
  '/data/usd_impact_score_v2.csv',
  '/data/usd_impact_score_v2.json',
  '/data/weekly_input_latest.json',
  '/data/research/independent_replication_protocol.json',
  '/data/research/score_v2_point_in_time_latest.json',
  '/data/research/score_v2_robustness_latest.json',
  '/data/research/score_v2_vintage_comparison_latest.csv',
  '/data/research/score_v2_vintage_comparison_latest.json',
  '/data/research/score_v2_vintage_comparison_latest.html',
  '/data/research/score_v2_vintage_comparison_latest', // Pages clean URL
]);
const PUBLIC_DATED_ARCHIVE_RE = /^\/archive\/\d{4}-\d{2}-\d{2}\/(?:score|weekly_input|repro_bundle)\.json$/;
function isPublicPath(pathname) {
  return PUBLIC_PATHS.has(pathname) || PUBLIC_DATED_ARCHIVE_RE.test(pathname);
}
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
  if (isPublicPath(url.pathname)) return context.next();

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
