// Cloudflare Pages Functions security perimeter for Score HTML.
// PREVIEW-ONLY until the ticket redemption, session validation and entitlement
// refresh are implemented and verified. Existing _redirects stay in place.
// This function deliberately FAILS CLOSED for all HTML and unknown routes.
const PUBLIC_PATHS = new Set(['/member-required.html', '/robots.txt', '/favicon.ico']);
const PROTECTED_EXTENSIONS = /\.(?:html?|json|xml|txt|pdf|csv)$/i;

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
  if (!['GET', 'HEAD'].includes(request.method)) {
    return new Response('Method Not Allowed', { status: 405, headers: { Allow: 'GET, HEAD' } });
  }
  // Never trust a request Host or forwarded header for entitlement.
  if (PUBLIC_PATHS.has(url.pathname)) return context.next();

  // No deployment flag can unlock HTML without a server-side verified session.
  // This flag is informational only and cannot authorize a request.
  void env?.SCORE_HANDOFF_ISSUANCE_ENABLED;
  if (url.pathname.endsWith('/') || PROTECTED_EXTENSIONS.test(url.pathname) ||
      !url.pathname.includes('.')) {
    return deny();
  }

  // Static assets are not proof of membership. The deployment must audit
  // whether JS/CSS/images themselves contain paid research before allowing.
  // Default deny until an explicit audited asset manifest is implemented.
  return deny();
}
