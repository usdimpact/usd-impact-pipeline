import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {
  SCORE_PRODUCTION_ORIGIN,
  SCORE_PRODUCTION_WEBSITE_ORIGIN,
  handleScoreWorkerProduction,
} from '../workers/score-production/index.mjs';

const secret = 's'.repeat(64);
const ticket = 't'.repeat(43);
const token = 'k'.repeat(43);

function limiter(success = true) {
  return { limit: async () => ({ success }) };
}
function env(overrides = {}) {
  return {
    SCORE_WORKER_ENABLED: 'true',
    SCORE_EDGE_GATE_ENABLED: 'true',
    SCORE_EDGE_REDEMPTION_ENABLED: 'true',
    SCORE_WORKER_ORIGIN: SCORE_PRODUCTION_ORIGIN,
    SCORE_WEBSITE_ORIGIN: SCORE_PRODUCTION_WEBSITE_ORIGIN,
    SCORE_EDGE_BRIDGE_ORIGIN: SCORE_PRODUCTION_WEBSITE_ORIGIN,
    SCORE_EDGE_SHARED_SECRET: secret,
    SCORE_REDEEM_LIMIT: limiter(true),
    SCORE_VALIDATE_LIMIT: limiter(true),
    ASSETS: {
      fetch: async (request) => new Response('asset:' + new URL(request.url).pathname, {
        status: 200,
        headers: { 'Content-Type': 'text/plain' },
      }),
    },
    ...overrides,
  };
}
function request(path = '/en/', options = {}) {
  return new Request(SCORE_PRODUCTION_ORIGIN + path, options);
}
function formRequest({ origin = SCORE_PRODUCTION_WEBSITE_ORIGIN, value = ticket } = {}) {
  return request('/score-redeem', {
    method: 'POST',
    headers: {
      Origin: origin,
      'Content-Type': 'application/x-www-form-urlencoded',
      'CF-Connecting-IP': '203.0.113.10',
    },
    body: new URLSearchParams({ ticket: value }),
  });
}

test('Production Worker is disabled by default', async () => {
  const result = await handleScoreWorkerProduction(request('/en/'), env({ SCORE_WORKER_ENABLED: 'false' }));
  assert.equal(result.status, 503);
  assert.equal(await result.text(), 'Score unavailable');
});

test('exact score.usd-impact.com origin is mandatory', async () => {
  const bad = new Request('https://other.example/en/');
  assert.equal((await handleScoreWorkerProduction(bad, env())).status, 403);
  assert.equal((await handleScoreWorkerProduction(
    request('/en/?debug=1'), env()
  )).status, 403);
});

test('public methodology allowlist bypasses membership but not the master kill switch', async () => {
  let validations = 0;
  const dependencies = { scoreEdgeSessionAllowed: async () => { validations++; return true; } };
  const result = await handleScoreWorkerProduction(
    request('/data/score_v2_methodology.json'), env(), dependencies,
  );
  assert.equal(result.status, 200);
  assert.equal(validations, 0);
  assert.match(result.headers.get('cache-control'), /^public/);

  const disabled = await handleScoreWorkerProduction(
    request('/data/score_v2_methodology.json'), env({ SCORE_WORKER_ENABLED: 'false' }), dependencies,
  );
  assert.equal(disabled.status, 503);
});

test('premium and archive content deny without a Score session', async () => {
  for (const path of ['/en/', '/archive/en/', '/index.html']) {
    const result = await handleScoreWorkerProduction(request(path), env());
    assert.equal(result.status, 403, path);
  }
});

test('redeem requires flag, exact website Origin, limiter and valid ticket', async () => {
  assert.equal((await handleScoreWorkerProduction(
    formRequest(), env({ SCORE_EDGE_REDEMPTION_ENABLED: 'false' })
  )).status, 503);

  assert.equal((await handleScoreWorkerProduction(
    formRequest({ origin: 'https://attacker.test' }), env()
  )).status, 403);

  assert.equal((await handleScoreWorkerProduction(
    formRequest(), env({ SCORE_REDEEM_LIMIT: limiter(false) })
  )).status, 429);

  assert.equal((await handleScoreWorkerProduction(
    formRequest({ value: 'short' }), env()
  )).status, 400);
});


test('Stage E redemption origin override is opt-in and limited to usd-impact-site Vercel deployment origins', async () => {
  const qaOrigin = 'https://usd-impact-site-5olortwna-usd-impact.vercel.app';
  const qaEnv = env({
    SCORE_PRODUCTION_QA_BRIDGE_ENABLED: 'true',
    SCORE_PRODUCTION_QA_WEBSITE_ORIGIN: qaOrigin,
  });
  const expiresAtMs = Date.now() + 60_000;
  const allowed = await handleScoreWorkerProduction(
    formRequest({ origin: qaOrigin }),
    qaEnv,
    {
      redeemScoreEdgeTicket: async () => ({ token, path: '/en/', expiresAtMs }),
    },
  );
  assert.equal(allowed.status, 303);

  const deniedBadHost = await handleScoreWorkerProduction(
    formRequest({ origin: 'https://attacker.vercel.app' }),
    { ...qaEnv, SCORE_PRODUCTION_QA_WEBSITE_ORIGIN: 'https://attacker.vercel.app' },
    {
      redeemScoreEdgeTicket: async () => ({ token, path: '/en/', expiresAtMs }),
    },
  );
  assert.equal(deniedBadHost.status, 403);

  const deniedMismatch = await handleScoreWorkerProduction(
    formRequest({ origin: SCORE_PRODUCTION_WEBSITE_ORIGIN }),
    qaEnv,
    {
      redeemScoreEdgeTicket: async () => ({ token, path: '/en/', expiresAtMs }),
    },
  );
  assert.equal(deniedMismatch.status, 403);
});

test('successful redemption sets only the host-only secure session cookie', async () => {
  const expiresAtMs = Date.now() + 60_000;
  const result = await handleScoreWorkerProduction(formRequest(), env(), {
    redeemScoreEdgeTicket: async (supplied) => supplied === ticket
      ? { token, path: '/en/', expiresAtMs }
      : null,
  });
  assert.equal(result.status, 303);
  assert.equal(result.headers.get('location'), '/en/');
  const cookie = result.headers.get('set-cookie');
  assert.match(cookie, /^__Host-score_session=[A-Za-z0-9_-]{43};/);
  assert.match(cookie, /; Path=\//);
  assert.match(cookie, /; Secure/);
  assert.match(cookie, /; HttpOnly/);
  assert.match(cookie, /; SameSite=Lax/);
  assert.doesNotMatch(cookie, /Domain=/i);
  assert.equal(cookie.includes(ticket), false);
});

test('protected request revalidates existing session before ASSETS', async () => {
  let assetCalls = 0;
  const e = env({
    ASSETS: { fetch: async () => { assetCalls++; return new Response('premium'); } },
  });
  const req = request('/en/', { headers: { Cookie: '__Host-score_session=' + token } });

  const denied = await handleScoreWorkerProduction(req.clone(), e, {
    scoreEdgeSessionAllowed: async () => false,
  });
  assert.equal(denied.status, 403);
  assert.equal(assetCalls, 0);

  const allowed = await handleScoreWorkerProduction(req.clone(), e, {
    scoreEdgeSessionAllowed: async () => true,
  });
  assert.equal(allowed.status, 200);
  assert.equal(assetCalls, 1);
  assert.equal(allowed.headers.get('x-robots-tag'), 'noindex, nofollow');
});

test('missing or failed rate limiter fails closed', async () => {
  const req = request('/en/', { headers: { Cookie: '__Host-score_session=' + token } });
  assert.equal((await handleScoreWorkerProduction(
    req.clone(), env({ SCORE_VALIDATE_LIMIT: null }), { scoreEdgeSessionAllowed: async () => true }
  )).status, 503);
  assert.equal((await handleScoreWorkerProduction(
    req.clone(), env({ SCORE_VALIDATE_LIMIT: limiter(false) }), { scoreEdgeSessionAllowed: async () => true }
  )).status, 429);
});

test('Production config is inert and contains no Development credential boundary', async () => {
  const raw = await readFile(new URL('../workers/score-production/wrangler.jsonc', import.meta.url), 'utf8');
  const config = JSON.parse(raw);
  assert.equal(config.name, 'usd-impact-score-production');
  assert.equal(config.workers_dev, false);
  assert.equal(config.vars.SCORE_WORKER_ENABLED, 'false');
  assert.equal(config.vars.SCORE_EDGE_GATE_ENABLED, 'false');
  assert.equal(config.vars.SCORE_EDGE_REDEMPTION_ENABLED, 'false');
  assert.equal(config.previews.vars.SCORE_WORKER_ENABLED, 'false');
  assert.equal(config.previews.vars.SCORE_EDGE_GATE_ENABLED, 'false');
  assert.equal(config.previews.vars.SCORE_EDGE_REDEMPTION_ENABLED, 'false');
  assert.equal(config.previews.vars.SCORE_WORKER_ORIGIN, 'https://score.usd-impact.com');
  assert.equal(config.previews.vars.SCORE_WEBSITE_ORIGIN, 'https://www.usd-impact.com');
  assert.equal(config.previews.vars.SCORE_EDGE_BRIDGE_ORIGIN, 'https://www.usd-impact.com');
  assert.equal(config.previews.ratelimits.length, 2);
  assert.equal(config.previews.ratelimits[0].namespace_id, config.ratelimits[0].namespace_id);
  assert.equal(config.previews.ratelimits[1].namespace_id, config.ratelimits[1].namespace_id);
  assert.notEqual(config.previews.ratelimits[0].namespace_id, config.previews.ratelimits[1].namespace_id);
  assert.equal(config.routes, undefined);
  assert.equal(config.route, undefined);
  assert.equal(raw.includes('ycstrcvshdluovtuasjc'), false);
  assert.equal(raw.includes('SCORE_PREVIEW_MACHINE'), false);
  assert.equal(raw.includes('SCORE_PREVIEW_SUPABASE'), false);
  assert.equal(raw.includes('score-preview-machine'), false);
  assert.equal(config.ratelimits.length, 2);
  assert.notEqual(config.ratelimits[0].namespace_id, config.ratelimits[1].namespace_id);
});

test('Production source contains no Development project or machine-auth references', async () => {
  const paths = [
    '../workers/score-production/index.mjs',
    './score-production-bridge-client.mjs',
  ];
  for (const path of paths) {
    const raw = await readFile(new URL(path, import.meta.url), 'utf8');
    assert.equal(raw.includes('ycstrcvshdluovtuasjc'), false, path);
    assert.equal(raw.includes('SCORE_PREVIEW_MACHINE'), false, path);
    assert.equal(raw.includes('score-preview-machine'), false, path);
  }
});
