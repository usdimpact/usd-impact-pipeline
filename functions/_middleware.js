// Draft-only: protected resource gate. Do not enable in production until
// storage, membership lookup, ticket redemption and host coverage are tested.
import { authorizeScoreEdgeRequest } from '../security/score-edge-authorization.mjs';

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
export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  if (!HOSTS.has(url.hostname) && !url.hostname.endsWith('.usd-impact-pipeline.pages.dev')) return deny();
  if (!['GET', 'HEAD'].includes(request.method)) {
    return new Response('Method Not Allowed', { status: 405, headers: { Allow: 'GET, HEAD' } });
  }
  if (PUBLIC_PATHS.has(url.pathname)) return context.next();

  // The route remains denied without an explicit, reviewed server-side
  // implementation. The flag alone cannot grant access.
  if (env?.SCORE_EDGE_GATE_ENABLED !== 'true') return deny();
  const dependencies = context.data?.scoreAuthorization;
  if (!dependencies || typeof dependencies.sessions?.lookup !== 'function' ||
      typeof dependencies.membership?.isActive !== 'function') return deny();
  const decision = await authorizeScoreEdgeRequest(request, dependencies);
  if (!decision.allowed) return deny();
  const response = await context.next();
  const headers = new Headers(response.headers);
  headers.set('Cache-Control', 'private, no-store');
  headers.set('X-Robots-Tag', 'noindex, nofollow');
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}
