// Isolated Cloudflare Workers Preview adapter. THIS IS NOT A PRODUCTION ENTRYPOINT.
// Production and new Preview environments are configured OFF in wrangler.jsonc.
// Every static asset request runs through this script: never serve before auth.
import { readScoreSessionCookie, scoreSessionCookie } from '../../security/score-session-cookie.mjs';
import { redeemScoreBrokerTicket, scoreBrokerSessionAllowed } from '../../security/score-preview-broker-client.mjs';
import { SCORE_DIRECT_WEBSITE_ORIGIN } from '../../security/score-preview-host-policy.mjs';
import { isPublicScorePath } from '../../security/score-public-paths.mjs';
import { parseBoundedScoreTicket } from '../../security/score-ticket-form.mjs';

const SECURITY_HEADERS = {
  'Cache-Control': 'private, no-store',
  'X-Content-Type-Options': 'nosniff',
  'X-Robots-Tag': 'noindex, nofollow',
  'Referrer-Policy': 'no-referrer',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  'X-Permitted-Cross-Domain-Policies': 'none',
};
const PUBLIC_CSP =
  "default-src 'none'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; " +
  "script-src 'self' 'sha256-IGL29GGZMxoGb4lM3VdzVRyVvzRgYYWet+kIdn3Xjik='; " +
  "script-src-attr 'none'; connect-src 'none'; font-src 'none'; media-src 'none'; " +
  "object-src 'none'; frame-src 'none'; worker-src 'none'; manifest-src 'none'; " +
  "base-uri 'none'; form-action 'none'; " +
  "frame-ancestors https://www.usd-impact.com https://usd-impact.com " +
  SCORE_DIRECT_WEBSITE_ORIGIN + "; upgrade-insecure-requests";
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
    'Content-Security-Policy': "default-src 'none'; base-uri 'none'; object-src 'none'; form-action 'none'",
  });
}
function unavailable(stage) {
  const extra = {};
  if (/^(machine-config|machine-auth-http|machine-claims|broker-config|broker-http|unknown)$/.test(stage || '')) {
    extra['X-Score-Preview-Stage'] = stage;
  }
  return response(503, 'Score Preview unavailable', extra);
}
function throttled() {
  return response(429, 'Score Preview throttled', { 'Retry-After': '60' });
}
function exactPreviewOrigin(request, env) {
  if (env?.SCORE_WORKER_PREVIEW_ENABLED !== 'true' ||
      typeof env?.SCORE_WORKER_PREVIEW_ORIGIN !== 'string') return false;
  try {
    const actual = new URL(request.url);
    const expected = new URL(env.SCORE_WORKER_PREVIEW_ORIGIN);
    // Preview URLs only. No Pages host, arbitrary Vercel host or Production route.
    return expected.protocol === 'https:' &&
      expected.hostname.endsWith('.workers.dev') &&
      expected.hostname !== 'workers.dev' &&
      expected.pathname === '/' && !expected.port && !expected.username &&
      !expected.password && !expected.search && !expected.hash &&
      actual.origin === expected.origin && !actual.search && !actual.hash;
  } catch { return false; }
}
async function rateCheck(binding, key) {
  // A missing, errored, or misconfigured Preview binding cannot permit access.
  if (!binding || typeof binding.limit !== 'function') return null;
  try {
    const result = await binding.limit({ key });
    return result?.success === true;
  } catch { return null; }
}
async function requestActor(request, scope) {
  // Rate-limit per *source* even when attackers rotate invalid session tokens.
  // Avoid storing client IP addresses or bearer tokens as raw limiter keys.
  // CF-Connecting-IP is set by Cloudflare in the hosted Worker environment.
  const ip = request.headers.get('cf-connecting-ip') || '';
  const actor = /^[0-9a-fA-F:.]{2,64}$/.test(ip) ? ip.toLowerCase() : 'unidentified';
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(actor));
  return scope + ':' + Array.from(new Uint8Array(digest),
    x => x.toString(16).padStart(2, '0')).join('');
}
async function asset(request, env, restricted) {
  if (typeof env?.ASSETS?.fetch !== 'function') return unavailable();
  try {
    const result = await env.ASSETS.fetch(request);
    const headers = new Headers(result.headers);
    for (const [key, value] of Object.entries(SECURITY_HEADERS)) headers.set(key, value);
    headers.set('Content-Security-Policy', PUBLIC_CSP);
    if (!restricted) headers.set('Cache-Control', 'public, max-age=300');
    return new Response(result.body, {status:result.status,statusText:result.statusText,headers});
  } catch (error) {
    return unavailable(env?.SCORE_PREVIEW_DIAGNOSTICS_ENABLED === 'true' ? (error?.code || 'unknown') : null);
  }
}
async function redeem(request, env) {
  if (env?.SCORE_EDGE_REDEMPTION_ENABLED !== 'true' ||
      env?.SCORE_DEV_BROKER_ENABLED !== 'true') return unavailable();
  if (request.headers.get('origin') !== SCORE_DIRECT_WEBSITE_ORIGIN) return denied();
  const limited = await rateCheck(env.SCORE_PREVIEW_REDEEM_LIMIT, await requestActor(request, 'redeem'));
  if (limited === null) return unavailable();
  if (!limited) return throttled();
  const ticket = await parseBoundedScoreTicket(request);
  if (!ticket) return response(400, 'Invalid Score handoff');
  try {
    const payload = await redeemScoreBrokerTicket(ticket, env);
    if (!payload) return denied();
    const cookie = scoreSessionCookie(payload.token, payload.expiresAtMs);
    return response(303, null, {Location:payload.path,'Set-Cookie':cookie});
  } catch { return unavailable(); }
}
export async function handleScoreWorkerPreview(request, env) {
  if (env?.SCORE_WORKER_PREVIEW_ENABLED !== 'true') return unavailable();
  if (!exactPreviewOrigin(request, env)) return denied();
  const url = new URL(request.url);
  if (url.pathname === '/score-redeem' && request.method === 'POST') {
    return redeem(request, env);
  }
  if (!['GET', 'HEAD'].includes(request.method)) {
    return response(405, 'Method Not Allowed', {Allow:'GET, HEAD'});
  }
  if (isPublicScorePath(url.pathname)) return asset(request, env, false);

  if (env?.SCORE_EDGE_GATE_ENABLED !== 'true' ||
      env?.SCORE_DEV_BROKER_ENABLED !== 'true') return denied();
  const token = readScoreSessionCookie(request.headers.get('cookie'));
  if (!token) return denied();

  let key;
  try { key = await requestActor(request, 'validate'); } catch { return unavailable(); }
  const limited = await rateCheck(env.SCORE_PREVIEW_VALIDATE_LIMIT, key);
  if (limited === null) return unavailable();
  if (!limited) return throttled();
  try {
    if (await scoreBrokerSessionAllowed(token, env) !== true) return denied();
  } catch (error) {
    if (env?.SCORE_PREVIEW_DIAGNOSTICS_ENABLED === 'true') {
      return unavailable(error?.code || 'unknown');
    }
    return denied();
  }
  return asset(request, env, true);
}

export default {
  fetch(request, env) {
    return handleScoreWorkerPreview(request, env);
  },
};
