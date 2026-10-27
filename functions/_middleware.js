// Cloudflare Pages is public delivery only.
// Premium Score HTML is authorized and served by usd-impact.com (Vercel + Supabase).
// This perimeter deliberately has no session, ticket, entitlement, secret, or backend logic.
import { isPublicScorePath } from '../security/score-public-paths.mjs';

const EXACT_HOSTS = new Set(['score.usd-impact.com', 'usd-impact-pipeline.pages.dev']);
const PAGES_PREVIEW_RE = /^[a-z0-9-]+\.usd-impact-pipeline\.pages\.dev$/;

const DENIAL_PAGE = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow">
<title>Research Membership required | USD Impact</title></head>
<body><main><h1>Research Membership required</h1>
<p>The Weekly Score dashboard requires an active Research Membership.</p>
<p><a href="https://www.usd-impact.com/score/">Continue at USD Impact to verify membership</a></p>
</main></body></html>`;

function safeHeaders(contentType = 'text/plain; charset=utf-8') {
  return {
    'Content-Type': contentType,
    'Cache-Control': 'private, no-store',
    'X-Content-Type-Options': 'nosniff',
    'X-Robots-Tag': 'noindex, nofollow',
    'Referrer-Policy': 'no-referrer',
    'Content-Security-Policy': "default-src 'none'; base-uri 'none'; object-src 'none'; form-action 'none'; frame-ancestors 'none'",
  };
}

function deny() {
  return new Response(DENIAL_PAGE, {
    status: 403,
    headers: safeHeaders('text/html; charset=utf-8'),
  });
}

function gone() {
  return new Response('Score redemption moved to usd-impact.com', {
    status: 410,
    headers: safeHeaders(),
  });
}

function allowedHost(hostname) {
  return EXACT_HOSTS.has(hostname) || PAGES_PREVIEW_RE.test(hostname);
}

export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);

  if (!allowedHost(url.hostname)) return deny();

  // Cloudflare no longer accepts, validates, or forwards Score tickets.
  if (url.pathname === '/score-redeem') return gone();

  if (!['GET', 'HEAD'].includes(request.method)) {
    return new Response('Method Not Allowed', {
      status: 405,
      headers: { ...safeHeaders(), Allow: 'GET, HEAD' },
    });
  }

  if (!isPublicScorePath(url.pathname)) return deny();
  return context.next();
}
