// Production Score Worker candidate. Draft-only until an explicit release GO.
// No routes/custom domains are declared in source; all activation flags default OFF.
import { readScoreSessionCookie, scoreSessionCookie } from '../../security/score-session-cookie.mjs';
import { redeemScoreEdgeTicket, scoreEdgeSessionAllowed } from '../../security/score-production-bridge-client.mjs';
import { isPublicScorePath } from '../../security/score-public-paths.mjs';
import { parseBoundedScoreTicket } from '../../security/score-ticket-form.mjs';

export const SCORE_PRODUCTION_ORIGIN = 'https://score.usd-impact.com';
export const SCORE_PRODUCTION_WEBSITE_ORIGIN = 'https://www.usd-impact.com';

const SECURITY_HEADERS = {
  'Cache-Control': 'private, no-store',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  'X-Permitted-Cross-Domain-Policies': 'none',
};
const PUBLIC_CSP =
  "default-src 'none'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; " +
  "script-src 'self' 'sha256-IGL29GGZMxoGb4lM3VdzVRyVvzRgYYWet+kIdn3Xjik='; " +
  "script-src-attr 'none'; connect-src 'none'; font-src 'none'; media-src 'none'; " +
  "object-src 'none'; frame-src 'none'; worker-src 'none'; manifest-src 'none'; " +
  "base-uri 'none'; form-action 'none'; frame-ancestors 'none'; upgrade-insecure-requests";
const DENIAL_HTML =
  '<!doctype html><html lang="en"><head><meta charset="utf-8">' +
  '<meta name="robots" content="noindex,nofollow"><title>Research Membership required</title>' +
  '</head><body><main><h1>Research Membership required</h1>' +
  '<p>The Weekly Score dashboard requires an active Research Membership.</p>' +
  '<p><a href="https://www.usd-impact.com/score/">Verify membership</a></p></main></body></html>';

function response(status, body, additional = {}) {
  return new Response(body, { status, headers: { ...SECURITY_HEADERS, ...additional } });
}
function denied() {
  return response(403, DENIAL_HTML, {
    'Content-Type': 'text/html; charset=utf-8',
    'Content-Security-Policy': "default-src 'none'; base-uri 'none'; object-src 'none'; form-action 'none'; frame-ancestors 'none'",
  });
}
function unavailable() {
  return response(503, 'Score unavailable');
}
function throttled() {
  return response(429, 'Score throttled', { 'Retry-After': '60' });
}
function exactProductionOrigin(request, env) {
  if (env?.SCORE_WORKER_ENABLED !== 'true' ||
      env?.SCORE_WORKER_ORIGIN !== SCORE_PRODUCTION_ORIGIN ||
      env?.SCORE_WEBSITE_ORIGIN !== SCORE_PRODUCTION_WEBSITE_ORIGIN) return false;
  try {
    const actual = new URL(request.url);
    return actual.origin === SCORE_PRODUCTION_ORIGIN && !actual.search && !actual.hash;
  } catch {
    return false;
  }
}
async function rateCheck(binding, key) {
  if (!binding || typeof binding.limit !== 'function') return null;
  try {
    const result = await binding.limit({ key });
    return result?.success === true;
  } catch {
    return null;
  }
}
async function hashKey(value, scope) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return scope + ':' + Array.from(new Uint8Array(digest),
    x => x.toString(16).padStart(2, '0')).join('');
}
async function redeemActor(request) {
  const ip = request.headers.get('cf-connecting-ip') || '';
  const actor = /^[0-9a-fA-F:.]{2,64}$/.test(ip) ? ip.toLowerCase() : 'unidentified';
  return hashKey(actor, 'redeem');
}
async function validateActor(token) {
  return hashKey(token, 'validate');
}
async function asset(request, env, restricted) {
  if (typeof env?.ASSETS?.fetch !== 'function') return unavailable();
  try {
    const result = await env.ASSETS.fetch(request);
    const headers = new Headers(result.headers);
    for (const [key, value] of Object.entries(SECURITY_HEADERS)) headers.set(key, value);
    headers.set('Content-Security-Policy', PUBLIC_CSP);
    if (restricted) headers.set('X-Robots-Tag', 'noindex, nofollow');
    else headers.set('Cache-Control', 'public, max-age=300');
    return new Response(result.body, {
      status: result.status,
      statusText: result.statusText,
      headers,
    });
  } catch {
    return unavailable();
  }
}
async function redeem(request, env, dependencies) {
  if (env?.SCORE_EDGE_REDEMPTION_ENABLED !== 'true') return unavailable();
  if (request.headers.get('origin') !== SCORE_PRODUCTION_WEBSITE_ORIGIN) return denied();

  let actor;
  try { actor = await redeemActor(request); } catch { return unavailable(); }
  const limited = await rateCheck(env.SCORE_REDEEM_LIMIT, actor);
  if (limited === null) return unavailable();
  if (!limited) return throttled();

  const ticket = await parseBoundedScoreTicket(request);
  if (!ticket) return response(400, 'Invalid Score handoff');

  const redeemTicket = dependencies.redeemScoreEdgeTicket || redeemScoreEdgeTicket;
  try {
    const payload = await redeemTicket(ticket, env);
    if (!payload) return denied();
    const cookie = scoreSessionCookie(payload.token, payload.expiresAtMs);
    return response(303, null, {
      Location: payload.path,
      'Set-Cookie': cookie,
    });
  } catch {
    return unavailable();
  }
}

export async function handleScoreWorkerProduction(request, env, dependencies = {}) {
  if (env?.SCORE_WORKER_ENABLED !== 'true') return unavailable();
  if (!exactProductionOrigin(request, env)) return denied();

  const url = new URL(request.url);
  if (url.pathname === '/score-redeem' && request.method === 'POST') {
    return redeem(request, env, dependencies);
  }
  if (!['GET', 'HEAD'].includes(request.method)) {
    return response(405, 'Method Not Allowed', { Allow: 'GET, HEAD' });
  }

  if (isPublicScorePath(url.pathname)) return asset(request, env, false);

  if (env?.SCORE_EDGE_GATE_ENABLED !== 'true') return denied();
  const token = readScoreSessionCookie(request.headers.get('cookie'));
  if (!token) return denied();

  let actor;
  try { actor = await validateActor(token); } catch { return unavailable(); }
  const limited = await rateCheck(env.SCORE_VALIDATE_LIMIT, actor);
  if (limited === null) return unavailable();
  if (!limited) return throttled();

  const validateSession = dependencies.scoreEdgeSessionAllowed || scoreEdgeSessionAllowed;
  try {
    if (await validateSession(token, env) !== true) return denied();
  } catch {
    return denied();
  }
  return asset(request, env, true);
}

export default {
  fetch(request, env) {
    return handleScoreWorkerProduction(request, env);
  },
};
